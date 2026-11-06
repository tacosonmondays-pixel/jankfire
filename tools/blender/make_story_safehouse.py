# OVERDUE safehouse props (DESIGN §6.8, ART_BIBLE #27), first seen in the Lost & Found: a scavenged bed (mattress on
# pallets, tie-dye blanket, a pillow with a face drawn on it), the dented stash locker, a wardrobe made from a dead
# ☺ CORP vending machine and the roll-up garage door ("lost & found parking only").
# -> public/models/story/s_<id>.glb + tools/blender/sheets/story/s_<id>.jpg
# run: blender -b --python tools/blender/make_story_safehouse.py [-- --only bed,locker] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bottom_kit import *

INK = 0x141018
DYE = [0xff6fae, 0xffe14d, 0x3fd6c6, 0xb48cff]


def plain(name, col, rough=0.5, metal=0.0, cc=0.0, var=0.08, speck=None, p=0.0, seed=1, size=16):
    return mat(name, col, rough=rough, metal=metal, clearcoat=cc, tex=tex_noise(name + '_t', col, var=var, size=size, speck=speck, speck_p=p, seed=seed))


# ------------------------------------------------------------------------------------------------ bed
def pallet(oz, woodm, G, B):
    """a block pallet 1.2 (x) by 0.8 (z), 144 mm tall: 5 top boards, 3 stringer boards on 9 blocks, 3 bottom boards"""
    P = []
    for z, w in ((-0.3275, 0.145), (-0.1588, 0.1), (0, 0.145), (0.1588, 0.1), (0.3275, 0.145)):
        P.append(uv_fit(box((1.2, 0.022, w), (0, 0.133, oz + z), woodm, bev=0.003, seg=1, rot=(0, random.uniform(-0.01, 0.01), 0)), G))
    for x in (-0.5275, 0, 0.5275):
        P.append(uv_fit(box((0.145, 0.022, 0.8), (x, 0.111, oz), woodm), G))
        for z in (-0.35, 0, 0.35): P.append(uv_fit(box((0.145, 0.078, 0.1 if z else 0.145), (x, 0.061, oz + z), woodm), B))
    for z in (-0.3275, 0, 0.3275): P.append(uv_fit(box((1.2, 0.022, 0.145), (0, 0.011, oz + z), woodm), G))
    return P


