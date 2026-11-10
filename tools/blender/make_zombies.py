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
#   z_manager  THE FLOOR MANAGER (mini boss): suit, tie, MANAGER badge, comb-over, megaphone, clipboard
#   z_mascot   THE MASCOT (mini boss): Bargain Buddy's plush suit with a mannequin inside
#   z_student / z_teacher / z_lunchlady   Jankfield High's own (shared/zmschool.js zm.skins): the plain zombies there wear these
#   z_stump    the empty socket left on the body where a limb popped off
# blender52 -b --python tools/blender/make_zombies.py [-- --no-sheet] [--only=chonk] [--qa: the blender-asset-qa gate on every kind]
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cast'))
from castlib import *  # noqa (blob, limb, cloth, rubber, skin_tex, path, panel + everything in lib.py)
from sidekit import quad

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


def place(jn, objs, at=None, name=None, weld=True):
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
    o = part(out, name or 'part_' + jn, pivot=p)
    bm = bmesh.new(); bm.from_mesh(o.data)  # weld the seams the joins left, drop collapsed faces
    if weld: bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    bm.to_mesh(o.data); bm.free()
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.material_slot_remove_unused()  # (a boolean cutter leaves an empty slot behind)
    return o


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
        if claw: out.append(rod(lerp3(b, c, 0.7), (c[0], c[1] - 0.022 * k, c[2] - 0.012 * k), 0.0075 * k, M.nail, seg=5, r1=0.001))  # (starts inside the fingertip)
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
        o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)  # (rods carry their place in their location: bake it first)
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
        trouser = min(trouser, 0.425)  # (its ends stay clear of the thigh's own: no two faces in one place)
        out.append(limb('trouser', [(0, 0.005, 0), (0, -trouser * 0.5, -0.003), (0, -trouser, -0.002)], [0.097 * fat, 0.093 * fat, 0.09 * fat], bm, seg=10))
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
    out.append(limb('band', [(0, 0.994, 0), (0, 1.036, 0)], [0.168 * w, 0.158 * w], M.bot, seg=14, squash=(1.0, 0.74)))
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
        st = blob('stripe', (sx * 0.125, 1.33, 0), (0.034, 0.2, 0.183), refl, seg=10, rings=14); cut(st, box((0.5, 0.2, 0.5), (0, 1.014, 0), None)); body.append(st)  # (cut a hair lower than the vest: no two hems in one plane)
    body.append(limb('vband', [(0, 1.172, 0), (0, 1.19, 0), (0, 1.208, 0)], [0.262, 0.27, 0.262], refl, seg=20, squash=(1.0, 0.675)))  # the stripe round the middle
    # tool belt: a pouch, a hammer in its loop, a tape measure
    body.append(limb('belt', [(0, 1.012, 0), (0, 1.034, 0), (0, 1.056, 0)], [0.176, 0.181, 0.176], leather, seg=16, squash=(1.0, 0.74)))
    body.append(box((0.05, 0.04, 0.012), (0, 1.028, -0.134), M.chrome, bev=0.004))
    body.append(box((0.1, 0.12, 0.05), (0.15, 0.95, -0.085), leather, bev=0.01, rot=(0, -0.5, 0)))
    body.append(rod((-0.19, 1.085, -0.03), (-0.2, 0.8, -0.02), 0.013, mat('z_wood', 0xb07a3a, rough=0.6), seg=7))  # hammer handle
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
    s = quad((0, 0, 0), 0.085, 0.045, stk, axis='z', sx=-1); s['keep_uv'] = 1  # the sticker: one quad, tipped back onto the dome
    s.data.transform(Matrix.Rotation(-0.42, 4, 'X')); s.data.transform(Matrix.Translation(gv(0, 0.056, -0.1655))); hat.append(s)
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
    body.append(limb('band', [(0, 0.99, 0), (0, 1.03, 0)], [0.3, 0.29], M.bot, seg=16, squash=(1.0, 0.8)))
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
    bib = panel('bib', 0.26, 0.24, (0, 1.39, -0.19), bibM, curve=0.07, nx=8, ny=6); bib.modifiers.clear(); bibM.use_backface_culling = False; body.append(bib)  # (one sheet, seen from both sides)
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


def keep(objs, *prefixes):
    """objs without the ones whose name starts with a prefix (those are deleted, not left lying in the scene)"""
    out = []
    for o in objs:
        if o is not None and o.name.startswith(prefixes): bpy.data.objects.remove(o, do_unlink=True)
        else: out.append(o)
    return out


