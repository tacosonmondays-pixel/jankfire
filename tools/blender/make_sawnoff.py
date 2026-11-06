# Half a Shotgun: a 12 gauge side-by-side hammer double (coach-gun pattern) with the barrels hacksawed to 300 mm and
# the buttstock cut off behind the wrist into a pistol grip. Real millimetres x1.0 (1 mm = 0.001), built on the code
# model's numbers (sidemodels.js sawnoffBuild): bore line y 20 with the barrels at x +-11, muzzle at z -310, breech
# face + hinge pin at z -12, the grip raking back from (0, 0, 73).
# Real parts: two barrels (23 mm at the chambers, 22 at the cut, 18.5 mm bores) on a top rib + bottom rib + lump, a
# splinter forend with its iron, the action with fences, knuckle, hinge pin, strikers, top lever and two exposed hammers,
# two triggers in one guard, the stock wrist ending in a rough saw cut.
# Made fun: candy red-orange furniture, colour case-hardened action (blue / straw / purple swirls), blued barrels with a
# crooked bright hacksaw cut (and a dashed "cut here" line it missed), brass bead + triggers, electrical tape on the
# grip with the end peeling, raw sawn end grain, a HALF OFF price sticker.
# Moving parts (sidearms.js): hinge_wzB (barrels, breaks open round the pin), forend_wzA + shell1_wzN / shell2_wzN
# ride on it, hammerR_wzN / hammerL_wzN (modelled cocked, the game drops them 0.75 rad onto the strikers).
# run: blender -b --python tools/blender/make_sawnoff.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

def g(*v): return tuple(a / 1000 for a in v)  # game millimetres -> metres
def pz(pts): return [(z / 1000, y / 1000) for z, y in pts]  # side outlines in mm (z, y)
BY, BX, MZ, HZ = 20, 11, -310, -12  # bore line, barrel axes at x +-11, muzzle, breech face (mm)
PIN = (0, 4, -12)  # hinge pin: the barrels, forend and shells swing round it
BF = -12.3  # the barrels' breech face (0.3 mm off the standing breech)
HAM = (13, 28, 54)  # hammer pivot (x mirrored)
COCK = 0.75  # the game drops the hammers this far (rad) from the modelled cocked pose onto the strikers
BEAD_R, RIB_TOP = 2.0, 33.5
BEAD_C = RIB_TOP + 1.5  # the bead sits a little into the rib
SIGHT_Y = BEAD_C + BEAD_R  # top of the bead
SIGHT_Z = 0.075  # the eye sits 0.17 m (viewmodel) behind this: far enough back that the gun stays under the crosshair
U = (0.5227, -0.8526)  # grip axis (z, y): 0.55 rad of rake
NB = (0.8526, 0.5227)  # across the grip, towards the comb


# ------------------------------------------------------------ small helpers
_cut = cut
def cut(o, cutter, op='DIFFERENCE', keep=False):  # lib's boolean, then clean the material index the cutter's faces come back with
    _cut(o, cutter, op, keep)
    n = max(1, len(o.data.materials))
    for p in o.data.polygons:
        if p.material_index >= n: p.material_index = 0
    return o


def link(o): bpy.context.scene.collection.objects.link(o); return o


def taper_x(o, z0, z1, s0, s1):  # narrow a part along game z (actions narrow to the wrist)
    for v in o.data.vertices:
        t = min(1.0, max(0.0, (-v.co.y - z0) / (z1 - z0)))
        v.co.x *= s0 + (s1 - s0) * t


def face_mats(o, mats, pick):
    """add materials to o and set each face's material from pick(centre, normal) (game coords) -> index or None"""
    apply_mods(o); bpy.context.view_layer.update()
    me = o.data
    for m in mats: me.materials.append(m)
    mw = o.matrix_world; R = mw.to_3x3()
    for p in me.polygons:
        c = mw @ p.center; n = (R @ p.normal).normalized()
        k = pick((c.x, c.z, -c.y), (n.x, n.z, -n.y))
        if k is not None: p.material_index = k


def prune_mats(o):  # drop material slots nothing uses (zone_join reads the first one)
    me = o.data
    used = sorted({p.material_index for p in me.polygons})
    mats = [me.materials[i] for i in used]; idx = [used.index(p.material_index) for p in me.polygons]
    me.materials.clear()
    for m in mats: me.materials.append(m)
    for p, i in zip(me.polygons, idx): p.material_index = i
    return o


def split_mats(o, names, name):
    """move the faces using the named materials into their own object (trims that keep their look under a wrap)"""
    apply_mods(o)
    n = link(o.copy()); n.data = o.data.copy(); n.name = name
    for ob, keep in ((o, False), (n, True)):
        bm = bmesh.new(); bm.from_mesh(ob.data)
        mn = [m.name for m in ob.data.materials]
        kill = [f for f in bm.faces if (mn[f.material_index] in names) != keep]
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        bm.to_mesh(ob.data); bm.free()
        prune_mats(ob)
    return n


