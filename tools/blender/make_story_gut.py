# OVERDUE story props, THE GUT (part 1): the living meat district's street furniture. Cartoony claymation gross: wet
# glossy flesh, bone, teeth, eyes, veins that carry light. Flesh materials are named *pulse* / *lung* / *flesh* so the
# game breathes them (welded smooth shells). Part 2 (the launderette, the Gristle & Sons sign, flesh blobs) is
# make_story_gut2.py.
# run: blender -b --python tools/blender/make_story_gut.py [-- --only=ribarch,lung --no-sheet]
# props -> public/models/story/s_<id>.glb, sheets -> tools/blender/sheets/story/s_<id>.jpg
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gutkit import *
from gutkit import _image, _obj, _link, _place, _waves


def meta_of(id_, **kw):
    d = {'kind': 'prop', 'id': id_, 'story': True, 'district': 'gut'}; d.update(kw); return d


# ---------------------------------------------------------------- 1. rib arch: a ribcage arch over an avenue
def rib_path(s, X=7.25, Y=10.3, n=30, xe=1.45):
    """one rib from the street (x = s*X) up to the spine, an ellipse quarter with a little twist in z."""
    out = []
    e = math.acos(xe / X)
    for i in range(n + 1):
        t = i / n
        ph = e * (t ** 0.9)
        out.append((s * X * math.cos(ph), max(-0.1, Y * math.sin(ph) - 0.1), 0.2 * math.sin(t * math.pi * 1.2) * s))
    return out


def rib_frame(pts, t):
    f = t * (len(pts) - 1); k = min(int(f), len(pts) - 2); u = f - k
    c = Vector(pts[k]).lerp(Vector(pts[k + 1]), u)
    T = Vector(pts[k + 1]) - Vector(pts[k]); T.z = 0; T.normalize()
    return c, T, Vector((-T.y, T.x, 0)), Vector((0, 0, 1))


