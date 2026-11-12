# The Zombies roller shutter (every Zombies map: public/js/zombies.js, one per buyable door): a mall security shutter
# in its 4 x 3 m opening. Fat ribbed steel slats (seen from both rooms, so both faces are the same shape), a bottom rail
# with lift handles and a padlock eye, guide channels down both sides, a rounded hood with hazard stripes over the
# coil (it covers the map's striped housing box), and a plywood board hung on the slats with S-hooks, front and back:
# the game paints the area's name and price on it.
# Door space, metres: x along the opening (-2 .. 2), y up from the door's floor, z across the wall (both faces are
# fronts). The game turns it 90 degrees for doors in walls that run along z.
# frame    channels + hood, origin 0,0,0. stays when the door is bought.
# curtain  slats, rail, boards: origin = the top of the opening (meta curtain.top), so scaling y rolls it up into the hood.
# meta: curtain {top}, sign {y, w, h, z} (the boards' face: centre height, size, depth of the front face; the back is -z).
# run: blender -b --python tools/blender/make_zmshutter.py   (-- --no-sheet  -- --no-export  -- --qa)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib
from bottom_kit import Atlas, grime, crust, uv_fit, xform, write, tw
from sidekit import bake_normals, text_c, smiley
from zmkit import grain, poly_fill, qa, seg_dist, star

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HW, TOP = 1.97, 2.95                   # the curtain's half width (into the channels), the top of the opening
SH, SD, SN = 0.1, 0.085, 0.05          # slat height, half depth at the rib, half depth at the joint
RAIL = 0.09                            # bottom rail height
SIGN = (1.72, 2.4, 1.05, 0.0)          # board centre y, width, height (z filled in below)
YEL, INK, PINK, CYAN = 0xffd21a, 0x15130f, 0xff4fd8, 0x4fd8ff

# atlas 256 x 192: curtain front (0,0,128,96), back (128,0,128,96), plywood (0,96,128,48), hazard (128,96,128,24),
# rail (128,120,128,16)
AT = {'front': (0, 0, 128, 96), 'back': (128, 0, 128, 96), 'ply': (0, 96, 128, 48), 'hazard': (128, 96, 128, 24), 'rail': (128, 120, 128, 16)}


def tag(px, pts, col, w=1.6):
    for a, b in zip(pts, pts[1:]): px_line(px, a[0], a[1], b[0], b[1], col, w)


def paint():
    A = Atlas('zs_t', 256, 192, bg=0xb8c0c8)
    for k, sd in (('front', 3), ('back', 4)):
        p = A.sub(*AT[k])
        crust(p, 0xb4bcc6, 0.06, seed=sd)
        r = np.random.default_rng(sd)
        for x in r.integers(0, 128, 9):  # rust streaks running down from the joints
            y0 = int(r.integers(0, 70)); L = int(r.integers(6, 24))
            p[y0:y0 + L, x:x + 1] = p[y0:y0 + L, x:x + 1] * 0.5 + hexrgb(0x8a4a1a) * 0.5
        grime(p, 0x6a6a70, p=0.07, seed=sd + 10, blob=2)
        p[-10:] = p[-10:] * 0.7 + hexrgb(0x3a3024) * 0.3  # dirt kicked up the bottom
    f = A.sub(*AT['front'])  # graffiti round where the board hangs: a pink tag, a smiley, CLOSED (FOREVER)
    tag(f, [(6, 80), (10, 66), (16, 78), (20, 64), (26, 80), (30, 70)], PINK, 2.2)
    tag(f, [(98, 82), (104, 72), (112, 86), (120, 70)], CYAN, 2.0)
    smiley(f, 114, 16, 7, face=0xffe14d)
    write(f, 'CLOSED', 4, 4, 1, INK); write(f, '(FOREVER)', 4, 13, 1, INK)
    b = A.sub(*AT['back'])
    tag(b, [(4, 20), (12, 8), (16, 22), (24, 10), (30, 18)], 0x7dff4f, 2.0)
    write(b, 'NO', 96, 76, 1, PINK); write(b, 'LOITERING', 76, 84, 1, PINK)
    write(b, 'SALE', 98, 10, 1, 0xffffff)
    p = A.sub(*AT['ply'])
    grain(p, 0xd8b078, 0x9a7040, seed=7, lines=6, knots=2, streak=0.3, cracks=3, crack_col=0x5a3a18)
    h = A.sub(*AT['hazard'])
    h[:] = hexrgb(YEL)
    for k in range(-3, 22): poly_fill(h, [(k * 12, 24), (k * 12 + 6, 24), (k * 12 + 18, 0), (k * 12 + 12, 0)], INK)
    grime(h, 0x6a5410, p=0.15, seed=21, blob=3)
    rl = A.sub(*AT['rail'])
    rl[:] = hexrgb(YEL)
    for k in range(-2, 24): poly_fill(rl, [(k * 8, 16), (k * 8 + 4, 16), (k * 8 + 12, 0), (k * 8 + 8, 0)], INK)
    return A


