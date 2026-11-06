# Pepper Mills (Half a Shotgun skin): two tall restaurant pepper mills (~300 mm, turned walnut, a chrome grinder
# ring at the foot) laid side by side as the barrels, held together with two blue produce rubber bands, on the
# sawn-off's stainless action and a walnut pistol grip. The grinder ends are the muzzles; the mill tops are the
# chambers, so breaking it open is refilling them: each takes one giant peppercorn (the shells). The hammers are the
# mills' turned finial knobs on steel arms. Built on the sawn-off's spots (real millimetres x1.0): muzzle (0, 0.02,
# -0.31), breech face z -0.012, the hinge pin in the knuckle at (0, -0.002, -0.05), the grip on its 0.55 rad rake.
# Made fun: FRESHLY CRACKED on the left mill, CORP PEPPER CO. on the right, a brass bead in the valley between them.
# Moving parts (sidearms.js): hinge_wzB (the mills break open round the pin; forend_wzA, shell1_wzN / shell2_wzN
# ride on it), hammerR_wzN / hammerL_wzN (modelled cocked, the game drops them 0.75 rad).
# run: blender -b --python tools/blender/make_sawnoff_pepper.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sidekit import quad, uv_ring, cyl_patch, smiley, text_c, one_mat, bake_normals

def g(*v): return tuple(a / 1000 for a in v)  # millimetres -> metres
def pz(pts): return [(z / 1000, y / 1000) for z, y in pts]
BY, MX, MZ, BF = 20, 19, -310, -12.3  # bore line, mill axes at x +-19, muzzle, the mills' top faces (mm)
PIN = (0, -2, -50)
HAM = (19, 30, 50)  # hammer pivot (x mirrored)
U = (0.5227, -0.8526)  # grip axis (z, y)
SIGHT_Y = 41.0
def far(p, t): return (p[0] + U[0] * t, p[1] + U[1] * t)

# the mill's turned profile (radius, z) in mm, from the grinder foot (muzzle) back to the top face (chamber)
MILL = [(10.0, -310), (16.5, -309.5), (18.0, -306), (18.0, -299), (16.6, -296.5), (17.5, -291), (18.4, -277), (17.6, -259), (15.6, -239), (13.4, -217), (12.0, -196),
        (11.3, -176), (11.3, -150), (12.0, -130), (13.4, -110), (15.4, -91), (17.2, -75), (18.0, -67), (17.4, -63.5), (15.6, -62), (15.4, -58)]
HEAD = [(15.4, -58), (17.4, -56.5), (18.4, -50), (18.5, -32), (17.8, -22), (16.6, -15.5), (15.2, -12.8), (9.2, -12.3)]  # the mill's turning head (the chamber end)


def stadium(z, r, n=10):  # a rubber band round both mills (a loop in the x-y plane at z)
    pts = []
    for sx, a0 in ((1, -90), (-1, 90)):
        for k in range(n + 1):
            a = math.radians(a0 + 180 * k / n)
            pts.append(g(sx * MX + math.cos(a) * r, BY + math.sin(a) * r, z))
    return pts