def build_ribarch(M):
    P = []; A = P.append
    bone, flesh, vein, glow, en = M['bone'], M['flesh'], M['vein'], M['glow'], M['enamel']
    cart = mat('ra_cartilage', 0xffffff, rough=0.15, clearcoat=1.0, tex=tex_flesh('ra_cart_t', 0xdfe2ff, 0xa9a8e8, 0xffffff, size=32, seed=21, amt=0.5))
    rrf = lambda t: 0.66 - 0.12 * t + 0.16 * math.exp(-(t / 0.09) ** 2)
    TC = 0.27  # the lower part of each rib is costal cartilage (bluish, glossier), a gristle cuff where they meet
    for s in (-1, 1):
        pts = rib_path(s)
        n = len(pts); kc = int(round(TC * (n - 1)))
        tt = [i / (n - 1) for i in range(n)]
        o = sweep(pts[kc:], [rrf(t) for t in tt[kc:]], bone, seg=10, name='ra_rib', squash=(0.62, 1.2))
        lump(o, 0.045, 1.1, seed=5 + s); A(o)
        o = sweep(pts[:kc + 1], [rrf(t) for t in tt[:kc + 1]], cart, seg=10, name='ra_costal', squash=(0.62, 1.2))
        lump(o, 0.03, 1.4, seed=7 + s); A(o)
        c, T, N, B = rib_frame(pts, TC)
        A(sweep([tuple(c - T * 0.28), tuple(c), tuple(c + T * 0.28)], [rrf(TC) * 1.05, rrf(TC) * 1.22, rrf(TC) * 1.05], flesh, seg=10, name='ra_cuff', squash=(0.62, 1.2)))
        # the rib head knob where it meets the spine
        A(ball(0.6, (s * 1.45, 10.1, 0), bone, scale=(0.95, 0.85, 1.25), seg=10, rings=6, name='ra_ribhead'))
        A(ball(0.42, (s * 1.05, 10.3, 0), flesh, scale=(1.0, 1.1, 1.5), seg=8, rings=6, name='ra_gristle'))
        # a vein coiling up the rib, over the cuff
        hel = []; N_ = 40
        for i in range(N_ + 1):
            t = 0.18 + 0.66 * i / N_
            c, T, N, B = rib_frame(pts, t)
            w = 2 * math.pi * 2.6 * i / N_ + (0 if s < 0 else 1.7)
            rr = rrf(t)
            hel.append(tuple(c + N * math.cos(w) * rr * 0.6 + B * math.sin(w) * rr * 1.16))
        A(sweep(hel, 0.11, vein, seg=5, name='ra_vein'))
        # gristle strings hanging off the underside, each with a drip
        for k, (t, ln) in enumerate(((0.42, 1.6), (0.68, 2.3))):
            c, T, N, B = rib_frame(pts, t)
            inn = (Vector((0, 4.5, 0)) - c); inn.z = 0; inn.normalize()
            p0 = c + inn * rrf(t) * 0.45
            sp = [tuple(p0 + Vector((math.sin(j * 1.3 + k) * 0.06, -ln * (j / 6) ** 1.1, 0.04 * j))) for j in range(7)]
            A(sweep(sp, [0.16, 0.12, 0.09, 0.07, 0.06, 0.05, 0.05], flesh, seg=6, name='ra_string'))
            A(ball(0.13, sp[-1], flesh, scale=(1, 1.35, 1), seg=8, rings=5, name='ra_drip'))
        # feet: gristle mounds where the ribs go into the street, a few tooth cobbles shoved up round them
        fx = s * 7.25
        balls = [((fx, 0.1, -0.7), 1.15), ((fx, 0.1, 0.7), 1.15), ((fx - s * 0.45, 0.55, 0), 0.95), ((fx + s * 0.55, 0.0, 0.0), 0.9),
                 ((fx - s * 0.35, 0.0, -1.25), 0.7), ((fx + s * 0.3, 0.0, 1.3), 0.75), ((fx - s * 0.25, 1.05, -0.4), 0.6)]
        o = meta(balls, res=0.16, m=flesh, target=420, name='ra_mound', clamp=lambda p: (p[0], max(p[1], -0.04), p[2]))
        lump(o, 0.06, 2.2, seed=3 + s); A(o)
        for k, (dx, dz, a) in enumerate(((1.15, -0.8, 0.4), (1.05, 1.0, 1.2), (-0.95, 1.3, 2.0), (-0.8, -1.4, 0.7))):
            f = molar if k % 2 == 0 else canine
            A(f(en, pos=(fx + s * dx, -0.04, dz), rot=(0.15 * (k - 1.5), a, 0.1), s=1.6 if k % 2 == 0 else 1.25, name='ra_tooth', seed=k))
    # the spine: two vertebrae along z with gristle discs, the neural arch over a canal, shark-fin spinous processes
    for zv in (-0.55, 0.55):
        A(lathe([(0.0, -0.45), (0.62, -0.47), (0.8, -0.41), (0.72, -0.2), (0.68, 0.0), (0.72, 0.2), (0.8, 0.41), (0.62, 0.47), (0.0, 0.45)],
                (0, 10.0, zv), bone, seg=12, axis='z', name='ra_centrum'))
        apts = [(math.cos(math.radians(a)) * 0.52, 10.92 + math.sin(math.radians(a)) * 0.46, zv) for a in range(-28, 209, 26)]
        A(sweep(apts, 0.24, bone, seg=8, name='ra_arch', squash=(1.0, 1.4)))
        sp = [(0, 11.3, zv - 0.05), (0, 11.6, zv + 0.08), (0, 11.85, zv + 0.25), (0, 12.0, zv + 0.42)]
        A(sweep(sp, [0.3, 0.25, 0.18, 0.08], bone, seg=8, name='ra_spinous', squash=(0.45, 1.45)))
        for s in (-1, 1):
            A(sweep([(s * 0.4, 10.55, zv), (s * 0.85, 10.5, zv * 0.85), (s * 1.3, 10.35, zv * 0.6)], [0.27, 0.22, 0.25], bone, seg=8, name='ra_transverse'))
    A(lathe([(0.0, -0.14), (0.62, -0.14), (0.84, -0.07), (0.88, 0.0), (0.84, 0.07), (0.62, 0.14), (0.0, 0.14)], (0, 10.0, 0), flesh, seg=12, axis='z', name='ra_disc'))
    for zz in (-1.07, 1.07):
        A(lathe([(0.0, -0.11), (0.62, -0.11), (0.74, 0.0), (0.62, 0.11), (0.0, 0.11)], (0, 10.0, zz), flesh, seg=12, axis='z', name='ra_disc_end'))
    # the nerve cord: glows, and droops out of both ends where the spine was cut off
    cord = [(0.06, 8.9, -1.7), (0.0, 9.8, -1.62), (0, 10.62, -1.35), (0, 10.9, -0.7), (0, 10.92, 0), (0, 10.9, 0.7), (0, 10.62, 1.35), (-0.05, 9.7, 1.62), (-0.06, 8.75, 1.72)]
    A(sweep(cord, [0.07, 0.11, 0.14, 0.15, 0.15, 0.15, 0.14, 0.11, 0.07], glow, seg=6, name='ra_nerve'))
    # the lantern organ: a glowing sac hanging off the middle disc on a stringy tendon, a fat cap on top
    A(sweep([(0, 9.3, 0), (0.04, 8.9, 0.03), (0.0, 8.55, 0.0)], [0.09, 0.06, 0.08], vein, seg=6, name='ra_tendon'))
    A(sweep([(0, 9.55, 0), (0, 9.25, 0)], [0.35, 0.12], vein, seg=6, name='ra_tendon_root'))
    sac = lathe([(0.0, 7.1), (0.22, 7.16), (0.45, 7.38), (0.58, 7.7), (0.57, 8.0), (0.46, 8.27), (0.28, 8.43), (0.12, 8.52), (0.0, 8.55)],
                (0, 0, 0), glow, seg=10, axis='y', name='ra_lantern')
    lump(sac, 0.04, 4.0, seed=9); A(sac)
    A(lathe([(0.0, 8.36), (0.36, 8.36), (0.44, 8.42), (0.38, 8.53), (0.17, 8.6), (0.0, 8.62)], (0, 0, 0), flesh, seg=10, axis='y', name='ra_lantern_cap'))
    parts = pack(P, 'ribarch', 0.6)
    return finish('s_ribarch', parts, meta_of('ribarch', col=[16, 12, 2], feet=[[-7.25, 0, 0], [7.25, 0, 0]], footR=1.4,
                                              lights=[[0, 7.8, 0, 0xff4f7a], [0, 10.9, 0, 0xff4f7a]],
                                              note='one pair of ribs off a two-vertebra spine; collide only the feet and the arch, never a 16 m box'))


