# JANKFIELD HIGH's furniture and props (20 Nov 2026): every item of school_layout.FURN as a chunky model, drawn with
# arenakit's primitives inside the kit's headless Blender run (school_models.py calls furniture(K, L)).
#
# The contract (school_layout.F): an item is (kind, cx, y, cz, sx, sy, sz, turn, kw), its box in world axes with its
# bottom at y. Where the item is solid that box is also its hit box, so a model fills it closely and never sticks out
# more than ~0.3 where people walk (overhangs above head height are fine). L.FACE(item) says which way its front
# looks ('n' -z, 's' +z, 'e' +x, 'w' -x). Each model is drawn in a local frame: u across the front (-W/2..W/2), w from
# the back (-D/2) to the front (+D/2), v up from the floor (0..H); Fr maps it to the world.
#
# Style (the owner's rules: chunky-model-style, less-colourful-look, structure-over-colour): few big rounded shapes,
# flat quiet colours (greys, creams, muted woods), colour only as one accent (L.ACCENT, a muted teal: seats, trims,
# the trophy case, mats). Real structure (legs, frames, drawers, rims) so a room reads as its room from across it.
# Textured faces: the classroom boards' slate (L.TEXKEY['chalkboard']) and the lockers' fronts (L.TEXKEY['lockers']);
# the courtyard sheds' brick (L.TEXKEY['brick']); everything else plain colours.
# No text, letters, digits, logos, real flags, nothing gory. Details stand at least 0.06 proud; pieces sink 0.05 into
# what they stand on (no flicker: memory roblox-zfight-check).
import math, random
from mathutils import Matrix

WOOD, WOOD_D, WOOD_L = 'a98a68', '7d6248', 'c4ab88'
METAL, METAL_D, STEEL = '8e969c', '5f666c', 'b4b9bc'
DARK, BLACK, SLATE = '3a3d42', '26282b', '2d3133'
CREAM, WHITE, PALE = 'e6e0d2', 'eeece6', 'd5d2ca'
FABRIC, BRASS = '6f7c82', 'b39a62'
LEAF, LEAF_D, SOIL, POT = '5d7a48', '4a6339', '5a4a3c', '9c6b52'
# (knobs the v2 builds turn: desk legs at least a third of a stud thick, no classroom pennant, the lobby's posts bigger
#  than their hit boxes; school_models.py sets them per variant)
LEGT, NO_FLAG, PILLAR_GROW = 0.2, False, 0.0
TRUNK, LIMB = 1.5, 0.9         # (the courtyard tree's trunk radius and limb thickness)
MIRROR, SCREEN = 'b9c7cc', '1f2326'
BOOKS = ('8a4f4a', '3f5470', '6b6e45', 'a8874a', '7c7f84', 'c9bfa6', '5e4a5e', '4f6b66')
FLOORS = (-16.0, 0.0, 16.0, 32.0)


def level_of(kind, y):
    """the item's floor: the highest floor at or under it (the gym's scoreboard hangs high: still the ground floor)"""
    if kind == 'scoreboard': return 'G'
    f = max([v for v in FLOORS if v <= y + 0.01] or [-16.0])
    return {-16.0: 'B', 0.0: 'G', 16.0: 'U', 32.0: 'R'}[f]


class Fr:
    """a local frame for one item: u across its front, w toward its front, v up from its bottom"""
    YAW = {'s': 0.0, 'n': math.pi, 'e': math.pi / 2, 'w': -math.pi / 2}

    def __init__(s, K, model, cx, y, cz, face, W, D, H):
        s.K, s.m, s.cx, s.y, s.cz, s.f = K, model, cx, y, cz, face
        s.W, s.D, s.H = W, D, H

    def P(s, u, w):
        f = s.f
        if f == 's': return (s.cx + u, s.cz + w)
        if f == 'n': return (s.cx - u, s.cz - w)
        if f == 'e': return (s.cx + w, s.cz - u)
        return (s.cx - w, s.cz + u)

    def box(s, col, u0, v0, w0, u1, v1, w1, bev=0.12, kind='plastic', segs=1):
        xa, za = s.P(u0, w0)
        xb, zb = s.P(u1, w1)
        s.K.B(s.m, col, xa, s.y + v0, za, xb, s.y + v1, zb, bev=bev, kind=kind, segs=segs)

    def rbox(s, col, cu, cv, cw, su, sv, sw, yaw=0.0, pitch=0.0, roll=0.0, bev=0.1, kind='plastic', segs=1):
        """a box by its local centre and size, turned (yaw about up, pitch about u, roll about w), radians"""
        K = s.K
        x, z = s.P(cu, cw)
        M = K.Tr(x, s.y + cv, z) @ K.Ry(Fr.YAW[s.f] + yaw) @ K.Rx(pitch) @ K.Rz(roll)
        K.B(s.m, col, -su / 2, -sv / 2, -sw / 2, su / 2, sv / 2, sw / 2, bev=bev, kind=kind, segs=segs, M=M)

    def cyl(s, col, u, v0, w, r, h, segs=12, bev=0.08, kind='plastic', r2=None):
        x, z = s.P(u, w)
        s.K.cyl(s.m, col, x, s.y + v0, z, r, h, segs=segs, bev=bev, kind=kind, r2=r2)

    def cylu(s, col, u0, u1, v, w, r, segs=10, bev=0.05):
        """a bar along local u"""
        xa, za = s.P(u0, w)
        xb, zb = s.P(u1, w)
        if abs(xb - xa) > abs(zb - za): s.K.cylx(s.m, col, min(xa, xb), max(xa, xb), s.y + v, za, r, segs=segs, bev=bev)
        else: s.K.cylz(s.m, col, min(za, zb), max(za, zb), xa, s.y + v, r, segs=segs, bev=bev)

    def cylw(s, col, w0, w1, v, u, r, segs=10, bev=0.05):
        """a bar along local w"""
        xa, za = s.P(u, w0)
        xb, zb = s.P(u, w1)
        if abs(xb - xa) > abs(zb - za): s.K.cylx(s.m, col, min(xa, xb), max(xa, xb), s.y + v, za, r, segs=segs, bev=bev)
        else: s.K.cylz(s.m, col, min(za, zb), max(za, zb), xa, s.y + v, r, segs=segs, bev=bev)

    def sph(s, col, u, v, w, r, segs=12, rings=8, kind='plastic'):
        x, z = s.P(u, w)
        s.K.sphere(s.m, col, x, s.y + v, z, r, segs=segs, rings_=rings, kind=kind)

    def blob(s, col, u, v, w, r, sy=0.75, sub=1, sx=1.0, sz=1.0):
        x, z = s.P(u, w)
        s.K.blob(s.m, col, x, s.y + v, z, r, sy=sy, sub=sub, sx=sx, sz=sz)

    def lathe(s, col, prof, u, v, w, segs=14, kind='plastic'):
        x, z = s.P(u, w)
        s.K.lathe(s.m, col, prof, x, s.y + v, z, segs=segs, kind=kind)

    def legs(s, col, u0, w0, u1, w1, v1, t=0.25, v0=-0.05):
        """four plain legs at the corners of a rectangle (their outer faces on it)"""
        for (u, w) in ((u0, w0), (u1 - t, w0), (u0, w1 - t), (u1 - t, w1 - t)):
            s.box(col, u, v0, w, u + t, v1, w + t, bev=0, segs=1)


# ================================================================ the models (each: f = the frame, it = the item)
def m_desk(f, it):
    """a student desk with its seat attached: the desktop in front (toward the board), the seat behind"""
    W, D, H = f.W, f.D, f.H
    f.box(WOOD_L, -W / 2, H - 0.18, D / 2 - 1.45, W / 2, H, D / 2, bev=0.08)                 # the top
    f.box(METAL_D, -W / 2 + 0.25, -0.05, -D / 2 + 0.25, -W / 2 + 0.25 + LEGT, H - 0.15, D / 2 - 0.25, bev=0)  # side frame (a slab of legs)
    f.box(METAL_D, W / 2 - 0.25 - LEGT, -0.05, -D / 2 + 0.25, W / 2 - 0.25, 0.25, D / 2 - 0.25, bev=0)      # the foot rail
    f.box(METAL_D, W / 2 - 0.25 - LEGT, -0.05, D / 2 - 0.3 - LEGT, W / 2 - 0.25, H - 0.15, D / 2 - 0.3, bev=0)     # the front leg
    f.box(f_acc(f), -W / 2 + 0.35, 1.35, -D / 2, W / 2 - 0.35, 1.55, -D / 2 + 1.1, bev=0.08)         # the seat
    f.box(f_acc(f), -W / 2 + 0.45, 1.55, -D / 2, W / 2 - 0.45, H, -D / 2 + 0.18, bev=0.06)           # the back
    f.box(METAL_D, -W / 2 + 0.6, 0.6, D / 2 - 1.3, W / 2 - 0.6, 0.72, D / 2 - 0.3, bev=0)            # the book rack under


def f_acc(f): return f.K_ACC


def m_teacherdesk(f, it):
    W, D, H = f.W, f.D, f.H
    # the desk at the front of its box, the teacher's chair tucked in behind
    f.box(WOOD, -W / 2, H - 0.22, D / 2 - 2.4, W / 2, H, D / 2, bev=0.1, segs=2)
    f.box(WOOD_D, -W / 2 + 0.1, -0.05, D / 2 - 2.3, -W / 2 + 2.3, H - 0.2, D / 2 - 0.1, bev=0.08)       # the drawer pedestal
    for k in range(3):
        f.box(WOOD_L, -W / 2 + 0.25, 0.25 + k * 0.78, D / 2 - 0.12, -W / 2 + 2.15, 0.95 + k * 0.78, D / 2 - 0.04, bev=0.05)
        f.box(STEEL, -W / 2 + 0.95, 0.55 + k * 0.78, D / 2 - 0.06, -W / 2 + 1.45, 0.65 + k * 0.78, D / 2 + 0.04, bev=0)
    f.box(WOOD_D, W / 2 - 0.35, -0.05, D / 2 - 2.3, W / 2 - 0.1, H - 0.2, D / 2 - 0.1, bev=0.05)         # the end panel
    f.box(WOOD_D, -W / 2 + 2.3, 0.6, D / 2 - 0.35, W / 2 - 0.35, H - 0.2, D / 2 - 0.15, bev=0.04)      # modesty panel
    chair(f, 0.6, -D / 2 + 0.6, 'front', seat=1.5, back=3.2, cw=1.8)
    f.box(DARK, 1.6, H - 0.05, D / 2 - 1.6, 2.6, H + 0.12, D / 2 - 0.8, bev=0.04)                      # a closed folder
    f.cyl(BRASS, -2.0, H - 0.05, D / 2 - 1.0, 0.3, 0.5, segs=8)                                        # a mug


def chair(f, u, w, facing, seat=1.6, back=3.0, cw=1.9, col=None):
    """a chair at local (u, w), cw wide; facing 'front' (+w) or 'back' (its back on the other side)"""
    col = col or f.K_ACC
    s = 1 if facing == 'front' else -1
    h = cw / 2
    f.box(METAL_D, u - h + 0.1, -0.05, w - h + 0.1, u - h + 0.28, seat, w + h - 0.1, bev=0)
    f.box(METAL_D, u + h - 0.28, -0.05, w - h + 0.1, u + h - 0.1, seat, w + h - 0.1, bev=0)
    f.box(col, u - h, seat - 0.05, w - h, u + h, seat + 0.18, w + h, bev=0.08)
    bw = w - s * (h - 0.12)
    f.box(col, u - h + 0.1, seat + 0.18, bw - 0.1, u + h - 0.1, back, bw + 0.1, bev=0.08)


def along(f, it):
    """a frame along the item's long side (benches, tables: no front)"""
    kind, cx, y, cz, sx, sy, sz, turn, kw = it
    W, D, H = (sx, sz, sy) if sx >= sz else (sz, sx, sy)
    g = Fr(f.K, f.m, cx, y, cz, 's' if sx >= sz else 'e', W, D, H)
    g.K_ACC, g.L = f.K_ACC, f.L
    return g


def m_board(f, it):
    """the chalkboard: the slate (textured) exactly on the item box, an aluminium frame and a chalk tray"""
    K, L = f.K, f.L
    kind, cx, y, cz, sx, sy, sz, turn, kw = it
    x0, x1 = cx - sx / 2, cx + sx / 2
    z0, z1 = cz - 8.0, cz + 8.0
    y0, y1 = y, y + 6.0
    K.B(f.m, L.TEXKEY['chalkboard'], x0, y0, z0, x1, y1, z1, bev=0.02, segs=1)
    fx = x1 + 0.08                                           # the frame stands proud of the slate's face
    for (a, b, c, d) in ((z0 - 0.3, y1, z1 + 0.3, y1 + 0.3), (z0 - 0.3, y0 - 0.3, z1 + 0.3, y0), (z0 - 0.3, y0, z0, y1), (z1, y0, z1 + 0.3, y1)):
        K.B(f.m, STEEL, x0, b, a, fx, d, c, bev=0.05, segs=1)
    K.B(f.m, STEEL, x0, y0 - 0.45, z0 + 0.2, x1 + 0.55, y0 - 0.25, z1 - 0.2, bev=0.04, segs=1)     # the tray
    for (zz, c) in ((z0 + 3.0, WHITE), (z0 + 3.6, PALE), (z1 - 4.0, WHITE)):
        K.cylz(f.m, c, zz - 0.25, zz + 0.25, x1 + 0.3, y0 - 0.17, 0.08, segs=6, bev=0)
    K.B(f.m, DARK, x1 + 0.1, y0 - 0.25, z1 - 2.8, x1 + 0.45, y0 - 0.05, z1 - 1.9, bev=0.04)        # the eraser