def outward(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


def forearm_sleeve(M, sm, fat=1.0, long=1.0):
    """a long sleeve's lower half over arm()'s forearm, cuff at the wrist (arm-local)"""
    L1, L2 = 0.29 * long, 0.26 * long
    e = (0, -0.012, -L1); w = (0, -0.05, -L1 - L2)
    return [limb('sleeve2', [lerp3(e, w, 0.04), lerp3(e, w, 0.5), lerp3(e, w, 0.9)], [0.056 * fat, 0.052 * fat, 0.046 * fat], sm, seg=10),
            limb('cuff', [lerp3(e, w, 0.86), lerp3(e, w, 0.94)], [0.05 * fat, 0.05 * fat], M.white, seg=10)]


def build_manager(M):
    """THE FLOOR MANAGER (mini boss): the mannequin from the suit department. navy suit, red tie, MANAGER badge, a
    comb-over that fools nobody, a moustache, glasses, a megaphone in one hand and a clipboard in the other"""
    suit = cloth('zb_suit', 0x232a44, tex_noise('zb_suitT', 0x232a44, 0.08, 32, seed=41))
    tie = mat('zb_tie', 0xff3030, rough=0.4, clearcoat=0.4)
    badge = mat('zb_badge', 0xffffff, rough=0.4, tex=tex_canvas('zb_badgeT', 48, 24, lambda px: (px.__setitem__(slice(None), hexrgb(0xffe14d)), px.__setitem__((slice(0, 3),), hexrgb(0x120818)), text_px(px, 'MANAGER', 3, 6, 1, 0x120818), text_px(px, 'ASK ME', 6, 15, 1, 0xff3030))))
    mega = mat('zb_mega', 0xf4f2ea, rough=0.3, clearcoat=0.6); megaP = mat('zb_megap', 0xff4fd8, rough=0.3, clearcoat=0.7)
    board = mat('zb_board', 0x8a5a2b, rough=0.6, tex=tex_wood('zb_boardT'))
    paper = mat('zb_paper', 0xffffff, rough=0.6, tex=tex_canvas('zb_paperT', 32, 40, lambda px: (px.__setitem__(slice(None), hexrgb(0xf8f6ee)), [px.__setitem__((slice(6 + i * 5, 7 + i * 5), slice(4, 28 - (i % 3) * 5)), hexrgb(0x55506a)) for i in range(6)], text_px(px, 'FIRED', 2, 33, 1, 0xff3030))))
    body = [blob('hips', (0, 0.95, 0), (0.18, 0.105, 0.13), suit, seg=16, rings=10),
            limb('waist', [(0, 1.0, 0), (0, 1.1, 0.004), (0, 1.2, 0)], [0.135, 0.125, 0.14], M.white, seg=12),
            blob('chest', (0, 1.34, 0), (0.238, 0.215, 0.148), M.white, seg=16, rings=12),
            limb('neck', [(0, 1.5, 0), (0, 1.62, 0)], [0.058, 0.046], M.skin, seg=10),
            limb('collar', [(0, 1.535, 0), (0, 1.575, 0)], [0.068, 0.06], M.white, seg=10)]
    for sx in (-1, 1): body.append(blob('socket', (sx * 0.25, 1.45, 0), (0.078,) * 3, suit, seg=12, rings=8))  # shoulder pads
    jk = blob('jacket', (0, 1.31, 0), (0.262, 0.262, 0.172), suit, seg=18, rings=14)  # open down the front in a V
    cut(jk, box((0.5, 0.7, 0.3), (0.21, 1.42, -0.2), None, rot=(0, 0, 0.42))); cut(jk, box((0.5, 0.7, 0.3), (-0.21, 1.42, -0.2), None, rot=(0, 0, -0.42)))
    cut(jk, box((0.15, 0.1, 0.5), (0, 1.585, 0), None))
    body.append(jk)
    body.append(sweep([(0, 1.535, -0.132), (0, 1.44, -0.146), (0, 1.22, -0.152), (0, 1.14, -0.146)], [0.016, 0.026, 0.034, 0.004], tie, seg=4, squash=(0.3, 1.0), name='tie'))
    body.append(blob('knot', (0, 1.535, -0.13), (0.02, 0.02, 0.012), tie, seg=8, rings=5))
    bd = quad((0, 0, 0), 0.085, 0.042, badge, axis='z', sx=-1); bd['keep_uv'] = 1
    bd.data.transform(Matrix.Rotation(0.42, 4, 'Z')); bd.data.transform(Matrix.Translation(gv(0.15, 1.4, -0.143))); body.append(bd)  # on the left lapel, turned to sit on the jacket
    body.append(limb('band', [(0, 0.994, 0), (0, 1.036, 0)], [0.176, 0.17], mat('zb_belt', 0x15120f, rough=0.3), seg=14, squash=(1.0, 0.74)))
    body.append(box((0.05, 0.04, 0.012), (0, 1.015, -0.132), M.gold, bev=0.004))
    hd = head(M, 'plain')
    cy = 0.155; R = (0.126, 0.18, 0.142)
    for i in range(6):  # the comb-over: six strands dragged across the top
        z = -0.07 + i * 0.03
        hd.append(tube([(-0.118, cy + 0.06, z), (-0.07, cy + 0.158 - abs(z) * 0.5, z), (0.02, cy + 0.183 - abs(z) * 0.7, z + 0.004), (0.1, cy + 0.12 - abs(z) * 0.4, z + 0.01)], 0.006, M.hair, seg=4))
    hd.append(blob('sideL', (-0.118, cy + 0.02, 0.02), (0.02, 0.06, 0.09), M.hair, seg=8, rings=6)); hd.append(blob('sideR', (0.118, cy + 0.02, 0.02), (0.02, 0.06, 0.09), M.hair, seg=8, rings=6))
    ez = -R[2] * 0.9; ey = cy + 0.05
    for sx in (-1, 1):  # glasses, and brows that have had enough
        hd.append(lathe([(0.03, -0.004), (0.036, -0.004), (0.036, 0.004), (0.03, 0.004)], (sx * 0.05, ey, ez - 0.012), M.chrome, seg=12, axis='z'))
        hd.append(blob('lens', (sx * 0.05, ey, ez - 0.008), (0.03, 0.03, 0.004), M.dark, seg=10, rings=4))
        hd.append(rod((sx * 0.086, ey, ez - 0.006), (sx * 0.122, ey + 0.004, 0.0), 0.004, M.chrome, seg=5))
        hd.append(box((0.06, 0.014, 0.03), (sx * 0.05, ey + 0.052, -0.106), M.hair, rot=(0, 0, -sx * 0.45)))
    hd.append(rod((-0.016, ey, ez - 0.014), (0.016, ey, ez - 0.014), 0.004, M.chrome, seg=5))
    hd.append(blob('tache', (0, cy - 0.055, -R[2] * 0.93), (0.055, 0.016, 0.016), M.hair, seg=10, rings=5))
    P = {'body': place('body', body), 'head': place('head', hd)}
    aR = arm(M, 1, 1.05, 1.0, sleeve=0.27, sleeve_m=suit) + forearm_sleeve(M, suit, 1.05)
    w = (0, -0.05, -0.55)  # the megaphone, held out front in the right hand (arm-local: forward = -z)
    mp = (0.0, w[1] + 0.07, w[2] - 0.07)
    aR.append(outward(lathe([(0.001, 0.07), (0.03, 0.065), (0.036, 0.02), (0.04, -0.05), (0.085, -0.24), (0.09, -0.25), (0.078, -0.245), (0.03, -0.06), (0.001, -0.05)], mp, mega, seg=14, axis='z')))  # a hollow horn
    aR.append(outward(lathe([(0.086, -0.238), (0.098, -0.244), (0.098, -0.262), (0.086, -0.262), (0.08, -0.25)], mp, megaP, seg=14, axis='z')))
    aR.append(blob('megadark', (mp[0], mp[1], mp[2] - 0.08), (0.03, 0.03, 0.03), M.dark, seg=8, rings=5))
    aR.append(rod((0.0, w[1] + 0.05, w[2] - 0.07), (0.0, w[1] - 0.03, w[2] - 0.085), 0.016, M.dark, seg=7))  # its grip, in the fist
    aL = arm(M, -1, 1.05, 1.0, sleeve=0.27, sleeve_m=suit) + forearm_sleeve(M, suit, 1.05)
    aL.append(box((0.19, 0.012, 0.26), (0.03, w[1] - 0.045, w[2] - 0.1), board, bev=0.004, rot=(0.25, 0, 0)))  # the clipboard
    pp = quad((0, 0, 0), 0.16, 0.21, paper, axis='y'); pp['keep_uv'] = 1
    pp.data.transform(Matrix.Rotation(0.25, 4, 'X')); pp.data.transform(Matrix.Translation(gv(0.03, w[1] - 0.036, w[2] - 0.0)))
    aL.append(pp)
    aL.append(box((0.07, 0.022, 0.03), (0.03, w[1] - 0.012, w[2] + 0.012), M.chrome, bev=0.004, rot=(0.25, 0, 0)))
    P['arm'] = place('arm', aR); P['armL'] = place('armL', aL)
    shoe = mat('zb_shoe', 0x111114, rough=0.12, clearcoat=1.0)
    for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
        P[k] = place(k, thigh(M, sx, 1.05, trouser=0.44, ragged=False, bm=suit))
        sh = shin(M, sx, 1.05, cuff=True, shoe=False, bm=suit)
        sh = keep(sh, 'ankle', 'foot', 'toe')
        sh.append(limb('leg2', [(0, -0.2, 0.002), (0, -0.4, 0)], [0.068, 0.066], suit, seg=10))
        sh.append(blob('shoe', (0, -0.415, -0.05), (0.062, 0.044, 0.135), shoe, seg=12, rings=8, fn=lambda p, n: 0.01 * max(0, -p.z / 0.135)))
        sh.append(box((0.124, 0.02, 0.28), (0, -0.458, -0.05), M.sole, bev=0.005))
        P[kn] = place(kn, sh)
    return finish_z('manager', P)


def build_mascot(M):
    """THE MASCOT (mini boss): the mall's own Bargain Buddy, with a mannequin still inside. a huge plush head with a
    stitched-on grin and eyes looking two ways, round ears with a 50% OFF tag, a zip-up fur suit, mitts, floppy feet"""
    fur = cloth('zb_fur', 0x4fd8ff, tex_noise('zb_furT', 0x4fd8ff, 0.1, 32, speck=0x2fb0e0, speck_p=0.12, seed=51))
    tum = cloth('zb_tum', 0xffe14d, tex_noise('zb_tumT', 0xffe14d, 0.07, 32, seed=52))
    pink = mat('zb_cheek', 0xff4fd8, rough=0.6)
    white = mat('zb_eyew', 0xffffff, rough=0.25, clearcoat=0.8)
    tagM = mat('zb_tag', 0xffffff, rough=0.5, tex=tex_canvas('zb_tagT', 32, 24, lambda px: (px.__setitem__(slice(None), hexrgb(0xffe14d)), text_px(px, '50%', 7, 3, 1, 0xff3030), text_px(px, 'OFF', 7, 13, 1, 0x120818))))
    name = mat('zb_name', 0xffffff, rough=0.6, tex=tex_canvas('zb_nameT', 64, 32, lambda px: (px.__setitem__(slice(None), hexrgb(0xffe14d)), text_px(px, 'BARGAIN', 11, 5, 1, 0xff4fd8), text_px(px, 'BUDDY', 17, 17, 1, 0x120818))))
    fuzz = lambda p, n: 0.006 * math.sin(p.x * 70 + p.y * 50) * math.sin(p.z * 60)
    body = [blob('hips', (0, 0.95, 0), (0.21, 0.13, 0.17), fur, seg=16, rings=10, fn=fuzz),
            blob('belly', (0, 1.2, -0.02), (0.27, 0.27, 0.23), fur, seg=18, rings=14, fn=fuzz),
            blob('chest', (0, 1.4, 0), (0.25, 0.17, 0.18), fur, seg=16, rings=10, fn=fuzz),
            blob('tum', (0, 1.2, -0.085), (0.2, 0.21, 0.18), tum, seg=16, rings=12),
            limb('neck', [(0, 1.5, 0), (0, 1.62, 0)], [0.058, 0.046], M.skin, seg=10),  # the mannequin's own neck, where the head doesn't quite meet the suit
            limb('ruff', [(0, 1.488, 0), (0, 1.56, 0)], [0.13, 0.1], fur, seg=14)]
    for sx in (-1, 1): body.append(blob('socket', (sx * 0.25, 1.45, 0), (0.085,) * 3, fur, seg=12, rings=8))
    body.append(rod((0, 1.48, -0.21), (0, 1.02, -0.262), 0.006, M.chrome, seg=5))  # the zip
    body.append(box((0.016, 0.04, 0.008), (0, 1.47, -0.214), M.chrome, bev=0.002))
    nm = quad((0, 0, 0), 0.2, 0.1, name, axis='z', sx=-1); nm['keep_uv'] = 1
    nm.data.transform(Matrix.Translation(gv(0.0, 1.27, -0.2562))); body.append(nm)
    tail = blob('tail', (0, 1.02, 0.2), (0.07, 0.07, 0.07), tum, seg=10, rings=8); body.append(tail)
    # the head: twice the size of what's inside it
    cy = 0.27
    hd = [blob('plush', (0, cy, 0), (0.3, 0.27, 0.27), fur, seg=22, rings=16, fn=fuzz),
          blob('muzzle', (0, cy - 0.07, -0.21), (0.15, 0.1, 0.1), tum, seg=14, rings=10),
          blob('nose', (0, cy - 0.02, -0.305), (0.035, 0.026, 0.02), M.dark, seg=10, rings=6),
          blob('neckball', (0, -0.012, 0), (0.052,) * 3, M.joint, seg=10, rings=8)]
    for sx in (-1, 1):
        hd.append(blob('ear', (sx * 0.24, cy + 0.24, 0.0), (0.1, 0.1, 0.05), fur, seg=12, rings=8))
        hd.append(blob('earin', (sx * 0.24, cy + 0.24, -0.03), (0.06, 0.06, 0.03), pink, seg=10, rings=6))
        hd.append(blob('cheek', (sx * 0.2, cy - 0.06, -0.19), (0.05, 0.04, 0.02), pink, seg=10, rings=6))
        hd.append(blob('eye', (sx * 0.11, cy + 0.07, -0.235), (0.062, 0.075, 0.03), white, seg=12, rings=8))
    hd.append(blob('pupilL', (-0.125, cy + 0.09, -0.262), (0.022, 0.026, 0.01), M.dark, seg=8, rings=5))  # one looks up and out,
    hd.append(blob('pupilR', (0.095, cy + 0.045, -0.262), (0.022, 0.026, 0.01), M.dark, seg=8, rings=5))   # one looks down and in
    grin = [(math.sin(a) * 0.11, cy - 0.085 - math.cos(a) * 0.045, -0.292 + abs(math.sin(a)) * 0.03) for a in [math.radians(d) for d in range(-70, 71, 14)]]
    hd.append(tube(grin, 0.009, M.dark, seg=5))  # the stitched-on smile
    for i in (2, 5, 8): hd.append(rod((grin[i][0], grin[i][1] + 0.016, grin[i][2] - 0.004), (grin[i][0], grin[i][1] - 0.016, grin[i][2] - 0.004), 0.004, M.dark, seg=4))  # ... and its stitches
    tg = box((0.004, 0.09, 0.12), (0.33, cy + 0.19, 0.0), tagM, rot=(0, 0, -0.3)); hd.append(tg)  # the price tag stapled through an ear
    hd.append(rod((0.3, cy + 0.26, 0.0), (0.325, cy + 0.235, 0.0), 0.004, M.chrome, seg=5))
    J2 = dict(JT, legL=(-0.15, 0.92, 0), legR=(0.15, 0.92, 0), kneeL=(-0.15, 0.48, 0), kneeR=(0.15, 0.48, 0))  # (fat legs: hips a bit wider)
    P = {'body': place('body', body), 'head': place('head', hd)}
    for k, sx in (('arm', 1), ('armL', -1)):
        a = keep(arm(M, sx, 1.5, 0.95, sleeve=0.26, sleeve_m=fur), 'finger', 'rod', 'thumb', 'mitt', 'wrist')
        a += [limb('sleeve2', [(0, -0.014, -0.29), (0, -0.03, -0.4), (0, -0.05, -0.52)], [0.086, 0.084, 0.082], fur, seg=10),
              blob('paw', (0, -0.06, -0.6), (0.085, 0.07, 0.1), fur, seg=12, rings=8, fn=fuzz),
              blob('pad', (0, -0.1, -0.61), (0.05, 0.02, 0.06), pink, seg=10, rings=5),
              blob('pawthumb', (-sx * 0.075, -0.06, -0.56), (0.035, 0.035, 0.045), fur, seg=8, rings=6)]
        P[k] = place(k, a)
    for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
        P[k] = place(k, thigh(M, sx, 1.4, trouser=0.42, ragged=False, bm=fur), at=J2[k])
        sh = keep(shin(M, sx, 1.4, cuff=True, shoe=False, bm=fur), 'ankle', 'foot', 'toe')
        sh.append(limb('leg2', [(0, -0.28, 0.002), (0, -0.4, 0)], [0.108, 0.112], fur, seg=10))
        sh.append(blob('bigfoot', (0, -0.41, -0.09), (0.11, 0.06, 0.2), tum, seg=14, rings=8))
        for i, tx in enumerate((-0.06, 0, 0.06)): sh.append(blob('toepad%d' % i, (tx, -0.4, -0.27), (0.03, 0.03, 0.03), pink, seg=8, rings=5))
        P[kn] = place(kn, sh, at=J2[kn])
    return finish_z('mascot', P, {'joints': {k: list(v) for k, v in J2.items() if v != JT[k]}})


def clean_arm(M, sx, sm, fat=1.0, long_sleeve=True, tag=False):
    """arm() with a whole sleeve (no rags): to the elbow, or to the wrist with a cuff"""
    a = keep(arm(M, sx, fat, 1.0, sleeve=0.27, sleeve_m=sm, tag=tag), 'box')  # (the boxes are the rags)
    return a + (forearm_sleeve(M, sm, fat) if long_sleeve else [])


def shod(M, sx, fat, bm, shoe_m, sole_m=None, cuff=True):
    """a shin in full trousers (or bare, cuff=False) with a shoe on: shoe_m the upper, sole_m the sole"""
    sh = keep(shin(M, sx, fat, cuff=cuff, shoe=False, bm=bm), 'ankle', 'foot', 'toe')
    if cuff: sh.append(limb('leg2', [(0, -0.278, 0.002), (0, -0.4, 0)], [0.075 * fat, 0.072 * fat], bm, seg=10))  # (clear of the cuff above it: no two skins in one place)
    else: sh.append(blob('ankle2', (0, -0.38, 0), (0.042 * fat,) * 3, M.joint, seg=8, rings=6))
    sh.append(blob('shoe', (0, -0.415, -0.05), (0.062 * fat, 0.044, 0.135), shoe_m, seg=12, rings=8, fn=lambda p, n: 0.01 * max(0, -p.z / 0.135)))
    sh.append(box((0.124 * fat, 0.02, 0.28), (0, -0.458, -0.05), sole_m or M.sole, bev=0.005))
    return sh


def build_student(M):
    """Jankfield High: a student. hoodie (the zombie's own top colour) with the hood down, a backpack that's mostly
    stickers, jeans, white trainers, earbuds still in"""
    pack = cloth('zs_pack', 0xff4fd8, tex_noise('zs_packT', 0xff4fd8, 0.08, 32, seed=61))
    strap = mat('zs_strap', 0x2a2433, rough=0.7)
    sneaker = mat('zs_sneaker', 0xf4f2ea, rough=0.35, clearcoat=0.5)
    stick = mat('zs_sticker', 0xffffff, rough=0.5, tex=tex_canvas('zs_stickerT', 32, 32, lambda px: (px.__setitem__(slice(None), hexrgb(0xffe14d)), px_disc(px, 16, 14, 9, 0x120818, r_in=7), px_disc(px, 12, 12, 1.5, 0x120818), px_disc(px, 20, 12, 1.5, 0x120818), px_line(px, 11, 18, 21, 18, 0x120818, 1.5), text_px(px, 'JHS', 8, 25, 1, 0xff3030))))
    body = [blob('hips', (0, 0.95, 0), (0.176, 0.105, 0.128), M.bot, seg=16, rings=10),
            limb('waist', [(0, 1.0, 0), (0, 1.1, 0.004), (0, 1.2, 0)], [0.15, 0.142, 0.15], M.top, seg=12),
            blob('hoodie', (0, 1.33, 0), (0.256, 0.235, 0.168), M.top, seg=16, rings=12),
            limb('hem', [(0, 1.02, 0), (0, 1.07, 0)], [0.182, 0.176], M.top, seg=14, squash=(1.0, 0.76)),
            limb('neck', [(0, 1.5, 0), (0, 1.62, 0)], [0.058, 0.046], M.skin, seg=10),
            blob('hood', (0, 1.56, 0.11), (0.15, 0.085, 0.1), M.top, seg=12, rings=8),  # down, bunched behind the neck
            blob('pocket', (0, 1.18, -0.142), (0.13, 0.06, 0.03), M.top, seg=10, rings=6)]
    for sx in (-1, 1):
        body.append(blob('socket', (sx * 0.25, 1.45, 0), (0.078,) * 3, M.top, seg=12, rings=8))
        body.append(tube([(sx * 0.035, 1.52, -0.13), (sx * 0.04, 1.42, -0.165), (sx * 0.045, 1.34, -0.166)], 0.005, M.white, seg=4))  # drawstrings
        body.append(tube([(sx * 0.13, 1.54, -0.03), (sx * 0.15, 1.45, -0.15), (sx * 0.15, 1.25, -0.155), (sx * 0.15, 1.16, -0.03), (sx * 0.14, 1.2, 0.14)], 0.014, strap, seg=5))  # the backpack's straps
    body.append(blob('backpack', (0, 1.32, 0.24), (0.19, 0.22, 0.11), pack, seg=14, rings=10))
    body.append(blob('packpocket', (0, 1.24, 0.335), (0.13, 0.1, 0.035), pack, seg=10, rings=6))
    body.append(rod((-0.11, 1.345, 0.345), (0.11, 1.345, 0.345), 0.005, M.chrome, seg=5))  # the zip
    st = quad((0, 0, 0), 0.1, 0.1, stick, axis='z', sx=1); st['keep_uv'] = 1
    st.data.transform(Matrix.Translation(gv(0.02, 1.235, 0.373))); body.append(st)
    body.append(box((0.104, 0.104, 0.02), (0.02, 1.235, 0.3615), strap, bev=0.003))  # its patch (so the sticker sits on something flat)
    hd = head(M, 'plain')
    for sx in (-1, 1):  # earbuds, one wire down into the hoodie
        hd.append(blob('bud', (sx * 0.127, 0.15, 0.0), (0.012, 0.014, 0.014), M.white, seg=6, rings=5))
        hd.append(tube([(sx * 0.13, 0.14, 0.0), (sx * 0.12, 0.05, -0.02), (sx * 0.06, -0.02, -0.05)], 0.003, M.white, seg=4))
    P = {'body': place('body', body), 'head': place('head', hd)}
    P['arm'] = place('arm', clean_arm(M, 1, M.top, tag=True)); P['armL'] = place('armL', clean_arm(M, -1, M.top))
    for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
        P[k] = place(k, thigh(M, sx, 1.0, trouser=0.44, ragged=False))
        P[kn] = place(kn, shod(M, sx, 1.0, M.bot, sneaker, mat('zs_snsole', 0xff4fd8, rough=0.5)))
    return finish_z('student', P)


def build_teacher(M):
    """Jankfield High: a teacher. mustard cardigan over a shirt and tie, grey slacks, sensible shoes, glasses on a
    chain, a red pen behind one ear, hair in a bun that gave up, a mug welded to one hand"""
    cardi = cloth('zs_cardi', 0xc89a2a, tex_stripes('zs_cardiT', 0xc89a2a, 0xb88a22, 16, 2, diag=False))
    slack = cloth('zs_slack', 0x6a6a74, tex_noise('zs_slackT', 0x6a6a74, 0.07, 32, seed=62))
    tie = mat('zs_tie', 0x4fd8ff, rough=0.4, clearcoat=0.3)
    shoe = mat('zs_shoe', 0x5a3a22, rough=0.3, clearcoat=0.6)
    mug = mat('zs_mug', 0xf4f2ea, rough=0.25, clearcoat=0.8)
    body = [blob('hips', (0, 0.95, 0), (0.176, 0.105, 0.128), slack, seg=16, rings=10),
            limb('waist', [(0, 1.0, 0), (0, 1.1, 0.004), (0, 1.2, 0)], [0.132, 0.122, 0.136], M.white, seg=12),
            blob('chest', (0, 1.34, 0), (0.236, 0.213, 0.146), M.white, seg=16, rings=12),
            limb('neck', [(0, 1.5, 0), (0, 1.62, 0)], [0.058, 0.046], M.skin, seg=10),
            limb('collar', [(0, 1.535, 0), (0, 1.572, 0)], [0.066, 0.058], M.white, seg=10),
            limb('band', [(0, 0.994, 0), (0, 1.036, 0)], [0.174, 0.168], slack, seg=14, squash=(1.0, 0.74))]
    for sx in (-1, 1): body.append(blob('socket', (sx * 0.25, 1.45, 0), (0.078,) * 3, cardi, seg=12, rings=8))
    cd = blob('cardigan', (0, 1.3, 0), (0.262, 0.27, 0.172), cardi, seg=18, rings=14)  # open down the front
    cut(cd, box((0.13, 0.8, 0.3), (0, 1.3, -0.16), None)); cut(cd, box((0.16, 0.1, 0.5), (0, 1.58, 0), None))
    body.append(cd)
    for i in range(3):
        by = 1.36 - i * 0.1
        body.append(blob('btn%d' % i, (0.078, by, -0.172 * math.sqrt(1 - (0.078 / 0.262) ** 2 - ((by - 1.3) / 0.27) ** 2)), (0.012, 0.012, 0.006), M.dark, seg=6, rings=4))
    body.append(sweep([(0, 1.535, -0.13), (0, 1.44, -0.144), (0, 1.26, -0.148), (0, 1.2, -0.144)], [0.014, 0.022, 0.028, 0.004], tie, seg=4, squash=(0.3, 1.0), name='tie'))
    hd = head(M, 'plain')
    cy = 0.155; ez = -0.142 * 0.9; ey = cy + 0.05
    hd.append(blob('hairback', (0, cy + 0.03, 0.05), (0.132, 0.17, 0.12), M.hair, seg=14, rings=10))  # hair over the back of the head
    hd.append(blob('bun', (0.02, cy + 0.2, 0.07), (0.06, 0.055, 0.06), M.hair, seg=10, rings=8))
    for i in range(3): hd.append(tube([(0.02, cy + 0.24, 0.07), (0.05 - i * 0.04, cy + 0.3, 0.09 - i * 0.03), (0.08 - i * 0.07, cy + 0.31, 0.12)], 0.004, M.hair, seg=4))  # ... coming undone
    for sx in (-1, 1):
        hd.append(lathe([(0.028, -0.004), (0.034, -0.004), (0.034, 0.004), (0.028, 0.004)], (sx * 0.048, ey, ez - 0.012), M.gold, seg=12, axis='z'))
        hd.append(tube([(sx * 0.08, ey, ez - 0.004), (sx * 0.125, ey - 0.02, 0.0), (sx * 0.1, ey - 0.16, 0.03), (sx * 0.05, ey - 0.2, 0.06)], 0.003, M.gold, seg=4))  # the chain
    hd.append(rod((-0.014, ey, ez - 0.014), (0.014, ey, ez - 0.014), 0.004, M.gold, seg=5))
    hd.append(rod((0.128, cy + 0.02, 0.06), (0.132, cy + 0.09, -0.06), 0.006, mat('zs_pen', 0xff3030, rough=0.3, clearcoat=0.6), seg=6))  # the red pen
    P = {'body': place('body', body), 'head': place('head', hd)}
    aR = clean_arm(M, 1, cardi, tag=True)
    w = (0, -0.05, -0.55)
    aR.append(outward(lathe([(0.001, -0.05), (0.04, -0.05), (0.042, 0.05), (0.036, 0.05), (0.034, -0.04), (0.001, -0.04)], (0.0, w[1] - 0.075, w[2] - 0.07), mug, seg=12, axis='y')))  # the mug, in its fist
    aR.append(tube([(0.04, w[1] - 0.05, w[2] - 0.07), (0.07, w[1] - 0.06, w[2] - 0.07), (0.07, w[1] - 0.1, w[2] - 0.07), (0.04, w[1] - 0.11, w[2] - 0.07)], 0.007, mug, seg=5))
    aR.append(blob('coffee', (0.0, w[1] - 0.04, w[2] - 0.07), (0.033, 0.006, 0.033), M.dark, seg=10, rings=4))
    P['arm'] = place('arm', aR); P['armL'] = place('armL', clean_arm(M, -1, cardi))
    for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
        P[k] = place(k, thigh(M, sx, 1.0, trouser=0.44, ragged=False, bm=slack))
        P[kn] = place(kn, shod(M, sx, 1.0, slack, shoe))
    return finish_z('teacher', P)


def build_lunchlady(M):
    """Jankfield High: the lunch lady. pink tabard, a white apron with one unidentified stain, a hairnet over a perm,
    rubber gloves, a ladle she is not putting down"""
    dress = cloth('zs_dress', 0xff9ad8, tex_noise('zs_dressT', 0xff9ad8, 0.06, 32, seed=63))
    apron = mat('zs_apron', 0xffffff, rough=0.6, tex=tex_canvas('zs_apronT', 32, 48, lambda px: (px.__setitem__(slice(None), hexrgb(0xf6f4ee)), px_disc(px, 20, 30, 5, 0xb8a060), px_disc(px, 24, 34, 3, 0xb8a060), text_px(px, 'EAT', 7, 6, 1, 0xff4fd8))))
    net = mat('zs_net', 0xdfe6ea, rough=0.5)
    glove = mat('zs_glove', 0xffe14d, rough=0.3, clearcoat=0.7)
    clog = mat('zs_clog', 0xf4f2ea, rough=0.3, clearcoat=0.6)
    body = [blob('hips', (0, 0.95, 0), (0.2, 0.115, 0.15), dress, seg=16, rings=10),
            blob('skirt', (0, 0.84, 0), (0.22, 0.16, 0.17), dress, seg=16, rings=10),
            limb('waist', [(0, 1.0, 0), (0, 1.1, 0.004), (0, 1.2, 0)], [0.165, 0.16, 0.168], dress, seg=12),
            blob('chest', (0, 1.34, 0), (0.256, 0.226, 0.176), dress, seg=16, rings=12),
            limb('neck', [(0, 1.5, 0), (0, 1.62, 0)], [0.06, 0.048], M.skin, seg=10)]
    for sx in (-1, 1):
        body.append(blob('socket', (sx * 0.25, 1.45, 0), (0.08,) * 3, dress, seg=12, rings=8))
        body.append(tube([(sx * 0.07, 1.54, -0.1), (sx * 0.08, 1.56, 0.0), (0, 1.56, 0.09)], 0.008, M.white, seg=4))  # the apron's neck strap
    ap = panel('apron', 0.3, 0.62, (0, 1.12, -0.2), apron, curve=0.09, nx=8, ny=8); ap.modifiers.clear(); apron.use_backface_culling = False
    body.append(ap)
    body.append(tube([(-0.15, 1.1, -0.13), (-0.2, 1.1, 0.0), (0, 1.1, 0.165), (0.2, 1.1, 0.0), (0.15, 1.1, -0.13)], 0.007, M.white, seg=4))  # ... and its ties
    hd = head(M, 'plain')
    cy = 0.155
    for i, (x, y, z, r) in enumerate(((0, 0.3, 0.02, 0.085), (-0.08, 0.27, 0.03, 0.07), (0.08, 0.27, 0.03, 0.07), (0, 0.24, 0.1, 0.08), (-0.1, 0.2, 0.06, 0.06), (0.1, 0.2, 0.06, 0.06))):
        hd.append(blob('perm%d' % i, (x, cy + y - 0.155, z), (r, r * 0.9, r), M.hair, seg=8, rings=6))  # the perm
    for a in range(0, 360, 45):  # the hairnet: hoops over it
        ar = math.radians(a)
        hd.append(tube([(math.cos(ar) * 0.14, cy + 0.02, 0.04 + math.sin(ar) * 0.13), (math.cos(ar) * 0.1, cy + 0.14, 0.04 + math.sin(ar) * 0.1), (math.cos(ar) * 0.02, cy + 0.19, 0.04 + math.sin(ar) * 0.02)], 0.003, net, seg=4))
    hd.append(tube([(math.cos(math.radians(a)) * 0.142, cy + 0.02, 0.04 + math.sin(math.radians(a)) * 0.132) for a in range(0, 361, 30)], 0.005, net, seg=4))
    P = {'body': place('body', body), 'head': place('head', hd)}
    for k, sx in (('arm', 1), ('armL', -1)):
        a = clean_arm(M, sx, dress, fat=1.15, long_sleeve=False, tag=False)
        a.append(limb('glove', [(0, -0.03, -0.42), (0, -0.045, -0.5), (0, -0.052, -0.56)], [0.05, 0.048, 0.05], glove, seg=10))  # rubber gloves to the elbow-ish
        if sx > 0:  # the ladle
            w = (0, -0.05, -0.55)
            a.append(rod((0.0, w[1] - 0.03, w[2] - 0.02), (0.0, w[1] + 0.02, w[2] - 0.42), 0.009, M.chrome, seg=6))
            a.append(outward(lathe([(0.001, -0.045), (0.035, -0.04), (0.055, -0.01), (0.058, 0.02), (0.05, 0.02), (0.046, -0.006), (0.03, -0.03), (0.001, -0.034)], (0.0, w[1] + 0.03, w[2] - 0.45), M.chrome, seg=12, axis='y')))
            a.append(blob('slop', (0.0, w[1] + 0.04, w[2] - 0.45), (0.045, 0.012, 0.045), mat('zs_slop', 0xb8a060, rough=0.3, clearcoat=0.6), seg=10, rings=4))
        P[k] = place(k, a)
    for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
        P[k] = place(k, thigh(M, sx, 1.15, trouser=0, ragged=False))
        P[kn] = place(kn, shod(M, sx, 1.15, M.bot, clog, cuff=False))
    return finish_z('lunchlady', P)


def _dots(base, dot, n=4):
    def draw(px):
        px[:] = hexrgb(base)
        for i in range(n):
            for j in range(n): px_disc(px, 4 + i * 8 + (4 if j % 2 else 0), 4 + j * 8, 1.6, dot)
    return draw


def build_patient(M):
    """Second Opinion General: a patient. spotty gown tied (badly) at the back, a bandage round the head with a bow
    on it, a wristband, bunny slippers, still holding their own drip"""
    gown = cloth('zs_gown', 0xa8d8f0, tex_canvas('zs_gownT', 32, 32, _dots(0xa8d8f0, 0x5a9ad0)))
    band = mat('zs_bandage', 0xf6f4ee, rough=0.7)
    fluff = cloth('zs_fluff', 0xff9ad8, tex_noise('zs_fluffT', 0xff9ad8, 0.1, 32, seed=71))
    drip = mat('zs_drip', 0x9af0d0, rough=0.12, clearcoat=1.0)
    body = [blob('hips', (0, 0.95, 0), (0.19, 0.11, 0.14), gown, seg=16, rings=10),
            limb('skirt', [(0, 1.03, 0), (0, 0.86, 0), (0, 0.64, 0)], [0.186, 0.212, 0.236], gown, seg=16, squash=(1.0, 0.78)),  # an A-line to the knee
            limb('waist', [(0, 1.0, 0), (0, 1.1, 0.004), (0, 1.2, 0)], [0.156, 0.15, 0.158], gown, seg=12),
            blob('chest', (0, 1.34, 0), (0.24, 0.218, 0.156), gown, seg=16, rings=12),
            limb('neck', [(0, 1.5, 0), (0, 1.62, 0)], [0.058, 0.046], M.skin, seg=10),
            limb('neckband', [(0, 1.522, 0), (0, 1.55, 0)], [0.075, 0.066], band, seg=10)]
    for sx in (-1, 1): body.append(blob('socket', (sx * 0.25, 1.45, 0), (0.078,) * 3, gown, seg=12, rings=8))
    for i, y in enumerate((1.42, 1.2, 1.0)):  # the ties down the back: a knot and two tails each
        z = 0.156 * math.sqrt(max(0.05, 1 - ((y - 1.34) / 0.218) ** 2)) if y > 1.2 else 0.158 if y > 1.05 else 0.142
        body.append(blob('knot%d' % i, (0, y, z), (0.016, 0.014, 0.012), band, seg=6, rings=5))
        for sx in (-1, 1): body.append(tube([(0, y, z), (sx * 0.04, y - 0.02, z + 0.012), (sx * 0.05, y - 0.07, z + 0.006)], 0.005, band, seg=4))
    hd = head(M, 'plain')
    cy = 0.155
    hd.append(limb('bandage', [(0, cy + 0.045, 0), (0, cy + 0.085, 0), (0, cy + 0.125, 0)], [0.1432, 0.1312, 0.1092], band, seg=16, squash=(0.887, 1.0)))
    hd.append(limb('bandage2', [(0, cy + 0.07, 0), (0, cy + 0.1, 0)], [0.1392, 0.1282], band, seg=16, squash=(0.887, 1.0)))
    hd.append(blob('bowknot', (0.1, cy + 0.11, -0.05), (0.014, 0.014, 0.014), band, seg=6, rings=5))  # ... with a bow
    for dz in (-1, 1):
        hd.append(blob('bow', (0.112, cy + 0.118, -0.05 + dz * 0.028), (0.008, 0.02, 0.024), band, seg=8, rings=6))
        hd.append(tube([(0.105, cy + 0.105, -0.05), (0.12, cy + 0.06, -0.05 + dz * 0.02), (0.118, cy + 0.02, -0.05 + dz * 0.03)], 0.004, band, seg=4))
    P = {'body': place('body', body), 'head': place('head', hd)}
    w = (0, -0.05, -0.55)
    aR = clean_arm(M, 1, gown, long_sleeve=False, tag=False)
    aR.append(blob('dripbag', (0.0, w[1] - 0.15, w[2] - 0.07), (0.05, 0.075, 0.02), drip, seg=12, rings=8))  # the drip, in its fist
    aR.append(blob('dripcap', (0.0, w[1] - 0.07, w[2] - 0.07), (0.018, 0.016, 0.014), M.white, seg=8, rings=5))
    aR.append(box((0.05, 0.035, 0.004), (0.0, w[1] - 0.15, w[2] - 0.0915), M.white, bev=0.001))  # its label
    aR.append(tube([(0.0, w[1] - 0.22, w[2] - 0.07), (0.0, w[1] - 0.25, w[2] - 0.02), (0.02, w[1] - 0.2, w[2] + 0.08), (0.0, -0.062, -0.4)], 0.004, drip, seg=5))
    aR.append(box((0.045, 0.006, 0.03), (0.0, -0.06, -0.4), band, bev=0.001))  # taped on
    aL = clean_arm(M, -1, gown, long_sleeve=False, tag=False)
    aL.append(limb('wristband', [(0, -0.047, -0.49), (0, -0.049, -0.515)], [0.05, 0.05], M.white, seg=10))
    aL.append(box((0.03, 0.012, 0.02), (0, 0.004, -0.5025), mat('zs_wbtag', 0x4fd8ff, rough=0.4), bev=0.002))
    P['arm'] = place('arm', aR); P['armL'] = place('armL', aL)
    eye = mat('zs_sleye', 0x120818, rough=0.2, clearcoat=0.8)
    for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
        P[k] = place(k, thigh(M, sx, 1.0, trouser=0, ragged=False))
        sh = shod(M, sx, 1.0, M.bot, fluff, M.white, cuff=False)
        for ex in (-1, 1):  # bunny slippers
            sh.append(blob('ear', (ex * 0.026, -0.335, -0.1), (0.015, 0.05, 0.011), fluff, seg=8, rings=6))
            sh.append(blob('earin', (ex * 0.026, -0.332, -0.109), (0.008, 0.034, 0.004), M.white, seg=6, rings=5))
            sh.append(blob('sleye', (ex * 0.024, -0.392, -0.158), (0.007, 0.008, 0.006), eye, seg=6, rings=4))
        sh.append(blob('nose', (0, -0.405, -0.181), (0.009, 0.007, 0.007), M.white, seg=6, rings=4))
        sh.append(blob('tail', (0, -0.4, 0.085), (0.02, 0.02, 0.02), M.white, seg=8, rings=6))
        P[kn] = place(kn, sh)
    return finish_z('patient', P)


def build_nurse(M):
    """Second Opinion General: a nurse. mint scrubs, a paper cap with a heart on it, a ponytail, a stethoscope, pens in
    the pocket, a clipboard, and a syringe that is frankly too big"""
    scrub = cloth('zs_scrub', 0x5ed8b8, tex_noise('zs_scrubT', 0x5ed8b8, 0.06, 32, seed=72))
    trim = mat('zs_scrubtrim', 0x2a9a80, rough=0.6)
    clog = mat('zs_nclog', 0xf4f2ea, rough=0.3, clearcoat=0.6)
    heart = mat('zs_heart', 0xff4fd8, rough=0.35, clearcoat=0.5)
    steth = mat('zs_steth', 0x2a2433, rough=0.4, clearcoat=0.4)
    liquid = mat('zs_syringe', 0x7dff4f, rough=0.1, clearcoat=1.0, emit=0x39ff14, strength=0.6)
    clip = mat('zs_clip', 0x8a5a2c, rough=0.6)
    body = [blob('hips', (0, 0.95, 0), (0.176, 0.105, 0.128), scrub, seg=16, rings=10),
            limb('waist', [(0, 1.0, 0), (0, 1.1, 0.004), (0, 1.2, 0)], [0.146, 0.138, 0.146], scrub, seg=12),
            blob('chest', (0, 1.34, 0), (0.24, 0.216, 0.15), scrub, seg=16, rings=12),
            limb('hem', [(0, 1.02, 0), (0, 1.07, 0)], [0.184, 0.178], scrub, seg=14, squash=(1.0, 0.76)),
            limb('hemtrim', [(0, 1.012, 0), (0, 1.026, 0)], [0.188, 0.188], trim, seg=14, squash=(1.0, 0.76)),
            limb('neck', [(0, 1.5, 0), (0, 1.62, 0)], [0.058, 0.046], M.skin, seg=10),
            limb('collar', [(0, 1.53, 0), (0, 1.556, 0)], [0.074, 0.064], trim, seg=10)]
    for sx in (-1, 1): body.append(blob('socket', (sx * 0.25, 1.45, 0), (0.078,) * 3, scrub, seg=12, rings=8))
    zc = lambda x, y: -0.15 * math.sqrt(max(0.02, 1 - (x / 0.24) ** 2 - ((y - 1.34) / 0.216) ** 2))  # the chest's front
    body.append(box((0.085, 0.075, 0.012), (0.1, 1.36, zc(0.1, 1.36) - 0.002), scrub, bev=0.003))  # the pocket
    body.append(box((0.089, 0.012, 0.014), (0.1, 1.399, zc(0.1, 1.397) - 0.008), trim, bev=0.002))
    for i, c in enumerate((0xff3030, 0x4fd8ff, 0xffe14d)):
        body.append(rod((0.078 + i * 0.022, 1.385, zc(0.1, 1.39) - 0.012), (0.078 + i * 0.022, 1.44, zc(0.1, 1.43) - 0.012), 0.005, mat('zs_pen%d' % i, c, rough=0.3, clearcoat=0.6), seg=6))
    st = [(-0.066, 1.5, -0.085), (-0.085, 1.535, 0.0), (0, 1.55, 0.075), (0.085, 1.535, 0.0), (0.066, 1.5, -0.085), (0.02, 1.42, zc(0.02, 1.42) - 0.006), (-0.06, 1.33, zc(-0.06, 1.33) - 0.006)]
    body.append(tube(st, 0.007, steth, seg=6))  # the stethoscope, round the neck
    body.append(lathe([(0.001, -0.008), (0.026, -0.008), (0.03, 0.0), (0.026, 0.008), (0.001, 0.008)], (-0.06, 1.33, zc(-0.06, 1.33) - 0.012), M.chrome, seg=12, axis='z'))
    hd = head(M, 'plain')
    cy = 0.155
    hd.append(blob('hairback', (0, cy + 0.03, 0.05), (0.132, 0.17, 0.12), M.hair, seg=14, rings=10))
    hd.append(blob('tieband', (0, cy + 0.08, 0.17), (0.03, 0.03, 0.022), heart, seg=8, rings=6))
    hd.append(sweep([(0, cy + 0.08, 0.17), (0, cy + 0.06, 0.25), (0, cy - 0.04, 0.29), (0, cy - 0.15, 0.27)], [0.03, 0.05, 0.042, 0.008], M.hair, seg=8, name='ponytail'))
    hd.append(box((0.17, 0.07, 0.06), (0, cy + 0.19, -0.035), M.white, bev=0.012))  # the paper cap
    hd.append(box((0.19, 0.02, 0.07), (0, cy + 0.158, -0.037), M.white, bev=0.006))
    for sx in (-1, 1): hd.append(blob('heart', (sx * 0.011, cy + 0.197, -0.066), (0.014, 0.014, 0.006), heart, seg=8, rings=5))
    hd.append(blob('heartpt', (0, cy + 0.184, -0.066), (0.012, 0.014, 0.006), heart, seg=8, rings=5))
    P = {'body': place('body', body), 'head': place('head', hd)}
    w = (0, -0.05, -0.55)
    aR = clean_arm(M, 1, scrub, long_sleeve=False, tag=False)  # the syringe: barrel forward, plunger back over the fist
    by = w[1] - 0.013; bz = w[2] - 0.07
    aR.append(outward(lathe([(0.001, -0.17), (0.03, -0.17), (0.032, -0.16), (0.032, 0.1), (0.05, 0.1), (0.05, 0.11), (0.001, 0.11)], (0.0, by, bz - 0.06), mat('zs_barrel', 0xe8f4ff, rough=0.08, clearcoat=1.0), seg=12, axis='z')))
    aR.append(outward(lathe([(0.0335, -0.06), (0.0345, -0.055), (0.0345, 0.045), (0.0335, 0.05)], (0.0, by, bz - 0.16), liquid, seg=12, axis='z', cap=False)))  # what's in it (a band round the barrel)
    aR.append(rod((0.0, by, bz - 0.2), (0.0, by, bz - 0.38), 0.005, M.chrome, seg=6))  # the needle
    aR.append(blob('needlehub', (0.0, by, bz - 0.235), (0.014, 0.014, 0.02), M.chrome, seg=8, rings=6))
    aR.append(rod((0.0, by, bz + 0.02), (0.0, by, bz + 0.153), 0.009, M.white, seg=6))
    aR.append(outward(lathe([(0.001, -0.008), (0.04, -0.008), (0.04, 0.008), (0.001, 0.008)], (0.0, by, bz + 0.15), M.white, seg=12, axis='z')))
    aL = clean_arm(M, -1, scrub, long_sleeve=False, tag=False)
    aL.append(box((0.19, 0.012, 0.26), (0.0, w[1] - 0.05, w[2] - 0.06), clip, bev=0.004))  # the clipboard, flat under its hand
    aL.append(box((0.165, 0.004, 0.22), (0.0, w[1] - 0.042, w[2] - 0.065), M.white, bev=0.001))
    aL.append(box((0.07, 0.014, 0.02), (0.0, w[1] - 0.036, w[2] + 0.05), M.chrome, bev=0.003))
    for i in range(4): aL.append(box((0.12 - (i % 2) * 0.03, 0.002, 0.008), (-0.005 - (i % 2) * 0.015, w[1] - 0.039, w[2] - 0.0 - i * 0.04), M.dark, bev=0.0005))
    P['arm'] = place('arm', aR); P['armL'] = place('armL', aL)
    for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
        P[k] = place(k, thigh(M, sx, 1.0, trouser=0.44, ragged=False, bm=scrub))
        P[kn] = place(kn, shod(M, sx, 1.0, scrub, clog, mat('zs_nsole', 0x5ed8b8, rough=0.5)))
    return finish_z('nurse', P)


def build_surgeon(M):
    """Second Opinion General: the surgeon. green gown to the knee, cap, mask, a head mirror, long blue gloves, shoe
    covers, and a defibrillator paddle in each hand. CLEAR"""
    gown = cloth('zs_sgown', 0x3aa888, tex_noise('zs_sgownT', 0x3aa888, 0.06, 32, seed=73))
    dark = cloth('zs_sscrub', 0x2a7a6a, tex_noise('zs_sscrubT', 0x2a7a6a, 0.06, 32, seed=74))
    glove = mat('zs_sglove', 0x7ac8ff, rough=0.25, clearcoat=0.8)
    cover = mat('zs_cover', 0x8ad0f4, rough=0.5)
    mask = mat('zs_mask', 0xdff2f8, rough=0.6)
    padl = mat('zs_paddle', 0xff3030, rough=0.3, clearcoat=0.7)
    cable = mat('zs_cable', 0x2a2433, rough=0.5)
    body = [blob('hips', (0, 0.95, 0), (0.192, 0.11, 0.142), gown, seg=16, rings=10),
            limb('skirt', [(0, 1.03, 0), (0, 0.86, 0), (0, 0.62, 0)], [0.188, 0.21, 0.23], gown, seg=16, squash=(1.0, 0.78)),  # an A-line to the knee
            limb('waist', [(0, 1.0, 0), (0, 1.1, 0.004), (0, 1.2, 0)], [0.158, 0.152, 0.16], gown, seg=12),
            blob('chest', (0, 1.34, 0), (0.25, 0.222, 0.162), gown, seg=16, rings=12),
            limb('neck', [(0, 1.5, 0), (0, 1.62, 0)], [0.058, 0.046], M.skin, seg=10),
            limb('collar', [(0, 1.52, 0), (0, 1.575, 0)], [0.08, 0.062], gown, seg=10),
            limb('sash', [(0, 1.085, 0), (0, 1.115, 0)], [0.158, 0.158], dark, seg=14)]
    for sx in (-1, 1): body.append(blob('socket', (sx * 0.25, 1.45, 0), (0.08,) * 3, gown, seg=12, rings=8))
    body.append(blob('sashknot', (0.06, 1.1, 0.158), (0.02, 0.018, 0.014), dark, seg=6, rings=5))
    for sx in (-1, 1): body.append(tube([(0.06, 1.1, 0.158), (0.06 + sx * 0.04, 1.07, 0.172), (0.06 + sx * 0.05, 1.0, 0.168)], 0.006, dark, seg=4))
    hd = head(M, 'plain')
    cy = 0.155
    hd.append(blob('cap', (0, cy + 0.085, 0.012), (0.134, 0.118, 0.152), gown, seg=16, rings=10))
    hd.append(limb('capband', [(0, cy + 0.03, 0.004), (0, cy + 0.06, 0.004)], [0.146, 0.142], dark, seg=16, squash=(0.9, 1.0)))
    hd.append(blob('mask', (0, cy - 0.05, -0.084), (0.094, 0.066, 0.072), mask, seg=12, rings=8))
    for i in range(3): hd.append(rod((-0.07, cy - 0.03 - i * 0.022, -0.146 + abs(i - 1) * 0.004), (0.07, cy - 0.03 - i * 0.022, -0.146 + abs(i - 1) * 0.004), 0.003, mat('zs_pleat', 0xb8d8e4, rough=0.6), seg=4))  # its pleats
    for sx in (-1, 1):
        for dy in (-0.02, -0.085): hd.append(tube([(sx * 0.085, cy + dy, -0.1), (sx * 0.125, cy + dy + 0.02, 0.0), (sx * 0.08, cy + dy + 0.03, 0.11), (0, cy + dy + 0.035, 0.137)], 0.003, mask, seg=4))  # ... and its ties
    hd.append(lathe([(0.001, -0.004), (0.04, -0.004), (0.046, 0.006), (0.04, 0.01), (0.012, 0.004), (0.001, 0.004)], (0.03, cy + 0.11, -0.132), M.chrome, seg=14, axis='z'))  # the head mirror
    hd.append(limb('mirrorband', [(0, cy + 0.098, 0.004), (0, cy + 0.122, 0.004)], [0.137, 0.131], dark, seg=16, squash=(0.9, 1.0)))  # ... on its band
    P = {'body': place('body', body), 'head': place('head', hd)}
    w = (0, -0.05, -0.55)
    for k, sx in (('arm', 1), ('armL', -1)):
        a = clean_arm(M, sx, gown, tag=False)
        e = (0, -0.012, -0.29)
        a.append(limb('glove', [lerp3(e, w, 0.4), lerp3(e, w, 0.7), lerp3(e, w, 1.03)], [0.061, 0.058, 0.057], glove, seg=10))  # (well clear of the sleeve inside it)
        a.append(limb('glovecuff', [lerp3(e, w, 0.37), lerp3(e, w, 0.43)], [0.066, 0.066], glove, seg=10))
        py = w[1] - 0.085; pz = w[2] - 0.075  # a paddle: the plate down, a handle through the fist, a coiled lead back up the arm
        a.append(box((0.13, 0.016, 0.17), (0.0, py - 0.029, pz), M.chrome, bev=0.006))
        a.append(box((0.11, 0.05, 0.15), (0.0, py, pz), padl, bev=0.014))
        a.append(box((0.03, 0.03, 0.15), (0.0, py + 0.045, pz + 0.01), padl, bev=0.01))
        a.append(blob('button', (0.0, py + 0.064, pz - 0.05), (0.012, 0.008, 0.012), mat('zs_pbtn', 0xffe14d, rough=0.3, emit=0xffe14d, strength=0.8), seg=8, rings=5))
        coil = [(0.0, py + 0.03, pz + 0.085)] + [(math.sin(i * 1.6) * 0.022 * sx, -0.105 + i * 0.004 + math.cos(i * 1.6) * 0.018, pz + 0.12 + i * 0.02) for i in range(9)]
        a.append(tube(coil, 0.005, cable, seg=5))
        P[k] = place(k, a)
    for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
        P[k] = place(k, thigh(M, sx, 1.0, trouser=0.44, ragged=False, bm=dark))
        sh = shod(M, sx, 1.0, dark, cover, cover)
        sh.append(limb('coverband', [(0, -0.36, 0.0), (0, -0.376, 0.0)], [0.081, 0.081], mat('zs_coverband', 0x5aa8d8, rough=0.5), seg=10))  # elastic
        P[kn] = place(kn, sh)
    return finish_z('surgeon', P)


def build_stump(M):
    o = place('body', stump(M), name='part_stump', weld=False)
    return finish('zombie_stump', [o], {'kind': 'zombie', 'id': 'stump'})


BUILD = {'plain': build_plain, 'chonk': build_chonk, 'biter': build_biter, 'hardhat': build_hardhat, 'screamer': build_screamer, 'manager': build_manager, 'mascot': build_mascot, 'student': build_student, 'teacher': build_teacher, 'lunchlady': build_lunchlady, 'patient': build_patient, 'nurse': build_nurse, 'surgeon': build_surgeon, 'stump': build_stump}


def run():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = [a.split('=')[1] for a in argv if a.startswith('--only=')]
    kinds = only[0].split(',') if only else list(BUILD)
    for kind in kinds:  # one scene each: the sheets don't see each other
        reset(); _clear_mats()
        root = BUILD[kind](Mats())
        for o in root.children:
            me = o.data; me.calc_loop_triangles(); print('JF_PART', kind, o.name, len(me.loop_triangles))
        if '--qa' in argv: qa(kind, root)
        if '--no-export' not in argv: export(root, 'z_' + kind)
        if '--no-sheet' not in argv: cast_sheet(root, 'z_' + kind, note=kind.upper())


def qa(kind, root):
    """the blender-asset-qa gate on this kind's parts, checked together (so a part off on its own shows as floating)"""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    hits = []
    if os.environ.get('JF_ZF_DEBUG'):  # where the coplanar faces are (world x, y, z), to find a z-fight by hand
        pit = qa_check._point_in_tri
        def spy(q, a, b, c, n):
            r = pit(q, a, b, c, n)
            if r and abs(n.dot((b - a).cross(c - a).normalized())) > 0.5: hits.append((round(q.x, 3), round(q.y, 3), round(q.z, 3), round(n.x, 2), round(n.y, 2), round(n.z, 2)))
            return r
        qa_check._point_in_tri = spy
    bpy.context.view_layer.update()
    res = qa_check.run(objects=[o.name for o in root.children], profile='game')
    print('JF_QA', kind, 'PASS' if res['pass'] else 'FAIL', len(res['errors']), 'errors', len(res['warnings']), 'warnings')
    for e in res['errors']: print('JF_QA_E', kind, str(e)[:300])
    for w in res['warnings']: print('JF_QA_W', kind, str(w)[:300])
    for h in sorted(set(hits))[:400]: print('JF_ZF', kind, h)


def _clear_mats():
    import lib
    lib._mats.clear()


run()
