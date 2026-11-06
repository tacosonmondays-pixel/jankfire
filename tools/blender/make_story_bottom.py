# OVERDUE: THE BOTTOM, the pastel favela rebel hub built from scrap on a rubble hill. Street props for the city
# instancer (public/js/city/props.js): washing, a wok satellite dish, plastic chairs, a sofa, a 50s fridge (Lumps' gym
# weights), a kick-scooter moped, a wall AC, the fallen ☺ CORP sign turned squat roof, string lights, a tie-dye
# lean-to, a scavenged front door, a shuttered window with a flower box and a soup crate.
# -> public/models/story/s_<id>.glb + tools/blender/sheets/story/s_<id>.jpg
# run: blender -b --python tools/blender/make_story_bottom.py [-- --only sofa,fridge] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bottom_kit import *

PINK, YEL, TEAL, MINT, LILAC, PEACH = 0xffb3c7, 0xffe58a, 0x5fd3c6, 0xa8f0d0, 0xc9a8ff, 0xffc49a
HOT, CYAN, INK = 0xff4fd8, 0x4fd8ff, 0x141018
DYE = [0xff6fae, 0xffe14d, 0x3fd6c6, 0xb48cff]
DYE2 = [0x3fd6c6, 0xb48cff, 0xff6fae, 0x9ff5c8]


def plain(name, col, rough=0.5, metal=0.0, cc=0.0, var=0.08, speck=None, p=0.0, seed=1, size=16):
    return mat(name, col, rough=rough, metal=metal, clearcoat=cc, tex=tex_noise(name + '_t', col, var=var, size=size, speck=speck, speck_p=p, seed=seed))


def tiled(objs, size=0.25):
    for o in objs: uv_tile(o, size)
    return objs


