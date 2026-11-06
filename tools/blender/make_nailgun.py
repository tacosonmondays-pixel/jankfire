# Nail Gun: a 21-degree pneumatic framing nailer, real millimetres x1.6, held the way everyone pretends to hold one:
# turned so the drive points forward. The piston housing becomes the "receiver", the handle hangs down as a pistol
# grip, and the stick magazine of full-round-head nails rakes back under the nose at its real 21 degrees, bolted to the
# grip's end cap like the real ones. Real parts: contact-trip nose with teeth, jam-clearing latch, depth-of-drive
# wheel, exhaust deflector, cap bolts, rubber overmould, brass 1/4in air plug, rafter hook, a follower you pull back.
# Made fun: candy-orange paint, a spirit level gaffer-taped on top as the sight, and the stickers say what they think.
# run: blender -b --python tools/blender/make_nailgun.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.6 / 1000
NOSE_Z, AXIS_Y = -0.358, 0.04  # the nose tip is the muzzle; the drive axis is the bore line
def Zu(u): return NOSE_Z + u * S          # u: mm back from the nose tip along the drive axis
def Yv(v): return AXIS_Y - v * S          # v: mm down from the drive axis (towards the grip)
def UV(u, v): return (Zu(u), Yv(v))       # side() wants (z, y)
def W(mm): return mm * S
RAKE = math.radians(21)
LEVEL_TOP = 84  # mm above the axis: the top of the spirit level's vial (the sight line)