# ---------------------------------------------------------------- 2. lung trampoline
def build_lung(M):
    P = []; A = P.append
    lungm = mat('lung_tissue', 0xffffff, rough=0.2, clearcoat=1.0,
                tex=tex_cells('lung_t', 0xff7fa3, 0xc8406c, n=40, size=64, seed=31, var=0.1, light=0xffc4d4, bulge=0.35, speck=0x4a2a6a, speck_p=0.02))
    br = mat('lung_bronchi', 0xffffff, rough=0.15, clearcoat=1.0, tex=tex_flesh('lung_br_t', 0xffe0e8, 0xf2a6bf, 0xffffff, size=16, seed=32, amt=0.4))
    fat = mat('lung_fat', 0xffffff, rough=0.22, clearcoat=0.8, tex=tex_cells('lung_fat_t', 0xffd27a, 0xe0a050, n=20, size=32, seed=33, light=0xfff4c8, bulge=0.5))
    dark = mat('lung_dark', 0x3a0a1c, rough=0.3)
    rnd = random.Random(5)
    lobes = []
    for sx in (-1, 1):
        # one lung: a blown-up dome, flat inner side, narrower apex toward the front, a fissure, a cardiac notch on the left
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=22, v_segments=12, radius=1.0)
        for v in bm.verts:
            x, y, z = gg(v.co)
            med = x * sx < 0
            X = x * 1.48 * (0.62 if med else 1.0)
            X *= 1 - 0.22 * max(0, -z) ** 1.5
            Z = z * 2.15 * (1 - 0.06 * y)
            Y = y * 1.5
            if Y < -0.95: Y = -0.95 + (Y + 0.95) * 0.25
            cx = sx * (1.5 + (0.12 if sx < 0 and med and abs(z + 0.1) < 0.6 else 0))
            if sx < 0 and med: X *= 1 - 0.35 * math.exp(-((z - 0.15) / 0.45) ** 2)  # the cardiac notch (room for a heart)
            d = z * 0.75 + x * sx * 0.62 - 0.05  # the oblique fissure between lobes
            g = 1 - 0.12 * math.exp(-(d / 0.07) ** 2) * (1 if y > -0.4 else 0)
            if sx > 0: g -= 0.09 * math.exp(-((z + 0.35 - 0.3 * x) / 0.07) ** 2) * (1 if y > -0.4 and d < 0 else 0)  # the right lung has three lobes
            v.co = gv(cx + X * g, 1.42 + Y * g, 0.25 + Z * g)
        lo = _obj('lung_lobe', bm, lungm); smooth(lo, 89)
        lump(lo, 0.06, 1.5, seed=4 + sx)
        lobes.append(lo); A(lo)
    bvhs = [bvh_of(o) for o in lobes]
    def ontop(x, z, off):
        best = None
        for b in bvhs:
            hit = b.ray_cast(gv(x, 8, z), Vector((0, 0, -1)))
            if hit[0] is not None and (best is None or hit[0].z > best[0].z): best = hit
        if best is None: return None
        return gg(best[0] + best[1] * off)
    branches = []
    def grow(x, z, ang, ln, rad, depth):
        pts = []; rads = []
        for i in range(6):
            t = i / 5
            a = ang + math.sin(t * 3 + depth) * 0.12
            q = ontop(x + math.cos(a) * ln * t, z + math.sin(a) * ln * t, rad * 0.55)
            if q is None: break
            pts.append(q); rads.append(rad * (1 - 0.25 * t))
        if len(pts) > 2: branches.append((pts, rads))
        if depth < 2 and len(pts) == 6:
            ex, ez = x + math.cos(ang) * ln, z + math.sin(ang) * ln
            for da in (-0.5, 0.55):
                grow(ex, ez, ang + da + rnd.uniform(-0.12, 0.12), ln * rnd.uniform(0.75, 0.9), rad * 0.72, depth + 1)
    for sx in (-1, 1):
        grow(sx * 1.05, -0.55, math.atan2(1.0, sx * 0.45), 1.15, 0.13, 0)
    print('JF_LUNG branches', len(branches))
    for pts, rads in branches:
        A(sweep(pts, rads, br, seg=5, name='lung_br'))
    # the windpipe: comes in from the front between the lungs and forks into the two main bronchi, ribbed with
    # cartilage, the open end rearing up like a snorkel (dark inside)
    tp = [(0.0, 1.55, -1.05), (0.0, 1.6, -1.7), (0.0, 1.75, -2.3), (0.0, 2.15, -2.75), (0.0, 2.65, -2.95)]
    path = []; rads = []
    for i in range(15):
        t = i / 14
        f = t * (len(tp) - 1); k = min(int(f), len(tp) - 2); u = f - k
        path.append(tuple(Vector(tp[k]).lerp(Vector(tp[k + 1]), u))); rads.append(0.3 if i % 2 == 0 else 0.35)
    rads[-1] = 0.38
    tr = sweep(path, rads, br, seg=10, name='lung_trachea')
    tr.data.materials.append(dark)
    max(tr.data.polygons, key=lambda p: (len(p.vertices), p.center.z)).material_index = 1
    A(tr)
    for sx in (-1, 1):
        A(sweep([(0.0, 1.55, -1.05), (sx * 0.35, 1.68, -0.95), (sx * 0.75, 1.95, -0.8)], [0.3, 0.24, 0.2], br, seg=8, name='lung_main_br'))
    # the bed of fat it sits in
    balls = []
    for gx in range(-4, 5):
        for gz in range(-3, 4):
            x, z = gx * 0.72, gz * 0.75 + 0.25
            if (x / 3.2) ** 2 + ((z - 0.2) / 2.65) ** 2 < 1:
                balls.append(((x + rnd.uniform(-0.12, 0.12), 0.0, z + rnd.uniform(-0.12, 0.12)), rnd.uniform(0.85, 1.0)))
    fb = meta(balls, res=0.15, m=fat, target=460, name='lung_fatbed', clamp=lambda p: (p[0], max(p[1], -0.02), p[2]))
    lump(fb, 0.05, 2.2, seed=6); A(fb)
    parts = pack(P, 'lung', 0.7)
    return finish('s_lung', parts, meta_of('lung', col=[6.0, 2.8, 5.0], bounce=True, note='trampoline: the two domes are the bouncy top; lung_* materials breathe'))


# ---------------------------------------------------------------- 3. tooth cobbles (scatter: instanced thousands of times)
def build_tooth(M):
    o = molar(M['enamel'], name='tooth_molar', seed=3)
    uv_box(o, 0.4)
    return finish('s_tooth', [o], meta_of('tooth', scatter=True, col=[0.36, 0.22, 0.34]))


def build_tooth_b(M):
    o = canine(M['enamel'], name='tooth_canine', seed=4)
    uv_box(o, 0.4)
    return finish('s_tooth_b', [o], meta_of('tooth_b', scatter=True, col=[0.16, 0.35, 0.2]))


# ---------------------------------------------------------------- 4. gutter eyeball
def build_eyeball(M):
    P = []
    e = eyeball(M['eye'], 0.2, (0, 0.08, 0), rot=(-0.35, 0, 0), name='eb_eye')
    P.append(e)
    rim = torus(0.205, 0.07, M['flesh'], (0, 0.07, 0), rot=(-0.12, 0, 0), n=12, k=4, name='eb_socket',
                wob=lambda a: 1 + 0.2 * math.sin(3 * a) + 0.12 * math.sin(2 * a + 1) + 0.25 * max(0, math.sin(a)))
    P.append(rim)
    parts = pack(P, 'eyeball', 0.15)
    return finish('s_eyeball', parts, meta_of('eyeball', scatter=True, col=[0.5, 0.3, 0.5], note='looks up and toward -z'))


