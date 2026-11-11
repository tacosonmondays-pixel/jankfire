# The Katana and its two sword skins as Blender models (w_katana, w_katana_shirasaya, w_katana_bokken). Each is the
# same sword its code model is (public/js/blades/katana.js, shirasaya.js, bokken.js have the measurements and the
# references), in the same place in the hand. The blade is its own node (meta katBlade, origin at the guard's front
# face, pointing -z, no rotation; katLen = origin to tip): the game stretches it along z as your kills grow it, so
# nothing else lives in that node and the habaki / tsubadome that hide its root sit outside it.
# What Blender adds: a real shinogi ridge and peaked mune, a painted hamon with its boshi turning back in the kissaki,
# file marks on the habaki, a hammered iron tsuba with a rounded rim, ray skin under a cord wrap with real thickness,
# wood grain running the right way. Wrap zones: the handle is A, the blade and its fittings B, pins and ornaments N.
# run: blender -b --python tools/blender/make_katanas.py [-- --only katana,katana_bokken] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bladekit import *
from lib import _obj

MM = 0.001
spow = lambda v, p=0.85: math.copysign(abs(v) ** p, v)


def steel_tex(name, base, var=0.07, seed=1, speck=None, p=0.0): return tex_noise(name, base, var=var, size=32, speck=speck, speck_p=p, seed=seed)


