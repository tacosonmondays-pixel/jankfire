# ZOMBIES (the co-op mode's horde): the game's mannequin gone rotten, in Blender. one glb per kind, each built as
# separate body parts named part_<joint> with its origin ON the joint of the multiplayer mannequin (models.js
# buildCharacter: body, head, arm, armL, legL, legR, kneeL, kneeR), so the game drops every part into the same joint
# group: loco.js still walks it and a limb still comes off as one piece (public/js/zmlimbs.js). every limb is closed
# with the mannequin's joint peg where it pops off (owner: no gore, keep it a clean mannequin). skin / top / bottom are their own materials (z_skin*, z_top, z_bot) the
# game tints per zombie (meta.tint = the colour each was painted here). a missing file = the code mannequin.
#   z_plain    the shambler: the blank egg-headed mannequin, ball joints, a faded t-shirt, the price tag still on
#   z_chonk    huge belly full of something purple, shirt three sizes too small
#   z_biter    ANKLE BITER: toddler-sized, all mouth, a bib that says BITE, a nappy with a safety pin
#   z_hardhat  hi-vis vest, tool belt, work boots; the hat is its own node (part_hat) so it can fly off
#   z_screamer long and thin, jaw down to its chest (part_jaw swings), stringy hair
#   z_stump    the empty socket left on the body where a limb popped off
# blender52 -b --python tools/blender/make_zombies.py [-- --no-sheet] [--only=chonk]
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cast'))
from castlib import *  # noqa (blob, limb, cloth, rubber, skin_tex, path, panel + everything in lib.py)

SKIN, TOP, BOT = 0x7f9f4a, 0x5a4a3a, 0x3a3a44  # what the tintable materials are painted (the game multiplies from these)
JT = {'body': (0, 0, 0), 'head': (0, 1.62, 0), 'arm': (0.25, 1.45, 0), 'armL': (-0.25, 1.45, 0), 'legL': (-0.1, 0.92, 0),
      'legR': (0.1, 0.92, 0), 'kneeL': (-0.1, 0.48, 0), 'kneeR': (0.1, 0.48, 0)}


class Mats:
    def __init__(self):
        self.skin = rubber('z_skin', SKIN, tex_noise('z_skinT', SKIN, 0.05, 32, seed=11), rough=0.3)
        self.joint = rubber('z_skin_joint', 0x5f7c36, tex_noise('z_jointT', 0x5f7c36, 0.05, 16, seed=12), rough=0.28)
        self.pale = rubber('z_skin_pale', 0x9db86a, skin_tex('z_paleT', 0x9db86a, 0x6f8f42, 32, seed=13, p=0.06), rough=0.4)
        self.top = cloth('z_top', TOP, tex_noise('z_topT', TOP, 0.1, 32, seed=14))
        self.bot = cloth('z_bot', BOT, tex_noise('z_botT', BOT, 0.1, 32, seed=15))
        self.meat = mat('z_meat', 0x9a1010, rough=0.25, clearcoat=0.8, tex=tex_noise('z_meatT', 0x9a1010, 0.25, 32, speck=0x4a0408, speck_p=0.18, seed=16))
        self.gore = mat('z_gore', 0x5a0408, rough=0.3, clearcoat=0.6)
        self.bone = mat('z_bone', 0xe8e0c8, rough=0.45, tex=tex_noise('z_boneT', 0xe8e0c8, 0.06, 16, speck=0xb8a880, speck_p=0.08, seed=17))
        self.dark = mat('z_dark', 0x120a10, rough=0.9)
        self.brain = mat('z_brain', 0xd98a9a, rough=0.2, clearcoat=0.9, tex=tex_noise('z_brainT', 0xd98a9a, 0.12, 32, speck=0xa85a70, speck_p=0.2, seed=18))
        self.eye = mat('z_eye', 0xe8ff5a, emit=0xd8ff4f, strength=2.2)
        self.tooth = mat('z_tooth', 0xf0e8c0, rough=0.3, clearcoat=0.5)
        self.gold = mat('z_gold', 0xe0b040, rough=0.25, metal=1.0)
        self.nail = mat('z_nail', 0x2a2a1a, rough=0.4)
        self.hair = mat('z_hair', 0x1c1a16, rough=0.7)
        self.chrome = mat('z_chrome', 0xc8ccd4, rough=0.18, metal=1.0)
        self.white = mat('z_white', 0xf4f2ea, rough=0.6, tex=tex_noise('z_whiteT', 0xf4f2ea, 0.05, 16, seed=19))
        self.shoe = mat('z_shoe', 0x2a2420, rough=0.5, tex=tex_noise('z_shoeT', 0x2a2420, 0.2, 16, seed=20))
        self.sole = mat('z_sole', 0x15120f, rough=0.85)


