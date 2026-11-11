# GRISTLE & SONS BIOLOGICS meat truck (OVERDUE m04, Act I: the Unpaid get loaded into it): a cab-over refrigerated
# box truck, ~7 m. A red cab with the smiling-butcher badge on its nose, a cream insulated box with the full livery on
# both sides (GRISTLE & SONS / BIOLOGICS / WE LOVE YOU BACK), half of it grown over with wet skin: veins crawling over
# the paint, an eye, teeth, drips off the rub rail. A chill unit over the cab. At the back: two barn doors with
# locking bars, a cantilever tail lift (the plate stands folded up against the doors), under-run bar, lights. Inside:
# a cold blue liner, two meat rails with hooks (staff lanyards hang off some of them), a -18 readout, a strip lamp.
# front = -z, ground at y 0, x right.
# nodes (for the game to drive): wheel_fl wheel_fr wheel_rl wheel_rr (axle pivots, spin round x); door_l door_r (hinge
# pivots, swing round y); lift_arm (the arms' pivot under the floor, round x); lift (the plate's hinge, moves with the
# arm tips) > lift_plate (folds round x). markers: load (where people stand to be loaded, on the lowered plate),
# cab_door_l (the driver gets out here). lod1: the whole thing decimated, doors shut (the props loader draws it far off).
# baked clips (glTF animations): open (fold the plate down, swing the doors open, lower the lift: 3.3 s), lift_up (the
# plate from the ground back to the floor: 1.5 s; play it reversed to lower), drive (one wheel turn, loops: 1 s at
# 30 fps = 1.25 turns per metre... see jf.wheelR). close = open played backwards.
# blender52 -b --python tools/blender/make_story_gristle_truck.py [-- --no-sheet]
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'cast'))
from castlib import *  # noqa (lib: box, cyl, rod, lathe, tube, sweep, ball, side, mat, tex_canvas, text_px, finish, sheet...)
import lib as _L
import gutkit as GK

ID = 'gristle_truck'
rng = random.Random(47)
FPS = 30

def box(size, pos=(0, 0, 0), m=None, bev=0.0, rot=None, name='box', seg=1, taper=None):
    """lib's box with a cheaper default: one chamfer, and none at all on the small bits (the budget is ~12k)"""
    return _L.box(size, pos, m, bev if bev >= 0.009 else 0.0, rot, name, seg, taper)


# ---------------------------------------------------------------- sizes (game metres)
BX = 1.25            # box half width (outer paint)
BZ0, BZ1 = -1.45, 3.38  # box front wall / back of the side walls
BY0, BY1 = 0.98, 3.55   # box skirt bottom / roof top
FLOOR = 1.1          # load floor (top)
CAB_Z0, CAB_Z1 = -3.45, -1.58
WR = 0.48            # tyre radius
FA, RA = -2.72, 2.15  # front / rear axle z
HZ = 3.55            # the doors' outer face line (z): shut, they sit in front of the rear frame
LIFT_PIV = (0.45, 2.85)         # (y, z) the lift arms' pivot under the floor
LIFT_HINGE = (1.04, 3.68)       # (y, z) the plate's hinge, stowed (behind the lock bars)


# ---------------------------------------------------------------- paint
CREAM, LIVER, PINK, RED, YEL, INK, PURP = 0xfff3d0, 0x8a2a4a, 0xff4f7a, 0xc8203a, 0xffe14d, 0x1a1030, 0x5b3a8f


def _badge(px, cx, cy, R):
    """the smiling butcher-doctor in his yellow disc (as on the campus sign), painted flat"""
    px_disc(px, cx, cy, R, RED); px_disc(px, cx, cy, R * 0.86, YEL)
    px_disc(px, cx, cy + R * 0.05, R * 0.46, 0xffc9a8)  # head
    for ex in (-1, 1):
        px_disc(px, cx + ex * R * 0.47, cy + R * 0.02, R * 0.1, 0xffc9a8)  # ears
        px_disc(px, cx + ex * R * 0.24, cy + R * 0.17, R * 0.09, 0xff8aa8)  # cheeks
        for k in range(5):  # shut happy eyes: little arcs
            a = math.pi * (0.15 + 0.7 * k / 4)
            px_disc(px, cx + ex * R * 0.2 - math.cos(a) * R * 0.08, cy - R * 0.06 - math.sin(a) * R * 0.06, max(1, R * 0.025), INK)
        for k in range(6):  # handlebar moustache
            t = k / 5; px_disc(px, cx + ex * (R * 0.04 + t * R * 0.3), cy + R * 0.13 - math.sin(t * math.pi) * R * 0.06 - t * t * R * 0.08, R * (0.06 - 0.03 * t), 0x7a3a28)
    for k in range(9):  # the grin
        a = math.radians(-70 + 140 * k / 8)
        px_disc(px, cx + math.sin(a) * R * 0.28, cy + R * 0.25 + math.cos(a) * R * 0.09, max(1, R * 0.035), INK)
    px[int(cy + R * 0.27):int(cy + R * 0.32), int(cx - R * 0.18):int(cx + R * 0.18)] = hexrgb(0xf8ecd2)  # teeth
    for k in range(7):  # the paper hat
        px_disc(px, cx - R * 0.3 + k * R * 0.1, cy - R * 0.42 - (R * 0.06 if k % 2 else 0), R * 0.13, 0xffffff)


