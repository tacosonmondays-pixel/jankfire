# THE GUT CHOIR (OVERDUE, ART_BIBLE #16, DESIGN §4.2): Gristle & Sons staff who stayed at their desks while the building
# grew round them, and became the stomach's choir. Robed puppets (head about 1 : 3), enormous hands, tiny office shoes
# peeking out under the hem, a face stretched into a permanent smile (the code face rig's 'choir' pose: the mouth wider
# than the face, the eyes still sad), and the office still showing: the Gristle & Sons lanyard out over the robe, a
# binder of quarterly hymns. Two of them:
#   choir    the tall one, 2.2 m: a fleshy pink robe, a long neck, a long sad face with a long nose (the code rig's big
#            round glasses go over it), a combover, a black ring binder held open. TENOR stamped on his staff badge
#   choir_b  the squat one, 1.5 m: a bile-yellow robe, a barrel chest, a round face, a perm, a pencil behind her ear,
#            a rubber finger on her page-turning hand, a clipboard. ALTO stamped on hers
# The robe's skirt is skinned to the code skeleton's body and legs (dressCast binds it), so it swings with the stride;
# the rest are rigid parts in their joints (castlib). The hands are modelled open, palm forward: in the game's stance
# (looks.js CHOIR_STANCE) they come up palm-up under the hymns, which are placed on the left palm through that pose.
# built in each joint's own frame (the code look's layout, public/js/story/looks.js choirLook), carried to root space.
# blender52 -b --python tools/blender/cast/make_cast_choir.py [-- b] [--no-sheet] [--no-export]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SQ = 'b' in argv
ID = 'choir_b' if SQ else 'choir'
JD = JOINTS[ID]
# the code look's numbers (looks.js choirLook / CHOIR_STANCE): head radii, the face rig's anchors in head space
if not SQ:
    SK, SKD = 0xc8cfe0, 0x9aa2b8
    HR = (0.21, 0.34, 0.215)
    EYE_SEP, EYE_Y, EYE_Z, EYE_R = 0.0783, 0.42, -0.1859, 0.0459
    MOUTH_Y, MOUTH_Z, MOUTH_HW, SMILE_UP, LIP_R = 0.2, -0.206, 0.1453, 0.0596, 0.0189
    TOR = [(-0.1, 0.168, 0.124, 0.116, 2.2), (-0.03, 0.17, 0.126, 0.118, 2.2), (0.08, 0.168, 0.128, 0.118, 2.3), (0.2, 0.174, 0.132, 0.118, 2.3),
           (0.31, 0.183, 0.124, 0.112, 2.4), (0.39, 0.186, 0.11, 0.106, 2.4), (0.445, 0.158, 0.092, 0.092, 2.2), (0.49, 0.1, 0.07, 0.07, 2.0), (0.525, 0.058, 0.052, 0.052, 2.0)]
    SKIRT = dict(top=1.05, hip=0.93, rx=(0.158, 0.19, 0.215, 0.235), rzf=(0.118, 0.152, 0.175, 0.19), rzb=(0.11, 0.15, 0.172, 0.19), floor=0.1472)
    UPPER, FORE, HAND_Y = 0.3, 0.28, -0.326
    RUFF = dict(y=0.5, R=0.1, rw=0.058, rh=0.036, n=26)
    STANCE = dict(L=(0.15, -0.4, -0.15, 2.05), R=(0.15, 0.4, 0.15, 2.05))
    ROBE, FOLD, LINE, STOLE, STOLE2 = 0xe07890, 0xb04866, 0x8a3050, 0xd6d04a, 0x8a2a4a
else:
    SK, SKD = 0xf2b898, 0xc8805a
    HR = (0.25, 0.24, 0.235)
    EYE_SEP, EYE_Y, EYE_Z, EYE_R = 0.0858, 0.28, -0.2064, 0.0416
    MOUTH_Y, MOUTH_Z, MOUTH_HW, SMILE_UP, LIP_R = 0.13, -0.225, 0.1599, 0.0657, 0.0169
    TOR = [(-0.1, 0.24, 0.18, 0.165, 2.0), (-0.02, 0.25, 0.192, 0.172, 2.0), (0.1, 0.262, 0.212, 0.18, 2.1), (0.22, 0.262, 0.205, 0.176, 2.2),
           (0.31, 0.252, 0.178, 0.162, 2.3), (0.365, 0.226, 0.146, 0.14, 2.2), (0.41, 0.165, 0.105, 0.1, 2.0), (0.44, 0.1, 0.075, 0.075, 2.0), (0.465, 0.07, 0.062, 0.062, 2.0)]
    SKIRT = dict(top=1.05, hip=0.93, rx=(0.232, 0.262, 0.285, 0.3), rzf=(0.172, 0.205, 0.225, 0.238), rzb=(0.16, 0.19, 0.215, 0.228), floor=0.4416)
    UPPER, FORE, HAND_Y = 0.22, 0.2, -0.25
    RUFF = dict(y=0.43, R=0.118, rw=0.068, rh=0.04, n=28)
    STANCE = dict(L=(0.55, -0.7, -0.1, 1.45), R=(0.55, 0.7, 0.1, 1.45))
    ROBE, FOLD, LINE, STOLE, STOLE2 = 0xd6cc3c, 0xa4a02a, 0x7a7418, 0x8a2a4a, 0xd6cc3c
HC = (0, HR[1], 0)  # the skull's centre, head space
HK = 1.22 if not SQ else 1.32  # the hands: enormous (one thing huge, ART_BIBLE)


# ------------------------------------------------------------ textures (px: h x w x 3, row 0 at the top)
def robe_px(base, fold, line, seed):
    def draw(px):  # the robe's cloth: a soft rib down it (a stomach lining's ridges, if you look), a slub here and there
        h, w = px.shape[:2]
        r = np.random.default_rng(seed)
        b, f, l = hexrgb(base), hexrgb(fold), hexrgb(line)
        for x in range(w):
            k = x % 8
            px[:, x] = b * 0.55 + f * 0.45 if k == 0 else (b * 0.8 + f * 0.2 if k in (1, 7) else b)
        px *= (0.95 + 0.07 * r.random((h, w, 1)))
        for _ in range(8): y, x = r.integers(0, h), r.integers(0, w); px[y, x:x + 2] = b * 0.6 + l * 0.4
    return draw