def obox(c, ax, hs, m, name='obox', bev=0.0):
    """a box from a centre, three axis vectors and half sizes (game coords, metres): stickers, tape, ridges"""
    bm = bmesh.new(); vs = {}
    for i in (-1, 1):
        for j in (-1, 1):
            for k in (-1, 1):
                vs[i, j, k] = bm.verts.new(gv(*[c[n] + ax[0][n] * hs[0] * i + ax[1][n] * hs[1] * j + ax[2][n] * hs[2] * k for n in range(3)]))
    for f in (((-1, -1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1)), ((1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1)), ((-1, -1, -1), (-1, -1, 1), (1, -1, 1), (1, -1, -1)),
              ((-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)), ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)), ((-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, -1, 1))):
        bm.faces.new([vs[k] for k in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me))
    if m: me.materials.append(m)
    smooth(o, 30); bevel(o, bev, 1)
    return o


def rrect(hw, hd, r, segc):  # rounded rectangle outline (the grip's cross-section)
    pts = []
    for cx, cy, a0 in ((hw - r, hd - r, 0), (r - hw, hd - r, 90), (r - hw, r - hd, 180), (hw - r, r - hd, 270)):
        for k in range(segc + 1):
            a = math.radians(a0 + 90 * k / segc); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def sleeve(c, u, nb, hw, hd, r, t, L, m, segc=3, tilt=0.0, name='sleeve'):
    """a band of tape round the grip: rounded-rect ring of thickness t and width L along the grip axis u"""
    bm = bmesh.new(); loops = []
    for off, s in ((0, -L / 2), (0, L / 2), (t, L / 2), (t, -L / 2)):
        ring = []
        for px, py in rrect(hw + off, hd + off, r + off, segc):
            ring.append(bm.verts.new(gv(*[c[i] + (1, 0, 0)[i] * px + nb[i] * py + u[i] * (s + py * tilt) for i in range(3)])))
        loops.append(ring)
    n = len(loops[0])
    for a, b in zip(loops, loops[1:] + loops[:1]):
        for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); me.materials.append(m)
    smooth(o, 50)
    return o


def turn(objs, pivot, a):  # rotate objects about the game x axis through pivot (three's rotation.x = a)
    bpy.context.view_layer.update()
    p = gv(*pivot); M = Matrix.Translation(p) @ Matrix.Rotation(a, 4, 'X') @ Matrix.Translation(-p)
    for o in objs: o.matrix_world = M @ o.matrix_world


def adopt(child, parent):  # child node that moves with its parent (keeps where it is)
    bpy.context.view_layer.update()
    child.parent = parent; child.matrix_parent_inverse = parent.matrix_world.inverted()


def axis_dist(c):  # distance (mm) from the nearer barrel axis, in the x-y plane
    return min(math.hypot(c[0] * 1000 - sx * BX, c[1] * 1000 - BY) for sx in (-1, 1))


# ------------------------------------------------------------ textures
def smooth_noise(r, size, n):  # tileable value noise, smoothstep-interpolated
    gr = r.random((n, n)); y, x = np.mgrid[0:size, 0:size] / size * n
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    tx, ty = x - x0, y - y0; tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    x0, y0, x1, y1 = x0 % n, y0 % n, (x0 + 1) % n, (y0 + 1) % n
    a = gr[y0, x0] * (1 - tx) + gr[y0, x1] * tx; b = gr[y1, x0] * (1 - tx) + gr[y1, x1] * tx
    return a * (1 - ty) + b * ty


def ramp(v, stops):
    out = np.zeros(v.shape + (3,), dtype=np.float32)
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        t = np.clip((v - a) / (b - a), 0, 1)[..., None]
        m = ((v >= a) & (v <= b))[..., None]
        out = np.where(m, hexrgb(ca) * (1 - t) + hexrgb(cb) * t, out)
    return out


def tex_case(name, size=64, seed=21):
    """colour case hardening: swirled patches of blue, purple, straw and amber over grey steel (turned up for fun)"""
    r = np.random.default_rng(seed)
    w = smooth_noise(r, size, 4)
    n = 0.55 * smooth_noise(r, size, 4) + 0.3 * smooth_noise(r, size, 8) + 0.15 * smooth_noise(r, size, 16)
    s = np.sin(2 * math.pi * (2.0 * n + 1.1 * w)) * 0.5 + 0.5  # the swirl bands
    v = 0.5 * n + 0.5 * s; v = (v - v.min()) / (np.ptp(v) + 1e-6)
    px = ramp(v, [(0.0, 0x1a2470), (0.16, 0x3550c8), (0.3, 0x7a46b0), (0.42, 0x8c8a9c), (0.54, 0xcfd2da), (0.64, 0xe6c068), (0.76, 0xc07a30), (0.88, 0x3c8ad0), (1.0, 0x22306e)])
    px *= (0.9 + 0.2 * r.random((size, size)))[..., None]  # crusty speckle
    return tex_canvas(name, size, size, lambda a: a.__setitem__(slice(None), px))


