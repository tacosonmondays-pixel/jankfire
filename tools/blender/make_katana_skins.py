# Katana skins: "Baguette Katana" (w_katana_baguette) and "Neon Tube" (w_katana_neon).
# Both keep the code katana's layout (public/js/blades/katana.js): a 26 cm tsuka on the grip (z -0.13 .. +0.13, y = 0),
# the guard stack in front of it, the blade starting at the front seppa's face (z = -0.139) and running 70 cm along the
# same arc (sori 1.7 cm, the tip 8.3 cm above the tsuka axis). The blade is its own node (meta katBlade, origin at
# the guard's front face, pointing -z, no rotation; katLen = origin to tip): the game stretches it along z as your
# kills grow it. The habaki-place collar sits outside it, so it keeps its size.
# Baguette Katana: a 70 cm baguette (4.6 x 3.6 cm, so a ficelle really) baked to the katana's curve, five scores along
# the mune, a bite out of it; a gold butter-foil habaki and fuchi; the tsuba is the lid of a round cheese box
# (FROMAGE); the tsuka is the loaf's own heel wrapped in red-and-white baker's twine in a hira-maki diamond pattern.
# Neon Tube: a 15 mm neon sign tube bent to the katana's curve, glowing hot pink inside its glass, an electrode chamber
# and rubber boot at the tip with a loose lead; at the guard a boot and a chrome electrode collar; the tsuba is a black
# finned heatsink with a cyan ring and a DO NOT LICK label; the tsuka is cable wound over a glowing cyan circuit core
# (the diamonds glow); the kashira is a strain relief with the power cord hanging out the back, unplugged.
# run: blender -b --python tools/blender/make_katana_skins.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj

NAGASA, SORI, Y0 = 0.70, 0.017, 0.0151
R = (NAGASA * NAGASA / 4 + SORI * SORI) / (2 * SORI)
T_TIP = 2 * math.asin(NAGASA / (2 * R))
Z_FUCHI, Z_KASHIRA = -0.130, 0.130
Z_BLADE = Z_FUCHI - 0.004 - 0.005   # front face of the front seppa (-0.139)
HABAKI = 0.034


def mune(t):  # (z, y) of the mune line at arc angle t, in the blade's own space (z = 0 at the guard face)
    return -R * math.sin(t), Y0 + R * (1 - math.cos(t))


def arc_centre(t, half):  # a point `half` below the mune, square to it
    z, y = mune(t)
    return (0.0, y - half * math.cos(t), Z_BLADE + z - half * math.sin(t))


def ribbon(pts, wdirs, width, thick, m, name, nrm=None, tile=0.06):
    """a flat strap along pts (game points), wide along wdirs, thick along nrm (default: across the path), u = length"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    P = [Vector(p) for p in pts]; rows = []; acc = [0.0]
    for i in range(1, len(P)): acc.append(acc[-1] + (P[i] - P[i - 1]).length)
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        w = Vector(wdirs[i]); w = (w - t * t.dot(w)).normalized()
        n = Vector(nrm[i]) if nrm else t.cross(w).normalized()
        n = (n - w * w.dot(n)).normalized()
        rows.append([bm.verts.new(gv(*(p + w * a * width / 2 + n * b * thick / 2))) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for i in range(len(rows) - 1):
        for k in range(4):
            kk = (k + 1) % 4
            f = bm.faces.new((rows[i][k], rows[i][kk], rows[i + 1][kk], rows[i + 1][k]))
            for lp, (ii, kv) in zip(f.loops, ((i, k), (i, kk), (i + 1, kk), (i + 1, k))):
                lp[uvl].uv = (acc[ii] / tile, (0.0, 1.0, 1.0, 0.0)[kv])
    for r in (rows[0], rows[-1]): bm.faces.new(r)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m); smooth(o, 40)
    return o


def ito(z0, z1, a, b, m, name, pitch=0.052, width=0.0105, thick=0.0016, n=22):
    """hira-maki: two cords wound opposite ways over an oval (half width a, half height b), crossing on the sides so
    the core shows through in diamonds"""
    out = []
    for hand, lift in ((1, 0.0), (-1, 0.0006)):
        pts, wd, nr = [], [], []
        turns = (z1 - z0) / pitch; tot = int(turns * n)
        for i in range(tot + 1):
            th = hand * 2 * math.pi * i / n + math.pi / 2
            c, s = math.cos(th), math.sin(th)
            rr = 1 + (thick / 2 + lift) / min(a, b)
            pts.append((a * rr * c, b * rr * s, z0 + (z1 - z0) * i / tot))
            wd.append((0, 0, 1)); nn = Vector((c / a, s / b, 0)).normalized(); nr.append(tuple(nn))
        out.append(ribbon(pts, wd, width, thick, m, name, nrm=nr, tile=0.03))
    return out


def oval_loft(z0, z1, ab, m, name, n=12, K=16, close=(False, False), cap=True):
    """an oval rod along z, ab(z) -> (half width, half height)"""
    zs_ = [z0 + (z1 - z0) * i / (n - 1) for i in range(n)]
    def ring(i, t):
        a, b = ab(zs_[i]); out = []
        for j in range(K):
            th = 2 * math.pi * j / K; c, s = math.cos(th), math.sin(th)
            out.append((b * math.copysign(abs(s) ** 0.85, s), a * math.copysign(abs(c) ** 0.85, c)))
        return out
    return loft([(0, 0, z) for z in zs_], ring, m=m, name=name, close=close, cap=cap, smooth_angle=60)


def core_ab(z):  # the code katana's tsuka core: wide at the fuchi, a waist, a little wider again
    t = (z - Z_FUCHI) / (Z_KASHIRA - Z_FUCHI)
    return 0.0112 - 0.0007 * math.sin(math.pi * min(1, t / 0.8)), 0.0163 - 0.0011 * math.sin(math.pi * min(1, t / 0.8))


def bool_transfer(o, cutter):
    """boolean difference that hands the cut faces the cutter's material (the bite shows crumb)"""
    apply_mods(cutter)
    md = o.modifiers.new('bite', 'BOOLEAN'); md.object = cutter; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
    md.material_mode = 'TRANSFER'
    apply_mods(o)
    bpy.data.objects.remove(cutter, do_unlink=True)