# ---------------------------------------------------------------- 5. sphincter door
def build_sphincter(M):
    musc = mat('sp_muscle_pulse', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_canvas('sp_muscle_t', 64, 32, _paint_sphincter))
    dark = mat('sp_throat_pulse', 0xffffff, rough=0.25, clearcoat=0.6, tex=tex_flesh('sp_throat_t', 0x5a0c26, 0x2a0410, 0x8a2a4a, size=16, seed=41))
    NA, NF, TW = 60, 10, 0.75
    # rings: (radius, z (wall at 0, -z out of the wall), fold amount, material)
    R = [(1.5, 0.12, 0.0, 0), (1.62, -0.05, 0.0, 0), (1.58, -0.24, 0.02, 0), (1.45, -0.33, 0.04, 0)]
    for i in range(9):
        t = i / 8; r = 1.3 - 0.86 * t
        R.append((r, -0.3 - 0.26 * t ** 0.8, 0.05 + 0.2 * t ** 0.8, 0))
    R += [(0.4, -0.6, 0.14, 0), (0.33, -0.55, 0.07, 1), (0.3, -0.36, 0.03, 1), (0.27, -0.1, 0.0, 1), (0.22, 0.06, 0.0, 1)]
    w_ = _waves(44)
    V = []; F = []; FM = []
    for i, (r, z, fa, mm) in enumerate(R):
        for j in range(NA):
            a = 2 * math.pi * j / NA
            ph = NF * a + TW * (1.5 - r) * 3
            f = math.cos(ph)
            rr = r * (1 + 0.09 * f * min(1, fa * 7)) * (1 + 0.05 * math.sin(3 * a + 1) + 0.03 * math.sin(7 * a)) if r > 0.3 else r * (1 + 0.06 * f)
            zz = z - fa * (0.5 + 0.5 * f) + 0.06 * nz(Vector((math.cos(a) * 2, math.sin(a) * 2, r)), w_, 1.0) * (1 if 0.3 < r < 1.6 else 0)
            V.append((math.cos(a) * rr, 1.5 + math.sin(a) * rr, zz))
    for i in range(len(R) - 1):
        for j in range(NA):
            j2 = (j + 1) % NA
            F.append((i * NA + j, (i + 1) * NA + j, (i + 1) * NA + j2, i * NA + j2)); FM.append(R[i + 1][3])
    c0 = len(V); V.append((0, 1.5, 0.08))  # throat end
    for j in range(NA): F.append(((len(R) - 1) * NA + j, (len(R) - 1) * NA + (j + 1) % NA, c0)); FM.append(1)
    c1 = len(V); V.append((0, 1.5, 0.14))  # back, hidden in the wall
    for j in range(NA): F.append(((j + 1) % NA, j, c1)); FM.append(1)
    def uvf(p):
        x, y = p[0], p[1] - 1.5
        a = math.atan2(y, x); r = math.hypot(x, y)
        return ((NF * a + TW * (1.5 - r) * 3) / (2 * math.pi), min(1, r / 1.6))
    o = mesh('sp_ring', V, F, musc, mats=[dark], fmat=FM)
    # uvs by hand so the crease stripes follow the twisting folds (u counts folds; one texture width = 4 folds)
    me = o.data; lay = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        ls = [(li, uvf(gg(me.vertices[me.loops[li].vertex_index].co))) for li in poly.loop_indices]
        ref = ls[0][1][0]
        for li, (u, v) in ls:
            while u - ref > NF / 2: u -= NF
            while u - ref < -NF / 2: u += NF
            lay.data[li].uv = (u / 4, v)
    o['keepuv'] = 1
    P = [o]
    # little teeth round the lip, pointing into the hole
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        x, y = math.cos(a) * 0.36, 1.5 + math.sin(a) * 0.36
        P.append(canine(M['enamel'], pos=(x, y, -0.42), rot=(0, 0, a + math.pi / 2), s=0.42, name='sp_tooth', seed=k))
    # veins rooting out over the wall: fat at the rim, one fork each, flattened against the brick
    rnd = random.Random(45)
    def vein(a0, r0, ln, rad, da, z0):
        pts = []
        for i in range(7):
            t = i / 6; r = r0 + t * ln
            aa = a0 + da * t + 0.05 * math.sin(t * 5 + a0 * 3)
            pts.append((math.cos(aa) * r, 1.5 + math.sin(aa) * r, z0 * (1 - t) - 0.035 * t))
        pts = [p for p in pts if p[1] > 0.12]
        if len(pts) > 2:
            P.append(sweep(pts, [rad * (1 - 0.6 * i / (len(pts) - 1)) for i in range(len(pts))], M['vein'], seg=6, name='sp_vein', squash=(1.0, 0.75)))
        return pts
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.35 + rnd.uniform(-0.2, 0.2)
        ln = rnd.uniform(1.0, 1.4)
        main = vein(a, 1.35, ln, 0.15, rnd.uniform(-0.25, 0.25), -0.18)
        if len(main) > 4:
            q = main[2]; am = math.atan2(q[1] - 1.5, q[0]); rm = math.hypot(q[0], q[1] - 1.5)
            vein(am, rm, ln * 0.65, 0.08, rnd.choice((-0.45, 0.45)), q[2])
    parts = pack(P, 'sphincter', 0.4)
    return finish('s_sphincter', parts, meta_of('sphincter', mount='wall', wallZ=0, col=[3.2, 3.2, 0.7], hole=[0, 1.5, 0.3],
                                                note='origin bottom centre on the wall plane, front -z; the dark hole is 0.65 m across'))