def tex_endgrain(name, size=32, seed=5):
    """walnut end grain (rings) with hacksaw kerf marks across it"""
    r = np.random.default_rng(seed)
    def draw(px):
        yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
        d = np.hypot(xx + 46, yy + 30)
        ring = (np.sin(d * 1.05 + np.sin(xx * 0.4) * 0.6) * 0.5 + 0.5) ** 3
        c = hexrgb(0xb07a48)[None, None] * (1 - ring[..., None]) + hexrgb(0x5a3418)[None, None] * ring[..., None]
        kerf = np.sin((yy * 1.7 + xx * 0.25 + np.sin(xx * 0.3) * 1.2)) * 0.5 + 0.5
        c *= (0.78 + 0.3 * kerf)[..., None]
        c *= (0.88 + 0.24 * r.random((size, size)))[..., None]
        px[:] = c
    return tex_canvas(name, size, size, draw)


def tex_sawcut(name, size=32, seed=9):  # bright raw steel with saw striations
    r = np.random.default_rng(seed)
    def draw(px):
        yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
        k = np.sin(xx * 1.3 + yy * 0.45 + np.sin(yy * 0.25) * 2) * 0.5 + 0.5
        px[:] = hexrgb(0xdfe3ea)[None, None] * (0.72 + 0.3 * k[..., None]) * (0.9 + 0.15 * r.random((size, size)))[..., None]
    return tex_canvas(name, size, size, draw)


