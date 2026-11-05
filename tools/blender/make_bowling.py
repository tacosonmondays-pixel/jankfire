# Bowling Ball Launcher: a backyard pneumatic cannon, built like the real ones: a big schedule-40 PVC barrel with a
# coupling at the mouth and a domed cap at the back, an air tank (a red extinguisher-style cylinder) strapped under
# it, a green sprinkler valve fired by a doorbell button and a taped-on 9 V battery, a pressure gauge you can read,
# and a bowling pin glued on as the front sight. Loaded with a swirly bowling ball (finger holes up).
# Game units (metres) directly: the ball is the game's size, everything else is sized off it.
# run: blender -b --python tools/blender/make_bowling.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *


def gauge(px):
    h, w = px.shape[:2]; c = w / 2
    px_disc(px, c, c, c - 0.5, 0xf4f4f0)
    px_disc(px, c, c, c - 4, 0x39c84a, r_in=c - 9, a0=-2.3, a1=0.2)
    px_disc(px, c, c, c - 4, 0xffd21a, r_in=c - 9, a0=0.2, a1=1.2)
    px_disc(px, c, c, c - 4, 0xe8281e, r_in=c - 9, a0=1.2, a1=2.3)
    for i in range(9):
        th = -2.3 + 4.6 * i / 8
        px_line(px, c + math.sin(th) * (c - 3), c - math.cos(th) * (c - 3), c + math.sin(th) * (c - 12), c - math.cos(th) * (c - 12), 0x111111, 1.5)
    text_px(px, 'PSI', int(c - 8), int(c + 9), 1, 0x111111)
    th = 2.0  # the needle is in the red. of course it is
    px_line(px, c, c, c + math.sin(th) * (c - 8), c - math.cos(th) * (c - 8), 0xe0102a, 2.4)
    px_disc(px, c, c, 3, 0x111111)


def swirl(px):
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w] / w
    v = np.sin(6 * xx + 3 * np.sin(5 * yy + 2 * np.sin(4 * xx))) + np.sin(7 * yy + 2 * np.cos(6 * xx))
    t = (v - v.min()) / (np.ptp(v) + 1e-6)
    a, b, c = hexrgb(0x2a3aa8), hexrgb(0x6b7bff), hexrgb(0xb070ff)
    px[:] = np.where(t[:, :, None] < 0.5, a + (b - a) * (t[:, :, None] * 2), b + (c - b) * ((t[:, :, None] - 0.5) * 2))