def materials():
    M = {}
    A = paint(); M['A'] = A
    M['slat'] = mat('zs_slat', 0xffffff, rough=0.32, metal=0.55, clearcoat=0.4, tex=A.image())
    M['paint'] = mat('zs_paint', 0xffffff, rough=0.3, clearcoat=0.8, tex=A.image())  # the hood and rail: candy hazard paint
    M['ply'] = mat('zs_ply', 0xffffff, rough=0.7, tex=A.image())
    M['steel'] = mat('zs_steel', 0x8e949c, rough=0.3, metal=0.95, tex=tex_noise('zs_steel_t', 0x8e949c, var=0.08, size=16, speck=0x6a4a2a, speck_p=0.08, seed=31))
    M['chrome'] = mat('zs_chrome', 0xd4d8de, rough=0.12, metal=1.0)
    M['rubber'] = mat('zs_rubber', 0x1e1c1c, rough=0.8)
    M['lock'] = mat('zs_lock', PINK, rough=0.18, clearcoat=1.0)
    return M


def rect(M, k): return M['A'].rect(*AT[k])


def uv_sides(o, lo, hi, rf, rb):
    """each face planar from its own side of the curtain: +z faces onto rf, -z faces onto rb (mirrored, so it reads)"""
    apply_mods(o); bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world
    for pg in me.polygons:
        c = mw @ pg.center; back = -c.y < 0  # (game z = -blender y)
        r = rb if back else rf
        nn = mw.to_3x3() @ pg.normal
        end = abs(nn.x) > 0.7  # (the slats' ends: seen from the side, a sliver of the edge)
        flat = abs(nn.z) > 0.7
        for li in pg.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            u = (p.x - lo[0]) / (hi[0] - lo[0]); v = (p.z - lo[1]) / (hi[1] - lo[1])
            if end: u = (0.02 if p.x < 0 else 0.98) + (-p.y) * 0.1
            if flat: v = v + (-p.y) * 0.1  # (the necks between slats: flat, seen from above)
            if back: u = 1 - u
            uv[li].uv = (r[0] + u * (r[2] - r[0]), r[1] + v * (r[3] - r[1]))
    return o