def place(jn, objs, at=None, name=None):
    """objs were modelled in the joint's own frame: carry them onto the joint and make one node with its origin there"""
    p = at or JT[jn]
    T = Matrix.Translation(gv(*p))
    out = []
    for o in objs:
        if o is None: continue
        apply_mods(o)
        o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)
        o.data.transform(T)
        if not o.get('keep_uv'): uv_box(o, 0.14)
        out.append(o)
    return part(out, name or 'part_' + jn, pivot=p)


def cap(M, r, at=(0, 0, 0), axis='y', sgn=1, k=1.0):
    """where a limb pops off: the mannequin's own joint peg (a flat plate and a plug), facing +axis * sgn"""
    d = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1)}[axis]
    v = lambda t: (at[0] + d[0] * t * sgn, at[1] + d[1] * t * sgn, at[2] + d[2] * t * sgn)
    return [rod(v(-0.01), v(0.012 * k), r * 0.92, M.joint, seg=10), rod(v(0.01 * k), v(0.05 * k), r * 0.36, M.chrome, seg=8, r1=r * 0.3)]


def hand(M, z, sx, k=1.0, long=1.0, claw=True):
    """a mitt at arm-local z with three spread fingers and a thumb, nails dark. fingers reach forward (-z), curled down"""
    out = [blob('wrist', (0, 0, z + 0.01), (0.032 * k, 0.032 * k, 0.032 * k), M.joint, seg=10, rings=6),
           blob('mitt', (0, -0.004, z - 0.05 * k), (0.043 * k, 0.022 * k, 0.05 * k), M.skin, seg=12, rings=8)]
    for i, fx in enumerate((-0.03, 0.0, 0.03)):
        L = (0.075 + (0.012 if i == 1 else 0)) * k * long
        a, b, c = (fx * k, -0.004, z - 0.085 * k), (fx * 1.5 * k, -0.012 * k, z - 0.085 * k - L * 0.6), (fx * 1.7 * k, -0.045 * k, z - 0.085 * k - L)
        out.append(limb('finger%d' % i, [a, b, c], [0.013 * k, 0.012 * k, 0.009 * k], M.skin, seg=6))
        if claw: out.append(rod(c, (c[0], c[1] - 0.022 * k, c[2] - 0.012 * k), 0.008 * k, M.nail, seg=5, r1=0.001))
    t0 = (-sx * 0.04 * k, -0.005, z - 0.03 * k); t1 = (-sx * 0.07 * k, -0.02 * k, z - 0.075 * k)
    out.append(limb('thumb', [t0, t1], [0.014 * k, 0.01 * k], M.skin, seg=6))
    return out


def arm(M, sx, fat=1.0, long=1.0, sleeve=0.13, bone_gap=False, tag=False, sleeve_m=None):
    """arm-local: the shoulder at the origin, reaching forward along -z (arms out, like every zombie)"""
    L1, L2 = 0.29 * long, 0.26 * long
    out = cap(M, 0.05 * fat, (0, 0, 0.0), 'z', 1, k=0.45)  # (short: it hides inside the shoulder socket until the arm's off)
    out.append(limb('upper', [(0, 0, 0.0), (0, -0.004, -L1 * 0.5), (0, -0.012, -L1)], [0.052 * fat, 0.05 * fat, 0.044 * fat], M.skin, seg=10))
    if sleeve:  # what's left of the sleeve, ragged at the end
        sm = sleeve_m or M.top
        out.append(limb('sleeve', [(0, 0, -0.005), (0, -0.003, -sleeve * 0.6), (0, -0.006, -sleeve)], [0.064 * fat, 0.062 * fat, 0.066 * fat], sm, seg=10))
        for i in range(5):
            a = i * 1.257 + sx
            out.append(box((0.03 * fat, 0.004, 0.05), (math.cos(a) * 0.062 * fat, math.sin(a) * 0.062 * fat - 0.006, -sleeve - 0.018), sm, rot=(0.25 * math.sin(a), 0, a + 1.57)))
    out.append(blob('elbow', (0, -0.012, -L1), (0.048 * fat,) * 3, M.joint, seg=10, rings=6))
    e = (0, -0.012, -L1); w = (0, -0.05, -L1 - L2)
    if bone_gap:  # the forearm's worn through: two bones between the elbow and what's left
        out.append(limb('fore_a', [e, lerp3(e, w, 0.28)], [0.044 * fat, 0.04 * fat], M.skin, seg=10))
        m0, m1 = lerp3(e, w, 0.24), lerp3(e, w, 0.66)
        out.append(rod((m0[0] - 0.012, m0[1], m0[2]), (m1[0] - 0.012, m1[1], m1[2]), 0.011, M.bone, seg=6))
        out.append(rod((m0[0] + 0.014, m0[1] + 0.004, m0[2]), (m1[0] + 0.014, m1[1] + 0.004, m1[2]), 0.008, M.bone, seg=6))
        out.append(blob('frag', lerp3(e, w, 0.3), (0.036, 0.036, 0.014), M.meat, seg=8, rings=5))
        out.append(blob('frag2', lerp3(e, w, 0.64), (0.034, 0.034, 0.014), M.meat, seg=8, rings=5))
        out.append(limb('fore_b', [lerp3(e, w, 0.62), w], [0.036 * fat, 0.034 * fat], M.skin, seg=10))
    else:
        out.append(limb('fore', [e, lerp3(e, w, 0.5), w], [0.044 * fat, 0.042 * fat, 0.034 * fat], M.skin, seg=10))
    hd = hand(M, 0, sx, k=fat ** 0.5, long=long ** 0.5)
    for o in hd:  # the hand hangs off the wrist, tipped down a bit
        o.data.transform(Matrix.Rotation(0.18, 4, 'X')); o.data.transform(Matrix.Translation(gv(w[0], w[1] - 0.004, w[2] - 0.012)))
    out += hd
    if tag:  # the price tag is still on (it's the mannequin's)
        tagM = mat('z_tag', 0xffffff, rough=0.5, tex=tex_canvas('z_tagT', 16, 16, lambda px: (px.__setitem__(slice(None), hexrgb(0xffffff)), text_px(px, '99', 2, 5, 1, 0xff3030))))
        out.append(tube([(0.03, w[1], w[2] + 0.02), (0.05, w[1] - 0.03, w[2] + 0.03), (0.055, w[1] - 0.06, w[2] + 0.035)], 0.002, M.bone))
        t = box((0.004, 0.06, 0.045), (0.056, w[1] - 0.09, w[2] + 0.035), tagM, rot=(0.3, 0.2, 0.1)); out.append(t)
    return out