def livery(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(CREAM)
    px[0:5, :] = hexrgb(LIVER); px[7:9, :] = hexrgb(PINK)
    px[h - 9:h - 4, :] = hexrgb(LIVER); px[h - 3:h, :] = hexrgb(PINK)
    _badge(px, 46, 56, 34)
    text_px(px, 'GRISTLE', 92, 18, 4, LIVER)
    text_px(px, '& SONS', 112, 50, 3, LIVER)
    text_px(px, 'BIOLOGICS', 96, 76, 2, PINK)
    text_px(px, 'WE LOVE YOU BACK', 140, 93, 1, PURP)
    text_px(px, 'FRESH DAILY', 12, 98, 1, LIVER)


def door_sheet(px):
    """the rear doors' stickers (one canvas, both doors use halves of it)"""
    h, w = px.shape[:2]
    px[:] = hexrgb(CREAM)
    px[0:3, :] = hexrgb(LIVER)
    text_px(px, 'KEEP', 8, 10, 2, LIVER); text_px(px, 'REFRIGERATED', 8, 28, 1, LIVER)
    text_px(px, 'HOW IS MY', 70, 10, 1, INK); text_px(px, 'DRIVING?', 70, 19, 1, INK); text_px(px, '0800 GRISTLE', 70, 30, 1, PINK)
    for x in range(0, w, 8):  # the conspicuity tape along the bottom: red / white
        px[h - 6:h, x:x + 4] = hexrgb(0xd82030); px[h - 6:h, x + 4:x + 8] = hexrgb(0xf4f4f0)


def cabdoor(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(RED)
    _badge(px, 20, 20, 15)
    text_px(px, 'GRISTLE', 40, 10, 1, CREAM); text_px(px, '& SONS', 40, 20, 1, CREAM)
    text_px(px, 'TRUCK 07', 40, 32, 1, YEL)
    px[h - 4:h, :] = hexrgb(CREAM)  # the cream stripe under the window line


def badge_tex(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(RED)
    _badge(px, w / 2, h / 2, w / 2 - 1)


def windscreen(px):
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    px[:] = hexrgb(0x1c2a3c) * (0.8 + 0.4 * (yy / h))[:, :, None]
    s = ((xx * 0.7 + yy) % 40) < 5  # a reflection streak or two
    px[s] = hexrgb(0x5a7a9a)
    px[:3, :] = hexrgb(0x101014); px[-3:, :] = hexrgb(0x101014); px[:, :3] = hexrgb(0x101014); px[:, -3:] = hexrgb(0x101014)


def sidewin(px):
    windscreen(px)


def chillface(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xd8dce2)
    for y in range(6, h - 6, 4): px[y:y + 2, 6:w // 2 - 6] = hexrgb(0x3a3e46)  # vent slots
    px_disc(px, w * 0.74, h / 2, h * 0.36, 0x3a3e46); px_disc(px, w * 0.74, h / 2, h * 0.3, 0x15161a)
    for k in range(5):
        a = k * 2 * math.pi / 5; px_line(px, w * 0.74, h / 2, w * 0.74 + math.cos(a) * h * 0.28, h / 2 + math.sin(a) * h * 0.28, 0x5a5e66, 1.5)
    text_px(px, 'CHILL-O-MATIC', 4, 1, 1, 0x4fd8ff)


def holdsign(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf4f4f0); px[:4, :] = hexrgb(LIVER)
    text_px(px, 'PLEASE HOLD STILL', 4, 8, 1, INK); text_px(px, 'YOUR SHIFT IS', 4, 18, 1, INK)
    text_px(px, 'IMPORTANT TO US', 4, 27, 1, INK); text_px(px, '<', w - 12, 27, 1, PINK)


def readout(px):
    px[:] = hexrgb(0x081810); text_px(px, '-18C', 3, 4, 2, 0x39ff14)


def tread(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x1e1e22)
    for x in range(0, w, 6): px[:, x:x + 2] = hexrgb(0x2e2e34)


def duct(px):  # the aluminium duct floor: ribs along the truck
    h, w = px.shape[:2]
    px[:] = hexrgb(0xa8b0b8)
    for x in range(0, w, 4): px[:, x] = hexrgb(0x6a7078)


def diamond(px):  # the lift plate: chequer plate, hazard stripes at the end
    h, w = px.shape[:2]
    px[:] = hexrgb(0xb8bec6)
    for y in range(0, h, 6):
        for x in range((y // 6 % 2) * 3, w, 6): px[y:y + 2, x:x + 3] = hexrgb(0xe0e4ea)
    for x in range(w):
        for y in range(h - 8, h):
            px[y, x] = hexrgb(YEL) if ((x + y) // 4) % 2 else hexrgb(0x15161a)


def chevron(px):
    h, w = px.shape[:2]
    for x in range(w):
        for y in range(h): px[y, x] = hexrgb(0xd82030) if ((x + y) // 6) % 2 else hexrgb(0xf4f4f0)


def plate_tex(px):
    px[:] = hexrgb(0xffe14d); text_px(px, 'GRS 07', 4, 4, 1, INK)


def lanyard_card(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf4f4f0); px[:4, :] = hexrgb(0x4fd8ff)
    px_disc(px, w / 2, 9, 3, 0xc8a080)
    for y in (15, 18): px_line(px, 3, y, w - 4, y, 0x5a5a5a)


# ---------------------------------------------------------------- shapes
def decal(name, c, w, h, m, face='-z', tilt=0.0):
    """a printed sheet: one quad facing `face` (-x, +x, -z, +z), reading the right way round from that side; tilt leans
    it back (round its horizontal axis)"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    right, nrm = {'-z': (Vector((1, 0, 0)), Vector((0, 0, -1))), '+z': (Vector((-1, 0, 0)), Vector((0, 0, 1))),
                  '-x': (Vector((0, 0, -1)), Vector((-1, 0, 0))), '+x': (Vector((0, 0, 1)), Vector((1, 0, 0)))}[face]
    up = Vector((0, 1, 0))
    if tilt: up = (up * math.cos(tilt) - nrm * math.sin(tilt))
    C = Vector(c); R = -right * (w / 2); U = up * (h / 2)
    vs = [bm.verts.new(gv(*p)) for p in (C - R - U, C + R - U, C + R + U, C - R + U)]
    f = bm.faces.new(vs)
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    bm.normal_update()
    o = lib_obj(name, bm, m); o['keep_uv'] = 1
    nn = o.data.polygons[0].normal; ng = Vector((nn.x, nn.z, -nn.y))
    if ng.dot(nrm) < 0: o.data.flip_normals()
    return o


def quad(name, P, m):
    """a decal through four game points (counter-clockwise seen from its front), uv 0..1"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*p)) for p in P]; f = bm.faces.new(vs)
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    o = lib_obj(name, bm, m); o['keep_uv'] = 1
    return o


def disc(name, c, r, m, face='-z', n=20):
    """a round decal (badges, hub caps), planar uv"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    right, nrm = {'-z': (Vector((1, 0, 0)), Vector((0, 0, -1))), '+x': (Vector((0, 0, 1)), Vector((1, 0, 0))), '-x': (Vector((0, 0, -1)), Vector((-1, 0, 0)))}[face]
    up = Vector((0, 1, 0)); C = Vector(c)
    ctr = bm.verts.new(gv(*C)); ring = []
    for k in range(n):
        a = 2 * math.pi * k / n
        ring.append((bm.verts.new(gv(*(C - right * (math.cos(a) * r) + up * (math.sin(a) * r)))), (0.5 + math.cos(a) * 0.5, 0.5 + math.sin(a) * 0.5)))
    for k in range(n):
        (v0, u0), (v1, u1) = ring[k], ring[(k + 1) % n]
        f = bm.faces.new((ctr, v0, v1))
        for lp, uv in zip(f.loops, ((0.5, 0.5), u0, u1)): lp[uvl].uv = uv
    bm.normal_update()
    o = lib_obj(name, bm, m); o['keep_uv'] = 1
    nn = o.data.polygons[0].normal; ng = Vector((nn.x, nn.z, -nn.y))
    if ng.dot(nrm) < 0: o.data.flip_normals()
    for p in o.data.polygons: p.use_smooth = False
    return o


def arch(name, x0, x1, cy, cz, r0, r1, a0, a1, m, n=10):
    """a mudguard: a slice of a ring round the axle (y, z) = (cy, cz), from angle a0 to a1 (0 = toward +z, 90 = up)"""
    bm = bmesh.new(); rows = []
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n); s, c = math.sin(a), math.cos(a)
        rows.append([bm.verts.new(gv(x, cy + s * r, cz + c * r)) for x, r in ((x0, r0), (x0, r1), (x1, r1), (x1, r0))])
    for a, b in zip(rows, rows[1:]):
        for i in range(4):
            j = (i + 1) % 4; bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(rows[0]); bm.faces.new(rows[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib_obj(name, bm, m)
    return o


def hook(c, m, s=1.0):
    """a meat hook hanging from a rail: an S of rod, the point turned up"""
    x, y, z = c
    pts = [(x, y, z), (x, y - 0.08 * s, z), (x, y - 0.16 * s, z + 0.02 * s)]
    pts += [(x, y - 0.2 * s - 0.05 * s * math.sin(math.radians(a)), z + 0.06 * s * math.cos(math.radians(a))) for a in range(0, 181, 45)]
    pts += [(x, y - 0.17 * s, z - 0.07 * s)]
    return sweep(pts, [0.008] * (len(pts) - 1) + [0.002], m, seg=4, name='hook')


# ---------------------------------------------------------------- build
def build():
    GK.eerie(True)  # the skin is the Gut's (the owner's darker pick), the paint isn't
    FM = GK.gut_mats()
    GK.eerie(False)
    flesh, vein, enamel, eyeM = FM['flesh'], FM['vein'], FM['enamel'], FM['eye']
    paint = mat('gt_cream', CREAM, rough=0.22, clearcoat=0.9)
    cabP = mat('gt_cabred', RED, rough=0.2, clearcoat=1.0)
    liner = mat('gt_liner', 0xc8d8e4, rough=0.35, clearcoat=0.3)
    alu = mat('gt_alu', 0xc8ccd2, metal=0.9, rough=0.25)
    steel = mat('gt_steel', 0x3a3e46, metal=0.6, rough=0.45)
    chrome = mat('gt_chrome', 0xd8dce4, metal=1.0, rough=0.12)
    blackP = mat('gt_black', 0x1a1a1e, rough=0.45, clearcoat=0.3)
    rubber = mat('gt_rubber', 0x141416, rough=0.8)
    tyre = mat('gt_tyre', 0xffffff, rough=0.8, tex=tex_canvas('gt_treadT', 32, 8, tread))
    rim = mat('gt_rim', 0xe8e8e0, metal=0.3, rough=0.3, clearcoat=0.6)
    liv = mat('gt_livery', 0xffffff, rough=0.22, clearcoat=0.9, tex=tex_canvas('gt_liveryT', 256, 112, livery))
    doorS = mat('gt_doorsheet', 0xffffff, rough=0.22, clearcoat=0.9, tex=tex_canvas('gt_doorT', 128, 48, door_sheet))
    cabD = mat('gt_cabdoor', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_canvas('gt_cabdoorT', 96, 44, cabdoor))
    badgeM = mat('gt_badge', 0xffffff, rough=0.15, clearcoat=1.0, tex=tex_canvas('gt_badgeT', 48, 48, badge_tex))
    glass = mat('gt_glass', 0xffffff, rough=0.05, clearcoat=1.0, tex=tex_canvas('gt_glassT', 64, 32, windscreen))
    head = mat('gt_headlamp', 0xfff8e0, rough=0.05, clearcoat=1.0, emit=0xfff0c0, strength=0.4)
    amber = mat('gt_amber', 0xffa020, rough=0.1, clearcoat=1.0, emit=0xff9010, strength=0.5)
    redL = mat('gt_redlamp', 0xd01020, rough=0.1, clearcoat=1.0, emit=0xff1020, strength=0.5)
    chill = mat('gt_chill', 0xffffff, rough=0.3, clearcoat=0.5, tex=tex_canvas('gt_chillT', 80, 40, chillface))
    ductM = mat('gt_duct', 0xffffff, metal=0.6, rough=0.35, tex=tex_canvas('gt_ductT', 32, 32, duct))
    diaM = mat('gt_diamond', 0xffffff, metal=0.6, rough=0.3, tex=tex_canvas('gt_diaT', 48, 64, diamond))
    chevM = mat('gt_chevron', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('gt_chevT', 64, 8, chevron))
    plateM = mat('gt_plate', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('gt_plateT', 40, 16, plate_tex))
    lamp = mat('gt_striplamp', 0xe8f8ff, emit=0xbfe8ff, strength=1.2)
    holdM = mat('gt_holdsign', 0xffffff, rough=0.4, tex=tex_canvas('gt_holdT', 104, 40, holdsign))
    readM = mat('gt_readout', 0xffffff, rough=0.2, emit_tex=True, emit=0x39ff14, strength=0.8, tex=tex_canvas('gt_readT', 32, 22, readout))
    strap = mat('gt_strap', 0x4fd8ff, rough=0.6)
    cardM = mat('gt_card', 0xffffff, rough=0.4, tex=tex_canvas('gt_cardT', 16, 24, lanyard_card))
    hookM = mat('gt_hook', 0xb8bcc4, metal=1.0, rough=0.3)
    body = []; B = body.append

    # ---- chassis: two rails, cross members, the subframe under the box
    for sx in (-1, 1):
        B(box((0.12, 0.26, 6.55), (sx * 0.45, 0.76, -0.17), steel, bev=0.01))
        B(box((0.1, 0.16, 4.86), (sx * 0.45, 0.96, 0.96), steel, bev=0.008))
    for z in (-3.0, -2.0, -0.6, 0.6, 1.6, 2.7): B(box((0.8, 0.12, 0.1), (0, 0.76, z), steel, bev=0.008))
    for k in range(9): B(box((2.3, 0.08, 0.08), (0, 0.98, -1.3 + k * 0.56), steel, bev=0.006))  # bearers under the floor
    # axles and diff
    B(rod((-0.9, WR, FA), (0.9, WR, FA), 0.06, steel, seg=10))
    B(rod((-0.92, WR, RA), (0.92, WR, RA), 0.07, steel, seg=10))
    B(ball(0.2, (0, WR, RA), steel, scale=(1.0, 0.9, 0.8), seg=12, rings=8))
    for sx in (-1, 1):  # leaf springs
        for z in (FA, RA): B(box((0.08, 0.1, 1.1), (sx * 0.45, WR + 0.16, z), steel, bev=0.01))
    # fuel tank (left), battery box (right), side guards, exhaust
    B(cyl(0.27, 1.0, (-0.82, 0.72, -0.35), alu, axis='x', seg=16, bev=0.02, rot=(0, math.pi / 2, 0)))
    B(cyl(0.29, 0.04, (-0.82, 0.72, -0.86), steel, axis='z', seg=16))
    B(cyl(0.29, 0.04, (-0.82, 0.72, 0.16), steel, axis='z', seg=16))
    B(cyl(0.06, 0.06, (-0.82, 1.0, -0.6), blackP, axis='y', seg=10))
    B(box((0.5, 0.45, 0.6), (0.78, 0.7, -0.4), blackP, bev=0.02))
    for sx in (-1, 1):
        for y in (0.5, 0.82): B(box((0.04, 0.1, 3.2), (sx * 1.18, y, -0.3), alu, bev=0.008))
        for z in (-1.6, -0.3, 1.0): B(box((0.65, 0.055, 0.06), (sx * 0.815, 0.807, z), steel))
        for z in (-1.6, -0.3, 1.0): B(box((0.035, 0.37, 0.047), (sx * 1.1525, 0.655, z), steel))
    B(rod((0.6, 0.45, -1.3), (0.6, 0.45, 0.9), 0.05, chrome, seg=10))
    B(rod((0.6, 0.45, 0.9), (1.0, 0.35, 1.25), 0.05, chrome, seg=10))
    # ---- the box: paint skin outside, a cold liner inside (they overlap, the insulation is between)
    BL = BZ1 - BZ0; BC = (BZ0 + BZ1) / 2
    for sx in (-1, 1):
        B(box((0.04, BY1 - BY0, BL), (sx * (BX - 0.02), (BY0 + BY1) / 2, BC), paint))
        B(box((0.045, BY1 - FLOOR - 0.03, BL - 0.1), (sx * (BX - 0.0605), (FLOOR - 0.03 + BY1 - 0.06) / 2, BC - 0.03), liner))
    B(box((2 * BX - 0.08, 0.04, BL), (0, BY1 - 0.022, BC), paint))
    B(box((2 * BX - 0.17, 0.045, BL - 0.1), (0, BY1 - 0.0605, BC - 0.03), liner))
    B(box((2 * BX - 0.08, BY1 - BY0 - 0.04, 0.04), (0, (BY0 + BY1 - 0.04) / 2, BZ0 + 0.02), paint))
    B(box((2 * BX - 0.17, BY1 - FLOOR - 0.03, 0.045), (0, (FLOOR - 0.03 + BY1 - 0.06) / 2, BZ0 + 0.0605), liner))
    B(box((2 * BX - 0.08, FLOOR - BY0 - 0.04, BL - 0.05), (0, (BY0 + FLOOR - 0.04) / 2 + 0.02, BC - 0.005), steel))  # floor block
    B(box((2 * BX - 0.17, 0.02, BL - 0.1), (0, FLOOR - 0.012, BC - 0.03), ductM))
    # corner extrusions on every long edge, the rub rail, the rear frame
    for sx in (-1, 1):
        for y in (BY1 - 0.01, BY0 + 0.01): B(box((0.07, 0.07, BL + 0.04), (sx * (BX - 0.012), y, BC), alu, bev=0.012))
        B(box((0.07, BY1 - BY0 - 0.03, 0.07), (sx * (BX - 0.012), (BY0 + BY1) / 2, BZ0 + 0.012), alu, bev=0.012))
        B(box((0.05, 0.09, BL - 0.1), (sx * (BX + 0.012), BY0 + 0.24, BC), alu, bev=0.01))  # rub rail
        for k in range(6): B(box((0.05, 0.035, 0.035), (sx * (BX + 0.01), BY0 + 0.14, BZ0 + 0.4 + k * 0.85), amber, bev=0.006))  # side markers
    B(box((2 * BX + 0.02, 0.07, 0.07), (0, BY1 - 0.01, BZ0 + 0.012), alu, bev=0.012))
    RF = BZ1 + 0.04  # the rear frame's centre z: it overlaps the walls' ends
    for sx in (-1, 1): B(box((0.14, 2.575, 0.1), (sx * (BX - 0.055), 2.2575, RF), steel, bev=0.012))
    B(box((2 * BX + 0.01, 0.26, 0.1), (0, BY1 - 0.12, RF), steel, bev=0.012))
    B(box((2 * BX + 0.01, 0.16, 0.12), (0, FLOOR - 0.07, RF + 0.005), steel, bev=0.012))
    for sx in (-1, 1):  # keepers for the lock bars, top and bottom
        for xx in (0.32, 0.88):
            for y in (FLOOR - 0.1, BY1 - 0.04): B(box((0.07, 0.07, 0.105), (sx * xx, y, RF + 0.0975), steel, bev=0.008))
    # rear: under-run bar with chevrons, lights, the lift's mount under the frame
    B(box((2.2, 0.14, 0.1), (0, 0.45, 3.42), steel, bev=0.012))
    B(decal('chev', (0, 0.45, 3.4715), 2.16, 0.12, chevM, face='+z'))
    for sx in (-1, 1):
        B(box((0.06, 0.5, 0.06), (sx * 0.7, 0.72, 3.25), steel, bev=0.006))
        B(box((0.3, 0.12, 0.06), (sx * 0.9, 0.62, 3.42), blackP, bev=0.01))
        for k, m_ in enumerate((redL, amber, 0)):
            if m_: B(box((0.08, 0.08, 0.02), (sx * (0.8 + k * 0.1), 0.62, 3.455), m_, bev=0.004))
        B(box((0.12, 0.26, 0.4), (sx * 0.55, 0.52, 2.85), steel, bev=0.01))  # the lift's brackets, hung off the rails
        B(box((0.45, 0.42, 0.015), (sx * 0.99, 0.62, RA + 0.62), rubber))  # mudflaps
        B(box((0.45, 0.04, 0.05), (sx * 0.99, 0.84, RA + 0.62), steel))
        B(arch('rguard', min(sx * 0.66, sx * 1.27), max(sx * 0.66, sx * 1.27), WR, RA, 0.53, 0.56, 15, 165, blackP))
    B(rod((-0.62, 0.45, 2.85), (0.62, 0.45, 2.85), 0.04, steel, seg=10))
    # ---- the livery on both sides, the doors' stickers are on the doors
    for sx in (-1, 1):
        B(decal('livery%d' % sx, (sx * (BX + 0.0015), 2.27, BC + 0.02), BL - 0.32, 2.1, liv, face='+x' if sx > 0 else '-x'))
    # ---- the chill unit over the cab, its pipes
    B(box((1.7, 0.6, 0.46), (0, 3.22, BZ0 - 0.22), mat('gt_chillbox', 0xd8dce2, rough=0.3, clearcoat=0.5), bev=0.04))
    B(decal('chillface', (0, 3.22, BZ0 - 0.4515), 1.55, 0.5, chill, face='-z'))
    for sx in (-1, 1): B(box((0.08, 0.5, 0.06), (sx * 0.7, 3.2, BZ0 - 0.015), steel, bev=0.008))
    # ---- inside: meat rails and hooks (some with staff lanyards), a strip lamp, the -18 readout
    for sx in (-1, 1):
        B(box((0.06, 0.05, BL - 0.3), (sx * 0.55, BY1 - 0.13, BC), hookM, bev=0.008))
        for k in range(7): B(box((0.03, 0.04, 0.03), (sx * 0.55, BY1 - 0.09, BZ0 + 0.25 + k * 0.7), steel))
    hooks = []
    for sx in (-1, 1):
        for k in range(6):
            z = BZ0 + 0.55 + k * 0.72 + rng.uniform(-0.12, 0.12)
            hooks.append((sx * 0.55, BY1 - 0.155, z))
            B(hook((sx * 0.55, BY1 - 0.155, z), hookM))
    for k, (x, y, z) in enumerate(hooks[1::3]):
        tip = (x, y - 0.25, z + 0.06)
        B(sweep([(x, y - 0.2, z + 0.06), (x - 0.03, y - 0.42, z + 0.04), (x, y - 0.6, z), (x + 0.03, y - 0.42, z - 0.04), (x, y - 0.2, z + 0.055)], 0.008, strap, seg=4, squash=(1.0, 3.0), name='lanyard', cap=False))
        B(box((0.004, 0.11, 0.075), (x, y - 0.66, z), cardM))
    B(box((0.12, 0.025, BL - 1.2), (0, BY1 - 0.097, BC), lamp))
    B(box((0.36, 0.26, 0.04), (0.6, 2.7, BZ0 + 0.098), blackP, bev=0.01))
    B(decal('readout', (0.6, 2.7, BZ0 + 0.1195), 0.3, 0.2, readM, face='+z'))
    B(decal('holdsign', (-0.35, 2.45, BZ0 + 0.0845), 0.78, 0.3, holdM, face='+z'))  # (on the liner, facing whoever is loaded)
    # ---- the skin: a sheet grown up over half of each side (over the words), lumps in it, an eye, teeth; veins crawl
    # out across the clean paint, drips hang off the rub rail. the right side's comes up from the back, the left's
    # from the front (mirrored along the box)
    SHEET = [(1.2, 3.1, .45), (1.6, 3.1, .45), (2.0, 3.1, .45), (2.4, 3.15, .45), (2.8, 3.1, .42), (3.2, 3.05, .38),
             (1.2, 2.6, .45), (1.6, 2.6, .45), (2.0, 2.55, .45), (2.45, 2.6, .42), (2.95, 2.65, .38),
             (1.2, 2.1, .42), (1.6, 2.1, .45), (2.0, 2.05, .42), (2.5, 2.15, .36),
             (1.2, 1.6, .4), (1.65, 1.55, .4), (2.1, 1.65, .34), (1.25, 1.1, .36), (1.7, 1.05, .32), (1.3, 0.6, .3),
             (2.9, 2.3, .26), (3.05, 1.95, .22), (3.1, 1.6, .18), (2.55, 1.35, .24), (2.7, 0.95, .2), (2.75, 0.6, .16),
             (1.95, 0.75, .26), (2.05, 0.35, .2), (1.15, 0.2, .22), (1.3, -0.15, .17)]
    LUMPS = [(2.05, 2.3, .34), (1.45, 1.35, .28), (2.6, 2.9, .26), (1.3, 2.75, .24)]

    def mz(z, sx): return z if sx > 0 else BZ0 + BZ1 - z
    for sx in (-1, 1):
        mb = bpy.data.metaballs.new('skinMB%d' % (sx + 1)); mb.resolution = 0.06; mb.render_resolution = 0.06; mb.threshold = 0.6
        for y, z, r in SHEET:
            e = mb.elements.new(); e.type = 'ELLIPSOID'; e.co = gv(sx * BX, y, mz(z, sx)); e.radius = r
            e.size_x, e.size_y, e.size_z = 0.2, 1.0, 1.0  # (blender x = game x: flat against the wall)
        for y, z, r in LUMPS:
            e = mb.elements.new(); e.co = gv(sx * (BX - 0.04), y, mz(z, sx)); e.radius = r
        o = bpy.data.objects.new('skinMB%d' % (sx + 1), mb); bpy.context.scene.collection.objects.link(o)
        bpy.context.view_layer.update()
        for q in bpy.context.view_layer.objects.selected: q.select_set(False)
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.object.convert(target='MESH')
        s = bpy.context.view_layer.objects.active; s.name = 'skin%d' % sx
        sm = s.modifiers.new('sm', 'SMOOTH'); sm.factor = 1.0; sm.iterations = 12; apply_mods(s)  # (melt the blobs into one sheet)
        for v in s.data.vertices:  # the half inside the wall flattened onto a plane in the paint
            g = GK.gg(v.co)
            if sx * g[0] < BX + 0.012: v.co = gv(sx * (BX - 0.02), g[1], g[2])  # (thin film near the paint too: a clean edge, no flicker)
        GK.decimate(s, 950)
        GK._drop_crumbs(s, keep=40)  # (smoothing leaves a few loose crumbs on the plane inside the wall)
        s.data.materials.clear(); s.data.materials.append(flesh)
        GK.lump(s, 0.025, 3.5, seed=7 + sx, mask=lambda g, sx=sx: max(0.0, min(1.0, (sx * g[0] - BX) / 0.03))); GK.wet(s)
        uv_box(s, 0.9); s['keep_uv'] = 1; B(s)
        bvh = GK.bvh_of(s)
        ex = 1 if sx > 0 else -1
        ep, _ = GK.onsurf(bvh, (sx * (BX + 0.6), 2.05, mz(2.3, sx)), -0.06)  # in the big lump, a third of it showing
        B(GK.eyeball(eyeM, 0.15, ep, rot=(0, 0, -ex * math.pi / 2), name='eye%d' % sx))
        for k, (y, z) in enumerate(((1.42, 1.25), (2.6, 2.75), (1.15, 2.4))):
            tp, _ = GK.onsurf(bvh, (sx * (BX + 0.6), y, mz(z, sx)), -0.035)
            B(GK.canine(enamel, pos=tp, rot=(0, 0, -ex * (math.pi / 2 - 0.35)), s=0.5, name='tooth', seed=k + (3 if sx < 0 else 0)))
        for pts in ([(2.3, 0.75), (2.45, 0.3), (2.3, -0.2), (2.55, -0.65), (2.42, -1.05)],
                    [(1.5, 0.35), (1.62, -0.15), (1.48, -0.6), (1.6, -0.95)],
                    [(3.05, 1.2), (3.15, 0.8), (3.05, 0.35)], [(2.95, 2.55), (3.2, 2.4), (3.3, 2.0)]):
            P = [(sx * (BX + 0.006), y, mz(z, sx)) for y, z in pts]
            P[0] = (sx * (BX - 0.005), P[0][1], P[0][2])  # (its root sunk in the skin)
            P[1:] = [(sx * (BX + 0.014), y, z) for _, y, z in P[1:]]  # (lying on the paint)
            B(sweep(P, [0.045 - 0.028 * i / (len(P) - 1) for i in range(len(P))], vein, seg=5, name='vein'))
        for k in range(4):  # drips off the rub rail, under the sheet
            z = mz(1.35 + k * 0.48, sx); L = 0.16 + 0.1 * (k % 2)
            B(sweep([(sx * (BX + 0.03), BY0 + 0.2, z), (sx * (BX + 0.032), BY0 + 0.2 - L * 0.6, z), (sx * (BX + 0.032), BY0 + 0.2 - L, z)], [0.025, 0.018, 0.01], flesh, seg=6, name='drip'))
            B(ball(0.02, (sx * (BX + 0.032), BY0 + 0.195 - L, z), flesh, seg=8, rings=6))

    # ---- the cab: a side profile pushed out across, the windscreen raked back
    prof = [(CAB_Z1, 1.02), (CAB_Z0 + 0.04, 1.02), (CAB_Z0, 1.12), (CAB_Z0, 1.78), (CAB_Z0 + 0.2, 2.72), (CAB_Z0 + 0.34, 2.9), (CAB_Z1 + 0.04, 2.9), (CAB_Z1, 2.86)]
    B(side(prof, 2.3, (0, 0, 0), cabP, bev=0.06, seg=3, name='cab'))
    # windscreen on the raked face, a sun visor, wipers
    a0, a1 = Vector((0, 1.78, CAB_Z0)), Vector((0, 2.72, CAB_Z0 + 0.2))
    d = (a1 - a0).normalized(); n = Vector((0, d.z, -d.y)) * -1  # outward (forward and a little up)
    n = Vector((0, -n.y, -n.z)) if n.z > 0 else n
    p0, p1 = a0 + d * 0.06 + n * 0.004, a0 + d * 0.86 + n * 0.004
    B(quad('windscreen', [(1.0, p0.y, p0.z), (-1.0, p0.y, p0.z), (-1.0, p1.y, p1.z), (1.0, p1.y, p1.z)], glass))  # (ccw seen from the front: its right is -x)
    B(box((2.1, 0.04, 0.22), (0, 2.8, CAB_Z0 + 0.18), blackP, bev=0.01, rot=(-0.25, 0, 0)))
    w0, w1 = a0 + d * 0.1 + n * 0.012, a0 + d * 0.5 + n * 0.012
    for x in (-0.5, 0.45): B(rod((x - 0.3, w0.y, w0.z), (x + 0.15, w1.y, w1.z), 0.008, blackP, seg=4))
    # side windows (doors), door shut lines as a painted panel, handles, steps, mirrors
    for sx in (-1, 1):
        xf = sx * 1.1525
        face = '+x' if sx > 0 else '-x'
        B(quad('sidewin%d' % sx, [(xf, 1.92, -3.15), (xf, 1.92, -2.15), (xf, 2.7, -2.15), (xf, 2.7, -3.02)] if sx < 0 else
               [(xf, 1.92, -2.15), (xf, 1.92, -3.15), (xf, 2.7, -3.02), (xf, 2.7, -2.15)], glass))
        B(decal('cabdoor%d' % sx, (xf, 1.5, -2.62), 0.92, 0.42, cabD, face=face))
        B(box((0.03, 0.04, 0.16), (sx * 1.165, 1.82, -2.25), chrome, bev=0.008))
        for y in (0.62, 0.86): B(box((0.34, 0.04, 0.32), (sx * 0.98, y, -1.82), blackP, bev=0.008))
        B(box((0.04, 0.44, 0.3), (sx * 1.15, 0.8, -1.82), steel))
        B(tube([(sx * 1.13, 2.45, -3.2), (sx * 1.42, 2.5, -3.28), (sx * 1.5, 2.45, -3.25)], 0.018, chrome, name='mirrorarm'))
        B(box((0.09, 0.46, 0.2), (sx * 1.5, 2.22, -3.25), blackP, bev=0.02))
        B(tube([(sx * 1.13, 2.05, -3.2), (sx * 1.48, 2.02, -3.26)], 0.015, chrome, name='mirrorarm2'))
        B(arch('fguard', min(sx * 0.82, sx * 1.2), max(sx * 0.82, sx * 1.2), WR, FA, 0.53, 0.56, 10, 170, blackP))
    # nose: grille, badge, headlamps, indicators, bumper, plate, roof markers
    B(box((1.2, 0.48, 0.04), (0, 1.38, CAB_Z0 - 0.012), blackP, bev=0.01))
    for k in range(4): B(box((1.14, 0.035, 0.03), (0, 1.2 + k * 0.11, CAB_Z0 - 0.04), chrome, bev=0.006))
    B(cyl(0.18, 0.04, (0, 1.74, CAB_Z0 - 0.015), chrome, axis='z', seg=20))
    B(disc('badge', (0, 1.74, CAB_Z0 - 0.0375), 0.155, badgeM, face='-z'))
    for sx in (-1, 1):
        B(box((0.34, 0.2, 0.04), (sx * 0.85, 1.3, CAB_Z0 - 0.012), chrome, bev=0.01))
        B(box((0.3, 0.16, 0.03), (sx * 0.85, 1.3, CAB_Z0 - 0.035), head, bev=0.008))
        B(box((0.12, 0.08, 0.03), (sx * 0.85, 1.12, CAB_Z0 - 0.02), amber, bev=0.006))
    B(box((2.36, 0.32, 0.2), (0, 0.87, CAB_Z0 - 0.06), mat('gt_bumper', 0x5a5e66, rough=0.4, clearcoat=0.4), bev=0.03))
    for sx in (-1, 1): B(box((0.14, 0.08, 0.02), (sx * 0.85, 0.8, CAB_Z0 - 0.165), amber, bev=0.004))
    B(decal('plate', (0, 0.88, CAB_Z0 - 0.1615), 0.42, 0.14, plateM, face='-z'))
    for k in range(5): B(box((0.1, 0.05, 0.06), (-0.5 + k * 0.25, 2.92, CAB_Z0 + 0.42), amber, bev=0.008))
    # ---- nodes
    root = finish('s_' + ID, [], {})
    J = {}

    def node(name, pos, parent):
        e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
        e.parent = parent; e.location = gv(*pos) - (parent.matrix_world.translation if parent is not root else Vector((0, 0, 0)))
        bpy.context.view_layer.update(); J[name] = e; return e

    def under(objs, parent, name):
        if not objs: return None
        for x in objs:
            if not x.get('keep_uv'): apply_mods(x); uv_box(x, 0.25)
        o = join(objs, name); apply_mods(o); bpy.context.view_layer.update()
        o.data.transform(Matrix.Translation(o.location)); o.location = (0, 0, 0)  # (join keeps the first piece's origin)
        o.data.transform(Matrix.Translation(-parent.matrix_world.translation)); o.parent = parent; o.location = (0, 0, 0)
        return o
    under(body, root, 'body')
    # ---- wheels: steel discs, singles at the front, twins at the back
    def tyre_rim(x, out, z, nuts=True):
        sx = 1 if out > 0 else -1
        p = [lathe([(0.3, -0.13), (0.44, -0.14), (WR, -0.09), (WR, 0.09), (0.44, 0.14), (0.3, 0.13)], (x, WR, z), tyre, seg=16, axis='x')]
        p.append(lathe([(0.0, 0.0), (0.3, 0.0), (0.28, 0.03), (0.16, 0.05), (0.1, 0.09), (0.0, 0.09)], (x + sx * 0.1, WR, z), rim, seg=12, axis='x', rot=(0, 0, math.pi) if sx < 0 else None))
        if nuts:
            for k in range(6):
                a = k * math.pi / 3
                p.append(cyl(0.018, 0.04, (x + sx * 0.2, WR + math.sin(a) * 0.12, z + math.cos(a) * 0.12), chrome, axis='x', seg=6))
        return p
    for nm, sx, z, twin in (('wheel_fl', -1, FA, False), ('wheel_fr', 1, FA, False), ('wheel_rl', -1, RA, True), ('wheel_rr', 1, RA, True)):
        w = node(nm, (sx * 0.95, WR, z), root)
        parts = tyre_rim(sx * (0.98 if not twin else 1.11), sx, z)
        if twin: parts += tyre_rim(sx * 0.82, sx, z, nuts=False)[:1]
        under(parts, w, nm + '_mesh')
    # ---- the back doors: hinged on the outer edges
    for nm, sx in (('door_l', -1), ('door_r', 1)):
        dn = node(nm, (sx * 1.3, (FLOOR + BY1) / 2, HZ + 0.04), root)
        dp = [box((1.2, BY1 - FLOOR - 0.12, 0.05), (sx * 0.61, (FLOOR + BY1) / 2 - 0.02, HZ - 0.035), paint, bev=0.012)]
        dp.append(decal(nm + '_sheet', (sx * 0.61, FLOOR + 0.42, HZ - 0.0085), 1.16, 0.44, doorS, face='+z'))
        for xx in (0.32, 0.88):  # two lock bars each, brackets, a handle on each
            dp.append(rod((sx * xx, FLOOR - 0.07, HZ + 0.01), (sx * xx, BY1 - 0.12, HZ + 0.01), 0.022, chrome, seg=8))
            for y in (FLOOR + 0.25, 2.3, BY1 - 0.4): dp.append(box((0.08, 0.06, 0.05), (sx * xx, y, HZ - 0.005), steel, bev=0.006))
            dp.append(box((0.04, 0.42, 0.04), (sx * (xx + 0.05), 1.7, HZ + 0.04), steel, bev=0.01, rot=(0, 0, sx * 0.05)))
        for y in (FLOOR + 0.15, 2.0, BY1 - 0.25):  # hinges, out to the pivot line
            dp.append(box((0.16, 0.08, 0.05), (sx * 1.22, y, HZ - 0.005), steel, bev=0.006))
            dp.append(cyl(0.025, 0.12, (sx * 1.3, y, HZ + 0.04), steel, axis='y', seg=8))
        if sx > 0:  # the skin creeping round the corner onto the right door, a vein across
            s = GK.meta([((1.12, 1.55, HZ - 0.02), 0.32), ((1.0, 1.25, HZ - 0.03), 0.28), ((1.15, 2.0, HZ - 0.03), 0.24)], res=0.07, m=flesh, target=260, name='doorskin',
                        clamp=lambda p: (min(p[0], 1.19), p[1], max(p[2], HZ - 0.05)))
            GK.lump(s, 0.02, 4.0, seed=12); dp.append(s)
            dp.append(sweep([(1.0, 1.7, HZ + 0.02), (0.75, 1.85, HZ - 0.004), (0.55, 1.78, HZ - 0.004), (0.4, 1.95, HZ - 0.004)], [0.03, 0.022, 0.016, 0.01], vein, seg=5, name='doorvein'))
        under(dp, dn, nm + '_mesh')
    # ---- the tail lift: arms from under the floor, the plate standing folded up against the doors
    ly, lz = LIFT_PIV; hy, hz = LIFT_HINGE
    LA = node('lift_arm', (0, ly, lz), root)
    ap = []
    for sx in (-1, 1):
        ap.append(box((0.1, 0.12, 1.08), (sx * 0.66, (ly + hy) / 2, (lz + hz) / 2), steel, bev=0.012, rot=(-math.atan2(hy - ly, hz - lz), 0, 0)))
        ap.append(cyl(0.07, 0.14, (sx * 0.62, ly, lz), steel, axis='x', seg=10))
    ap.append(rod((-0.7, ly + 0.2, lz + 0.33), (0.7, ly + 0.2, lz + 0.33), 0.045, steel, seg=8))
    under(ap, LA, 'lift_arm_mesh')
    L = node('lift', (0, hy, hz), root)
    LP = node('lift_plate', (0, hy, hz), L)
    lp = [box((2.2, 1.6, 0.08), (0, hy + 0.8, hz), diaM, bev=0.01)]
    for sx in (-1, 1):
        lp.append(cyl(0.06, 0.16, (sx * 0.66, hy, hz), steel, axis='x', seg=10))
        lp.append(box((0.06, 1.5, 0.05), (sx * 1.05, hy + 0.8, hz + 0.06), steel, bev=0.008))
    lp.append(box((2.1, 0.06, 0.05), (0, hy + 1.56, hz + 0.06), steel, bev=0.008))
    under(lp, LP, 'lift_plate_mesh')
    node('load', (0, 0.12, 4.55), root)  # where the unlucky stand, on the lowered plate
    node('cab_door_l', (-1.6, 0, -2.6), root)
    # ---- far away: everything as one decimated mesh, doors shut
    bpy.context.view_layer.update()
    cps = []
    for o in [o for o in root.children_recursive if o.type == 'MESH']:
        c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c); c.parent = None; c.matrix_world = o.matrix_world.copy(); cps.append(c)
    lod = join(cps, 'lod1'); dm = lod.modifiers.new('dec', 'DECIMATE'); dm.ratio = 0.2; apply_mods(lod); lod.parent = root; lod.hide_render = True
    # ---- the baked clips
    clips(root, J)
    root['jf'] = json.dumps({'kind': 'prop', 'id': ID, 'story': True, 'vehicle': True, 'size': [2.95, 3.55, 7.0], 'front': '-z',
                             'wheels': ['wheel_fl', 'wheel_fr', 'wheel_rl', 'wheel_rr'], 'wheelR': WR, 'doors': ['door_l', 'door_r'],
                             'lift': 'lift', 'lift_plate': 'lift_plate', 'lift_arm': 'lift_arm', 'load': 'load', 'floor': FLOOR,
                             'clips': {'open': 3.3, 'lift_up': 1.5, 'drive': 1.0},
                             'col': [[-1.27, 0, -3.6, 1.27, 2.95, -1.55], [-1.27, 0.3, -1.55, 1.27, 3.55, 3.5]],
                             'note': 'close = open backwards; lower the plate = lift_up backwards. col = boxes (minx,miny,minz,maxx,maxy,maxz) with the doors shut'})
    return root


def clips(root, J):
    """bake the clips as NLA tracks (one track name per clip, on every node it moves): the glTF exporter merges
    same-named tracks into one animation"""
    bpy.context.scene.render.fps = FPS  # (the keys are in 30 fps frames)
    ly, lz = LIFT_PIV; hy, hz = LIFT_HINGE
    La = math.hypot(hy - ly, hz - lz); a0 = math.atan2(hy - ly, hz - lz)
    down = a0 - math.asin((0.05 - ly) / La)  # how far the arms turn to put the plate's hinge 5 cm off the ground

    def tip(t):  # the arm tip (= the plate's hinge) after the arm turned t of the way down
        a = a0 - down * t
        return (0, ly + La * math.sin(a), lz + La * math.cos(a))

    def ease(t): return t * t * (3 - 2 * t)
    tracks = {}

    def key(o, clip, path, frames, interp='BEZIER'):
        """frames: [(frame, value tuple)]"""
        ad = o.animation_data_create(); ad.action = None
        base = getattr(o, path).copy() if hasattr(getattr(o, path), 'copy') else getattr(o, path)
        for f, v in frames:
            setattr(o, path, v); o.keyframe_insert(path, frame=f)
        act = ad.action; act.name = clip + '_' + o.name
        for fc in _fcurves(act):
            for kp in fc.keyframe_points: kp.interpolation = interp
        tr = ad.nla_tracks.new(); tr.name = clip; tr.strips.new(clip, 1, act); ad.action = None
        tr.mute = True  # (muted: the rest pose stays shut; the exporter still writes every track)
        setattr(o, path, base)
        tracks.setdefault(clip, []).append(o.name)

    r0 = lambda o: tuple(o.rotation_euler)
    # open: 0-0.8 s the plate folds down; 0.7-1.9 s the doors swing round to the sides; 1.9-3.3 s the lift lowers
    F = lambda s: 1 + round(s * FPS)
    LPn, Ln, LAn = J['lift_plate'], J['lift'], J['lift_arm']
    key(LPn, 'open', 'rotation_euler', [(F(0), (0, 0, 0)), (F(0.8), (math.pi / 2, 0, 0)), (F(3.3), (math.pi / 2, 0, 0))])
    for nm, sg in (('door_l', -1), ('door_r', 1)):
        d = J[nm]; ang = sg * math.radians(262 if nm == 'door_l' else 226)  # (round blender z = game y; the right one stops on the skin)
        fr = [(F(0), (0, 0, 0)), (F(0.7), (0, 0, 0))]
        for k in range(1, 7): t = k / 6; fr.append((F(0.7 + 1.2 * t), (0, 0, ease(t) * ang)))  # (sampled: one long swing)
        fr.append((F(3.3), (0, 0, ang)))
        key(d, 'open', 'rotation_euler', fr, interp='LINEAR')
    for clip, t0, t1, dur, seq in (('open', 1.9, 3.3, 3.3, (0.0, 1.0)), ('lift_up', 0.0, 1.5, 1.5, (1.0, 0.0))):
        fa, fl = [], []
        if t0 > 0: fa.append((F(0), (0, 0, 0))); fl.append((F(0), gv(*tip(0))))
        for k in range(9):
            t = k / 8; s = seq[0] + (seq[1] - seq[0]) * ease(t)
            fa.append((F(t0 + (t1 - t0) * t), (down * s, 0, 0)))  # (blender +x turns game-back toward game-down)
            fl.append((F(t0 + (t1 - t0) * t), gv(*tip(s))))
        key(LAn, clip, 'rotation_euler', fa, interp='LINEAR')
        key(Ln, clip, 'location', fl, interp='LINEAR')
    for nm, ang in (('door_l', -math.radians(262)), ('door_r', math.radians(226))): key(J[nm], 'lift_up', 'rotation_euler', [(F(0), (0, 0, ang)), (F(1.5), (0, 0, ang))])
    key(LPn, 'lift_up', 'rotation_euler', [(F(0), (math.pi / 2, 0, 0)), (F(1.5), (math.pi / 2, 0, 0))])
    for nm in ('wheel_fl', 'wheel_fr', 'wheel_rl', 'wheel_rr'):
        key(J[nm], 'drive', 'rotation_euler', [(F(k / 8), (-2 * math.pi * k / 8, 0, 0)) for k in range(9)], interp='LINEAR')
    bpy.context.scene.frame_set(1)
    root['clips'] = json.dumps(tracks)


def _fcurves(act):
    """the action's F-curves (blender 5: layers > strips > channelbags; older: act.fcurves)"""
    if hasattr(act, 'layers') and len(act.layers):
        out = []
        for ly in act.layers:
            for st in ly.strips:
                for cb in st.channelbags: out += list(cb.fcurves)
        return out
    return list(act.fcurves)


def export_anim(root, file_id):
    os.makedirs(MODELS, exist_ok=True)
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    root.select_set(True)
    for c in root.children_recursive: c.select_set(True)
    path = os.path.join(MODELS, file_id + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                              export_extras=True, export_yup=True, export_texcoords=True, export_normals=True,
                              export_materials='EXPORT', export_image_format='AUTO', export_lights=False, export_cameras=False,
                              export_animations=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True,
                              export_optimize_animation_size=False, export_optimize_animation_keep_anim_object=True)  # (keep the 'hold' tracks)
    tris, lo, hi = stats(root)
    print(f'JF_EXPORT {file_id}: {os.path.getsize(path) // 1024} KB, {tris} tris, '
          f'x {lo[0]:.3f}..{hi[0]:.3f} y {lo[1]:.3f}..{hi[1]:.3f} z {lo[2]:.3f}..{hi[2]:.3f}')
    return path


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    reset()
    root = build()
    if '--no-export' not in argv: export_anim(root, 'story/s_' + ID)
    if '--no-sheet' not in argv: sheet(root, 's_' + ID, exposure=-0.4)


main()