def _paint_sphincter(px):
    # u = round the ring (4 folds per texture width, follows the twist), v = centre (top row) to rim (bottom row)
    h, w = px.shape[:2]
    rng = np.random.default_rng(42)
    for y in range(h):
        t = y / (h - 1)  # 0 at the hole, 1 at the rim
        base = hexrgb(0x8a2a4a) * (1 - t) + hexrgb(0xff6f91) * t
        if t > 0.86: base = hexrgb(0xff8fae)
        px[y, :] = base
    for x in range(w):
        f = math.cos(2 * math.pi * x / (w / 4))
        if f < -0.55: px[:, x] = px[:, x] * 0.5 + 0.5 * hexrgb(0x6a1030)  # creases
        elif f > 0.85: px[:, x] = px[:, x] * 0.85 + 0.15 * hexrgb(0xffc4d4)  # wet crest
    px *= (0.93 + 0.14 * rng.random((h, w)))[:, :, None]
    px[rng.random((h, w)) < 0.02] = hexrgb(0xffd27a)
    px[:] = px[::-1]


# ---------------------------------------------------------------- 6. tongue door / ramp
def tongue_obj(M, name='tg', s=1.0, pos=(0, 0, 0)):
    top = mat('tg_tongue_pulse', 0xffffff, rough=0.14, clearcoat=1.0, tex=tex_canvas('tg_top_t', 64, 64, _paint_tongue))
    under = mat('tg_under_pulse', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_flesh('tg_under_t', 0xc23a62, 0x8a2a4a, 0xff6f91, seed=61, speck=0x6a48b0, speck_p=0.03))
    path = [(0, 0.78, 0.6), (0, 0.72, 0.35), (0, 0.62, 0.08), (0, 0.5, -0.2), (0, 0.34, -0.5), (0, 0.24, -0.85), (0, 0.21, -1.2), (0, 0.2, -1.55),
            (0, 0.21, -1.9), (0, 0.22, -2.15), (0, 0.25, -2.38), (0, 0.3, -2.56), (0, 0.38, -2.7), (0, 0.46, -2.78)]
    C = []
    for k in range(len(path) - 1):
        for u in (0, 0.5):
            C.append(tuple(Vector(path[k]).lerp(Vector(path[k + 1]), u)))
    C.append(path[-1])
    K = 18
    def ring(i, t):
        if t < 0.7: hw = 0.66 + 0.14 * math.sin(min(1, t / 0.55) * math.pi * 0.5)
        else: hw = 0.8 * math.sqrt(max(0.03, 1 - ((t - 0.7) / 0.3) ** 2))
        ht = (0.3 - 0.15 * t) * (1 if t < 0.88 else max(0.4, 1 - (t - 0.88) / 0.12))
        wob = 1 + 0.04 * math.sin(t * 17)
        out = []
        for k in range(K):
            a = 2 * math.pi * k / K
            sa, ca = math.sin(a), math.cos(a)
            up = sa * ht * (1 - 0.1 * ca * ca + 0.12 * math.exp(-((abs(ca) - 0.5) / 0.22) ** 2))
            if sa < 0: up = max(up, -ht * 0.7)
            if sa > 0: up -= 0.11 * math.exp(-(ca / 0.22) ** 2) * (1 - t * 0.5)  # the groove down the middle
            out.append((up * s, ca * hw * wob * s))
        return out
    cen = [tuple(Vector(pos) + Vector(c) * s) for c in C]
    o = loft(cen, ring, top, name=name + '_tongue', cap=True, close=(False, True), up=(0, 1, 0), smooth_angle=80)
    o.data.materials.append(under)
    for p in o.data.polygons:
        if p.normal.z < -0.25: p.material_index = 1  # underside (blender z = game y)
    me = o.data; lay = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            g = gg(o.matrix_world @ me.vertices[me.loops[li].vertex_index].co)
            lay.data[li].uv = ((g[0] - pos[0]) / (1.7 * s) + 0.5, -(g[2] - pos[2] - 0.6 * s) / (3.4 * s))
    o['keepuv'] = 1
    parts = [o]
    # big papillae in a V at the back of the tongue, half sunk
    for k, (x, z) in enumerate(((-0.4, -0.12), (-0.27, -0.25), (-0.13, -0.35), (0.0, -0.4), (0.13, -0.35), (0.27, -0.25), (0.4, -0.12))):
        y = 0.62 - 0.36 * max(0, -z - 0.0) + 0.17
        b = ball(0.075 * s, (pos[0] + x * s, pos[1] + (y + 0.02 - 0.06 * abs(x)) * s, pos[2] + z * s), top, scale=(1, 0.75, 1), seg=8, rings=5, name=name + '_pap')
        parts.append(b)
    return parts


def _paint_tongue(px):
    h, w = px.shape[:2]
    rng = np.random.default_rng(62)
    yy, xx = np.mgrid[0:h, 0:w]
    base = np.ones((h, w, 3)) * hexrgb(0xf2557f)
    edge = np.abs(xx + 0.5 - w / 2) / (w / 2)
    base = base * (1 - 0.25 * edge[:, :, None] ** 3)
    groove = np.exp(-((xx + 0.5 - w / 2) / 2.5) ** 2)[:, :, None]
    base = base * (1 - 0.3 * groove)
    px[:] = base * (0.92 + 0.12 * rng.random((h, w)))[:, :, None]
    for k in range(150):  # taste buds: little lighter dots, a few red ones
        x, y = rng.integers(1, w - 1), rng.integers(1, h - 1)
        px[y, x] = px[y, x] * 0.4 + 0.6 * hexrgb(0xffa8bc if k % 6 else 0xe8365f)


def build_tongue(M):
    P = tongue_obj(M, 'tg')
    # the doorway's lower lip, a fat glossy roll the tongue lolls over, with a few bottom teeth either side
    lipm = mat('tg_lip_pulse', 0xffffff, rough=0.12, clearcoat=1.0, tex=tex_flesh('tg_lip_t', 0xff3a6a, 0xc21a4a, 0xff9ab8, size=16, seed=63))
    lip = sweep([(-1.05, 0.14, 0.3), (-0.8, 0.22, 0.1), (-0.42, 0.27, 0.0), (0, 0.25, -0.03), (0.42, 0.27, 0.0), (0.8, 0.22, 0.1), (1.05, 0.14, 0.3)],
                [0.1, 0.2, 0.26, 0.25, 0.26, 0.2, 0.1], lipm, seg=10, name='tg_lip', squash=(1.0, 0.8))
    lump(lip, 0.02, 6, seed=2)
    P.append(lip)
    for k, x in enumerate((-0.92, -0.8, 0.8, 0.92)):
        f = canine if k in (1, 2) else molar
        P.append(f(M['enamel'], pos=(x * 0.95, 0.3, 0.16), rot=(0.2, 0, 0.1 * (x > 0) - 0.05), s=0.75 if f is canine else 0.6, name='tg_tooth', seed=k))
    parts = pack(P, 'tongue', 0.5)
    return finish('s_tongue', parts, meta_of('tongue', mount='door', col=[1.6, 0.5, 3.0], ramp=[[0, 0.78, 0.6], [0, 0.22, -2.6]],
                                             note='origin on the doorway threshold (wall plane z = 0); the root goes 0.6 m into the door, the tip lies 2.8 m out toward -z'))