def thigh(M, sx, fat=1.0, trouser=0.3, ragged=True, bm=None):
    bm = bm or M.bot
    out = cap(M, 0.07 * fat, (0, 0.0, 0), 'y', 1)
    out.append(limb('thigh', [(0, 0, 0), (0, -0.22, -0.004), (0, -0.44, 0)], [0.086 * fat, 0.08 * fat, 0.064 * fat], M.skin, seg=10))
    if trouser:
        out.append(limb('trouser', [(0, 0.0, 0), (0, -trouser * 0.5, -0.003), (0, -trouser, -0.002)], [0.097 * fat, 0.093 * fat, 0.09 * fat], bm, seg=10))
        if ragged:
            for i in range(6):
                a = i * 1.047 + sx * 0.4
                out.append(box((0.04 * fat, 0.06 + 0.02 * (i % 2), 0.005), (math.cos(a) * 0.086 * fat, -trouser - 0.022, math.sin(a) * 0.086 * fat), bm, rot=(0, -a + 1.57, 0)))
    return out


def shin(M, sx, fat=1.0, cuff=False, shoe=True, boot=None, bm=None):
    bm = bm or M.bot
    out = [blob('knee', (0, 0, 0), (0.062 * fat,) * 3, M.joint, seg=10, rings=6),
           limb('shin', [(0, 0, 0), (0, -0.18, 0.004), (0, -0.37, 0)], [0.058 * fat, 0.054 * fat, 0.04 * fat], M.skin, seg=10)]
    if cuff: out.append(limb('cuff', [(0, 0.02, 0), (0, -0.14, 0.003), (0, -0.27, 0.002)], [0.07 * fat, 0.066 * fat, 0.07 * fat], bm, seg=10))
    if boot is not None:  # work boot: tall, a toe cap, a thick sole, laces
        out.append(limb('bootleg', [(0, -0.2, 0), (0, -0.4, 0)], [0.062 * fat, 0.066 * fat], boot, seg=10))
        out.append(blob('boot', (0, -0.405, -0.055), (0.066 * fat, 0.05, 0.13), boot, seg=12, rings=8, fn=lambda p, n: 0.012 * max(0, -p.z / 0.13)))
        out.append(blob('toecap', (0, -0.4, -0.15), (0.058 * fat, 0.042, 0.05), mat('z_toecap', 0x8a6a2a, rough=0.3, clearcoat=0.5), seg=10, rings=6))
        out.append(box((0.14 * fat, 0.03, 0.29), (0, -0.455, -0.055), M.sole, bev=0.008))
        for i in range(3): out.append(rod((-0.03, -0.3 - i * 0.035, -0.064), (0.03, -0.3 - i * 0.035, -0.064), 0.005, mat('z_lace', 0xffe14d, rough=0.6), seg=5))
    elif shoe:
        out.append(blob('shoe', (0, -0.415, -0.05), (0.058 * fat, 0.042, 0.125), M.shoe, seg=12, rings=8, fn=lambda p, n: 0.01 * max(0, -p.z / 0.125)))
        out.append(box((0.118 * fat, 0.02, 0.26), (0, -0.458, -0.05), M.sole, bev=0.005))
    else:  # a bare foot, toes and all
        out.append(blob('ankle', (0, -0.38, 0), (0.04 * fat,) * 3, M.joint, seg=8, rings=6))
        out.append(blob('foot', (0, -0.435, -0.055), (0.052 * fat, 0.032, 0.115), M.skin, seg=12, rings=8))
        for i, tx in enumerate((-0.034, -0.012, 0.01, 0.03)):
            out.append(blob('toe%d' % i, (tx * fat, -0.445, -0.168 + abs(tx) * 0.5), (0.013 * fat, 0.013, 0.02), M.skin, seg=6, rings=5))
            out.append(blob('toenail%d' % i, (tx * fat, -0.436, -0.18 + abs(tx) * 0.5), (0.008, 0.005, 0.008), M.nail, seg=6, rings=4))
    return out