def build():
    # ---------------- materials
    blued = mat('so_blued', 0x222a3c, rough=0.26, metal=0.8, tex=tex_noise('so_blued_t', 0x232c40, var=0.07, size=16, seed=31))
    ribtop = mat('so_ribtop', 0x1a1f2a, rough=0.62, metal=0.6, tex=tex_stripes('so_ribtop_t', 0x161a24, 0x262c3a, size=16, width=1, diag=False))
    case = mat('so_case', 0xa0a4b0, rough=0.22, metal=0.85, tex=tex_case('so_case_t', 64, 21))
    case2 = mat('so_case_ham', 0xa0a4b0, rough=0.2, metal=0.85, tex=tex_case('so_case_ham_t', 32, 47))
    sawn = mat('so_cut', 0xdfe3ea, rough=0.32, metal=1.0, tex=tex_sawcut('so_cut_t'))
    bore = mat('so_bore', 0x060607, rough=0.5, metal=0.3)
    chamber = mat('so_chamber', 0x34363c, rough=0.35, metal=0.8)
    breech = mat('so_breech', 0x9ca2ae, rough=0.24, metal=1.0, tex=tex_noise('so_breech_t', 0xa2a8b4, var=0.08, size=16, seed=33))
    screw = mat('so_screw', 0xd6dbe4, rough=0.16, metal=1.0)
    brass = mat('so_brass', 0xe8b445, rough=0.18, metal=1.0)
    candy = mat('so_candy', 0xe05a3a, rough=0.2, clearcoat=1.0, tex=tex_wood('so_candy_t', 0xff6a3c, 0xb8301a, size=64, seed=41, rings=5))
    grain = mat('so_endgrain', 0x9a6a3c, rough=0.85, tex=tex_endgrain('so_endgrain_t'))
    tape = mat('so_tape', 0x18181b, rough=0.38, tex=tex_stripes('so_tape_t', 0x151517, 0x24242a, size=16, width=3, diag=True))
    hull = mat('so_hull', 0xd8202c, rough=0.18, clearcoat=1.0)
    dash = mat('so_dash', 0xffe14d, rough=0.5)
    black = mat('so_black', 0x050505, rough=0.4)
    def head_draw(px):  # the shell's base: brass, primer, a headstamp
        h, w = px.shape[:2]
        px[:] = hexrgb(0xd9a53a)
        px_disc(px, w / 2, h / 2, w / 2, 0xb07a24, r_in=w / 2 - 1.5)
        px_disc(px, w / 2, h / 2, 5.2, 0x9a9ca4); px_disc(px, w / 2, h / 2, 4.2, 0xc8ccd4); px_disc(px, w / 2, h / 2, 1.4, 0x7a7c84)
        text_px(px, '12', 10, 3, 1, 0x7a5418); text_px(px, 'GA', 10, 22, 1, 0x7a5418)
    headstamp = mat('so_headstamp', 0xffffff, rough=0.2, metal=0.9, tex=tex_canvas('so_headstamp_t', 32, 32, head_draw))
    def tag_draw(px):  # the price sticker
        px[:] = hexrgb(0xffe14d); px[:1] = px[-1:] = hexrgb(0xe0301a); px[:, :1] = px[:, -1:] = hexrgb(0xe0301a)
        text_px(px, 'HALF', 4, 2, 1, 0x111111); text_px(px, 'OFF', 7, 11, 1, 0xe0301a)
    sticker = mat('so_sticker', 0xffffff, rough=0.45, tex=tex_canvas('so_sticker_t', 32, 20, tag_draw))
    parts = []; A = parts.append

    # ======================================================== the barrels (hinge node): one solid, bored and sawn
    # parts are unioned with staggered ends (no coplanar caps), then the breech and the muzzle are cut flat in one go
    # (22.3 mm forward: a hair over touching, so the two tubes really overlap instead of kissing along a line)
    prof = [(11.5, -86), (11.38, -100), (11.25, -120), (11.15, -140), (11.15, -296), (11.15, -302), (11.15, -305.5), (11.15, -308.2), (11.15, -312)]
    br = lathe([(r / 1000, z / 1000) for r, z in [(11.5, BF + 0.5)] + prof + [(11.15, -318)]], g(BX, BY, 0), blued, seg=24)
    cut(br, lathe([(r / 1000, z / 1000) for r, z in [(11.5, BF + 0.8)] + prof + [(11.15, -317.4)]], g(-BX, BY, 0), None, seg=24), 'UNION')
    cut(br, side_x([(-0.004, RIB_TOP / 1000), (0.004, RIB_TOP / 1000), (0.004, 0.0287), (0, 0.022), (-0.004, 0.0287)], 0.3056, g(0, 0, -164.2), None), 'UNION')  # top rib (V bottom: clear of the chambers)
    cut(br, side_x([(-0.004, 0.0105), (0.004, 0.0105), (0.004, 0.0113), (0, 0.018), (-0.004, 0.0113)], 0.3053, g(0, 0, -163.85), None), 'UNION')  # bottom rib
    cut(br, side(pz([(-11.6, 9.3), (-34, 9.3), (-34, -6.8), (-23.5, -6.8), (-11.6, 5.1)]), 0.017, (0, 0, 0), None), 'UNION')  # lump (swings into the knuckle)
    cut(br, box((0.1, 0.1, 0.02), g(0, 10, BF + 10), None))  # the breech face, flat
    # the hacksaw cut: a bit crooked (yaw 2.5, pitch 1.5 degrees) through the muzzle point
    ry, rx = math.radians(2.5), math.radians(1.5)
    nm = (-math.sin(ry), math.cos(ry) * math.sin(rx), -math.cos(ry) * math.cos(rx))
    p0 = g(0, BY, MZ)
    cut(br, box((0.1, 0.1, 0.06), tuple(p0[i] + nm[i] * 0.03 for i in range(3)), None, rot=(rx, ry, 0)))
    for sx in (-1, 1):
        cut(br, cyl(0.00925, 0.33, g(sx * BX, BY, -170), None, seg=24))  # bore
        cut(br, cyl(0.01045, 0.0712, g(sx * BX, BY, -46.4), None, seg=24))  # chamber
        cut(br, cyl(0.01045, 0.0125, g(sx * BX, BY, -87.75), None, seg=24, r2=0.0092))  # forcing cone
    rr = cut(cyl(0.0111, 0.0028, g(BX, BY, -12.4), None, seg=24), cyl(0.0111, 0.0028, g(-BX, BY, -12.4), None, seg=24), 'UNION')
    cut(br, rr)  # rim recesses (one cutter: they overlap a hair between the barrels)
    def plane_d(c): return sum((c[i] - p0[i]) * nm[i] for i in range(3))  # > 0 beyond the cut
    def barrel_pick(c, n):
        d = axis_dist(c)
        if n[2] < -0.95 and plane_d(c) > -0.0004: return 1  # the sawn face
        if plane_d(c) > -0.0026 and d > 10.8 and abs(n[2]) < 0.3: return 1  # bright ring where the file deburred it
        if d < 9.6 and abs(n[2]) < 0.5: return 2  # bore
        if d < 11.2 and abs(n[2]) < 0.9 and c[2] > -0.095: return 3  # chamber + forcing cone + recess walls
        if n[2] > 0.95 and c[2] > -0.0145: return 4  # breech face + recess floors
        if n[1] > 0.95 and c[1] > 0.033 and abs(c[0]) < 0.0045: return 5  # matted rib top
        return None
    uv_box(br, 0.04)
    face_mats(br, [sawn, bore, chamber, breech, ribtop], barrel_pick)
    btrim = split_mats(br, {'so_cut', 'so_bore'}, 'btrim')
    hinge = [br]
    # extractor: a bright plate between the rims under the bore line
    ex = side_x([(x / 1000, y / 1000) for x, y in [(0, 17.2), (0.75, 15), (2.13, 13), (4.17, 11), (6.0, 9.6), (6.5, 7.5), (-6.5, 7.5), (-6.0, 9.6), (-4.17, 11), (-2.13, 13), (-0.75, 15)]], 0.0006, g(0, 0, BF - 0.25), screw)
    hinge.append(ex)
    trim = [btrim]
    # brass bead on a stem, near the cut
    trim.append(ball(BEAD_R / 1000, g(0, BEAD_C, -302), brass, seg=12, rings=8))
    trim.append(cyl(0.0011, 0.002, g(0, RIB_TOP + 0.6, -302), brass, axis='y', seg=8))
    # the dashed "cut here" line they drew... and then sawed somewhere else (crooked the other way)
    rng = random.Random(4)
    for sx in (-1, 1):
        for k in range(13):
            th = math.radians(-125 + k * 250 / 12) if sx > 0 else math.radians(180 - (-125 + k * 250 / 12))
            x, y = sx * BX + 11.35 * math.cos(th), BY + 11.35 * math.sin(th)
            z = -296.5 - 0.06 * x + rng.uniform(-0.35, 0.35)
            trim.append(box(g(2.6, 0.35, 2.2), g(x, y, z), dash, rot=(0, 0, th - math.pi / 2)))
    for x in (-2.2, 2.0):
        trim.append(box(g(2.6, 0.35, 2.2), g(x, RIB_TOP + 0.15, -296.5 - 0.06 * x + 0.1), dash))

    # ======================================================== the forend (rides on the hinge) + its iron
    fe = side(pz([(-45, 16), (-150, 16), (-158, 14), (-164, 9), (-166.5, 2), (-165, -4), (-160, -9), (-150, -12.5), (-120, -13.3), (-60, -13.3), (-46, -13.0)]), 0.036, (0, 0, 0), candy, bev=0.004, seg=3)
    taper_x(fe, -0.045, -0.166, 1.0, 32 / 36)
    arc_pts = [(PIN[2] - 16 * math.cos(math.radians(a)), PIN[1] + 16 * math.sin(math.radians(a))) for a in (-50, -33, -16, 0, 16)]
    iron = side(pz([(-27.4, 16), (-46.5, 16), (-46.5, -13.2), (-26.0, -12.6)] + arc_pts), 0.035, (0, 0, 0), case, bev=0.0012, seg=2)
    for o in (fe, iron):
        apply_mods(o)
        for sx in (-1, 1):  # carve the top to the barrels' shape (0.25 mm clear)
            cut(o, lathe([((r + 0.25) / 1000, z / 1000) for r, z in [(11.5, -8), (11.5, -86), (11.38, -100), (11.25, -120), (11.15, -140), (11.15, -180)]], g(sx * BX, BY, 0), None, seg=24))
        cut(o, box(g(8.4, 10, 200), g(0, 15.6, -90), None))  # room for the bottom rib
    firon = [iron]
    firon.append(box(g(6, 1.2, 20), g(0, -13.6, -80), case, bev=0.0004))  # forend latch lever
    firon.append(box(g(6, 3.2, 3), g(0, -14.6, -90.5), case, bev=0.0005))
    for sx in (-1, 1): firon.append(cyl(0.0021, 0.0008, g(sx * 17.65, 1.5, -38), screw, axis='x', seg=10))

    # ======================================================== the shells (ride on the hinge), rims flush with the breech face
    shells = []
    for sx in (1, -1):
        s = [cyl(0.0109, 0.0003, g(sx * BX, BY, BF - 0.15), headstamp, axis='z', seg=24)]
        s.append(lathe([(r / 1000, z / 1000) for r, z in [(10.9, BF - 0.3), (10.9, BF - 1.4), (10.35, BF - 1.6), (10.35, BF - 12)]], g(sx * BX, BY, 0), brass, seg=24))
        s.append(lathe([(r / 1000, z / 1000) for r, z in [(10.18, BF - 11.7), (10.18, BF - 66.5), (9.95, BF - 68.2), (9.0, BF - 69.4), (6.0, BF - 69.8), (0, BF - 69.0)]], g(sx * BX, BY, 0), hull, seg=24))
        shells.append(s)

    # ======================================================== the action (static): body, knuckle, fences, hammer slots
    knuck = [(PIN[2] - 15.5 * math.cos(math.radians(a)), PIN[1] + 15.5 * math.sin(math.radians(a))) for a in (-90, -75, -60, -45)]
    act = side(pz([(-12, 4), (-12, 26), (0, 26), (4, 27.5), (8, 30.5), (12, RIB_TOP), (56, RIB_TOP), (61, 32.5), (63.5, 30), (63.5, -11.5)] + knuck), 0.046, (0, 0, 0), case, bev=0.002, seg=3)
    taper_x(act, -0.012, 0.0635, 1.0, 41 / 46)
    slots = [box(g(7.6, 22, 36), g(sx * HAM[0], 30, 55), None) for sx in (-1, 1)]
    for c_ in slots: cut(act, c_, keep=True)
    A(act)
    for sx in (-1, 1):  # fences: the rounded shoulders round each barrel's breech
        A(lathe([(r / 1000, z / 1000) for r, z in [(12.3, -11.8), (12.3, -9), (11.8, -5), (10.5, -1), (8.5, 3), (5.5, 6.5), (0.5, 8.5)]], g(sx * BX, BY, 0), case, seg=24))
        sxw = 23 - 2.5 * (66 / 75.5)
        A(cyl(0.0036, 0.0016, g(sx * 23.3, PIN[1], PIN[2]), screw, axis='x', seg=14, bev=0.0004))  # hinge pin heads
        A(cyl(0.0032, 0.0016, g(sx * (sxw + 0.3), HAM[1], HAM[2]), screw, axis='x', seg=14, bev=0.0004))  # hammer pivot pins
        A(lathe([(r / 1000, y / 1000) for r, y in [(2.6, 32.6), (2.6, 34.0), (1.9, 34.7), (0, 34.9)]], g(sx * 12, 0, 31), screw, seg=12, axis='y'))  # strikers
        A(cyl(0.0028, 0.0005, g(sx * BX, BY, -12.0), screw, axis='z', seg=14))  # firing pin bushings
        A(cyl(0.0009, 0.0005, g(sx * BX, BY, -12.02), black, axis='z', seg=8))
        A(cyl(0.0062, 0.00525, g(sx * 20.375, PIN[1], PIN[2]), case, axis='x', seg=20))  # knuckle cheeks round the pin
    # top lever: lies flat on the top strap between the hammers, thumb pad at the back
    A(box(g(7, 1.5, 40), g(0, RIB_TOP + 0.7, 38), blued, bev=0.0005))
    A(cyl(0.005, 0.0015, g(0, RIB_TOP + 0.7, 18), blued, axis='y', seg=16, bev=0.0004))
    A(cyl(0.0025, 0.0007, g(0, RIB_TOP + 1.6, 18), screw, axis='y', seg=10))
    A(box(g(11, 1.6, 12), g(1.2, RIB_TOP + 0.8, 61), blued, bev=0.0006, rot=(0, -0.12, 0)))
    for k in range(4): A(box(g(10, 0.5, 0.7), g(1.2, RIB_TOP + 1.75, 56.5 + k * 2.6), blued, rot=(0, -0.12, 0)))
    # trigger guard (blued) + two brass triggers (front = right barrel, back = left)
    A(side(pz([(3, -10.5), (3.2, -18), (5.5, -27), (11, -35), (20, -40.5), (34, -43), (48, -42.5), (58, -38.5), (65, -32), (69.5, -24), (72, -16), (60, -10.5)]), 0.008, (0, 0, 0), blued, bev=0.0012,
           holes=[pz([(6.5, -11.0), (6.7, -18), (8.6, -25.5), (13.3, -32.4), (21, -37.2), (34, -39.8), (47, -39.3), (56, -35.8), (61.5, -30.5), (64.5, -24), (65.5, -16), (62, -11.0)])]))
    A(side(pz([(19.5, -10.5), (24.5, -10.5), (25, -16), (26.5, -22), (29.5, -27.5), (32.5, -30.5), (31, -32.2), (27, -29.5), (23.5, -24), (21.5, -17)]), 0.0045, (0, 0, 0), brass, bev=0.0009))
    A(side(pz([(35.5, -10.5), (40.5, -10.5), (41, -16), (42.5, -21.5), (45.3, -26.3), (48, -28.8), (46.6, -30.5), (43, -28), (39.5, -23), (37.5, -16.5)]), 0.0045, (0, 0, 0), brass, bev=0.0009))

    # ======================================================== the grip: the stock's wrist, sawn off
    back = [(59, 32.5), (66, 31.5), (74, 28.5), (82, 22.5), (89, 13.5), (95, 4)]
    front = [(67, -22.5), (63, -16), (59, -11.5)]
    far = lambda p, t: (p[0] + U[0] * t, p[1] + U[1] * t)
    gp = side(pz(back + [far((95, 4), t) for t in (40, 70, 100)] + [(150, -90), (125, -108)] + [far((67, -22.5), t) for t in (95, 60, 30)] + front + [(56, 0), (56, 20)]), 0.034, (0, 0, 0), candy, bev=0.006, seg=3)
    apply_mods(gp)
    for c_ in slots: cut(gp, c_, keep=True)
    for c_ in slots: bpy.data.objects.remove(c_, do_unlink=True)
    # the saw cut: 7 degrees off square, through the grip axis 105 mm down
    M0 = (81, -9.25)  # on the grip's centre line
    C = far(M0, 94)
    a = math.atan2(U[1], U[0]) + math.radians(7)
    nc = (math.cos(a), math.sin(a))  # (z, y) out of the cut
    th = math.atan2(-nc[0], -nc[1])  # box rotation.x whose -y faces along nc
    cut(gp, box((0.08, 0.1, 0.1), (0, (C[1] + nc[1] * 50) / 1000, (C[0] + nc[0] * 50) / 1000), None, rot=(th, 0, 0)))
    uv_box(gp, 0.04)
    face_mats(gp, [grain], lambda c, n: 1 if n[2] * nc[0] + n[1] * nc[1] > 0.97 else None)
    A(split_mats(gp, {'so_endgrain'}, 'sawn_end'))
    A(gp)
    for sgn, x, s in ((1, -7, 1.0), (-1, 6, 0.8)):  # a couple of splinters left on the cut edge, bent outwards
        e = (C[0] + nc[0] * 0.2 + NB[0] * 17.3 * sgn, C[1] + nc[1] * 0.2 + NB[1] * 17.3 * sgn)
        a0 = Vector((0, nc[1] + 0.5 * NB[1] * sgn, nc[0] + 0.5 * NB[0] * sgn)).normalized()
        a2 = Vector((0, NB[1], NB[0])); a2 = (a2 - a0 * a2.dot(a0)).normalized()
        A(obox(g(x, e[1], e[0]), [tuple(a0), (1, 0, 0), tuple(a2)], (0.0018 * s, 0.0015 * s, 0.0006), grain))
    # top tang down the back of the wrist, guard tang down the belly
    def strap(line, lo, hi, w, m):
        pts = [];
        for i, p in enumerate(line):
            q0, q1 = line[max(0, i - 1)], line[min(len(line) - 1, i + 1)]
            tz, ty = q1[0] - q0[0], q1[1] - q0[1]; L = math.hypot(tz, ty); nz, ny = -ty / L, tz / L  # left normal of the polyline
            pts.append((p, nz, ny))
        poly = [(p[0] + nz * hi, p[1] + ny * hi) for p, nz, ny in pts] + [(p[0] + nz * lo, p[1] + ny * lo) for p, nz, ny in pts[::-1]]
        return side(pz(poly), w, (0, 0, 0), m, bev=0.0005)
    A(strap([(61.5, 32.8), (66, 31.5), (74, 28.5), (82, 22.5), (86.5, 17)], -0.6, 1.0, 0.009, case))  # (the back line runs top -> down: its left is outward)
    A(strap([far((67, -22.5), t) for t in (30, 16, 4)], -0.6, 1.2, 0.007, blued))  # guard tang (drawn bottom -> up)
    for (pz_, py_), nz, ny in (((85.2, 18.6), 0.78, 0.62), (far((67, -22.5), 26), -NB[0], -NB[1])):
        A(rod(g(0, py_, pz_), g(0, py_ + ny * 1.5, pz_ + nz * 1.5), 0.0021, screw, seg=10))
    # electrical tape: two wraps round the middle of the grip, the end peeling off on the left
    tc = far(M0, 30)
    u3, nb3 = (0, U[1], U[0]), (0, NB[1], NB[0])
    A(sleeve(g(0, tc[1], tc[0]), u3, nb3, 0.0174, 0.01925, 0.0062, 0.0005, 0.03, tape, tilt=0.05))
    tail_dir = [-(0.94 * nb3[i] + 0.34 * (1, 0, 0)[i]) for i in range(3)]
    t0 = [tc[0] / 1000 + U[0] * 0.0075, tc[1] / 1000 + U[1] * 0.0075]  # the last wrap's end lifts off
    A(obox([-0.01815 + tail_dir[0] * 0.0045, t0[1] + 0.004 * NB[1] + tail_dir[1] * 0.0045, t0[0] + 0.004 * NB[0] + tail_dir[2] * 0.0045],
           [tail_dir, u3, [0.34 * nb3[i] - 0.94 * (1, 0, 0)[i] for i in range(3)]], (0.0045, 0.0072, 0.00025), tape))
    # the price sticker, slapped on crooked (left side of the action, the side you see)
    sxw = 23 - 2.5 * (32 / 75.5)
    lb = box(g(0.3, 12.5, 20), g(-sxw - 0.25, 9.5, 20), sticker)
    apply_mods(lb); uv_planar(lb, (-(sxw + 0.25) / 1000, 0.0095, 0.02), (0.02, 0.0125), '-x')
    lb.rotation_euler = Euler((0.14, 0, math.atan(2.5 / 75.5)), 'YZX')  # crooked, and along the action's taper
    A(lb)

    # ======================================================== the hammers: modelled down on the strikers, then cocked
    hams = []
    for sx in (1, -1):
        hp = (sx * HAM[0], HAM[1], HAM[2])
        out = [(0, -6.5), (-4.6, -4.6), (-6.5, 0), (-9.5, 3.8), (-15.5, 6.3), (-17.5, 7.0), (-28.5, 7.0), (-30.5, 8.5), (-31, 11), (-29.5, 13.6), (-25, 14.6), (-18, 14.6),
               (-13, 15.2), (-7.5, 17.5), (-4, 21.5), (-2, 26.5), (0, 30.5), (2.8, 32.3), (5.8, 31.3), (6.6, 28), (6.3, 22), (6.6, 14), (6.6, 4), (4.6, -4.6)]
        h = [side(pz([(HAM[2] + dz, HAM[1] + dy) for dz, dy in out]), 0.0064, (hp[0] / 1000, 0, 0), case2, bev=0.001, seg=2)]
        h.append(side(pz([(HAM[2] + dz, HAM[1] + dy) for dz, dy in [(-17.5, 7.0), (-28.5, 7.0), (-30.5, 8.5), (-31, 11), (-29.5, 13.6), (-25, 14.6), (-18, 14.6), (-16.5, 11)]]),
                      0.0084, (hp[0] / 1000 - sx * 0.0004, 0, 0), case2, bev=0.0008, seg=2))  # the head, a bit wider, leaning in to the striker
        for k, (dz, dy, an) in enumerate(((0.6, 31.4, 0.5), (2.6, 32.4, 0.1), (4.6, 32.0, -0.35), (6.3, 30.0, -0.9))):  # checkering on the spur
            h.append(box(g(6.8, 0.6, 0.7), (hp[0] / 1000, (HAM[1] + dy) / 1000, (HAM[2] + dz) / 1000), case2, rot=(an, 0, 0)))
        turn(h, g(*hp), COCK)
        hams.append((h, hp))

    # ======================================================== nodes + metadata
    for p in parts + hinge + trim + firon + [fe] + sum(shells, []) + sum([h for h, _ in hams], []):
        if not p.data.uv_layers: uv_box(p, 0.04)
    for s in shells:
        apply_mods(s[0]); uv_planar(s[0], (s[0].matrix_world.translation.x, BY / 1000, BF / 1000), 0.0218, 'z')
    WZ = {'so_candy': 'a', 'so_case': 'b', 'so_blued': 'b', 'so_ribtop': 'b', 'so_breech': 'b', 'so_chamber': 'b'}  # wrap zones: a = furniture, b = metal, the rest keeps its look
    bodies = zone_join(parts, 'so_body', WZ, default='n')
    hn = part(hinge, 'hinge_wzB', pivot=g(*PIN))
    tn = part(trim, 'hinge_trim_wzN', pivot=g(*PIN)); adopt(tn, hn)
    fn = part([fe], 'forend_wzA', pivot=g(*PIN))
    fi = part(firon, 'forend_iron_wzB', pivot=g(*PIN)); adopt(fi, fn)
    sn = [part(s, f'shell{i + 1}_wzN', pivot=g(sx * BX, BY, BF)) for i, (s, sx) in enumerate(zip(shells, (1, -1)))]
    hm = [part(h, 'hammerR_wzN' if hp[0] > 0 else 'hammerL_wzN', pivot=g(*hp)) for h, hp in hams]
    meta = {'kind': 'weapon', 'id': 'sawnoff', 'paint': ['so_candy'], 'muzzle': [0, BY / 1000, MZ / 1000], 'sight': {'y': round(SIGHT_Y / 1000, 4), 'z': SIGHT_Z},
            'hatAt': [[0, round((RIB_TOP + 0.4) / 1000 + 0.04 * 0.05, 4), -0.018], 0.05],  # on the breech: brims clear the hammers, cocked or down
            'hinge': {'node': 'hinge_wzB', 'open': 0.7, 'rides': ['forend_wzA', 'shell1_wzN', 'shell2_wzN']},
            'shells': ['shell1_wzN', 'shell2_wzN'], 'hammers': ['hammerR_wzN', 'hammerL_wzN']}
    return finish('w_sawnoff', bodies + [hn, fn] + sn + hm, meta)


main(build, 'w_sawnoff')