# ---------------------------------------------------------------- 8. heart lamp
def build_heartlamp(M):
    P = []; A = P.append
    pole = mat('hl_vein', 0xffffff, rough=0.18, clearcoat=1.0, tex=tex_flesh('hl_vein_t', 0x6a48b0, 0x3e2470, 0x9a7ae0, size=32, seed=81, amt=0.55))
    heart = mat('hl_heart_pulse', 0xffffff, rough=0.2, clearcoat=1.0, emit=0xff3a66, strength=2.2,
                tex=tex_canvas('hl_heart_t', 32, 32, _paint_heart), emit_tex=True)
    art = mat('hl_artery_glow_pulse', 0xff8aa8, rough=0.2, emit=0xff3a66, strength=2.0)
    # the pole: a fat vein rising from roots, curling over like a crook; the heart hangs off the end by its aorta
    sp = [(0, -0.05, 0), (0.02, 0.6, 0), (-0.03, 1.4, 0.02), (0.02, 2.3, -0.02), (0.0, 3.2, 0.0), (0.04, 3.95, 0), (0.18, 4.55, 0),
          (0.45, 4.88, 0), (0.78, 4.95, 0), (1.05, 4.8, 0), (1.15, 4.6, 0)]
    rr = [0.15, 0.12, 0.11, 0.105, 0.1, 0.095, 0.09, 0.085, 0.085, 0.09, 0.1]
    o = sweep(sp, rr, pole, seg=8, name='hl_pole'); lump(o, 0.012, 9, seed=8); A(o)
    # an artery twisting up round it, glowing
    hel = []
    for i in range(23):
        t = i / 22; y = 0.15 + 3.75 * t; w = t * 2 * math.pi * 3.5
        hel.append((math.cos(w) * 0.115, y, math.sin(w) * 0.115))
    A(sweep(hel, 0.04, art, seg=5, name='hl_artery'))
    # roots into the street
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        A(sweep([(0, 0.35, 0), (math.cos(a) * 0.3, 0.12, math.sin(a) * 0.3), (math.cos(a) * 0.55, 0.0, math.sin(a) * 0.55)], [0.09, 0.07, 0.04], pole, seg=5, name='hl_root'))
    A(meta([((0, 0.0, 0), 0.42), ((0.12, 0.12, 0.05), 0.3)], res=0.1, m=M['flesh'], target=90, name='hl_base', clamp=lambda p: (p[0], max(p[1], -0.03), p[2])))
    # the heart: a squashed sphere with an apex, two atria on top, a crooked aorta, pulmonary stubs
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=1.0)
    for v in bm.verts:
        x, y, z = gg(v.co)
        k = 1.0 - 0.45 * max(0, -y) ** 1.3  # narrow to the apex
        X, Y, Z = x * 0.42 * k, y * 0.5 - 0.1 * max(0, -y) ** 2, z * 0.37 * k
        X += -0.06 * max(0, -y) ** 2  # the apex points off to one side, like a real one
        Y += 0.05 * math.exp(-((x - 0.5) ** 2 + (y - 0.7) ** 2) * 4) + 0.05 * math.exp(-((x + 0.5) ** 2 + (y - 0.7) ** 2) * 4)
        v.co = gv(1.15 + X, 3.95 + Y, Z)
    hobj = _obj('hl_heart', bm, heart); smooth(hobj, 80); lump(hobj, 0.02, 7, seed=12); A(hobj)
    A(sweep([(1.1, 4.3, 0), (1.15, 4.48, 0), (1.15, 4.62, 0)], [0.14, 0.11, 0.1], heart, seg=8, name='hl_aorta'))
    for dx, dz in ((-0.1, 0.07), (0.12, -0.05)):
        A(sweep([(1.15 + dx * 0.8, 4.3, dz * 0.6), (1.15 + dx * 2.0, 4.5, dz * 1.4), (1.15 + dx * 2.6, 4.55, dz * 2.0)], [0.08, 0.065, 0.06], heart, seg=6, name='hl_stub'))
    parts = pack(P, 'heartlamp', 0.4)
    return finish('s_heartlamp', parts, meta_of('heartlamp', col=[0.4, 5.0, 0.4], lights=[[1.15, 3.9, 0, 0xff3a66]], note='arm and heart reach +x like the streetlight'))


def _paint_heart(px):
    rng = np.random.default_rng(82)
    h, w = px.shape[:2]
    px[:] = hexrgb(0xff3a5e) * (0.88 + 0.15 * rng.random((h, w)))[:, :, None]
    for k in range(5):  # coronary vessels: darker branching lines (they glow less)
        x, y = rng.uniform(0, w), 0.0
        for s in range(8):
            nx, ny = x + rng.uniform(-3, 3), y + rng.uniform(2.5, 4.5)
            px_line(px, x, y, nx, ny, 0x5b1a34, 1.4); x, y = nx, ny
    px[rng.random((h, w)) < 0.03] = hexrgb(0xff9ab8)