def build_bed():
    W = Atlas('bd_wood_t', 64)
    wood(W.sub(0, 0, 64, 32), 0xdcb070, 0x9a6a30, seed=41, rings=5)
    bl = W.sub(0, 32, 32, 32); crust(bl, 0xc89a5a, 0.06, seed=4); write(bl, 'EUR', 6, 6, 1, 0x3a1a08); smiley(bl, 16, 22, 6, face=0xc89a5a, ink=0x3a1a08)
    woodm = mat('bd_wood', 0xffffff, rough=0.7, tex=W.image())
    M = Atlas('bd_mattress_t', 64)
    mt = M.sub(0, 0, 64, 64); stripes(mt, [0xf4f0ff, 0xf4f0ff, 0x9ab8f0, 0xf4f0ff], 3, horizontal=False)
    rng = np.random.default_rng(2)
    for k in range(5):
        px_disc(mt, rng.uniform(5, 59), rng.uniform(5, 59), rng.uniform(4, 9), 0xe0c890)
        px_disc(mt, rng.uniform(5, 59), rng.uniform(5, 59), rng.uniform(2, 6), 0xd8b880)
    mt[:] = mt * (0.92 + 0.08 * rng.random((64, 64, 1)))
    mtm = mat('bd_mattress', 0xffffff, rough=0.75, tex=M.image())
    C = Atlas('bd_cloth_t', 128)
    tiedye(C.sub(0, 0, 128, 96), DYE, seed=27, arms=4, twist=5, cx=0.5, cy=0.45)
    pf = C.sub(0, 96, 64, 32); crust(pf, 0xfffaf6, 0.03, seed=5)
    px_disc(pf, 22, 11, 3.2, INK, r_in=2.0); px_disc(pf, 22, 11, 1.2, INK)  # one wonky eye, one X
    px_line(pf, 38, 8, 44, 14, INK, 1.6); px_line(pf, 44, 8, 38, 14, INK, 1.6)
    px_disc(pf, 32, 18, 9, INK, r_in=7.6, a0=math.pi * 0.62, a1=math.pi * 1.38)
    px_line(pf, 17, 5, 26, 4, INK, 1.4); px_line(pf, 37, 4, 45, 6, INK, 1.4)
    write(pf, 'gary', 4, 23, 1, 0xff3a8a, seed=2)
    tag = C.sub(64, 96, 64, 16); tag[:] = hexrgb(0xffffff); write(tag, 'do not remove', 2, 5, 1, INK)
    cloth = mat('bd_cloth', 0xffffff, rough=0.85, tex=C.image())
    O = []
    G = W.rect(0, 0, 64, 32); Bk = W.rect(0, 32, 32, 32)
    O += pallet(-0.4, woodm, G, Bk) + pallet(0.4, woodm, G, Bk)
    mat_ = pillow((1.35, 0.2, 1.9), (0.02, 0.244, 0.0), mtm, puff=0.06, pinch=0.02, cuts=3, top=1.0)
    for v in mat_.data.vertices:  # the ends flop over the pallets
        z = -v.co.y
        if abs(z) > 0.8: v.co.z -= (abs(z) - 0.8) * 0.22
    O.append(uv_fit(mat_, M.rect(0, 0, 64, 64)))
    O.append(uv_fit(box((0.12, 0.05, 0.002), (0.4, 0.22, -0.956), cloth, rot=(0.1, 0, 0.05)), C.rect(64, 96, 64, 16)))
    cross = [(-0.745, 0.15), (-0.742, 0.25), (-0.72, 0.33), (-0.64, 0.368), (-0.32, 0.378), (0.02, 0.384), (0.36, 0.378), (0.68, 0.368), (0.76, 0.33), (0.782, 0.25), (0.785, 0.15)]
    rows = []
    zs = [-0.38, -0.33, -0.2, 0.0, 0.2, 0.4, 0.6, 0.78, 0.9]
    rnd = random.Random(4)
    for j, z in enumerate(zs):
        row = []
        for i, (x, y) in enumerate(cross):
            sag = (z - 0.8) * 0.2 if z > 0.8 else 0.0
            yy = y + (0.035 if j == 0 else 0.018 if j == 1 else 0.0) - sag + (rnd.uniform(-0.012, 0.012) if 2 < i < 8 and j > 1 else 0)
            if j == 0: x *= 0.99
            row.append((x + (rnd.uniform(-0.01, 0.01) if i in (0, 10) else 0), yy, z + (0.03 * math.sin(i * 1.7) if j == 0 else 0)))
        rows.append(row)
    bk = sheet_grid(rows, cloth, 'blanket'); face_toward(bk, (0, 1, 0))
    O.append(uv_remap(bk, C.rect(0, 0, 128, 96)))
    pw = pillow((0.62, 0.13, 0.4), (-0.02, 0.405, -0.68), cloth, puff=0.3, pinch=0.1, rot=(-0.12, 0.08, 0.03))
    O.append(uv_fit(pw, C.rect(0, 96, 64, 32)))
    return O, {'use': 'bed', 'lie': [0, 0.4, 0]}