# ============================================================ Baguette Katana
def baguette():
    crust = mat('bk_crust', 0xffffff, rough=0.58, clearcoat=0.15, tex=tex_noise('bk_crust_t', 0xb86e2a, var=0.14, size=32, speck=0x9a5a1e, speck_p=0.12, seed=41))
    dark = mat('bk_dark', 0xffffff, rough=0.55, clearcoat=0.18, tex=tex_noise('bk_dark_t', 0x7a3c14, var=0.16, size=32, speck=0x5a2a0a, speck_p=0.12, seed=42))
    flour = mat('bk_flour', 0xffffff, rough=0.9, tex=tex_noise('bk_flour_t', 0xcc9e6a, var=0.12, size=32, speck=0xf2e8d2, speck_p=0.3, seed=43))
    crumb = mat('bk_crumb', 0xffffff, rough=0.85, tex=tex_noise('bk_crumb_t', 0xf2d8a0, var=0.1, size=16, speck=0xc89a58, speck_p=0.22, seed=44))
    foil = mat('bk_foil', 0xffffff, rough=0.22, metal=1.0, tex=tex_noise('bk_foil_t', 0xe0b84a, var=0.12, size=16, seed=45))
    twine_t = tex_stripes('bk_twine_t', 0xe8262a, 0xf8f2ea, size=16, width=3, diag=True)
    twine = mat('bk_twine', 0xffffff, rough=0.85, tex=twine_t)
    wood = mat('bk_wood', 0xffffff, rough=0.6, tex=tex_wood('bk_wood_t', 0xe2c89a, 0xb8925a, size=32, seed=46, rings=5))
    def label_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xf6eedc)
        px_disc(px, w / 2, h / 2, w / 2 - 0.5, 0xc81e28, r_in=w / 2 - 3.5)
        px_disc(px, w / 2, h / 2, w / 2 - 6, 0x2a7a3a, r_in=w / 2 - 7.2)
        text_px(px, 'FROMAGE', 3, h // 2 - 4, 1, 0xc81e28)
        text_px(px, 'EXTRA', 10, h // 2 - 14, 1, 0x2a7a3a); text_px(px, 'STINKY', 7, h // 2 + 6, 1, 0x2a7a3a)
    label = mat('bk_label', 0xffffff, rough=0.45, clearcoat=0.3, tex=tex_canvas('bk_label_t', 48, 48, label_px))

    # ---- the blade: a baguette along the katana's arc, pointed at the tip, scored along the top
    HH, HW = 0.023, 0.018     # half height / half width
    N, K = 84, 26
    ts = [T_TIP * (i / (N - 1)) for i in range(N)]
    tip_t = 0.9
    def prof(u):  # 0 base .. 1 tip
        k = 1.0 if u < tip_t else math.sqrt(max(0.0, 1 - ((u - tip_t) / (1 - tip_t)) ** 2))
        return k * (1 + 0.03 * math.sin(u * 23))
    SC = [(0.16 + 0.155 * k, 0.003 * (-1) ** k) for k in range(5)]  # (u centre, sideways nudge)
    S_LEN, S_W, S_D, S_EAR, S_ANG = 0.13, 0.016, 0.0065, 0.0028, 0.32
    def score(u, th, s):
        L = u * NAGASA; a = (HW * 0.9) * s * (((th - math.pi / 2) + math.pi) % (2 * math.pi) - math.pi)
        dep = ear = 0.0; zone = None
        for uc, ac in SC:
            du, dv = L - uc * NAGASA, a - ac
            p = du * math.cos(S_ANG) + dv * math.sin(S_ANG); q = -du * math.sin(S_ANG) + dv * math.cos(S_ANG)
            if abs(p) >= S_LEN / 2: continue
            kk = math.sqrt(1 - (2 * p / S_LEN) ** 2); half = S_W / 2 * kk
            if abs(q) < half: dep = max(dep, S_D * (1 - (q / half) ** 2) * kk); zone = 'crumb'
            elif half <= q < half + S_W * 0.5: ear = max(ear, S_EAR * kk * (1 - (q - half) / (S_W * 0.5))); zone = zone or 'ear'
        return dep, ear, zone
    def sec(u, th, s):
        c, sn = math.cos(th), math.sin(th)
        up = (HH * sn if sn >= 0 else -HH * 0.82 * abs(sn) ** 0.75) * s
        return up, HW * c * s
    def ring(i, t):
        u = i / (N - 1); s = prof(u); out = []
        for j in range(K):
            th = 2 * math.pi * j / K
            up, sd = sec(u, th, s)
            dep, ear, _ = score(u, th, s) if s > 0.6 else (0, 0, None)
            L = math.hypot(up, sd) or 1.0; f = (L - dep + ear) / L
            out.append((up * f, sd * f))
        return out
    cen = [arc_centre(t, HH * 0.95) for t in ts]
    cen[0] = (0.0, cen[0][1], Z_BLADE + 0.002)
    blade = loft(cen, ring, m=crust, name='bk_blade', close=(False, True), smooth_angle=70)
    for mm in (dark, flour, crumb): blade.data.materials.append(mm)
    for f in blade.data.polygons:
        st, sl = divmod(f.index, K)
        if st >= N - 1: f.material_index = 1; continue
        u = (st + 0.5) / (N - 1); th = 2 * math.pi * (sl + 0.5) / K; s = prof(u)
        _, _, zone = score(u, th, s) if s > 0.6 else (0, 0, None)
        if zone == 'crumb': f.material_index = 3
        elif zone == 'ear' or u > 0.95: f.material_index = 1
        elif math.sin(th) < -0.4: f.material_index = 2
    uv_box(blade, 0.06)
    # somebody had a bite: a crescent out of the mune, two thirds of the way up
    tb = T_TIP * 0.64; bc = arc_centre(tb, HH * 0.95)
    bite = ball(0.024, (bc[0] + 0.006, bc[1] + HH * 1.08, bc[2]), crumb, scale=(1.2, 0.72, 1.0), seg=16, rings=10, name='bite')
    bool_transfer(blade, bite)
    blade = part([blade], 'bk_blade_wzB', pivot=(0, 0, Z_BLADE))
    tip = arc_centre(T_TIP, HH * 0.95)
    kat_len = round(Z_BLADE - tip[2], 4)

    # ---- the habaki: butter foil crimped round the root of the loaf
    def foil_ab(z):
        return HW * 1.09 + 0.0008 * math.sin(z * 900), HH * 1.0 + 0.0008 * math.cos(z * 700)
    hab = oval_loft(Z_BLADE - HABAKI, Z_BLADE + 0.0005, foil_ab, foil, 'bk_habaki', n=8, K=20)
    hab.location = gv(0, -0.003, 0)
    jitter(hab, 0.0006, 47); uv_box(hab, 0.03)
    # ---- the tsuba: a round cheese box lid, label facing you, wood rim
    lid = lathe([(0.0, -0.139), (0.0405, -0.139), (0.0418, -0.1385), (0.0418, -0.1295), (0.0405, -0.129), (0.0, -0.129)], (0, 0, 0), wood, seg=36, axis='z', name='bk_tsuba')
    uv_box(lid, 0.05)
    lab = cyl(0.036, 0.0006, (0, 0, -0.1288), label, axis='z', seg=36, name='bk_label')
    apply_mods(lab); bpy.context.view_layer.update()
    me = lab.data; uvl = (me.uv_layers.active or me.uv_layers.new()).data
    for f in me.polygons:
        for li in f.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl[li].uv = (v.x / 0.072 + 0.5, v.z / 0.072 + 0.5)  # read from behind (+z, where you stand): image right = +x
    # ---- fuchi: more foil; the tsuka: the heel of the loaf under twine
    fuchi = oval_loft(-0.1305, -0.1185, lambda z: (0.0136, 0.0192), foil, 'bk_fuchi', n=4, K=20)
    jitter(fuchi, 0.0004, 48); uv_box(fuchi, 0.03)
    core = oval_loft(-0.12, 0.108, core_ab, crust, 'bk_core', n=10, K=18, cap=False)
    uv_box(core, 0.05)
    cords = ito(-0.118, 0.1, *core_ab(-0.01), twine, 'bk_ito', width=0.0125, thick=0.0022)
    # kashira: the heel's crusty end, rounded off
    kash = oval_loft(0.104, Z_KASHIRA, lambda z: (lambda q: (0.0108 * q, 0.0155 * q))(math.sqrt(max(0.02, 1 - ((z - 0.104) / 0.026) ** 2))), dark, 'bk_kashira', n=8, K=18, close=(False, True))
    uv_box(kash, 0.05)
    # a knot of twine where the wrap ends
    knot = ball(0.0055, (0.0, 0.0172, 0.1), twine, scale=(1.3, 0.8, 1.0), seg=10, rings=6, name='bk_knot')
    uv_box(knot, 0.02)
    ends = [sweep([(0.002, 0.018, 0.102), (0.004, 0.014, 0.116), (0.006, 0.004, 0.126), (0.007, -0.006, 0.13)], 0.0012, twine, seg=5, name='bk_end'),
            sweep([(-0.002, 0.018, 0.102), (-0.005, 0.012, 0.112), (-0.009, 0.0, 0.118)], 0.0012, twine, seg=5, name='bk_end')]
    for e in ends: uv_box(e, 0.02)
    hilt = zone_join([core, kash] + cords + [knot] + ends, 'bk_tsuka', {'bk_twine': 'a', 'bk_crust': 'a', 'bk_dark': 'a'}, default='a')
    fit = zone_join([hab, fuchi, lid, lab], 'bk_fit', {'bk_foil': 'b', 'bk_wood': 'a', 'bk_label': 'n'}, default='b')
    meta = {'kind': 'weapon', 'id': 'katana', 'skin': 'katana_baguette', 'paint': ['bk_crust'], 'muzzle': [0, round(tip[1], 4), round(tip[2], 4)],
            'katBlade': 'bk_blade_wzB', 'katLen': kat_len, 'hatAt': [[0, 0.0205, -0.01], 0.055]}
    return finish('w_katana_baguette', [blade] + hilt + fit, meta)


# ============================================================ Neon Tube
def circuit_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(51)
    px[:] = hexrgb(0x062a3a)
    for _ in range(14):
        x, y = int(r.integers(0, w)), int(r.integers(0, h))
        for _ in range(4):
            if r.random() < 0.5:
                x1 = int(np.clip(x + r.integers(-10, 11), 0, w - 1)); px[y, min(x, x1):max(x, x1) + 1] = hexrgb(0x4fd8ff); x = x1
            else:
                y1 = int(np.clip(y + r.integers(-8, 9), 0, h - 1)); px[min(y, y1):max(y, y1) + 1, x] = hexrgb(0x4fd8ff); y = y1
        px_disc(px, x + 0.5, y + 0.5, 1.3, 0xbff4ff)


def neon():
    glow = mat('nt_glow', 0xff4fd8, rough=0.3, emit=0xff3ad0, strength=3.0)
    glass = mat('nt_glass', 0xffd8f6, rough=0.02, clearcoat=1.0, alpha=0.22)
    rubber = mat('nt_rubber', 0x141218, rough=0.62)
    chrome = mat('nt_chrome', 0xeef2f6, rough=0.06, metal=1.0)
    alu = mat('nt_alu', 0x1c1a22, rough=0.3, metal=0.9)
    ring_m = mat('nt_ring', 0x4fd8ff, rough=0.3, emit=0x4fd8ff, strength=2.5)
    circ = mat('nt_circuit', 0xffffff, rough=0.35, emit=0xffffff, strength=1.2, tex=tex_canvas('nt_circuit_t', 32, 32, circuit_px), emit_tex=True)
    elec = mat('nt_electrode', 0x8a8e96, rough=0.35, metal=1.0)
    brass = mat('nt_brass', 0xe0b040, rough=0.2, metal=1.0)
    def lick_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xffe14d)
        for x in range(-h, w, 6):
            for y in range(h):
                if 0 <= x + y < w and (y < 2 or y >= h - 2): px[y, x + y] = hexrgb(0x120818)
        px[0:2] = px[h - 2:] = hexrgb(0x120818)
        text_px(px, 'DO NOT LICK', 2, (h - 7) // 2, 1, 0x120818)
    lick = mat('nt_lick', 0xffffff, rough=0.4, clearcoat=0.4, tex=tex_canvas('nt_lick_t', 70, 13, lick_px))

    # ---- the tube: glow core inside clear glass, along the arc; electrode chamber + boot + lead at the tip
    RT, RG = 0.0062, 0.0078
    N = 60
    T_BODY = T_TIP * 0.91   # where the electrode chamber starts
    ts = [T_BODY * i / (N - 1) for i in range(N)]
    half = 0.012
    cen = [arc_centre(t, half) for t in ts]
    cen[0] = (0.0, cen[0][1], Z_BLADE + 0.001)
    core = sweep(cen, RT, glow, seg=14, name='nt_core', cap=True)
    shell = sweep(cen, RG, glass, seg=18, name='nt_shell', cap=False)
    # electrode chamber: the glass swells, the electrode can shows inside, then the boot
    ch = [arc_centre(T_BODY + (T_TIP * 0.985 - T_BODY) * i / 8, half) for i in range(9)]
    rch = [RG + (0.0108 - RG) * min(1, i / 2.5) for i in range(9)]
    chamber = sweep(ch, rch, glass, seg=18, name='nt_chamber', cap=False)
    can = sweep(ch[2:8], 0.0062, elec, seg=12, name='nt_can')
    glowtip = sweep([cen[-1], ch[2]], RT, glow, seg=14, name='nt_core2')
    tb = [arc_centre(T_TIP * 0.985 + (T_TIP * 1.03 - T_TIP * 0.985) * i / 4, half) for i in range(5)]
    boot = sweep(tb, [0.0112, 0.0118, 0.0116, 0.0098, 0.006], rubber, seg=16, name='nt_boot')
    e = tb[-1]
    lead = sweep([e, (e[0], e[1] + 0.004, e[2] - 0.012), (e[0] + 0.006, e[1] - 0.004, e[2] - 0.022), (e[0] + 0.004, e[1] - 0.016, e[2] - 0.026), (e[0] - 0.002, e[1] - 0.024, e[2] - 0.02)],
                 0.0018, rubber, seg=6, name='nt_lead')
    blade_parts = [core, shell, chamber, can, glowtip, boot, lead]
    for o in blade_parts: uv_box(o, 0.04)
    blade = part(blade_parts, 'nt_blade_wzN', pivot=(0, 0, Z_BLADE))
    tip = (0.0, tb[-1][1], tb[-1][2])
    kat_len = round(Z_BLADE - tip[2], 4)

    # ---- the base boot + chrome electrode collar (the habaki's place, outside the growing blade)
    bc = [arc_centre(0.0, half)[1]]
    hb = [lathe([(0.0098, Z_BLADE - HABAKI), (0.0112, Z_BLADE - HABAKI + 0.004), (0.0118, Z_BLADE - 0.006), (0.0124, Z_BLADE)], (0, bc[0], 0), rubber, seg=20, axis='z', name='nt_hboot', cap=False),
          lathe([(0.013, Z_BLADE - 0.009), (0.0138, Z_BLADE - 0.006), (0.0138, Z_BLADE - 0.001), (0.013, Z_BLADE)], (0, bc[0], 0), chrome, seg=20, axis='z', name='nt_collar', cap=False)]
    # ---- the tsuba: a black finned heatsink disc, a glowing cyan ring on its back, the label
    disc = lathe([(0.0, -0.139), (0.036, -0.139), (0.0378, -0.1375), (0.0378, -0.1305), (0.036, -0.129), (0.0, -0.129)], (0, 0, 0), alu, seg=32, axis='z', name='nt_tsuba')
    fins = []
    for k in range(20):  # heatsink fins round the rim
        a = 2 * math.pi * k / 20
        fins.append(box((0.0032, 0.0064, 0.0086), (0.0392 * math.cos(a), 0.0392 * math.sin(a), -0.134), alu, rot=(0, 0, a + math.pi / 2), name='nt_fin'))
    gring = lathe([(0.0255, -0.1287), (0.0285, -0.1287), (0.0285, -0.1283), (0.0255, -0.1283), (0.0255, -0.1287)], (0, 0, 0), ring_m, seg=32, axis='z', name='nt_gring', cap=False)
    lk = box((0.03, 0.0056, 0.0006), (0, -0.0175, -0.1286), lick, name='nt_label')
    apply_mods(lk); bpy.context.view_layer.update()
    me = lk.data; uvl = (me.uv_layers.active or me.uv_layers.new()).data
    for f in me.polygons:
        for li in f.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl[li].uv = (v.x / 0.03 + 0.5, (v.z + 0.0175) / 0.0056 + 0.5)
    # ---- fuchi (chrome), tsuka (cable over a glowing circuit core), kashira (strain relief + the cord, unplugged)
    fuchi = oval_loft(-0.1305, -0.1185, lambda z: (0.0136, 0.0192), chrome, 'nt_fuchi', n=4, K=20)
    core_t = oval_loft(-0.12, 0.106, core_ab, circ, 'nt_coret', n=10, K=18, cap=False)
    uv_box(core_t, 0.03)
    cords = ito(-0.118, 0.104, *core_ab(-0.01), rubber, 'nt_ito', width=0.0098)
    kash = lathe([(0.0136, 0.104), (0.0142, 0.108), (0.0142, 0.118), (0.0118, 0.124), (0.0072, 0.127), (0.0072, 0.136), (0.0058, 0.142), (0.0046, 0.146)], (0, 0, 0), chrome, seg=20, axis='z', name='nt_kashira')
    kash.scale = (0.82, 1.15, 1.0)
    relief = lathe([(0.0055, 0.14), (0.0052, 0.15), (0.0042, 0.162), (0.0034, 0.17)], (0, 0, 0), rubber, seg=12, axis='z', name='nt_relief')
    cord_pts = [(0, 0, 0.168), (0, -0.004, 0.182), (0.004, -0.018, 0.19), (0.008, -0.04, 0.186), (0.006, -0.06, 0.174), (0.0, -0.072, 0.168)]
    cord = sweep(cord_pts, 0.0028, rubber, seg=8, name='nt_cord')
    pe = cord_pts[-1]
    plug = box((0.017, 0.022, 0.011), (pe[0], pe[1] - 0.012, pe[2] - 0.001), rubber, bev=0.002, name='nt_plug')
    prongs = [box((0.0018, 0.016, 0.0062), (pe[0] + sx * 0.0045, pe[1] - 0.03, pe[2] - 0.001), brass, bev=0.0005, name='nt_prong') for sx in (1, -1)]
    for o in [fuchi, kash, relief, cord, plug] + prongs + hb + [disc, gring] + fins: uv_box(o, 0.03)
    hilt = zone_join([core_t] + cords + [kash, relief, cord, plug] + prongs, 'nt_tsuka', {'nt_rubber': 'a', 'nt_circuit': 'n', 'nt_chrome': 'b', 'nt_brass': 'b'}, default='a')
    fit = zone_join(hb + [disc, gring, lk, fuchi] + fins, 'nt_fit', {'nt_rubber': 'b', 'nt_chrome': 'b', 'nt_alu': 'b', 'nt_ring': 'n', 'nt_lick': 'n'}, default='b')
    meta = {'kind': 'weapon', 'id': 'katana', 'skin': 'katana_neon', 'paint': [], 'muzzle': [0, round(tip[1], 4), round(tip[2], 4)],
            'katBlade': 'nt_blade_wzN', 'katLen': kat_len, 'hatAt': [[0, 0.0205, -0.01], 0.055]}
    return finish('w_katana_neon', [blade] + hilt + fit, meta)


main_multi(lambda: [(baguette(), 'w_katana_baguette'), (neon(), 'w_katana_neon')], exposure=-0.5)