# ---------------------------------------------------------------- 9. specimen jar
def build_organjar(M):
    P = []; A = P.append
    glass = mat('oj_glass', 0xd8fff4, rough=0.04, alpha=0.22, clearcoat=1.0)
    fluid = mat('oj_fluid_glow', 0x9adf3a, rough=0.1, emit=0x7dbf1e, strength=0.7, alpha=0.38)
    brass = mat('oj_brass', 0xd8a838, rough=0.22, metal=1.0)
    wood = mat('oj_wood', 0xffffff, rough=0.35, clearcoat=0.6, tex=tex_wood('oj_wood_t', 0x7a3a28, 0x4a1e14, size=32, seed=91))
    label = mat('oj_label', 0xffffff, rough=0.5, tex=tex_canvas('oj_label_t', 96, 48, _paint_jarlabel))
    organ = mat('oj_organ', 0xffffff, rough=0.18, clearcoat=1.0, tex=tex_canvas('oj_brain_t', 32, 32, _paint_brain))
    A(lathe([(0.0, 0.0), (0.44, 0.0), (0.46, 0.04), (0.44, 0.09), (0.4, 0.1), (0.0, 0.1)], (0, 0, 0), wood, seg=12, axis='y', name='oj_plinth'))
    A(lathe([(0.0, 0.09), (0.35, 0.09), (0.38, 0.13), (0.385, 0.9), (0.36, 0.98), (0.33, 1.02)], (0, 0, 0), glass, seg=12, axis='y', name='oj_glass', cap=True))
    A(lathe([(0.0, 0.105), (0.355, 0.105), (0.37, 0.14), (0.372, 0.82), (0.0, 0.82)], (0, 0, 0), fluid, seg=12, axis='y', name='oj_fluid'))
    A(lathe([(0.0, 0.99), (0.355, 0.99), (0.36, 1.1), (0.33, 1.13), (0.0, 1.13)], (0, 0, 0), brass, seg=12, axis='y', name='oj_lid'))
    A(lathe([(0.0, 1.12), (0.07, 1.12), (0.09, 1.16), (0.05, 1.2), (0.0, 1.2)], (0, 0, 0), brass, seg=8, axis='y', name='oj_knob'))
    # the label: a curved patch on the front of the glass
    lb = []; lf = []
    nseg = 6
    for i in range(nseg + 1):
        a = math.radians(-150 + 120 * i / nseg)  # round the front (-z)
        for y in (0.16, 0.36):
            lb.append((math.cos(a) * 0.392, y, math.sin(a) * 0.392))
    for i in range(nseg): lf.append((i * 2, i * 2 + 1, i * 2 + 3, i * 2 + 2))
    lbo = mesh('oj_labelpatch', lb, lf, label, uvs=lambda p: (1 - (math.atan2(p[2], p[0]) - math.radians(-150)) / math.radians(120), (p[1] - 0.16) / 0.2))
    # make sure it faces out
    orient(lbo, lambda c: Vector((c.x, c.y, 0)))
    A(lbo)
    # the organ: a brain, floating, with a dangling stem (it is a specimen, it does not breathe)
    for sx in (-1, 1):  # two hemispheres, the gyri painted on, a little lumpy
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=7, radius=1.0)
        for v in bm.verts:
            x, y, z = gg(v.co)
            v.co = gv(sx * 0.115 + x * 0.12, 0.52 + y * 0.17 - 0.04 * max(0, -y), z * 0.25 * (1 - 0.1 * max(0, z)))
        br = _obj('oj_brain', bm, organ); smooth(br, 80); lump(br, 0.012, 14, seed=3 + sx)
        uv_box(br, 0.18); br['keepuv'] = 1; A(br)
    A(sweep([(0, 0.42, 0.06), (0.02, 0.32, 0.08), (0.05, 0.24, 0.06)], [0.05, 0.04, 0.03], organ, seg=6, name='oj_stem'))
    parts = pack(P, 'organjar', 0.25)
    return finish('s_organjar', parts, meta_of('organjar', col=[0.9, 1.2, 0.9], lights=[[0, 0.5, 0, 0xa6e22e]]))


def _paint_brain(px):
    rng = np.random.default_rng(93)
    px[:] = hexrgb(0xffa8bc)
    for k in range(16):  # wiggly sulci
        x, y = rng.uniform(0, 32), rng.uniform(0, 32); a = rng.uniform(0, 6.3)
        for s_ in range(6):
            a += rng.uniform(-1.2, 1.2); nx, ny = x + math.cos(a) * 3, y + math.sin(a) * 3
            px_line(px, x, y, nx, ny, 0xc8506e, 1.0); x, y = nx, ny
    px *= (0.93 + 0.1 * rng.random((32, 32)))[:, :, None]


def _paint_jarlabel(px):
    px[:] = hexrgb(0xfff3d0)
    px[1:3, :] = hexrgb(0x8a2a4a); px[-3:-1, :] = hexrgb(0x8a2a4a)
    text_px(px, 'GRISTLE', 3, 6, 2, 0x8a2a4a)
    text_px(px, '& SONS', 56, 6, 1, 0x8a2a4a)
    text_px(px, 'SPECIMEN 07', 3, 24, 1, 0x3e2470)
    text_px(px, 'DO NOT TAP', 3, 34, 1, 0xd8203a)
    px_disc(px, 82, 30, 7, 0xff6f91); px_disc(px, 82, 30, 4, 0xfff3d0)  # a little smiling stamp
    px[27, 79:86] = hexrgb(0x8a2a4a)


# ---------------------------------------------------------------- 10. vein cable span
def build_veincable(M):
    vein = mat('vc_vein_pulse', 0xffffff, rough=0.18, clearcoat=1.0, tex=tex_flesh('vc_vein_t', 0x6a48b0, 0x3e2470, 0xb07ae8, size=16, seed=101, amt=0.5))
    glow = mat('vc_node_glow_pulse', 0xff9ab8, rough=0.2, emit=0xff4f7a, strength=3.0)
    N = 22; nodes = (0.27, 0.52, 0.76)
    pts = []; rr = []
    for i in range(N + 1):
        t = i / N
        y = -0.62 * 4 * t * (1 - t)
        pts.append((-2 + 4 * t, y, 0.06 * math.sin(t * 9)))
        r = 0.065 + 0.012 * math.sin(t * 23)
        for c in nodes: r += 0.1 * math.exp(-((t - c) / 0.045) ** 2)
        if t < 0.06 or t > 0.94: r += 0.06 * (1 - min(t, 1 - t) / 0.06)  # suckers where it grips the walls
        rr.append(r)
    o = sweep(pts, rr, vein, seg=6, name='vc_cable')
    o.data.materials.append(glow)
    for p in o.data.polygons:
        g = gg(p.center); t = (g[0] + 2) / 4
        if any(abs(t - c) < 0.055 for c in nodes): p.material_index = 1
    parts = pack([o], 'veincable', 0.2)
    lights = [[-2 + 4 * c, -0.62 * 4 * c * (1 - c), 0, 0xff4f7a] for c in nodes]
    return finish('s_veincable', parts, meta_of('veincable', span=[[-2, 0, 0], [2, 0, 0]], sag=0.62, lights=lights,
                                                note='hangs between (-2,0,0) and (2,0,0); scale x to fit a span'))