# ------------------------------------------------------------------------------------------------ laundry
def laundry_atlases():
    A = Atlas('ld_cloth_t', 128)
    tiedye(A.sub(0, 0, 64, 64), DYE, seed=3, arms=3, twist=7)
    yf = A.sub(64, 0, 64, 32); crust(yf, 0xfdfaf4, 0.04, seed=4)
    for (hx, hy) in ((10, 14), (30, 22), (50, 12), (20, 27), (44, 27), (56, 24), (6, 24)): heart(yf, hx, hy, 2.2, 0xff5fa0)
    yf[0:6] = hexrgb(0x4fa8ff); write(yf, 'XXXXL', 17, 0, 1, 0xffffff)
    px_line(yf, 32, 6, 32, 18, 0xd8d0c8, 1.2); px_line(yf, 32, 18, 26, 31, 0xd8d0c8, 1.2); px_line(yf, 32, 18, 38, 31, 0xd8d0c8, 1.2)
    bd = A.sub(64, 32, 32, 40); bd[:] = hexrgb(0xffffff); bd[0:9] = hexrgb(HOT)
    smiley(bd, 6, 4.5, 3.6, face=0xffe14d, ink=INK); write(bd, 'CORP', 12, 1, 1, 0xffffff)
    bd[11:25, 3:15] = hexrgb(0xcfd6e0); px_disc(bd, 9, 16, 3.5, 0xf0e6dc); bd[21:25, 5:13] = hexrgb(0x5a6a8a)
    write(bd, 'TEMP', 2, 27, 1, INK)
    for k in range(17, 30, 2): bd[12:24, k] = hexrgb(INK)
    bd[35:38, 3:29] = hexrgb(0xff3030)
    st = A.sub(96, 32, 8, 40); st[:] = hexrgb(0xff5fa0); st[::5, 2:6] = hexrgb(0xffe14d)
    pegs = [A.fill(104 + (k % 2) * 12, 32 + (k // 2) * 12, 12, 12, c) for k, c in enumerate((0xff6fae, 0x3fd6c6, 0xffe14d, 0xb48cff))]
    bx = A.sub(0, 64, 64, 32); crust(bx, 0x9ff0cc, 0.04, seed=6); dots(bx, 0xffffff, 8, 1.6, seed=2); bx[0:5] = hexrgb(0x3a3a8a)
    tiedye(A.sub(64, 64, 64, 64), DYE2, seed=8, arms=2, twist=10, cx=0.45, cy=0.4)
    A.fill(0, 96, 16, 16, 0xc0c4cc)  # clip metal
    R = dict(td=A.rect(0, 0, 64, 64), yf=A.rect(64, 0, 64, 32), badge=A.rect(64, 32, 32, 40), strap=A.rect(96, 32, 8, 40),
             pegs=pegs, boxer=A.rect(0, 64, 64, 32), td2=A.rect(64, 64, 64, 64), clip=A.rect(0, 96, 16, 16, 2))
    P = Atlas('ld_paint_t', 64)
    tw_ = P.sub(0, 0, 32, 64); crust(tw_, 0xfbfbf8, 0.05, seed=9, block=1)
    for y in (5, 8, 55, 58): tw_[y:y + 2] = hexrgb(0xb8b8bc)
    tw_[0:2, ::2] = hexrgb(0xd0d0d0); tw_[62:64, ::2] = hexrgb(0xd0d0d0)
    sk = P.sub(32, 0, 32, 32); crust(sk, 0xf8f8f6, 0.05, seed=10)
    for y in range(0, 9, 2): sk[y] = hexrgb(0xc8c8cc)
    sk[24:32, 0:10] = hexrgb(0xb0b0b6); sk[26:32, 22:32] = hexrgb(0xb0b0b6); sk[12:15] = hexrgb(0xdadade)
    grime(sk, 0x8a7a6a, 0.08, seed=4, blob=4)
    R.update(towel=P.rect(0, 0, 32, 64), sock=P.rect(32, 0, 32, 32))
    return A, P, R


SOCK = [(0, -0.045, 0.045), (-0.12, -0.046, 0.046), (-0.24, -0.044, 0.044), (-0.31, -0.047, 0.07), (-0.36, -0.047, 0.125), (-0.405, -0.036, 0.13)]


def sock(x0, m, rect, seed, long=1.0, flip=False):
    rows = [(y * long if i < 3 else y - 0.24 * (long - 1), xl, xr) for i, (y, xl, xr) in enumerate(SOCK)]
    if flip: rows = [(y, -xr, -xl) for y, xl, xr in rows]
    o = garment(rows, 4, m, x0, 0.01, 0.0, dip=lambda r, u: 0.012 * (abs(u - 0.5) * 2) ** 3 if r == len(rows) - 1 else 0.0,
                amp=0.012, wave=0.1, sway=0.03, seed=seed, name='sock')
    return uv_fit(o, rect, mode='front')


def lanyard(x0, cloth, plastic, R):
    pts = [(x0 + 0.004, -0.29, 0.012), (x0 - 0.014, -0.25, 0.012), (x0 - 0.03, -0.14, 0.008), (x0 - 0.04, -0.02, 0.002),
           (x0 - 0.026, 0.012, 0.0), (x0, 0.02, 0.0), (x0 + 0.026, 0.012, 0.0), (x0 + 0.04, -0.02, 0.002),
           (x0 + 0.032, -0.14, 0.008), (x0 + 0.016, -0.25, 0.012), (x0 - 0.002, -0.29, 0.012)]
    st = sweep(pts, 0.0085, cloth, seg=4, squash=(1.0, 0.22), name='strap'); uv_fit(st, R['strap'], mode='front')
    clip = box((0.014, 0.03, 0.006), (x0, -0.302, 0.012), plastic, rot=(0, 0, 0.06)); uv_fit(clip, R['clip'])
    card = box((0.056, 0.086, 0.004), (x0 + 0.003, -0.357, 0.013), plastic, rot=(0.05, 0, 0.06), name='badge')
    uv_fit(card, R['badge'])
    return [st, clip, card]


def build_laundry(variant):
    def fn():
        A, Pa, R = laundry_atlases()
        cloth = mat('ld_cloth', 0xffffff, rough=0.85, tex=A.image())
        plastic = mat('ld_peg', 0xffffff, rough=0.3, clearcoat=0.6, tex=A.image())
        paint = mat('ld_paint', 0xffffff, rough=0.85, tex=Pa.image())
        O = []; pg = R['pegs']
        def pegs(xs, k=0):
            for i, x in enumerate(xs): O.extend(peg(x, 0.0, 0.0, plastic, pg[(k + i) % 4], rot=random.uniform(-0.12, 0.12)))
        if variant == 'a':
            for i, (x, f) in enumerate(((-1.38, False), (-1.24, False))):
                O.append(sock(x, paint, R['sock'], 11 + i, long=1.0 - 0.06 * i)); pegs([x], i)
            tee = [(0, -0.39, 0.39), (-0.09, -0.395, 0.395), (-0.19, -0.4, 0.4), (-0.21, -0.27, 0.27), (-0.46, -0.275, 0.275), (-0.72, -0.28, 0.28)]
            nk = lambda u: max(0.0, 1 - abs(u - 0.5) / 0.16)
            sl = lambda u: max(0.0, (abs(u - 0.5) - 0.3) / 0.2)
            t = garment(tee, 9, cloth, -0.72, 0.01, 0.0, dip=lambda r, u: (-0.07 * nk(u) - 0.05 * sl(u)) if r == 0 else (-0.05 * sl(u) if r < 3 else 0.0),
                        amp=0.022, wave=0.24, sway=0.05, seed=3, name='tee')
            O.append(uv_fit(t, R['td'], mode='front')); pegs([-0.94, -0.5], 1)
            yx = [-0.37, -0.31, -0.22, -0.08, 0, 0.08, 0.22, 0.31, 0.37]; yy = [-0.2, -0.25, -0.34, -0.45, -0.46, -0.45, -0.34, -0.25, -0.2]
            yrows = [(0, -0.36, 0.36), (-0.1, -0.37, 0.37), (-0.17, -0.39, 0.39), [(x, y) for x, y in zip(yx, yy)]]
            y = garment_pts(yrows, 9, cloth, 0.12, 0.01, amp=0.018, wave=0.2, sway=0.04, seed=5, name='yfronts')
            O.append(uv_fit(y, R['yf'], mode='front')); pegs([-0.2, 0.44], 2)
            tow = [(0, -0.27, 0.27), (-0.2, -0.272, 0.272), (-0.42, -0.275, 0.275), (-0.66, -0.275, 0.275), (-0.9, -0.27, 0.27)]
            t2 = garment(tow, 6, paint, 0.82, 0.01, 0.0, dip=lambda r, u: 0.025 * math.sin(math.pi * u) if r == 4 else 0.0, amp=0.02, wave=0.3, sway=0.06, seed=7, name='towel')
            O.append(uv_fit(t2, R['towel'], mode='front')); pegs([0.6, 1.04], 3)
            O.extend(lanyard(1.36, cloth, plastic, R))
        else:
            sh = [(0, -0.5, 0.5), (-0.2, -0.5, 0.5), (-0.42, -0.505, 0.505), (-0.64, -0.505, 0.505), (-0.86, -0.5, 0.5), (-1.06, -0.5, 0.5)]
            s = garment(sh, 10, cloth, -0.86, 0.01, 0.0, dip=lambda r, u: 0.03 * math.sin(math.pi * u * 2) if r == 5 else 0.0, amp=0.035, wave=0.32, sway=0.07, seed=21, name='sheet')
            O.append(uv_fit(s, R['td2'], mode='front')); pegs([-1.32, -0.86, -0.4], 0)
            for i, (x, L, fl) in enumerate(((-0.2, 1.0, False), (-0.06, 1.35, True), (0.08, 0.85, False))):
                O.append(sock(x, paint, R['sock'], 30 + i, long=L, flip=fl)); pegs([x], i)
            bxx = [-0.3, -0.22, -0.12, -0.04, 0, 0.04, 0.12, 0.22, 0.3]; bxy = [-0.42, -0.42, -0.41, -0.33, -0.3, -0.33, -0.41, -0.42, -0.42]
            brows = [(0, -0.26, 0.26), (-0.1, -0.27, 0.27), (-0.2, -0.29, 0.29), [(x, y) for x, y in zip(bxx, bxy)]]
            b = garment_pts(brows, 9, cloth, 0.56, 0.01, amp=0.02, wave=0.22, sway=0.04, seed=33, name='boxers')
            O.append(uv_fit(b, R['boxer'], mode='front')); pegs([0.38, 0.74], 2)
            ht = [(0, -0.2, 0.2), (-0.18, -0.2, 0.2), (-0.36, -0.205, 0.205), (-0.54, -0.2, 0.2)]
            h = garment(ht, 5, paint, 1.18, 0.01, 0.0, amp=0.015, wave=0.25, sway=0.05, seed=35, name='handtowel')
            O.append(uv_fit(h, R['towel'], mode='front')); pegs([1.02, 1.34], 3)
        return O, {'line': {'y': 0, 'x': [-1.5, 1.5]}, 'hang': 1.1, 'paint': ['ld_paint']}
    return fn


def garment_pts(rows, ncols, m, x0, y0, **kw):
    """garment() where a row can also be an explicit list of (x, y) points (leg holes, crotches)"""
    r = random.Random(kw.get('seed', 1)); ph = r.random() * 6.28
    amp, wave, sway = kw.get('amp', 0.02), kw.get('wave', 0.22), kw.get('sway', 0.05)
    pts = []
    for row in rows:
        if isinstance(row, tuple):
            y, xl, xr = row; P2 = [(xl + (xr - xl) * c / (ncols - 1), y) for c in range(ncols)]
        else: P2 = row
        out = []
        for x, y in P2:
            dep = max(0.0, -y)
            z = amp * math.sin(2 * math.pi * x / wave + ph) * (0.25 + dep * 2.2) + sway * dep ** 1.4 + r.uniform(-1, 1) * 0.004 * dep
            out.append((x0 + x, y0 + y, z))
        pts.append(out)
    o = sheet_grid(pts, m, kw.get('name', 'garment'))
    return face_toward(o, (0, 0, -1))


# ------------------------------------------------------------------------------------------------ wok dish
def build_wokdish():
    steel = mat('wk_steel', 0xffffff, rough=0.32, metal=0.85, tex=tex_noise('wk_steel_t', 0x3c363c, var=0.16, size=32, seed=3, speck=0x7a6a9a, speck_p=0.02))
    chrome = plain('wk_chrome', 0xd8dce4, rough=0.18, metal=1.0, var=0.06, seed=4)
    paint = mat('wk_paint', 0xffffff, rough=0.4, clearcoat=0.5, tex=tex_noise('wk_paint_t', 0xf4f0ea, var=0.06, size=32, seed=5, speck=0xb06a3a, speck_p=0.025))
    wood = mat('wk_wood', 0xffffff, rough=0.55, clearcoat=0.4, tex=tex_wood('wk_wood_t', 0xb87a40, 0x6a3a18, size=32, seed=6, rings=4))
    black = plain('wk_black', 0x1a181c, rough=0.45, var=0.05, seed=7)
    O = []
    # wall bracket: plate, arm, brace, post
    O.append(box((0.16, 0.26, 0.012), (0, 0, -0.006), paint))
    for y in (-0.1, 0.1): O.append(cyl(0.011, 0.012, (0, y, -0.016), chrome, axis='z', seg=5))
    O.append(box((0.04, 0.04, 0.41), (0, -0.05, -0.215), paint))
    O.append(rod((0, -0.122, -0.01), (0, -0.065, -0.3), 0.011, paint, seg=4))
    O.append(cyl(0.022, 0.19, (0, 0.035, -0.4), paint, axis='y', seg=6))
    O.append(box((0.07, 0.05, 0.06), (0, 0.13, -0.4), chrome))
    # the wok, built bowl-up round its outer bottom, then tipped to face forward and up
    W = []
    prof = [(0.0, 0.0), (0.17, 0.03), (0.27, 0.1), (0.302, 0.15), (0.272, 0.118), (0.17, 0.046), (0.0, 0.01)]
    W.append(lathe(prof, (0, 0, 0), steel, seg=14, axis='y', name='wok'))
    W.append(box((0.09, 0.03, 0.09), (0, -0.008, 0), chrome))  # clamp on the wok's back
    W.append(rod((0.296, 0.14, 0), (0.37, 0.16, 0), 0.013, steel, seg=4))
    W.append(rod((0.365, 0.158, 0), (0.58, 0.2, 0), 0.019, wood, seg=6, r1=0.016))
    W.append(sweep([(-0.288, 0.136, -0.045), (-0.352, 0.142, -0.025), (-0.352, 0.142, 0.025), (-0.288, 0.136, 0.045)], 0.0055, chrome, seg=4, name='loop'))
    # coat-hanger arm from the low rim (its hook still on) out to the focus, holding a spoon as the feed horn
    W.append(sweep([(0, 0.145, -0.318), (0, 0.118, -0.305), (0, 0.15, -0.29), (0, 0.2, -0.22), (0, 0.27, -0.12), (0, 0.318, -0.02)], 0.004, chrome, seg=4, name='hanger'))
    W.append(lathe([(0.0, 0.372), (0.036, 0.362), (0.052, 0.334), (0.044, 0.336), (0.0, 0.358)], (0, 0, 0), chrome, seg=8, axis='y', name='spoon'))
    W.append(rod((0, 0.352, -0.044), (0, 0.29, -0.12), 0.0065, chrome, seg=4))
    W.append(rod((0, 0.31, -0.06), (0, 0.285, -0.1), 0.013, black, seg=6))
    tilt = -0.96; M = (0, 0.155, -0.4)
    xform(W, rot=(tilt, 0, 0), move=M)
    O.extend(W)
    f = mpt(rot=(tilt, 0, 0), move=M)
    c0 = f((0.012, 0.3, -0.08)); c2 = f((0.016, 0.16, -0.28))
    O.append(sweep([c0, c2, (0.035, c2[1] - 0.1, c2[2] + 0.08), (0.045, -0.11, -0.05), (0.04, -0.11, -0.012)], 0.0048, black, seg=4, name='cable'))
    tiled(O, 0.2)
    # lod1: bracket, a coarse wok, handle, spoon on its wire
    L = [box((0.16, 0.26, 0.012), (0, 0, -0.006), paint), box((0.04, 0.04, 0.41), (0, -0.05, -0.215), paint), cyl(0.022, 0.19, (0, 0.035, -0.4), paint, axis='y', seg=4)]
    LW = [lathe([(0.0, 0.0), (0.24, 0.05), (0.302, 0.15), (0.0, 0.012)], (0, 0, 0), steel, seg=8, axis='y', name='wok'),
          rod((0.3, 0.14, 0), (0.58, 0.2, 0), 0.018, wood, seg=4), rod((0, 0.15, -0.29), (0, 0.33, 0), 0.006, chrome, seg=3),
          ball(0.05, (0, 0.35, 0), chrome, scale=(1, 0.5, 1), seg=4, rings=3)]
    xform(LW, rot=(tilt, 0, 0), move=M); L += LW
    tiled(L, 0.2)
    return O, {'_lod': L, 'mount': 'wall', 'note': 'origin on the wall face, sticks out toward -z'}


# ------------------------------------------------------------------------------------------------ plastic chair
def build_pchair():
    paint = mat('pc_paint', 0xffffff, rough=0.3, clearcoat=0.5, tex=tex_noise('pc_paint_t', 0xf6f3ef, var=0.05, size=16, seed=8, speck=0xd6cec6, speck_p=0.08))
    tape = plain('pc_tape', 0xb4b8c0, rough=0.35, metal=0.35, var=0.12, seed=9)
    O = []
    O.append(box((0.47, 0.035, 0.44), (0, 0.44, -0.005), paint, bev=0.014, seg=1, taper=(1.07, 1.0)))
    for s in (-1, 1):
        O.append(rod((s * 0.275, 0.0, -0.27), (s * 0.248, 0.64, -0.205), 0.019, paint, seg=6, r1=0.03))  # front leg runs up into the arm
        O.append(rod((s * 0.28, 0.0, 0.275), (s * 0.225, 0.445, 0.205), 0.019, paint, seg=6, r1=0.031))
        O.append(rod((s * 0.225, 0.42, 0.2), (s * 0.212, 0.83, 0.29), 0.028, paint, seg=6, r1=0.024))
        O.append(sweep([(s * 0.255, 0.645, -0.245), (s * 0.24, 0.655, 0.0), (s * 0.222, 0.66, 0.245)], 0.032, paint, seg=4, squash=(0.45, 1.0), name='arm'))
    O.append(sweep([(-0.232, 0.82, 0.285), (-0.12, 0.85, 0.31), (0, 0.856, 0.316), (0.12, 0.85, 0.31), (0.232, 0.82, 0.285)], 0.03, paint, seg=6, squash=(1.0, 0.55), name='toprail'))
    for y in (0.545, 0.63, 0.715):
        z = 0.2 + (y - 0.42) / 0.41 * 0.09
        O.append(sweep([(-0.215, y, z), (-0.1, y + 0.004, z + 0.018), (0.1, y + 0.004, z + 0.018), (0.215, y, z)], 0.033, paint, seg=4, squash=(1.0, 0.24), name='slat'))
    O.append(cyl(0.0265, 0.06, (0.267, 0.12, -0.257), tape, axis='y', seg=8, rot=(0, 0, 0.04)))  # duct-tape splint on a cracked leg
    tiled(O, 0.3)
    L = [box((0.47, 0.035, 0.44), (0, 0.44, -0.005), paint, taper=(1.07, 1.0)), box((0.46, 0.4, 0.03), (0, 0.66, 0.255), paint, rot=(0.21, 0, 0))]
    for s_ in (-1, 1):
        L += [rod((s_ * 0.275, 0.0, -0.27), (s_ * 0.248, 0.64, -0.205), 0.024, paint, seg=3), rod((s_ * 0.28, 0.0, 0.275), (s_ * 0.225, 0.445, 0.205), 0.024, paint, seg=3),
              box((0.05, 0.03, 0.48), (s_ * 0.24, 0.655, 0.0), paint)]
    tiled(L, 0.3)
    return O, {'_lod': L, 'paint': ['pc_paint'], 'sit': [0, 0.47, 0]}


# ------------------------------------------------------------------------------------------------ sofa
def build_sofa():
    def fab(px):
        crust(px, 0xf2ede6, 0.08, seed=12)
        px[::2] *= 0.93; grime(px, 0x9a8a78, 0.18, seed=5, blob=4)
    paint = mat('sf_paint', 0xffffff, rough=0.8, tex=tex_canvas('sf_paint_t', 32, 32, fab))
    O_ = Atlas('sf_odd_t', 64)
    tiedye(O_.sub(0, 0, 64, 48), [0xff6fae, 0x3fd6c6, 0xffe14d], seed=4, arms=4, twist=8)
    foam = O_.fill(16, 48, 16, 16, 0xffd84a); hole = O_.fill(0, 48, 16, 16, 0x2a2026)
    odd = mat('sf_odd', 0xffffff, rough=0.75, tex=O_.image())
    tape = plain('sf_tape', 0xb8bcc4, rough=0.35, metal=0.4, var=0.14, seed=13)
    metal = plain('sf_metal', 0xd4d8e0, rough=0.2, metal=1.0, var=0.05, seed=14)
    woodm = mat('sf_wood', 0xffffff, rough=0.5, clearcoat=0.3, tex=tex_wood('sf_wood_t', 0x7a4a24, 0x3a2010, size=16, seed=3))
    O = []
    O.append(box((1.96, 0.24, 0.8), (0, 0.2, 0.0), paint, bev=0.035, seg=1))
    for s in (-1, 1):
        O.append(box((0.22, 0.48, 0.84), (s * 0.88, 0.345, 0.0), paint, bev=0.04, seg=1))
        O.append(cyl(0.125, 0.86, (s * 0.89, 0.59, 0.0), paint, axis='z', seg=8, bev=0.02))
    O.append(box((1.56, 0.42, 0.22), (0, 0.53, 0.3), paint, bev=0.04, seg=1))
    for i, x in enumerate((-0.515, 0.0, 0.515)):
        m = odd if i == 1 else paint
        sink = -0.025 if i == 2 else 0.0
        O.append(pillow((0.52, 0.16, 0.64), (x, 0.395 + sink, -0.075), m, puff=0.2, top=1.3, rot=(0.02 * (i - 1), 0.03 * (1 - i), 0.025 * (i - 1) + (0.04 if i == 2 else 0))))
        O.append(pillow((0.5, 0.42, 0.17), (x, 0.635, 0.135), paint, puff=0.14, pinch=0.05, cuts=2, rot=(0.2 + 0.04 * i, 0.02 * (i - 1), 0.03 * (1 - i) if i != 1 else -0.06)))
    for x in (-0.9, 0.9):
        for z in (-0.33, 0.33): O.append(cyl(0.03, 0.08, (x, 0.04, z), woodm, axis='y', seg=6, r2=0.022))
    # the escaped spring and its foam, out of the right seat cushion
    hp = []
    for k in range(19):
        a = k / 18 * 3.2 * 2 * math.pi; r = 0.034 + 0.01 * k / 18
        hp.append((0.47 + math.cos(a) * r + k * 0.002, 0.455 + k / 18 * 0.2, -0.16 + math.sin(a) * r))
    O.append(sweep(hp, 0.0048, metal, seg=4, name='spring'))
    fo = ball(0.05, (0.47, 0.46, -0.16), odd, scale=(1.0, 0.45, 1.0), seg=8, rings=5); jitter(fo, 0.012, seed=3)
    uv_fit(fo, foam); O.append(fo)
    # duct tape: an X on the left arm, a strip over the middle back cushion
    for a in (0.62, -0.62):
        O.append(box((0.055, 0.34, 0.004), (-0.88, 0.36, -0.4245), tape, rot=(0, 0, a)))
    O.append(box((0.06, 0.38, 0.005), (0.02, 0.64, 0.035), tape, rot=(0.22, 0, 0.12)))
    for o in O:
        if o.data.materials and o.data.materials[0] == odd and o is not fo: uv_fit(o, O_.rect(0, 0, 64, 48))
        elif o is not fo: uv_tile(o, 0.3)
    return O, {'paint': ['sf_paint'], 'sit': [[-0.52, 0.47, -0.1], [0, 0.47, -0.1], [0.52, 0.47, -0.1]]}


# ------------------------------------------------------------------------------------------------ fridge
def rr_pts(w, d, r, n=2, side=2):
    """rounded rectangle (x, z) with extra points along the straight sides (so they can dent)"""
    base = rrect(0, 0, w, d, r, n)
    out = []
    for i, p in enumerate(base):
        q = base[(i + 1) % len(base)]
        out.append(p)
        if math.dist(p, q) > r * 1.5:
            for k in range(1, side + 1):
                t = k / (side + 1); out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def ring_body(sections, m, name='body'):
    """a closed shell through rings [(y, [(x, z)...])] (all the same count), fan-capped top and bottom"""
    bm = bmesh.new()
    R = [[bm.verts.new(gv(x, y, z)) for x, z in pts] for y, pts in sections]
    n = len(R[0])
    for a, b in zip(R, R[1:]):
        for i in range(n):
            j = (i + 1) % n; bm.faces.new((a[i], a[j], b[j], b[i]))
    for ring, (y, pts) in ((R[0], sections[0]), (R[-1], sections[-1])):
        c = bm.verts.new(gv(sum(p[0] for p in pts) / n, y, sum(p[1] for p in pts) / n))
        for i in range(n): bm.faces.new((ring[i], ring[(i + 1) % n], c))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 40)
    return o


def build_fridge():
    paint = mat('fr_paint', 0xffffff, rough=0.22, clearcoat=0.8, tex=tex_noise('fr_paint_t', 0xf8f5ef, var=0.04, size=32, seed=15, speck=0xb0683a, speck_p=0.03))
    chrome = plain('fr_chrome', 0xe0e4ec, rough=0.12, metal=1.0, var=0.04, seed=16)
    A = Atlas('fr_decal_t', 128)
    note = A.sub(0, 0, 48, 56); crust(note, 0xfff6d0, 0.03, seed=3); note[0:3] = hexrgb(0xf0e0a0)
    for i, (t, sc) in enumerate((("lumps'", 1), ('gym.', 1), ('do not', 1), ('open', 1))):
        write(note, t, 4, 6 + i * 11, 1, 0x1a2a8a if i < 2 else 0xd01830, wob=1, seed=i + 2, bold=True)
    px_line(note, 4, 50, 40, 49, 0xd01830, 1.5)
    pl = A.sub(48, 0, 80, 16); crust(pl, 0xc8ccd6, 0.05, seed=4); pl[0] = pl[-1] = hexrgb(0x7a7e88)
    write(pl, 'BRRR-O-MATIC', 4, 4, 1, 0xd0203a, bold=True)
    gr = A.sub(48, 16, 64, 16); gr[:] = hexrgb(0xc8ccd4); gr[2:14, 1::4] = hexrgb(0x1a1a20); gr[2:14, 2::4] = hexrgb(0x2a2a30)
    letters = []
    for k, (ch, bg) in enumerate(zip('LUMPS', (0xff3030, 0xffe14d, 0x3fa8ff, 0x39d070, 0xff4fd8))):
        x = k * 14; sub = A.sub(x, 56, 14, 16); sub[:] = hexrgb(bg); write(sub, ch, 2, 2, 2, 0xffffff if k != 1 else INK)
        letters.append(A.rect(x, 56, 14, 16))
    ban = A.fill(72, 56, 8, 8, 0xffd83a); piz = A.sub(80, 56, 16, 16); piz[:] = hexrgb(0xffb43a); px_disc(piz, 5, 6, 2.4, 0xd02a2a); px_disc(piz, 10, 11, 2.2, 0xd02a2a)
    red = A.fill(96, 56, 8, 8, 0xe02a3a)
    decal = mat('fr_decal', 0xffffff, rough=0.35, clearcoat=0.4, tex=A.image())
    O = []
    secs = [(0.07, 0.0), (0.38, 0.0), (0.7, 0.0), (1.0, 0.0), (1.22, 0.0), (1.30, 0.03), (1.36, 0.075), (1.395, 0.125), (1.41, 0.17)]
    body = ring_body([(y, [(x, z) for x, z in rr_pts(0.72 - 2 * i, 0.66 - 2 * i, 0.075, 2, 2)]) for y, i in secs], paint, 'fridge')
    dent(body, (0.36, 0.62, 0.06), 0.16, 0.03); dent(body, (0.12, 1.41, 0.08), 0.16, 0.02); dent(body, (-0.33, 0.3, 0.3), 0.14, 0.025)
    O.append(body)
    door = side_x(rrect(0, 0.68, 0.68, 1.08, 0.09, 3), 0.05, (0, 0, -0.35), paint, bev=0.018, seg=2)
    O.append(door)
    O.append(box((0.05, 0.15, 0.03), (-0.285, 0.97, -0.386), chrome, bev=0.008, seg=1))
    O.append(sweep([(-0.285, 1.02, -0.39), (-0.292, 1.035, -0.43), (-0.295, 0.99, -0.452), (-0.295, 0.9, -0.452), (-0.29, 0.86, -0.44)], 0.014, chrome, seg=6, squash=(1.0, 0.7), name='handle'))
    O.append(box((0.6, 0.014, 0.006), (0, 1.05, -0.377), chrome))
    O.append(uv_fit(box((0.22, 0.045, 0.006), (0, 1.13, -0.377), decal), A.rect(48, 0, 80, 16)))
    O.append(uv_fit(box((0.64, 0.075, 0.02), (0, 0.115, -0.33), decal, bev=0.004, seg=1), A.rect(48, 16, 64, 16)))
    for x in (-0.3, 0.3):
        for z in (-0.26, 0.26): O.append(cyl(0.026, 0.075, (x, 0.04, z), chrome, axis='y', seg=8, r2=0.02))
    # magnets + the note
    zf = -0.375 - 0.005
    for k, (x, y, a) in enumerate(((-0.17, 0.86, 0.1), (-0.12, 0.85, -0.08), (-0.07, 0.865, 0.05), (-0.02, 0.85, -0.12), (0.035, 0.862, 0.18))):
        O.append(uv_fit(box((0.04, 0.05, 0.01), (x, y, zf), decal, rot=(0, 0, a)), letters[k]))
    O.append(uv_fit(box((0.17, 0.2, 0.002), (0.12, 0.6, -0.3765), decal, rot=(0, 0, -0.06)), A.rect(0, 0, 48, 56)))
    O.append(uv_fit(cyl(0.017, 0.01, (0.12, 0.69, -0.384), decal, axis='z', seg=8), red))
    bn = sweep([(0.18, 0.95, zf), (0.21, 0.93, zf), (0.24, 0.935, zf), (0.265, 0.96, zf)], [0.006, 0.011, 0.011, 0.005], decal, seg=6, squash=(1.0, 0.6), name='banana')
    O.append(uv_fit(bn, ban))
    pz = side_x([(-0.03, 0.03), (0.03, 0.03), (0.0, -0.045)], 0.008, (-0.2, 0.42, zf), decal, bev=0.002, seg=1)
    O.append(uv_fit(pz, A.rect(80, 56, 16, 16)))
    for o in O:
        if o.data.materials and o.data.materials[0] in (paint, chrome): uv_tile(o, 0.3)
    return O, {'paint': ['fr_paint'], 'carry': True}


# ------------------------------------------------------------------------------------------------ scooter
def build_scooter():
    paint = mat('sc_paint', 0xffffff, rough=0.2, clearcoat=0.9, tex=tex_noise('sc_paint_t', 0xf8f6f2, var=0.04, size=16, seed=17, speck=0xc8c0b8, speck_p=0.05))
    chrome = plain('sc_chrome', 0xdde1ea, rough=0.14, metal=1.0, var=0.05, seed=18)
    rub = plain('sc_rubber', 0x24222a, rough=0.6, var=0.12, seed=19, speck=0x4a4652, p=0.1)
    A = Atlas('sc_decal_t', 64)
    st = [A.fill(k * 8, 0, 8, 32, c) for k, c in enumerate((0xff4fd8, 0xffe14d, 0x4fd8ff, 0x7dff4f))]
    plate = A.sub(0, 32, 64, 16); plate[:] = hexrgb(0xffe14d); plate[0] = plate[-1] = hexrgb(INK); write(plate, 'LIL ZOOM', 8, 4, 1, INK)
    decal = mat('sc_decal', 0xffffff, rough=0.45, clearcoat=0.3, tex=A.image())
    lens = mat('sc_lens', 0xfff4d0, rough=0.1, emit=0xfff0b8, strength=6.0)
    O = []
    O.append(box((0.125, 0.028, 0.58), (0, 0.076, 0.03), paint, bev=0.01, seg=1))
    for z in (0.345, -0.37):  # fat little tyres, capped (the cap is the hub)
        O.append(lathe([(0.062, -0.017), (0.1, 0.0), (0.062, 0.017)], (0, 0.1, z), rub, seg=8, axis='x', name='tyre'))
    O.append(box((0.06, 0.05, 0.1), (0, 0.095, 0.3), chrome))
    O.append(box((0.05, 0.13, 0.03), (0, 0.17, -0.355), chrome, rot=(-0.15, 0, 0)))
    O.append(sweep([(0, 0.1 + 0.112 * math.sin(math.radians(a)), 0.345 - 0.112 * math.cos(math.radians(a))) for a in (20, 55, 90, 125)], 0.036, paint, seg=4, squash=(0.13, 1.0), name='guard'))
    O.append(rod((0, 0.085, -0.255), (0, 0.24, -0.335), 0.019, chrome, seg=4))
    O.append(rod((0, 0.22, -0.345), (0, 0.865, -0.262), 0.016, chrome, seg=5))
    O.append(rod((-0.2, 0.865, -0.262), (0.2, 0.865, -0.262), 0.011, chrome, seg=4))
    for s in (-1, 1):
        O.append(cyl(0.019, 0.1, (s * 0.165, 0.865, -0.262), rub, axis='x', seg=5))
        for k in range(2):
            x0 = s * 0.212; dz = (k - 0.5) * 0.012
            pts = [(x0, 0.865, -0.262 + dz), (x0 + s * 0.02, 0.77, -0.21 + dz), (x0 + s * (0.03 + k * 0.01), 0.66 - k * 0.04, -0.16 + dz * 2)]
            O.append(uv_fit(sweep(pts, 0.009, decal, seg=4, squash=(1.0, 0.2), name='streamer'), st[(k + (0 if s < 0 else 2)) % 4]))
    # moped bits: leg shield, headlight, seat, exhaust, plate
    pts = []
    for j in range(4):
        y = 0.2 + j * 0.14; row = []
        hw = 0.09 + (y - 0.2) / 0.42 * 0.085 - (0.025 if j == 3 else 0)
        for i in range(4):
            u = i / 3 * 2 - 1; x = u * hw
            row.append((x, y + (0.03 * (1 - u * u) if j == 3 else 0), -0.372 + (y - 0.2) * 0.14 + 2.2 * x * x))
        pts.append(row)
    sh = sheet_grid(pts[::-1], paint, 'shield')
    sol = sh.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.012; sol.offset = 0.0
    apply_mods(sh)
    bmx = bmesh.new(); bmx.from_mesh(sh.data); bmesh.ops.recalc_face_normals(bmx, faces=bmx.faces); bmx.to_mesh(sh.data); bmx.free()
    O.append(sh)
    O.append(cyl(0.056, 0.03, (0, 0.5, -0.345), lens, axis='z', seg=8, rot=(-0.14, 0, 0)))
    O.append(rod((0, 0.09, 0.2), (0, 0.42, 0.225), 0.013, chrome, seg=4))
    O.append(box((0.17, 0.06, 0.26), (0, 0.445, 0.23), rub, rot=(-0.05, 0, 0), taper=(0.75, 1.0)))
    O.append(sweep([(0.03, 0.06, 0.14), (0.07, 0.07, 0.3), (0.078, 0.1, 0.45)], 0.016, chrome, seg=4, name='exhaust'))
    O.append(uv_fit(box((0.1, 0.05, 0.004), (0, 0.175, 0.452), decal, rot=(-0.35, 0, 0)), A.rect(0, 32, 64, 16)))
    for o in O:
        if o.data.materials and o.data.materials[0] in (paint, chrome, rub, lens): uv_tile(o, 0.2)
    L = [box((0.125, 0.028, 0.58), (0, 0.076, 0.03), paint), rod((0, 0.09, -0.3), (0, 0.865, -0.262), 0.018, chrome, seg=4),
         box((0.42, 0.024, 0.024), (0, 0.865, -0.262), rub), box((0.3, 0.4, 0.03), (0, 0.42, -0.36), paint, taper=(0.65, 1.0), rot=(-0.14, 0, 0)),
         box((0.17, 0.06, 0.26), (0, 0.445, 0.23), rub), rod((0, 0.09, 0.2), (0, 0.42, 0.225), 0.014, chrome, seg=3)]
    for z in (0.345, -0.37): L.append(lathe([(0.062, -0.017), (0.1, 0.0), (0.062, 0.017)], (0, 0.1, z), rub, seg=5, axis='x', name='tyre'))
    tiled(L, 0.2)
    return O, {'_lod': L, 'paint': ['sc_paint'], 'lights': [[0, 0.5, -0.37, 0xfff0b8]]}


# ------------------------------------------------------------------------------------------------ wall AC
def build_acunit():
    A = Atlas('ac_paint_t', 64)
    crust(A.sub(0, 0, 32, 32), 0xf4f2ee, 0.05, seed=20, speck=0xc8c2ba, p=0.05)
    lv = A.sub(32, 0, 32, 32); crust(lv, 0xf0eee8, 0.04, seed=21)
    for y in range(3, 30, 4): lv[y:y + 2, 3:29] = hexrgb(0x5a5a62)
    stn = A.sub(0, 32, 64, 32); crust(stn, 0xf4f2ee, 0.05, seed=20, speck=0xc8c2ba, p=0.05)
    for x, L in ((20, 26), (23, 18), (40, 30), (44, 14)): drip(stn, x, 0, L, 0xa07a50, 2)
    grime(stn, 0xa88a60, 0.12, seed=7, blob=3)
    paint = mat('ac_paint', 0xffffff, rough=0.35, clearcoat=0.4, tex=A.image())
    dark = plain('ac_dark', 0x1c1a22, rough=0.5, var=0.1, seed=22)
    metal = plain('ac_metal', 0xaab0b8, rough=0.3, metal=0.9, var=0.12, seed=23, speck=0x8a6a4a, p=0.05)
    D = Atlas('ac_decal_t', 64)
    stk = D.sub(0, 0, 64, 40); stk[:] = hexrgb(0xffffff); stk[0:12] = hexrgb(0x4fd8ff)
    smiley(stk, 7, 6, 5, face=0xffe14d, ink=INK); write(stk, 'CORP', 15, 3, 1, INK)
    write(stk, 'COOLING', 3, 15, 1, 0x2a5a9a); px_line(stk, 2, 18, 46, 18, 0xff3030, 1.6)
    write(stk, 'cold-ish', 6, 26, 1, 0xff3030, wob=1, seed=4, bold=True)
    wht = D.fill(0, 40, 16, 16, 0xf2f2f2); blu = D.fill(16, 40, 16, 16, 0x7ad0ff); cop = D.fill(32, 40, 16, 16, 0xd08a5a)
    decal = mat('ac_decal', 0xffffff, rough=0.25, clearcoat=0.5, tex=D.image())
    O = []
    case = box((0.76, 0.52, 0.27), (0, 0.26, -0.185), paint, bev=0.014, seg=1); O.append(uv_fit(case, A.rect(0, 0, 32, 32)))
    O.append(uv_fit(box((0.004, 0.36, 0.2), (0.381, 0.27, -0.19), paint), A.rect(32, 0, 32, 32)))  # louvres (pipe side)
    O.append(uv_fit(box((0.3, 0.2, 0.003), (-0.1, 0.11, -0.3215), paint), A.rect(0, 32, 64, 32)))  # the drip stain
    fx, fy, fz = -0.1, 0.27, -0.32
    O.append(cyl(0.2, 0.012, (fx, fy, fz - 0.002), dark, axis='z', seg=10))
    for k in range(2):
        a = k * math.pi + 0.5
        O.append(box((0.3, 0.07, 0.006), (fx, fy, fz - 0.016 - 0.007 * k), dark, rot=(0, 0.35, a)))
    O.append(torus(0.195, 0.0045, (fx, fy, fz - 0.03), metal, axis='z', seg=12, sides=3))
    for a in (math.pi / 4, -math.pi / 4):
        O.append(box((0.39, 0.009, 0.006), (fx, fy, fz - 0.03), metal, rot=(0, 0, a)))
    O.append(uv_fit(box((0.13, 0.075, 0.002), (0.24, 0.43, -0.3215), decal, rot=(0, 0, 0.05)), D.rect(0, 0, 64, 40)))
    O.append(box((0.03, 0.13, 0.09), (0.392, 0.11, -0.26), paint))
    O.append(uv_fit(sweep([(0.4, 0.14, -0.26), (0.48, 0.14, -0.25), (0.49, 0.14, -0.04), (0.49, 0.14, 0.01)], 0.016, decal, seg=4, name='insul'), wht))
    O.append(uv_fit(rod((0.4, 0.085, -0.26), (0.46, 0.085, -0.26), 0.008, decal, seg=4), cop))
    O.append(uv_fit(sweep([(0.3, 0.005, -0.2), (0.3, -0.08, -0.205), (0.315, -0.17, -0.19)], 0.006, decal, seg=4, name='drain'), wht))
    O.append(uv_fit(ball(0.011, (0.315, -0.186, -0.19), decal, scale=(1, 1.5, 1), seg=6, rings=3), blu))
    for x in (-0.28, 0.28):
        O.append(box((0.035, 0.035, 0.34), (x, -0.0175, -0.17), metal))
        O.append(rod((x, -0.28, -0.003), (x, -0.03, -0.31), 0.009, metal, seg=4))
    for o in O:
        if o.data.materials and o.data.materials[0] in (dark, metal): uv_tile(o, 0.2)
    L = [uv_fit(box((0.76, 0.52, 0.27), (0, 0.26, -0.185), paint), A.rect(0, 0, 32, 32)), cyl(0.2, 0.014, (fx, fy, fz - 0.002), dark, axis='z', seg=8),
         uv_fit(box((0.13, 0.075, 0.002), (0.24, 0.43, -0.3215), decal), D.rect(0, 0, 64, 40)), uv_fit(rod((0.4, 0.14, -0.25), (0.49, 0.14, 0.01), 0.016, decal, seg=4), wht)]
    for x in (-0.28, 0.28): L.append(box((0.035, 0.035, 0.34), (x, -0.0175, -0.17), metal))
    for o in L[1:2] + L[4:]: uv_tile(o, 0.2)
    return O, {'_lod': L, 'paint': ['ac_paint'], 'mount': 'wall', 'note': 'origin on the wall face at the underside of the case'}


# ------------------------------------------------------------------------------------------------ fallen ☺ sign
def build_smilesign():
    F = Atlas('ss_face_t', 128)
    fc = F.sub(0, 0, 128, 128); crust(fc, 0xffe14d, 0.07, seed=30, speck=0xf0c030, p=0.06)
    rr = np.random.default_rng(5)
    for k in range(5):  # cracks from the broken chunk (lower left, as seen from the front)
        x, y = 104.0, 100.0
        for s in range(14):
            nx, ny = x - rr.uniform(3, 9), y - rr.uniform(-6, 7) - k * 0.8
            px_line(fc, x, y, nx, ny, 0x6a5010, 1.2); x, y = nx, ny
    for x in range(6, 128, 13): drip(fc, x, int(rr.uniform(0, 20)), int(rr.uniform(8, 30)), 0xd8b030, 1)
    write(fc, 'home', 18, 98, 3, 0xff4fd8, wob=2, seed=3, bold=True); heart(fc, 98, 104, 4, 0xff4fd8)
    grime(fc, 0xb09030, 0.12, seed=6, blob=8)
    ink = F.fill(0, 0, 1, 1, INK)
    INK_R = F.rect(0, 0, 1, 1, 0)
    face = mat('ss_face', 0xffffff, rough=0.28, clearcoat=0.6, tex=F.image())
    inkm = plain('ss_ink', 0x18141c, rough=0.15, cc=0.8, var=0.04, seed=31)
    M_ = Atlas('ss_rim_t', 32)
    rim_r = M_.fill(0, 0, 16, 32, 0x4fd8ff); glass = M_.fill(16, 0, 16, 16, 0xf4f0e8); pole = M_.fill(16, 16, 16, 16, 0x9aa0aa)
    rim = mat('ss_rim', 0xffffff, rough=0.22, metal=0.3, clearcoat=0.7, tex=M_.image())
    lit = mat('ss_lit', 0xfff2c0, rough=0.1, emit=0xffe8a0, strength=5.0)
    RB = Atlas('ss_rubble_t', 64)
    crust(RB.sub(0, 0, 64, 48), 0x9a928a, 0.16, seed=32, speck=[(0x6a625a, 0.1), (0xffb3c7, 0.04), (0x5fd3c6, 0.04), (0xffe58a, 0.04)])
    chips = [RB.fill(k * 16, 48, 16, 16, c) for k, c in enumerate((0xffb3c7, 0x5fd3c6, 0xffe58a, 0x9a4a2a))]
    rub = mat('ss_rubble', 0xffffff, rough=0.85, tex=RB.image())
    T = Atlas('ss_tarp_t', 64)
    tiedye(T.sub(0, 0, 64, 48), DYE, seed=12, arms=3, twist=6)
    rope = T.fill(0, 48, 16, 16, 0xe8d8a8); woodr = T.fill(16, 48, 16, 16, 0xa8743a); brush = T.fill(32, 48, 16, 16, 0xffd84a)
    tarp = mat('ss_tarp', 0xffffff, rough=0.8, tex=T.image())
    # --- the sign, built upright facing -z round its centre, then tipped back into the rubble
    S = []
    disc = cyl(2.0, 0.28, (0, 0, 0), face, axis='z', seg=32)
    multi_mat(disc, [face, rim], lambda n, c: 0 if n[2] < -0.9 else 1)
    uv_fit(disc, (0, 0, 1, 1), mode='front', only={0}); uv_fit(disc, rim_r, only={1})
    chunk_poly = [(-2.3, -0.3), (-1.55, -0.55), (-1.25, -0.95), (-0.95, -1.15), (-1.05, -1.55), (-0.7, -2.4), (-2.4, -2.4)]
    piece = dup(disc)
    cut(disc, side_x([(x + 0.02, y + 0.02) for x, y in chunk_poly], 1.0, (0, 0, 0), rim))  # a hair inside the rim's cut
    cut(piece, side_x(chunk_poly, 1.0, (0, 0, 0), rim), op='INTERSECT')
    S.append(disc)
    ring = lathe([(1.95, -0.13), (2.06, -0.13), (2.06, -0.22), (1.95, -0.22), (1.95, -0.13)], (0, 0, 0), rim, seg=32, axis='z', name='rim', cap=False)
    cut(ring, side_x(chunk_poly, 1.0, (0, 0, 0), rim))
    S.append(uv_fit(ring, rim_r))
    for s in (-1, 1):
        S.append(lathe([(0.0, -0.21), (0.13, -0.204), (0.21, -0.178), (0.25, -0.14), (0.25, -0.12)], (s * 0.62, 0.72, 0), inkm, seg=12, axis='z', name='eye'))
    for o in S[-2:]:
        for v in o.data.vertices: v.co.z = v.co.z * 1.55  # tall oval eyes (local z = game up)
    mp = []
    for k in range(11):
        a = math.radians(208 + 124 * k / 10)
        mp.append((math.cos(a) * 1.05, 0.38 + math.sin(a) * 1.05, -0.15))
    S.append(sweep(mp, 0.1, inkm, seg=6, squash=(1.0, 0.35), name='mouth'))
    for s in (-1, 1): S.append(rod((s * 0.96, -0.02, -0.15), (s * 1.06, 0.12, -0.15), 0.06, inkm, seg=6))  # dimples
    lit_k = {1, 5, 6, 11, 15, 19}; gone = {9, 22}
    bulbs = []
    for k in range(24):
        a = 2 * math.pi * k / 24 + 0.13
        x, y = math.cos(a) * 2.005, math.sin(a) * 2.005
        if pip((x, y), chunk_poly): continue  # in the broken chunk
        if k in gone:
            S.append(uv_fit(cyl(0.022, 0.03, (x, y, -0.235), rim, axis='z', seg=6), pole)); continue
        b = ball(0.046, (x, y, -0.262), lit if k in lit_k else rim, scale=(1, 1, 1.2), seg=6, rings=4)
        if k not in lit_k: uv_fit(b, glass)
        S.append(b); bulbs.append(((x, y, -0.27), k in lit_k))
    tiltx, roll, yaw = 0.74, 0.1, 0.12
    C = (0.0, 1.32, -0.05)
    xform(S, rot=(tiltx, yaw, roll), move=C)
    f = mpt(rot=(tiltx, yaw, roll), move=C)
    for o in S[:2]: cut(o, box((12, 4, 12), (0, -2.0 + 0.02, 0), rim))
    S = [o for o in S if game_bbox(o)[1][1] > 0.02]
    bulbs = [(p, on) for p, on in bulbs if f(p)[1] > 0.1]
    # the broken-off chunk, face up on the rubble out front
    lo, hi = game_bbox(piece); pc = [(lo[k] + hi[k]) / 2 for k in range(3)]
    xform([piece], rot=(1.3, 0.6, 0.15), move=(-1.25 - pc[0], 0.3 - pc[1], -1.75 - pc[2]), pivot=pc)
    for o in (S[0], S[1], piece):  # cut faces came in with no UVs
        k = [i for i, m in enumerate(o.data.materials) if m == rim]
        uv_fit(o, rim_r, only=set(k))
    # rubble mound round the sign's foot
    R = []
    def hgt(x, z):
        e = max(0.0, 1 - ((x / 2.7) ** 2 + ((z + 0.3) / 1.75) ** 2))
        return 0.85 * e ** 0.9 * math.exp(-((z + 0.75) / 1.1) ** 2)
    bm = bmesh.new(); NA, NR = 16, 5; rings = []
    rr_ = random.Random(11)
    jag = [rr_.uniform(0.86, 1.08) for _ in range(NA)]
    for r in range(1, NR + 1):
        ring = []
        for i in range(NA):
            a = 2 * math.pi * i / NA; t = r / NR
            x, z = math.cos(a) * 2.75 * t * (jag[i] if r == NR else 1), -0.45 + math.sin(a) * 1.75 * t * (jag[i] if r == NR else 1)
            y = 0.0 if r == NR else max(0.02, hgt(x, z) + rr_.uniform(-0.06, 0.06))
            ring.append(bm.verts.new(gv(x + (rr_.uniform(-0.08, 0.08) if r < NR else 0), y, z)))
        rings.append(ring)
    cv = bm.verts.new(gv(0, hgt(0, -0.45), -0.45))
    for i in range(NA): bm.faces.new((cv, rings[0][i], rings[0][(i + 1) % NA]))
    for a_, b_ in zip(rings, rings[1:]):
        for i in range(NA): bm.faces.new((a_[i], b_[i], b_[(i + 1) % NA], a_[(i + 1) % NA]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mound = lib._obj('mound', bm, rub); face_toward(mound, (0, 1, 0))
    R.append(uv_fit(mound, RB.rect(0, 0, 64, 48)))
    rnd = random.Random(9)
    for k in range(13):
        x, z = rnd.uniform(-2.3, 2.3), rnd.uniform(-1.9, 0.6)
        s = rnd.uniform(0.16, 0.42)
        c = box((s, s * rnd.uniform(0.4, 0.8), s * rnd.uniform(0.6, 1.1)), (x, hgt(x, z) - 0.02 + s * 0.15, z), rub, rot=(rnd.uniform(-0.5, 0.5), rnd.uniform(0, 3), rnd.uniform(-0.5, 0.5)))
        jitter(c, s * 0.08, seed=k)
        R.append(uv_fit(c, chips[k % 4] if k % 3 == 0 else RB.rect(0, 0, 64, 48)))
    for k, (x, z) in enumerate(((-1.6, -1.1), (1.3, -1.25), (0.7, -1.7), (-0.5, -1.6))):
        y0 = hgt(x, z)
        R.append(uv_fit(sweep([(x, y0 - 0.05, z), (x + 0.04, y0 + 0.3, z - 0.03), (x + 0.14, y0 + 0.42 + k * 0.05, z - 0.08)], 0.009, rub, seg=4, name='rebar'), chips[3]))
    # props under its back + the tarp roof the squatters tied off it
    for s in (-1, 1):
        a = f((s * 0.85, 0.35, 0.14)); g = (a[0] + s * 0.15, 0.0, a[2] + 0.75)
        R.append(uv_fit(rod(g, a, 0.03, rim, seg=6), pole))
    A0 = [f((-1.38, 1.38, 0.15)), f((0.0, 1.5, 0.15)), f((1.38, 1.38, 0.15))]
    back_z = max(p[2] for p in A0) + 2.1
    poles = [(-1.45, back_z), (1.45, back_z)]
    TT = []
    for j in range(7):
        v = j / 6; row = []
        for i in range(9):
            u = i / 8
            a = A0[0] if u <= 0.5 else A0[2]
            t = (u * 2) if u <= 0.5 else (u - 0.5) * 2
            att = tuple(A0[0][k] + (A0[1][k] - A0[0][k]) * t for k in range(3)) if u <= 0.5 else tuple(A0[1][k] + (A0[2][k] - A0[1][k]) * t for k in range(3))
            back = (-1.5 + 3.0 * u, 1.92 - 0.14 * math.sin(math.pi * u), back_z + 0.05)
            p = [att[k] + (back[k] - att[k]) * v for k in range(3)]
            p[1] -= 0.22 * math.sin(math.pi * v) * (0.6 + 0.4 * math.sin(math.pi * u))
            p[1] += random.uniform(-0.015, 0.015)
            row.append(tuple(p))
        TT.append(row)
    tp = sheet_grid(TT, tarp, 'tarp'); face_toward(tp, (0, 1, 0))
    R.append(uv_fit(tp, T.rect(0, 0, 64, 48), mode='box'))
    for (x, z) in poles:
        R.extend(broom(x, z, 1.92, tarp, tarp, woodr, brush))
        R.append(uv_fit(sweep([(x, 1.9, z), (x * 1.05, 1.0, z + 0.6), (x * 1.08, 0.02, z + 1.1)], 0.007, tarp, seg=4, name='guy'), rope))
        R.append(uv_fit(box((0.22, 0.08, 0.11), (x * 1.08, 0.04, z + 1.12), rub, bev=0.01, seg=1), chips[3]))
    for p in A0:
        R.append(uv_fit(torus(0.06, 0.008, p, tarp, axis='x', seg=8, sides=3), rope))
    lights = [[round(c, 2) for c in f(p)] + [0xffe8a0] for p, on in bulbs if on]
    return S + [piece] + R, {'lights': lights, 'roof': True}


# ------------------------------------------------------------------------------------------------ string lights
def build_stringlights():
    A = Atlas('sl_bulb_t', 32)
    cols = [0xffd890, 0xff6fd0, 0xffe14d, 0x5fe8ff]
    sw = [A.fill((k % 4) * 8, (k // 4) * 8, 8, 8, c) for k, c in enumerate(cols)]
    dead = A.fill(0, 16, 8, 8, 0x3a3640)
    bulbm = mat('sl_bulb', 0xffffff, rough=0.1, emit=0xffffff, strength=4.0, tex=A.image(), emit_tex=True)
    cab = plain('sl_cable', 0x1a181e, rough=0.4, var=0.06, seed=40)
    O = []
    path = bend_path((-2, 0, 0), (2, 0, 0), 0.32, n=10)
    O.append(sweep(path, 0.0055, cab, seg=4, name='cable'))
    def yat(x):
        t = (x + 2) / 4
        return -0.32 * 4 * t * (1 - t)
    lights = []
    for i in range(10):
        x = -1.8 + i * 0.4; y = yat(x)
        O.append(cyl(0.0125, 0.045, (x, y - 0.02, 0), cab, axis="y", seg=4, cap=False))
        k = i % 4
        b = ball(0.034, (x, y - 0.075, 0), bulbm, scale=(1, 1.25, 1), seg=6, rings=3)
        if i == 6: uv_fit(b, dead)
        else: uv_fit(b, sw[k]); lights.append([round(x, 2), round(y - 0.075, 3), 0, cols[k]])
        O.append(b)
    for o in O:
        if o.data.materials[0] == cab: uv_tile(o, 0.2)
    L = [sweep(bend_path((-2, 0, 0), (2, 0, 0), 0.32, n=4), 0.006, cab, seg=3, name='cable')]
    uv_tile(L[0], 0.2)
    for i in range(10):
        x = -1.8 + i * 0.4
        b = ball(0.04, (x, yat(x) - 0.06, 0), bulbm, scale=(1, 1.3, 1), seg=3, rings=2)
        L.append(uv_fit(b, dead if i == 6 else sw[i % 4]))
    return O, {'_lod': L, 'span': [-2, 2], 'lights': lights}


# ------------------------------------------------------------------------------------------------ tie-dye lean-to
def build_tarp():
    T = Atlas('tp_cloth_t', 128)
    tiedye(T.sub(0, 0, 128, 128), [0xff6fae, 0xffe14d, 0x3fd6c6, 0xb48cff, 0x9ff5c8], seed=17, arms=3, twist=6)
    cloth = mat('tp_cloth', 0xffffff, rough=0.8, tex=T.image())
    K = Atlas('tp_kit_t', 64)
    wd = K.sub(0, 0, 32, 32); wood(wd, 0xc8955a, 0x8a5a2b, seed=3)
    rope = K.fill(32, 0, 16, 16, 0xe8d8a8); brush = K.fill(48, 0, 16, 16, 0xffd84a); brushh = K.fill(32, 16, 16, 16, 0xff6fae)
    tin = K.sub(0, 32, 32, 32); crust(tin, 0x9aa8b0, 0.1, seed=4); tin[4:12] = hexrgb(0x5fd3c6); write(tin, 'PAINT', 1, 5, 1, 0xffffff)
    conc = K.fill(32, 32, 16, 16, 0xa8a49e); brick = K.fill(48, 32, 16, 16, 0xb8583a)
    kit = mat('tp_kit', 0xffffff, rough=0.6, clearcoat=0.2, tex=K.image())
    O = []
    G = []
    for j in range(9):
        v = j / 8; z = 1.0 - 2.15 * v; row = []
        for i in range(13):
            u = i / 12; x = -1.55 + 3.1 * u
            y = 2.32 + (1.97 - 2.32) * v
            y -= 0.16 * math.sin(math.pi * v) * (0.55 + 0.45 * math.sin(math.pi * u))
            if j == 8: y -= 0.07 * math.sin(math.pi * (abs(x) - 1.42) / 0.1) if abs(x) > 1.42 else 0.09 * math.sin(math.pi * (x + 1.42) / 2.84)
            y += random.uniform(-0.012, 0.012) * math.sin(math.pi * v)
            row.append((x, y, z))
        G.append(row)
    tp = sheet_grid(G, cloth, 'tarp'); face_toward(tp, (0, 1, 0)); O.append(uv_fit(tp, (0, 0, 1, 1)))
    O.append(uv_fit(box((3.0, 0.09, 0.045), (0, 2.34, 1.0), kit, bev=0.006, seg=1), K.rect(0, 0, 32, 32)))
    for x in (-1.2, 0.0, 1.2): O.append(uv_fit(torus(0.035, 0.007, (x, 2.33, 0.98), kit, axis='x', seg=8, sides=3), rope))
    for s in (-1, 1):
        x, z = s * 1.42, -1.15
        O.extend(broom(x, z, 1.95, kit, kit, K.rect(0, 0, 32, 32), brush if s < 0 else brushh, lean=(s * 0.03, 0.02), y0=0.05))
        O.append(uv_fit(cyl(0.12, 0.2, (x, 0.1, z), kit, axis='y', seg=10, bev=0.006), K.rect(0, 32, 32, 32)))
        O.append(uv_fit(cyl(0.11, 0.01, (x, 0.2, z), kit, axis='y', seg=10), conc))
        O.append(uv_fit(torus(0.03, 0.007, (x + s * 0.03, 1.93, z + 0.02), kit, axis='y', seg=8, sides=3), rope))
        O.append(uv_fit(sweep([(x + s * 0.03, 1.93, z), (x + s * 0.25, 1.0, z - 0.45), (x + s * 0.45, 0.06, z - 0.85)], 0.007, kit, seg=4, name='guy'), rope))
        O.append(uv_fit(box((0.22, 0.08, 0.11), (x + s * 0.47, 0.04, z - 0.87), kit, bev=0.01, seg=1, rot=(0, 0.3 * s, 0)), brick))
    return O, {'wall': '+z edge (z = 1) goes against a wall', 'roof': True}


# ------------------------------------------------------------------------------------------------ front door
def build_door_bottom():
    P = Atlas('dr_paint_t', 32, 64)
    crust(P.sub(0, 0, 32, 64), 0xeeece6, 0.05, seed=50, speck=0xc8c4bc, p=0.05)
    for x in range(2, 32, 5): P.px[:, x] *= 0.97
    paint = mat('dr_paint', 0xffffff, rough=0.35, clearcoat=0.5, tex=P.image())
    W = Atlas('dr_wood_t', 64)
    wood(W.sub(0, 0, 64, 16), 0xc8955a, 0x8a5a2b, seed=5)
    tw_ = W.sub(0, 16, 64, 16); wood(tw_, 0x5fd3c6, 0x3a9a90, seed=6, rings=3); m = np.random.default_rng(3).random(tw_.shape[:2]) < 0.25; tw_[m] = hexrgb(0xb88a50)
    pw = W.sub(0, 32, 64, 16); wood(pw, 0xffb3c7, 0xd88aa0, seed=7, rings=3); m = np.random.default_rng(4).random(pw.shape[:2]) < 0.2; pw[m] = hexrgb(0xb88a50)
    for x in (6, 30, 56): px_disc(pw, x, 8, 1.3, 0x5a5a60)
    woodm = mat('dr_wood', 0xffffff, rough=0.6, clearcoat=0.2, tex=W.image())
    chrome = plain('dr_metal', 0xd8dce4, rough=0.16, metal=1.0, var=0.05, seed=51)
    D = Atlas('dr_decal_t', 128)
    pl = D.sub(0, 0, 64, 16); crust(pl, 0xd8b04a, 0.06, seed=52); pl[0] = pl[-1] = hexrgb(0x8a6a20); write(pl, 'MANAGER', 11, 4, 1, 0x2a1a08)
    px_line(pl, 4, 2, 60, 14, 0xff2a3a, 2.2); px_line(pl, 4, 14, 60, 2, 0xff2a3a, 2.2); drip(pl, 20, 9, 6, 0xff2a3a); drip(pl, 44, 8, 7, 0xff2a3a)
    tp = D.sub(0, 16, 64, 16); crust(tp, 0xf0e2b8, 0.04, seed=53); write(tp, 'everyone', 7, 4, 1, 0x1a1a8a, wob=1, seed=5, bold=True)
    gl = D.sub(64, 0, 16, 64); gl[:] = hexrgb(0x3a5a6a); gl[::4] = hexrgb(0x9ab0b8); gl[:, ::4] = hexrgb(0x9ab0b8); gl[2:30, 2:5] = hexrgb(0x6a8a9a)
    st1 = D.sub(80, 0, 48, 24); st1[:] = hexrgb(0xffe14d); st1[0] = st1[-1] = st1[:, 0] = st1[:, -1] = hexrgb(INK)
    write(st1, 'no', 4, 2, 1, INK); write(st1, 'interns', 4, 12, 1, INK)
    st2 = D.sub(80, 24, 24, 24); st2[:] = hexrgb(0xffffff); smiley(st2, 12, 12, 10, face=0xffe14d, ink=INK)
    px_line(st2, 6, 15, 12, 13, INK, 2.0); px_line(st2, 12, 13, 18, 15, INK, 2.0)  # moustache
    fl = D.sub(0, 32, 32, 32); fl[:] = hexrgb(0x5a5a62); fl[3:29, 3:29] = hexrgb(0x8a7a9a); fl[3:6, 3:29] = hexrgb(0xb0a0c0); write(fl, 'CAT', 7, 12, 1, 0xffffff)
    cb = D.sub(32, 32, 32, 32); crust(cb, 0xa8a49e, 0.1, seed=54); cb[5:27, 4:14] = hexrgb(0x4a4844); cb[5:27, 18:28] = hexrgb(0x4a4844)
    kn = D.sub(0, 64, 64, 40); crust(kn, 0xc8995a, 0.06, seed=55); grime(kn, 0x8a6a3a, 0.1, seed=2, blob=4)
    write(kn, 'knock', 3, 4, 2, 0x1a1a20, wob=1, seed=6); write(kn, 'loud', 10, 22, 2, 0xc0182a, wob=1, seed=8, bold=True)
    decal = mat('dr_decal', 0xffffff, rough=0.3, clearcoat=0.4, tex=D.image())
    O = []
    O.append(uv_fit(box((0.07, 2.1, 0.12), (0.465, 1.05, 0), woodm, rot=(0, 0, 0.006)), W.rect(0, 16, 64, 16)))
    O.append(uv_fit(box((0.075, 2.08, 0.11), (-0.4625, 1.04, 0.005), woodm, rot=(0, 0, -0.004)), W.rect(0, 0, 64, 16)))
    O.append(uv_fit(box((1.02, 0.075, 0.125), (0, 2.065, 0), woodm, rot=(0, 0, 0.012)), W.rect(0, 32, 64, 16)))
    leaf = box((0.85, 1.98, 0.044), (-0.005, 1.035, 0), paint, bev=0.006, seg=1, rot=(0, 0, 0.006))
    O.append(uv_fit(leaf, P.rect(0, 0, 32, 64)))
    O.append(uv_fit(box((0.15, 0.6, 0.05), (-0.2, 1.5, 0), decal), D.rect(64, 0, 16, 64)))  # wired vision panel, both faces
    O.append(cyl(0.03, 0.06, (-0.35, 1.0, 0), chrome, axis='z', seg=6))  # roses, both sides in one
    for s_ in (-1, 1): O.append(box((0.12, 0.018, 0.016), (-0.3, 1.0, s_ * 0.048), chrome))
    O.append(uv_fit(box((0.3, 0.075, 0.003), (0.08, 1.68, -0.0235), decal, rot=(0, 0, -0.02)), D.rect(0, 0, 64, 16)))
    O.append(uv_fit(box((0.3, 0.07, 0.002), (0.09, 1.585, -0.024), decal, rot=(0, 0, 0.04)), D.rect(0, 16, 64, 16)))
    O.append(uv_fit(box((0.2, 0.1, 0.002), (0.18, 1.33, -0.024), decal, rot=(0, 0, -0.08)), D.rect(80, 0, 48, 24)))
    O.append(uv_fit(box((0.14, 0.14, 0.002), (0.24, 1.12, -0.024), decal, rot=(0, 0, 0.15)), D.rect(80, 24, 24, 24)))
    O.append(uv_fit(box((0.34, 0.21, 0.004), (0.04, 0.72, -0.0245), decal, rot=(0, 0, -0.05)), D.rect(0, 64, 64, 40)))
    O.append(uv_fit(box((0.22, 0.22, 0.054), (0.08, 0.2, 0), decal), D.rect(0, 32, 32, 32)))
    for y in (0.3, 1.0, 1.75): O.append(cyl(0.012, 0.09, (0.428, y, -0.024), chrome, axis='y', seg=4))
    O.append(uv_fit(box((0.39, 0.19, 0.19), (0.05, 0.095, -0.2), decal, rot=(0, 0.06, 0)), D.rect(32, 32, 32, 32)))
    for o in O:
        if o.data.materials and o.data.materials[0] == chrome: uv_tile(o, 0.2)
    L = [uv_fit(box((0.07, 2.1, 0.12), (0.465, 1.05, 0), woodm), W.rect(0, 16, 64, 16)), uv_fit(box((0.075, 2.08, 0.11), (-0.4625, 1.04, 0.005), woodm), W.rect(0, 0, 64, 16)),
         uv_fit(box((1.02, 0.075, 0.125), (0, 2.065, 0), woodm), W.rect(0, 32, 64, 16)), uv_fit(box((0.85, 1.98, 0.044), (-0.005, 1.035, 0), paint), P.rect(0, 0, 32, 64)),
         uv_fit(box((0.34, 0.21, 0.052), (0.04, 0.72, 0)), D.rect(0, 64, 64, 40))]
    L[-1].data.materials.append(decal)
    return O, {'_lod': L, 'paint': ['dr_paint'], 'doorway': [1.0, 2.1]}


# ------------------------------------------------------------------------------------------------ shuttered window
def build_shutter():
    paint = mat('sh_paint', 0xffffff, rough=0.35, clearcoat=0.5, tex=tex_noise('sh_paint_t', 0xf2efe8, var=0.06, size=16, seed=60, speck=0xb8a890, speck_p=0.06))
    corr = Atlas('sh_metal_t', 32)
    for y in range(32): corr.px[y] = hexrgb(0xb8c0c8) * (0.75 + 0.25 * math.cos(y / 32 * 8 * 2 * math.pi))
    grime(corr.px, 0x8a6a4a, 0.1, seed=4, blob=4)
    metal = mat('sh_metal', 0xffffff, rough=0.3, metal=0.8, tex=corr.image())
    glass = mat('sh_glass', 0x9fd8e8, rough=0.05, metal=0.1, alpha=0.38)
    K = Atlas('sh_kit_t', 128)
    tiedye(K.sub(0, 0, 64, 64), [0xff6fae, 0xffe14d, 0xb48cff], seed=22, arms=2, twist=12)
    fb = K.sub(64, 0, 64, 24); wood(fb, 0xffb3c7, 0xe08aa8, seed=8, rings=3); write(fb, 'do not eat', 3, 8, 1, 0x7a1a3a, wob=1, seed=2, bold=True)
    soil = K.fill(64, 24, 16, 16, 0x4a3020); leaf = K.fill(80, 24, 16, 16, 0x4ac060); stem = K.fill(96, 24, 16, 16, 0x2a8a3a)
    fls = [K.fill(64 + k * 16, 40, 16, 16, c) for k, c in enumerate((0xff4fd8, 0xffe14d, 0xffffff, 0x4fd8ff))]
    strap = K.fill(112, 24, 16, 16, 0xffe14d)
    kit = mat('sh_kit', 0xffffff, rough=0.7, tex=K.image())
    O = []
    O.append(box((1.5, 0.06, 0.2), (0, 0.03, -0.04), paint, bev=0.01, seg=1))
    for s_ in (-1, 1): O.append(box((0.07, 0.94, 0.12), (s_ * 0.715, 0.53, 0), paint))
    O.append(box((1.5, 0.06, 0.12), (0, 1.03, 0), paint))
    O.append(box((0.04, 0.94, 0.06), (0, 0.53, 0), paint))
    O.append(box((1.37, 0.94, 0.006), (0, 0.53, 0.0), glass))
    for s_ in (-1, 1):  # curtains pulled to the sides inside
        xs = [s_ * (0.66 - k * 0.09) for k in range(4)]
        rows = []
        for j in range(3):
            y = 0.98 - j * 0.4; rows.append([(x - s_ * (0.08 if j == 1 else 0.0) * (k / 3), y, 0.05 + 0.015 * math.sin(k * 2.4)) for k, x in enumerate(xs)])
        c = sheet_grid(rows, kit, 'curtain'); face_toward(c, (0, 0, -1)); O.append(uv_fit(c, K.rect(0, 0, 64, 64), mode='front'))
    O.append(cyl(0.085, 1.44, (0, 1.145, -0.1), metal, axis='x', seg=8, cap=False))
    for s_ in (-1, 1):
        O.append(box((0.02, 0.2, 0.2), (s_ * 0.73, 1.13, -0.08), metal))
        O.append(box((0.035, 0.94, 0.04), (s_ * 0.68, 0.53, -0.08), metal))
    rows = []
    for j in range(3):
        y = 1.07 - j * 0.07; rows.append([(-0.67 + 1.34 * i, y, -0.08 - 0.006 * (j % 2)) for i in range(2)])
    sh = sheet_grid(rows, metal, 'slats'); face_toward(sh, (0, 0, -1)); O.append(uv_fit(sh, (0, 0, 1, 1), mode='front'))
    O.append(box((1.34, 0.025, 0.03), (0, 0.9, -0.08), metal))
    for s_ in (-1, 1): O.append(box((0.03, 0.03, 0.26), (s_ * 0.5, -0.12, -0.18), metal))
    O.append(uv_fit(box((1.3, 0.17, 0.17), (0, -0.02, -0.235), kit), K.rect(64, 0, 64, 24)))
    O.append(uv_fit(box((1.26, 0.02, 0.14), (0, 0.058, -0.235), kit), soil))
    rnd = random.Random(5)
    for k in range(2):
        x = -0.3 + k * 0.62
        O.append(uv_fit(ball(0.1, (x, 0.08, -0.235), kit, scale=(1.5, 0.7, 0.85), seg=5, rings=3), leaf))
    for k in range(4):
        x = -0.48 + k * 0.32 + rnd.uniform(-0.03, 0.03); h = rnd.uniform(0.2, 0.32); z = -0.235 + rnd.uniform(-0.04, 0.04)
        droop = k == 2
        top = (x + (0.06 if droop else rnd.uniform(-0.03, 0.03)), 0.06 + h * (0.75 if droop else 1), z - 0.02)
        O.append(uv_fit(rod((x, 0.05, z), top, 0.006, kit, seg=3), stem))
        O.append(uv_fit(cyl(0.045, 0.012, (top[0], top[1] + 0.005, top[2]), kit, axis='z', seg=5, rot=((1.6 if droop else -0.45), 0, rnd.uniform(0, 1))), fls[k % 4]))
    for o in O:
        if o.data.materials and o.data.materials[0] in (paint, glass): uv_tile(o, 0.3)
        elif o.data.materials and o.data.materials[0] == metal and o.name not in ('slats',): uv_tile(o, 0.12)
    L = [box((1.5, 0.06, 0.2), (0, 0.03, -0.04), paint), box((1.5, 0.06, 0.12), (0, 1.03, 0), paint), box((1.37, 0.94, 0.006), (0, 0.53, 0.0), glass),
         cyl(0.085, 1.44, (0, 1.145, -0.1), metal, axis='x', seg=6, cap=False)]
    for s_ in (-1, 1): L.append(box((0.07, 0.94, 0.12), (s_ * 0.715, 0.53, 0), paint))
    for o in L: uv_tile(o, 0.3)
    L.append(uv_fit(box((1.3, 0.17, 0.17), (0, -0.02, -0.235), kit), K.rect(64, 0, 64, 24)))
    L.append(uv_fit(box((1.1, 0.14, 0.1), (0, 0.13, -0.235), kit), leaf))
    return O, {'_lod': L, 'paint': ['sh_paint'], 'window': [1.5, 1.2], 'note': 'y = 0 is the underside of the sill; the flower box hangs below it'}


# ------------------------------------------------------------------------------------------------ soup crate
def build_crate_soup():
    W = Atlas('cs_wood_t', 64)
    wood(W.sub(0, 0, 64, 32), 0xd8b070, 0x9a6a30, seed=9, rings=4)
    en = W.sub(0, 32, 64, 32); wood(en, 0xd0a868, 0x9a6a30, seed=10, rings=3)
    en[3:9, 22:42] = hexrgb(0x3a2410)
    write(en, 'RATIONS', 11, 14, 1, 0x5a2a10); smiley(en, 32, 26, 4, face=0xd0a868, ink=0x5a2a10)
    woodm = mat('cs_wood', 0xffffff, rough=0.6, clearcoat=0.2, tex=W.image())
    C = Atlas('cs_can_t', 128)
    lab = C.sub(0, 0, 128, 40); lab[:] = hexrgb(0xfff8ee); lab[0:6] = hexrgb(0xe02a3a); lab[34:40] = hexrgb(0xe02a3a)
    lab[6:8] = lab[32:34] = hexrgb(0xd8b04a)
    for h in (0, 64):
        write(lab, 'SOUP', h + 8, 12, 2, 0xe02a3a, bold=True)
        write(lab, 'GRISTLE', h + 9, 26, 1, 0x5a2a20)
        px_disc(lab, h + 52, 22, 6, 0xffb43a); px_disc(lab, h + 52, 20, 6.2, 0xfff8ee, r_in=0, a0=-1.6, a1=1.6)
    lid = C.sub(0, 40, 32, 32); lid[:] = hexrgb(0xc8ccd4); px_disc(lid, 16, 16, 15, 0x9aa0aa, r_in=13); px_disc(lid, 16, 16, 9, 0xb4bac4, r_in=8)
    sg = C.sub(32, 40, 96, 64); crust(sg, 0xc8995a, 0.06, seed=11); grime(sg, 0x8a6a3a, 0.08, seed=3, blob=4)
    write(sg, 'soup', 22, 6, 3, 0xc0182a, wob=2, seed=1, bold=True)
    write(sg, '2 coupons', 2, 36, 2, 0x1a1a20, wob=1, seed=3)
    px_line(sg, 4, 56, 90, 54, 0xc0182a, 1.5)
    canm = mat('cs_can', 0xffffff, rough=0.3, metal=0.15, clearcoat=0.5, tex=C.image())
    O = []
    G = W.rect(0, 0, 64, 32); E = W.rect(0, 32, 64, 32)
    for s in (-1, 1):
        O.append(uv_fit(box((0.02, 0.16, 0.36), (s * 0.25, 0.08, 0), woodm, bev=0.004, seg=1), E))
        for y in (0.035, 0.12):
            O.append(uv_fit(box((0.49, 0.065, 0.012), (0, y, s * 0.174), woodm, rot=(0, 0, 0.006 * s)), G))
    O.append(uv_fit(box((0.48, 0.012, 0.34), (0, 0.006, 0), woodm), G))
    LR = C.rect(0, 0, 128, 40); LD = C.rect(0, 40, 32, 32)
    def can(x, y, z, turn=0.0, lie=None, seg=10):
        o = cyl(0.074, 0.18, (x, y, z), canm, axis='y', seg=seg)
        apply_mods(o)
        uv_can(o, x, z, y - 0.09, y + 0.09, LR, LD, turn=turn)
        if lie is not None: xform([o], rot=lie, pivot=(x, y, z))
        return o
    rnd = random.Random(3)
    for x in (-0.155, 0.0, 0.155):
        for z in (-0.08, 0.08): O.append(can(x, 0.102, z, rnd.uniform(0, 6), seg=8))
    O.append(can(-0.08, 0.283, 0.0, 1.0)); O.append(can(0.075, 0.283, 0.01, 2.0))
    O.append(can(-0.004, 0.464, 0.004, 4.0))
    O.append(can(0.34, 0.074, -0.3, 0.5, lie=(0, 0.6, math.pi / 2)))
    O.append(uv_fit(box((0.42, 0.28, 0.006), (-0.02, 0.135, -0.215), canm, rot=(0.24, 0.03, 0.02)), C.rect(32, 40, 96, 64)))
    return O, {'sign': 'soup 2 coupons'}


BUILDERS = [
    ('laundry_a', build_laundry('a')), ('laundry_b', build_laundry('b')), ('wokdish', build_wokdish), ('pchair', build_pchair),
    ('sofa', build_sofa), ('fridge', build_fridge), ('scooter', build_scooter), ('acunit', build_acunit),
    ('smilesign', build_smilesign), ('stringlights', build_stringlights), ('tarp', build_tarp), ('door_bottom', build_door_bottom),
    ('shutter', build_shutter), ('crate_soup', build_crate_soup),
]

run(BUILDERS)