def lining_px(base, seed):
    def draw(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        px[:] = hexrgb(base) * 0.55 * (0.9 + 0.15 * r.random((h, w, 1)))
    return draw


def skin_px(base, dark, seed, freckles=False):
    def draw(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        n = np.kron(r.random((h // 4 + 1, w // 4 + 1)), np.ones((4, 4)))[:h, :w]
        px[:] = hexrgb(base)[None, None, :] * (0.965 + 0.04 * n[:, :, None] + 0.015 * r.random((h, w, 1)))
        m = r.random((h, w)) < (0.05 if freckles else 0.03); px[m] = px[m] * 0.6 + hexrgb(dark) * 0.4
    return draw


SW, SH = 0.4, 0.46  # the face texture: metres across and up, centred on the face (head space y = FACE_CY)
FACE_CY = (EYE_Y + MOUTH_Y) / 2


def face_px(px):
    """the face, seen straight on: the skin, tired eyes, the stretch creases out from the smile, the cheeks"""
    h, w = px.shape[:2]
    skin_px(SK, SKD, 61 + SQ, freckles=SQ)(px)
    U = lambda x: (0.5 - x / SW) * w; Vr = lambda y: (0.5 - (y - FACE_CY) / SH) * h
    yy, xx = np.mgrid[0:h, 0:w]
    def soft(cx, cy, rad, col, k):
        m = np.exp(-(((xx - U(cx)) ** 2 + (yy - Vr(cy)) ** 2) / (rad / SW * w) ** 2))[:, :, None] * k
        px[:] = px * (1 - m) + hexrgb(col)[None, None, :] * m
    def crease(pts, dark, k):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            ax, ay, bx, by = U(x0), Vr(y0), U(x1), Vr(y1)
            vx, vy = bx - ax, by - ay; L2 = max(1e-6, vx * vx + vy * vy)
            t = np.clip(((xx + 0.5 - ax) * vx + (yy + 0.5 - ay) * vy) / L2, 0, 1)
            d = np.hypot(xx + 0.5 - (ax + t * vx), yy + 0.5 - (ay + t * vy))
            m = (np.exp(-(d / 0.8) ** 2) * k)[:, :, None]
            px[:] = px * (1 - m) + hexrgb(dark)[None, None, :] * m
    for sx in (-1, 1):
        soft(sx * EYE_SEP, EYE_Y - EYE_R * 1.05, EYE_R * 0.75, 0x6a5a8a if not SQ else 0xb07070, 0.45)  # bags under the eyes (they've been up since the building grew)
        soft(sx * (MOUTH_HW * 0.82), MOUTH_Y + SMILE_UP + 0.035, 0.034, 0xe87a8a if SQ else 0xd890a8, 0.5)  # the cheeks, pulled up hard and flushed
        cx0, cy0 = sx * MOUTH_HW * 1.02, MOUTH_Y + SMILE_UP
        for k, (dx, dy) in enumerate(((0.06, 0.07), (0.07, 0.025), (0.055, -0.02))):  # the stretch: lines out from the corners of the smile toward the ears
            crease([(cx0, cy0), (cx0 + sx * dx * 0.5, cy0 + dy * 0.6), (cx0 + sx * dx, cy0 + dy)], 0x7a5a78 if not SQ else 0xb0705a, 0.55 - 0.1 * k)
    if not SQ:  # a five o'clock shadow, sixty years long
        r = np.random.default_rng(65)
        m = (r.random((h, w)) < 0.22) & ((yy > Vr(MOUTH_Y - 0.01)) | (np.abs(xx - U(0)) > w * 0.36)) & (yy > Vr(MOUTH_Y + 0.05))
        px[m] = px[m] * 0.82 + hexrgb(0x6a6a80) * 0.18


def ruff_px(px):
    h, w = px.shape[:2]
    for x in range(w): px[:, x] = hexrgb(0xf2ead6) * (0.8 + 0.2 * abs(math.sin(x * math.pi / 4)))
    r = np.random.default_rng(66); px *= (0.95 + 0.06 * r.random((h, w, 1)))
    for _ in range(6): px_disc(px, r.integers(0, w), r.integers(0, h), r.uniform(0.8, 1.6), 0xd8c890)  # the gut is damp: a few yellow spots


def stole_px(px):  # the stole: a stitched border, a little smiling butcher (the Gristle & Sons badge) embroidered on it
    h, w = px.shape[:2]
    px[:] = hexrgb(STOLE)
    px[:, :2] = px[:, -2:] = hexrgb(STOLE2)
    for y in range(0, h, 4): px[y, 3] = px[y, w - 4] = hexrgb(0xf2ead6)
    for cy in (h - 14,):
        px_disc(px, w / 2, cy, 5.5, 0xffe14d); px_disc(px, w / 2, cy, 5.5, 0xd8203a, r_in=4.6)
        px[cy - 2, int(w / 2) - 2] = px[cy - 2, int(w / 2) + 1] = hexrgb(0x1a1030)
        px_disc(px, w / 2, cy + 0.5, 2.6, 0x1a1030, r_in=1.7, a0=math.pi * 0.6, a1=math.pi * 1.4)


def ribbon_px(px):  # the lanyard: Gristle & Sons liver red, G&S in cream all the way along
    h, w = px.shape[:2]
    px[:] = hexrgb(0x8a2a4a)
    for y in range(1, h, 10): text_px(px, 'G', 1, y, 1, 0xf2ead6)


def badge_px(px):
    """the staff badge: the company band, their photo from before (a normal face, a normal smile), the job they had,
    and the choir's stamp across it"""
    h, w = px.shape[:2]
    px[:] = hexrgb(0xfff3d0)
    px[:9, :] = hexrgb(0x8a2a4a); text_px(px, 'G&S', 3, 1, 1, 0xfff3d0)
    px_disc(px, w - 6, 4.5, 3.3, 0xffe14d); px_disc(px, w - 6, 4.5, 3.3, 0xd8203a, r_in=2.6)
    px[12:30, 3:17] = hexrgb(0x9ab8d0)  # the photo
    px_disc(px, 10, 21, 5.2, 0xe6c0a0 if not SQ else 0xf0b898)
    px_disc(px, 10, 15.5, 5.0, 0x3a2e2a if not SQ else 0x8a5a3a, a0=-1.6, a1=1.6)
    px[20, 8] = px[20, 12] = hexrgb(0x1a1a1a); px[24, 9:12] = hexrgb(0x8a4a4a)
    px[27:30, 5:16] = hexrgb(0x5a6a8a)
    text_px(px, 'STAFF', 19, 12, 1, 0x1a1a1a)
    text_px(px, 'ACCTS' if not SQ else 'HR', 19, 21, 1, 0x5a5a5a)
    for i in range(3): px[33 + i * 3, 3:w - 3] = hexrgb(0xc8bca0)
    # the stamp: red, crooked, over everything
    sh = np.zeros_like(px); text_px(sh, 'TENOR' if not SQ else 'ALTO', 3 if not SQ else 6, 0, 1, 0xffffff)
    for y in range(h):
        for x in range(w):
            sy = y - 26 + (x - w / 2) * 0.28
            if 0 <= sy < 7 and sh[int(sy), x].sum() > 0 and (x * 7 + y * 3) % 11: px[y, x] = hexrgb(0xd8203a)


def patch_px(px):  # the Gristle & Sons badge as a sewn patch: yellow, a red rim, the smiling butcher-doctor in a paper hat
    h, w = px.shape[:2]
    px[:] = hexrgb(0xd8203a)
    px_disc(px, w / 2, h / 2, w / 2 - 2.5, 0xffe14d)
    for a in range(0, 360, 20): px_disc(px, w / 2 + math.sin(math.radians(a)) * (w / 2 - 1.2), h / 2 - math.cos(math.radians(a)) * (h / 2 - 1.2), 0.6, 0xf2ead6)  # stitches
    px_disc(px, w / 2, h / 2 + 1, 8, 0xffc9a8)  # the face
    px_disc(px, w / 2, h / 2 - 7, 7.5, 0xffffff, a0=-1.7, a1=1.7)  # the paper hat
    for sx in (-1, 1): px_line(px, w / 2 + sx * 3 - 1.5, h / 2 - 1, w / 2 + sx * 3 + 1.5, h / 2 - 1, 0x1a1030, 1)  # happy shut eyes
    px_disc(px, w / 2, h / 2 + 3, 4.5, 0x1a1030, r_in=3.3, a0=math.pi * 0.55, a1=math.pi * 1.45)  # the grin
    for sx in (-1, 1): px_line(px, w / 2, h / 2 + 1.5, w / 2 + sx * 6, h / 2 + 0.5, 0x7a3a28, 1.6)  # the moustache


def label_px(px):  # the binder's spine and cover labels
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf4f0e2)
    px[:3, :] = px[-3:, :] = hexrgb(0x8a2a4a)
    text_px(px, 'HYMNS', 3, 5, 1, 0x1a1a1a)
    text_px(px, 'Q3', 3, 14, 1, 0xd8203a)


def pages_px(left):
    def draw(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xf6f0dc)
        if left:  # a bar chart: hymns sung, by quarter (going down)
            text_px(px, 'Q3', 3, 3, 1, 0x1a1a1a)
            for i, v in enumerate((20, 16, 13, 9, 5)): px[h - 6 - v:h - 6, 4 + i * 6:8 + i * 6] = hexrgb([0x8a2a4a, 0xd8203a, 0xe07890, 0xd6cc3c, 0x9ab8d0][i])
            px[h - 6, 3:w - 3] = hexrgb(0x1a1a1a)
        else:  # the hymn: staves and notes, the words underneath
            for s in range(3):
                y0 = 4 + s * 11
                for l in range(5): px[y0 + l * 1, 2:w - 2] = hexrgb(0x8a8070)
                for k in range(5):
                    x = 5 + k * 6; y = y0 + (k * 3 + s) % 5
                    px_disc(px, x, y + 0.5, 1.4, 0x1a1a1a); px[y - 4:y, x + 1] = hexrgb(0x1a1a1a)
                px[y0 + 7, 3:w - 3:2] = hexrgb(0x5a5a5a)
    return draw


def clip_px(px):  # the back of her clipboard: hardboard, the office's sticker on it
    h, w = px.shape[:2]; r = np.random.default_rng(67)
    px[:] = hexrgb(0x9a6a3a) * (0.9 + 0.12 * r.random((h, w, 1)))
    for y in range(h): px[y, :] *= 0.95 + 0.05 * math.sin(y * 0.9)
    y0 = h // 2 - 12; px[y0:y0 + 22, 6:w - 6] = hexrgb(0xfff3d0); px[y0:y0 + 4, 6:w - 6] = hexrgb(0x8a2a4a)
    text_px(px, 'HR', w // 2 - 5, y0 + 6, 1, 0x1a1a1a)
    px_disc(px, w // 2, y0 + 17, 3.2, 0xffe14d); px_disc(px, w // 2, y0 + 17, 3.2, 0xd8203a, r_in=2.5)


def sheet_px(px):  # her hymn sheet, a tick list
    h, w = px.shape[:2]
    px[:] = hexrgb(0xfaf6ea)
    text_px(px, 'HYMN', 3, 2, 1, 0x1a1a1a)
    for i in range(6):
        y = 13 + i * 6; px[y + 4, 9:w - 3] = hexrgb(0x9a9aa8)
        px[y:y + 5, 2] = px[y:y + 5, 6] = px[y, 2:7] = px[y + 4, 2:7] = hexrgb(0x5a5a6a)
        if i < 4: px_line(px, 3, y + 2, 4.5, y + 3.5, 0xd8203a, 1); px_line(px, 4.5, y + 3.5, 6.5, y + 0.5, 0xd8203a, 1)


def hair_px(base, seed):
    def draw(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        for x in range(w): px[:, x] = hexrgb(base) * (0.85 + 0.25 * r.random()) * (0.8 if x % 3 == 1 else 1.0)
    return draw


# ------------------------------------------------------------ shapes
def ell(name, c, ax, m, seg=12, rings=8):
    """an ellipsoid with its three semi-axes as game vectors, centred on c"""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    A, B, C = (Vector(a) for a in ax)
    for v in bm.verts:
        bx, by, bz = v.co
        v.co = gv(*(Vector(c) + A * bx + B * bz + C * (-by)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib_obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def sculpt(name, c, radii, m, fn, seg=32, rings=24):
    """an ellipsoid (radii in game axes, centred on c) whose every vertex moves by fn(g, n) -> a game-space offset
    vector (g: the point relative to c, n: its outward direction). faces, skulls"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in bm.verts:
        bx, by, bz = v.co
        g = Vector((bx * radii[0], bz * radii[1], -by * radii[2]))
        nrm = Vector((bx / radii[0], bz / radii[1], -by / radii[2])).normalized()
        g = g + fn(g, nrm)
        v.co = gv(c[0] + g.x, c[1] + g.y, c[2] + g.z)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib_obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def shell(name, secs, m, seg=40, fn=None, cap=(True, True)):
    """a lofted body: sections (y, half width, front depth, back depth, squareness) round the game y axis (front -z).
    fn(p, n) -> a push along the normal"""
    bm = bmesh.new(); rings = []
    for (y, rx, rzf, rzb, pw) in secs:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; c, s = math.cos(a), math.sin(a)
            x = rx * math.copysign(abs(c) ** (2 / pw), c); z = (rzb if s > 0 else rzf) * math.copysign(abs(s) ** (2 / pw), s)
            ring.append(bm.verts.new(gv(x, y, z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    for end, ring in ((0, rings[0]), (1, rings[-1])):
        if not cap[end]: continue
        tip = bm.verts.new(gv(0, secs[0 if end == 0 else -1][0], 0))
        for k in range(seg): bm.faces.new((ring[k], ring[(k + 1) % seg], tip))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if fn:
        bm.normal_update()
        moves = []
        for v in bm.verts:
            p = Vector((v.co.x, v.co.z, -v.co.y)); nb = v.normal; n = Vector((nb.x, nb.z, -nb.y))
            moves.append((v, n, fn(p, n)))
        for v, n, d in moves:
            if d: v.co += gv(*(n * d)) - gv(0, 0, 0)
    o = lib_obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def tor_at(y):
    s = TOR
    if y <= s[0][0]: return s[0][1:]
    for a, b in zip(s, s[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0]); return tuple(a[i] + (b[i] - a[i]) * t for i in range(1, 5))
    return s[-1][1:]


def front_z(x, y, out=0.0):
    rx, rzf, rzb, pw = tor_at(y)
    q = max(0.0, 1 - abs(x / rx) ** pw)
    return -rzf * q ** (1 / pw) - out


def solid(o, t, off=-1.0):
    so = o.modifiers.new('solid', 'SOLIDIFY'); so.thickness = t; so.offset = off; so.use_even_offset = True
    return o


def rot_about(o, c, rx=0.0, ry=0.0, rz=0.0):
    """turn o's mesh about game point c (three.js XYZ order)"""
    apply_mods(o)
    M = Matrix.Rotation(rx, 4, 'X') @ Matrix.Rotation(-rz, 4, 'Y') @ Matrix.Rotation(ry, 4, 'Z')  # (game x, y, z -> blender x, z, -y)
    C = gv(*c)
    o.data.transform(Matrix.Translation(C) @ M @ Matrix.Translation(-C))
    return o


def decal_q(name, c, right, up, w, h, m, lift=0.0):
    """a flat printed quad, centred on c, its image's right along `right` and up along `up` (game vectors)"""
    R, U = Vector(right).normalized(), Vector(up).normalized(); Nn = R.cross(U).normalized()
    C = Vector(c) + Nn * lift
    P = [C - R * w / 2 - U * h / 2, C + R * w / 2 - U * h / 2, C + R * w / 2 + U * h / 2, C - R * w / 2 + U * h / 2]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*p)) for p in P]
    f = bm.faces.new(vs)
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    o = lib_obj(name, bm, m); o['keep_uv'] = 1
    return o


def slab(name, c, U, Vv, N, w, h, t, m, uv=None, bev=0.0):
    """a box in a frame (U right, V up, N out of its face), w x h x t; uv: a picture on the N face (the rest plain)"""
    U, Vv, N = (Vector(x).normalized() for x in (U, Vv, N))
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    P = {}
    for i in (-1, 1):
        for j in (-1, 1):
            for k in (-1, 1): P[(i, j, k)] = bm.verts.new(gv(*(Vector(c) + U * i * w / 2 + Vv * j * h / 2 + N * k * t / 2)))
    faces = [((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)), ((-1, -1, 1), (-1, 1, 1), (-1, 1, -1), (-1, -1, -1)),
             ((-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)), ((-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1)),
             ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)), ((1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1))]
    for fk in faces:
        f = bm.faces.new([P[q] for q in fk])
        for lp, q in zip(f.loops, fk):
            if all(x[2] == 1 for x in fk): lp[uvl].uv = ((q[0] + 1) / 2, (q[1] + 1) / 2)  # (the picture)
            else:  # (the edges and the back: a sliver of the picture's corner, never a zero-area face)
                same = [ax for ax in range(3) if all(x[ax] == fk[0][ax] for x in fk)][0]; a0, a1 = [ax for ax in range(3) if ax != same]
                lp[uvl].uv = (0.01 + 0.03 * (q[a0] + 1) / 2, 0.97 + 0.02 * (q[a1] + 1) / 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib_obj(name, bm, m); o['keep_uv'] = 1
    if bev: bevel(o, bev, 2, 30)
    return o


def on_scalp(o, p, off):
    """a point pushed out from the skull's centre onto o's surface (game coords, o not yet moved), plus off along it"""
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new(); bm.from_mesh(o.data); t = BVHTree.FromBMesh(bm); bm.free()
    c = gv(*HC); d = (gv(*p) - c).normalized()
    hit = t.ray_cast(c, d)
    q = hit[0] + d * off if hit[0] is not None else gv(*p)
    return (q.x, q.z, -q.y)


def back_patch(src, c, rad, m):
    """a round patch cut from the bodice's back (the faces round c = (x, y) on the back), lifted 1.5 mm (clear of a
    z-fight, still sewn on), the picture straight on from behind"""
    me = src.data.copy(); o = bpy.data.objects.new('patch', me); bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me)
    keep = lambda p: p.z > 0.02 and math.hypot(p.x - c[0], p.y - c[1]) < rad
    dead = [f for f in bm.faces if not keep(Vector((f.calc_center_median().x, f.calc_center_median().z, -f.calc_center_median().y)))]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.normal_update()
    for v in bm.verts: v.co += v.normal * 0.0015
    bm.to_mesh(me); bm.free()
    me.materials.clear(); me.materials.append(m)
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (0.5 + (v.x - c[0]) / (2 * rad), 0.5 + (v.z - c[1]) / (2 * rad))  # (seen from behind: game +x is on the viewer's right)
    o['keep_uv'] = 1
    return o


def uv_hairband(o):
    """combed UVs for hair round the head: u round it (the texture's strands run down), v up it"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        us = []
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            us.append((li, math.atan2(v.x, v.y) / math.pi * 6, v.z * 3))
        u0 = us[0][1]
        for li, u, w in us:
            while u - u0 > 6: u -= 12
            while u - u0 < -6: u += 12
            uv[li].uv = (u, w)
    o['keep_uv'] = 1
    return o


def tapered(name, pts, r0, r1, m, seg=8):
    n = len(pts); return limb(name, pts, [r0 + (r1 - r0) * i / (n - 1) for i in range(n)], m, seg=seg)


# ------------------------------------------------------------ the game's stance, for placing things and posing sheets
def M4(e): return np.array(e, float).reshape(4, 4).T


def _rx(a): c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]])
def _ry(a): c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]])
def _rz(a): c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])


def stance_fk(L=None, R=None):
    """the arms' world matrices (game coords, root space) with looks.js's stance set on them (as actors.js does)"""
    d = JD['mats']; out = {}
    for a, f, h, want, rz0 in (('armL', 'foreL', 'handL', L or STANCE['L'], -0.08), ('arm', 'foreR', 'handR', R or STANCE['R'], 0.08)):
        Ma, Mf, Mh = M4(d[a]), M4(d[f]), M4(d[h])
        Wa = Ma @ np.linalg.inv(_rz(rz0)) @ _rx(want[0]) @ _ry(want[1]) @ _rz(want[2])
        Wf = Wa @ np.linalg.inv(Ma) @ Mf @ _rx(want[3])
        Wh = Wf @ np.linalg.inv(Mf) @ Mh
        out[a], out[f], out[h] = Wa, Wf, Wh
    return out


def to_local(joint, W):
    """a world placement W (4x4, game, at the stance) -> that joint's local frame"""
    return np.linalg.inv(stance_fk()[joint]) @ W


def place(objs, T):
    """carry objects built in their own frame (game coords) by a 4x4 game-space matrix T"""
    C = np.array(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)), float)  # game -> blender
    Mb = Matrix((C @ T @ np.linalg.inv(C)).tolist())
    for o in objs:
        apply_mods(o); o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4); o.data.transform(Mb)
    return objs


def frame(c, U, Vv, N):
    """a 4x4 game matrix with columns U, V, N at c"""
    T = np.eye(4); T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = U, Vv, N, c
    return T


# ------------------------------------------------------------ the robe's skirt: a thick cloth bell, skinned
def skirt(name, m, lining):
    """from the waist (body space y top) to the floor: folds deepening down it, the hem rolled, a little raised at the
    front so the shoes show; a closed shell (outside down, round the hem, the lining back up)"""
    S = SKIRT; NA = 56
    ys = [S['top'], S['hip'], S['hip'] - 0.25 * (S['hip'] - S['floor']), S['hip'] - 0.55 * (S['hip'] - S['floor']), S['floor'] + 0.015]
    def lerpk(arr, t):  # radius at t (0 top .. 1 hem) through the 4 key heights (top, hip, mid, hem)
        keys = (0.0, (S['top'] - S['hip']) / (S['top'] - ys[-1]), 0.55, 1.0)
        for i in range(3):
            if t <= keys[i + 1]:
                u = (t - keys[i]) / (keys[i + 1] - keys[i]); u = u * u * (3 - 2 * u); return arr[i] + (arr[i + 1] - arr[i]) * u
        return arr[-1]
    rng = random.Random(71 + SQ)
    ph = [rng.uniform(0, 6.28) for _ in range(4)]
    def folds(a):
        return (0.55 * math.sin(9 * a + ph[0]) + 0.3 * math.sin(14 * a + ph[1]) + 0.2 * math.sin(5 * a + ph[2])
                + 0.6 * math.exp(-((math.atan2(math.sin(a + math.pi / 2), math.cos(a + math.pi / 2))) / 0.35) ** 2) * math.sin(3 * a))  # (a deeper break down the front)
    def ring(t, inset=0.0, dy=0.0):
        y = S['top'] + (ys[-1] - S['top']) * t
        rx, rzf, rzb = lerpk(S['rx'], t), lerpk(S['rzf'], t), lerpk(S['rzb'], t)
        dep = 0.004 + 0.022 * t ** 1.3
        pts = []
        for k in range(NA):
            a = 2 * math.pi * k / NA; c_, s_ = math.cos(a), math.sin(a)
            rz = rzb if s_ > 0 else rzf
            f = folds(a) * dep
            x, z = (rx + f) * c_, (rz + f) * s_
            nx, nz = c_ / rx, s_ / rz; nl = math.hypot(nx, nz); nx, nz = nx / nl, nz / nl
            yy = y + dy
            if t >= 0.999:  # the hem: it follows the folds, and lifts at the front over the shoes
                yy += 0.01 * folds(a) + 0.03 * math.exp(-((a - (-math.pi / 2)) / 0.5) ** 2)
            pts.append(Vector((x - nx * inset, yy, z - nz * inset)))
        return pts
    T = 0.014  # the cloth's thickness
    rings = [ring(i / 15) for i in range(16)]
    hem = rings[-1]
    out_hem = [Vector((p.x, p.y - 0.004, p.z)) for p in hem]
    mid = ring(1.0, T * 0.5, -0.009)
    in_hem = ring(1.0, T, -0.002)
    inner = [ring(1 - i / 7, T) for i in range(1, 8)]  # (back up to the waist on the inside)
    seq = rings + [out_hem, mid, in_hem] + inner
    bm = bmesh.new(); vr = [[bm.verts.new(gv(*p)) for p in r] for r in seq]
    bm.verts.index_update()
    VS = {}; acc = 0.0  # (v: the distance along the cloth from the waist, outside down and the lining back up, so no face has no height)
    for i, r in enumerate(seq):
        if i: acc += max(0.004, (Vector(seq[i][0]) - Vector(seq[i - 1][0])).length)
        for v in vr[i]: VS[v.index] = acc
    for a, b in zip(vr, vr[1:]):
        for k in range(NA): bm.faces.new((a[k], a[(k + 1) % NA], b[(k + 1) % NA], b[k]))
    for k in range(NA): bm.faces.new((vr[-1][k], vr[-1][(k + 1) % NA], vr[0][(k + 1) % NA], vr[0][k]))  # the waist: the lining meets the outside
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uvl = bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:  # (round the skirt: twelve repeats of the weave, no face straddling the seam)
        us = [math.atan2(-lp.vert.co.y, lp.vert.co.x) / (2 * math.pi) * 12 for lp in f.loops]
        for i in range(1, len(us)):
            while us[i] - us[0] > 6: us[i] -= 12
            while us[i] - us[0] < -6: us[i] += 12
        for lp, u in zip(f.loops, us): lp[uvl].uv = (u, VS[lp.vert.index] * 1.4)
        f.smooth = True
    o = lib_obj(name, bm, m); o['keep_uv'] = 1
    o.data.materials.append(lining)
    return o, (len(rings) + 2) * NA  # (the first vertex of the lining: past the outside rows, the hem's outer row and its turn)


def skirt_lining(o, first_inner_vert):
    for p_ in o.data.polygons:
        if min(p_.vertices) >= first_inner_vert: p_.material_index = 1


def skin_skirt(o, arm):
    """weights: the waist on the body; down the skirt more and more on the leg on that side (half and half down the
    middle), up to 0.55 at the hem: the robe swings with the stride, the hem a beat behind"""
    S = SKIRT
    for g in ('body', 'legL', 'legR'): o.vertex_groups.new(name=g)
    hipy = JD['joints']['legL'][1]; top = S['top'] + JD['joints']['body'][1]
    for v in o.data.vertices:
        p = v.co; x, y = p.x, p.z  # (blender z is game y)
        t = min(1.0, max(0.0, (top - y) / (top - 0.0)))
        lw = 0.6 * t ** 1.6
        sR = 0.5 + 0.5 * max(-1.0, min(1.0, x / 0.12))
        sR = sR * sR * (3 - 2 * sR)
        w = {'body': 1 - lw, 'legL': lw * (1 - sR), 'legR': lw * sR}
        for g, x_ in w.items():
            if x_ > 1e-4: o.vertex_groups[g].add([v.index], x_, 'REPLACE')
    o.parent = arm; md = o.modifiers.new('rig', 'ARMATURE'); md.object = arm
    return o


def make_rig(root):
    """an armature with the code skeleton's body and leg joints (by name: dressCast binds the skirt to ch.body,
    ch.legL, ch.legR at the pose they have when the look is built)"""
    ad = bpy.data.armatures.new(ID + '_rig'); arm = bpy.data.objects.new(ID + '_rig', ad); bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    for s_ in bpy.context.view_layer.objects.selected: s_.select_set(False)
    arm.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    J_ = JD['joints']
    b = ad.edit_bones.new('body'); b.head = gv(*J_['body']); b.tail = gv(*J_['spine'])
    for n, k in (('legL', 'kneeL'), ('legR', 'kneeR')):
        e = ad.edit_bones.new(n); e.head = gv(*J_[n]); e.tail = gv(*J_[k]); e.parent = b; e.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.parent = root
    return arm


# ------------------------------------------------------------ the parts
def hand(hk, sx, skin, nail, extras):
    """an enormous open hand, hand space (the wrist at 0, fingers down -y, palm forward -z, thumb on the inside):
    a broad flat palm, long fingers curled a little with their knuckles in them, nails, the thumb out at an angle
    (in the stance they all go under the hymns, palm up)"""
    k = HK
    out = [blob('palm' + hk, (0, -0.074 * k, 0.003), (0.064 * k, 0.078 * k, 0.023 * k), skin,
                fn=lambda p, n: -0.005 * max(0.0, -n.z) * math.exp(-((p.y + 0.008) / 0.045) ** 2 - (p.x / 0.05) ** 2) + 0.004 * max(0.0, n.z) * math.exp(-((p.y + 0.06) / 0.02) ** 2), seg=16, rings=12)]
    out.append(blob('heel' + hk, (-sx * 0.03 * k, -0.045 * k, -0.01), (0.032 * k, 0.04 * k, 0.02 * k), skin, seg=12, rings=8))  # the thumb's pad
    out.append(limb('wrist' + hk, [(0, 0.03, 0.002), (0, -0.012, 0.002), (0, -0.032, 0.003)], [0.034, 0.04 * k, 0.046 * k], skin, seg=12))
    lens = (0.13, 0.148, 0.14, 0.112)
    for fi in range(4):
        fx = sx * (-0.044 + fi * 0.0295) * k  # (index on the thumb's side)
        base = Vector((fx, (-0.142, -0.147, -0.145, -0.137)[fi] * k, -0.002))
        spread = sx * (-0.1 + fi * 0.065)  # a little fan
        curl = (0.1, 0.2, 0.16)
        L = lens[fi] * k; segs = (0.44, 0.31, 0.25); a = 0.0; p = base.copy(); joints = [p.copy()]
        for i, f in enumerate(segs):
            a += curl[i]; d = Vector((math.sin(spread), -math.cos(a) * math.cos(spread), -math.sin(a))).normalized()
            p = p + d * L * f; joints.append(p.copy())
        r = (0.0138, 0.0145, 0.014, 0.0124)[fi] * k
        pts, rr = [], []
        for i in range(3):  # (the knuckles bulge a touch: the radius swells at each joint)
            pts += [joints[i], joints[i].lerp(joints[i + 1], 0.5)]; rr += [r * (1.08 if i else 1.04) * (1 - 0.05 * i), r * (0.95 - 0.06 * i)]
        pts.append(joints[3]); rr.append(r * 0.72)
        out.append(limb('f%s%d' % (hk, fi), [tuple(q) for q in pts], rr, skin, seg=10))
        tip, dv = joints[3], (joints[3] - joints[2]).normalized(); dors = Vector((0, -math.sin(a), math.cos(a))).normalized()
        out.append(ell('nail%s%d' % (hk, fi), tuple(tip - dv * L * 0.08 + dors * r * 0.68), (Vector((r * 0.66, 0, 0)), dors * 0.003, dv * r * 0.95), nail, 8, 5))
        if fi in extras.get('ring', ()):  # a wedding ring
            q = joints[0].lerp(joints[1], 0.42); out.append(lathe([(r * 1.02 + 0.003 * math.cos(t), 0.003 * math.sin(t)) for t in (i * math.pi / 3 for i in range(7))], tuple(q), extras['gold'], seg=14, axis='y'))
        if fi in extras.get('plaster', ()):  # a plaster on a paper cut
            q = joints[1].lerp(joints[2], 0.5); out.append(blob('plaster' + hk, tuple(q), (r * 1.08, r * 0.75, r * 1.08), extras['tan'], seg=12, rings=8))
        if fi in extras.get('thimble', ()):  # a rubber finger (for counting the hymn sheets)
            out.append(limb('thimble' + hk, [tuple(joints[2].lerp(joints[3], 0.0)), tuple(joints[2].lerp(joints[3], 0.55)), tuple(joints[3] + dv * 0.004)], [r * 1.1, r * 1.0, r * 0.82], extras['rubber'], seg=10))
    tb = [(-sx * 0.05 * k, -0.04 * k, -0.016), (-sx * 0.078 * k, -0.08 * k, -0.026), (-sx * 0.092 * k, -0.112 * k, -0.03), (-sx * 0.1 * k, -0.138 * k, -0.028)]
    out.append(limb('thumb' + hk, [tb[0], Vector(tb[0]).lerp(Vector(tb[1]), 0.5)[:], tb[1], Vector(tb[1]).lerp(Vector(tb[2]), 0.5)[:], tb[2], tb[3]],
                    [0.02 * k, 0.019 * k, 0.019 * k, 0.017 * k, 0.017 * k, 0.012 * k], skin, seg=10))
    tt, td = Vector(tb[3]), (Vector(tb[3]) - Vector(tb[2])).normalized(); tdors = Vector((-sx * 0.35, 0, 1)).normalized()
    out.append(ell('thumbn' + hk, tuple(tt - td * 0.008 + tdors * 0.0095), (td.cross(tdors).normalized() * 0.009, tdors * 0.0028, td * 0.011), nail, 8, 5))
    return out


def build():
    rng = random.Random(1999 + SQ)
    skin = rubber(ID + '_skin', 0xffffff, tex_canvas(ID + '_skinT', 32, 32, skin_px(SK, SKD, 62 + SQ, SQ)), rough=0.38)
    faceM = rubber(ID + '_face', 0xffffff, tex_canvas(ID + '_faceT', 112, 128, face_px), rough=0.36)  # (stretched shiny)
    nail = rubber(ID + '_nail', 0xe8d8d0 if not SQ else 0xff6fa8, rough=0.25)
    robe = cloth(ID + '_robe', 0xffffff, tex_canvas(ID + '_robeT', 32, 32, robe_px(ROBE, FOLD, LINE, 72 + SQ)))
    lining = cloth(ID + '_lining', 0xffffff, tex_canvas(ID + '_liningT', 8, 8, lining_px(ROBE, 73)))
    ruffM = cloth(ID + '_ruff', 0xffffff, tex_canvas(ID + '_ruffT', 32, 8, ruff_px))
    stoleM = cloth(ID + '_stole', 0xffffff, tex_canvas(ID + '_stoleT', 16, 48, stole_px))
    ribbonM = cloth(ID + '_ribbon', 0xffffff, tex_canvas(ID + '_ribbonT', 8, 40, ribbon_px))
    badgeM = mat(ID + '_badge', 0xffffff, rough=0.25, clearcoat=0.8, tex=tex_canvas(ID + '_badgeT', 36, 46, badge_px))
    chrome = mat(ID + '_chrome', 0xd8dce4, metal=1.0, rough=0.2)
    gold = mat(ID + '_gold', 0xe8b840, metal=1.0, rough=0.25)
    cord = mat(ID + '_cord', 0xffffff, rough=0.6, tex=tex_stripes(ID + '_cordT', STOLE2 if not SQ else 0x8a2a4a, 0xf2ead6 if not SQ else 0x5a1a30, 16, 2))
    hairM = mat(ID + '_hair', 0xffffff, rough=0.7, tex=tex_canvas(ID + '_hairT', 24, 8, hair_px(0x3a2e2a if not SQ else 0x8a5a3a, 74 + SQ)))
    shoeM = mat(ID + '_shoe', 0x18181c, rough=0.18, clearcoat=0.9) if not SQ else mat(ID + '_shoe', 0xf4f0e6, rough=0.45, clearcoat=0.2)
    soleM = mat(ID + '_sole', 0x3a2a20 if not SQ else 0xd8203a, rough=0.6)
    sockM = cloth(ID + '_sock', 0x2a2a3a if not SQ else 0xf4f0e6)
    lipM = rubber(ID + '_lip', 0x9a5a7a if not SQ else 0xd0607a, rough=0.3)
    tan = cloth(ID + '_plaster', 0xe8b888)
    rubberM = mat(ID + '_thimble', 0xff7a3a, rough=0.45, clearcoat=0.3)
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))

    # ================================================================ the head (head space: the skull's centre HC)
    def skull_fn(g, n):
        q = g + Vector(HC); off = Vector((0, 0, 0)); fr = max(0.0, -n.z)
        ex = lambda cx, cy, sx_, sy_: math.exp(-(((q.x - cx) / sx_) ** 2 + ((q.y - cy) / sy_) ** 2))
        if fr > 0.15:
            # the lower face pulled forward into one flat stretched plate behind the smile
            wx = 1 - ss_(MOUTH_HW * 0.85, MOUTH_HW * 1.35, abs(q.x)); wy = ss_(MOUTH_Y - 0.12, MOUTH_Y - 0.06, q.y) * (1 - ss_(MOUTH_Y + SMILE_UP + 0.02, MOUTH_Y + SMILE_UP + 0.08, q.y))
            arc = MOUTH_Y + SMILE_UP * (q.x / MOUTH_HW) ** 2  # (the smile's line)
            zt = MOUTH_Z + 0.009 + 0.012 * (q.x / MOUTH_HW) ** 2 - 0.004 * math.exp(-((q.y - arc + 0.005) / 0.012) ** 2)
            w = wx * wy * min(1.0, fr * 1.6)
            if q.z > zt: off.z += (zt - q.z) * w
            for sx in (-1, 1):  # the cheeks, pulled up hard into two round apples over the corners of the smile
                off.z -= (0.03 if not SQ else 0.038) * ex(sx * MOUTH_HW * 0.8, MOUTH_Y + SMILE_UP + 0.045, 0.05, 0.04) * fr
                off.z += 0.013 * ex(sx * EYE_SEP, EYE_Y, EYE_R * 0.9, EYE_R * 0.9) * fr  # the sockets
            off.z -= 0.012 * ex(0, EYE_Y + EYE_R * 1.7, 0.1, 0.02) * fr  # a brow, worried
            off.z -= (0.016 if not SQ else 0.012) * ex(0, MOUTH_Y - 0.085, 0.05, 0.03) * fr  # a chin
            for sx in (-1, 1):  # the stretch: grooves out from the corners toward the ears
                cx0, cy0 = sx * MOUTH_HW, MOUTH_Y + SMILE_UP
                for dx, dy, dep in ((0.07, 0.075, 0.006), (0.08, 0.028, 0.007), (0.065, -0.022, 0.005)):
                    vx, vy = sx * dx, dy; L2 = vx * vx + vy * vy
                    t = max(0.0, min(1.0, ((q.x - cx0) * vx + (q.y - cy0) * vy) / L2))
                    d = math.hypot(q.x - (cx0 + t * vx), q.y - (cy0 + t * vy))
                    off.z += dep * math.exp(-(d / 0.006) ** 2) * math.sin(math.pi * min(1.0, t * 1.15)) * fr
        if not SQ and q.y > HR[1] * 1.45: off += n * 0.008 * (q.y - HR[1] * 1.45) / (HR[1] * 0.55)  # (a long high dome)
        return off
    skull = sculpt('skull', HC, HR, faceM, skull_fn, seg=44, rings=34)
    flip_uv(skull, (0, FACE_CY, MOUTH_Z), (SW, SH)); skull['keep_uv'] = 1
    skull.data.materials.append(skin); uvd = skull.data.uv_layers.active.data
    for poly in skull.data.polygons:  # (the face picture only where it faces front; the rest is plain skin)
        nb = poly.normal
        c_ = poly.center
        if nb.y > 0.35 and abs(c_.x) < SW * 0.48 and abs(c_.z - FACE_CY) < SH * 0.48: continue
        poly.material_index = 1
        for li in poly.loop_indices:
            v = skull.data.vertices[skull.data.loops[li].vertex_index].co; ax_ = max(range(3), key=lambda k: abs(nb[k]))
            uvd[li].uv = ((v.y, v.z) if ax_ == 0 else (v.x, v.z) if ax_ == 1 else (v.x, v.y))
            uvd[li].uv = (uvd[li].uv[0] / 0.12, uvd[li].uv[1] / 0.12)
    head = [skull]
    # the inside of the mouth: a dark pocket the code lips sit over (so the gap between them never shows skin)
    mp = [(x, MOUTH_Y + SMILE_UP * (x / MOUTH_HW) ** 2 - LIP_R * 0.9, MOUTH_Z + 0.016) for x in (MOUTH_HW * (i / 6 - 1) * 0.9 for i in range(13))]
    head.append(sweep(mp, [0.016] * 13, rubber(ID + '_mouth', 0x3a0a18, rough=0.5), seg=8, squash=(1.0, 0.75), name='mouthbag'))
    if not SQ:
        # a long sad nose: down from between the glasses, a bulb at the end
        nose = limb('nose', [(0, EYE_Y - 0.005, EYE_Z - 0.03), (0, EYE_Y - 0.05, EYE_Z - 0.04), (0, EYE_Y - 0.1, EYE_Z - 0.058), (0, EYE_Y - 0.135, EYE_Z - 0.078), (0, EYE_Y - 0.148, EYE_Z - 0.08)],
                    [0.016, 0.019, 0.024, 0.028, 0.022], skin, seg=12)
        head += [nose, blob('bulb', (0, EYE_Y - 0.137, EYE_Z - 0.083), (0.033, 0.03, 0.03), skin)]
        for sx in (-1, 1): head.append(blob('nostril%d' % sx, (sx * 0.022, EYE_Y - 0.15, EYE_Z - 0.07), (0.016, 0.013, 0.016), skin))
        # big sad ears: a shell standing off the head, a rolled rim, a bowl, long lobes
        for sx in (-1, 1):
            ec = (sx * (HR[0] - 0.006), 0.355, 0.03)
            e = blob('ear%d' % sx, ec, (0.02, 0.07, 0.046), skin, fn=lambda p, n, sx=sx: -0.012 * math.exp(-((p.y - 0.005) ** 2 + (p.z + 0.002) ** 2) / 0.026 ** 2) * max(0.0, n.x * sx), seg=16, rings=12)
            rim = tube([(sx * (HR[0] + 0.006), 0.3, 0.06), (sx * (HR[0] + 0.012), 0.36, 0.078), (sx * (HR[0] + 0.012), 0.41, 0.06), (sx * (HR[0] + 0.01), 0.425, 0.03), (sx * (HR[0] + 0.006), 0.41, 0.004)], 0.01, skin, seg=8, name='helix%d' % sx)
            lobe = blob('lobe%d' % sx, (sx * (HR[0] + 0.0), 0.285, 0.035), (0.015, 0.026, 0.02), skin)
            for q in (e, rim, lobe): rot_about(q, ec, 0.08, sx * 0.38, sx * -0.12); head.append(q)
        # the hair: a horseshoe from above one ear round the back to the other, down to the nape, and a combover: seven
        # thin flat strands from a low parting on the left, plastered over the dome to the right, the scalp between them
        def band(a):  # (head space height of its top / bottom edge at angle a round the head, 0 = the front)
            A = abs(a)
            return (0.47 + 0.035 * ss_(1.4, 2.6, A), 0.41 - 0.2 * ss_(1.5, 2.7, A))
        hb = sculpt('horseshoe', HC, (HR[0] * 1.006, HR[1] * 1.004, HR[2] * 1.006), hairM, lambda g, n: n * (0.0025 * math.sin(math.atan2(g.x, -g.z) * 40)), seg=40, rings=32)
        cut_faces(hb, lambda p: abs(math.atan2(p.x, -p.z)) > 1.32 and band(math.atan2(p.x, -p.z))[1] < p.y < band(math.atan2(p.x, -p.z))[0])
        solid(hb, 0.012, 1.0); apply_mods(hb); uv_hairband(hb); head.append(hb)
        for i in range(7):
            z0 = -0.13 + i * 0.038; pts = []
            for j in range(10):
                u = j / 9; x = -HR[0] * 0.86 + u * HR[0] * 1.62
                pts.append(on_scalp(skull, (x, HC[1] + HR[1] * 0.85, z0 + 0.012 * math.sin(u * 2.5 + i * 1.7)), 0.003))
            rr = [0.007, 0.0095, 0.0105, 0.011, 0.011, 0.0108, 0.0104, 0.0098, 0.008, 0.005]
            head.append(limb('strand%d' % i, pts, rr, hairM, seg=8, squash=(0.3, 1.0)))
    else:
        head.append(blob('nose', (0, EYE_Y - 0.06, EYE_Z - 0.035), (0.034, 0.03, 0.03), skin))  # a button nose
        for sx in (-1, 1): head.append(blob('nostril%d' % sx, (sx * 0.02, EYE_Y - 0.077, EYE_Z - 0.03), (0.014, 0.011, 0.014), skin))
        for sx in (-1, 1):  # small round ears under the perm, a pearl on each
            ec = (sx * (HR[0] - 0.006), 0.22, 0.02)
            head.append(rot_about(blob('ear%d' % sx, ec, (0.014, 0.046, 0.032), skin, fn=lambda p, n, sx=sx: -0.008 * math.exp(-(p.y ** 2 + p.z ** 2) / 0.016 ** 2) * max(0.0, n.x * sx), seg=12, rings=10), ec, 0.1, sx * 0.3, 0))
            head.append(ball(0.011, (sx * (HR[0] + 0.004), 0.177, 0.016), mat(ID + '_pearl', 0xf8f4ec, rough=0.15, clearcoat=0.9), seg=10, rings=8))
        # the perm: a cap of tight curls from the hairline over the top and down to the nape, curls bunched round its edge
        def perm_fn(p, n):
            return 0.012 * (0.5 + 0.5 * math.sin(p.x * 70) * math.sin(p.z * 70) * math.sin(p.y * 60 + 1))
        def edge(a):  # (the hairline's height round her head; a = 0 the front)
            A = abs(a)
            return 0.37 if A < 0.9 else 0.37 - 0.12 * (A - 0.9) / 0.7 if A < 1.6 else 0.25 - 0.14 * (A - 1.6) / (math.pi - 1.6)
        cap = sculpt('perm', HC, (HR[0] * 1.06, HR[1] * 1.12, HR[2] * 1.08), hairM, lambda g, n: n * perm_fn(g, n), seg=36, rings=24)
        cut_faces(cap, lambda p: p.y > edge(math.atan2(p.x, -p.z)) - 0.002)
        head.append(cap)
        for i in range(26):  # the curls round the edge and over the crown, for the silhouette
            a = -math.pi + 2 * math.pi * i / 26 + rng.uniform(-0.05, 0.05)
            y = edge(a) + 0.01
            d = Vector((math.sin(a), 0, -math.cos(a)))
            ny = (y - HC[1]) / (HR[1] * 1.12); ny = max(-0.95, min(0.95, ny)); k_ = math.sqrt(1 - ny * ny)
            c = Vector((d.x * HR[0] * 1.06 * k_, y, d.z * HR[2] * 1.08 * k_))
            head.append(ball(0.038 + rng.uniform(-0.004, 0.006), tuple(c), hairM, seg=9, rings=6))
        for i in range(10):
            a = rng.uniform(-math.pi, math.pi); e_ = rng.uniform(0.35, 1.3)
            d = Vector((math.sin(a) * math.cos(e_), math.sin(e_), -math.cos(a) * math.cos(e_)))
            c = Vector(HC) + Vector((d.x * HR[0] * 1.1, d.y * HR[1] * 1.16, d.z * HR[2] * 1.12))
            if c.y < edge(a) + 0.02: continue
            head.append(ball(0.04 + rng.uniform(-0.005, 0.005), tuple(c), hairM, seg=9, rings=6))
        # a pencil behind the right ear
        pc = (HR[0] + 0.012, 0.27, 0.03)
        head.append(rod((pc[0] - 0.01, pc[1] + 0.07, pc[2] - 0.05), (pc[0] + 0.004, pc[1] - 0.04, pc[2] + 0.07), 0.008, mat(ID + '_pencil', 0xffc830, rough=0.4, clearcoat=0.5), seg=6))
        head.append(rod((pc[0] - 0.01, pc[1] + 0.07, pc[2] - 0.05), (pc[0] - 0.014, pc[1] + 0.085, pc[2] - 0.068), 0.008, mat(ID + '_wood', 0xe8c890, rough=0.6), seg=6, r1=0.0015))
        head.append(rod((pc[0] + 0.004, pc[1] - 0.04, pc[2] + 0.07), (pc[0] + 0.006, pc[1] - 0.052, pc[2] + 0.085), 0.0082, mat(ID + '_eraser', 0xff8aa8, rough=0.5), seg=6))
    add('head', head)

    # ================================================================ the neck (neck space: the head pivot at y 0.02)
    if not SQ:
        nk = [limb('neck', [(0, -0.2, 0.012), (0, -0.08, 0.006), (0, 0.0, 0.0), (0, 0.07, 0.004)], [0.05, 0.044, 0.043, 0.05], skin, seg=14),
              blob('adam', (0, -0.075, -0.04), (0.016, 0.022, 0.014), skin)]  # (an adam's apple: it goes up and down when he sings. it doesn't)
    else:
        nk = [limb('neck', [(0, -0.06, 0.0), (0, 0.0, 0.0), (0, 0.06, 0.004)], [0.085, 0.08, 0.085], skin, seg=14)]
    add('neck', nk)

    # ================================================================ the robe's top, the ruff, the stole, the lanyard, the belt (spine space)
    def tor_fn(p, n):
        a = math.atan2(p.x, -p.z)
        g = max(0.0, min(1.0, (0.3 - p.y) / 0.3))  # (gathered from a yoke over the chest: folds below it)
        return 0.0045 * g * math.sin(a * 11 + 0.6) + 0.002 * math.sin(a * 23)
    tor = [shell('bodice', TOR, robe, seg=48, fn=tor_fn)]
    R_ = RUFF; NT, NP = R_['n'] * 3, 8
    bm = bmesh.new(); rows = []
    for i in range(NT):
        th = 2 * math.pi * i / NT; pl = math.sin(R_['n'] * th)
        row = []
        for j in range(NP):
            ph_ = 2 * math.pi * j / NP; c_, s_ = math.cos(ph_), math.sin(ph_)
            r = R_['R'] + R_['rw'] * c_ + 0.014 * pl * max(0.0, c_) ** 0.7
            y = R_['y'] + R_['rh'] * s_ * (1 + 0.12 * pl)
            row.append(bm.verts.new(gv(r * math.sin(th), y, -r * math.cos(th))))
        rows.append(row)
    for i in range(NT):
        a_, b_ = rows[i], rows[(i + 1) % NT]
        for j in range(NP): bm.faces.new((a_[j], a_[(j + 1) % NP], b_[(j + 1) % NP], b_[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); ruff = lib_obj('ruff', bm, ruffM)
    for p_ in ruff.data.polygons: p_.use_smooth = True
    tor.append(ruff)
    # the stole: over the shoulders from behind the ruff, down the front to the belt, a fringe on each end
    for sx in (-1, 1):
        pts = [(sx * 0.07, RUFF['y'] - 0.01, 0.06), (sx * 0.1, RUFF['y'] - 0.03, -0.02)]
        for y in (TOR[-3][0] - 0.02, TOR[4][0], TOR[3][0], TOR[2][0], TOR[1][0], TOR[0][0] + 0.015):
            x = sx * (0.085 - 0.012 * (TOR[-3][0] - y)); pts.append((x, y, front_z(x, y, 0.006)))
        tor.append(sweep(pts, [0.03] * len(pts), stoleM, seg=8, squash=(0.22, 1.0), name='stole%d' % sx))
        x = pts[-1][0]; y = pts[-1][1]
        for f_ in range(5): tor.append(rod((x - 0.02 + f_ * 0.01, y - 0.004, front_z(x, y, 0.008)), (x - 0.02 + f_ * 0.01, y - 0.045, front_z(x, y, 0.012) - 0.004), 0.003, cord, seg=4))
    # the lanyard: out from under the ruff, a V down the robe to the clip, the staff badge (tilted: it's been there years)
    bx, by = (0.03, TOR[2][0] - 0.005) if not SQ else (0.035, TOR[2][0] + 0.02)  # (on a long lanyard: below the hymns, where you can see it)
    for sx in (-1, 1):
        x0 = sx * 0.045; y0 = RUFF['y'] - RUFF['rh'] - 0.005
        pts = [(x0, y0, front_z(x0, y0, 0.012))]
        for i in range(1, 5):
            u = i / 4; x = x0 + (bx + sx * 0.008 - x0) * u; y = y0 + (by + 0.07 - y0) * u
            pts.append((x, y, front_z(x, y, 0.0085)))
        tor.append(sweep(pts, [0.009] * len(pts), ribbonM, seg=6, squash=(1.0, 0.25), name='lanyard%d' % sx))
    cz = front_z(bx, by + 0.065, 0.012)
    tor.append(rod((bx, by + 0.075, cz), (bx, by + 0.055, cz - 0.002), 0.006, chrome, seg=8))  # the clip
    bz = front_z(bx, by, 0.012)
    Nb = Vector((0, 0.17, -1)).normalized(); Ub = Vector((-math.cos(0.12), math.sin(0.12), 0)); Ub = (Ub - Nb * Ub.dot(Nb)).normalized(); Vb = Nb.cross(Ub)
    if Vb.y < 0: Vb = -Vb
    bd = slab('badge', (bx, by, bz - 0.002), tuple(Ub), tuple(Vb), tuple(Nb), 0.075, 0.098, 0.004, badgeM)
    tor.append(bd)
    # the belt: a cord round the waist, a knot on the left, two ends with tassels
    yb = TOR[1][0] + 0.005
    bp = []
    for k in range(40):
        a = 2 * math.pi * k / 40; rx, rzf, rzb, pw = tor_at(yb)
        c_, s_ = math.cos(a), math.sin(a); rz = rzb if s_ > 0 else rzf
        bp.append((rx * 1.03 * math.copysign(abs(c_) ** (2 / pw), c_), yb, rz * 1.04 * math.copysign(abs(s_) ** (2 / pw), s_)))
    tor.append(tube(bp, 0.013, cord, seg=8, name='belt', closed=True))
    kx = -tor_at(yb)[0] * 0.75; kz = front_z(kx, yb, 0.015)
    tor.append(blob('knot', (kx, yb, kz), (0.024, 0.022, 0.02), cord))
    for j, dx in enumerate((-0.012, 0.014)):
        e = [(kx + dx, yb - 0.01, kz), (kx + dx * 1.4, yb - 0.07, kz - 0.006), (kx + dx * 1.8, yb - 0.14, kz - 0.012)]
        tor.append(sweep(e, [0.009, 0.009, 0.009], cord, seg=6, name='end%d' % j))
        tor.append(lathe([(0.0, 0.0), (0.012, -0.004), (0.018, -0.03), (0.014, -0.05), (0.0, -0.052)], e[-1], cord, seg=10, axis='y'))
    # the back: the company's patch, the smiling butcher, sewn on (a choir robe with a logo on the back, like a team's)
    tor.append(back_patch(tor[0], (0, TOR[4][0] - 0.04), 0.075 if not SQ else 0.09, mat(ID + '_patch', 0xffffff, rough=0.6, tex=tex_canvas(ID + '_patchT', 32, 32, patch_px))))
    add('spine', tor)

    # ================================================================ arms: bell sleeves that hang in the reading pose
    fk = stance_fk()
    for k, fk_, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        R_up = UPPER
        up = [blob('shoulder' + k, (-sx * 0.006, -0.015, 0), (0.078 if not SQ else 0.085, 0.07, 0.078), robe),
              limb('upper' + k, [(0, -0.02, 0), (0, -R_up * 0.5, 0.002), (0, -R_up, 0)], [0.07, 0.072, 0.078] if not SQ else [0.074, 0.076, 0.08], robe, seg=16)]
        add(k, up)
        # the fore: from the elbow, widening to a deep cuff; the cuff's lower side hangs (down, in the stance pose)
        Wf = fk[fk_]; gdn = np.linalg.inv(Wf[:3, :3]) @ np.array((0, -1, 0.0))
        gperp = Vector((gdn[0], 0, gdn[2]));
        gperp = gperp.normalized() if gperp.length > 1e-4 else Vector((0, 0, 1))
        cl = -HAND_Y - 0.03; r0, r1 = (0.078, 0.15) if not SQ else (0.08, 0.15)  # (to just short of the wrist)
        NA, NR = 32, 10
        def sleeve_pt(i, j, inset):
            a = 2 * math.pi * i / NA; t = j / (NR - 1)
            d = Vector((math.cos(a), 0, math.sin(a)))
            hang = max(0.0, d.dot(gperp))
            r = r0 + (r1 - r0) * t ** 1.4 + 0.006 * math.sin(a * 7 + sx) * t
            y = -cl * t - 0.07 * hang ** 1.5 * t ** 2  # (the hanging side runs longer)
            dd = d * (r - inset) + gperp * 0.035 * hang * t ** 2
            return Vector((dd.x, y, dd.z))
        bm = bmesh.new(); sr = []
        for j in range(NR): sr.append([bm.verts.new(gv(*sleeve_pt(i, j, 0))) for i in range(NA)])
        T_ = 0.012
        sr.append([bm.verts.new(gv(*(sleeve_pt(i, NR - 1, T_ * 0.5) + Vector((0, -0.006, 0))))) for i in range(NA)])
        for j in range(NR - 1, 1, -3): sr.append([bm.verts.new(gv(*sleeve_pt(i, j, T_))) for i in range(NA)])
        for a_, b_ in zip(sr, sr[1:]):
            for i in range(NA): bm.faces.new((a_[i], a_[(i + 1) % NA], b_[(i + 1) % NA], b_[i]))
        for i in range(NA): bm.faces.new((sr[-1][i], sr[-1][(i + 1) % NA], sr[0][(i + 1) % NA], sr[0][i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        sl = lib_obj('sleeve' + fk_, bm, robe)
        for p_ in sl.data.polygons: p_.use_smooth = True
        fo = [sl, blob('elbow' + fk_, (0, 0.0, 0.002), (0.08, 0.075, 0.08) if not SQ else (0.083, 0.078, 0.083), robe),
              limb('arm' + fk_, [(0, -cl * 0.45, 0), (0, HAND_Y + 0.05, 0), (0, HAND_Y + 0.004, 0.0)], [0.04, 0.036, 0.036], skin, seg=10)]
        add(fk_, fo)
        ex = {'gold': gold, 'tan': tan, 'rubber': rubberM}
        if not SQ: ex.update({'ring': (2,) if sx < 0 else (), 'plaster': (0,) if sx > 0 else ()})
        else: ex.update({'thimble': (0,) if sx > 0 else (), 'ring': (2,) if sx < 0 else ()})
        add(hk, hand(hk, sx, skin, nail, ex))

    # ================================================================ the hymns, on the left palm (placed through the stance)
    WL, WR = fk['handL'], fk['handR']
    pL = (WL @ np.array((0.0, -0.11 * HK, -0.026 * HK, 1)))[:3]; pR = (WR @ np.array((0.0, -0.11 * HK, -0.026 * HK, 1)))[:3]
    nL, nR = -WL[:3, 2], -WR[:3, 2]
    N = (nL + nR); N /= np.linalg.norm(N)
    U = pR - pL; U -= N * U.dot(N); U /= np.linalg.norm(U)
    Vv = np.cross(N, U)  # (up the page: away from the reader)
    if not SQ:
        thick = 0.012; C = (pL + pR) / 2 + N * 0.026; C[0] = 0.0  # (its covers on the fingers)
        T = frame(C, U, Vv, N)
        bmat = mat(ID + '_binder', 0x1a1a22, rough=0.22, clearcoat=0.8)
        labelM = mat(ID + '_label', 0xffffff, rough=0.4, tex=tex_canvas(ID + '_labelT', 36, 24, label_px))
        pageL = cloth(ID + '_pageL', 0xffffff, tex_canvas(ID + '_pageLT', 36, 36, pages_px(True)))
        pageR = cloth(ID + '_pageR', 0xffffff, tex_canvas(ID + '_pageRT', 36, 36, pages_px(False)))
        pageE = cloth(ID + '_pagee', 0xf2ead4)
        W_, H_, open_ = 0.235, 0.31, 0.16  # a cover each side, opened to a shallow V
        B = []
        for side_, pm in ((-1, pageL), (1, pageR)):
            ca, sa = math.cos(open_), math.sin(open_)
            ux = Vector((side_ * ca, 0, sa)); cc = ux * (W_ / 2 + 0.012)
            B.append(slab('cover%d' % side_, tuple(cc - Vector((0, 0, 0.0035))), tuple(ux * side_), (0, 1, 0), tuple(Vector((-sa * side_, 0, ca)) * side_ * side_), W_, H_, 0.006, bmat, bev=0.002))
            pg = slab('pages%d' % side_, tuple(cc + Vector((0, 0, 0)) + Vector((-sa * side_, 0, ca)) * 0.01 - ux * 0.006), tuple(ux * side_), (0, 1, 0), tuple(Vector((-sa * side_, 0, ca))), W_ - 0.03, H_ - 0.022, 0.013, pageE)
            B.append(pg)
            B.append(decal_q('print%d' % side_, tuple(cc + Vector((-sa * side_, 0, ca)) * 0.0185 - ux * 0.006), tuple(Vector((ca, 0, side_ * sa))), (0, 1, 0), W_ - 0.05, H_ - 0.04, pm))
        B.append(slab('spine', (0, 0, -0.0035), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.03, H_, 0.006, bmat, bev=0.002))
        for k in (-1, 0, 1): B.append(lathe([(0.012 + 0.0022 * math.cos(a), 0.0022 * math.sin(a)) for a in (i * math.pi / 3 for i in range(7))], (0, k * 0.09, 0.006), chrome, seg=14, axis='y'))  # the rings
        ul = Vector((-math.cos(open_), 0, math.sin(open_))); nl = Vector((math.sin(open_), 0, math.cos(open_)))
        B.append(decal_q('label', tuple(ul * (W_ / 2 + 0.012) - Vector((0, 0, 0.0035)) - nl * 0.0052 + Vector((0, 0.04, 0))), tuple(ul), (0, 1, 0), 0.1, 0.066, labelM))  # (on the back of the left cover: what you see from the front)
        place(B, to_local('handL', T))
        add('handL', B)
    else:
        C = (pL + pR) / 2 + N * 0.022; C[0] = 0.0
        T = frame(C, U, Vv, N)
        board = mat(ID + '_board', 0xffffff, rough=0.5, clearcoat=0.3, tex=tex_canvas(ID + '_boardT', 32, 44, clip_px))
        sheetM = cloth(ID + '_sheet', 0xffffff, tex_canvas(ID + '_sheetT', 36, 48, sheet_px))
        W_, H_ = 0.3, 0.4
        B = [slab('board', (0, 0, 0), (-1, 0, 0), (0, 1, 0), (0, 0, -1), W_, H_, 0.008, board, bev=0.002)]
        B.append(slab('sheet', (0, -0.012, 0.0055), (1, 0, 0), (0, 1, 0), (0, 0, 1), W_ - 0.035, H_ - 0.06, 0.003, sheetM))
        B.append(slab('clip', (0, H_ / 2 - 0.03, 0.011), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.1, 0.045, 0.008, chrome, bev=0.003))  # (its back on the sheet's face)
        B.append(rod((-0.035, H_ / 2 - 0.01, 0.016), (0.035, H_ / 2 - 0.01, 0.016), 0.005, chrome, seg=8))
        B.append(rod((0.07, H_ / 2 - 0.05, 0.012), (0.075, -H_ / 2 + 0.08, 0.016), 0.0055, mat(ID + '_pen', 0x2a5ad0, rough=0.3, clearcoat=0.6), seg=8))  # a pen under the clip
        place(B, to_local('handL', T))
        add('handL', B)

    # ================================================================ tiny office shoes (knee space, leg-scaled: built at world size)
    ls = JD['legScale']
    for kn, sx in (('kneeL', -1), ('kneeR', 1)):
        floor_y = -JD['joints'][kn][1]  # (the floor, below the knee, world metres)
        sh = []
        L_ = 0.15 if not SQ else 0.135
        z0 = -0.09 if not SQ else -0.11  # (set forward under the robe so the toes peek out of the hem)
        def shoe_fn(p, n, L_=L_):
            off = 0.0
            if p.z < -L_ * 0.18: off -= 0.012 * min(1.0, (-L_ * 0.18 - p.z) / (L_ * 0.3)) * max(0.0, n.y)  # (the toe goes down)
            if n.y < -0.3 and p.y < -0.012: off += (-0.012 - p.y) / n.y  # a flat sole
            return off
        sc = Vector((0, floor_y + 0.03, z0 - L_ / 2))
        if not SQ:  # black loafers, pointy, shiny
            sh.append(blob('shoe' + kn, tuple(sc), (0.04, 0.032, L_ / 2), shoeM, fn=lambda p, n, f=shoe_fn: f(p, n) - (0.006 * max(0.0, -p.z / (L_ * 0.5)) ** 2 if abs(p.x) > 0.02 else 0), seg=16, rings=12))
            sh.append(blob('sole' + kn, tuple(sc + Vector((0, -0.016, 0))), (0.042, 0.012, L_ / 2 + 0.004), soleM, seg=16, rings=6))
            sh.append(box((0.03, 0.006, 0.02), tuple(sc + Vector((0, 0.025, -L_ * 0.12))), soleM, bev=0.002))  # the loafer's strap
        else:  # white trainers, pink laces
            sh.append(blob('shoe' + kn, tuple(sc), (0.042, 0.034, L_ / 2), shoeM, fn=shoe_fn, seg=16, rings=12))
            sh.append(blob('sole' + kn, tuple(sc + Vector((0, -0.018, 0))), (0.046, 0.013, L_ / 2 + 0.005), soleM, seg=16, rings=6))
            for i in range(3): sh.append(rod((-0.022, sc.y + 0.024 + i * 0.002, sc.z - 0.01 - i * 0.017), (0.022, sc.y + 0.026 + i * 0.002, sc.z - 0.004 - i * 0.017), 0.0035, mat(ID + '_lace', 0xff4fd8, rough=0.5), seg=4))
        sh.append(limb('sock' + kn, [(0, floor_y + 0.045, z0 - L_ * 0.25), (0, floor_y + 0.12, z0 * 0.4), (0, floor_y + 0.24, 0.0)], [0.025, 0.026, 0.03], sockM, seg=10))
        for o in sh:  # (built at world size: shrink by the leg's scale, which the joint puts back)
            apply_mods(o); o.data.transform(Matrix.Scale(1 / ls, 4))
        add(kn, sh)

    root = parts_root(ID, P, {'face': True, 'skirt': 'skinned: body, legL, legR'})
    # the skirt, skinned (not joined: its own mesh, its own armature)
    sk, first_lining = skirt('part_body_skirt', robe, lining)
    in_joint(ID, 'body', [sk])
    skirt_lining(sk, first_lining)
    arm = make_rig(root)
    skin_skirt(sk, arm)
    return root, sk, arm


def ss_(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if b != a else (1.0 if x >= b else 0.0)
    return t * t * (3 - 2 * t)


def cut_faces(o, keep):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    dead = [f for f in bm.faces if not keep(Vector((f.calc_center_median().x, f.calc_center_median().z, -f.calc_center_median().y)))]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(me); bm.free()
    return o


# ------------------------------------------------------------ export + pictures
def export_all(root, arm):
    """the rigid parts, the armature and the skinned skirt in one glb"""
    os.makedirs(MODELS, exist_ok=True)
    for s_ in bpy.context.view_layer.objects.selected: s_.select_set(False)
    root.select_set(True)
    for c in root.children_recursive: c.select_set(True)
    path = os.path.join(MODELS, 'cast', 'c_' + ID + '.glb')
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_extras=True, export_yup=True, export_texcoords=True,
              export_normals=True, export_materials='EXPORT', export_image_format='AUTO', export_lights=False, export_cameras=False, export_skins=True, export_animations=False)
    props = bpy.ops.export_scene.gltf.get_rna_type().properties
    if 'export_all_influences' in props: kw['export_all_influences'] = False
    bpy.ops.export_scene.gltf(**kw)
    tris, lo, hi = stats(root)
    print(f'JF_EXPORT {ID}: {os.path.getsize(path) // 1024} KB, {tris} tris, y {lo[1]:.3f}..{hi[1]:.3f}')
    return path


def face_preview(root):
    """not exported: the code face rig's eyes, lids, brows, lips, glasses, roughly, so the sheets' faces read like the game's"""
    white = mat('pv_white', 0xf6f2e8, rough=0.15); iris = mat('pv_iris', 0xc8d850 if not SQ else 0x5aa0d0, rough=0.2); pup = mat('pv_pupil', 0x0a0a0a)
    lid = rubber('pv_lid', SK); brow = mat('pv_brow', 0x3a2e2a if not SQ else 0x6a4a3a, rough=0.6); lip = rubber('pv_lip', 0x9a5a7a if not SQ else 0xd0607a, rough=0.3)
    teeth = rubber('pv_teeth', 0xf2e6a0 if not SQ else 0xfafaf2, rough=0.25)
    objs = []
    for sx in (-1, 1):
        e = Vector((sx * EYE_SEP, EYE_Y, EYE_Z))
        objs.append(ball(EYE_R, tuple(e), white, seg=14, rings=10))
        objs.append(ball(EYE_R * 0.55, tuple(e + Vector((sx * -0.004, -0.006, -EYE_R * 0.92))), iris, scale=(1, 1, 0.3), seg=12, rings=8))
        objs.append(ball(EYE_R * 0.27, tuple(e + Vector((sx * -0.004, -0.006, -EYE_R * 1.0))), pup, scale=(1, 1, 0.3), seg=8, rings=6))
        objs.append(ball(EYE_R * 1.12, tuple(e + Vector((0, EYE_R * 0.32, -0.003))), lid, scale=(1, 0.66, 1), seg=14, rings=8))
        objs.append(box((0.06 * (1.35 if not SQ else 1.3), 0.024, 0.025), (sx * EYE_SEP, EYE_Y + EYE_R * 1.45 + 0.012, EYE_Z - EYE_R * 0.25), brow, rot=(0, 0, sx * 0.33)))
        if not SQ:
            gr = torus_ring((sx * EYE_SEP * 1.05, EYE_Y, EYE_Z - EYE_R * 0.95), EYE_R * 1.7, EYE_R * 0.16, mat('pv_glass', 0x2a2a30, rough=0.4))
            objs.append(gr)
    if not SQ: objs.append(box((EYE_SEP * 0.5, EYE_R * 0.2, EYE_R * 0.2), (0, EYE_Y + EYE_R * 0.3, EYE_Z - EYE_R * 0.95), mat('pv_glass', 0x2a2a30, rough=0.4)))
    for k in (0, 1):
        pts = []
        for i in range(9):
            u = i / 8 - 0.5; x = u * 2 * MOUTH_HW
            y = MOUTH_Y + SMILE_UP * (2 * u) ** 2 * (1 if k == 0 else 0.8) - (0 if k == 0 else LIP_R * 1.7)
            pts.append((x, y, MOUTH_Z - (0 if k == 0 else 0.002)))
        objs.append(limb('pvlip%d' % k, pts, [LIP_R * (0.8 if i in (0, 8) else 1.0) for i in range(9)], lip, seg=8))
    n = 4 if not SQ else 9
    for i in range(n):
        x = (i / (n - 1) - 0.5) * 2 * MOUTH_HW * 0.75; y = MOUTH_Y + SMILE_UP * (x / MOUTH_HW) ** 2 - LIP_R * 1.1
        if not SQ: objs.append(box((MOUTH_HW * 2 * 0.13 / 2.05 * 1.6, LIP_R * 2.2, LIP_R), (x, y - LIP_R * 0.4, MOUTH_Z + 0.004), teeth))
        else: objs.append(rod((x, y + LIP_R * 0.2, MOUTH_Z + 0.004), (x, y - LIP_R * 1.6, MOUTH_Z + 0.004), LIP_R * 0.45, teeth, seg=4, r1=0.0005))
    out = in_joint(ID, 'head', objs)
    pv = join(out, 'preview_face'); pv.parent = root; pv.matrix_parent_inverse = Matrix.Identity(4)
    return pv


def torus_ring(c, R, r, m):
    bm = bmesh.new(); n, k = 24, 6; rows = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rows.append([bm.verts.new(gv(c[0] + (R + r * math.cos(2 * math.pi * j / k)) * math.cos(a), c[1] + (R + r * math.cos(2 * math.pi * j / k)) * math.sin(a), c[2] + r * math.sin(2 * math.pi * j / k))) for j in range(k)])
    for i in range(n):
        for j in range(k): bm.faces.new((rows[i][j], rows[i][(j + 1) % k], rows[(i + 1) % n][(j + 1) % k], rows[(i + 1) % n][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib_obj('ring', bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def pose_sheet(root):
    """the sheets show the game's stance: arms up, the hymns open (looks.js CHOIR_STANCE)"""
    fk = stance_fk(); C = np.array(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)), float)
    for j in ('armL', 'foreL', 'handL', 'arm', 'foreR', 'handR'):
        T = C @ (fk[j] @ np.linalg.inv(M4(JD['mats'][j]))) @ np.linalg.inv(C)
        for o in root.children:
            if o.name == 'part_' + j or o.name.startswith('part_%s__' % j): o.matrix_world = Matrix(T.tolist()) @ o.matrix_world


def closeups(root):
    """the face (front, 3/4, side), the hands and the hymns, the badge, the shoes -> sheets/c_<id>_closeups.jpg"""
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 520, 520
    cam = sc.camera
    Mh = joint_matrix(ID, 'head'); hc = Mh @ gv(0, (EYE_Y + MOUTH_Y) / 2, 0); fwd = (Mh.to_3x3() @ gv(0, 0, -1)).normalized()
    side = (Mh.to_3x3() @ gv(1, 0, 0)).normalized()
    fk = stance_fk(); hp = Vector(((fk['handL'][:3, 3] + fk['handR'][:3, 3]) / 2).tolist())
    hb = gv(*hp)
    sp = joint_matrix(ID, 'spine')
    badge = sp @ gv(0.04, TOR[3][0] + 0.02, -0.15)
    foot = gv(0, 0.05, -0.15)
    shots = [(hc, hc + fwd * 0.95 + Vector((0, 0, 0.04)), 60), (hc, hc + (fwd * 0.75 + side * 0.55) + Vector((0, 0, 0.05)), 60), (hc, hc + side * 0.95, 60),
             (hb + Vector((0, 0, 0.05)), hb + Vector((0.25, 0.75, 0.45)), 45), (badge, badge + Vector((0.1, 0.55, 0.12)), 45), (foot, foot + Vector((0.35, 0.75, 0.25)), 45)]
    out = []
    tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True)
    for i, (tg, cp, lens) in enumerate(shots):
        cam.location = cp; cam.data.lens = lens; cam.data.clip_start = 0.01; d = tg - cp; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        pth = os.path.join(tmp, 'cu_%s_%d.png' % (ID, i)); sc.render.filepath = pth; bpy.ops.render.render(write_still=True); out.append(pth)
    dst = os.path.join(SHEETS, 'c_%s_closeups.jpg' % ID)
    os.system('ffmpeg -loglevel error -y ' + ' '.join('-i "%s"' % q for q in out) + ' -filter_complex "xstack=inputs=6:layout=0_0|w0_0|w0+w1_0|0_h0|w0_h0|w0+w1_h0" -q:v 3 "%s"' % dst)
    for q in out: os.remove(q)
    print('JF_SHEET', dst)


def head_views(root):
    """the back and sides of the head up close -> sheets/c_<id>_head.jpg"""
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 480, 480
    cam = sc.camera; hc = joint_matrix(ID, 'head') @ gv(0, HR[1], 0.0)
    out = []; tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True)
    for i, (deg, up) in enumerate(((180, 0.05), (220, 0.1), (140, 0.1), (90, 0.03), (270, 0.03), (180, 0.6))):
        a = math.radians(deg); d = Vector((math.sin(a), math.cos(a), up)).normalized()
        cam.location = hc + d * (1.5 if not SQ else 1.25); cam.data.lens = 60; cam.data.clip_start = 0.01
        dd = hc - cam.location; cam.rotation_euler = dd.to_track_quat('-Z', 'Y').to_euler()
        pth = os.path.join(tmp, 'hv_%s_%d.png' % (ID, i)); sc.render.filepath = pth; bpy.ops.render.render(write_still=True); out.append(pth)
    dst = os.path.join(SHEETS, 'c_%s_head.jpg' % ID)
    os.system('ffmpeg -loglevel error -y ' + ' '.join('-i "%s"' % q for q in out) + ' -filter_complex "xstack=inputs=6:layout=0_0|w0_0|w0+w1_0|0_h0|w0_h0|w0+w1_h0" -q:v 3 "%s"' % dst)
    for q in out: os.remove(q)
    print('JF_SHEET', dst)


def main():
    reset()
    root, sk, arm = build()
    for o in root.children_recursive:
        if o.type == 'MESH': me = o.data; me.calc_loop_triangles(); print('JF_PART', o.name, len(me.loop_triangles))
    if '--no-export' not in argv: export_all(root, arm)
    if '--no-sheet' in argv: return
    face_preview(root)
    pose_sheet(root)
    cast_sheet(root, ID, note=('THE GUT CHOIR, tall (the stance; face = the code rig)' if not SQ else 'THE GUT CHOIR, squat (the stance; face = the code rig)'))
    closeups(root)
    head_views(root)


main()