def build():
    walnut = mat('pm_walnut', 0xffffff, rough=0.25, clearcoat=1.0, tex=tex_wood('pm_walnut_t', 0x7a4624, 0x3e2010, size=64, seed=31, rings=6.0))
    walnut2 = mat('pm_walnut2', 0xffffff, rough=0.25, clearcoat=1.0, tex=tex_wood('pm_walnut2_t', 0x8a5630, 0x48281a, size=64, seed=37, rings=7.0))
    steel = mat('pm_steel', 0xffffff, rough=0.38, metal=0.9, tex=tex_noise('pm_steel_t', 0x8e96a2, var=0.06, size=16, seed=32))
    lacquer = mat('pm_lacquer', 0x15121a, rough=0.12, clearcoat=1.0)
    chrome = mat('pm_chrome', 0xdde2e8, rough=0.1, metal=1.0)
    black = mat('pm_black', 0x060606, rough=0.5)
    brass = mat('pm_brass', 0xe0b04a, rough=0.2, metal=1.0)
    band = mat('pm_band', 0x2f7bff, rough=0.5, clearcoat=0.2)
    corn = mat('pm_corn', 0xffffff, rough=0.55, tex=tex_noise('pm_corn_t', 0x2a1c14, var=0.3, size=16, speck=0x5a3a24, speck_p=0.3, seed=33))
    def lab_l(px):
        px[:] = hexrgb(0xf4ecd8); px[:1] = px[-1:] = hexrgb(0xd01c1c)
        text_c(px, 'FRESHLY', 26, 2, 1, 0x2a1c14); text_c(px, 'CRACKED', 26, 11, 1, 0xd01c1c)
    lab_r = lambda px: (px.__setitem__(slice(None), hexrgb(0xffe14d)), smiley(px, 8, 9.5, 6.8), text_px(px, 'CORP', 18, 3, 1, 0x111111), text_px(px, 'PEPPER CO.', 18, 11, 1, 0x111111))
    labL = mat('pm_label_l', 0xffffff, rough=0.4, tex=tex_canvas('pm_label_l_t', 52, 20, lab_l))
    labR = mat('pm_label_r', 0xffffff, rough=0.4, tex=tex_canvas('pm_label_r_t', 80, 20, lab_r))

    hinge, trim, fore, parts, hams = [], [], [], [], []
    shells = [[], []]
    mills = []
    # ---------------- the mills (barrels): turned walnut, chrome grinder ring + nut at the foot, the fill hole on top
    for i, sx in enumerate((1, -1)):
        x = sx * MX / 1000
        m = lathe([(r / 1000, z / 1000) for r, z in MILL], (x, BY / 1000, 0), walnut if sx > 0 else walnut2, seg=28, name='mill'); mills.append(m); hinge.append(m)
        hinge.append(lathe([(r / 1000, z / 1000) for r, z in HEAD], (x, BY / 1000, 0), lacquer, seg=28, name='head'))
        hinge.append(lathe([(0.0157, -0.0612), (0.0163, -0.0605), (0.0163, -0.0585), (0.0157, -0.0578)], (x, BY / 1000, 0), brass, seg=28, cap=False, name='headring'))
        for zz, rr in ((-292.5, 17.3), (-268, 18.3), (-82, 16.6)):  # burned turning lines
            hinge.append(lathe([(rr / 1000 + 0.0003, zz / 1000 - 0.0006), (rr / 1000 + 0.0003, zz / 1000 + 0.0006)], (x, BY / 1000, 0), black, seg=28, cap=False, name='line'))
        hinge.append(lathe([(0.0098, -0.3092), (0.0106, -0.311), (0.0106, -0.3145), (0.0094, -0.3155), (0.0, -0.3155)], (x, BY / 1000, 0), chrome, seg=20, name='grinder'))
        hinge.append(cyl(0.0045, 0.0015, (x, BY / 1000, -0.3162), black, axis='z', seg=12, name='spout'))
        for k in range(6):
            a = 2 * math.pi * k / 6
            hinge.append(box((0.0016, 0.002, 0.0035), (x + math.cos(a) * 0.0103, BY / 1000 + math.sin(a) * 0.0103, -0.3125), chrome, rot=(0, 0, a), name='grinder_tooth'))
        hinge.append(lathe([(0.0092, -0.0122), (0.0086, -0.0135), (0.0086, -0.03), (0.0, -0.03)], (x, BY / 1000, 0), black, seg=18, name='fillhole'))
        # the peppercorn in its chamber (the shell)
        c = ball(0.0084, (x, BY / 1000, -0.0205), corn, seg=12, rings=8, name='corn')
        jitter(c, 0.0009, seed=40 + i)
        shells[i].append(c)
        hinge.append(lathe([(0.0108, -0.0125), (0.0112, -0.0118), (0.0112, -0.0112)], (x, BY / 1000, 0), brass, seg=20, cap=False, name='fillrim'))
    # rubber bands round both, a brass bead in the valley at the muzzle
    for z in (-270, -163):
        trim.append(tube(stadium(z, (18.0 if z < -200 else 11.3) + 1.0), 0.0017, band, seg=8, name='band', closed=True))
    hinge.append(box((0.006, 0.006, 0.01), g(0, 34.5, -302), brass, bev=0.0015, name='beadpost'))
    hinge.append(ball(0.0022, g(0, SIGHT_Y - 2.0, -302), brass, seg=10, rings=6, name='bead'))
    # labels on the mills (flat stickers on the sides you see)
    # (left: seen from -x, the image's up toward +y means the angle runs from below to above; right mirrored)
    trim.append(cyl_patch(-MX / 1000, BY / 1000, 0.0116, -0.178, -0.128, math.pi + 0.95, math.pi - 0.95, labL, name='label'))
    trim.append(cyl_patch(MX / 1000, BY / 1000, 0.0116, -0.188, -0.118, -0.95, 0.95, labR, name='label', flip=True))
    # the knuckle round the pin + the lump that hooks under the action
    hinge.append(side(pz([(-62, 2), (-14, 2), (-14, -4), (-40, -10), (-50, -12.2), (-58, -10)]), 0.022, (0, 0, 0), steel, bev=0.002, name='lump'))
    # ---------------- forend (rides on the hinge): a walnut block cradling the mills, a steel tip
    fore.append(side(pz([(-196, 4), (-80, 4), (-78, -6), (-90, -13), (-190, -13), (-197, -7)]), 0.03, (0, 0, 0), walnut, bev=0.004, seg=2, name='forend'))
    fore.append(side(pz([(-198, 3), (-192, 3), (-192, -12), (-198, -9)]), 0.0305, (0, 0, 0), steel, bev=0.0015, name='forendtip'))
    # ---------------- the action: stainless, standing breech, fences, the bar under the chambers, the knuckle pin
    A = parts.append
    A(side(pz([(-62, -2), (-12, -2), (-12, 40), (-4, 46), (40, 46), (64, 38), (80, 26), (88, 14), (88, -4), (70, -14), (40, -16), (-4, -16), (-40, -12), (-58, -10)]), 0.044, (0, 0, 0), steel, bev=0.004, seg=2, name='action'))
    for sx in (-1, 1):
        A(lathe([(0.0, -0.0118), (0.0184, -0.0118), (0.0186, -0.006), (0.0, -0.006)], (sx * MX / 1000, BY / 1000, 0), steel, seg=24, name='fence'))
        A(cyl(0.0022, 0.002, (sx * MX / 1000, BY / 1000, -0.0124), chrome, axis='z', seg=10, name='striker'))
    A(cyl(0.0052, 0.05, g(*PIN), chrome, axis='x', seg=14, name='pin'))
    A(box((0.006, 0.004, 0.018), g(0, 47.5, 18), brass, bev=0.0012, name='toplever'))
    A(side(pz([(-4, 46), (40, 46), (40, 48.5), (-4, 48.5)]), 0.008, (0, 0, 0), steel, bev=0.001, holes=[pz([(4, 44), (30, 44), (30, 50), (4, 50)])], name='notch'))  # a rear notch
    # trigger guard + two brass triggers
    A(side(pz([(22, -14), (24, -30), (34, -40), (62, -40), (74, -30), (76, -14)]), 0.01, (0, 0, 0), steel, bev=0.002,
           holes=[pz([(28, -16), (70, -16), (68, -28), (60, -35), (36, -35), (30, -28)])], name='guard'))
    for z in (40, 54):
        A(side(pz([(z - 2, -15), (z + 2, -15), (z + 4, -22), (z + 2, -31), (z - 1, -30), (z, -22)]), 0.005, (0, 0, 0), brass, bev=0.001, name='trigger'))
    # ---------------- the grip: walnut, on the sawn-off's rake, a chrome mill-top cap for a pommel
    back = [(59, 32.5), (66, 31.5), (74, 28.5), (82, 22.5), (89, 13.5), (95, 4)]
    front = [(67, -22.5), (63, -16), (59, -11.5)]
    gp = side(pz(back + [far((95, 4), t) for t in (40, 70, 92)] + [far((67, -22.5), t) for t in (100, 60, 30)] + front + [(56, 0), (56, 20)]), 0.034, (0, 0, 0), walnut2, bev=0.006, seg=3, name='grip')
    A(gp)
    for sx in (-1, 1):
        A(cyl(0.004, 0.003, g(sx * 17.4, -40, 92), brass, axis='x', seg=10, name='gripscrew'))
    # ---------------- hammers: the mills' finial knobs on steel arms (modelled cocked, leaned back)
    for sx in (1, -1):
        hx, hy, hz = sx * HAM[0], HAM[1], HAM[2]
        L = 0.7
        tip = (hx, hy + 22 * math.cos(L), hz + 22 * math.sin(L))
        h = [rod(g(hx, hy, hz), g(*tip), 0.0022, steel, seg=8, name='arm'),
             cyl(0.004, 0.006, g(hx, hy, hz), steel, axis='x', seg=10, name='hampin'),
             lathe([(0.0, -0.004), (0.004, -0.0035), (0.0062, 0.0), (0.0055, 0.004), (0.0028, 0.006), (0.0026, 0.008), (0.0042, 0.0105), (0.0, 0.0135)], (0, 0, 0), walnut, seg=14, axis='y', name='finial')]
        f = h[-1]
        apply_mods(f); f.data.transform(Matrix.Translation(gv(*g(*tip))) @ Matrix.Rotation(L, 4, 'X'))
        hams.append((h, (hx, hy, hz)))

    # ---------------- UVs, nodes
    allp = hinge + trim + fore + parts + [o for hh, _ in hams for o in hh] + shells[0] + shells[1]
    for p in allp: apply_mods(p)
    one_mat(allp)
    for p in allp:
        if p.data.materials[0].name.startswith('pm_label'): continue
        uv_box(p, 0.04)
    for m in mills:
        uv_ring(m, m.matrix_world.translation.x, BY / 1000, -0.31, -0.012)
        for l in m.data.uv_layers.active.data: u, v = l.uv; l.uv = (u * 2.0, v * 1.0)
    bake_normals(allp)
    WZ = {'pm_walnut2': 'a', 'pm_steel': 'b', 'pm_chrome': 'b', 'pm_brass': 'n', 'pm_walnut': 'a', 'pm_lacquer': 'b'}
    bodies = zone_join(parts, 'pm_body', WZ, default='n')
    hn = part(hinge, 'hinge_wzB', pivot=g(*PIN))
    tn = part(trim, 'hinge_trim_wzN', pivot=g(*PIN))
    bpy.context.view_layer.update(); tn.parent = hn; tn.matrix_parent_inverse = hn.matrix_world.inverted()
    fn = part(fore, 'forend_wzA', pivot=g(*PIN))
    sn = [part(s, f'shell{i + 1}_wzN', pivot=g(sx * MX, BY, BF)) for i, (s, sx) in enumerate(zip(shells, (1, -1)))]
    hm = [part(h, 'hammerR_wzN' if hp[0] > 0 else 'hammerL_wzN', pivot=g(*hp)) for h, hp in hams]
    meta = {'kind': 'weapon', 'id': 'sawnoff', 'skin': 'sawnoff_pepper', 'paint': ['pm_walnut2'], 'muzzle': [0, BY / 1000, MZ / 1000],
            'sight': {'y': round(SIGHT_Y / 1000, 4), 'z': 0.13},
            'hatAt': [[0, 0.0485, 0.012], 0.05],
            'hinge': {'node': 'hinge_wzB', 'open': 0.7, 'rides': ['forend_wzA', 'shell1_wzN', 'shell2_wzN']},
            'shells': ['shell1_wzN', 'shell2_wzN'], 'hammers': ['hammerR_wzN', 'hammerL_wzN']}
    return finish('w_sawnoff_pepper', bodies + [hn, fn] + sn + hm, meta)


main(build, 'w_sawnoff_pepper')
