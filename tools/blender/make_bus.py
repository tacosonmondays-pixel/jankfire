# School bus: a conventional (hood out front) full-size school bus: 11 m box + 1 m hood, 2.44 m wide, 3.1 m tall,
# nine windows a side, black rub rails, red + amber warning lights, a stop arm, dual rear wheels. Front = +x.
# Grimy school-bus yellow, a district that doesn't exist, a magenta tag on the back.
# Collision boxes: shared/props.js PROPS.bus.  run: blender -b --python tools/blender/make_bus.py -- [--qa] [--fresh]
# Far LOD (lod1, from 60 m): far() below. farlod.main keeps the shipped lod0 byte for byte and adds it (--fresh: all new).
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import farlod


def build():
    yel = mat('bus_yellow', 0xffb400, rough=0.3, clearcoat=0.5, tex=tex_noise('bus_yellow_t', 0xffb400, var=0.07, size=32, speck=0x8a6a20, speck_p=0.025, seed=31))
    black = mat('bus_black', 0x161618, rough=0.55)
    glass = mat('bus_glass', 0x1e2c3c, rough=0.06, metal=0.6)
    chrome = mat('bus_chrome', 0xd8dde6, rough=0.12, metal=1.0)
    tire = mat('bus_tire', 0x1c1c1e, rough=0.9)
    rim = mat('bus_rim', 0xd8d8d8, rough=0.35, metal=0.4)
    red = mat('bus_red', 0xff1a2a, rough=0.2, emit=0xff1020, strength=2.5)
    amber = mat('bus_amber', 0xffa020, rough=0.2, emit=0xff9010, strength=2.5)
    head = mat('bus_head', 0xfff4d0, rough=0.2, emit=0xfff0c0, strength=2.0)
    stopm = mat('bus_stop', 0xd01020, rough=0.3)
    def side_draw(px):
        px[:] = hexrgb(0xffb400)
        text_px(px, 'JANKFIRE CO SCHOOLS', 2, 2, 2, 0x111111)
    side_t = mat('bus_lettering', 0xffffff, rough=0.35, tex=tex_canvas('bus_side_t', 232, 18, side_draw))
    def sign_draw(px):
        px[:] = hexrgb(0xffb400)
        text_px(px, 'SCHOOL BUS', 2, 2, 2, 0x111111)
    sign = mat('bus_sign', 0xffffff, rough=0.35, tex=tex_canvas('bus_sign_t', 124, 18, sign_draw))
    def stop_draw(px):
        px[:] = hexrgb(0xd01020); text_px(px, 'STOP', 4, 10, 2, 0xffffff)
    stop_t = mat('bus_stop_t', 0xffffff, rough=0.35, tex=tex_canvas('bus_stopt', 56, 34, stop_draw))
    def tag_draw(px):
        px[:] = hexrgb(0xffb400)
        text_px(px, 'JANK!', 2, 4, 3, 0xff1ad0); text_px(px, 'JANK!', 3, 5, 3, 0x6a0060)
    tag = mat('bus_tag', 0xffffff, rough=0.4, tex=tex_canvas('bus_tag_t', 96, 30, tag_draw))
    P = []; A = P.append
    L, HW = 5.5, 1.22

    # ---------------- box body with a rounded roof, wheel arches cut in
    body = side_x([(-L, 0.48), (L, 0.48), (L, 3.08), (-L, 3.08)], HW * 2, (0, 0, 0), yel, bev=0.16, seg=4)
    for x, r in ((5.75, 0.58), (-2.6, 0.6)):
        for sz in (-1, 1): cut(body, cyl(r, 0.6, (x, 0.5, sz * HW), None, axis='z', seg=32))
    A(body)
    A(side_x([(L - 0.1, 0.5), (6.42, 0.5), (6.55, 0.72), (6.5, 1.42), (6.2, 1.72), (L - 0.1, 1.78)], 2.1, (0, 0, 0), yel, bev=0.1, seg=3))  # hood
    for x, r in ((5.75, 0.55), (-2.6, 0.57)): A(cyl(r, 2.3, (x, 0.52, 0), black, axis='z', seg=24))
    # ---------------- windows, rub rails, lettering
    for sz in (-1, 1):
        z = sz * (HW + 0.005)
        for k in range(9):
            x = -4.75 + k * 1.05
            A(box((0.86, 0.78, 0.03), (x, 2.24, z), glass, bev=0.02))
            A(box((0.86, 0.03, 0.04), (x, 2.3, z), black))  # sash
        for y in (0.78, 1.16, 1.66): A(box((2 * L - 0.2, 0.07, 0.04), (0, y, z), black, bev=0.012))
        A(box((7.2, 0.3, 0.012), (-0.6, 1.41, z + sz * 0.01), side_t, rot=(0, math.pi if sz < 0 else 0, 0)))
        A(box((0.2, 0.14, 0.32), (L + 0.2, 2.5, sz * 1.45), black, bev=0.03))  # mirror
        A(tube([(L - 0.05, 2.2, sz * 1.2), (L + 0.2, 2.45, sz * 1.42)], 0.025, chrome, seg=6))
    A(box((0.04, 0.9, 1.04), (L + 0.005, 2.33, -0.56), glass, bev=0.02))  # windshield
    A(box((0.04, 0.9, 1.04), (L + 0.005, 2.33, 0.56), glass, bev=0.02))
    A(box((0.85, 1.9, 0.04), (4.85, 1.5, HW + 0.01), glass))  # folding door (right side)
    A(box((0.04, 1.9, 0.05), (4.85, 1.5, HW + 0.025), black))
    A(box((0.02, 0.3, 1.6), (L + 0.02, 2.92, 0), sign))
    A(box((0.02, 0.3, 1.6), (-L - 0.02, 2.92, 0), sign, rot=(0, math.pi, 0)))
    A(box((0.02, 0.3, 0.92), (-L - 0.02, 1.4, 0.6), tag, rot=(0, math.pi, 0.08)))
    A(box((0.04, 1.4, 0.7), (-L - 0.005, 2.1, -0.5), glass, bev=0.02))  # rear emergency door window
    A(box((0.04, 1.4, 0.7), (-L - 0.005, 2.1, 0.5), glass, bev=0.02))
    # ---------------- lights, grille, bumpers, stop arm
    for sx, xx in ((1, L + 0.02), (-1, -L - 0.02)):
        for sz in (-1, 1):
            A(cyl(0.1, 0.06, (xx, 2.92, sz * 1.0), red, axis='x', seg=14))
            A(cyl(0.1, 0.06, (xx, 2.92, sz * 0.82), amber, axis='x', seg=14))
    for sz in (-1, 1):
        A(cyl(0.11, 0.06, (6.53, 1.08, sz * 0.72), head, axis='x', seg=16))
        A(cyl(0.12, 0.08, (-L - 0.02, 1.0, sz * 0.9), red, axis='x', seg=16))
    A(box((0.06, 0.6, 1.0), (6.55, 1.06, 0), black, bev=0.03))
    for k in range(6): A(box((0.03, 0.04, 0.96), (6.58, 0.84 + k * 0.09, 0), chrome))
    A(box((0.2, 0.3, 2.4), (6.62, 0.62, 0), black, bev=0.05))
    A(box((0.2, 0.3, 2.44), (-L - 0.08, 0.62, 0), black, bev=0.05))
    oc = cyl(0.24, 0.03, (3.9, 2.0, -HW - 0.12), stopm, axis='z', seg=8, rot=(0, 0, math.pi / 8))
    A(oc); A(box((0.4, 0.26, 0.01), (3.9, 2.0, -HW - 0.14), stop_t, rot=(0, math.pi, 0)))
    A(box((0.08, 0.08, 0.14), (3.9, 2.0, -HW - 0.05), black))
    # ---------------- wheels (dual rear)
    for sz in (-1, 1):
        P.extend(wheel(0.5, 0.3, (5.75, 0.5, sz * 1.06), tire, rim, spokes=8))
        P.extend(wheel(0.52, 0.28, (-2.6, 0.52, sz * 1.1), tire, rim, spokes=8))
        P.extend(wheel(0.52, 0.28, (-2.6, 0.52, sz * 0.8), tire, rim, spokes=8))
    for p in P: uv_box(p, 0.4)
    bus = join(P, 'bus')
    root = finish('p_bus', [bus], {'kind': 'prop', 'id': 'bus', 'lod': 60})
    farlod.attach_far(root, [join(far(black, rim), 'bus_far')])
    return root