def teeth(M, y, z, n, w, up, k=1.0, gold=-1, gap=()):
    out = []
    for i in range(n):
        if i in gap: continue
        x = (i - (n - 1) / 2) * w / max(1, n - 1)
        zz = z + abs(x) * 0.35
        out.append(rod((x, y, zz), (x, y + up * 0.024 * k, zz - 0.003), 0.0085 * k, M.gold if i == gold else M.tooth, seg=5, r1=0.004 * k))
    return out


def head(M, kind='plain'):
    """head-local (the joint is the base of the neck): the mannequin's blank egg with its mould seam. only the ones
    whose whole job is a mouth get one"""
    big = kind == 'biter'
    k = 1.5 if big else 0.95 if kind == 'chonk' else 1.0
    cy = 0.155 * k; R = (0.126 * k, 0.18 * k, 0.142 * k)
    out = [blob('egg', (0, cy, 0), R, M.skin, seg=20, rings=14)]
    seam = [(0.0, cy + math.cos(a) * R[1] * 1.003, math.sin(a) * R[2] * 1.003) for a in [math.radians(d) for d in range(-150, 151, 15)]]
    out.append(tube(seam, 0.0042 * k, M.joint, seg=5))  # the mould seam, front to back over the top
    out.append(blob('neckball', (0, -0.012, 0), (0.052 * (1.1 if big else 1),) * 3, M.joint, seg=10, rings=8))
    ez = -R[2] * 0.86; ey = cy + 0.05 * k
    if kind == 'screamer':  # two wide glowing eyes
        pink = mat('z_eye_pink', 0xff7ae4, emit=0xff4fd8, strength=3.0)
        for sx in (-1, 1): out.append(blob('eye', (sx * 0.05, ey + 0.012, ez - 0.004), (0.024, 0.03, 0.012), pink, seg=10, rings=6))
        return out  # (its mouth is the jaw's job)
    if big:  # ANKLE BITER: all mouth. a neat cartoon grin, two rows
        my = cy - 0.07 * k; mz = -R[2] * 0.86; mw = 0.094 * k
        out.append(blob('mouth', (0, my, mz + 0.012 * k), (mw, 0.05 * k, 0.034 * k), M.dark, seg=14, rings=8))
        out += teeth(M, my + 0.036 * k, mz - 0.02 * k, 9, mw * 1.7, -1, k * 1.25)
        out += teeth(M, my - 0.04 * k, mz - 0.022 * k, 8, mw * 1.55, 1, k * 1.25)
    return out


def torso(M, kind='plain'):
    """body-local = root space: hips, waist, chest, neck, the shoulder sockets"""
    out = []
    thin = kind == 'screamer'
    w = 0.8 if thin else 1.0
    out.append(blob('hips', (0, 0.95, 0), (0.172 * w, 0.105, 0.125 * w), M.bot, seg=16, rings=10))
    out.append(limb('waist', [(0, 1.0, 0), (0, 1.1, 0.004), (0, 1.2, 0)], [0.125 * w, 0.108 * w, 0.13 * w], M.skin, seg=12))
    chest = blob('chest', (0, 1.34, 0), (0.238 * w, 0.215, 0.148 * w), M.skin, seg=16, rings=12, fn=lambda p, n: -0.012 * abs(math.sin(p.y * 38)) if (p.y < 0.02 and abs(n.x) > 0.3) else 0)
    out.append(chest)
    for sx in (-1, 1): out.append(blob('socket', (sx * 0.25, 1.45, 0), (0.07,) * 3, M.joint, seg=12, rings=8))
    out.append(limb('neck', [(0, 1.5, 0), (0, 1.62, 0)], [0.058, 0.046], M.skin, seg=10))
    if kind in ('plain', 'hardhat', 'screamer'):  # a faded t-shirt, short at the hem
        shirt = blob('shirt', (0, 1.335, 0), (0.25 * w, 0.228, 0.16 * w), M.top, seg=16, rings=12)
        cut(shirt, box((0.7, 0.2, 0.5), (0, 1.07, 0), None, rot=(0, 0, -0.06)))
        cut(shirt, box((0.14, 0.1, 0.4), (0.0, 1.57, 0), None))  # the neck hole
        out.append(shirt)
    # the waistband, and a bit of belt
    out.append(limb('band', [(0, 1.0, 0), (0, 1.035, 0)], [0.168 * w, 0.158 * w], M.bot, seg=14, squash=(0.74, 1.0)))
    return out


