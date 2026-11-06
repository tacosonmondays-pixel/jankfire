# Bread skin "Sliced Loaf" (w_bread_sliced).
# A sliced white sandwich loaf in its bag: a real tin loaf is ~10 x 10 cm with a domed top that overhangs the sides,
# ~12 mm slices, crust all round, a crusty heel at each end; here it's the FAMILY SIZE: x2 across and stretched to the
# Bread's bat length (1.3 m of loaf, 42 slices), so it swings like the baguette. The bag (clear on top so you see the
# slices, polka-dot print round the bottom, a label on each side) is twisted shut at the back and fastened with a
# paper twist tie; the twisted neck and the loose end of the bag are the handle.
# Held like the Bread: the neck runs along the grip (y = 0, the hands round z 0 .. 0.2), the loaf out in front,
# muzzle = the front end, like the code loaf.
# Made fun: it's FAMILY SIZE (the label says so, on both sides).
# run: blender -b --python tools/blender/make_bread_sliced.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

Z_L0, Z_L1 = -0.205, -1.475          # the loaf's back and front faces
NS = 42                              # slices
HW, YB, YS, YT = 0.094, -0.088, 0.052, 0.098   # half width, bottom, top of the sides, top of the dome
Z_TIE = -0.085                       # the twist tie
Z_TAIL = 0.255                       # end of the loose bag


def smooth01(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


def loaf_sec(th, k=1.0, pad=0.0):
    """(up, side) of a tin loaf's section at angle th (0 = +x side, pi/2 = the dome's top): square sides and bottom,
    a dome on top that overhangs the sides a little. k scales it about the centre (the heels), pad pushes it out."""
    c, s = math.cos(th), math.sin(th)
    if s >= 0:  # the dome: a squashed half-ellipse sitting on the sides, a bit wider than them (the muffin top)
        ow = HW * 1.06
        side = ow * math.copysign(abs(c) ** 0.7, c)
        up = YS + (YT - YS) * (abs(s) ** 0.9) - 0.01 * (1 - abs(s)) ** 3  # the overhang's lip tucks back in
        if abs(c) > 0.97: side = HW * math.copysign(1.0, c) + (ow - HW) * (1 - abs(c)) / 0.03 * math.copysign(1, c)
    else:  # square-ish sides and bottom (the tin)
        side = HW * math.copysign(abs(c) ** 0.25, c)
        up = YS + (YB - YS) * abs(s) ** 0.25
    cy = (YB + YT) / 2
    up = cy + (up - cy) * k; side *= k
    if pad:
        L = math.hypot(up - cy, side) or 1.0
        up += (up - cy) / L * pad; side += side / L * pad
    return up, side


def print_px(px):
    """the bag print, u = along the bag (front -> back), v = round it (0 = the bottom, .25 the +x side, .5 top, .75 -x side)"""
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffffff)
    r = np.random.default_rng(3)
    cols = [0xffe14d, 0xff4fd8, 0x4fd8ff]
    for k in range(70):  # polka dots
        px_disc(px, r.uniform(0, w), r.uniform(0, h), r.uniform(2.0, 3.6), cols[k % 3])
    def label(cx, cy, flip_v, flip_u):
        lw, lh = 76, 22
        L = np.zeros((lh, lw, 3), dtype=np.float32); L[:] = hexrgb(0x2a6cff)
        L[0] = L[-1] = hexrgb(0xffe14d)
        text_px(L, 'SLICED', 2, 2, 2, 0xffffff)
        text_px(L, 'FAMILY SIZE', 0, 14, 1, 0xffe14d)
        if flip_v: L = L[::-1]
        if flip_u: L = L[:, ::-1]
        y0, x0 = int(cy - lh / 2), int(cx - lw / 2)
        px[y0:y0 + lh, x0:x0 + lw] = L
    # rows: v = 1 - (row + .5) / h. on the -x side (v .75) up is -v, so it's flipped in v; on the +x side (v .25) you
    # read it with +z on your left, so it's mirrored in u
    label(w * 0.42, h * 0.25, True, False)
    label(w * 0.42, h * 0.75, False, True)
    r2 = np.random.default_rng(4)
    px[:] *= (0.95 + 0.06 * r2.random((h, w, 1)))