def far(black, rim):
    """lod1, the bus from 60 m on (~280 tris): the body and hood outlines with the arches cut, its windows, rub rails,
    lettering, door, stop arm, signs and lamps painted on one picture (the same yellow), black bumpers and wheel wells,
    octagon wheels (the rear duals as one wide one)."""
    W = H = 256
    X0, X1, Y0, Y1, Z0, Z1 = -5.7, 6.7, 0.3, 3.15, -1.25, 1.25
    # each side's picture: its pixel rect, the game axis that runs across it (from a0 at the left to a1) and up it
    V = {'+z': ((0, 0, 256, 60), 0, X0, X1, 1, Y0, Y1), '-z': ((0, 60, 256, 60), 0, X1, X0, 1, Y0, Y1),
         '+y': ((0, 120, 256, 52), 0, X0, X1, 2, Z0, Z1), '-y': ((104, 172, 8, 8), 0, X0, X1, 2, Z0, Z1),
         '+x': ((0, 172, 52, 60), 2, Z1, Z0, 1, Y0, Y1), '-x': ((52, 172, 52, 60), 2, Z0, Z1, 1, Y0, Y1)}
    def to_px(k, a, b):
        (rx, ry, rw, rh), _, a0, a1, _, b0, b1 = V[k]
        return rx + (a - a0) / (a1 - a0) * rw, ry + (b1 - b) / (b1 - b0) * rh
    def rect(px, k, a0, a1, b0, b1, col):
        (c0, r0), (c1, r1) = to_px(k, a0, b1), to_px(k, a1, b0)
        c0, c1 = sorted((c0, c1)); r0, r1 = sorted((r0, r1))
        c0, r0 = int(round(c0)), int(round(r0))
        px[r0:max(r0 + 1, int(round(r1))), c0:max(c0 + 1, int(round(c1)))] = hexrgb(col)
    def disc(px, k, a, b, r, col):
        cx, cy = to_px(k, a, b); (rx, ry, rw, rh), _, a0, a1, _, _, _ = V[k]
        px_disc(px, cx, cy, max(1.0, r / abs(a1 - a0) * rw), col)
    def text(px, k, s, a, b, col, w):  # centred on (a, b), squeezed into w metres
        g = np.zeros((7, 6 * len(s) - 1, 3), np.float32); text_px(g, s, 0, 0, 1, 0xffffff); m = g[:, :, 0] > 0.5
        cx, cy = to_px(k, a, b); (rx, ry, rw, rh), _, a0, a1, _, _, _ = V[k]
        wp = max(1, int(round(w / abs(a1 - a0) * rw)))
        mm = m[:, (np.arange(wp) * m.shape[1] / wp).astype(int)]
        x0, y0 = int(round(cx - wp / 2)), int(round(cy - 3.5))
        sub = px[y0:y0 + 7, x0:x0 + wp]; sub[mm[:sub.shape[0], :sub.shape[1]]] = hexrgb(col)
    GLASS, INK = 0x1c2836, 0x161618
    def draw(px):
        px[:] = hexrgb(0xffb400)
        rect(px, '-y', X0, X1, Z0, Z1, INK)  # (the underside, the arch roofs)
        for k in ('+z', '-z'):
            for i in range(9):
                x = -4.75 + i * 1.05
                rect(px, k, x - 0.43, x + 0.43, 1.85, 2.63, GLASS); rect(px, k, x - 0.43, x + 0.43, 2.285, 2.315, INK)  # windows, sash
            for y in (0.78, 1.16, 1.66): rect(px, k, -5.4, 5.4, y - 0.035, y + 0.035, INK)  # rub rails
            text(px, k, 'JANKFIRE CO SCHOOLS', -0.6, 1.41, 0x111111, 7.2)
        rect(px, '+z', 4.425, 5.275, 0.55, 2.45, GLASS); rect(px, '+z', 4.835, 4.865, 0.55, 2.45, INK)  # the folding door
        disc(px, '-z', 3.9, 2.0, 0.24, 0xd01020); rect(px, '-z', 3.78, 4.02, 1.98, 2.02, 0xffffff)  # the stop arm, folded
        for k in ('+x', '-x'):
            text(px, k, 'SCHOOL BUS', 0.0, 2.92, 0x111111, 1.5)
            for z, c in ((1.0, 0xff1a2a), (0.82, 0xffa020), (-0.82, 0xffa020), (-1.0, 0xff1a2a)): disc(px, k, z, 2.92, 0.1, c)
        for z in (-0.56, 0.56): rect(px, '+x', z - 0.52, z + 0.52, 1.88, 2.78, GLASS)  # windscreen
        rect(px, '+x', -0.5, 0.5, 0.76, 1.36, INK)  # grille
        for i in range(6): rect(px, '+x', -0.48, 0.48, 0.825 + i * 0.09, 0.855 + i * 0.09, 0xc8ccd4)
        for z in (-0.72, 0.72): disc(px, '+x', z, 1.08, 0.11, 0xfff4d0)  # headlamps
        for z in (-0.5, 0.5): rect(px, '-x', z - 0.35, z + 0.35, 1.4, 2.8, GLASS)  # the emergency door's windows
        for z in (-0.9, 0.9): disc(px, '-x', z, 1.0, 0.12, 0xff1a2a)  # tail lamps
        text(px, '-x', 'JANK!', 0.6, 1.4, 0xff1ad0, 0.9)
    pic = mat('bus_far', 0xffffff, rough=0.3, tex=tex_canvas('bus_far_t', W, H, draw))
    def uv_views(o):  # each face takes the picture of the side it looks at
        me = o.data; uv = (me.uv_layers.active or me.uv_layers.new()).data; mw = o.matrix_world; nm = mw.to_3x3()
        for poly in me.polygons:
            n = nm @ poly.normal; g = (n.x, n.z, -n.y); i = max(range(3), key=lambda j: abs(g[j]))
            (rx, ry, rw, rh), ia, a0, a1, ib, b0, b1 = V[('+' if g[i] > 0 else '-') + 'xyz'[i]]
            for li in poly.loop_indices:
                v = mw @ me.vertices[me.loops[li].vertex_index].co; q = (v.x, v.z, -v.y)
                uv[li].uv = ((rx + (q[ia] - a0) / (a1 - a0) * rw) / W, 1 - (ry + (b1 - q[ib]) / (b1 - b0) * rh) / H)
    arch = lambda cx, cy, r, angs: [(cx + r * math.cos(math.radians(t)), cy + r * math.sin(math.radians(t))) for t in angs]
    out = [(-5.5, 0.48), (-3.2, 0.48)] + arch(-2.6, 0.5, 0.6, (160, 120, 90, 60, 20)) + [(-2.0, 0.48), (5.17, 0.48)] + \
          arch(5.75, 0.5, 0.58, (160, 130)) + [(5.5, 1.023), (5.5, 2.96), (5.38, 3.08), (-5.38, 3.08), (-5.5, 2.96)]
    F = [side_x(out, 2.44, (0, 0, 0), pic, name='far_body'),
         side_x([(5.4, 0.5), (6.42, 0.5), (6.55, 0.72), (6.5, 1.42), (6.2, 1.72), (5.4, 1.78)], 2.1, (0, 0, 0), pic, name='far_hood')]
    for o in F: apply_mods(o); uv_views(o)
    D = [box((1.2, 0.63, 1.34), (-2.6, 0.805, 0), black, name='far_well'),  # wheel wells, just touching the tyres
         box((1.16, 0.61, 1.84), (5.75, 0.795, 0), black, name='far_well'),
         box((0.2, 0.3, 2.4), (6.62, 0.62, 0), black, name='far_bumper'), box((0.2, 0.3, 2.43), (-5.58, 0.62, 0), black, name='far_bumper')]
    for sz in (-1, 1):
        D.append(farlod.far_wheel(0.5, 0.3, (5.75, 0.5, sz * 1.06), black, rim))
        D.append(farlod.far_wheel(0.52, 0.58, (-2.6, 0.52, sz * 0.95), black, rim))  # (the duals)
    for o in D: uv_box(o, 0.4)
    return F + D


farlod.main(build, 'p_bus')