def stump(M):
    """the end left on the body: the empty socket the peg sat in, a little red round the rim. pointing +y from the origin"""
    return [lathe([(0.03, 0.0), (0.062, 0.004), (0.066, 0.02), (0.05, 0.03), (0.034, 0.026), (0.03, 0.004)], (0, 0, 0), M.joint, seg=12, axis='y'),
            lathe([(0.001, 0.006), (0.032, 0.008)], (0, 0, 0), M.dark, seg=10, axis='y'),
            lathe([(0.05, 0.03), (0.058, 0.034), (0.066, 0.022)], (0, 0, 0), M.meat, seg=12, axis='y')]


def std_limbs(M, P, fat=1.0, long=1.0, boots=None, kind='plain'):
    P['arm'] = place('arm', arm(M, 1, fat, long, tag=True, sleeve=0.13 if kind != 'screamer' else 0))
    P['armL'] = place('armL', arm(M, -1, fat, long, bone_gap=False, sleeve=0.05 if kind == 'plain' else 0.13 if kind == 'hardhat' else 0))
    P['legL'] = place('legL', thigh(M, -1, fat, trouser=0.2 if kind != 'hardhat' else 0.44, ragged=kind != 'hardhat'))
    P['legR'] = place('legR', thigh(M, 1, fat, trouser=0.44, ragged=False))
    P['kneeL'] = place('kneeL', shin(M, -1, fat, cuff=kind == 'hardhat', shoe=False, boot=boots))
    P['kneeR'] = place('kneeR', shin(M, 1, fat, cuff=True, shoe=True, boot=boots))


def finish_z(kind, P, meta=None):
    return finish('zombie_' + kind, list(P.values()), {'kind': 'zombie', 'id': kind, 'tint': {'z_skin': SKIN, 'z_top': TOP, 'z_bot': BOT}, **(meta or {})})


# ------------------------------------------------------------ the kinds
def build_plain(M):
    P = {'body': place('body', torso(M)), 'head': place('head', head(M))}
    std_limbs(M, P)
    return finish_z('plain', P)