def ring_solid(rings, uvs, m, name, caps=(True, True), angle=35, crown=(0.0, 0.0)):
    """a closed solid through rings of game points (same count each), every point carrying its own uv. the end caps
    are fans (their middle pushed out by crown), mapped as a small flat patch"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); n = len(rings[0])
    R = [[bm.verts.new(gv(*p)) for p in r] for r in rings]
    def face(vs, uv):
        if len(set(vs)) < 3: return
        try: f = bm.faces.new(vs)
        except ValueError: return
        for lp, q in zip(f.loops, uv): lp[uvl].uv = q
    for i in range(len(R) - 1):
        for k in range(n):
            k1 = (k + 1) % n
            ua, ub, uc, ud = uvs[i][k], uvs[i][k1], uvs[i + 1][k1], uvs[i + 1][k]
            if k1 == 0:  # the seam: round again, or (a blade's edge, both sides on one line of the skin) a sliver of its own
                fix = lambda q, a: (q[0], q[1] + 1) if q[1] < a[1] - 1e-9 else (q[0], a[1] + 0.02) if abs(q[1] - a[1]) < 1e-9 else q
                ub, uc = fix(ub, ua), fix(uc, ud)
            face([R[i][k], R[i][k1], R[i + 1][k1], R[i + 1][k]], [ua, ub, uc, ud])
    mid = lambda r: sum((v.co for v in r), Vector()) / n
    for r, on, cr, nb, uv in ((R[0], caps[0], crown[0], R[1], uvs[0]), (R[-1], caps[1], crown[1], R[-2], uvs[-1])):
        if not on: continue
        c = mid(r); out = (c - mid(nb)).normalized(); cv = bm.verts.new(c + out * cr)
        t1 = out.cross(Vector((1, 0, 0))).normalized(); t2 = out.cross(t1)
        q = lambda v: (uv[0][0] + (v.co - c).dot(t1) * 2, 0.5 + (v.co - c).dot(t2) * 2)
        for k in range(n): face([r[k], r[(k + 1) % n], cv], [q(r[k]), q(r[(k + 1) % n]), q(cv)])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, dist=2e-6, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); outward(bm)
    o = _obj(name, bm, m); smooth(o, angle)
    return o


def strap(sections, m, name, tile=0.012):
    """a cord: sections = [[inner left, left, crown, right, inner right]] game points, joined in order into one closed
    strap (flat underneath, a ridge down its back). u = along, v = across"""
    V = (0.0, 0.15, 0.4, 0.65, 0.8); acc = [0.0]
    for a, b in zip(sections, sections[1:]): acc.append(acc[-1] + (Vector(b[2]) - Vector(a[2])).length / tile)
    return ring_solid(sections, [[(acc[i], v) for v in V] for i in range(len(sections))], m, name, angle=50)


def weave(name, base, dark, w=32, h=16, seed=1):
    """braided cord: slanted ribs across the strap"""
    def draw(px):
        r = np.random.default_rng(seed); b, d = hexrgb(base), hexrgb(dark)
        for row in range(h):
            for col in range(w): px[row, col] = (d if (col + row // 2) % 4 == 0 else b) * (0.9 + 0.2 * r.random())
    return tex_canvas(name, w, h, draw)


def grain(name, base, dark, w=128, h=32, seed=1, rays=0.0):
    """wood: long streaks down the piece (u), a few darker lines, the odd fleck (oak rays)"""
    def draw(px):
        r = np.random.default_rng(seed); b, d = hexrgb(base), hexrgb(dark); line = r.random(h); ph = r.random(h) * 6.28
        for row in range(h):
            for col in range(w):
                k = 0.5 + 0.5 * math.sin(col * 0.11 + ph[row]); c = b * (0.9 + 0.14 * k * line[row])
                if line[row] > 0.82: c = c * 0.55 + d * 0.45
                if rays and r.random() < rays: c = c * 0.8
                px[row, col] = c * (0.97 + 0.06 * r.random())
    return tex_canvas(name, w, h, draw)


# ------------------------------------------------------------------------------------------------ the steel blade
NAGASA, SORI = 0.70, 0.017; MOTOHABA, SAKIHABA = 0.031, 0.0215; KASANE0, KASANE1 = 0.0070, 0.0050
KISSAKI, RIDGE, SHINOGI0, SHINOGI1, Y0, HABAKI = 0.040, 0.0014, 0.70, 0.74, 0.0151, 0.034
R_ARC = (NAGASA * NAGASA / 4 + SORI * SORI) / (2 * SORI)
T_TIP = 2 * math.asin(NAGASA / (2 * R_ARC)); T_YOKOTE = T_TIP - KISSAKI / R_ARC
TIP = (-R_ARC * math.sin(T_TIP), Y0 + R_ARC * (1 - math.cos(T_TIP)))  # (z, y) in the blade's own space
UB = 0.88  # the skin's u at the yokote: the body is 0 .. UB, the kissaki UB .. 1
ROOT = 0.0015  # the blade starts this far in front of its origin (inside the habaki, clear of its back)


def hamon_at(s):  # height of the temper line above the edge (m): straight at the machi, waves, calm at the yokote
    start, calm = min(1, s / 0.08), min(1, (1 - s) / 0.1)
    wave = 0.0021 * math.sin(s * 58 + 0.6) + 0.0012 * math.sin(s * 131 + 2.1) + 0.0006 * math.sin(s * 19)
    return 0.0042 + (0.0034 + wave) * start * calm


def katana_blade(z_origin, name, pre='kt'):
    """the shinogi-zukuri blade (katana.js bladeMesh): one even arc, the shinogi ridge 70-74% up, a peaked mune, a chu-
    kissaki behind its yokote. returns (node with its origin at z_origin, katLen, tip (y, z) in model space)"""
    NM, NK = 44, 9; st = []
    t0 = math.asin(ROOT / R_ARC)
    for i in range(NM + 1):
        s = i / NM; W = MOTOHABA + (SAKIHABA - MOTOHABA) * (s * 0.85 + s * s * 0.15)
        k = (KASANE0 + (KASANE1 - KASANE0) * s) / 2; vs = SHINOGI0 + (SHINOGI1 - SHINOGI0) * s
        st.append((t0 + (T_YOKOTE - t0) * s, W, [(0.0, 0.00012), (vs, k), (1 - RIDGE / W, k * 0.8), (1.0, 0.0)], UB * s))
    dKs, kY = (1 - SHINOGI1) * SAKIHABA, KASANE1 / 2
    for j in range(1, NK + 1):
        u = j / NK; W = SAKIHABA * (1 - u ** 1.6)
        if W < 1e-5: st.append((T_TIP, 0.0, [(0.0, 0.0), (0.4, 0.0), (0.8, 0.0), (1.0, 0.0)], 1.0)); continue
        k = kY * (1 - u) ** 0.9; vks = max(0.3, 1 - dKs * (1 - u) / W); vm = max(vks + 0.02, 1 - RIDGE * (1 - u) / W)
        st.append((T_YOKOTE + (T_TIP - T_YOKOTE) * u, W, [(0.0, 0.00012 * (1 - u)), (vks, k), (vm, k * 0.8), (1.0, 0.0)], UB + (1 - UB) * u))
    rings, uvs = [], []
    for t, W, rows, u in st:
        zS, yS = -R_ARC * math.sin(t), Y0 + R_ARC * (1 - math.cos(t)); zE, yE = zS - W * math.sin(t), yS - W * math.cos(t)
        P = lambda r, sx: (sx * r[1], yE + (yS - yE) * r[0], z_origin + zE + (zS - zE) * r[0])
        ring = [P(r, 1) for r in rows] + [P(r, -1) for r in rows[-2::-1]]  # up one side, down the other (the ridge is shared)
        rings.append(ring); uvs.append([(u, r[0]) for r in rows] + [(u, r[0]) for r in rows[-2::-1]])
    # ---- the polish, painted: hamon, ji, burnished shinogi-ji and mune, the kissaki's own finish, the yokote line
    HAM, JI, SJI, MUNE, NAR = hexrgb(0xf4f6f8), hexrgb(0xb4bcc6), hexrgb(0x87929f), hexrgb(0x96a0ac), hexrgb(0xdde2e7)
    def draw(px):
        h, w = px.shape[0], px.shape[1]; r = np.random.default_rng(7)
        for col in range(w):
            u = (col + 0.5) / w
            for row in range(h):
                v = 1 - (row + 0.5) / h
                if u < UB:
                    s = u / UB; W = MOTOHABA + (SAKIHABA - MOTOHABA) * (s * 0.85 + s * s * 0.15); vs = SHINOGI0 + (SHINOGI1 - SHINOGI0) * s; vh = hamon_at(s) / W
                    if v < vh: c = HAM
                    elif v < vh + 0.035: c = HAM * 0.55 + JI * 0.45  # the misty line where the hamon lets go
                    elif v < vs: c = JI * (0.96 + 0.07 * (0.5 + 0.5 * math.sin(s * 310 + v * 23)))  # the grain of the steel, faint
                    elif v < 1 - RIDGE / W: c = SJI
                    else: c = MUNE
                    if UB - u < 1.5 / w and v < vs: c = HAM  # the yokote
                else:
                    q = (u - UB) / (1 - UB); W = max(1e-5, SAKIHABA * (1 - q ** 1.6)); vks = max(0.3, 1 - dKs * (1 - q) / W)
                    vb = min(vks - 0.06, 0.0042 / W)
                    c = HAM if v < vb else NAR if v < vks else SJI if v < 0.94 else MUNE
                px[row, col] = c * (0.985 + 0.03 * r.random())
    bm_ = mat(pre + '_blade', 0xffffff, rough=0.1, metal=0.96, tex=tex_canvas(pre + '_blade_t', 512, 64, draw))
    o = ring_solid(rings, uvs, bm_, pre + '_blade', caps=(True, False), angle=24)
    node = part([o], name, pivot=(0, 0, z_origin))
    return node, -TIP[0], (TIP[1], z_origin + TIP[0])


def habaki(z_back, m, name='habaki'):
    """the blade collar: a wedge sleeve, deeper and thicker at the back, its mouth stepped where it grips the blade"""
    def sec(z, hx, top, bot): return [(hx * 0.5, top, z), (hx, top - 0.0026, z), (hx, bot + 0.0038, z), (hx * 0.42, bot, z), (-hx * 0.42, bot, z), (-hx, bot + 0.0038, z), (-hx, top - 0.0026, z), (-hx * 0.5, top, z)]
    lp = [sec(z_back, 0.0066, Y0 + 0.0030, Y0 - MOTOHABA - 0.0026), sec(z_back - 0.011, 0.0063, Y0 + 0.0029, Y0 - MOTOHABA - 0.0024),
          sec(z_back - 0.0116, 0.0059, Y0 + 0.0026, Y0 - MOTOHABA - 0.0021), sec(z_back - HABAKI, 0.0054, Y0 + 0.0024, Y0 - MOTOHABA - 0.0018)]
    o = loft_loops(lp, m, name, angle=30, crown=(0.0004, 0.0004)); uvb(o, 0.02)
    return o


def filed(name, base, dark, seed=3):
    """the habaki's neko-gaki: slanted file strokes over gold-washed copper"""
    def draw(px):
        r = np.random.default_rng(seed); b, d = hexrgb(base), hexrgb(dark)
        for row in range(32):
            for col in range(32): px[row, col] = (b * 0.78 + d * 0.22 if (col + row) % 5 == 0 else b) * (0.93 + 0.14 * r.random())
    return tex_canvas(name, 32, 32, draw)