# ------------------------------------------------------------------------------------------------ locker
def build_locker():
    paint = mat('lk_paint', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_noise('lk_paint_t', 0xf2f0ec, var=0.05, size=32, seed=60, speck=0xa8683a, speck_p=0.03))
    Mt = Atlas('lk_metal_t', 16)
    chrome = Mt.fill(0, 0, 8, 16, 0xdde1e8); brass = Mt.fill(8, 0, 8, 16, 0xd8a840)
    metal = mat('lk_metal', 0xffffff, rough=0.18, metal=1.0, tex=Mt.image())
    D = Atlas('lk_decal_t', 128)
    tp = D.sub(0, 0, 80, 18); crust(tp, 0xf0e2b8, 0.04, seed=6); write(tp, 'the stash', 4, 4, 1, INK, wob=1, seed=3, bold=True)
    nm = D.sub(80, 0, 32, 18); nm[:] = hexrgb(0xc8ccd4); nm[0] = nm[-1] = hexrgb(0x6a6e78); write(nm, '13', 9, 2, 2, INK)
    ht = D.sub(0, 18, 24, 24); ht[:] = hexrgb(0xffffff); heart(ht, 12, 11, 7, 0xff4fd8)
    sm = D.sub(24, 18, 24, 24); sm[:] = hexrgb(0xffffff); smiley(sm, 12, 12, 10, face=0xffe14d, ink=INK)
    px_line(sm, 3, 3, 21, 21, 0xff3030, 2.4)
    for dx in (-5, 5): px_line(sm, 12 + dx, 4, 12 + dx * 1.6, 0, 0xff3030, 1.6)  # horns
    np_ = D.sub(48, 18, 48, 16); np_[:] = hexrgb(0xff4fd8); write(np_, 'no peeking', 0, 5, 1, 0xffffff)
    hi = D.sub(96, 18, 32, 24); hi[:] = hexrgb(0x4fd8ff); write(hi, 'hi', 6, 4, 2, INK)
    decal = mat('lk_decal', 0xffffff, rough=0.4, clearcoat=0.3, tex=D.image())
    O = []
    O.append(box((0.5, 1.76, 0.45), (0, 0.92, 0), paint, bev=0.008, seg=1))
    door = box((0.44, 1.64, 0.018), (0, 0.92, -0.233), paint)
    subdiv(door, 3)
    dent(door, (0.06, 0.68, -0.242), 0.17, 0.028, axis=(0, 0, 1)); dent(door, (-0.12, 1.3, -0.242), 0.09, 0.012, axis=(0, 0, 1))
    O.append(door)
    for y0 in (0.26, 1.56):
        for k in range(5): O.append(box((0.28, 0.013, 0.012), (0.02, y0 + k * 0.03, -0.247), paint, rot=(0.5, 0, 0)))
    for x in (-0.22, 0.22):
        for z in (-0.19, 0.19): O.append(uv_fit(cyl(0.02, 0.045, (x, 0.022, z), metal, axis='y', seg=6), chrome))
    hx = -0.17
    O.append(uv_fit(box((0.04, 0.16, 0.01), (hx, 0.97, -0.246), metal, bev=0.003, seg=1), chrome))
    O.append(uv_fit(rod((hx, 1.0, -0.252), (hx, 0.93, -0.262), 0.007, metal, seg=6), chrome))
    O.append(uv_fit(box((0.035, 0.05, 0.006), (hx, 0.86, -0.245), metal), chrome))
    O.append(uv_fit(box((0.045, 0.05, 0.02), (hx, 0.8, -0.262), metal, bev=0.005, seg=1), brass))
    O.append(uv_fit(sweep([(hx - 0.013, 0.82, -0.262), (hx - 0.013, 0.845, -0.262), (hx, 0.858, -0.262), (hx + 0.013, 0.845, -0.262), (hx + 0.013, 0.82, -0.262)], 0.004, metal, seg=6, name='shackle'), chrome))
    zf = -0.2435
    O.append(uv_fit(box((0.09, 0.05, 0.002), (0, 1.68, zf), decal), D.rect(80, 0, 32, 18)))
    O.append(uv_fit(box((0.36, 0.08, 0.002), (0.02, 1.46, zf), decal, rot=(0, 0, -0.04)), D.rect(0, 0, 80, 18)))
    O.append(uv_fit(box((0.11, 0.11, 0.002), (0.1, 1.12, zf), decal, rot=(0, 0, 0.2)), D.rect(0, 18, 24, 24)))
    O.append(uv_fit(box((0.13, 0.13, 0.002), (0.08, 0.5, zf - 0.006), decal, rot=(0, 0, -0.12)), D.rect(24, 18, 24, 24)))
    O.append(uv_fit(box((0.18, 0.06, 0.002), (0.04, 1.0, zf), decal, rot=(0, 0, 0.06)), D.rect(48, 18, 48, 16)))
    O.append(uv_fit(box((0.002, 0.07, 0.09), (0.2515, 1.3, 0.05), decal, rot=(0.1, 0, 0)), D.rect(96, 18, 32, 24)))
    for o in O:
        if o.data.materials and o.data.materials[0] == paint: uv_tile(o, 0.3)
    return O, {'paint': ['lk_paint'], 'use': 'stash'}