def build_hardhat(M):
    vest = cloth('z_vest', 0xff7a1a, tex_noise('z_vestT', 0xff7a1a, 0.08, 32, speck=0xc85a10, speck_p=0.05, seed=31))
    refl = mat('z_reflect', 0xdfe6ea, rough=0.2, metal=0.6)
    leather = mat('z_leather', 0x6a4420, rough=0.5, tex=tex_noise('z_leatherT', 0x6a4420, 0.18, 16, seed=32))
    hatM = mat('z_hat', 0xffd21f, rough=0.2, clearcoat=0.9)
    boot = mat('z_boot', 0x8a5a26, rough=0.55, tex=tex_noise('z_bootT', 0x8a5a26, 0.2, 16, seed=33))
    body = torso(M, 'hardhat')
    # the hi-vis vest: open down the front, two silver stripes over the shoulders, one round the middle
    v = blob('vest', (0, 1.32, 0), (0.262, 0.215, 0.172), vest, seg=20, rings=14)
    cut(v, box((0.075, 0.6, 0.3), (0, 1.3, -0.14), None)); cut(v, box((0.16, 0.1, 0.5), (0, 1.56, 0), None)); cut(v, box((0.7, 0.2, 0.5), (0, 1.02, 0), None))
    for sx in (-1, 1): cut(v, blob('armhole', (sx * 0.27, 1.44, 0), (0.09, 0.1, 0.1), None))
    body.append(v)
    for sx in (-1, 1):
        st = blob('stripe', (sx * 0.125, 1.33, 0), (0.036, 0.222, 0.178), refl, seg=10, rings=14); cut(st, box((0.5, 0.2, 0.5), (0, 1.02, 0), None)); body.append(st)
    band = blob('vband', (0, 1.19, 0), (0.266, 0.03, 0.176), refl, seg=20, rings=6); cut(band, box((0.075, 0.2, 0.3), (0, 1.19, -0.14), None)); body.append(band)
    # tool belt: a pouch, a hammer in its loop, a tape measure
    body.append(limb('belt', [(0, 1.005, 0), (0, 1.05, 0)], [0.178, 0.176], leather, seg=16, squash=(0.74, 1.0)))
    body.append(box((0.05, 0.04, 0.012), (0, 1.028, -0.134), M.chrome, bev=0.004))
    body.append(box((0.1, 0.12, 0.05), (0.15, 0.95, -0.085), leather, bev=0.01, rot=(0, -0.5, 0)))
    body.append(rod((-0.19, 1.06, -0.03), (-0.2, 0.8, -0.02), 0.013, mat('z_wood', 0xb07a3a, rough=0.6), seg=7))  # hammer handle
    body.append(box((0.035, 0.035, 0.11), (-0.19, 1.085, -0.03), M.chrome, bev=0.006))
    body.append(lathe([(0.032, -0.014), (0.036, -0.012), (0.036, 0.012), (0.032, 0.014)], (-0.1, 0.96, -0.118), mat('z_tape', 0xffe14d, rough=0.3, clearcoat=0.6), seg=12, axis='z'))
    P = {'body': place('body', body), 'head': place('head', head(M, 'hardhat'))}
    std_limbs(M, P, boots=boot, kind='hardhat')
    # the hat: its own node (head-local origin at the crown line) so it can dink and fly
    stk = mat('z_hatsticker', 0xffffff, rough=0.4, tex=tex_canvas('z_hatstickerT', 32, 16, lambda px: (px.__setitem__(slice(None), hexrgb(0xffffff)), px.__setitem__((slice(0, 3),), hexrgb(0xff3030)), text_px(px, '0 DAYS', 1, 5, 1, 0x120818))))
    hat = [lathe([(0.001, 0.142), (0.06, 0.134), (0.11, 0.105), (0.143, 0.055), (0.152, 0.0), (0.156, -0.012)], (0, 0, 0), hatM, seg=20, axis='y')]
    hat[0].data.transform(Matrix.Diagonal((1.0, 1.14, 1.0, 1.0)))  # longer front to back (blender y = game -z)
    hat.append(lathe([(0.15, 0.0), (0.186, -0.012), (0.19, -0.02), (0.15, -0.02)], (0, 0, 0), hatM, seg=20, axis='y'))
    hat[1].data.transform(Matrix.Diagonal((1.0, 1.16, 1.0, 1.0)))
    hat.append(box((0.2, 0.012, 0.11), (0, -0.016, -0.2), hatM, bev=0.005, rot=(0.12, 0, 0)))  # the peak
    for x in (-0.05, 0, 0.05):  # the ribs over the crown
        pts = [(x, 0.006 + 0.142 * math.cos(a) * (1 - (x / 0.2) ** 2), math.sin(a) * 0.165) for a in [math.radians(d) for d in range(-78, 79, 13)]]
        hat.append(tube(pts, 0.011 if x == 0 else 0.008, hatM, seg=6))
    s = box((0.085, 0.045, 0.004), (0, 0.058, -0.155), stk, rot=(-0.5, 0, 0)); s['keep_uv'] = 1; uv_planar(s, centre(s), (0.085, 0.045), axis='z'); hat.append(s)
    hat.append(lathe([(0.02, 0.0), (0.026, -0.012), (0.026, -0.03), (0.02, -0.034)], (0.0, 0.03, -0.172), M.chrome, seg=10, axis='z'))  # a head torch
    hat.append(blob('lens', (0, 0.03, -0.208), (0.02, 0.02, 0.006), mat('z_torch', 0xfff2a0, emit=0xfff2a0, strength=2.5), seg=8, rings=4))
    P['hat'] = place('head', hat, at=(0, 1.62 + 0.262, 0), name='part_hat')
    return finish_z('hardhat', P, {'hat': [0, 0.262, 0]})