# ------------------------------------------------------------------------------------------------ Katana
def katana():
    """the Edo-period uchigatana in full koshirae (public/js/blades/katana.js): 70 cm shinogi-zukuri blade, gold-washed
    copper habaki, a seppa either side of a round iron tsuba with its two hitsu-ana, shakudo fuchi and domed kashira,
    white ray skin under dark blue hira-maki cord with its diamond windows, gold menuki, a bamboo mekugi, the last turn
    of cord crossing the kashira into gold shitodome. made fun: nothing, it is the one serious thing in the game"""
    Z_FUCHI, Z_KASH = -0.130, 0.130; FUCHI_L, KASHIRA_L, SEPPA_T, TSUBA_T = 0.012, 0.034, 0.002, 0.005
    Z_BLADE = Z_FUCHI - SEPPA_T * 2 - TSUBA_T; ZW0, ZW1 = Z_FUCHI + FUCHI_L - 0.0005, Z_KASH - KASHIRA_L + 0.0005
    PITCH = 0.026; Z_X0 = ZW0 + PITCH / 4; MEN_O, MEN_U, MEN_HALF, MEN_H = Z_X0 + PITCH * 1.5, Z_X0 + PITCH * 6, 0.023, 0.0046
    NR = 20; PHI = [2 * math.pi * i / NR for i in range(NR)]
    CORE = [(Z_FUCHI, 0.0114, 0.0165), (ZW0, 0.0113, 0.0163), (-0.03, 0.0106, 0.0152), (0.04, 0.0106, 0.0153), (ZW1, 0.0109, 0.0156), (Z_KASH, 0.0109, 0.0156)]
    cA, cB = interp([(z, a) for z, a, b in CORE]), interp([(z, b) for z, a, b in CORE])
    oval_at = lambda a, b, phi: (a * spow(math.sin(phi)), b * spow(math.cos(phi)))
    tsuka = lambda z, phi, lift=0.0: oval_at(cA(z) + lift, cB(z) + lift, phi) + (z,)
    loop = lambda z, a, b: [oval_at(a, b, p) + (z,) for p in PHI]
    blade, kat_len, tip = katana_blade(Z_BLADE, 'kat_blade_wzB')
    gold = mat('kt_gold', 0xffffff, rough=0.26, metal=1.0, tex=filed('kt_gold_t', 0xc9963f, 0x7d5a22))
    hb = habaki(Z_BLADE, gold, 'kt_habaki')
    seppa_m = mat('kt_seppa', 0xffffff, rough=0.3, metal=1.0, tex=steel_tex('kt_seppa_t', 0xb98b3a, var=0.06, seed=2))
    sep = [plate(oval(0.0146, 0.0216, 24), SEPPA_T, z, seppa_m, name='kt_seppa', bev=0.0004) for z in (Z_BLADE + SEPPA_T / 2, Z_FUCHI - SEPPA_T / 2)]
    # ---- tsuba: a round iron plate, the kozuka hole (a D) on the omote side and the kogai hole (two lobes) on the ura, a rounded rim
    iron = mat('kt_iron', 0xffffff, rough=0.62, metal=0.75, tex=tex_noise('kt_iron_t', 0x3b342e, var=0.2, size=32, speck=0x6a4630, speck_p=0.07, seed=4))
    kozuka = [(-0.0150, 0.0125), (-0.0150, -0.0125)] + [(-0.0150 - 0.0072 * math.sin(math.pi * (1 - (i + 1) / 8)), 0.0125 * math.cos(math.pi * (1 - (i + 1) / 8))) for i in range(7)]
    kogai = [(0.0150, 0.0125), (0.0193, 0.0121), (0.0221, 0.0088), (0.0207, 0.0038), (0.0186, 0), (0.0207, -0.0038), (0.0221, -0.0088), (0.0193, -0.0121), (0.0150, -0.0125)]
    zc = Z_FUCHI - SEPPA_T - TSUBA_T / 2; zf, zb = zc - TSUBA_T / 2, zc + TSUBA_T / 2
    body = side_x(oval(0.0358, 0.0378, 32), TSUBA_T, (0, 0, zc), iron, name='kt_tsuba', holes=[kozuka, kogai], bev=0.0003, seg=1)
    rim_m = mat('kt_rim', 0xffffff, rough=0.5, metal=0.8, tex=tex_noise('kt_rim_t', 0x463d35, var=0.16, size=16, speck=0x6a4630, speck_p=0.05, seed=5))
    mimi = squash(lathe([(0.0338, zf + 0.0012), (0.0345, zf - 0.0004), (0.0358, zf - 0.0008), (0.0370, zf - 0.0002), (0.0374, zc), (0.0370, zb + 0.0002), (0.0358, zb + 0.0008),
                         (0.0345, zb + 0.0004), (0.0338, zb - 0.0012), (0.0338, zf + 0.0012)], (0, 0, 0), rim_m, seg=32, name='kt_mimi', cap=False), 1.0, 0.0392 / 0.0372)
    # ---- fuchi and kashira: shakudo, blue-black
    shak = mat('kt_shakudo', 0xffffff, rough=0.3, metal=0.85, clearcoat=0.4, tex=tex_noise('kt_shakudo_t', 0x26242b, var=0.16, size=16, speck=0x4a4052, speck_p=0.1, seed=6))
    fuchi = loft_loops([loop(Z_FUCHI, 0.0134, 0.0193), loop(Z_FUCHI + 0.001, 0.0138, 0.0198), loop(Z_FUCHI + FUCHI_L - 0.0015, 0.0136, 0.0195), loop(Z_FUCHI + FUCHI_L, 0.0130, 0.0186)], shak, 'kt_fuchi', angle=40)
    KA, KB = 0.0134, 0.0184; z0k = Z_KASH - KASHIRA_L; Z_SHI = z0k + 0.016
    kash = loft_loops([loop(z, KA * k, KB * k) for z, k in ((z0k, 0.97), (z0k + 0.002, 1), (Z_KASH - 0.007, 1), (Z_KASH - 0.0025, 0.9), (Z_KASH - 0.0005, 0.66), (Z_KASH, 0.4))], shak, 'kt_kashira', angle=40, crown=(0.0, 0.0006))
    # ---- the core: white ray skin, its nodes showing in the diamonds
    same = mat('kt_same', 0xffffff, rough=0.55, tex=tex_noise('kt_same_t', 0xe8e2d2, var=0.1, size=32, speck=0xbdb39a, speck_p=0.3, seed=7))
    core = loft_loops([[tsuka(z, p) for p in PHI] for z in (ZW0 - 0.004, -0.09, -0.03, 0.04, ZW1 + 0.004)], same, 'kt_core', angle=60)
    for o in sep + [body, mimi, fuchi, kash, core]: uvb(o, 0.02)
    # ---- the ito: two cords wound opposite ways, crossing on the side faces every pitch
    ito_m = mat('kt_ito', 0xffffff, rough=0.7, tex=weave('kt_ito_t', 0x26305a, 0x161d3c, seed=8))
    LIFT, OVER, CROWN, TH, L = 0.00135, 0.0019, 0.0008, 0.0011, PITCH  # (the top cord rides on the lower one's back)
    def bump(z, phi):
        s = math.sin(phi)
        for zm, sd in ((MEN_O, -1), (MEN_U, 1)):
            if s * sd > 0.99 and abs(z - zm) < MEN_HALF: return MEN_H * 0.85
        return 0.0
    turn = [(145, -L / 4), (117.5, -L / 8), (90, 0), (62.5, L / 8), (35, L / 4), (0, L / 4), (-35, L / 4), (-62.5, 3 * L / 8), (-90, L / 2), (-117.5, 5 * L / 8), (-145, 3 * L / 4), (-180, 3 * L / 4)]
    def cut(smp, z0, z1, surf, TH=TH):
        """samples (phi, z, width, lift) -> strap sections, clipped to z0 .. z1; a run ends where the cord leaves that span"""
        runs, cur = [], []
        for phi, z, wz, lift in smp:
            za, zb_, zm = min(z1, max(z0, z - wz / 2)), min(z1, max(z0, z + wz / 2)), min(z1, max(z0, z))
            if zb_ - za < 0.0015:
                if len(cur) > 1: runs.append(cur)
                cur = []; continue
            zm = min(zb_ - 0.0005, max(za + 0.0005, zm))
            cur.append([surf(za, phi, lift - TH), surf(za, phi, lift), surf(zm, phi, lift + CROWN), surf(zb_, phi, lift), surf(zb_, phi, lift - TH)])
        if len(cur) > 1: runs.append(cur)
        return runs
    cords = []
    for cord in (0, 1):
        raw = []
        for mth in range(-1, math.ceil((ZW1 - ZW0) / L) + 2):
            for p, dz in turn:
                phi = math.radians(180 - p if cord else p) - (2 * math.pi * mth if not cord else -2 * math.pi * mth); z = Z_X0 + dz + mth * L; s = math.sin(phi)
                over = (cord == 0 and s > 0.5) or (cord == 1 and s < -0.5)
                raw.append((phi, z, 0.0112 if abs(s) > 0.99 else 0.75 * L + 0.0016 if abs(s) > 0.8 else L / 2, LIFT + (OVER if over else 0) + bump(z, phi)))
        smp = []
        for a, b in zip(raw, raw[1:]):  # one more sample between each pair: the cord rounds the corners
            smp += [a, tuple((x + y) / 2 for x, y in zip(a, b))]
        smp.append(raw[-1])
        for run in cut(smp, ZW0, ZW1, tsuka): cords.append(strap(run, ito_m, 'kt_ito'))
    # the last turn: each cord crosses over the kashira into the eyelet on the far side
    ksurf = lambda z, phi, lift: oval_at(KA + lift, KB + lift, phi) + (z,)
    zk0 = z0k + 0.004
    for sd in (1, -1):
        smp = [(math.radians(sd * d), zk0 + (Z_SHI - zk0) * i / 5, 0.0080, 0.0013 + (OVER if sd > 0 else 0)) for i, d in enumerate((75, 35, 0, -35, -70, -90))]
        fine = []
        for a, b in zip(smp, smp[1:]): fine += [a, tuple((x + y) / 2 for x, y in zip(a, b))]
        fine.append(smp[-1])
        for run in cut(fine, zk0 - 0.0035, Z_KASH - 0.007, ksurf, TH=0.0016 + (OVER + 0.0012 if sd > 0 else 0)): cords.append(strap(run, ito_m, 'kt_itok'))
    # ---- menuki: a pair of gold ornaments under the cord, staggered; the mekugi; the shitodome eyelets
    orn = mat('kt_menuki', 0xffffff, rough=0.22, metal=1.0, tex=steel_tex('kt_menuki_t', 0xd8a83c, var=0.08, seed=9, speck=0x8e6a1e, p=0.08))
    prof = [(-1, 0), (-0.72, 0.62), (0, 1), (0.72, 0.62), (1, 0)]; along = [(-1, 0.3), (-0.78, 0.85), (-0.42, 1), (0, 0.72), (0.42, 1), (0.78, 0.85), (1, 0.3)]
    trims = []
    for zc_, sd in ((MEN_O, -1), (MEN_U, 1)):
        lp = [[(sd * (cA(zc_ + f * MEN_HALF) - 0.001 + h * (MEN_H + 0.001) * sc), u * 0.0074 * sc, zc_ + f * MEN_HALF) for u, h in prof] for f, sc in along]
        trims.append(loft_loops(lp, orn, 'kt_menuki', angle=50, crown=(0.0003, 0.0003)))
    bamboo = mat('kt_mekugi', 0xffffff, rough=0.6, tex=tex_noise('kt_mekugi_t', 0xb28a52, var=0.1, size=8, seed=10))
    trims += [stud(0.0022, cA(Z_X0), 0.0009, (0, 0, Z_X0), bamboo, sx, seg=8, name='kt_mekugi', tip=(0.5, 0.65)) for sx in (1, -1)]
    trims += [stud(0.0026, KA + (0.0024 if sx > 0 else 0.0043), 0.001, (0, 0, Z_SHI), orn, sx, seg=10, name='kt_shitodome', sink=0.007, tip=(0.45, 0.6)) for sx in (1, -1)]  # (each through the cord that ends there)
    for o in trims: uvb(o, 0.02)
    meta = {'kind': 'weapon', 'id': 'katana', 'paint': [], 'muzzle': [0, round(tip[0], 5), round(tip[1], 5)], 'katBlade': 'kat_blade_wzB', 'katLen': round(kat_len, 5),
            'hatAt': [[0, 0.019, -0.01], 0.055]}
    parts = [blade] + zone_join([core, fuchi, kash] + cords, 'kat_tsuka', {}, default='a') + zone_join([hb, body, mimi] + sep, 'kat_guard', {}, default='b') + zone_join(trims, 'kat_trims', {}, default='n')
    return finish('w_katana', parts, meta)