def slat(y0, h, M):
    """one slat: a fat rib on both faces, necked where it hooks into the next one, extruded the curtain's width"""
    prof = [(0.0, SN), (0.18 * h, SD - 0.012), (0.4 * h, SD), (0.62 * h, SD), (0.84 * h, SD - 0.012), (h, SN)]
    pts = [(y0 + y, z) for y, z in prof] + [(y0 + y, -z) for y, z in reversed(prof)]
    bm = bmesh.new()
    L = [bm.verts.new(gv(-HW, y, z)) for y, z in pts]; R = [bm.verts.new(gv(HW, y, z)) for y, z in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((L[i], L[j], R[j], R[i]))
    bm.faces.new(L); bm.faces.new(R[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj('slat', bm, M['slat']); smooth(o, 50)
    return o


def build_curtain(M):
    P = []
    lo, hi = (-HW, 0.0), (HW, TOP)
    n = int(round((TOP - RAIL) / SH))
    sh = (TOP - RAIL) / n
    for k in range(n):
        o = slat(RAIL + k * sh, sh, M)
        uv_sides(o, lo, hi, rect(M, 'front'), rect(M, 'back'))
        P.append(o)
    # the bottom rail: a hazard-painted bar, a rubber lip under it, lift handles both sides, a padlock eye at the right
    r = box((2 * HW, RAIL - 0.012, 2 * (SD + 0.02)), (0, 0.012 + (RAIL - 0.012) / 2, 0), M['paint'], bev=0.008, seg=2, name='rail')
    apply_mods(r); uv_fit(r, rect(M, 'rail')); P.append(r)
    P.append(box((2 * HW - 0.02, 0.012, 0.05), (0, 0.006, 0), M['rubber'], bev=0.003, seg=1))
    for sz in (-1, 1):
        for x in (-0.5, 0.5):
            P.append(tube([(x - 0.08, 0.05, sz * (SD + 0.02)), (x - 0.06, 0.05, sz * (SD + 0.06)), (x + 0.06, 0.05, sz * (SD + 0.06)), (x + 0.08, 0.05, sz * (SD + 0.02))], 0.011, M['chrome'], seg=8, name='handle'))
    P.append(box((0.06, 0.07, 0.012), (1.6, 0.035, SD + 0.026), M['steel'], bev=0.002, seg=1))  # the hasp plate
    P.append(tube([(1.6, 0.012, SD + 0.032), (1.6, 0.012, SD + 0.06), (1.6, 0.035, SD + 0.07), (1.6, 0.058, SD + 0.06), (1.6, 0.058, SD + 0.032)], 0.007, M['chrome'], seg=6, name='eye'))
    lk = box((0.06, 0.07, 0.025), (1.6, -0.0, SD + 0.075), M['lock'], bev=0.008, seg=2); xform([lk], move=(0, 0.035, 0)); P.append(lk)
    # the plywood boards, hung on two S-hooks off a slat, front and back: the game paints on them
    cy, w, h, _ = SIGN
    for sz in (-1, 1):
        zb = sz * (SD + 0.012)
        b = box((w, h, 0.016), (0, cy, zb), M['ply'], bev=0.004, seg=1, name='board')
        apply_mods(b); uv_fit(b, rect(M, 'ply')); P.append(b)
        for x in (-w * 0.38, w * 0.38):
            y0 = cy + h / 2
            P.append(tube([(x, y0 - 0.03, zb), (x, y0 + 0.05, zb), (x, y0 + 0.09, sz * (SD - 0.01)), (x, y0 + 0.12, sz * (SD - 0.04))], 0.006, M['steel'], seg=6, name='hook'))
    for o in P:
        apply_mods(o)
        if not o.data.uv_layers or o.name.split('.')[0] in ('handle', 'eye', 'hook'): uv_box(o, 0.2)
    return P


def build_frame(M):
    P = []
    # guide channels: a web against the wall's end, two flanges either side of the slats
    for sx in (-1, 1):
        x0 = sx * 1.992
        P.append(box((0.006, TOP, 0.24), (x0, TOP / 2, 0), M['steel'], bev=0.002, seg=1))
        for sz in (-1, 1): P.append(box((0.054, TOP, 0.008), (sx * 1.962, TOP / 2, sz * 0.112), M['steel'], bev=0.002, seg=1))
        for y in (0.4, 1.5, 2.6):
            for sz in (-1, 1): P.append(cyl(0.008, 0.006, (sx * 1.965, y, sz * 0.118), M['chrome'], axis='z', seg=6))
    # the hood: a rounded box over the coil, hazard paint, chrome end plates with the axle boss
    r = 0.11; L = 4.26; yb, yt, zh = 2.93, 3.33, 0.28
    prof = []
    for cy_, cz_, a0 in ((yt - r, zh - r, 0), (yt - r, -zh + r, 90)):
        for i in range(4): a = math.radians(a0 + 30 * i); prof.append((cy_ + r * math.sin(a), cz_ + r * math.cos(a)))
    prof = [(yb, zh)] + prof + [(yb, -zh)]
    bm = bmesh.new(); Lv = [bm.verts.new(gv(-L / 2, y, z)) for y, z in prof]; Rv = [bm.verts.new(gv(L / 2, y, z)) for y, z in prof]
    n = len(prof)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((Lv[i], Lv[j], Rv[j], Rv[i]))
    bm.faces.new(Lv); bm.faces.new(Rv[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    hood = lib._obj('hood', bm, M['paint']); smooth(hood, 40)
    uv_fit(hood, rect(M, 'hazard')); P.append(hood)
    for sx in (-1, 1):
        P.append(box((0.012, yt - yb + 0.02, 2 * zh + 0.02), (sx * (L / 2 + 0.006), (yb + yt) / 2, 0), M['chrome'], bev=0.004, seg=1))
        P.append(cyl(0.05, 0.03, (sx * (L / 2 + 0.02), (yb + yt) / 2 + 0.02, 0), M['steel'], axis='x', seg=10, bev=0.004))
        for y in (yb + 0.08, yt - 0.08):
            for sz in (-1, 1): P.append(cyl(0.009, 0.01, (sx * (L / 2 + 0.014), y, sz * (zh - 0.06)), M['steel'], axis='x', seg=6))
    for o in P:
        apply_mods(o)
        if not o.data.uv_layers: uv_box(o, 0.2)
    return P


def build():
    M = materials()
    C = build_curtain(M); bake_normals(C)
    curtain = part(C, 'curtain', pivot=(0, TOP, 0))
    F = build_frame(M); bake_normals(F)
    frame = part(F, 'frame', pivot=(0, 0, 0))
    meta = {'kind': 'prop', 'id': 'zmshutter', 'curtain': {'top': TOP}, 'sign': {'y': SIGN[0], 'w': SIGN[1], 'h': SIGN[2], 'z': SD + 0.012 + 0.008}}
    root = finish('x_zmshutter', [frame, curtain], meta)
    if '--qa' in ARGV: qa([frame, curtain])
    return root


if __name__ == '__main__':
    main(build, 'x_zmshutter', exposure=-0.2)