def build_chonk(M):
    boil = mat('z_boil', 0xc79bff, emit=0xb07dff, strength=1.6, rough=0.2, clearcoat=1.0)
    crop = cloth('z_top', TOP)
    body = [blob('hips', (0, 0.93, 0), (0.27, 0.13, 0.22), M.bot, seg=18, rings=10)]
    # the belly: most of it. it sags, the button's an outie, stretch marks down the sides
    belly = blob('belly', (0, 1.12, -0.07), (0.4, 0.33, 0.39), M.skin, seg=28, rings=20,
                 fn=lambda p, n: 0.03 * max(0, -n.y) * max(0, -n.z))
    body.append(belly)
    body.append(blob('button', (0, 1.06, -0.458), (0.03, 0.03, 0.022), M.pale, seg=8, rings=6))
    body.append(blob('chest', (0, 1.42, 0.0), (0.33, 0.17, 0.22), M.skin, seg=20, rings=12))
    for sx in (-1, 1):
        body.append(blob('socket', (sx * 0.31, 1.45, 0), (0.085,) * 3, M.joint, seg=12, rings=8))
        body.append(blob('roll', (sx * 0.3, 1.16, 0.04), (0.14, 0.09, 0.2), M.skin, seg=12, rings=8))  # love handles
    body.append(limb('neck', [(0, 1.5, 0), (0, 1.62, 0)], [0.1, 0.085], M.skin, seg=12))
    body.append(blob('chin2', (0, 1.6, -0.06), (0.1, 0.045, 0.085), M.skin, seg=12, rings=6))  # the second chin
    # the shirt: three sizes too small, ridden right up, one button holding on
    sh = blob('shirt', (0, 1.44, 0), (0.345, 0.16, 0.235), M.top, seg=22, rings=12)
    cut(sh, box((0.9, 0.3, 0.9), (0, 1.2, 0), None, rot=(0.12, 0, 0.05))); cut(sh, box((0.24, 0.1, 0.5), (0, 1.6, 0), None))
    body.append(sh)
    body.append(blob('shirtbtn', (0, 1.375, -0.232), (0.014, 0.014, 0.006), M.white, seg=8, rings=4))
    for (x, y, z, r) in ((0.21, 1.3, -0.33, 0.06), (-0.22, 1.0, -0.33, 0.05), (-0.33, 1.22, -0.12, 0.055), (0.05, 1.2, 0.3, 0.06)):
        body.append(blob('boil', (x, y, z), (r, r, r * 0.8), boil, seg=10, rings=7))  # it's full of something purple
    body.append(limb('band', [(0, 0.99, 0), (0, 1.03, 0)], [0.3, 0.29], M.bot, seg=16, squash=(0.8, 1.0)))
    J2 = dict(JT, arm=(0.31, 1.45, 0), armL=(-0.31, 1.45, 0), legL=(-0.17, 0.92, 0), legR=(0.17, 0.92, 0), kneeL=(-0.17, 0.48, 0), kneeR=(0.17, 0.48, 0))
    P = {'body': place('body', body), 'head': place('head', head(M, 'chonk'))}
    P['arm'] = place('arm', arm(M, 1, 1.75, 0.9, tag=True, sleeve=0.1), at=J2['arm'])
    P['armL'] = place('armL', arm(M, -1, 1.75, 0.9, sleeve=0.1), at=J2['armL'])
    P['legL'] = place('legL', thigh(M, -1, 1.7, trouser=0.3), at=J2['legL'])
    P['legR'] = place('legR', thigh(M, 1, 1.7, trouser=0.36), at=J2['legR'])
    P['kneeL'] = place('kneeL', shin(M, -1, 1.6, shoe=False), at=J2['kneeL'])
    P['kneeR'] = place('kneeR', shin(M, 1, 1.6, shoe=False), at=J2['kneeR'])
    return finish_z('chonk', P, {'joints': {k: list(v) for k, v in J2.items() if v != JT[k]}})


def build_biter(M):
    bibM = mat('z_bib', 0xffffff, rough=0.6, tex=tex_canvas('z_bibT', 32, 32, lambda px: (px.__setitem__(slice(None), hexrgb(0xf4f2ea)), px.__setitem__((slice(0, 2),), hexrgb(0xff4fd8)), px.__setitem__((slice(30, 32),), hexrgb(0xff4fd8)),
                                                                                         text_px(px, 'BITE', 5, 9, 1, 0xff3030))))
    body = [blob('nappy', (0, 0.95, 0), (0.2, 0.13, 0.16), M.white, seg=16, rings=10, fn=lambda p, n: 0.012 * max(0, -n.y)),
            limb('waist', [(0, 1.02, 0), (0, 1.2, 0)], [0.15, 0.14], M.skin, seg=12),
            blob('tum', (0, 1.2, -0.04), (0.19, 0.17, 0.17), M.skin, seg=16, rings=10),  # a toddler's pot belly
            blob('chest', (0, 1.38, 0), (0.2, 0.16, 0.14), M.skin, seg=16, rings=10),
            limb('neck', [(0, 1.5, 0), (0, 1.62, 0)], [0.07, 0.065], M.skin, seg=10)]
    for sx in (-1, 1): body.append(blob('socket', (sx * 0.25, 1.45, 0), (0.07,) * 3, M.joint, seg=12, rings=8))
    body.append(limb('pinbar', [(-0.19, 1.0, -0.06), (-0.2, 0.93, -0.085)], [0.006, 0.006], M.chrome, seg=5))  # the safety pin
    body.append(blob('pinhead', (-0.19, 1.005, -0.058), (0.016, 0.014, 0.012), mat('z_pin', 0x4fd8ff, rough=0.3, clearcoat=0.7), seg=8, rings=5))
    bib = panel('bib', 0.26, 0.24, (0, 1.39, -0.19), bibM, curve=0.07, nx=8, ny=6); body.append(bib)
    body.append(tube([(-0.11, 1.5, -0.13), (-0.09, 1.56, -0.03), (0, 1.58, 0.06), (0.09, 1.56, -0.03), (0.11, 1.5, -0.13)], 0.008, mat('z_bibtie', 0xff4fd8, rough=0.6), seg=5))
    P = {'body': place('body', body), 'head': place('head', head(M, 'biter'))}
    P['arm'] = place('arm', arm(M, 1, 1.15, 0.86, sleeve=0)); P['armL'] = place('armL', arm(M, -1, 1.15, 0.86, sleeve=0))
    P['legL'] = place('legL', thigh(M, -1, 1.15, trouser=0)); P['legR'] = place('legR', thigh(M, 1, 1.15, trouser=0))
    P['kneeL'] = place('kneeL', shin(M, -1, 1.15, shoe=False)); P['kneeR'] = place('kneeR', shin(M, 1, 1.15, shoe=False))
    return finish_z('biter', P)