# ------------------------------------------------------------------------------------------------ Shirasaya
def shirasaya():
    """the plain storage mount (public/js/blades/shirasaya.js): the same blade and habaki in an unvarnished honoki
    handle, no guard, no wrap, one bamboo peg; the handle follows the tang's slight curve. made fun: someone has
    brushed a name down the side and it has mostly rubbed off"""
    Z_MOUTH, Z_END, RISE = -0.130, 0.130, 0.0055; RT = (Z_END - Z_MOUTH) ** 2 / (2 * RISE); Z_MEK = Z_MOUTH + 0.050
    PROF = [(Z_MOUTH, 0.0132, 0.0201), (-0.080, 0.0129, 0.0195), (0.000, 0.0124, 0.0186), (0.080, 0.0121, 0.0181), (Z_END, 0.0120, 0.0179)]
    pa, pb = interp([(z, a) for z, a, b in PROF]), interp([(z, b) for z, a, b in PROF])
    yc = lambda z: (z - Z_MOUTH) ** 2 / (2 * RT)
    def nrm(z): s = (z - Z_MOUTH) / RT; l = math.hypot(s, 1); return -s / l, 1 / l
    NS = 20
    def section(z, k=1.0):
        a, b = pa(z), pb(z); nz, ny = nrm(z); y0 = yc(z); pts = []
        for i in range(NS):
            phi = 2 * math.pi * i / NS; c = math.cos(phi)
            x = a * k * spow(math.sin(phi), 0.78) * (1 + 0.07 * c if c < 0 else 1); u = b * k * spow(c, 0.9)
            pts.append((x, y0 + u * ny, z + u * nz))
        return pts
    blade, kat_len, tip = katana_blade(Z_MOUTH, 'shira_blade_wzB', pre='sh')
    gold = mat('sh_gold', 0xffffff, rough=0.26, metal=1.0, tex=filed('sh_gold_t', 0xc9963f, 0x7d5a22, seed=13))
    hb = habaki(Z_MOUTH, gold, 'sh_habaki')
    def wood_px(px):  # honoki: pale, straight grained; a brushed name (sayagaki) down one side, worn
        h, w = px.shape[0], px.shape[1]; r = np.random.default_rng(15); b, d, ink = hexrgb(0xe6dbb9), hexrgb(0xc9b78e), hexrgb(0x3a342c); line = r.random(h); ph = r.random(h) * 6.28
        for row in range(h):
            for col in range(w):
                k = 0.5 + 0.5 * math.sin(col * 0.09 + ph[row]); c = b * (0.93 + 0.09 * k * line[row])
                if line[row] > 0.86: c = c * 0.7 + d * 0.3
                if 0.2 < row / h < 0.3 and 0.25 < col / w < 0.7 and (col // 5) % 3 != 2 and ((col % 5) in (1, 2) or row % 3 == 0) and r.random() > 0.35: c = c * 0.45 + ink * 0.55
                px[row, col] = c * (0.97 + 0.06 * r.random())
    wood = mat('sh_honoki', 0xffffff, rough=0.72, tex=tex_canvas('sh_honoki_t', 128, 40, wood_px))
    st = [(Z_MOUTH, 0.955), (Z_MOUTH + 0.0012, 1), (-0.08, 1), (-0.02, 1), (0.04, 1), (0.1, 1), (Z_END - 0.0045, 1), (Z_END - 0.0015, 0.965), (Z_END, 0.88)]
    rings = [section(z, k) for z, k in st]
    uvs = [[((z - Z_MOUTH) / (Z_END - Z_MOUTH), i / NS) for i in range(NS)] for z, k in st]
    tsuka = ring_solid(rings, uvs, wood, 'sh_tsuka', angle=50, crown=(0.0, 0.0015))
    peg = mat('sh_mekugi', 0xffffff, rough=0.6, tex=tex_noise('sh_mekugi_t', 0x7a5530, var=0.1, size=8, seed=16))
    pegs = []
    for sx, r, h in ((-1, 0.0030, 0.0011), (1, 0.0026, 0.0008)):  # the thick end stands proud on the omote side
        o = stud(r, pa(Z_MEK), h, (0, yc(Z_MEK), Z_MEK), peg, sx, seg=8, name='sh_mekugi', tip=(0.5, 0.65)); uvb(o, 0.02); pegs.append(o)
    meta = {'kind': 'weapon', 'id': 'katana', 'skin': 'katana_shirasaya', 'paint': [], 'muzzle': [0, round(tip[0], 5), round(tip[1], 5)], 'katBlade': 'shira_blade_wzB', 'katLen': round(kat_len, 5),
            'hatAt': [[0, round(yc(0.03) + pb(0.03) - 0.0004, 5), 0.03], 0.055]}
    parts = [blade] + zone_join([tsuka], 'shira_tsuka', {}, default='a') + zone_join([hb], 'shira_habaki', {}, default='b') + zone_join(pegs, 'shira_pegs', {}, default='n')
    return finish('w_katana_shirasaya', parts, meta)


# ------------------------------------------------------------------------------------------------ Bokken
def bokken():
    """the one-piece red oak practice sword (public/js/blades/bokken.js): 102 cm on one gentle arc, an oval handle, an
    egg-shaped blade with a flat spine, a soft shinogi and a blunt edge, a small blunt point; a black plastic guard
    wedged on with its white rubber keeper. the blade is the katBlade node: yes, the wood grows too"""
    R = 4.65; yc = lambda z: z * z / (2 * R)
    def at(z, u): a = -z / R; l = math.hypot(a, 1); return z + a / l * u, yc(z) + u / l
    Z_BUTT, Z_GUARD, TSUBA_T = 0.13, -0.13, 0.0065; Z_BLADE = Z_GUARD - TSUBA_T / 2; Z_TIP, KISS = -0.89, 0.024
    H0, W0, HY, WY, U_TIP = 0.034, 0.024, 0.0295, 0.0185, 0.28
    KST = [(0.14, 0.93), (0.28, 0.86), (0.42, 0.78), (0.56, 0.7), (0.69, 0.61), (0.8, 0.52), (0.89, 0.43), (0.95, 0.3)]
    BSEC = [(1, 0), (1, 0.5), (0.955, 0.8), (0.85, 0.97), (0.68, 1), (0.4, 0.86), (0.15, 0.54), (0.04, 0.3), (0, 0)]
    OSEC = [(1, 0), (0.985, 0.48), (0.93, 0.82), (0.82, 0.98), (0.62, 1), (0.38, 0.99), (0.18, 0.93), (0.07, 0.76), (0.015, 0.44), (0, 0)]
    station = lambda z, h, w: (at(z, h / 2), at(z, -h / 2), w)
    def solid(st, sec, m, name, caps, crown=(0.0, 0.0), u0=0.0, tile=0.3):
        rings, uvs = [], []; n = 2 * len(sec) - 2; acc = 0.0; prev = None
        for S, E, w in st:
            P = lambda q, sx: (sx * q[1] * w / 2, E[1] + (S[1] - E[1]) * q[0], E[0] + (S[0] - E[0]) * q[0])
            mid = ((S[0] + E[0]) / 2, (S[1] + E[1]) / 2)
            if prev: acc += math.hypot(mid[0] - prev[0], mid[1] - prev[1])
            prev = mid
            rings.append([P(q, 1) for q in sec] + [P(q, -1) for q in sec[-2:0:-1]]); uvs.append([(u0 + acc / tile, k / n) for k in range(n)])
        return ring_solid(rings, uvs, m, name, caps=caps, angle=40, crown=crown)
    oak = mat('bo_oak', 0xffffff, rough=0.5, clearcoat=0.2, tex=grain('bo_oak_t', 0xb8714a, 0x86492b, seed=21, rays=0.04))
    grip = mat('bo_grip', 0xffffff, rough=0.6, tex=grain('bo_grip_t', 0xa8643f, 0x7a4226, seed=22, rays=0.04))  # the handled end: a shade darker, duller
    tsuka = solid([station(Z_BUTT, 0.032, 0.022), station(Z_BUTT - 0.002, 0.036, 0.026), station(0, 0.0355, 0.0255), station(Z_GUARD, 0.035, 0.025), station(Z_GUARD - 0.0005, 0.035, 0.025)],
                  OSEC, grip, 'bo_tsuka', (True, True), crown=(0.0004, 0.0))
    plastic = mat('bo_tsuba', 0xffffff, rough=0.4, clearcoat=0.3, tex=tex_noise('bo_tsuba_t', 0x1c1c1f, var=0.12, size=16, speck=0x2e2e33, speck_p=0.1, seed=23))
    y_g = yc(Z_GUARD)
    tsuba = plate([(math.cos(2 * math.pi * i / 28) * 0.038, y_g + math.sin(2 * math.pi * i / 28) * 0.038) for i in range(28)], TSUBA_T - 0.002, Z_GUARD, plastic, name='bo_tsubap', bev=0.001); uvb(tsuba, 0.03)
    rubber = mat('bo_dome', 0xffffff, rough=0.75, tex=tex_noise('bo_dome_t', 0xe6e1d6, var=0.07, size=16, speck=0xb9b2a2, speck_p=0.06, seed=24))
    dome = solid([station(Z_BLADE, 0.042, 0.032), station(Z_BLADE - 0.0125, 0.042, 0.032), station(Z_BLADE - 0.0145, 0.0385, 0.0285)], OSEC, rubber, 'bo_dome', (True, True), crown=(0.0, 0.0003), tile=0.05)
    lerp = lambda a, b, t: a + (b - a) * t
    bez = lambda p0, p1, p2, s: tuple((1 - s) * (1 - s) * p0[k] + 2 * (1 - s) * s * p1[k] + s * s * p2[k] for k in (0, 1))
    def stations(zp):
        zy = zp + KISS; st = [station(lerp(Z_BLADE + 0.0025, zy, k / 14), lerp(H0, HY, k / 14), lerp(W0, WY, k / 14)) for k in range(15)]
        a = -zp / R; zEnd = zp - a / math.hypot(a, 1) * U_TIP * HY; kz = lambda t: lerp(zy, zEnd, t)
        for s, wf in KST:
            sp, ed = bez((0, 0.5), (0.5, 0.5), (1, U_TIP), s), bez((0, -0.5), (0.4, -0.5), (1, U_TIP), s)
            st.append((at(kz(sp[0]), sp[1] * HY), at(kz(ed[0]), ed[1] * HY), WY * wf))
        return st
    tip_of = lambda st: ((st[-1][0][0] + st[-1][1][0]) / 2, (st[-1][0][1] + st[-1][1][1]) / 2)
    zp = Z_TIP; zp += Z_TIP - tip_of(stations(zp))[0]; st = stations(zp); tz, ty = tip_of(st)
    bl = solid(st, BSEC, oak, 'bo_blade', (True, True), crown=(0.0, 0.0008), u0=0.3)
    blade = part([bl], 'bok_blade_wzB', pivot=(0, 0, Z_BLADE))
    meta = {'kind': 'weapon', 'id': 'katana', 'skin': 'katana_bokken', 'paint': [], 'muzzle': [0, round(ty, 5), round(tz, 5)], 'katBlade': 'bok_blade_wzB', 'katLen': round(Z_BLADE - tz, 5),
            'hatAt': [[0, 0.0178, 0.05], 0.06]}
    parts = [blade] + zone_join([tsuka], 'bok_tsuka', {}, default='a') + zone_join([tsuba, dome], 'bok_guard', {}, default='n')
    return finish('w_katana_bokken', parts, meta)


BUILD = {'katana': (katana, 'w_katana'), 'katana_shirasaya': (shirasaya, 'w_katana_shirasaya'), 'katana_bokken': (bokken, 'w_katana_bokken')}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(argv[argv.index('--only') + 1].split(',')) if '--only' in argv else None
main_multi(lambda: [(fn(), fid) for k, (fn, fid) in BUILD.items() if not only or k in only], exposure=-0.3)