def build():
    pvc = mat('bw_pvc', 0xdcdcd2, rough=0.45, tex=tex_noise('bw_pvc_t', 0xdcdcd2, var=0.06, size=32, speck=0xa8a89a, speck_p=0.03, seed=111))
    cap = mat('bw_cap', 0xc8c8be, rough=0.45)
    inner = mat('bw_inner', 0x3a3a40, rough=0.8)
    blue = mat('bw_coupling', 0x6b7bff, rough=0.2, clearcoat=0.8)
    tankm = mat('bw_tank', 0xd81e28, rough=0.2, clearcoat=0.8)
    tape = mat('bw_tape', 0x9aa0a8, rough=0.45, metal=0.3, tex=tex_noise('bw_tape_t', 0x9aa0a8, var=0.15, size=16, seed=112))
    valve = mat('bw_valve', 0x2a8a3a, rough=0.35)
    black = mat('bw_black', 0x111114, rough=0.5)
    brass = mat('bw_brass', 0xe0ad3c, rough=0.25, metal=1.0)
    orange = mat('bw_grip', 0xff7a1a, rough=0.35, tex=tex_noise('bw_grip_t', 0xff7a1a, var=0.12, size=16, seed=113))
    button = mat('bw_button', 0xff1a2a, rough=0.2, clearcoat=1.0)
    batt = mat('bw_battery', 0x1a1a1a, rough=0.4)
    copper = mat('bw_copper', 0xd08040, rough=0.3, metal=1.0)
    wire_r = mat('bw_wire_r', 0xe0202a, rough=0.5); wire_k = mat('bw_wire_k', 0x111111, rough=0.5)
    pin_w = mat('bw_pin', 0xf8f8f8, rough=0.2, clearcoat=1.0); pin_r = mat('bw_pin_r', 0xe0202a, rough=0.2, clearcoat=1.0)
    ballm = mat('bw_ball', 0x6b7bff, rough=0.08, clearcoat=1.0, tex=tex_canvas('bw_ball_t', 64, 64, swirl))
    hole = mat('bw_hole', 0x05050a, rough=0.6)
    gface = mat('bw_gauge', 0xffffff, rough=0.2, tex=tex_canvas('bw_gauge_t', 48, 48, gauge))
    def print_draw(px):
        px[:] = hexrgb(0xdcdcd2); text_px(px, '10IN SCH40 PVC  NOT FOR COMPRESSED AIR', 2, 1, 1, 0x3a3aa0)
    printm = mat('bw_print', 0xffffff, rough=0.45, tex=tex_canvas('bw_print_t', 232, 9, print_draw))
    def strike(px):
        px[:] = hexrgb(0x111111); px[2:-2, 2:-2] = hexrgb(0xff4fd8)
        text_px(px, 'STRIKE!', 5, 6, 2, 0xffe14d)
    strike_t = mat('bw_strike', 0xffffff, rough=0.35, tex=tex_canvas('bw_strike_t', 94, 26, strike))
    def label(px):
        px[:] = hexrgb(0xf4f4f0); text_px(px, 'AIR ONLY', 3, 3, 1, 0x111111); text_px(px, 'MAX 120 PSI', 3, 12, 1, 0xe0102a)
    label_t = mat('bw_label', 0xffffff, rough=0.4, tex=tex_canvas('bw_label_t', 70, 21, label))
    parts, decals = [], []
    A = parts.append

    # ---------------- barrel: PVC pipe (hollow at the mouth), blue coupling, domed cap, the printing on the side
    A(lathe([(0, 0.05), (0.145, 0.05), (0.145, -0.556), (0.155, -0.556), (0.155, 0.09)], (0, 0, 0), pvc, seg=32))
    A(lathe([(0.1445, 0.04), (0.1445, -0.55)], (0, 0, 0), inner, seg=32))
    A(lathe([(0.149, -0.55), (0.149, -0.585), (0.172, -0.585), (0.176, -0.578), (0.176, -0.478), (0.168, -0.472), (0.156, -0.472)], (0, 0, 0), blue, seg=32))
    A(lathe([(0.157, 0.05), (0.168, 0.055), (0.168, 0.135), (0.152, 0.158), (0.105, 0.174), (0.0, 0.18)], (0, 0, 0), cap, seg=32))
    pr = box((0.001, 0.018, 0.46), (-0.1525, 0.035, -0.23), printm, rot=(0, math.pi, 0)); A(pr); decals.append((pr, (0.46, 0.018)))
    st = box((0.001, 0.05, 0.13), (-0.1535, -0.035, -0.3), strike_t, rot=(0, math.pi, 0)); A(st); decals.append((st, (0.13, 0.05)))
    # ---------------- bowling pin front sight
    A(lathe([(0.0, 0.0), (0.008, 0.001), (0.012, 0.013), (0.009, 0.03), (0.0055, 0.039), (0.0075, 0.05), (0.006, 0.059), (0.0, 0.061)], (0, 0.152, -0.44), pin_w, seg=12, axis='y'))
    for y0 in (0.034, 0.039): A(lathe([(0.0064, y0), (0.0062, y0 + 0.0025)], (0, 0.152, -0.44), pin_r, seg=12, axis='y'))
    # ---------------- air tank strapped underneath, its label, tyre valve
    tank_y = -0.262
    A(lathe([(0.0, -0.5), (0.05, -0.496), (0.074, -0.47), (0.075, -0.13), (0.06, -0.1), (0.022, -0.085), (0.0, -0.085)], (0, tank_y, 0), tankm, seg=24))
    lb = box((0.001, 0.05, 0.16), (-0.0755, tank_y, -0.3), label_t, rot=(0, math.pi, 0)); A(lb); decals.append((lb, (0.16, 0.05)))
    A(cyl(0.006, 0.03, (-0.07, tank_y + 0.03, -0.42), black, axis='x', seg=8, rot=(0, 0, 0.4)))
    for z in (-0.42, -0.19):  # duct-tape straps: round the barrel, round the tank, a web between
        A(lathe([(0.157, z - 0.018), (0.157, z + 0.018)], (0, 0, 0), tape, seg=32))
        A(lathe([(0.077, z - 0.018), (0.077, z + 0.018)], (0, tank_y, 0), tape, seg=24))
        for sx in (-1, 1): A(box((0.004, 0.13, 0.036), (sx * 0.07, -0.16, z), tape, rot=(0, 0, sx * 0.5)))
    # ---------------- sprinkler valve + solenoid, elbow up into the barrel, wires, grip with a doorbell button, 9 V
    A(lathe([(0.012, -0.09), (0.012, -0.07)], (0, tank_y, 0), brass, seg=12))
    A(box((0.07, 0.06, 0.07), (0, tank_y, -0.035), valve, bev=0.01))
    A(cyl(0.018, 0.04, (0, tank_y + 0.05, -0.035), black, axis='y', seg=14, bev=0.004))
    A(sweep([(0, tank_y + 0.0, 0.0), (0, tank_y + 0.02, 0.03), (0, -0.2, 0.05), (0, -0.152, 0.055)], 0.02, pvc, seg=14))
    A(sweep([(0.006, tank_y + 0.07, -0.035), (0.03, -0.2, 0.02), (0.012, -0.19, 0.06)], 0.0025, wire_r, seg=5))
    A(sweep([(-0.006, tank_y + 0.07, -0.035), (-0.03, -0.21, 0.02), (-0.016, -0.2, 0.065)], 0.0025, wire_k, seg=5))
    A(side([(0.04, -0.15), (0.1, -0.15), (0.13, -0.3), (0.125, -0.315), (0.095, -0.318), (0.086, -0.305), (0.076, -0.26), (0.08, -0.245), (0.07, -0.225), (0.072, -0.21), (0.062, -0.19)], 0.034, (0, 0, 0), orange, bev=0.007, seg=3))
    A(cyl(0.012, 0.012, (0, -0.185, 0.046), button, axis='z', seg=14, bev=0.003, rot=(0.3, 0, 0)))
    A(cyl(0.016, 0.008, (0, -0.184, 0.052), black, axis='z', seg=14, rot=(0.3, 0, 0)))
    A(box((0.017, 0.048, 0.026), (-0.026, -0.245, 0.095), batt, bev=0.002))
    for dx in (-0.004, 0.004): A(cyl(0.0035, 0.006, (-0.026 + dx, -0.218, 0.095), copper, axis='y', seg=8))
    A(box((0.024, 0.016, 0.03), (-0.026, -0.25, 0.095), tape))  # taped on, obviously
    # ---------------- pressure gauge on the cap, tilted up at you
    gx, gy, gz = 0, 0.168, 0.124
    A(cyl(0.008, 0.04, (0, 0.15, 0.13), brass, axis='y', seg=10))
    gb = cyl(0.036, 0.022, (0, 0, 0), brass, axis='z', seg=24, bev=0.003)
    gfc = cyl(0.031, 0.002, (0, 0, 0.012), gface, axis='z', seg=24)
    apply_mods(gfc); uv_planar(gfc, (0, 0, 0.012), 0.062, 'z')
    gg = join([gb, gfc], 'gauge')
    gg.location = gv(gx, gy + 0.02, gz + 0.015)
    gg.rotation_euler = Euler((-0.75, 0, 0), 'XYZ')  # tilt the face up and back at you
    A(gg)
    # ---------------- the ball: swirly, glossy, three finger holes facing up at you
    bc = (0, 0.0, -0.47)
    ball_o = ball(0.14, bc, ballm, seg=28, rings=18)
    for dvec, r in (((-0.25, 0.85, 0.45), 0.012), ((0.25, 0.85, 0.45), 0.012), ((0.0, 0.62, 0.78), 0.014)):
        l = math.sqrt(sum(v * v for v in dvec)); dvec = [v / l for v in dvec]
        cut(ball_o, rod(tuple(bc[i] + dvec[i] * 0.17 for i in range(3)), tuple(bc[i] + dvec[i] * 0.09 for i in range(3)), r, None, seg=12))
    A(ball_o)
    for p in parts: uv_box(p, 0.08)
    for o, sz in decals:
        apply_mods(o); c = o.matrix_world.translation; uv_planar(o, (c.x, c.z, -c.y), sz, '-x')
    WZ = {'bw_pvc': 'a', 'bw_cap': 'a', 'bw_coupling': 'b', 'bw_tank': 'b', 'bw_valve': 'b', 'bw_black': 'b', 'bw_grip': 'b', 'bw_ball': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'bowling_body', WZ, default='n', rule=None)
    meta = {'kind': 'weapon', 'id': 'bowling', 'paint': ['bw_coupling', 'bw_ball'], 'muzzle': [0, 0, -0.6], 'hatAt': [[0, 0.157, -0.12], 0.15]}
    return finish('w_bowling', bodies + [], meta)


main(build, 'w_bowling')