def build():
    crust = mat('bs_crust', 0xffffff, rough=0.6, clearcoat=0.12, tex=tex_noise('bs_crust_t', 0xb87430, var=0.12, size=32, speck=0x8a4a1a, speck_p=0.1, seed=61))
    top = mat('bs_top', 0xffffff, rough=0.5, clearcoat=0.2, tex=tex_noise('bs_top_t', 0x9a5418, var=0.14, size=32, speck=0x6a3410, speck_p=0.1, seed=62))
    crumb = mat('bs_crumb', 0xffffff, rough=0.9, tex=tex_noise('bs_crumb_t', 0xf6ecd0, var=0.08, size=16, speck=0xd8c49a, speck_p=0.25, seed=63))
    clear = mat('bs_bag', 0xf4faff, rough=0.2, clearcoat=0.3, alpha=0.16)
    prnt = mat('bs_print', 0xffffff, rough=0.3, clearcoat=0.5, tex=tex_canvas('bs_print_t', 192, 96, print_px))
    tie = mat('bs_tie', 0xffffff, rough=0.6, tex=tex_stripes('bs_tie_t', 0x39ff14, 0x2ab80e, size=8, width=2, diag=False))

    # ---- the loaf: 42 slices with a crumb groove between each, crust round the outside, rounded heels
    K = 20
    T = (Z_L0 - Z_L1) / NS
    G, D = 0.0055, 0.0042            # groove half width along z, depth
    stations = []                    # (z, groove depth, heel scale)
    for k in range(NS):
        za = Z_L1 + k * T
        for z in (za, za + G, za + T - G):
            stations.append(z)
    stations.append(Z_L0)
    # rounded heels: a couple of extra rings closing each end
    def heel(z):
        e = min(z - Z_L1, Z_L0 - z)
        return math.sqrt(max(0.0, 1 - max(0.0, (0.03 - e) / 0.03) ** 2)) * 0.12 + 0.88 if e < 0.03 else 1.0
    zs = [Z_L1 - 0.012, Z_L1 - 0.004] + stations + [Z_L0 + 0.004, Z_L0 + 0.012]
    def ring(i, t):
        z = zs[i]
        if z < Z_L1: k = 0.55 + 0.45 * max(0.0, 1 - (Z_L1 - z) / 0.012) ** 0.5
        elif z > Z_L0: k = 0.55 + 0.45 * max(0.0, 1 - (z - Z_L0) / 0.012) ** 0.5
        else: k = heel(z)
        seam = (i - 2) % 3 == 0 and Z_L1 < z < Z_L0 - 0.001 and i > 2
        out = []
        for j in range(K):
            th = 2 * math.pi * j / K
            out.append(loaf_sec(th, k, -D if seam else 0.0))
        return out
    loaf = loft([(0, 0, z) for z in zs], ring, m=crust, name='loaf', smooth_angle=40)
    for mm in (top, crumb): loaf.data.materials.append(mm)
    for f in loaf.data.polygons:
        st, sl = divmod(f.index, K)
        if st >= len(zs) - 1: f.material_index = 0; continue
        z0, z1 = zs[st], zs[st + 1]
        inner = Z_L1 <= z0 and z1 <= Z_L0 and abs(z1 - z0) < G * 1.1 and st >= 2  # a groove wall
        th = 2 * math.pi * (sl + 0.5) / K
        if inner: f.material_index = 2
        elif math.sin(th) > 0.35: f.material_index = 1
    uv_box(loaf, 0.06)

    # ---- the bag: loose round the loaf, folded shut at the front, gathered and twisted at the back into the handle
    N_B, KB = 40, 20
    bz = [Z_L1 - 0.03 + (Z_L0 + 0.02 - (Z_L1 - 0.03)) * i / 21 for i in range(22)]   # over the loaf
    nz = [Z_L0 + 0.04 + (Z_TAIL - Z_L0 - 0.04) * i / 21 for i in range(22)]           # shoulder, neck, tail
    allz = bz + nz
    rng = random.Random(7)
    def neck_r(z):  # radius of the gathered neck along z
        if z < Z_TIE: return 0.024 + (0.11 - 0.024) * smooth01(Z_TIE, Z_L0 + 0.02, z) ** 0.8
        if z < 0.2: return 0.024 + 0.0035 * math.sin((z - Z_TIE) * 60)
        return 0.024 + 0.03 * smooth01(0.2, Z_TAIL, z)
    def bring(i, t):
        z = allz[i]; out = []
        for j in range(KB):
            th = 2 * math.pi * j / KB
            if z <= Z_L0 + 0.02:
                kf = 1.0
                if z < Z_L1: kf = 0.35 + 0.65 * math.sqrt(max(0.0, 1 - ((Z_L1 - z) / 0.03) ** 2))
                up, sd = loaf_sec(th, kf, 0.008 + 0.003 * rng.random())
            else:
                rr = neck_r(z) * (1 + 0.12 * math.sin(th * 5 + z * 90) * (1 if z > Z_TIE else 0.4))  # twisted pleats
                cy = (YB + YT) / 2 * smooth01(Z_TIE, Z_L0 + 0.02, z) * (1 if z < Z_TIE else 0)
                up, sd = cy + rr * math.sin(th), rr * math.cos(th)
            out.append((up, sd))
        return out
    bag = loft([(0, 0, z) for z in allz], bring, m=clear, name='bag', close=(True, False), cap=False, smooth_angle=50)
    bag.data.materials.append(prnt)
    for f in bag.data.polygons:
        st, sl = divmod(f.index, KB)
        if st >= len(allz) - 1: continue
        z = (allz[st] + allz[st + 1]) / 2; th = 2 * math.pi * (sl + 0.5) / KB
        if Z_L1 + 0.05 < z < Z_L0 - 0.08 and math.sin(th) < 0.55: f.material_index = 1  # print round the bottom + sides, clear window on top
    uv_cyl(bag, 'z', Z_L1, Z_L0, turn=-math.pi / 2)
    md = bag.modifiers.new('solid', 'SOLIDIFY'); md.thickness = 0.0012; md.offset = 1.0
    apply_mods(bag)
    # ---- the twist tie: a paper-wrapped wire wound twice round the neck, its ends twisted into a little tail
    tp = []
    for k in range(29):
        a = 2 * math.pi * 2 * k / 28
        tp.append((0.0262 * math.cos(a), 0.0262 * math.sin(a), Z_TIE + 0.007 * k / 28))
    tw = tube(tp, 0.0026, tie, seg=6, name='tie')
    e0 = tp[-1]
    ends = sweep([(e0[0], e0[1], e0[2]), (0.03, 0.006, Z_TIE + 0.012), (0.046, 0.016, Z_TIE + 0.006), (0.058, 0.02, Z_TIE - 0.006)], 0.0028, tie, seg=6, name='tie_end', squash=(1.0, 2.2))
    for o in (tw, ends): uv_box(o, 0.02)
    WZ = {'bs_print': 'a', 'bs_bag': 'a', 'bs_tie': 'n', 'bs_crust': 'b', 'bs_top': 'b', 'bs_crumb': 'b'}
    parts = zone_join([loaf, bag, tw, ends], 'sliced', WZ, default='b')
    meta = {'kind': 'weapon', 'id': 'bread', 'skin': 'bread_sliced', 'paint': ['bs_crust'], 'muzzle': [0, 0, -1.45], 'hatAt': [[0, YT + 0.012, -0.42], 0.16]}
    return finish('w_bread_sliced', parts, meta)


main(build, 'w_bread_sliced', exposure=-0.6)