def build_screamer(M):
    gown = cloth('z_top', TOP)
    body = torso(M, 'screamer')
    P = {'body': place('body', body)}
    hd = head(M, 'screamer')
    # the top of the mouth: a dark gape with the upper teeth round it, then long stringy hair
    cy = 0.155; mz = -0.142 * 0.86
    hd.append(blob('gape', (0, cy - 0.08, mz + 0.02), (0.07, 0.05, 0.04), M.dark, seg=14, rings=8))
    hd += teeth(M, cy - 0.045, mz - 0.012, 7, 0.115, -1, 1.15)
    for i in range(11):
        a = math.radians(-100 + i * 20) + math.pi; x0, z0 = math.sin(a) * 0.1, -math.cos(a) * 0.11
        L = 0.3 + 0.12 * ((i * 5) % 3)
        hd.append(limb('hair%d' % i, [(x0 * 0.7, cy + 0.15, z0 * 0.7), (x0 * 1.18, cy + 0.06, z0 * 1.2), (x0 * 1.3, cy - L * 0.5, z0 * 1.35 + 0.02), (x0 * 1.15 + 0.02 * math.sin(i), cy - L, z0 * 1.3 + 0.04)],
                       [0.012, 0.014, 0.011, 0.004], M.hair, seg=5, squash=(0.5, 1.0)))
    P['head'] = place('head', hd)
    # the jaw: its own node, hinged under the ears, hanging down to the chest (the game swings it wider when it shrieks)
    jy, jz = cy - 0.07, 0.02
    jaw = [limb('jawL', [(-0.095, 0, 0), (-0.085, -0.1, -0.07), (-0.04, -0.17, -0.125), (0, -0.185, -0.135)], [0.02, 0.022, 0.022, 0.024], M.skin, seg=7),
           limb('jawR', [(0.095, 0, 0), (0.085, -0.1, -0.07), (0.04, -0.17, -0.125), (0, -0.185, -0.135)], [0.02, 0.022, 0.022, 0.024], M.skin, seg=7),
           blob('chin', (0, -0.19, -0.12), (0.05, 0.035, 0.04), M.skin, seg=10, rings=6),
           blob('throat', (0, -0.09, -0.04), (0.075, 0.1, 0.06), M.dark, seg=12, rings=8)
           ]
    for i in range(6):
        t = i / 5; x = -0.07 + 0.14 * t; zz = -0.105 - 0.03 * math.sin(math.pi * t); yy = -0.135 - 0.04 * math.sin(math.pi * t)
        jaw.append(rod((x, yy, zz), (x, yy + 0.034, zz - 0.004), 0.009, M.tooth, seg=5, r1=0.003))
    P['jaw'] = place('head', jaw, at=(0, 1.62 + jy, jz), name='part_jaw')
    P['arm'] = place('arm', arm(M, 1, 0.8, 1.16, tag=True, sleeve=0)); P['armL'] = place('armL', arm(M, -1, 0.8, 1.16, sleeve=0))
    P['legL'] = place('legL', thigh(M, -1, 0.82, trouser=0.16)); P['legR'] = place('legR', thigh(M, 1, 0.82, trouser=0.2))
    P['kneeL'] = place('kneeL', shin(M, -1, 0.82, shoe=False)); P['kneeR'] = place('kneeR', shin(M, 1, 0.82, shoe=False))
    return finish_z('screamer', P, {'jaw': [0, jy, jz]})


def build_stump(M):
    o = place('body', stump(M), name='part_stump')
    return finish('zombie_stump', [o], {'kind': 'zombie', 'id': 'stump'})


BUILD = {'plain': build_plain, 'chonk': build_chonk, 'biter': build_biter, 'hardhat': build_hardhat, 'screamer': build_screamer, 'stump': build_stump}


def run():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = [a.split('=')[1] for a in argv if a.startswith('--only=')]
    kinds = only[0].split(',') if only else list(BUILD)
    for kind in kinds:  # one scene each: the sheets don't see each other
        reset(); _clear_mats()
        root = BUILD[kind](Mats())
        for o in root.children:
            me = o.data; me.calc_loop_triangles(); print('JF_PART', kind, o.name, len(me.loop_triangles))
        if '--no-export' not in argv: export(root, 'z_' + kind)
        if '--no-sheet' not in argv: cast_sheet(root, 'z_' + kind, note=kind.upper())


def _clear_mats():
    import lib
    lib._mats.clear()


run()