# ------------------------------------------------------------------------------------------------ vending-machine wardrobe
def build_wardrobe():
    L = Atlas('vw_paint_t', 128)
    crust(L.sub(0, 0, 64, 64), 0xf6f4f0, 0.04, seed=70, speck=0xc0b8b0, p=0.04)
    lv = L.sub(64, 0, 64, 128); crust(lv, 0xf6f4f0, 0.04, seed=71); lv[:, 0:10] = hexrgb(0x4fd8ff); lv[:, 54:64] = hexrgb(0x4fd8ff)
    smiley(lv, 32, 30, 18, face=0xffe14d, ink=INK); write(lv, 'SNAX', 9, 58, 2, 0x2a6aa8, bold=True)
    write(lv, 'always', 14, 78, 1, 0x2a6aa8); write(lv, 'open', 20, 87, 1, 0x2a6aa8)
    px_line(lv, 12, 88, 52, 76, 0xff3030, 2.2); write(lv, 'wardrobe', 6, 100, 1, 0xff4fd8, wob=1, seed=3, bold=True)
    for x in (16, 30, 44): drip(lv, x, 108, 8, 0xff4fd8)
    paint = mat('vw_paint', 0xffffff, rough=0.25, clearcoat=0.7, tex=L.image())
    glass = mat('vw_glass', 0xa8e8ff, rough=0.04, metal=0.1, alpha=0.28)
    metal = plain('vw_metal', 0xdde1e8, rough=0.15, metal=1.0, var=0.04, seed=72)
    C = Atlas('vw_cloth_t', 128)
    tiedye(C.sub(0, 0, 64, 64), DYE, seed=31, arms=3, twist=7)
    bz = C.sub(64, 0, 64, 64); crust(bz, 0x4fc8ef, 0.04, seed=8)
    for y in range(64): bz[y, 32 - y // 3:32 + y // 3] = hexrgb(0xffffff) if y < 40 else bz[y, 32]
    smiley(bz, 46, 20, 4, face=0xffe14d, ink=INK); bz[24:28, 42:52] = hexrgb(0xffffff)
    hd = C.sub(0, 64, 64, 64); crust(hd, 0xff9ac8, 0.05, seed=9); hd[44:52, 16:48] = hexrgb(0xff6fae); write(hd, 'JANK', 20, 20, 1, 0xffffff)
    sh_ = C.fill(64, 64, 16, 16, 0xffffff); shp = C.fill(80, 64, 16, 16, 0x7dff4f); sock = C.fill(96, 64, 16, 16, 0xffe14d)
    cloth = mat('vw_cloth', 0xffffff, rough=0.8, tex=C.image())
    Pn = Atlas('vw_panel_t', 96, 64)
    pn = Pn.sub(0, 0, 32, 64); pn[:] = hexrgb(0x1a1820); pn[4:14, 4:28] = hexrgb(0x0a2a1a); write(pn, '--', 9, 6, 1, 0x39ff14)
    for r_ in range(4):
        for c_ in range(3): pn[20 + r_ * 6:24 + r_ * 6, 5 + c_ * 8:11 + c_ * 8] = hexrgb(0xff4fd8 if (r_, c_) in ((1, 2), (3, 0)) else 0x3a3844)
    pn[48:58, 13:19] = hexrgb(0x5a5864); pn[52:54, 14:18] = hexrgb(0x0a0a0a)
    hdr = Pn.sub(32, 0, 64, 16); hdr[:] = hexrgb(0x120818); write(hdr, 'OUT OF', 14, 0, 1, 0xff4fd8); write(hdr, 'ORDER', 17, 8, 1, 0xff4fd8)
    fl = Pn.sub(32, 16, 32, 16); fl[:] = hexrgb(0x16141c); write(fl, 'PUSH', 4, 5, 1, 0x5a5864)
    panel = mat('vw_panel', 0xffffff, rough=0.2, clearcoat=0.5, tex=Pn.image(), emit=0xffffff, strength=2.5, emit_tex=True)
    O = []
    body = L.rect(0, 0, 64, 64); liv = L.rect(64, 0, 64, 128)
    O.append(uv_fit(box((0.9, 1.82, 0.04), (0, 0.915, 0.4), paint, bev=0.006, seg=1), body))
    for s in (-1, 1): O.append(uv_fit(box((0.04, 1.83, 0.85), (s * 0.455, 0.915, 0), paint, bev=0.008, seg=1), liv))
    O.append(uv_fit(box((0.98, 0.06, 0.87), (0, 1.805, 0), paint, bev=0.008, seg=1), body))
    O.append(uv_fit(box((0.86, 0.14, 0.8), (0, 0.072, -0.01), paint, bev=0.008, seg=1), body))
    O.append(uv_fit(box((0.87, 0.2, 0.05), (0, 1.67, -0.395), paint, bev=0.005, seg=1), body))
    O.append(uv_fit(box((0.7, 0.13, 0.004), (0, 1.67, -0.4215), panel), Pn.rect(32, 0, 64, 16)))
    # inside: a clothes rail with hangers, three garments, sneakers and one leftover product spiral holding a sock
    O.append(rod((-0.435, 1.45, 0.05), (0.435, 1.45, 0.05), 0.011, metal, seg=8))
    def hanger(x):  # wire coat hanger: hook over the rail, two shoulders, a bar
        P = [torus(0.017, 0.003, (x, 1.452, 0.05), metal, axis='x', seg=6, sides=3)]
        for a, b in (((x, 1.43, 0.05), (x, 1.355, 0.27)), ((x, 1.43, 0.05), (x, 1.355, -0.17)), ((x, 1.352, 0.27), (x, 1.352, -0.17))):
            P.append(rod(a, b, 0.0035, metal, seg=4))
        return join(P, 'hanger')
    tee = [(0, -0.2, 0.2), (-0.08, -0.205, 0.205), (-0.17, -0.21, 0.21), (-0.19, -0.15, 0.15), (-0.6, -0.155, 0.155)]
    for x, ln, rect, seed in ((-0.3, 0.62, C.rect(0, 0, 64, 64), 1), (-0.1, 0.8, C.rect(64, 0, 64, 64), 2), (0.12, 0.58, C.rect(0, 64, 64, 64), 3)):
        O.append(hanger(x))
        rows = [(y * ln / 0.6, xl * 1.15, xr * 1.15) for y, xl, xr in tee]
        g = garment(rows, 7, cloth, 0.0, 1.36, 0.0, amp=0.012, wave=0.18, sway=0.0, seed=seed, name='garment')
        uv_fit(g, rect, mode='front')
        xform([g], rot=(0, math.pi / 2, 0), move=(x, 0, 0.05))
        O.append(g)
    for x in (0.25, 0.36): O.append(hanger(x))
    for k, x in enumerate((-0.2, 0.0)):
        O.append(uv_fit(pillow((0.11, 0.07, 0.27), (x, 0.175, -0.05 + k * 0.03), cloth, puff=0.25, rot=(0, 0.1 * k, 0)), shp))
        O.append(uv_fit(box((0.115, 0.025, 0.28), (x, 0.152, -0.05 + k * 0.03), cloth, bev=0.008, seg=1, rot=(0, 0.1 * k, 0)), sh_))
    hp = [(0.3 + 0.06 * math.cos(t / 20 * 3 * 2 * math.pi), 0.9 + 0.06 * math.sin(t / 20 * 3 * 2 * math.pi), -0.3 + t / 20 * 0.66) for t in range(21)]
    O.append(sweep(hp, 0.006, metal, seg=4, name='spiral'))
    O.append(rod((0.3, 0.9, 0.36), (0.42, 0.9, 0.36), 0.01, metal, seg=6))
    sk = garment([(0, -0.035, 0.035), (-0.12, -0.035, 0.035), (-0.16, -0.035, 0.08), (-0.19, -0.03, 0.085)], 3, cloth, 0.35, 0.875, -0.1, amp=0.004, sway=0.0, seed=4, name='sock')
    O.append(uv_fit(sk, sock, mode='front'))
    # the door: glass, control panel, frame, swung open on its left hinge
    D = []
    for (sx, sy, sz, x, y) in ((0.9, 0.05, 0.05, 0, 1.535), (0.9, 0.06, 0.05, 0, 0.17), (0.05, 1.4, 0.056, 0.45, 0.85), (0.05, 1.4, 0.056, -0.45, 0.85), (0.04, 1.32, 0.046, -0.2, 0.85)):
        D.append(uv_fit(box((sx, sy, sz), (x, y, -0.45), paint, bev=0.006, seg=1), body))
    D.append(box((0.61, 1.31, 0.008), (0.125, 0.85, -0.45), glass))
    D.append(uv_fit(box((0.21, 1.31, 0.03), (-0.325, 0.85, -0.445), panel), Pn.rect(0, 0, 32, 64)))
    D.append(uv_fit(box((0.5, 0.12, 0.01), (0.125, 0.29, -0.47), panel), Pn.rect(32, 16, 32, 16)))
    for y in (0.4, 1.3): D.append(cyl(0.012, 0.1, (0.478, y, -0.45), metal, axis='y', seg=6))
    xform(D, rot=(0, -0.42, 0), pivot=(0.478, 0, -0.45))
    O += D
    for o in O:
        if o.data.materials and o.data.materials[0] in (metal, glass): uv_tile(o, 0.2)
    return O, {'paint': ['vw_paint'], 'use': 'wardrobe', 'lights': [[0, 1.67, -0.45, 0xff4fd8]]}


# ------------------------------------------------------------------------------------------------ garage door
def build_garagedoor():
    G = Atlas('gd_curtain_t', 256, 192)
    px = G.px; crust(px, 0xbfe8d8, 0.05, seed=80, speck=0x8a7a6a, p=0.02)
    rows_px = 192 / 22
    for k in range(22):
        y0 = int(k * rows_px)
        px[y0:y0 + 2] *= 1.08; px[int(y0 + rows_px) - 2:int(y0 + rows_px)] *= 0.78
    for x in range(10, 256, 23): drip(px, x, int(np.random.default_rng(x).uniform(0, 160)), 20, 0xa07a50, 1)
    def spray(s, x0, y0, sc, fill, line, seed):
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)): write(px, s, x0 + dx, y0 + dy, sc, line, wob=1, seed=seed)
        write(px, s, x0, y0, sc, fill, wob=1, seed=seed)
        r = random.Random(seed)
        for i in range(len(s)):
            if r.random() < 0.35: drip(px, x0 + i * 6 * sc + 2 * sc, y0 + 7 * sc - 1, r.randint(6, 18), fill, 2)
    spray('lost & found', 20, 40, 3, 0xff4fd8, INK, 4)
    spray('parking only', 22, 78, 3, 0xffe14d, INK, 7)
    smiley(px, 214, 138, 16, face=0xffe14d, ink=INK); px_line(px, 196, 120, 232, 156, 0xff3030, 4); px_line(px, 232, 120, 196, 156, 0xff3030, 4)
    write(px, 'no corp', 24, 128, 2, 0x2a2a9a, wob=1, seed=9); heart(px, 140, 140, 7, 0xff4fd8); drip(px, 140, 148, 14, 0xff4fd8, 2)
    write(px, 'tow zone: void', 20, 168, 1, INK, seed=3)
    curt = mat('gd_curtain', 0xffffff, rough=0.4, metal=0.35, clearcoat=0.3, tex=G.image())
    paint = mat('gd_paint', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_noise('gd_paint_t', 0xf2f0ea, var=0.06, size=16, seed=81, speck=0xa86a3a, speck_p=0.05))
    metal = plain('gd_metal', 0xa8b0b8, rough=0.3, metal=0.9, var=0.12, seed=82, speck=0x8a5a3a, p=0.06)
    O = []
    O.append(box((3.0, 0.38, 0.42), (0, 2.41, 0.0), paint, bev=0.015, seg=1))
    for s in (-1, 1):
        O.append(box((0.08, 2.24, 0.1), (s * 1.46, 1.11, -0.03), metal, bev=0.006, seg=1))
        O.append(box((0.1, 0.05, 0.14), (s * 1.44, 2.2, -0.03), metal, bev=0.004, seg=1))
    rows = []
    ys = []
    for k in range(22):
        y0 = 0.04 + k * 0.1
        ys += [(y0, 0.0), (y0 + 0.03, -0.014), (y0 + 0.07, -0.014)]
    ys.append((2.24, 0.0))
    for y, z in ys[::-1]:
        row = []
        for i in range(6):
            x = -1.44 + i * 0.576
            lift = max(0.0, (0.5 - y)) / 0.5 * (x + 1.44) / 2.88 * 0.055  # hangs crooked: a gap under one side
            row.append((x, y + lift, z - 0.02))
        rows.append(row)
    cu = sheet_grid(rows, curt, 'curtain'); face_toward(cu, (0, 0, -1))
    dent(cu, (-1.15, 0.28, -0.03), 0.62, 0.09, axis=(0, 0, 1))
    O.append(uv_fit(cu, (0, 0, 1, 1), mode='front', lo=[-1.44, 0.0, -0.1], hi=[1.44, 2.24, 0.1]))
    O.append(box((2.9, 0.05, 0.045), (0, 0.035, -0.03), metal, bev=0.006, seg=1, rot=(0, 0, 0.018)))
    O.append(sweep([(-0.15, 0.06, -0.055), (-0.15, 0.12, -0.085), (0.15, 0.12, -0.085), (0.15, 0.06, -0.055)], 0.009, metal, seg=6, name='handle'))
    O.append(box((0.06, 0.08, 0.02), (0.5, 0.08, -0.06), metal, bev=0.004, seg=1))
    for o in O:
        if o.data.materials and o.data.materials[0] in (paint, metal): uv_tile(o, 0.3)
    return O, {'paint': ['gd_paint'], 'opening': [2.88, 2.24], 'note': 'roll-up door: the curtain is one sheet from y 0 to 2.24 between the rails'}


BUILDERS = [('bed', build_bed), ('locker', build_locker), ('wardrobe', build_wardrobe), ('garagedoor', build_garagedoor)]
run(BUILDERS)