def build():
    orange = mat('ng_orange', 0xff6f3c, rough=0.18, clearcoat=1.0, tex=tex_noise('ng_orange_t', 0xff6f3c, var=0.05, size=32, speck=0xd8501c, speck_p=0.03, seed=401))
    mag = mat('ng_magnesium', 0x7c828a, rough=0.38, metal=0.75, tex=tex_noise('ng_mag_t', 0x7c828a, var=0.1, size=32, seed=402))
    alu = mat('ng_alu', 0xb8bec6, rough=0.28, metal=0.9)
    steel = mat('ng_steel', 0x5a5f66, rough=0.3, metal=0.9)
    black = mat('ng_black', 0x18181c, rough=0.45, clearcoat=0.3)
    rubber = mat('ng_rubber', 0x1c1c20, rough=0.85, tex=tex_noise('ng_rubber_t', 0x202024, var=0.18, size=16, seed=403))
    brass = mat('ng_brass', 0xe0ad3c, rough=0.2, metal=1.0)
    nailm = mat('ng_nail', 0xc8d0d8, rough=0.22, metal=1.0)
    paper = mat('ng_collation', 0xd8b878, rough=0.7)  # the paper strip the nails are glued to
    redt = mat('ng_trigger', 0xe0202a, rough=0.3, clearcoat=0.6)
    tape = mat('ng_tape', 0x2a2a2e, rough=0.6, tex=tex_noise('ng_tape_t', 0x2a2a2e, var=0.2, size=16, seed=404))
    vial = mat('ng_vial', 0x9dff3a, rough=0.05, alpha=0.6, emit=0x7dff2a, strength=0.6)
    bubble = mat('ng_bubble', 0xf4fff0, rough=0.05, emit=0xffffff, strength=0.4)
    def lbl(px):
        px[:] = hexrgb(0x18181c); px[1:-1, 1:-1] = hexrgb(0xffe14d)
        text_px(px, 'JANKFIRE', 3, 3, 1, 0x18181c); text_px(px, 'NAILER 21', 3, 12, 1, 0x18181c)
    label = mat('ng_label', 0xffffff, rough=0.35, tex=tex_canvas('ng_label_t', 72, 21, lbl))
    def warn(px):
        px[:] = hexrgb(0xf4f4f0); px[:4] = hexrgb(0xe0202a)
        text_px(px, 'WARNING', 2, 0, 1, 0xf4f4f0); text_px(px, 'NOT A GUN', 2, 6, 1, 0x111111); text_px(px, 'MOSTLY', 2, 14, 1, 0xe0202a)
    warning = mat('ng_warning', 0xffffff, rough=0.4, tex=tex_canvas('ng_warn_t', 48, 22, warn))
    parts, decals = [], []
    A = parts.append

    # ---------------- piston housing (the "receiver"): front flange, waist, cap with bolts, exhaust deflector
    A(lathe([(W(30), Zu(118)), (W(46), Zu(120)), (W(47), Zu(134)), (W(44), Zu(140)), (W(42), Zu(190)), (W(44), Zu(250)), (W(45.5), Zu(276)), (W(45.5), Zu(284))],
            (0, AXIS_Y, 0), orange, seg=28))
    A(lathe([(W(46.5), Zu(283)), (W(47), Zu(287)), (W(46), Zu(300)), (W(40), Zu(305)), (W(18), Zu(308)), (0, Zu(308))], (0, AXIS_Y, 0), black, seg=28))
    for i in range(4):  # cap bolts round the back
        a = math.pi / 4 + i * math.pi / 2
        A(cyl(W(4.5), W(5), (math.cos(a) * W(37), AXIS_Y + math.sin(a) * W(37), Zu(306.5)), steel, axis='z', seg=6))
    # exhaust deflector: a ring of slots on top of the cap you can turn
    A(lathe([(W(26), Zu(296)), (W(28), Zu(297)), (W(28), Zu(304)), (W(24), Zu(306))], (0, AXIS_Y + W(26), 0), black, seg=20, axis='z'))
    for i in range(5): A(box((W(3), W(9), W(10)), (W(-12 + i * 6), AXIS_Y + W(56), Zu(300)), steel, bev=0.0006))
    # front flange bolts
    for i in range(6):
        a = i * math.pi / 3 + 0.3
        A(cyl(W(3), W(4), (math.cos(a) * W(42), AXIS_Y + math.sin(a) * W(42), Zu(118)), steel, axis='z', seg=6))
    # ---------------- nose: drive guide (magnesium), jam latch, depth wheel, contact trip with teeth
    A(side([UV(22, -20), UV(118, -30), UV(122, -24), UV(122, 34), UV(108, 38), UV(22, 22)], W(30), (0, 0, 0), mag, bev=0.0015, seg=2))
    A(side([UV(30, -12), UV(108, -20), UV(108, 26), UV(30, 16)], W(36), (0, 0, 0), mag, bev=0.002, seg=2))  # the gate over the drive channel
    A(box((W(6), W(14), W(28)), (W(19), Yv(-6), Zu(72)), steel, bev=0.001))  # jam latch lever
    A(cyl(W(3), W(44), (0, Yv(-6), Zu(60)), steel, axis='x', seg=8))  # its pivot pin through the nose
    A(cyl(W(9), W(8), (W(-21), Yv(4), Zu(88)), black, axis='x', seg=16, bev=0.0006))  # depth-of-drive wheel (knurled)
    for i in range(10):
        a = i * math.pi / 5
        A(box((W(9), W(2.4), W(2.4)), (W(-21), Yv(4) + math.sin(a) * W(9.5), Zu(88) + math.cos(a) * W(9.5)), steel))
    A(side([UV(0, -10), UV(26, -14), UV(26, 14), UV(0, 10)], W(26), (0, 0, 0), steel, bev=0.001))  # contact trip
    for i in range(4): A(box((W(4), W(5), W(5)), (W(-9 + i * 6), Yv(-8), Zu(-1.5)), steel, rot=(0.6, 0, 0)))  # its teeth
    A(rod((W(12), Yv(-12), Zu(24)), (W(12), Yv(-30), Zu(130)), W(2.2), steel, seg=6))  # trip linkage up the side
    # ---------------- handle (pistol grip): orange body, rubber overmould, end cap, brass air plug
    gz = 252  # grip centre, mm back from the nose
    A(side([UV(gz - 30, 36), UV(gz + 28, 36), UV(gz + 24, 120), UV(gz + 26, 196), UV(gz - 24, 196), UV(gz - 22, 120)], W(34), (0, 0, 0), orange, bev=0.004, seg=3))
    A(side([UV(gz - 25, 82), UV(gz + 27, 82), UV(gz + 28, 120), UV(gz + 29, 188), UV(gz - 26, 188), UV(gz - 25, 120)], W(38), (0, 0, 0), rubber, bev=0.005, seg=3))
    for k in range(5): A(box((W(39), W(3), W(54)), (0, Yv(100 + k * 18), Zu(gz + 1.5)), black, bev=0.0006))  # finger grooves in the rubber
    A(side([UV(gz - 30, 194), UV(gz + 30, 194), UV(gz + 32, 214), UV(gz - 30, 214)], W(40), (0, 0, 0), black, bev=0.003, seg=2))  # end cap
    A(cyl(W(9), W(10), (0, Yv(220), Zu(gz)), brass, axis='y', seg=6))  # hex of the air plug
    A(lathe([(W(5), -W(0)), (W(5), -W(10)), (W(6.5), -W(12)), (W(6.5), -W(16)), (W(4), -W(19)), (W(4), -W(26))], (0, Yv(225), Zu(gz)), brass, seg=14, axis='y'))
    # trigger: a red lever with a black safety selector, in front of the grip just under the housing
    A(side([UV(gz - 30, 48), UV(gz - 40, 52), UV(gz - 44, 78), UV(gz - 38, 80), UV(gz - 32, 60)], W(10), (0, 0, 0), redt, bev=0.0012, seg=2))
    A(box((W(16), W(8), W(8)), (0, Yv(46), Zu(gz - 34)), black, bev=0.0008))
    # ---------------- stick magazine: aluminium channel raked back 21 degrees, nails inside, follower, bracket to the grip
    def mpt(t, side_off):  # t: mm down the magazine from the nose; side_off: mm toward the back of the channel
        return (Zu(48 + math.sin(RAKE) * t + math.cos(RAKE) * side_off), Yv(18 + math.cos(RAKE) * t - math.sin(RAKE) * side_off))
    ML = 186
    for sx in (-1, 1):  # side walls: solid over the heads, a long window over the shanks so you see the nails
        A(side([mpt(0, 22), mpt(0, 50), mpt(ML, 50), mpt(ML, 22)], W(5), (sx * W(12), 0, 0), alu, bev=0.001))
        A(side([mpt(0, -14), mpt(0, 22), mpt(10, 22), mpt(10, -14)], W(5), (sx * W(12), 0, 0), alu, bev=0.001))
        A(side([mpt(ML - 12, -14), mpt(ML - 12, 22), mpt(ML, 22), mpt(ML, -14)], W(5), (sx * W(12), 0, 0), alu, bev=0.001))
        A(side([mpt(0, -14), mpt(0, -6), mpt(ML, -6), mpt(ML, -14)], W(5), (sx * W(12), 0, 0), alu, bev=0.001))
    A(side([mpt(0, 44), mpt(0, 56), mpt(ML, 56), mpt(ML, 44)], W(30), (0, 0, 0), alu, bev=0.0012))  # back spine
    A(side([mpt(0, -18), mpt(0, -12), mpt(ML, -12), mpt(ML, -18)], W(30), (0, 0, 0), alu, bev=0.001))  # nose-side lip
    # the nail strip: full round heads stacked down the channel (seen through the open gap), shanks along the drive
    for i in range(16):
        t = 8 + i * 10.5
        hz, hy = mpt(t, 32)  # heads sit in the back of the channel, the shanks run forward along the drive
        A(cyl(W(4.2), W(2.4), (0, hy, hz), nailm, axis='z', seg=10))
        A(cyl(W(1.5), W(40), (0, hy, hz - W(21)), nailm, axis='z', seg=6))
        A(cyl(W(1.5), W(4), (0, hy, hz - W(43)), nailm, axis='z', seg=6, r2=0.0002))  # the point
    A(side([mpt(4, 12), mpt(4, 15), mpt(ML - 14, 15), mpt(ML - 14, 12)], W(4), (0, 0, 0), paper))  # the paper collation
    fz, fy = mpt(ML - 10, 20)
    A(box((W(28), W(18), W(26)), (0, fy, fz), orange, bev=0.002, rot=(RAKE, 0, 0)))  # follower
    A(cyl(W(6), W(14), (W(16), fy, fz), black, axis='x', seg=12, bev=0.0008))  # its pull knob
    bz0, by0 = mpt(ML, 18); bz1, by1 = UV(gz - 26, 204)
    A(side([(bz0 - W(10), by0 + W(6)), (bz1, by1 + W(6)), (bz1, by1 - W(10)), (bz0 - W(14), by0 - W(12))], W(22), (0, 0, 0), black, bev=0.002))  # bracket
    A(cyl(W(4), W(30), (0, by0 - W(2), bz0 - W(6)), steel, axis='x', seg=6))  # bracket screw
    # ---------------- rafter hook on the right, spirit level taped on top (the sight), stickers
    A(tube([(W(48), Yv(-10), Zu(200)), (W(58), Yv(-10), Zu(200)), (W(62), Yv(-10), Zu(150)), (W(60), Yv(-24), Zu(132))], W(2.6), steel, seg=8))
    A(box((W(10), W(16), W(22)), (W(44), Yv(-10), Zu(204)), black, bev=0.001))
    lv_y = AXIS_Y + W(LEVEL_TOP - 16)
    A(box((W(16), W(18), W(130)), (0, lv_y, Zu(212)), redt, bev=0.002))  # the level's body
    A(box((W(12), W(10), W(30)), (0, lv_y + W(5), Zu(180)), vial))  # front vial
    A(box((W(12), W(10), W(30)), (0, lv_y + W(5), Zu(244)), vial))  # rear vial
    A(ball(W(3.2), (0, lv_y + W(8), Zu(181)), bubble, seg=10, rings=6))
    for zz in (Zu(176), Zu(184), Zu(240), Zu(248)): A(box((W(13), W(11), W(1)), (0, lv_y + W(5), zz), black))
    for zz in (Zu(156), Zu(266)): A(lathe([(W(47.5), zz - W(8)), (W(47.5), zz + W(8))], (0, AXIS_Y, 0), tape, seg=28))  # gaffer tape holding it on
    lb = box((0.0008, W(26), W(84)), (W(-46.5), AXIS_Y - W(4), Zu(211)), label, rot=(0, math.pi, 0)); A(lb); decals.append((lb, (W(84), W(26))))
    wn = box((0.0008, W(22), W(48)), (W(46.5), AXIS_Y - W(6), Zu(240)), warning); A(wn); decals.append((wn, (W(48), W(22)), 'x'))
    for p in parts: uv_box(p, 0.06)
    for d in decals:
        o, sz = d[0], d[1]
        apply_mods(o); c = o.matrix_world.translation; uv_planar(o, (c.x, c.z, -c.y), sz, d[2] if len(d) > 2 else '-x')
    WZ = {'ng_orange': 'a', 'ng_rubber': 'a', 'ng_alu': 'a', 'ng_magnesium': 'b', 'ng_steel': 'b', 'ng_black': 'b'}
    bodies = zone_join(parts, 'nailgun_body', WZ, default='n')
    meta = {'kind': 'weapon', 'id': 'nailgun', 'paint': ['ng_orange'], 'muzzle': [0, AXIS_Y, NOSE_Z],
            'sight': {'y': AXIS_Y + W(LEVEL_TOP), 'z': Zu(244) + 0.1}, 'hatAt': [[0, AXIS_Y + W(LEVEL_TOP), Zu(232)], 0.09]}
    return finish('w_nailgun', bodies, meta)


main(build, 'w_nailgun')