def m_cubbies(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(WOOD_L, -W / 2, -0.05, -D / 2, W / 2, H, -D / 2 + 0.2, bev=0.05)                 # the back
    for k in range(5):                                                                   # the uprights
        u = -W / 2 + k * (W - 0.25) / 4
        f.box(WOOD, u, -0.05, -D / 2 + 0.15, u + 0.25, H, D / 2, bev=0.05)
    for k in range(4):                                                                   # the shelves
        v = k * (H - 0.2) / 3
        f.box(WOOD, -W / 2 + 0.05, v, -D / 2 + 0.15, W / 2 - 0.05, v + 0.2, D / 2 - 0.02, bev=0.04)
    rnd = random.Random(int(it[1] * 7 + it[3] * 13))
    for i in range(4):
        for j in range(3):
            if rnd.random() < 0.55:
                u = -W / 2 + i * (W - 0.25) / 4 + 0.6
                v = j * (H - 0.2) / 3 + 0.2
                c = rnd.choice(BOOKS)
                f.box(c, u, v, -D / 2 + 0.3, u + 1.2, v + 0.75 + rnd.random() * 0.25, D / 2 - 0.3, bev=0.12)


def m_flag(f, it):
    """a classroom pennant on a short pole (plain: no country, no marks)"""
    if NO_FLAG: return
    f.cyl(METAL_D, 0, -0.05, 0, 0.35, 0.3, segs=8)
    f.cyl(STEEL, 0, 0.2, 0, 0.07, f.H - 0.2, segs=6, bev=0)
    f.sph(BRASS, 0, f.H + 0.05, 0, 0.16, segs=6, rings=4)
    x, z = f.P(0.05, 0)
    M = f.K.Tr(x, f.y + f.H - 2.6, z) @ f.K.Ry(Fr.YAW[f.f])
    f.K.plate(f.m, f.K_ACC, [(0, 0), (2.4, 0.9), (0, 1.8)], 0.08, M, bev=0.02)


def m_stalls(f, it):
    """a row of toilet stalls: partitions every 5 studs (on the stallwall hit boxes), doors standing open, a toilet in
    each; its front (the open side) faces FACE"""
    W, D, H = f.W, f.D, f.H
    n = it[8].get('n', int(W // 5))
    PART, DOOR = 'a8b3b5', '9aa6a8'
    for k in range(n + 1):
        u = -W / 2 + 5 * k
        f.box(PART, u - 0.2, 0.8, -D / 2, u + 0.2, H, D / 2 - 0.2, bev=0.06)
        f.box(STEEL, u - 0.15, -0.05, D / 2 - 0.55, u + 0.15, 0.85, D / 2 - 0.25, bev=0)     # a foot
        f.box(PART, u - 0.35, -0.05, D / 2 - 0.2, u + 0.35, H, D / 2, bev=0)                  # the front pilaster
    for k in range(n):
        u0 = -W / 2 + 5 * k
        f.box(PART, u0 + 0.35, H - 0.5, D / 2 - 0.15, u0 + 5 - 0.35, H - 0.1, D / 2, bev=0)     # the head rail
        # the door, hung on the right pilaster, swung in 70 degrees
        hu, hw = u0 + 5 - 0.35, D / 2 - 0.1
        a = math.radians(70)
        L2 = 4.1
        cu, cw = hu - math.cos(a) * L2 / 2, hw - math.sin(a) * L2 / 2
        f.rbox(DOOR, cu, 0.8 + 2.9, cw, L2, 5.8, 0.25, yaw=-a, bev=0)
        # the toilet at the back
        tu = u0 + 2.5
        f.box(WHITE, tu - 0.9, 1.4, -D / 2 + 0.05, tu + 0.9, 3.2, -D / 2 + 0.75, bev=0.15)    # the tank
        f.cyl(WHITE, tu, -0.05, -D / 2 + 1.7, 0.75, 1.6, segs=8, bev=0, r2=0.6)              # the bowl
        f.cyl(PALE, tu, 1.5, -D / 2 + 1.7, 0.8, 0.15, segs=8, bev=0)                         # the seat


def m_sinks(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(PALE, -W / 2, H - 0.3, -D / 2, W / 2, H, D / 2, bev=0.1, segs=2)                # the counter top
    f.box(STEEL, -W / 2 + 0.1, -0.05, -D / 2, W / 2 - 0.1, H - 0.3, -D / 2 + 0.4, bev=0.04)  # the back skirt
    f.box(PALE, -W / 2 + 0.2, H - 1.0, D / 2 - 0.35, W / 2 - 0.2, H - 0.28, D / 2 - 0.15, bev=0.05)  # the apron
    n = max(1, int(W // 3.2))
    for k in range(n):
        u = -W / 2 + (k + 0.5) * W / n
        f.cyl(STEEL, u, H - 0.02, 0.15, 0.75, 0.08, segs=10, bev=0)                       # the basin (a steel disc)
        f.cyl(STEEL, u, H - 0.05, -D / 2 + 0.55, 0.12, 0.85, segs=6, bev=0)               # the tap
        f.box(STEEL, u - 0.1, H + 0.65, -D / 2 + 0.45, u + 0.1, H + 0.8, 0.0, bev=0)


def m_mirror(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(STEEL, -W / 2, 0, -D / 2, W / 2, H, D / 2, bev=0.04)
    f.box(MIRROR, -W / 2 + 0.15, 0.15, -D / 2, W / 2 - 0.15, H - 0.15, D / 2 + 0.07, bev=0.02)


def m_reception(f, it):
    """the front desk: a raised counter toward the visitors, a lower work top behind"""
    W, D, H = f.W, f.D, f.H
    f.box(WOOD, -W / 2, -0.05, D / 2 - 1.3, W / 2, H - 0.25, D / 2, bev=0.15, segs=2)          # the front body
    f.box(CREAM, -W / 2 - 0.0, H - 0.25, D / 2 - 1.5, W / 2, H, D / 2, bev=0.1)                # the counter top
    f.box(f.K_ACC, -W / 2 + 0.3, 0.9, D / 2 - 0.02, W / 2 - 0.3, 1.2, D / 2 + 0.06, bev=0.03)   # an accent band
    f.box(WOOD_D, -W / 2 + 0.2, 2.35, -D / 2, W / 2 - 0.2, 2.6, D / 2 - 1.3, bev=0.08)          # the work top
    f.box(WOOD_D, -W / 2, -0.05, -D / 2, -W / 2 + 0.4, 2.35, D / 2 - 1.3, bev=0.05)
    f.box(WOOD_D, W / 2 - 0.4, -0.05, -D / 2, W / 2, 2.35, D / 2 - 1.3, bev=0.05)
    for u in (-5.0, 3.0):                                                                       # monitors (dark, blank)
        f.box(DARK, u - 0.15, 2.6, -D / 2 + 0.6, u + 0.15, 3.1, -D / 2 + 0.9, bev=0)
        f.box(SCREEN, u - 1.0, 3.0, -D / 2 + 0.55, u + 1.0, 4.2, -D / 2 + 0.75, bev=0.05)
    f.box(PALE, 6.0, H, D / 2 - 1.2, 7.4, H + 0.12, D / 2 - 0.3, bev=0.03)                       # a sign-in tray


def m_pillar(f, it):
    W, D, H = f.W + PILLAR_GROW, f.D + PILLAR_GROW, f.H
    x0, z0 = f.P(-W / 2 + 0.25, -D / 2 + 0.25)
    x1, z1 = f.P(W / 2 - 0.25, D / 2 - 0.25)
    f.K.chamfer(f.m, CREAM, min(x0, x1), f.y + 0.6, min(z0, z1), max(x0, x1), f.y + H - 0.6, max(z0, z1), ch=0.4)
    f.box(PALE, -W / 2, -0.05, -D / 2, W / 2, 0.6, D / 2, bev=0.1)                        # base
    f.box(PALE, -W / 2, H - 0.6, -D / 2, W / 2, H + 0.05, D / 2, bev=0.1)                 # capital


def m_trophy(f, it):
    """the trophy case: a wood and accent frame, glass front, three shelves of cups and plates"""
    W, D, H = f.W, f.D, f.H
    acc = f.K_ACC
    f.box(WOOD_D, -W / 2, -0.05, -D / 2, W / 2, 1.4, D / 2, bev=0.1)                       # base cabinet
    f.box(WOOD_D, -W / 2, 1.4, -D / 2, W / 2, H, -D / 2 + 0.2, bev=0.04)                  # back
    f.box(acc, -W / 2, 1.4, -D / 2, -W / 2 + 0.25, H, D / 2, bev=0.05)                    # sides
    f.box(acc, W / 2 - 0.25, 1.4, -D / 2, W / 2, H, D / 2, bev=0.05)
    f.box(acc, -W / 2, H - 0.35, -D / 2, W / 2, H, D / 2, bev=0.06)                       # top
    f.box(PALE, -W / 2 + 0.25, 1.4, D / 2 - 0.1, W / 2 - 0.25, H - 0.35, D / 2 - 0.02, kind='glass', bev=0)
    rnd = random.Random(int(it[1] * 3 + it[3] * 11))
    for j, v in enumerate((1.4, 3.3, 5.2)):
        if j: f.box(PALE, -W / 2 + 0.25, v - 0.1, -D / 2 + 0.2, W / 2 - 0.25, v, D / 2 - 0.15, kind='glass', bev=0)
        u = -W / 2 + 1.0
        while u < W / 2 - 1.0:
            if rnd.random() < 0.6:
                h = 0.9 + rnd.random() * 0.8
                f.lathe(BRASS if rnd.random() < 0.7 else STEEL, [(0, 0), (0.35, 0), (0.12, 0.15), (0.1, h * 0.5), (0.45, h * 0.75), (0.5, h), (0, h)], u, v - 0.05, 0, segs=10)
            else:
                f.rbox(STEEL, u, v + 0.5, -D / 2 + 0.45, 1.0, 1.0, 0.1, pitch=-0.15, bev=0.03)
            u += 1.3 + rnd.random() * 0.7


def m_bench(f, it):
    """a bench (it runs along its box's long side)"""
    g = along(f, it)
    W, D, H = g.W, g.D, g.H
    g.box(WOOD, -W / 2, H - 0.3, -D / 2, W / 2, H, -D / 2 + D * 0.48, bev=0.08)
    g.box(WOOD, -W / 2, H - 0.3, D / 2 - D * 0.48, W / 2, H, D / 2, bev=0.08)
    for u in (-W / 2 + 0.4, W / 2 - 0.9, 0.0 - 0.25) if W > 6 else (-W / 2 + 0.4, W / 2 - 0.9):
        g.box(METAL_D, u, -0.05, -D / 2 + 0.25, u + 0.5, H - 0.25, D / 2 - 0.25, bev=0.04)


def m_plant(f, it):
    W, D, H = f.W, f.D, f.H
    f.cyl(POT, 0, -0.05, 0, W / 2 - 0.15, 1.9, segs=12, bev=0.12, r2=W / 2)
    f.cyl(SOIL, 0, 1.8, 0, W / 2 - 0.3, 0.15, segs=12, bev=0)
    f.blob(LEAF, 0, 3.2, 0, 1.4, sy=1.0, sub=1)
    f.blob(LEAF_D, 0.5, 4.2, -0.3, 1.0, sy=1.0, sub=1)
    f.blob(LEAF, -0.4, 4.3, 0.4, 0.9, sy=1.0, sub=1)


def m_bed(f, it):
    """a nurse's cot: frame on legs, mattress, pillow at the head (the back), a curtain bunched at the head corner"""
    W, D, H = f.W, f.D, f.H
    f.legs(STEEL, -W / 2 + 0.1, -D / 2 + 0.2, W / 2 - 0.1, D / 2 - 0.2, 1.3, t=0.25)
    f.box(METAL, -W / 2, 1.2, -D / 2 + 0.1, W / 2, 1.5, D / 2 - 0.1, bev=0.06)
    f.box(WHITE, -W / 2 + 0.15, 1.45, -D / 2 + 0.2, W / 2 - 0.15, 2.15, D / 2 - 0.2, bev=0.25, segs=2)
    f.box(PALE, -W / 2 + 0.6, 2.1, -D / 2 + 0.4, W / 2 - 0.6, 2.4, -D / 2 + 1.5, bev=0.12)
    f.box(f.K_ACC, -W / 2 + 0.12, 1.5, D / 2 - 2.6, W / 2 - 0.12, 2.25, D / 2 - 0.25, bev=0.2)   # a folded blanket
    f.box(STEEL, -W / 2 - 0.1, -0.05, -D / 2 - 0.0, -W / 2 + 0.1, 3.2, -D / 2 + 0.25, bev=0)    # the head rail
    f.box(STEEL, W / 2 - 0.1, -0.05, -D / 2 - 0.0, W / 2 + 0.1, 3.2, -D / 2 + 0.25, bev=0)
    f.cylu(STEEL, -W / 2 - 0.1, W / 2 + 0.1, 3.1, -D / 2 + 0.12, 0.1, segs=6, bev=0)
    f.cylw(STEEL, -D / 2, D / 2 - 0.2, 8.5, W / 2 - 0.1, 0.08, segs=6, bev=0)                 # the curtain rail (high)
    f.box(PALE, W / 2 - 0.45, 1.6, -D / 2 + 0.3, W / 2 + 0.0, 8.4, -D / 2 + 1.0, bev=0.15)      # the curtain, bunched


def m_desk_big(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(WOOD, -W / 2, H - 0.25, -D / 2, W / 2, H, D / 2, bev=0.1, segs=2)
    pw = min(2.2, W * 0.3)
    for s in (-1, 1):
        u0 = -W / 2 + 0.1 if s < 0 else W / 2 - pw - 0.1
        f.box(WOOD_D, u0, -0.05, -D / 2 + 0.1, u0 + pw, H - 0.24, D / 2 - 0.1, bev=0.06)
        for k in range(3 if H > 2.4 else 2):
            vv = 0.25 + k * (H - 0.6) / 3
            f.box(WOOD_L, u0 + 0.12, vv, D / 2 - 0.12, u0 + pw - 0.12, vv + (H - 0.6) / 3 - 0.1, D / 2 - 0.04, bev=0.04)
    f.box(WOOD_D, -W / 2 + pw, 0.7, D / 2 - 0.35, W / 2 - pw, H - 0.25, D / 2 - 0.15, bev=0.04)
    if W > 5:
        f.box(DARK, -0.15, H - 0.05, -D / 2 + 0.5, 0.15, H + 0.5, -D / 2 + 0.8, bev=0)
        f.box(SCREEN, -1.1, H + 0.4, -D / 2 + 0.45, 1.1, H + 1.7, -D / 2 + 0.65, bev=0.05)


def m_cabinet(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(PALE, -W / 2, -0.05, -D / 2, W / 2, H - 0.3, D / 2 - 0.08, bev=0.08)
    f.box(METAL_D, -W / 2 - 0.0, H - 0.35, -D / 2, W / 2, H, D / 2, bev=0.08)
    f.box(METAL_D, -W / 2 + 0.1, -0.05, D / 2 - 0.15, W / 2 - 0.1, 0.35, D / 2 - 0.02, bev=0.03)
    for s in (-1, 1):
        u0 = -W / 2 + 0.12 if s < 0 else 0.04
        f.box(CREAM, u0, 0.45, D / 2 - 0.12, u0 + W / 2 - 0.16, H - 0.45, D / 2 - 0.02, bev=0.05)
        f.box(STEEL, s * 0.35 - 0.06, H * 0.5 - 0.6, D / 2 - 0.05, s * 0.35 + 0.06, H * 0.5 + 0.6, D / 2 + 0.06, bev=0)


def m_servery(f, it):
    """the serving counter: a steel top, a tray rail toward the queue, a sneeze guard over it"""
    W, D, H = f.W, f.D, f.H
    f.box(PALE, -W / 2, -0.05, -D / 2, W / 2, H - 0.25, D / 2 - 0.35, bev=0.1)
    f.box(STEEL, -W / 2, H - 0.25, -D / 2, W / 2, H, D / 2 - 0.25, bev=0.06)
    f.box(METAL_D, -W / 2 + 0.2, -0.05, D / 2 - 0.45, W / 2 - 0.2, 0.4, D / 2 - 0.3, bev=0.03)     # kick
    for v in (H - 0.7, H - 0.45):
        f.box(STEEL, -W / 2, v, D / 2 - 0.3, W / 2, v + 0.1, D / 2 - 0.02, bev=0)                  # the tray rail
    for u in (-W / 2 + 0.4, W / 2 - 0.6) + tuple(-W / 2 + 4 * k for k in range(1, int(W // 4))):
        f.box(STEEL, u, H, -0.15, u + 0.2, H + 2.2, 0.05, bev=0)
    f.rbox(PALE, 0, H + 1.9, 0.35, W - 0.2, 0.08, 1.4, pitch=0.35, kind='glass', bev=0)          # the sneeze guard
    rnd = random.Random(int(it[3] * 5))
    u = -W / 2 + 1.2
    while u < W / 2 - 1.2:                                                                        # the food pans
        f.box(METAL, u - 0.9, H - 0.02, -D / 2 + 0.3, u + 0.9, H + 0.12, -D / 2 + 1.6, bev=0.03)
        f.box(rnd.choice(('b89a6a', 'a4a58a', 'c2b294')), u - 0.75, H + 0.08, -D / 2 + 0.45, u + 0.75, H + 0.16, -D / 2 + 1.45, bev=0)
        u += 2.2


def m_kitchen(f, it):
    """ranges and ovens along the kitchen's wall, a hood over them"""
    W, D, H = f.W, f.D, f.H
    f.box(STEEL, -W / 2, -0.05, -D / 2, W / 2, H - 0.2, D / 2 - 0.08, bev=0.08)
    f.box(METAL, -W / 2, H - 0.25, -D / 2, W / 2, H, D / 2, bev=0.06)
    n = max(1, int(W // 3.0))
    for k in range(n):
        u0 = -W / 2 + k * W / n + 0.2
        u1 = u0 + W / n - 0.4
        f.box(METAL_D, u0, 0.6, D / 2 - 0.12, u1, H - 0.7, D / 2 - 0.02, bev=0.05)              # the oven door
        f.box(STEEL, u0 + 0.2, H - 0.95, D / 2 - 0.06, u1 - 0.2, H - 0.85, D / 2 + 0.06, bev=0)  # its handle
        for (du, dw) in ((0.3, -0.6), (0.7, 0.4)):
            f.cyl(DARK, u0 + (u1 - u0) * du, H - 0.05, dw, 0.5, 0.12, segs=8, bev=0)             # burners
    f.box(STEEL, -W / 2, 7.0, -D / 2, W / 2, 9.0, D / 2 + 0.2, bev=0.15, segs=2)                # the hood


def m_fridge(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(STEEL, -W / 2, -0.05, -D / 2, W / 2, H, D / 2 - 0.12, bev=0.15, segs=2)
    for s in (-1, 1):
        u0 = -W / 2 + 0.1 if s < 0 else 0.05
        f.box(STEEL, u0, 0.4, D / 2 - 0.15, u0 + W / 2 - 0.15, H - 0.1, D / 2 - 0.02, bev=0.08)
        f.box(METAL_D, s * 0.4 - 0.08, 3.0, D / 2 - 0.05, s * 0.4 + 0.08, 5.6, D / 2 + 0.06, bev=0)
    f.box(METAL_D, -W / 2 + 0.2, -0.05, D / 2 - 0.4, W / 2 - 0.2, 0.4, D / 2 - 0.1, bev=0.03)


def m_lunchtable(f, it):
    """a cafeteria table with its two benches on one frame"""
    g = along(f, it)
    W, D, H = g.W, g.D, g.H
    g.box(CREAM, -W / 2 + 0.2, H - 0.25, -1.5, W / 2 - 0.2, H, 1.5, bev=0.12, segs=2)        # the top
    g.box(g.K_ACC, -W / 2 + 0.5, 1.45, -D / 2, W / 2 - 0.5, 1.65, -D / 2 + 1.25, bev=0.1)   # the benches
    g.box(g.K_ACC, -W / 2 + 0.5, 1.45, D / 2 - 1.25, W / 2 - 0.5, 1.65, D / 2, bev=0.1)
    for u in (-W / 2 + 1.6, W / 2 - 2.0):                                                     # the frames
        g.box(METAL_D, u, -0.05, -D / 2 + 0.4, u + 0.4, 0.25, D / 2 - 0.4, bev=0)
        g.box(METAL_D, u, 0.2, -0.2, u + 0.4, H - 0.25, 0.2, bev=0)
        g.box(METAL_D, u, 1.25, -D / 2 + 0.5, u + 0.4, 1.45, D / 2 - 0.5, bev=0)
    g.box(METAL_D, -W / 2 + 1.6, 1.0, -0.15, W / 2 - 1.6, 1.25, 0.15, bev=0)


def m_trash(f, it):
    W, D, H = f.W, f.D, f.H
    f.cyl('6f7a6a', 0, -0.05, 0, W / 2 - 0.1, H - 0.25, segs=12, bev=0.08, r2=W / 2)
    f.cyl('5c6658', 0, H - 0.3, 0, W / 2 + 0.05, 0.3, segs=12, bev=0.08)


def m_labbench(f, it):
    """a lab bench: pale cabinets, a black top, a sink with a gooseneck tap and gas taps in the middle"""
    W, D, H = f.W, f.D, f.H
    f.box(PALE, -W / 2 + 0.2, -0.05, -D / 2 + 0.2, W / 2 - 0.2, H - 0.25, D / 2 - 0.2, bev=0.08)
    f.box(SLATE, -W / 2, H - 0.28, -D / 2, W / 2, H, D / 2, bev=0.06)
    for s in (-1, 1):                                                         # doors on both long sides
        for k in range(3):
            u0 = -W / 2 + 0.4 + k * (W - 0.8) / 3
            u1 = u0 + (W - 0.8) / 3 - 0.15
            w = s * (D / 2 - 0.2)
            f.box(CREAM, u0, 0.4, w - 0.08 if s > 0 else w - 0.0, u1, H - 0.5, w + 0.08 if s < 0 else w + 0.0, bev=0.04)
    f.box(METAL_D, -1.0, H - 0.05, -0.6, 1.0, H + 0.02, 0.6, bev=0.02)                       # the sink
    f.cyl(STEEL, 0, H - 0.05, 0.0, 0.1, 1.5, segs=6, bev=0)
    f.box(STEEL, -0.1, H + 1.4, -0.1, 0.1, H + 1.55, 0.7, bev=0)
    for u in (-3.0, 3.0):
        f.box(DARK, u - 0.4, H - 0.05, -0.25, u + 0.4, H + 0.6, 0.25, bev=0.05)                  # gas tap posts
        f.cyl(BRASS, u, H + 0.6, 0, 0.12, 0.2, segs=6, bev=0)


def m_fume(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(PALE, -W / 2, -0.05, -D / 2, W / 2, 3.0, D / 2 - 0.05, bev=0.08)                  # base
    f.box(SLATE, -W / 2, 3.0, -D / 2, W / 2, 3.25, D / 2, bev=0.04)                          # work top
    f.box(PALE, -W / 2, 3.25, -D / 2, -W / 2 + 0.35, H, D / 2, bev=0.06)                     # sides
    f.box(PALE, W / 2 - 0.35, 3.25, -D / 2, W / 2, H, D / 2, bev=0.06)
    f.box(PALE, -W / 2, H - 1.0, -D / 2, W / 2, H, D / 2, bev=0.08)                          # hood top
    f.box(PALE, -W / 2 + 0.35, 3.25, -D / 2, W / 2 - 0.35, H - 1.0, -D / 2 + 0.2, bev=0)     # back
    f.box(STEEL, -W / 2 + 0.35, 4.9, D / 2 - 0.2, W / 2 - 0.35, 5.6, D / 2 - 0.05, bev=0.03)  # the sash frame
    f.box(PALE, -W / 2 + 0.4, 5.6, D / 2 - 0.16, W / 2 - 0.4, H - 1.0, D / 2 - 0.08, kind='glass', bev=0)
    for k in range(3):                                                                         # glassware inside
        f.cyl('bccfd0', -W / 2 + 1.5 + k * 1.6, 3.2, -0.2, 0.3 + 0.1 * k, 0.9 + 0.3 * k, segs=8, bev=0.03, kind='glass')
    f.cyl(METAL, 0, H - 0.05, -0.3, 0.7, 2.0, segs=10, bev=0.05)                              # the duct


def m_skeleton(f, it):
    """(no skeletons: a big ball-and-stick molecule model on a stand)"""
    f.cyl(METAL_D, 0, -0.05, 0, 0.9, 0.3, segs=10)
    f.cyl(STEEL, 0, 0.2, 0, 0.1, 3.0, segs=6, bev=0)
    pts = [(0, 3.9, 0, 0.55, '9a5a52'), (0.9, 4.5, 0.3, 0.38, WHITE), (-0.9, 4.4, -0.2, 0.38, WHITE), (0.2, 4.7, -0.8, 0.45, '3f5470'),
           (-0.3, 3.2, 0.7, 0.38, WHITE), (0.7, 3.3, -0.6, 0.38, WHITE)]
    for (u, v, w, r, c) in pts:
        f.sph(c, u, v, w, r, segs=10, rings=6)
    for (u, v, w, r, c) in pts[1:]:
        dx, dy, dz = u, v - 3.9, w
        ln = math.sqrt(dx * dx + dy * dy + dz * dz)
        yaw = math.atan2(dx, dz)
        pitch = -math.asin(dy / ln)
        f.rbox(PALE, u / 2, (v + 3.9) / 2, w / 2, 0.12, 0.12, ln, yaw=yaw, pitch=pitch, bev=0)


def m_lockers(f, it):
    """a run of lockers: the front (textured: 4 doors per 8 studs) from the floor to 6.5, a darker cap and kick"""
    W, D, H = f.W, f.D, f.H
    L = f.L
    f.box(METAL_D, -W / 2 + 0.06, -0.05, -D / 2, W / 2 - 0.06, H, D / 2 - 0.12, bev=0.04)          # the body
    f.box(L.TEXKEY['lockers'], -W / 2 + 0.12, 0.0, D / 2 - 0.16, W / 2 - 0.12, H, D / 2, bev=0.02)  # the fronts
    f.box(METAL_D, -W / 2, -0.05, D / 2 - 0.3, W / 2, 0.4, D / 2 + 0.07, bev=0.02)                  # the kick
    f.box(METAL_D, -W / 2, H, -D / 2, W / 2, H + 0.35, D / 2 + 0.07, bev=0.04)                      # the cap


def m_shelf(f, it):
    """steel shelving (along its long side): four uprights, four shelves, boxes on them"""
    f = along(f, it)
    W, D, H = f.W, f.D, f.H
    for (u, w) in ((-W / 2, -D / 2), (W / 2 - 0.2, -D / 2), (-W / 2, D / 2 - 0.2), (W / 2 - 0.2, D / 2 - 0.2)):
        f.box(METAL, u, -0.05, w, u + 0.2, H, w + 0.2, bev=0)
    rnd = random.Random(int(it[1] * 17 + it[3]))
    for k in range(4):
        v = 0.3 + k * (H - 0.5) / 3
        f.box(STEEL, -W / 2 + 0.05, v, -D / 2 + 0.05, W / 2 - 0.05, v + 0.12, D / 2 - 0.05, bev=0)
        if k == 3: continue
        u = -W / 2 + 0.4
        while u < W / 2 - 1.2:
            bw = 0.8 + rnd.random() * 1.4
            bh = min(1.6, 0.6 + rnd.random() * 1.2)
            c = rnd.choice(('b39a74', 'a68a62', '8e969c', 'c9bfa6', '6f7a6a'))
            f.box(c, u, v + 0.1, -D / 2 + 0.3, min(u + bw, W / 2 - 0.3), v + 0.1 + bh, D / 2 - 0.3, bev=0.06)
            u += bw + 0.2 + rnd.random() * 0.4


def m_mopsink(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(PALE, -W / 2, -0.05, -D / 2, W / 2, 1.2, D / 2, bev=0.15)
    f.box(METAL, -W / 2 + 0.3, 1.05, -D / 2 + 0.3, W / 2 - 0.3, 1.2, D / 2 - 0.3, bev=0.02)
    f.cyl(STEEL, 0, -0.05, -D / 2 + 0.2, 0.1, H + 1.2, segs=6, bev=0)
    f.box(STEEL, -0.1, H + 1.0, -D / 2 + 0.1, 0.1, H + 1.15, -D / 2 + 1.0, bev=0)
    f.box(WOOD_L, W / 2 - 0.7, 1.2, -D / 2 + 0.2, W / 2 - 0.5, 6.0, -D / 2 + 0.4, bev=0)          # a mop handle


def m_cart(f, it):
    W, D, H = f.W, f.D, f.H
    f.box('7a8b6a', -W / 2 + 0.2, 0.3, -D / 2 + 0.2, W / 2 - 0.2, 2.6, D / 2 - 1.6, bev=0.15)  # the caddy
    f.cyl('b8a24e', 0, 0.3, D / 2 - 0.9, min(W, 1.6) / 2 - 0.05, 1.4, segs=10, bev=0.08)      # the bucket (muted yellow)
    f.box(METAL_D, -W / 2, -0.05, -D / 2, W / 2, 0.35, D / 2, bev=0.04)
    f.box(WOOD_L, -0.1, 1.5, D / 2 - 1.0, 0.1, 6.5, D / 2 - 0.8, bev=0)                         # the mop
    f.box(METAL_D, -W / 2 + 0.1, 0.3, -D / 2 + 0.05, W / 2 - 0.1, H, -D / 2 + 0.25, bev=0.04)   # the handle frame


def m_tree(f, it):
    """the courtyard's big tree: a round brick planter (its hit box) and a trunk with big canopy blobs to ~30"""
    W, D, H = f.W, f.D, f.H
    L = f.L
    r = W / 2
    f.cyl(L.TEXKEY['brick'], 0, -0.05, 0, r, H + 0.05, segs=28, bev=0.12)
    f.cyl(PALE, 0, H - 0.05, 0, r + 0.15, 0.3, segs=28, bev=0.1)                                # the coping
    f.cyl(SOIL, 0, H - 0.1, 0, r - 0.6, 0.25, segs=24, bev=0)
    f.cyl('6a5a48', 0, H, 0, TRUNK, 12.0, segs=12, bev=0.3, r2=TRUNK * 0.67)                   # the trunk
    for (a, h, ln) in ((0.3, 10.0, 6.0), (2.4, 11.5, 5.5), (4.3, 9.5, 6.5)):
        f.rbox('6a5a48', math.sin(a) * ln * 0.45, h + 2.0, math.cos(a) * ln * 0.45, LIMB, LIMB, ln, yaw=a, pitch=-0.6, bev=0.2)
    for (u, v, w, rr) in ((0, 22, 0, 8.0), (5, 19.5, 2, 5.5), (-5, 20, -2, 5.8), (2, 25.5, -3, 5.0), (-2.5, 18.5, 4.5, 5.2), (3, 18.5, -5, 5.0)):
        f.blob(LEAF if rr > 5.4 else LEAF_D, u, v, w, rr, sy=0.72, sub=2)
    for k in range(6):                                                                           # shrubs in the planter
        a = k * math.pi / 3 + 0.4
        f.blob(LEAF_D, math.cos(a) * (r - 1.6), H + 0.6, math.sin(a) * (r - 1.6), 1.2, sy=0.7, sub=1)


def m_planter(f, it):
    W, D, H = f.W, f.D, f.H
    L = f.L
    f.box(L.TEXKEY['brick'], -W / 2, -0.05, -D / 2, W / 2, H, D / 2, bev=0.1)
    f.box(PALE, -W / 2 - 0.1, H - 0.05, -D / 2 - 0.1, W / 2 + 0.1, H + 0.25, D / 2 + 0.1, bev=0.08)
    f.box(SOIL, -W / 2 + 0.4, H + 0.2, -D / 2 + 0.4, W / 2 - 0.4, H + 0.3, D / 2 - 0.4, bev=0)
    for k in range(3):
        f.blob(LEAF if k % 2 else LEAF_D, -W / 2 + 1.5 + k * (W - 3) / 2, H + 1.0, 0, 1.3, sy=0.8, sub=1)


def m_picnic(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(WOOD, -W / 2, H - 0.25, -1.5, W / 2, H, 1.5, bev=0.1)
    for s in (-1, 1):
        f.box(WOOD, -W / 2 + 0.3, 1.4, s * (D / 2 - 0.6) - 0.6, W / 2 - 0.3, 1.6, s * (D / 2 - 0.6) + 0.6, bev=0.08)
    for u in (-W / 2 + 1.2, W / 2 - 1.5):                                                        # A-frames
        for s in (-1, 1):
            f.rbox(WOOD_D, u + 0.15, H / 2 - 0.1, s * 1.1, 0.3, H + 0.4, 0.3, pitch=s * 0.45, bev=0.03)
        f.box(WOOD_D, u, 1.2, -D / 2 + 0.2, u + 0.3, 1.4, D / 2 - 0.2, bev=0.03)


def m_flagpole(f, it):
    H = f.H
    f.cyl(PALE, 0, -0.05, 0, 1.2, 0.6, segs=12, bev=0.1)
    f.cyl(STEEL, 0, 0.5, 0, 0.32, H - 0.5, segs=10, bev=0.05, r2=0.2)
    f.sph(BRASS, 0, H + 0.2, 0, 0.4, segs=8, rings=6)
    x, z = f.P(0.2, 0)
    M = f.K.Tr(x, f.y + H - 5.0, z) @ f.K.Ry(Fr.YAW[f.f] + 0.3)
    f.K.plate(f.m, f.K_ACC, [(0, 0), (6.0, 0.2), (6.2, 3.4), (0, 3.6)], 0.1, M, bev=0.03)


def m_bikerack(f, it):
    g = along(f, it)
    W, D, H = g.W, g.D, g.H
    n = int(W // 1.6)
    for k in range(n):
        u = -W / 2 + 0.8 + k * (W - 1.6) / max(1, n - 1)
        for s in (-1, 1):
            g.box(METAL_D, u - 0.1, -0.05, s * 0.75 - 0.1, u + 0.1, H - 0.3, s * 0.75 + 0.1, bev=0)
        g.box(METAL_D, u - 0.1, H - 0.35, -0.85, u + 0.1, H - 0.15, 0.85, bev=0.05)
    g.box(METAL_D, -W / 2 + 0.6, -0.05, -0.15, W / 2 - 0.6, 0.2, 0.15, bev=0)


def m_shed(f, it):
    """a courtyard shed: brick walls on its hit boxes, the doorway (6 wide, 0.5 to 6.5) facing the courtyard, a low
    pitched roof over the hit roof, a door frame round the opening (outside it: the opening stays clear)"""
    K, L = f.K, f.L
    kind, cx, y, cz, sx, sy, sz, turn, kw = it
    x0, x1, z0, z1 = cx - sx / 2, cx + sx / 2, cz - sz / 2, cz + sz / 2
    BR = L.TEXKEY['brick']
    west = x0 < 0                                   # the west shed: its back on the hall's wall (x0), the door east
    back0, back1 = (x0, x0 + 1.0) if west else (x1 - 1.0, x1)
    fr0, fr1 = (x1 - 1.0, x1) if west else (x0, x0 + 1.0)
    c = cz
    K.B(f.m, BR, back0, 0.0, z0, back1, 10.0, z1, bev=0.05)
    K.B(f.m, BR, x0, 0.0, z0, x1, 10.0, z0 + 1.0, bev=0.05)
    K.B(f.m, BR, x0, 0.0, z1 - 1.0, x1, 10.0, z1, bev=0.05)
    K.B(f.m, BR, fr0, 0.0, z0 + 1.0, fr1, 10.0, c - 3.0, bev=0.03)
    K.B(f.m, BR, fr0, 0.0, c + 3.0, fr1, 10.0, z1 - 1.0, bev=0.03)
    K.B(f.m, BR, fr0, 6.5, c - 3.0, fr1, 10.0, c + 3.0, bev=0.03)
    K.B(f.m, PALE, fr0 - 0.05, 0.0, c - 3.0, fr1 + 0.05, 0.5, c + 3.0, bev=0.03)             # the step
    # the door frame: on the courtyard face, round the opening
    out = fr1 + 0.08 if west else fr0 - 0.08
    a, b = (fr1 - 0.02, out) if west else (out, fr0 + 0.02)
    for (za, zb, ya, yb) in ((c - 3.4, c - 3.0, 0.0, 6.9), (c + 3.0, c + 3.4, 0.0, 6.9), (c - 3.4, c + 3.4, 6.5, 6.9)):
        K.B(f.m, WOOD_D, min(a, b), ya, za, max(a, b), yb, zb, bev=0.03)
    # the inside: dark, a few things stacked (seen through the boards)
    K.B(f.m, '4a4640', x0 + 1.0, -0.02, z0 + 1.0, x1 - 1.0, 0.04, z1 - 1.0, bev=0)
    bx0, bx1 = (x0 + 1.05, x0 + 2.6) if west else (x1 - 2.6, x1 - 1.05)
    K.B(f.m, 'a68a62', bx0, 0.0, z0 + 1.1, bx1, 2.5, z0 + 3.0, bev=0.1)
    K.B(f.m, METAL, bx0, 0.0, z1 - 2.8, bx1, 4.0, z1 - 1.1, bev=0.1)
    # the roof: the hit roof (10 to 11) as a fascia, a low pitch over it, the ridge along z
    K.B(f.m, '6c6862', x0 - 0.5, 10.0, z0 - 0.5, x1 + 0.5, 11.0, z1 + 0.5, bev=0.06)
    xm = (x0 + x1) / 2
    for s in (-1, 1):
        ln = (sx / 2 + 0.9) / math.cos(0.32)
        M = K.Tr(xm + s * (sx / 4 + 0.35), 11.0 + math.tan(0.32) * (sx / 4 + 0.35) + 0.15, cz) @ K.Rz(-s * 0.32)
        K.B(f.m, '5f6b6e', -ln / 2, -0.15, -sz / 2 - 0.9, ln / 2, 0.15, sz / 2 + 0.9, bev=0.05, M=M)
    for zz in (z0 - 0.6, z1 + 0.3):
        K.poly(f.m, '6c6862', [(x0 - 0.5, zz), (x1 + 0.5, zz), (x1 + 0.5, zz + 0.3), (x0 - 0.5, zz + 0.3)], 11.0, 11.2, bev=0.02)


def m_vault(f, it):
    W, D, H = f.W, f.D, f.H
    n = 4
    for k in range(n):
        ins = 0.12 * k
        f.box('a8754a', -W / 2 + ins, -0.05 + k * (H - 0.6) / n, -D / 2 + ins * 0.6, W / 2 - ins, (k + 1) * (H - 0.6) / n, D / 2 - ins * 0.6, bev=0.1)
    f.box('c9b28a', -W / 2 + 0.5, H - 0.62, -D / 2 + 0.3, W / 2 - 0.5, H, D / 2 - 0.3, bev=0.25, segs=2)


def m_mat(f, it):
    W, D, H = f.W, f.D, f.H
    n = 3
    for k in range(n):
        f.box(f.K_ACC, -W / 2 + k * W / n + 0.03, -0.05, -D / 2, -W / 2 + (k + 1) * W / n - 0.03, H, D / 2, bev=0.2, segs=2)


def m_ballrack(f, it):
    W, D, H = f.W, f.D, f.H
    for (u, w) in ((-W / 2, -D / 2), (W / 2 - 0.2, -D / 2), (-W / 2, D / 2 - 0.2), (W / 2 - 0.2, D / 2 - 0.2)):
        f.box(METAL_D, u, -0.05, w, u + 0.2, H, w + 0.2, bev=0)
    for v in (0.3, 1.7):
        f.box(METAL_D, -W / 2, v, -D / 2, W / 2, v + 0.15, D / 2, bev=0)
    n = int((W - 0.4) // 1.25)
    for row, v in enumerate((0.95, 2.35)):
        for k in range(n):
            u = -W / 2 + 0.2 + 0.62 + k * 1.25
            f.sph('b0703f' if (k + row) % 3 else 'c9b28a', u, v, 0, 0.6, segs=12, rings=8)


def m_hoop(f, it):
    """a basketball hoop on the end wall: the bracket, a white backboard with a dark frame, the rim, a net"""
    W, D, H = f.W, f.D, f.H
    f.box(METAL_D, -0.6, 0.5, -D / 2, 0.6, 1.1, D / 2 - 0.3, bev=0.05)                       # bracket
    f.box(WHITE, -W / 2, 0.0, D / 2 - 0.35, W / 2, H, D / 2 - 0.15, bev=0.08)               # backboard
    for (a, b, c, d) in ((-W / 2, H - 0.2, W / 2, H), (-W / 2, 0, W / 2, 0.2), (-W / 2, 0, -W / 2 + 0.2, H), (W / 2 - 0.2, 0, W / 2, H)):
        f.box(DARK, a, b, D / 2 - 0.15, c, d, D / 2 - 0.08, bev=0)
    for (a, b, c, d) in ((-1.0, 1.0, 1.0, 1.15), (-1.0, 1.0, -0.85, 2.3), (0.85, 1.0, 1.0, 2.3), (-1.0, 2.15, 1.0, 2.3)):
        f.box(DARK, a, b, D / 2 - 0.08, c, d, D / 2 - 0.02, bev=0)                           # the shooter's square (lines only)
    x, z = f.P(0, D / 2 + 0.85)
    f.K.ring(f.m, 'b5683e', x, f.y + 0.95, f.y + 1.05, z, 0.75, 0.88, segs=16)
    f.box('b5683e', -0.15, 0.95, D / 2 - 0.15, 0.15, 1.05, D / 2 + 0.1, bev=0)
    f.cyl(WHITE, 0, -0.35, D / 2 + 0.85, 0.5, 1.3, segs=10, bev=0, kind='glass', r2=0.78)


def m_scoreboard(f, it):
    """blank: dark panels, a frame in the accent, two rows of amber lamp dots (no digits)"""
    W, D, H = f.W, f.D, f.H
    f.box(f.K_ACC, -W / 2, 0, -D / 2, W / 2, H, D / 2, bev=0.15)
    f.box(BLACK, -W / 2 + 0.4, 0.4, D / 2 - 0.1, W / 2 - 0.4, H - 0.4, D / 2 + 0.07, bev=0.04)
    for s in (-1, 1):
        f.box(SCREEN, s * W / 4 - 2.4, 1.6, D / 2 + 0.05, s * W / 4 + 2.4, H - 1.0, D / 2 + 0.13, bev=0.03)
    for v in (0.9, H - 0.7):
        for k in range(6):
            u = -W / 2 + 1.6 + k * (W - 3.2) / 5
            f.box('a88a52', u - 0.2, v - 0.2, D / 2 + 0.05, u + 0.2, v + 0.2, D / 2 + 0.16, bev=0, kind='neon')


def m_showers(f, it):
    """tiled shower stalls behind the showerwall (the hit box 0.2-0.4 in front of the item's box): partitions every 4
    along the run, heads on the back wall, a tiled front wall"""
    W, D, H = f.W, f.D, f.H
    L = f.L
    TILE = L.TEXKEY['rtile_wall']
    f.box(TILE, -W / 2, -0.05, D / 2 + 0.0, W / 2, H, D / 2 + 0.4, bev=0.04)                # the showerwall
    n = max(1, int(W // 4))
    for k in range(1, n):
        u = -W / 2 + k * W / n
        f.box(PALE, u - 0.15, 0.5, -D / 2, u + 0.15, H - 0.5, D / 2 - 2.6, bev=0.04)
    for k in range(n):
        u = -W / 2 + (k + 0.5) * W / n
        f.box(STEEL, u - 0.08, 5.6, -D / 2, u + 0.08, 5.75, -D / 2 + 0.8, bev=0)
        f.cyl(STEEL, u, 5.4, -D / 2 + 0.8, 0.3, 0.25, segs=8, bev=0)
        f.cyl(METAL_D, u, -0.04, -D / 2 + 1.6, 0.25, 0.06, segs=8, bev=0)
        f.cyl(STEEL, u, 3.4, -D / 2 + 0.1, 0.18, 0.2, segs=6, bev=0)


def m_weightbench(f, it):
    g = along(f, it)
    W, D, H = g.W, g.D, g.H
    g.box(DARK, -W / 2 + 0.6, H - 0.5, -0.65, W / 2 - 0.2, H, 0.65, bev=0.18, segs=2)        # the pad
    for u in (-W / 2 + 1.0, W / 2 - 1.0):
        g.box(METAL_D, u - 0.2, -0.05, -0.9, u + 0.2, H - 0.45, 0.9, bev=0)
    for s in (-1, 1):                                                                          # the rack uprights
        g.box(METAL_D, -W / 2 + 0.05, -0.05, s * 0.95 - 0.12, -W / 2 + 0.3, 3.6, s * 0.95 + 0.12, bev=0)
    g.cylw(STEEL, -D / 2 - 1.2, D / 2 + 1.2, 3.45, -W / 2 + 0.18, 0.1, segs=6, bev=0)         # the bar
    for s in (-1, 1):
        g.cylw(DARK, s * (D / 2 + 0.55) - 0.25, s * (D / 2 + 0.55) + 0.25, 3.45, -W / 2 + 0.18, 0.75, segs=12, bev=0.05)


def m_rack(f, it):
    """a dumbbell rack: two sloped tiers of hex dumbbells"""
    W, D, H = f.W, f.D, f.H
    for u in (-W / 2, W / 2 - 0.3, 0.0 - 0.15):
        f.box(METAL_D, u, -0.05, -D / 2, u + 0.3, 3.4, D / 2, bev=0.03)
    for (v, w0, w1) in ((1.4, -D / 2, D / 2), (2.8, -D / 2 + 0.3, D / 2 - 0.5)):
        f.box(METAL_D, -W / 2, v, w0, W / 2, v + 0.15, w1, bev=0)
        n = int((W - 0.6) // 1.4)
        for k in range(n):
            u = -W / 2 + 0.7 + k * 1.4
            s = 0.28 + 0.03 * k
            f.box(DARK, u - s, v + 0.15, w0 + 0.15, u + s, v + 0.15 + 2 * s, w0 + 0.55, bev=0)
            f.box(DARK, u - s, v + 0.15, w1 - 0.55, u + s, v + 0.15 + 2 * s, w1 - 0.15, bev=0)
            f.box(STEEL, u - 0.07, v + 0.15 + s - 0.07, w0 + 0.55, u + 0.07, v + 0.15 + s + 0.07, w1 - 0.55, bev=0)
    if H > 4:                                                                                    # a mirror strip on top
        f.box(MIRROR, -W / 2 + 0.2, 3.6, -D / 2 + 0.2, W / 2 - 0.2, H - 0.1, -D / 2 + 0.4, bev=0.02)


def m_crate(f, it):
    W, D, H = f.W, f.D, f.H
    f.box('a68a62', -W / 2 + 0.12, -0.05, -D / 2 + 0.12, W / 2 - 0.12, H - 0.12, D / 2 - 0.12, bev=0.05)
    for (a, b) in ((-W / 2, -D / 2), (W / 2 - 0.3, -D / 2), (-W / 2, D / 2 - 0.3), (W / 2 - 0.3, D / 2 - 0.3)):
        f.box(WOOD_D, a, -0.05, b, a + 0.3, H, b + 0.3, bev=0.04)
    for v in (-0.05, H - 0.3):
        f.box(WOOD_D, -W / 2, v, -D / 2, W / 2, v + 0.3, -D / 2 + 0.3, bev=0.04)
        f.box(WOOD_D, -W / 2, v, D / 2 - 0.3, W / 2, v + 0.3, D / 2, bev=0.04)


def m_workbench(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(WOOD, -W / 2, H - 0.3, -D / 2, W / 2, H, D / 2, bev=0.06)
    f.legs(METAL_D, -W / 2 + 0.1, -D / 2 + 0.1, W / 2 - 0.1, D / 2 - 0.1, H - 0.28, t=0.3)
    f.box(METAL_D, -W / 2 + 0.3, 0.5, -D / 2 + 0.2, W / 2 - 0.3, 0.7, D / 2 - 0.2, bev=0)
    f.box('9a8a6c', -W / 2, H, -D / 2 - 0.05, W / 2, H + 3.2, -D / 2 + 0.15, bev=0.04)          # pegboard
    rnd = random.Random(int(it[1] * 3 + it[3]))
    for k in range(int(W // 1.6)):
        u = -W / 2 + 0.8 + k * 1.6
        f.box(rnd.choice((METAL_D, DARK, 'a8754a')), u - 0.1, H + 1.0 + rnd.random(), -D / 2 + 0.14, u + 0.1, H + 2.2 + rnd.random(), -D / 2 + 0.3, bev=0)
    f.box(METAL_D, W / 2 - 2.2, H, D / 2 - 1.2, W / 2 - 1.0, H + 0.8, D / 2 - 0.2, bev=0.08)      # a vise
    f.box('8a4f4a', -W / 2 + 1.0, H, -0.6, -W / 2 + 3.0, H + 0.9, 0.6, bev=0.1)                    # a toolbox


def m_boiler(f, it):
    """a big rounded boiler: a plinth, the body, a burner box with gauges at the front, a flue to the ceiling"""
    W, D, H = f.W, f.D, f.H
    f.box('4e4a46', -W / 2, -0.05, -D / 2, W / 2, 0.8, D / 2, bev=0.15)
    f.box('6e5a52', -W / 2 + 0.2, 0.8, -D / 2 + 0.2, W / 2 - 0.2, H, D / 2 - 1.2, bev=1.2, segs=2)
    f.box(METAL_D, -W / 2 + 1.5, 0.8, D / 2 - 1.3, W / 2 - 1.5, 5.0, D / 2, bev=0.2)               # the burner
    for u in (-2.5, 0.0, 2.5):                                                                  # gauge faces
        x, z = f.P(u, D / 2 - 0.02)
        M = f.K.Tr(x, f.y + 4.0, z) @ f.K.Ry(Fr.YAW[f.f]) @ f.K.Rx(math.pi / 2)
        f.K.cyl(f.m, PALE, 0, -0.06, 0, 0.55, 0.12, segs=12, bev=0.02, M=M)
    f.cyl(METAL, 0, H - 0.2, -1.0, 1.2, 7.0 if f.y < -8 else 3.0, segs=12, bev=0.1)              # the flue
    f.cylu(METAL, -W / 2 - 0.3, W / 2 + 0.3, 2.2, -D / 2 + 1.2, 0.45, segs=10)                    # pipes out the side


def m_heater(f, it):
    W, D, H = f.W, f.D, f.H
    f.cyl('9aa0a6', 0, -0.05, 0, W / 2 - 0.1, H - 0.6, segs=14, bev=0.25)
    f.cyl('9aa0a6', 0, H - 0.7, 0, W / 2 - 0.4, 0.7, segs=14, bev=0.25, r2=0.6)
    f.cyl(METAL, 0, H - 0.1, 0, 0.5, 6.0 if f.y < -8 else 1.0, segs=8, bev=0)
    f.cylu(BRASS, -W / 2 - 0.5, 0, 3.0, 0, 0.18, segs=6, bev=0)


def m_generator(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(METAL_D, -W / 2, -0.05, -D / 2, W / 2, 0.5, D / 2, bev=0.06)                          # skids
    f.box('5f6b5a', -W / 2 + 0.2, 0.5, -D / 2 + 0.2, W / 2 - 1.6, H - 0.4, D / 2 - 0.2, bev=0.35, segs=2)
    f.box(DARK, W / 2 - 1.5, 0.5, -D / 2 + 0.6, W / 2 - 0.1, H - 1.2, D / 2 - 0.6, bev=0.15)      # the panel
    f.box('a88a52', W / 2 - 1.3, H - 2.0, D / 2 - 0.6, W / 2 - 0.5, H - 1.6, D / 2 - 0.54, kind='neon', bev=0)
    f.cyl(METAL, -W / 2 + 1.0, H - 0.45, -D / 2 + 1.0, 0.35, 2.5, segs=8, bev=0)


def m_pipes(f, it):
    """look-only pipe runs under the ceiling: two runs along the item's long side, hangers"""
    kind, cx, y, cz, sx, sy, sz, turn, kw = it
    K = f.K
    along_x = sx >= sz
    ln = max(sx, sz)
    for (off, r, c) in ((-0.6, 0.55, '8e969c'), (0.7, 0.35, 'a8754a')):
        if along_x: K.cylx(f.m, c, cx - ln / 2, cx + ln / 2, y + sy / 2, cz + off, r, segs=10, bev=0)
        else: K.cylz(f.m, c, cz - ln / 2, cz + ln / 2, cx + off, y + sy / 2, r, segs=10, bev=0)
    for k in range(int(ln // 8) + 1):                     # hangers: a thin rod per pipe up to the ceiling, a strap under
        t = -ln / 2 + k * ln / max(1, int(ln // 8))
        for (off, r) in ((-0.6, 0.55), (0.7, 0.35)):
            yc = y + sy / 2
            if along_x:
                K.B(f.m, METAL_D, cx + t - 0.07, yc, cz + off - 0.07, cx + t + 0.07, yc + 3.4, cz + off + 0.07, bev=0)
                K.B(f.m, METAL_D, cx + t - 0.1, yc - r - 0.12, cz + off - r - 0.05, cx + t + 0.1, yc - r, cz + off + r + 0.05, bev=0)
            else:
                K.B(f.m, METAL_D, cx + off - 0.07, yc, cz + t - 0.07, cx + off + 0.07, yc + 3.4, cz + t + 0.07, bev=0)
                K.B(f.m, METAL_D, cx + off - r - 0.05, yc - r - 0.12, cz + t - 0.1, cx + off + r + 0.05, yc - r, cz + t + 0.1, bev=0)


def m_bookshelf(f, it):
    """a library stack (double-sided when it stands free) or a bookcase against a wall: rows of book blocks"""
    kind, cx, y, cz, sx, sy, sz, turn, kw = it
    W, D, H = (sx, sz, sy) if sx >= sz else (sz, sx, sy)
    face = f.f
    double = D >= 2.0 and _free(f, it)
    g = Fr(f.K, f.m, cx, y, cz, ('s' if sx >= sz else 'e') if double else face, W, D, H); g.K_ACC, g.L = f.K_ACC, f.L
    g.box(WOOD_D, -W / 2, -0.05, -D / 2, -W / 2 + 0.3, H, D / 2, bev=0.06)                        # end panels
    g.box(WOOD_D, W / 2 - 0.3, -0.05, -D / 2, W / 2, H, D / 2, bev=0.06)
    g.box(WOOD_D, -W / 2, H - 0.3, -D / 2, W / 2, H, D / 2, bev=0.08)                             # top
    g.box(WOOD_D, -W / 2 + 0.3, -0.05, -0.1 if double else -D / 2, W / 2 - 0.3, H - 0.3, 0.1 if double else -D / 2 + 0.15, bev=0)  # the spine
    rnd = random.Random(int(cx * 7 + cz * 3))
    sides = (-1, 1) if double else (1,)
    nshelf = 4
    for k in range(nshelf):
        v = 0.25 + k * (H - 0.55) / nshelf
        g.box(WOOD, -W / 2 + 0.3, v - 0.12, -D / 2 + 0.05, W / 2 - 0.3, v + 0.04, D / 2 - 0.05, bev=0)
        for s in sides:
            u = -W / 2 + 0.4
            while u < W / 2 - 0.55:
                bw = min(0.6 + rnd.random() * 1.0, W / 2 - 0.4 - u)
                bh = (H - 0.55) / nshelf * (0.55 + rnd.random() * 0.35)
                if rnd.random() < 0.08: u += bw; continue
                w0, w1 = (0.15, D / 2 - 0.12 - rnd.random() * 0.15) if s > 0 else (-D / 2 + 0.12 + rnd.random() * 0.15, -0.15)
                if not double: w0, w1 = -D / 2 + 0.2, D / 2 - 0.12 - rnd.random() * 0.15
                g.box(rnd.choice(BOOKS), u, v + 0.04, w0, u + bw - 0.06, v + 0.04 + bh, w1, bev=0)
                u += bw


def _free(f, it):
    """a piece standing free (more than 3 studs from its room's walls on its long sides)"""
    kind, cx, y, cz, sx, sy, sz, turn, kw = it
    L = f.L
    lv = level_of(kind, y)
    r = L.room_at(lv, cx, cz)
    if r is None: return True
    x0, z0, x1, z1 = r['r']
    if sx < sz: return min(cx - sx / 2 - x0, x1 - cx - sx / 2) > 3.0
    return min(cz - sz / 2 - z0, z1 - cz - sz / 2) > 3.0


def m_readtable(f, it):
    g = along(f, it)
    W, D, H = g.W, g.D, g.H
    g.box(WOOD, -W / 2 + 0.2, H - 0.25, -D / 2 + 0.7, W / 2 - 0.2, H, D / 2 - 0.7, bev=0.1, segs=2)
    g.legs(WOOD_D, -W / 2 + 0.4, -D / 2 + 0.9, W / 2 - 0.4, D / 2 - 0.9, H - 0.24, t=0.3)
    for u in (-W / 4, W / 4):
        for s in (-1, 1):
            chair(g, u, s * (D / 2 - 0.75), 'front' if s < 0 else 'back', seat=1.55, back=3.1, cw=1.5)
    g.box(BOOKS[1], -1.0, H - 0.05, -0.4, 0.2, H + 0.25, 0.5, bev=0.04)


def m_globe(f, it):
    W, D, H = f.W, f.D, f.H
    f.cyl(WOOD_D, 0, -0.05, 0, W / 2 - 0.1, 0.3, segs=10, bev=0.08)
    f.cyl(WOOD_D, 0, 0.2, 0, 0.18, H - 1.9, segs=6, bev=0)
    f.sph('6d8fa0', 0, H - 1.0, 0, 0.95, segs=16, rings=10)
    f.blob('8a9a6a', 0.35, H - 0.8, 0.55, 0.45, sy=0.8, sub=1)
    f.blob('8a9a6a', -0.5, H - 1.3, 0.4, 0.4, sy=0.8, sub=1)
    x, z = f.P(0, 0)
    f.K.ring(f.m, BRASS, x, f.y + H - 1.06, f.y + H - 0.94, z, 1.02, 1.12, segs=18)


def m_arttable(f, it):
    W, D, H = f.W, f.D, f.H
    f.box('d9cfb8', -W / 2, H - 0.3, -D / 2, W / 2, H, D / 2, bev=0.08)
    f.legs(WOOD_D, -W / 2 + 0.2, -D / 2 + 0.2, W / 2 - 0.2, D / 2 - 0.2, H - 0.28, t=0.35)
    f.box(WOOD_D, -W / 2 + 0.5, 0.5, -D / 2 + 0.5, W / 2 - 0.5, 0.7, D / 2 - 0.5, bev=0)
    rnd = random.Random(int(it[1] * 5 + it[3] * 7))
    for k in range(4):                                                                             # paint pots, a brush jar
        u, w = -W / 2 + 1.0 + rnd.random() * (W - 2), -D / 2 + 0.8 + rnd.random() * (D - 1.6)
        f.cyl(rnd.choice(('a35a4e', '4f6b8a', 'c2a44e', f.K_ACC, PALE)), u, H - 0.05, w, 0.3, 0.45, segs=8, bev=0.03)
    f.box(CREAM, -1.5, H - 0.02, -0.8, 1.2, H + 0.06, 0.9, bev=0)                                 # a sheet of paper


def m_easel(f, it):
    W, D, H = f.W, f.D, f.H
    for s in (-1, 1):
        f.rbox(WOOD, s * 0.85, H / 2 - 0.1, 0.2, 0.18, H + 0.2, 0.18, roll=s * 0.12, pitch=0.08, bev=0)
    f.rbox(WOOD, 0, H / 2 - 0.2, -0.5, 0.18, H, 0.18, pitch=-0.25, bev=0)
    f.box(WOOD, -1.2, 1.9, 0.3, 1.2, 2.05, 0.6, bev=0)                                           # the ledge
    f.rbox(CREAM, 0, 3.15, 0.38, 2.2, 2.5, 0.12, pitch=0.08, bev=0.04)                           # a blank canvas


def m_kiln(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(METAL_D, -W / 2 + 0.3, -0.05, -D / 2 + 0.3, W / 2 - 0.3, 1.0, D / 2 - 0.3, bev=0.04)   # the stand
    f.cyl('9aa0a6', 0, 1.0, 0, W / 2 - 0.1, H - 1.6, segs=8, bev=0.15)                             # octagonal body
    f.cyl(METAL_D, 0, H - 0.65, 0, W / 2 - 0.05, 0.5, segs=8, bev=0.1)                             # the lid
    f.box(DARK, -0.8, 1.8, W / 2 - 0.4, 0.8, 3.0, W / 2 + 0.05, bev=0.05)                         # the controller
    f.box('a88a52', -0.2, 2.6, W / 2, 0.2, 2.8, W / 2 + 0.1, kind='neon', bev=0)


def m_drying(f, it):
    W, D, H = f.W, f.D, f.H
    for u in (-W / 2, W / 2 - 0.25):
        f.box(METAL_D, u, -0.05, -D / 2, u + 0.25, H, D / 2, bev=0.03)
    for k in range(12):
        v = 0.8 + k * (H - 1.2) / 12
        f.box(STEEL, -W / 2 + 0.25, v, -D / 2 + 0.1, W / 2 - 0.25, v + 0.06, D / 2 - 0.1, bev=0)
        if k % 3 != 1: f.box(CREAM, -W / 2 + 0.6, v + 0.06, -D / 2 + 0.25, W / 2 - 0.6, v + 0.1, D / 2 - 0.4, bev=0)


def m_counter(f, it):
    """the front office's counter (long, facing the visitors) or the lounge's kitchenette (sink, coffee machine)"""
    W, D, H = f.W, f.D, f.H
    f.box(WOOD, -W / 2, -0.05, -D / 2, W / 2, H - 0.25, D / 2 - 0.1, bev=0.1)
    f.box(CREAM, -W / 2, H - 0.25, -D / 2, W / 2, H, D / 2, bev=0.08)
    f.box(METAL_D, -W / 2 + 0.2, -0.05, D / 2 - 0.25, W / 2 - 0.2, 0.4, D / 2 - 0.05, bev=0.02)
    if W > 12:                                                                                      # front office: a
        f.box(f.K_ACC, -W / 2 + 0.3, 1.2, D / 2 - 0.12, W / 2 - 0.3, 1.45, D / 2 + 0.06, bev=0.03)  # band, monitors
        for u in (-6.0, 2.0):
            f.box(SCREEN, u - 1.0, H + 0.4, -D / 2 + 0.3, u + 1.0, H + 1.6, -D / 2 + 0.5, bev=0.05)
            f.box(DARK, u - 0.15, H - 0.05, -D / 2 + 0.35, u + 0.15, H + 0.45, -D / 2 + 0.6, bev=0)
        f.box(PALE, 7.0, H, -0.3, 9.0, H + 0.1, 1.0, bev=0.02)
    else:                                                                                           # the kitchenette
        f.box(STEEL, -0.8, H - 0.05, -D / 2 + 0.5, 0.8, H + 0.02, D / 2 - 0.5, bev=0.02)        # the sink
        f.cyl(STEEL, 0, H - 0.05, -D / 2 + 0.3, 0.1, 1.3, segs=6, bev=0)
        f.box(DARK, -W / 2 + 1.0, H - 0.05, -D / 2 + 0.3, -W / 2 + 2.6, H + 1.8, D / 2 - 0.6, bev=0.12)  # coffee machine
        f.cyl(PALE, -W / 2 + 1.8, H + 0.3, D / 2 - 0.45, 0.25, 0.5, segs=8, bev=0.03)
        f.box(WOOD, -W / 2, 7.0, -D / 2, W / 2, 9.5, -D / 2 + 1.6, bev=0.1)                         # upper cabinets
        f.box(PALE, -W / 2 + 0.1, 8.0, -D / 2 + 1.55, W / 2 - 0.1, 8.2, -D / 2 + 1.67, bev=0)


def m_chair(f, it):
    W, D, H = f.W, f.D, f.H
    chair(f, 0, 0, 'front', seat=1.55, back=H, cw=min(W, D))


def m_filing(f, it):
    W, D, H = f.W, f.D, f.H
    n = max(1, int(W // 2.9))
    for k in range(n):
        u0 = -W / 2 + k * W / n + 0.05
        u1 = u0 + W / n - 0.1
        f.box('8e969c', u0, -0.05, -D / 2, u1, H, D / 2 - 0.08, bev=0.08)
        for j in range(3):
            v0 = 0.2 + j * (H - 0.3) / 3
            f.box('a4abb0', u0 + 0.1, v0, D / 2 - 0.12, u1 - 0.1, v0 + (H - 0.3) / 3 - 0.12, D / 2 - 0.02, bev=0.04)
            f.box(DARK, (u0 + u1) / 2 - 0.4, v0 + 0.7, D / 2 - 0.05, (u0 + u1) / 2 + 0.4, v0 + 0.85, D / 2 + 0.07, bev=0)


def m_bigdesk(f, it):
    """the principal's desk: a heavy top with an inset leather pad, pedestals both sides, a lamp, a closed laptop"""
    W, D, H = f.W, f.D, f.H
    f.box(WOOD_D, -W / 2, H - 0.3, -D / 2, W / 2, H, D / 2, bev=0.15, segs=2)
    f.box(f.K_ACC, -W / 2 + 1.5, H - 0.05, -D / 2 + 0.6, W / 2 - 1.5, H + 0.04, D / 2 - 1.0, bev=0)
    for s in (-1, 1):
        u0 = -W / 2 + 0.15 if s < 0 else W / 2 - 2.8
        f.box(WOOD_D, u0, -0.05, -D / 2 + 0.15, u0 + 2.65, H - 0.28, D / 2 - 0.15, bev=0.08)
        for j in range(3):
            v0 = 0.25 + j * 0.75
            f.box(WOOD, u0 + 0.15, v0, -D / 2 + 0.05, u0 + 2.5, v0 + 0.62, -D / 2 + 0.16, bev=0.04)
    f.box(WOOD_D, -W / 2 + 2.8, 0.4, D / 2 - 0.4, W / 2 - 2.8, H - 0.3, D / 2 - 0.15, bev=0.05)
    f.cyl(BRASS, W / 2 - 1.2, H - 0.05, -D / 2 + 1.0, 0.4, 0.15, segs=10, bev=0.03)                # the lamp
    f.cyl(BRASS, W / 2 - 1.2, H + 0.1, -D / 2 + 1.0, 0.07, 1.6, segs=6, bev=0)
    f.cyl('cfc4a4', W / 2 - 1.2, H + 1.5, -D / 2 + 1.0, 0.6, 0.7, segs=10, bev=0.05, r2=0.35)                # (a shade, not a glow)
    f.cyl('8a7350', W / 2 - 1.2, H + 1.55, -D / 2 + 1.0, 0.18, 0.3, segs=8, bev=0, kind='neon')
    f.box(DARK, -1.2, H - 0.02, -0.4, 0.8, H + 0.12, 0.9, bev=0.04)                              # a closed laptop


def m_bigchair(f, it):
    W, D, H = f.W, f.D, f.H
    f.cyl(METAL_D, 0, -0.05, 0, 1.0, 0.25, segs=5, bev=0.05)
    f.cyl(METAL, 0, 0.2, 0, 0.15, 1.2, segs=6, bev=0)
    f.box('3f4446', -W / 2 + 0.1, 1.3, -D / 2 + 0.2, W / 2 - 0.1, 1.85, D / 2 - 0.1, bev=0.2, segs=2)
    f.box('3f4446', -W / 2 + 0.2, 1.8, -D / 2, W / 2 - 0.2, H + 1.6, -D / 2 + 0.45, bev=0.2, segs=2)
    for s in (-1, 1):
        f.box(METAL_D, s * (W / 2 - 0.15) - 0.12, 1.8, -D / 2 + 0.6, s * (W / 2 - 0.15) + 0.12, 2.5, D / 2 - 0.3, bev=0.05)


def m_couch(f, it):
    W, D, H = f.W, f.D, f.H
    col = '5f7378'
    f.box(DARK, -W / 2 + 0.3, -0.05, -D / 2 + 0.3, W / 2 - 0.3, 0.35, D / 2 - 0.3, bev=0.03)
    f.box(col, -W / 2, 0.3, -D / 2, W / 2, 1.2, D / 2, bev=0.25, segs=2)                          # base
    for k in range(3):
        u0 = -W / 2 + 0.8 + k * (W - 1.6) / 3
        f.box(col, u0 + 0.04, 1.15, -D / 2 + 1.0, u0 + (W - 1.6) / 3 - 0.04, 1.65, D / 2 - 0.05, bev=0.22, segs=2)
    f.box(col, -W / 2, 1.15, -D / 2, W / 2, H, -D / 2 + 1.0, bev=0.3, segs=2)                     # back
    for s in (-1, 1):
        f.box(col, s * W / 2 - (0.8 if s > 0 else 0), 1.15, -D / 2, s * W / 2 + (0.8 if s < 0 else 0), 2.1, D / 2, bev=0.25, segs=2)


def m_coffeetable(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(WOOD, -W / 2, H - 0.25, -D / 2, W / 2, H, D / 2, bev=0.1)
    f.legs(WOOD_D, -W / 2 + 0.2, -D / 2 + 0.2, W / 2 - 0.2, D / 2 - 0.2, H - 0.24, t=0.3)
    f.box(BOOKS[0], -1.5, H - 0.05, -0.5, -0.2, H + 0.25, 0.6, bev=0.04)


def m_table(f, it):
    g = along(f, it)
    W, D, H = g.W, g.D, g.H
    g.box(WOOD_L, -W / 2 + 0.3, H - 0.25, -D / 2 + 0.9, W / 2 - 0.3, H, D / 2 - 0.9, bev=0.1)
    g.legs(WOOD_D, -W / 2 + 0.5, -D / 2 + 1.1, W / 2 - 0.5, D / 2 - 1.1, H - 0.24, t=0.3)
    for u in (-W / 4, W / 4):
        for s in (-1, 1):
            chair(g, u, s * (D / 2 - 0.8), 'front' if s < 0 else 'back', seat=1.55, back=3.1, cw=1.6)


def m_computers(f, it):
    """a row of computer desks: monitors (blank, dark), keyboards, towers under, chairs tucked in at the front"""
    W, D, H = f.W, f.D, f.H
    f.box(PALE, -W / 2, H - 0.22, -D / 2, W / 2, H, D / 2 - 0.9, bev=0.08)
    n = max(1, int(W // 3.4))
    for k in range(n + 1):
        u = -W / 2 + 0.1 + k * (W - 0.4) / n
        f.box(METAL_D, u, -0.05, -D / 2 + 0.1, u + 0.25, H - 0.2, D / 2 - 1.0, bev=0)
    for k in range(n):
        u = -W / 2 + (k + 0.5) * W / n
        f.box(DARK, u - 0.15, H - 0.05, -D / 2 + 0.3, u + 0.15, H + 0.5, -D / 2 + 0.55, bev=0)
        f.box(SCREEN, u - 1.1, H + 0.35, -D / 2 + 0.25, u + 1.1, H + 1.75, -D / 2 + 0.45, bev=0.06)
        f.box(PALE, u - 0.9, H - 0.04, -D / 2 + 1.0, u + 0.9, H + 0.06, -D / 2 + 1.6, bev=0)
        f.box(DARK, u + 0.6, -0.05, -D / 2 + 0.3, u + 1.2, 1.5, -D / 2 + 1.6, bev=0)
        chair(f, u, D / 2 - 0.85, 'back', seat=1.55, back=3.0, cw=1.6)


def m_piano(f, it):
    W, D, H = f.W, f.D, f.H
    f.box('2f2f33', -W / 2, -0.05, -D / 2, W / 2, H, -D / 2 + 1.6, bev=0.12, segs=2)            # the body
    f.box('2f2f33', -W / 2, 2.2, -D / 2 + 1.5, W / 2, 2.5, D / 2 - 0.4, bev=0.06)                 # the key bed
    f.box(WHITE, -W / 2 + 0.4, 2.45, -D / 2 + 1.55, W / 2 - 0.4, 2.6, D / 2 - 0.5, bev=0.02)
    for k in range(14):
        u = -W / 2 + 0.6 + k * (W - 1.2) / 14
        if k % 7 in (2, 6): continue
        f.box(BLACK, u, 2.58, -D / 2 + 1.55, u + 0.18, 2.72, -D / 2 + 2.0, bev=0)
    for s in (-1, 1):
        f.box('2f2f33', s * (W / 2 - 0.25) - 0.25, -0.05, -D / 2 + 1.5, s * (W / 2 - 0.25) + 0.25, 2.3, D / 2 - 0.2, bev=0.06)
    f.box(BRASS, -0.6, 0.3, -D / 2 + 1.55, 0.6, 0.4, -D / 2 + 1.75, bev=0)                       # pedals rail


def m_riser(f, it):
    W, D, H = f.W, f.D, f.H
    L = f.L
    f.box(WOOD_D, -W / 2, -0.05, -D / 2, W / 2, H - 0.15, D / 2, bev=0.06)
    f.box(L.TEXKEY['woodfloor'], -W / 2 + 0.05, H - 0.2, -D / 2 + 0.05, W / 2 - 0.05, H, D / 2 - 0.05, bev=0.03)
    f.box(f.K_ACC, -W / 2 + 0.1, 0.1, D / 2 - 0.02, W / 2 - 0.1, 0.3, D / 2 + 0.07, bev=0.02)


def m_hvac(f, it):
    """a rooftop unit: a curb, the cabinet with louvres down its long sides, a fan grille on top"""
    W, D, H = f.W, f.D, f.H
    f.box(METAL_D, -W / 2 + 0.3, -0.05, -D / 2 + 0.3, W / 2 - 0.3, 0.8, D / 2 - 0.3, bev=0.05)
    f.box('a9aeb0', -W / 2, 0.8, -D / 2, W / 2, H, D / 2, bev=0.3, segs=2)
    for s in (-1, 1):
        w0, w1 = (D / 2 - 0.05, D / 2 + 0.1) if s > 0 else (-D / 2 - 0.1, -D / 2 + 0.05)
        for k in range(6):
            v = 1.4 + k * 0.7
            f.box('8e9496', -W / 2 + 1.0, v, w0, W / 2 - 5.0, v + 0.35, w1, bev=0)
    x, z = f.P(W / 2 - 3.0, 0)
    f.K.ring(f.m, METAL_D, x, f.y + H - 0.05, f.y + H + 0.4, z, 1.9, 2.3, segs=18)
    f.cyl(DARK, W / 2 - 3.0, H - 0.05, 0, 1.9, 0.2, segs=18, bev=0)
    for a in (0.0, math.pi / 2):
        f.rbox(METAL_D, W / 2 - 3.0, H + 0.3, 0, 3.8, 0.12, 0.2, yaw=a, bev=0)
    f.box(METAL, -W / 2 + 1.5, -0.05, -D / 2 - 1.6, -W / 2 + 3.5, 2.0, -D / 2 + 0.2, bev=0.1)    # a duct into the roof


def m_greenhouse(f, it):
    """a framed glass house on the roof: its walls' glass on the layout's greenglass hit boxes, a pitched glass roof,
    raised plant beds; the doorway in its east wall between z -62 and -50"""
    K = f.K
    kind, cx, y, cz, sx, sy, sz, turn, kw = it
    x0, x1, z0, z1 = cx - sx / 2, cx + sx / 2, cz - sz / 2, cz + sz / 2       # -115..-93, -71..-41
    G, FR = 'b9d8c2', '4f5c56'
    top = y + 11.0
    panes = [(-115, -71, -93, -70.6), (-115, -41.4, -93, -41), (-115.4, -71, -115, -41), (-93, -71, -92.6, -62), (-93, -50, -92.6, -41)]
    for (a, b, c, d) in panes:
        K.B(f.m, G, a, y, b, c, top, d, bev=0, kind='glass')
    # the sill walls round the glass's foot (the panes: north z -71..-70.6, south -41.4..-41, west x -115.4..-115,
    # east -93..-92.6 with the doorway z -62..-50)
    K.B(f.m, FR, x0 - 0.6, y - 0.05, z0 - 0.2, x1 + 0.6, y + 1.2, z0 + 0.6, bev=0.05)
    K.B(f.m, FR, x0 - 0.6, y - 0.05, z1 - 0.6, x1 + 0.6, y + 1.2, z1 + 0.2, bev=0.05)
    K.B(f.m, FR, x0 - 0.6, y - 0.05, z0 + 0.6, x0 + 0.2, y + 1.2, z1 - 0.6, bev=0.05)
    for (za, zb) in ((z0 + 0.6, -62.0), (-50.0, z1 - 0.6)):
        K.B(f.m, FR, x1 - 0.2, y - 0.05, za, x1 + 0.6, y + 1.2, zb, bev=0.05)
    # mullions straddling the panes every few studs, a top plate
    for k in range(9):
        xx = x0 + k * sx / 8
        for (za, zb) in ((z0 - 0.08, z0 + 0.48), (z1 - 0.48, z1 + 0.08)):
            K.B(f.m, FR, xx - 0.15, y, za, xx + 0.15, top, zb, bev=0)
    for k in range(11):
        zz = z0 + k * sz / 10
        K.B(f.m, FR, x0 - 0.48, y, zz - 0.15, x0 + 0.08, top, zz + 0.15, bev=0)
        if not (-62.5 < zz < -49.5): K.B(f.m, FR, x1 - 0.08, y, zz - 0.15, x1 + 0.48, top, zz + 0.15, bev=0)
    for zz in (-62.0, -50.0):
        K.B(f.m, FR, x1 - 0.1, y, zz - 0.2, x1 + 0.5, top, zz + 0.2, bev=0.02)                 # the door posts
    K.B(f.m, FR, x0 - 0.5, top, z0 - 0.5, x1 + 0.5, top + 0.4, z1 + 0.5, bev=0.05)              # the top plate
    # the pitched glass roof, ridge along z
    pitch = 0.42
    half = sx / 2 + 0.5
    ln = half / math.cos(pitch)
    for s in (-1, 1):
        M = K.Tr(cx + s * half / 2, top + 0.4 + math.tan(pitch) * half / 2, cz) @ K.Rz(-s * pitch)
        K.B(f.m, G, -ln / 2, -0.08, -sz / 2 - 0.5, ln / 2, 0.08, sz / 2 + 0.5, bev=0, kind='glass', M=M)
        for k in range(6):
            zz = z0 - 0.5 + k * (sz + 1.0) / 5
            M2 = K.Tr(cx + s * half / 2, top + 0.4 + math.tan(pitch) * half / 2 + 0.12, zz) @ K.Rz(-s * pitch)
            K.B(f.m, FR, -ln / 2, -0.1, -0.15, ln / 2, 0.1, 0.15, bev=0, M=M2)
    K.B(f.m, FR, cx - 0.25, top + 0.4 + math.tan(pitch) * half, z0 - 0.5, cx + 0.25, top + 0.75 + math.tan(pitch) * half, z1 + 0.5, bev=0.05)
    # plant beds inside: two long raised beds and plants
    rnd = random.Random(41)
    for (bx0, bx1) in ((x0 + 1.0, x0 + 5.0), (x1 - 9.0, x1 - 5.0)):
        K.B(f.m, WOOD_D, bx0, y - 0.05, z0 + 2.0, bx1, y + 2.4, z1 - 2.0, bev=0.1)
        K.B(f.m, SOIL, bx0 + 0.3, y + 2.3, z0 + 2.3, bx1 - 0.3, y + 2.5, z1 - 2.3, bev=0)
        zz = z0 + 3.5
        while zz < z1 - 3.0:
            K.blob(f.m, LEAF if rnd.random() < 0.6 else LEAF_D, (bx0 + bx1) / 2 + rnd.uniform(-0.6, 0.6), y + 3.3, zz, 1.0 + rnd.random() * 0.5, sy=0.8, sub=1)
            zz += 2.4
    K.B(f.m, WOOD, x0 + 7.0, y - 0.05, z0 + 2.0, x0 + 10.0, y + 2.6, z0 + 8.0, bev=0.08)       # a potting bench
    for k in range(3):
        K.cyl(f.m, POT, x0 + 8.5, y + 2.55, z0 + 3.0 + k * 1.8, 0.5, 0.7, segs=8, bev=0.04)


def m_towerleg(f, it):
    """a leg of the water tower (the tank, braces and ladder: watertank)"""
    W, D, H = f.W, f.D, f.H
    f.cyl(PALE, 0, -0.05, 0, 1.0, 0.8, segs=8, bev=0.08)
    f.cyl('7a7f84', 0, 0.7, 0, 0.55, H - 0.7 + 0.3, segs=10, bev=0.05)


def m_watertank(f, it):
    """the water tower's tank (on its four legs at +-6), a catwalk, braces between the legs, a ladder"""
    K = f.K
    kind, cx, y, cz, sx, sy, sz, turn, kw = it
    r = sx / 2 - 0.5
    TANK = 'a3a8a6'
    K.lathe(f.m, TANK, [(0, 0), (r - 1.5, 0), (r, 1.4), (r, sy - 2.0), (r + 0.2, sy - 2.0), (r * 0.15, sy + 3.5), (0, sy + 3.5)], cx, y, cz, segs=24)
    K.lathe(f.m, METAL_D, [(0, sy + 3.4), (0.35, sy + 3.4), (0.35, sy + 4.6), (0.6, sy + 4.9), (0, sy + 5.0)], cx, y, cz, segs=8)
    K.ring(f.m, METAL_D, cx, y + 0.9, y + 1.25, cz, r - 0.2, r + 1.6, segs=24)                   # the catwalk
    K.ring(f.m, METAL_D, cx, y + 4.0, y + 4.15, cz, r + 1.45, r + 1.6, segs=24)                  # its rail
    for k in range(8):
        a = k * math.pi / 4
        K.B(f.m, METAL_D, cx + math.cos(a) * (r + 1.5) - 0.08, y + 1.2, cz + math.sin(a) * (r + 1.5) - 0.08,
            cx + math.cos(a) * (r + 1.5) + 0.08, y + 4.0, cz + math.sin(a) * (r + 1.5) + 0.08, bev=0)
    legs = [(cx - 6, cz - 6), (cx + 6, cz - 6), (cx - 6, cz + 6), (cx + 6, cz + 6)]
    base = 32.0
    for (ya, yb) in ((base + 4.0, base + 10.0), (base + 10.0, base + 16.0)):
        for (a, b) in ((0, 1), (2, 3), (0, 2), (1, 3)):
            (xa, za), (xb, zb) = legs[a], legs[b]
            K.B(f.m, METAL_D, min(xa, xb) - 0.12, yb - 0.12, min(za, zb) - 0.12, max(xa, xb) + 0.12, yb + 0.12, max(za, zb) + 0.12, bev=0)
            ln = math.hypot(xb - xa, zb - za)
            dy = yb - ya
            d = math.hypot(ln, dy)
            for s in (-1, 1):
                yaw = math.atan2(xb - xa, zb - za)
                M = K.Tr((xa + xb) / 2, (ya + yb) / 2, (za + zb) / 2) @ K.Ry(yaw) @ K.Rx(s * math.atan2(dy, ln))
                K.B(f.m, METAL_D, -0.08, -0.08, -d / 2, 0.08, 0.08, d / 2, bev=0, M=M)
    lx, lz = cx + 6.6, cz                                                                         # the ladder (east side)
    for s in (-0.6, 0.6):
        K.B(f.m, METAL_D, lx - 0.08, base, lz + s - 0.08, lx + 0.08, y + 1.2, lz + s + 0.08, bev=0)
    for k in range(int((y + 1.2 - base) // 1.2)):
        K.B(f.m, METAL_D, lx - 0.06, base + 0.8 + k * 1.2, lz - 0.6, lx + 0.06, base + 0.92 + k * 1.2, lz + 0.6, bev=0)


def m_solar(f, it):
    """a row of solar panels tilted to the south on a frame"""
    W, D, H = f.W, f.D, f.H
    tilt = math.atan2(H - 1.0, D - 0.6)
    ln = math.hypot(H - 1.0, D - 0.6)
    for k in range(int(W // 6)):
        u = -W / 2 + 3.0 + k * 6.0
        for (w, hh) in ((-D / 2 + 0.4, H - 0.3), (D / 2 - 0.65, 1.05)):
            f.box(METAL_D, u - 0.15, -0.05, w, u + 0.15, hh, w + 0.25, bev=0)
        f.rbox('3d4650', u, (H + 1.0) / 2, 0, 5.8, 0.15, ln, pitch=tilt, bev=0.03)
        for j in range(1, 3):
            f.rbox('59636c', u - 2.9 + j * 1.93, (H + 1.0) / 2 + 0.09, 0, 0.08, 0.06, ln - 0.1, pitch=tilt, bev=0)


def m_skylight(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(PALE, -W / 2, -0.05, -D / 2, W / 2, 1.2, D / 2, bev=0.1)
    for s in (-1, 1):
        ln = math.hypot(W / 2, H - 1.0)
        a = math.atan2(H - 1.0, W / 2)
        f.rbox('b8cdd6', s * W / 4, 1.2 + (H - 1.0) / 2, 0, ln, 0.1, D - 0.4, roll=-s * a, kind='glass', bev=0)
    f.box(METAL_D, -0.15, H - 0.1, -D / 2 + 0.2, 0.15, H + 0.1, D / 2 - 0.2, bev=0)


def m_dish(f, it):
    W, D, H = f.W, f.D, f.H
    f.box(METAL_D, -1.5, -0.05, -1.5, 1.5, 0.4, 1.5, bev=0.08)
    f.cyl(METAL, 0, 0.4, 0, 0.25, H - 3.0, segs=8, bev=0)
    x, z = f.P(0, 0.4)
    M = f.K.Tr(x, f.y + H - 2.4, z) @ f.K.Ry(Fr.YAW[f.f]) @ f.K.Rx(-math.pi / 2 + 0.6)
    bm_pts = [(0, 0), (0.6, 0.02), (1.4, 0.12), (2.2, 0.32), (2.6, 0.5), (2.5, 0.55), (0, 0.15)]
    _lathe_m(f, PALE, bm_pts, M)
    f.rbox(METAL_D, 0, H - 1.6, 1.2, 0.12, 0.12, 2.6, pitch=-0.9, bev=0)


def _lathe_m(f, col, prof, M, segs=18):
    """a lathe placed by a matrix (arenakit's lathe only translates)"""
    import bmesh
    K = f.K
    bm = bmesh.new()
    rings = []
    for r, h in prof:
        if r < 1e-5: rings.append([bm.verts.new((0, h, 0))])
        else: rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), h, r * math.sin(2 * math.pi * i / segs))) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) > 1 and len(b) > 1: bm.faces.new((a[i], a[j], b[j], b[i]))
            elif len(a) > 1: bm.faces.new((a[i], a[j], b[0]))
            elif len(b) > 1: bm.faces.new((a[0], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    K.put(f.m, 'plastic', col, bm, M)


def m_frontdoors(f, it):
    """the chained front doors as shallow reliefs on both faces of the solid south wall (z 96..98): an aluminium frame,
    two dark glass leaves, push bars, a chain through the bars with a padlock"""
    K = f.K
    kind, cx, y, cz, sx, sy, sz, turn, kw = it
    x0, x1 = cx - 6.0, cx + 6.0
    for (zf, s) in ((96.0, -1), (98.0, 1)):                       # s: which way is out of the wall at this face
        def zb(d0, d1):
            a, b = zf + s * d0, zf + s * d1
            return min(a, b), max(a, b)
        za, zb_ = zb(-0.02, 0.12)
        for (a, b, c, d) in ((x0 - 0.5, y, x0, y + 10.5), (x1, y, x1 + 0.5, y + 10.5), (x0 - 0.5, y + 10.0, x1 + 0.5, y + 10.6), (cx - 0.2, y, cx + 0.2, y + 10.0)):
            K.B(f.m, STEEL, a, b, za, c, d, zb_, bev=0.03)
        za, zb_ = zb(-0.02, 0.08)
        for (a, c) in ((x0, cx - 0.2), (cx + 0.2, x1)):
            K.B(f.m, '2e3a42', a + 0.15, y + 0.4, za, c - 0.15, y + 9.6, zb_, bev=0.02)
            K.B(f.m, STEEL, a + 0.15, y, za, c - 0.15, y + 0.45, zb_, bev=0.02)                    # kick plates
        za, zb_ = zb(0.08, 0.5)
        for (a, c) in ((x0 + 0.8, cx - 0.6), (cx + 0.6, x1 - 0.8)):
            K.B(f.m, STEEL, a, y + 4.0, za, c, y + 4.3, zb_, bev=0.03)                              # push bars
        za, zb_ = zb(0.45, 0.65)
        for k in range(9):                                                                           # the chain
            xx = cx - 2.4 + k * 0.6
            yy = y + 4.15 - 0.35 * math.sin(k / 8 * math.pi)
            K.B(f.m, '6c7177', xx - 0.22, yy - 0.12, za, xx + 0.22, yy + 0.12, zb_, bev=0.02)
        za, zb_ = zb(0.5, 0.85)
        K.B(f.m, BRASS, cx - 0.35, y + 3.0, za, cx + 0.35, y + 3.7, zb_, bev=0.06)                  # the padlock


def m_unknown(f, it):
    f.box('b8b1a3', -f.W / 2, -0.05, -f.D / 2, f.W / 2, f.H, f.D / 2, bev=0.15)


MODELS = {
    'desk': m_desk, 'teacherdesk': m_teacherdesk, 'board': m_board, 'cubbies': m_cubbies, 'flag': m_flag,
    'stalls': m_stalls, 'sinks': m_sinks, 'mirror': m_mirror, 'reception': m_reception, 'pillar': m_pillar,
    'trophy': m_trophy, 'bench': m_bench, 'plant': m_plant, 'bed': m_bed, 'desk_big': m_desk_big, 'cabinet': m_cabinet,
    'servery': m_servery, 'kitchen': m_kitchen, 'fridge': m_fridge, 'lunchtable': m_lunchtable, 'trash': m_trash,
    'labbench': m_labbench, 'fume': m_fume, 'skeleton': m_skeleton, 'lockers': m_lockers, 'shelf': m_shelf,
    'mopsink': m_mopsink, 'cart': m_cart, 'tree': m_tree, 'planter': m_planter, 'picnic': m_picnic,
    'flagpole': m_flagpole, 'bikerack': m_bikerack, 'shed': m_shed, 'vault': m_vault, 'mat': m_mat,
    'ballrack': m_ballrack, 'hoop': m_hoop, 'scoreboard': m_scoreboard, 'showers': m_showers,
    'weightbench': m_weightbench, 'rack': m_rack, 'crate': m_crate, 'workbench': m_workbench, 'boiler': m_boiler,
    'heater': m_heater, 'generator': m_generator, 'pipes': m_pipes, 'bookshelf': m_bookshelf, 'readtable': m_readtable,
    'globe': m_globe, 'arttable': m_arttable, 'easel': m_easel, 'kiln': m_kiln, 'drying': m_drying,
    'counter': m_counter, 'chair': m_chair, 'filing': m_filing, 'bigdesk': m_bigdesk, 'bigchair': m_bigchair,
    'couch': m_couch, 'coffeetable': m_coffeetable, 'table': m_table, 'computers': m_computers, 'piano': m_piano,
    'riser': m_riser, 'hvac': m_hvac, 'greenhouse': m_greenhouse, 'towerleg': m_towerleg, 'watertank': m_watertank,
    'solar': m_solar, 'skylight': m_skylight, 'dish': m_dish, 'frontdoors': m_frontdoors,
}
SKIP = ('stallwall', 'showerwall')
FACE_FIX = {'servery': lambda it: 'e'}        # (the serving counter faces the dining room; it stands clear of walls)


def furniture(K, L, items=None, verbose=True):
    """draw every item of L.FURN (or `items`). Returns {kind: triangles}"""
    items = L.FURN if items is None else items
    tris = {}
    cur = ['']
    put0 = K.put

    def put(model, kind, col, bm, M=K.I4):
        tris[cur[0]] = tris.get(cur[0], 0) + sum(len(fc.verts) - 2 for fc in bm.faces)
        put0(model, kind, col, bm, M)
    K.put = put
    try:
        for it in items:
            kind, cx, y, cz, sx, sy, sz, turn, kw = it
            if kind in SKIP: continue
            face = FACE_FIX[kind](it) if kind in FACE_FIX else L.FACE(it)
            W, D = (sx, sz) if face in ('s', 'n') else (sz, sx)
            f = Fr(K, 'sc_furn_' + level_of(kind, y), cx, y, cz, face, W, D, sy)
            f.K_ACC, f.L = L.ACCENT, L
            cur[0] = kind
            MODELS.get(kind, m_unknown)(f, it)
    finally:
        K.put = put0
    if verbose:
        tot = sum(tris.values())
        top = sorted(tris.items(), key=lambda kv: -kv[1])
        print('PROPS triangles %d; by kind: %s' % (tot, ', '.join('%s %d' % kv for kv in top)))
    return tris