# ---------------------------------------------------------------- 13. choir pipe
def build_choirpipe(M):
    cart = mat('cp_cartilage_pulse', 0xffffff, rough=0.16, clearcoat=1.0, tex=tex_flesh('cp_cart_t', 0xe6d8f0, 0xb49ad8, 0xfff4fa, size=32, seed=131, amt=0.5))
    tis = mat('cp_tissue_pulse', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_flesh('cp_tis_t', 0xff6f91, 0xc23a62, 0xffa3b8, size=32, seed=132, speck=0xffd27a, speck_p=0.03))
    dark = mat('cp_throat_pulse', 0x3a0a1c, rough=0.3)
    lips = mat('cp_lips_pulse', 0xffffff, rough=0.12, clearcoat=1.0, tex=tex_flesh('cp_lips_t', 0xff3a6a, 0xc21a4a, 0xff9ab8, size=16, seed=133))
    NA = 10
    prof = [(0.0, 0.0, 0), (0.14, 0.0, 0), (0.16, 0.12, 0), (0.24, 0.55, 0), (0.36, 0.95, 0), (0.39, 1.0, 0)]
    y = 1.6; k = 0
    while y < 5.85:
        prof.append((0.39, y - 0.11, 1)); prof.append((0.44, y, 2)); y += 0.3; k += 1
    prof.append((0.39, 5.9, 1)); prof.append((0.43, 5.97, 2)); prof.append((0.42, 6.0, 2)); prof.append((0.33, 6.0, 2)); prof.append((0.32, 5.9, 3)); prof.append((0.0, 5.9, 3))
    V = []; F = []; FM = []
    for i, (r, yy, kind) in enumerate(prof):
        for j in range(NA):
            a = 2 * math.pi * j / NA - math.pi / 2  # j = 0 at the back (+z)
            back = math.cos(a + math.pi / 2)  # 1 at the back
            rr = r
            if kind == 2 and back > 0.55: rr = 0.395  # the C ring is open at the back: smooth membrane there
            V.append((math.cos(a) * rr, yy, -math.sin(a) * rr))
    for i in range(len(prof) - 1):
        for j in range(NA):
            j2 = (j + 1) % NA
            F.append((i * NA + j, i * NA + j2, (i + 1) * NA + j2, (i + 1) * NA + j))
            a = 2 * math.pi * (j + 0.5) / NA - math.pi / 2; back = math.cos(a + math.pi / 2)
            k1, k2 = prof[i][2], prof[i + 1][2]
            if 3 in (k1, k2) and k2 == 3: FM.append(2)
            elif k1 == 2 and k2 == 2: FM.append(0)  # rim
            elif (k1 == 2 or k2 == 2) and back <= 0.55: FM.append(0)
            else: FM.append(1)
    o = mesh('cp_pipe', V, F, cart, mats=[tis, dark], fmat=FM)
    # the mouth (the flue opening) is a pair of lips, singing, round a dark slot
    mouth = []; mf = []
    for i in range(7):
        a = math.radians(-90 - 42 + 84 * i / 6)
        for yy in (1.1, 1.38):
            mouth.append((math.cos(a) * 0.405, yy, math.sin(a) * 0.405))
    for i in range(6): mf.append((i * 2, i * 2 + 1, i * 2 + 3, i * 2 + 2))
    mo = mesh('cp_mouth', mouth, mf, dark)
    orient(mo, lambda c: Vector((c.x, c.y, 0)))
    AA = list(range(-138, -41, 12))
    lr = lambda a, k: 0.035 + k * math.sin(math.radians((a + 138) / 96 * 180)) ** 0.7
    up = [(math.cos(math.radians(a)) * 0.43, 1.42 + 0.035 * math.cos(math.radians(a + 90) * 4), math.sin(math.radians(a)) * 0.43) for a in AA]
    lo_ = [(math.cos(math.radians(a)) * 0.43, 1.06 - 0.03 * math.cos(math.radians(a + 90) * 2), math.sin(math.radians(a)) * 0.43) for a in AA]
    P = [o, mo, sweep(up, [lr(a, 0.06) for a in AA], lips, seg=6, name='cp_lip_up'),
         sweep(lo_, [lr(a, 0.08) for a in AA], lips, seg=6, name='cp_lip_lo')]
    # uvs: wrap round the pipe
    for ob in (o,):
        uv_cyl(ob, axis='y', a0=0, a1=1.5)
        ob['keepuv'] = 1
    parts = pack(P, 'choirpipe', 0.3)
    return finish('s_choirpipe', parts, meta_of('choirpipe', col=[0.9, 6.0, 0.9], note='mouth (lips) faces -z at 1.1-1.4 m'))


BUILDS = {'ribarch': build_ribarch, 'lung': build_lung, 'tooth': build_tooth, 'tooth_b': build_tooth_b, 'eyeball': build_eyeball,
          'sphincter': build_sphincter, 'tongue': build_tongue, 'heartlamp': build_heartlamp, 'organjar': build_organjar,
          'veincable': build_veincable, 'choirpipe': build_choirpipe}


def build():
    only = argv_only()
    M = gut_mats()
    out = []
    for k, f in BUILDS.items():
        if only and k not in only: continue
        out.append((f(M), 'story/s_' + k, k))
    return out


EXPO = {'tooth': -2.0, 'tooth_b': -2.0, 'eyeball': -1.8, 'ribarch': -1.8, 'choirpipe': -2.2}
run_multi(build, EXPO)
