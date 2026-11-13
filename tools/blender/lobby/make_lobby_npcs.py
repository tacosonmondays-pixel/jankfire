# The zombies lobby's three people as Blender characters (public/js/lobbyscenes/warehouse.js; docs/menu/LOBBY_SCENES.md):
#   DEB    PASSIVES. tired admin lady at her tanker desk: a pink cardigan over a frilly blouse, cat-eye readers low on her
#          nose on a bead chain, a grey bun with a pencil through it, HELLO MY NAME IS DEB, a rubber stamp in her left
#          hand, a taped-up office chair with a caster missing, bunny slippers (one on backwards)
#   GUS    PISTOLS. the gun counter guy (make_lobby_gus below)
#   MARGE  THE ITEM. the quartermaster on her crates (make_lobby_marge below)
# One skinned mesh each on its own skeleton (npckit.py), clips baked in: idle (loop), talk (loop), gesture (once).
# Placed by the game against the Blender props (x_lobby_whprops): meta.place says where, in the prop's own frame.
#   blender52 -b --python tools/blender/lobby/make_lobby_npcs.py -- [--only=deb,gus] [--no-sheet] [--no-export] [--qa]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from npckit import *  # noqa

ONLY = next((a.split('=', 1)[1].split(',') for a in ARGV if a.startswith('--only=')), None)
DESK_TOP = 0.96  # the props' desk top (metres)


def cm(v): return v / S  # metres -> mannequin units (prop sizes are real metres)


def skin_col(base, cheek=None, cheeks=((-0.068, 1.733), (0.068, 1.733)), r=0.03):
    """a skin colour fn: rouge on the cheeks (front of the egg only)"""
    def f(p):
        if cheek is None or p[2] > -0.07: return base
        for cx, cy in cheeks:
            d = math.hypot(p[0] - cx, p[1] - cy)
            if d < r:
                k = (1 - d / r) ** 1.5 * 0.7
                a, b = hexrgb(base), hexrgb(cheek); c = a * (1 - k) + b * k
                return (int(c[0] * 255) << 16) | (int(c[1] * 255) << 8) | int(c[2] * 255)
        return base
    return f


# ================================================================== the face kit (shared, tuned per person)
def face(C, skin, lid_col, brow_col, lips=None, nose=(0.017, 0.026, 0.02), nose_off=(0, 0, 0), lid_shut=0.0, cheek=None, ears=True,
         brow=dict(w=0.036, arch=0.006, tilt=0.0, r=0.006)):
    """eyes + lids + brows + nose + ears + the puppet jaw. lid_shut: 0 = lids modelled at half-mast (tired), the clip opens them"""
    H = C.J
    C.add(egg('egg'), 'head', 'gloss', skin_col(skin, cheek), 'skin', span=0.4)
    for s, sx in (('L', -1), ('R', 1)):
        x = sx * EYE_X; z0 = ez(x, EYE_Y)
        C.add(blob('eye' + s, (x, EYE_Y, z0 + 0.008), (0.024, 0.02, 0.013), None, seg=16, rings=10), 'head', 'gloss', 0xf6f2e8, 'plastic')
        C.add(blob('pupil' + s, (x * 0.96, EYE_Y - 0.002, z0 - 0.0045), (0.0095, 0.011, 0.005), None, seg=12, rings=8), 'head', 'gloss', 0x1a1420, 'plastic')
        # the lid: a closed half-dome over the top of the eye (its flat face at the eye's middle), turned by lid<s>
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-6], context='VERTS')
        bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
        for v in bm.verts:
            bx, by, bzz = v.co
            g = Vector((bx * 0.029, bzz * 0.025, -by * 0.024)); v.co = gv(x + g.x, H['lid' + s][1][1] + g.y, H['lid' + s][1][2] + g.z)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        lid = lib._obj('lid' + s, bm, None)
        for pp in lid.data.polygons: pp.use_smooth = True
        if lid_shut: move([lid], R=(-lid_shut, 0, 0), pivot=H['lid' + s][1])
        C.add(lid, 'lid' + s, 'gloss', lid_col, 'skin')
        # brows: a bar following the egg, arched
        bw, ba, bt, br = brow['w'], brow['arch'], brow['tilt'] * sx, brow['r']
        bx0 = H['brow' + s][1]
        pts = []
        for i in range(7):
            u = i / 6 - 0.5; xx = bx0[0] + u * bw; yy = bx0[1] + ba * (1 - (2 * u) ** 2) + brow['tilt'] * u * sx
            pts.append((xx, yy, ez(xx, yy) - 0.004))
        C.add(limb('brow' + s, pts, [br * 0.6, br * 0.9, br, br, br * 0.95, br * 0.8, br * 0.55], None, seg=8), 'brow' + s, 'gloss', brow_col, 'hair')
        if ears:
            C.add(blob('ear' + s, (sx * 0.117, 1.762, 0.008), (0.013, 0.03, 0.021), None, seg=12, rings=8,
                       fn=lambda p, n, sx=sx: -0.006 * max(0.0, n.x * sx) * math.exp(-(p.y ** 2 + p.z ** 2) / 0.0004)), 'head', 'gloss', skin, 'skin')
    nz = ez(0, 1.752) - nose[2] * 0.55
    C.add(blob('nose', (nose_off[0], 1.752 + nose_off[1], nz + nose_off[2]), nose, None, seg=14, rings=10), 'head', 'gloss', skin, 'skin')
    # the mouth: upper lip on the head, a dark pocket behind, the jaw plate (chin + lower lip) hinged at the ears
    lip_c = lips or skin
    C.add(limb('lipU', [(x, 1.704, ez(x, 1.704) - 0.003) for x in (-0.032, -0.02, 0, 0.02, 0.032)], [0.003, 0.0052, 0.0058, 0.0052, 0.003], None, seg=8), 'head', 'gloss', lip_c, 'skin')
    C.add(blob('mouth', (0, 1.69, ez(0, 1.69) + 0.007), (0.031, 0.017, 0.012), None, seg=14, rings=8), 'head', 'gloss', 0x3a0a18, 'plastic')
    C.add(blob('tongue', (0, 1.682, ez(0, 1.682) + 0.002), (0.018, 0.006, 0.01), None, seg=10, rings=6), 'head', 'gloss', 0xc85a6a, 'plastic')
    C.add(blob('jawplate', (0, 1.656, ez(0, 1.656) + 0.024), (0.056, 0.042, 0.047), None, seg=18, rings=12,
               fn=lambda p, n: -0.01 * max(0.0, n.y) * max(0.0, -n.z)), 'jaw', 'gloss', skin, 'skin')
    C.add(limb('lipD', [(x, 1.6895, ez(x, 1.6895) - 0.006) for x in (-0.029, -0.017, 0, 0.017, 0.029)], [0.003, 0.0055, 0.0064, 0.0055, 0.003], None, seg=8), 'jaw', 'gloss', lip_c, 'skin')


def arm_sleeve(C, s, sh, top_r, col, kind='cloth', pat='knit', upper=True, fore=True, cuff=True, fore_skin=None, short=False):
    """sleeve: shoulder cap + upper tube on arm<s>, elbow ball + forearm tube on fore<s>, a cuff"""
    sx = -1 if s == 'L' else 1; x = sx * sh
    if upper:
        C.add(ball(top_r * 1.05, (x, 1.45, 0), None, seg=16, rings=10, name='cap' + s), 'arm' + s, kind, col, pat)
        y1 = 1.3 if short else 1.17
        C.add(limb('upper' + s, [(x, 1.47, 0), (x, 1.36, 0.002), (x, y1, 0)], [top_r, top_r * 0.95, top_r * (1.02 if short else 0.9)], None, seg=14), 'arm' + s, kind, col, pat)
        if short: C.add(lathe([(top_r * 1.0, 0.0), (top_r * 1.08, 0.004), (top_r * 1.08, 0.018), (top_r * 0.98, 0.022)], (x, y1 - 0.02, 0), None, seg=14, axis='y', name='hem' + s), 'arm' + s, kind, col, pat)
    if fore:
        C.add(ball(top_r * 0.92, (x, 1.17, 0), None, seg=14, rings=10, name='elbow' + s), 'fore' + s, kind, col, pat)
        C.add(limb('fore' + s, [(x, 1.17, 0), (x, 1.06, -0.003), (x, 0.965, 0)], [top_r * 0.9, top_r * 0.86, top_r * 0.8], None, seg=14), 'fore' + s, kind, col, pat)
        if cuff:
            C.add(lathe([(top_r * 0.62, 0.0), (top_r * 0.86, 0.002), (top_r * 0.86, 0.03), (top_r * 0.62, 0.034)], (x, 0.94, 0), None, seg=16, axis='y', name='cuff' + s), 'fore' + s, kind, col, pat)


def hand(C, s, sh, skin, curl, thumb, fing_bone=None, thumb_bone=None, k=1.0, tilt=None):
    """a hand on hand<s> at the wrist (s = L / R); fing_bone / thumb_bone: those parts ride their own bones"""
    palm, fing, th = hand_r(curl, thumb, k)
    allp = palm + [o for f in fing for o in f] + th
    if s == 'L': mirror(allp)
    x = (-1 if s == 'L' else 1) * sh
    move(allp, (x, 0.925, 0))
    C.many(palm, 'hand' + s, 'gloss', skin, 'skin')
    for f in fing: C.many(f, fing_bone or 'hand' + s, 'gloss', skin, 'skin')
    C.many(th, thumb_bone or 'hand' + s, 'gloss', skin, 'skin')


FIST = [(-1.32, -1.48), (-1.5, -1.56), (-1.46, -1.62), (-1.3, -1.5)]  # (a natural fist: each finger curls its own amount, so the segments interleave, not stack into one plane)
FIST_HOLE = (-0.031, -0.069, 0.0)  # where a fist's grip passes (right hand, round the origin), along z


# ================================================================== DEB
DEB = dict(skin=0xe0ac69, cardi=0xf27ac0, cardi_dk=0xc04a90, blouse=0xfaf0f4, skirt=0x3a3a4a, tights=0xc89a78, hair=0xa290cc,
           hair_dk=0x7a6a9e, lips=0xc8204a, frames=0xff2a6a, chair=0x6a3a8a, slipper=0xffb0d8)
# where she sits: in the desk's own frame (x_lobby_whprops 'desk'), facing the desk's +z (the customer's side)
DEB_AT = (0.22, -0.8)


def deb_hand_stamp(C, sh):
    """her left fist round the stamp (the desk's red stamp: wood knob, black neck, red mount, the rubber face)"""
    palm, fing, th = hand_r(FIST, (1.0, 0.9))
    hx, hy, _ = FIST_HOLE
    st = [ball(cm(0.042), (hx, hy, -0.064), None, seg=14, rings=10, name='knob'),
          cyl(0.0125, 0.105, (hx, hy, 0.0), None, axis='z', seg=10, name='neck'),
          box((0.088, 0.072, 0.034), (hx, hy, 0.066), None, bev=0.006, name='mount'),
          box((0.08, 0.064, 0.008), (hx, hy, 0.086), None, name='rubber')]
    allp = palm + [o for f in fing for o in f] + th + st
    mirror(allp); move(allp, (-sh, 0.925, 0))
    for o in palm + [o for f in fing for o in f] + th: C.add(o, 'handL', 'gloss', DEB['skin'], 'skin')
    C.add(st[0], 'handL', 'gloss', 0x9a6a3a, 'vinyl'); C.add(st[1], 'handL', 'gloss', 0x17121c, 'plastic')
    C.add(st[2], 'handL', 'gloss', 0xc0202a, 'plastic'); C.add(st[3], 'handL', 'gloss', 0x2a1a1e, 'vinyl')
    # (the stamp face, hand space: where the game / the IK aim it)
    return (-(hx), hy, 0.09)


def deb_chair(C):
    """a five-star office chair, purple vinyl, one caster gone (it leans that way), the seat taped up"""
    P = []
    blk, chrome, vin = 0x1a1820, 0xd8dde4, DEB['chair']
    for i in range(5):
        a = math.radians(i * 72 + 18); ca, sa = math.cos(a), math.sin(a)
        P.append((rod((ca * 0.03, 0.07, sa * 0.03), (ca * 0.25, 0.045, sa * 0.25), 0.016, None, seg=8, name='spoke'), 'gloss', blk, 'plastic'))
        P.append((ball(0.02, (ca * 0.25, 0.045, sa * 0.25), None, seg=10, rings=6, name='tip'), 'gloss', blk, 'plastic'))
        if i != 1:  # (the missing caster)
            P.append((cyl(0.022, 0.018, (ca * 0.255, 0.023, sa * 0.255), None, axis='x', seg=12, name='caster', rot=(0, math.atan2(-ca, -sa), 0)), 'gloss', 0x2a2830, 'plastic'))
            P.append((box((0.02, 0.03, 0.03), (ca * 0.25, 0.04, sa * 0.25), None, name='fork'), 'metal', chrome, 'chrome'))
    P.append((cyl(0.04, 0.05, (0, 0.075, 0), None, axis='y', seg=14, name='hub'), 'gloss', blk, 'plastic'))
    P.append((cyl(0.036, 0.15, (0, 0.17, 0), None, axis='y', seg=14, r2=0.03, name='shroud'), 'gloss', blk, 'plastic'))
    P.append((cyl(0.018, 0.14, (0, 0.3, 0), None, axis='y', seg=12, name='gaslift'), 'metal', chrome, 'chrome'))
    P.append((box((0.27, 0.03, 0.25), (0, 0.375, 0.03), None, bev=0.006, name='pan'), 'gloss', blk, 'plastic'))
    P.append((box((0.36, 0.075, 0.34), (0, 0.42, 0.035), None, bev=0.03, seg=3, name='seat'), 'gloss', vin, 'vinyl'))
    for k, r in enumerate((0.6, -0.6)):  # duct tape X on the front corner
        P.append((box((0.11, 0.004, 0.035), (0.11, 0.4605 + k * 0.0025, -0.075), None, rot=(0, r, 0), name='tape'), 'cloth', 0xb8b8b0, 'canvas'))
    P.append((tube([(0, 0.39, 0.17), (0, 0.42, 0.25), (0, 0.55, 0.27), (0, 0.66, 0.27)], 0.016, None, seg=8, name='spine'), 'metal', chrome, 'chrome'))
    P.append((box((0.34, 0.3, 0.07), (0, 0.8, 0.27), None, bev=0.03, seg=3, rot=(0.12, 0, 0), name='back'), 'gloss', vin, 'vinyl'))
    P.append((box((0.15, 0.004, 0.03), (-0.05, 0.86, 0.231), None, rot=(0.12, 0, 0.5), name='tape2'), 'cloth', 0xb8b8b0, 'canvas'))
    objs = [p[0] for p in P]
    move(objs, (0, 0.0105, 0), R=(0.035, 0, -0.03), pivot=(0, 0, 0))  # (leans onto the missing caster's corner)
    for o, kind, col, pat in P: C.add(o, 'root', kind, col, pat)


def deb_slipper(C, s, backwards=False):
    """fluffy pink bunny slippers, ears and a face at the toe. one is on backwards"""
    sx = -1 if s == 'L' else 1; x = sx * 0.1; fy = 0.085
    P = []
    P.append((blob('slip', (0, 0.04, -0.045), (0.055, 0.042, 0.125), None, seg=16, rings=10, fn=lambda p, n: -0.012 * max(0.0, n.y) * max(0.0, p.z + 0.05) / 0.17), 'cloth', DEB['slipper'], 'fuzz'))
    P.append((box((0.1, 0.014, 0.24), (0, 0.006, -0.045), None, bev=0.006, name='sole'), 'gloss', 0xe8d8e0, 'vinyl'))
    for ex in (-0.022, 0.022):
        P.append((blob('ear', (ex, 0.105, -0.12), (0.014, 0.05, 0.008), None, seg=10, rings=8), 'cloth', DEB['slipper'], 'fuzz'))
        P.append((blob('earin', (ex, 0.105, -0.128), (0.007, 0.035, 0.004), None, seg=8, rings=6), 'gloss', 0xff6aa8, 'plastic'))
        P.append((ball(0.008, (ex * 0.9, 0.058, -0.138), None, seg=8, rings=6, name='eye'), 'gloss', 0x120818, 'plastic'))
    P.append((ball(0.009, (0, 0.05, -0.16), None, seg=8, rings=6, name='nose'), 'gloss', 0xff4fa0, 'plastic'))
    objs = [p[0] for p in P]
    if backwards: move(objs, R=(0, math.pi, 0), pivot=(0, 0, -0.03))
    move(objs, (x, 0, 0.0))
    for o, kind, col, pat in P: C.add(o, 'foot' + s, kind, col, pat)


def make_deb():
    sh = 0.235
    J = skeleton(sh=sh, extra={
        'glasses': ('head', (0, 1.756, ez(0, 1.756) - 0.03)),
        'fingR': ('handR', (sh - 0.004, 0.925 - 0.078, 0)), 'thumbR': ('handR', (sh - 0.012, 0.925 - 0.03, -0.034))})
    C = Char('deb', J); C.order = order(J)
    sk, cd, ck = DEB['skin'], DEB['cardi'], DEB['cardi_dk']
    # ---- head
    face(C, sk, 0x9fc8e8, 0x6a5a6a, lips=DEB['lips'], cheek=0xf08a9a, nose=(0.016, 0.025, 0.019), brow=dict(w=0.04, arch=0.009, tilt=0.004, r=0.0042))
    for s, sx in (('L', -1), ('R', 1)):  # eye bags (it has been a long shift)
        C.add(blob('bag' + s, (sx * EYE_X, 1.768, ez(sx * EYE_X, 1.768) + 0.004), (0.022, 0.009, 0.009), None, seg=12, rings=8), 'head', 'gloss', 0xc48c64, 'skin')
        C.add(ball(0.012, (sx * 0.121, 1.733, -0.004), None, seg=12, rings=8, name='pearl'), 'head', 'gloss', 0xfff6ea, 'plastic')
    # hair: a set grey-lilac helmet (pulled in where the face is), a fringe roll, curls over the ears, the bun + its pencil
    def cap(p, n):
        front = min(1.0, max(0.0, (-n.z - 0.15) / 0.25)) * min(1.0, max(0.0, (0.052 - p.y) / 0.02))
        low = min(1.0, max(0.0, (-0.075 - p.y) / 0.02))
        side = min(1.0, max(0.0, (abs(n.x) - 0.55) / 0.2)) * min(1.0, max(0.0, (-0.035 - p.y) / 0.02))
        return -0.055 * max(front, low, side) + 0.006 * math.sin(p.x * 90) * math.sin(p.z * 80)
    C.add(blob('hair', (0, 1.8, 0.012), (0.132, 0.152, 0.146), None, fn=cap, seg=32, rings=22), 'head', 'gloss', DEB['hair'], 'hair', span=0.35)
    fr = [(x, 1.858 + 0.012 * (1 - (x / 0.115) ** 2), ez(x, 1.858) - 0.006 + 0.03 * (x / 0.115) ** 2) for x in [i * 0.023 - 0.115 for i in range(11)]]
    C.add(limb('fringe', fr, [0.012, 0.022, 0.028, 0.03, 0.031, 0.031, 0.031, 0.03, 0.028, 0.022, 0.012], None, seg=12), 'head', 'gloss', DEB['hair'], 'hair')
    for sx in (-1, 1):
        for i, (y, z) in enumerate(((1.8, 0.03), (1.765, 0.06), (1.74, 0.035))):
            C.add(blob('curl', (sx * 0.118, y, z), (0.02, 0.022, 0.024), None, seg=12, rings=8), 'head', 'gloss', DEB['hair'] if i != 1 else DEB['hair_dk'], 'hair')
    C.add(blob('bun', (0, 1.965, 0.045), (0.072, 0.058, 0.07), None, seg=20, rings=14, fn=lambda p, n: 0.005 * math.sin(math.atan2(p.z, p.x) * 5 + p.y * 40)), 'head', 'gloss', DEB['hair'], 'hair')
    pa, pb = Vector((-0.1, 2.0, 0.015)), Vector((0.11, 1.955, 0.085)); d = (pb - pa).normalized()
    C.add(rod(tuple(pa), tuple(pb), 0.008, None, seg=6, name='pencil'), 'head', 'gloss', 0xffd21a, 'plastic')
    C.add(rod(tuple(pb), tuple(pb + d * 0.026), 0.008, None, seg=6, r1=0.0015, name='tip'), 'head', 'gloss', 0xe8c890, 'plastic')
    C.add(rod(tuple(pa - d * 0.012), tuple(pa), 0.0085, None, seg=8, name='ferrule'), 'head', 'metal', 0xd8b048, 'brushed')
    C.add(rod(tuple(pa - d * 0.03), tuple(pa - d * 0.012), 0.0082, None, seg=8, name='eraser'), 'head', 'gloss', 0xff7a9a, 'plastic')
    # cat-eye readers, low on the nose (glasses bone), and the bead chain round the back of the neck
    gz = ez(0, 1.75) - 0.026; GY = 1.748
    def rim(sx):
        pts = []
        for i in range(17):
            a = 2 * math.pi * i / 16
            px, py = math.cos(a) * 0.027, math.sin(a) * 0.018
            if py > 0 and px * sx > 0: py += 0.012 * (px * sx / 0.027) ** 3  # (the cat-eye flick, up at the outer corner)
            xx = sx * 0.036 + px; pts.append((xx, GY + py, gz + 0.014 * (xx / 0.07) ** 2))
        return pts
    for s, sx in (('L', -1), ('R', 1)):
        C.add(tube(rim(sx), 0.0042, None, seg=6, name='rim' + s, closed=True), 'glasses', 'gloss', DEB['frames'], 'plastic')
        C.add(rod((sx * 0.066, GY + 0.018, gz + 0.008), (sx * 0.114, 1.79, 0.02), 0.0035, None, seg=6, name='temple' + s), 'glasses', 'gloss', DEB['frames'], 'plastic')
        C.add(ball(0.0055, (sx * 0.066, GY + 0.018, gz + 0.008), None, seg=8, rings=6, name='hinge' + s), 'glasses', 'metal', 0xd8b048, 'brushed')
    C.add(tube([(-0.01, GY + 0.004, gz - 0.002), (0, GY + 0.008, gz - 0.004), (0.01, GY + 0.004, gz - 0.002)], 0.0038, None, seg=6, name='bridge'), 'glasses', 'gloss', DEB['frames'], 'plastic')
    chain = [(0.066, GY + 0.014, gz + 0.012), (0.09, 1.7, -0.07), (0.1, 1.62, -0.035), (0.085, 1.56, 0.02), (0.045, 1.53, 0.07), (0, 1.522, 0.085)]
    chain = chain + [(-x, y, z) for x, y, z in reversed(chain[:-1])]
    def chain_w(p):
        if p[1] > 1.72: return {'glasses': 1.0}
        if p[1] > 1.63: t = (p[1] - 1.63) / 0.09; return {'glasses': t, 'head': 1 - t}
        if p[1] > 1.56: t = (p[1] - 1.56) / 0.07; return {'head': t, 'chest': 1 - t}
        return {'chest': 1.0}
    C.add(tube(chain, 0.0028, None, seg=5, name='chain'), chain_w, 'metal', 0xe0b84a, 'chain')
    for i in range(1, len(chain) - 1, 1):
        C.add(ball(0.0055, chain[i], None, seg=8, rings=6, name='bead'), chain_w, 'metal', 0xe0b84a, 'brushed')
    # ---- neck, blouse collar, the cardigan, the sticker
    C.add(limb('neck', [(0, 1.5, 0.004), (0, 1.58, 0.002), (0, 1.67, 0.012)], [0.05, 0.046, 0.05], None, seg=14), 'neck', 'gloss', sk, 'skin')
    ruff = [(math.sin(a) * 0.066, 1.535 + 0.008 * math.cos(a * 7), -math.cos(a) * 0.06 + 0.006) for a in [i * 2 * math.pi / 24 for i in range(25)]]
    C.add(tube(ruff, 0.016, None, seg=8, name='ruffle', closed=True), 'chest', 'cloth', DEB['blouse'], 'weave')
    def cardi(p, n):  # bust + a soft slump at the belly
        return 0.022 * math.exp(-((abs(p.x) - 0.09) ** 2 + (p.y - 0.02) ** 2) / 0.004) * max(0.0, -n.z) + 0.004 * math.sin(p.y * 160)
    C.add(blob('cardi', (0, 1.33, 0.006), (0.232, 0.205, 0.152), None, fn=cardi, seg=28, rings=20), 'chest', 'cloth', cd, 'knit')
    C.add(blob('cardi_lo', (0, 1.105, 0.0), (0.205, 0.13, 0.15), None, seg=24, rings=14,
               fn=lambda p, n: 0.012 * max(0.0, -n.z) * max(0.0, -p.y) / 0.13 + 0.004 * math.sin(p.y * 160)), blend('spine', 'chest', 1.12, 1.22), 'cloth', cd, 'knit')
    C.add(lathe([(0.192, 0.0), (0.212, 0.004), (0.214, 0.03), (0.2, 0.036)], (0, 0.985, 0.002), None, seg=28, axis='y', name='hem'), 'spine', 'cloth', ck, 'knit')
    # the open front: blouse in a V, the cardigan's button bands down each edge, five pearl buttons
    vz = lambda x, y: -0.152 * math.sqrt(max(0.0, 1 - (x / 0.232) ** 2 - ((y - 1.33) / 0.205) ** 2)) + 0.006
    def vpanel():
        bm = bmesh.new(); rows = []
        for j in range(9):
            y = 1.515 - j * 0.0385; half = 0.07 * (y - 1.2) / 0.33 + 0.004
            row = [bm.verts.new(gv(x, y, vz(x, y) - 0.01)) for x in [half * (2 * i / 6 - 1) for i in range(7)]]
            rows.append(row)
        for a, b in zip(rows, rows[1:]):
            for i in range(6): bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = lib._obj('blouse', bm, None)
        so = o.modifiers.new('t', 'SOLIDIFY'); so.thickness = 0.006; so.offset = 1
        for pp in o.data.polygons: pp.use_smooth = True
        return o
    C.add(vpanel(), 'chest', 'cloth', DEB['blouse'], 'weave')
    for sx in (-1, 1):
        band = [(sx * (0.074 * (y - 1.2) / 0.33 + 0.012), y, vz(sx * (0.074 * (y - 1.2) / 0.33 + 0.012), y) - 0.016) for y in [1.545 - i * 0.04 for i in range(9)]]
        band += [(sx * 0.02, 1.16, vz(0.02, 1.16) - 0.012), (sx * 0.03, 1.06, -0.158), (sx * 0.036, 0.99, -0.152)]
        C.add(limb('band', band, 0.012, None, seg=8, squash=(0.6, 1.0)), lambda p: blend('spine', 'chest', 1.12, 1.22)(p), 'cloth', ck, 'knit')
    for i, y in enumerate((1.4, 1.32, 1.24, 1.16, 1.08)):
        x = -(0.074 * (y - 1.2) / 0.33 + 0.012) if y > 1.2 else -0.02 - (1.2 - y) * 0.12
        z = (vz(x, y) - 0.026) if y > 1.15 else -0.15 * math.sqrt(max(0.0, 1 - (x / 0.205) ** 2 - ((y - 1.105) / 0.13) ** 2)) - 0.012 * max(0.0, 1.105 - y) / 0.13 - 0.004
        C.add(ball(0.012, (x, y, z), None, seg=10, rings=6, scale=(1, 1, 0.55), name='button'), 'chest' if y > 1.15 else 'spine', 'gloss', 0xfff4f0, 'plastic')
    for sx, sp in ((-1, 0), (1, 1)):  # patch pockets; a tissue out of the right one, a pen in the left
        C.add(box((0.1, 0.085, 0.012), (sx * 0.12, 1.085, -0.153), None, bev=0.004, rot=(0, sx * 0.45, 0), name='pocket'), 'spine', 'cloth', ck, 'knit')
    C.add(blob('tissue', (0.115, 1.14, -0.158), (0.03, 0.028, 0.018), None, seg=12, rings=8, fn=lambda p, n: 0.006 * math.sin(p.x * 260) * math.sin(p.y * 200)), 'spine', 'cloth', 0xffffff, 'weave')
    C.add(rod((-0.13, 1.08, -0.16), (-0.125, 1.165, -0.168), 0.007, None, seg=8, name='pen'), 'spine', 'gloss', 0x2a4aff, 'plastic')
    C.add(box((0.004, 0.04, 0.008), (-0.128, 1.15, -0.176), None, name='clip'), 'spine', 'metal', 0xd8dde4, 'chrome')
    decal(C, 'cloth', 'hello', 48, 36, sticker_hello)
    sx0, sy0 = -0.115, 1.395
    C.add(box((0.078, 0.058, 0.004), (sx0, sy0, vz(sx0, sy0) - 0.01), None, rot=(0.12, 0.42, 0.0), name='hello'), 'chest', 'cloth', 0xffffff, decal=('hello', '-z'))
    # ---- arms: knit sleeves, a left fist round the stamp, a free right hand (its fingers ride fingR / thumbR)
    for s in ('L', 'R'): arm_sleeve(C, s, sh, 0.06, cd)
    C.stamp_face = deb_hand_stamp(C, sh)
    hand(C, 'R', sh, sk, [(-0.15, -0.25), (-0.12, -0.22), (-0.18, -0.28), (-0.25, -0.3)], (0.35, 0.25), fing_bone='fingR', thumb_bone='thumbR')
    # ---- hips: pencil skirt, tights, knee balls, bunny slippers
    C.add(blob('skirt', (0, 0.94, 0.008), (0.2, 0.12, 0.152), None, seg=24, rings=14), 'hips', 'cloth', DEB['skirt'], 'weave')
    for s, sx in (('L', -1), ('R', 1)):
        kk = 1.0 if s == 'L' else 0.975
        C.add(limb('skirtleg' + s, [(sx * 0.103, 0.96, 0.006), (sx * 0.101, 0.72, 0.004), (sx * 0.097, 0.5, 0.0)], [0.105 * kk, 0.09 * kk, 0.08 * kk], None, seg=16 if s == 'L' else 15), 'thigh' + s, 'cloth', DEB['skirt'], 'weave')
        C.add(ball(0.056, (sx * 0.1, 0.49, 0), None, seg=14, rings=10, name='knee'), 'shin' + s, 'gloss', DEB['tights'], 'skin')
        C.add(limb('shin' + s, [(sx * 0.1, 0.48, 0.0), (sx * 0.1, 0.32, 0.008), (sx * 0.1, 0.12, 0.0)], [0.05, 0.052, 0.038], None, seg=14), 'shin' + s, 'gloss', DEB['tights'], 'skin')
        C.add(ball(0.036, (sx * 0.1, 0.095, 0), None, seg=12, rings=8, name='ankle'), 'foot' + s, 'gloss', DEB['tights'], 'skin')
        deb_slipper(C, s, backwards=(s == 'R'))
    deb_chair(C)
    return C


def sticker_hello(px):
    """HELLO / MY NAME IS / DEB in marker"""
    h, w = px.shape[:2]; px[:] = 1.0
    px[:13] = hexrgb(0xe0203a); px[h - 3:] = hexrgb(0xe0203a)
    text_px(px, 'HELLO', 10, 3, 1, 0xffffff)
    text_px(px, 'DEB', 6, 16, 2, 0x120818)
    px[30, 6:40] = hexrgb(0x3050ff)  # (she underlined it)


# ---------------------------------------------------------------- Deb's clips
def deb_pose(C):
    """sitting at the desk, slumped, head tipped (the house jank)"""
    P = {'hips.py': -0.468, 'hips.x': 0.12, 'spine.x': -0.05, 'chest.x': -0.15, 'neck.x': 0.04, 'head.x': 0.04, 'head.z': 0.085, 'head.y': -0.04,
         'thighL.x': 1.45, 'thighR.x': 1.45, 'thighL.z': -0.05, 'thighR.z': 0.03, 'thighL.y': 0.12, 'thighR.y': -0.05,
         'shinL.x': -1.42, 'shinR.x': -1.62, 'footL.x': -0.03, 'footR.x': 0.1, 'footR.y': 0.25,
         'shoulderL.z': 0.02, 'shoulderR.z': -0.03, 'lidL.x': 0.12, 'lidR.x': 0.06, 'browL.py': 0.0, 'browR.py': 0.002,
         'glasses.z': -0.04, 'fingR.z': 0.05}
    return P


def desk_pt(X, Y, Z):
    """a point in the desk's frame -> Deb's frame (she sits at DEB_AT facing the desk's +z)"""
    return (-(X - DEB_AT[0]), Y, -(Z - DEB_AT[1]))


def deb_reach(C, P, side, target, face_down=True, extra=(), w_dir=0.25, chans=None):
    """IK one hand: the stamp face (left) or the fingertips (right) onto a point in her own space"""
    if side == 'L':
        lp = (C.stamp_face[0] * S, C.stamp_face[1] * S, C.stamp_face[2] * S)
        terms = [('pos', 'handL', lp, target, 1.0)]
        if face_down: terms.append(('dir', 'handL', (0, 0, 1), (0, -1, 0), w_dir))
    else:
        lp = (-0.012 * S, -0.115 * S, -0.01 * S)
        terms = [('pos', 'handR', lp, target, 1.0)]
        if face_down: terms.append(('dir', 'handR', (1, 0, 0), (0, 1, 0), w_dir)); terms.append(('dir', 'handR', (0, -1, 0), (0.15, -0.1, -1), w_dir * 0.6))
    W = fk(C, P); sxs = -1 if side == 'L' else 1
    sp = W['arm' + side][:3, 3]; terms.append(('pos', 'fore' + side, (0, 0, 0), tuple(sp + np.array([sxs * 0.035, -0.25, -0.1])), 0.12))  # (elbows in, not chicken wings)
    terms += list(extra)
    ch = chans or [f'arm{side}.x', f'arm{side}.y', f'arm{side}.z', f'fore{side}.x', f'fore{side}.y', f'hand{side}.x', f'hand{side}.y', f'hand{side}.z']
    return ik(C, P, terms, ch)


def deb_clips(C):
    B = deb_pose(C)
    ink = desk_pt(0.5, DESK_TOP + 0.022, 0.0)          # the ink pad
    form = desk_pt(-0.1, DESK_TOP + 0.075, -0.29)      # top of the forms stack
    restL = desk_pt(0.32, DESK_TOP + 0.002, -0.38)     # the stamp stood on the desk by her
    restR = desk_pt(-0.08, DESK_TOP + 0.075, -0.4)     # her right hand flat on the forms
    B = deb_reach(C, B, 'L', restL); B = deb_reach(C, B, 'R', restR)
    C.base = B
    # ---- idle (8 s): drums her fingers, a big sigh, pushes her glasses up (they slide straight back down)
    I = Clip('idle', 8.0, True, B)
    I.osc += [('chest.x', 0.012, 4.0, 0.0), ('shoulderL.z', -0.008, 4.0, 0.3), ('shoulderR.z', 0.008, 4.0, 0.3), ('head.x', -0.006, 4.0, 0.6)]
    for t in (0.35, 0.5, 0.65, 0.8, 1.55, 1.7, 1.85, 2.0): I.pulses.append(('fingR.z', t, 0.32, 0.05, 0.0, 0.08))
    I.blink(1.25, d=0.32); I.blink(4.7, d=0.4); I.blink(7.3, d=0.3)
    I.key(2.4, B)
    I.key(3.1, {'chest.x': B['chest.x'] + 0.1, 'shoulderL.z': -0.07, 'shoulderR.z': 0.07, 'head.x': 0.16, 'lidL.x': -0.5, 'lidR.x': -0.55, 'jaw.x': -0.02, 'hips.x': 0.14})
    I.key(3.5, {'chest.x': B['chest.x'] + 0.11, 'head.x': 0.18, 'lidL.x': -0.9, 'lidR.x': -0.95})
    I.key(4.25, {'chest.x': B['chest.x'] - 0.06, 'shoulderL.z': 0.03, 'shoulderR.z': -0.04, 'head.x': -0.06, 'lidL.x': 0.05, 'lidR.x': 0.0, 'jaw.x': -0.09, 'hips.x': 0.11})
    I.key(4.9, {**{k: B[k] for k in ('chest.x', 'shoulderL.z', 'shoulderR.z', 'head.x', 'lidL.x', 'lidR.x', 'hips.x')}, 'jaw.x': 0.0})
    I.key(5.3, B)
    P = I.last(); W = fk(C, P); g = W['glasses'][:3, 3]
    up = deb_reach(C, P, 'R', tuple(g + np.array([0.0, -0.005, -0.03])), face_down=False,
                   extra=[('dir', 'handR', (0, -1, 0), (0, 0.6, -0.4), 0.15)], chans=['armR.x', 'armR.y', 'armR.z', 'foreR.x', 'foreR.y', 'handR.x', 'handR.z'])
    up['fingR.z'] = 0.25; up['head.x'] = B['head.x'] - 0.04
    I.key(5.85, up)
    up2 = dict(up); up2['glasses.py'] = 0.012; up2['glasses.z'] = 0.0
    I.key(6.15, up2)
    I.key(6.6, B, **{'glasses.py': 0.011, 'glasses.z': -0.01})
    I.key(7.4, {'glasses.py': 0.002, 'glasses.z': -0.035})
    I.key(8.0, B)
    # ---- talk (2.4 s loop): leans in, looks over her readers (they slide down her nose), a palm-up "well?"
    T0 = dict(B, **{'chest.x': B['chest.x'] - 0.1, 'head.x': B['head.x'] - 0.12, 'neck.x': 0.0, 'lidL.x': 0.32, 'lidR.x': 0.3,
                    'browL.py': 0.004, 'browR.py': 0.011, 'glasses.py': -0.012, 'glasses.pz': -0.004})
    T = Clip('talk', 2.4, True, T0)
    palm = deb_reach(C, T0, 'R', desk_pt(-0.02, DESK_TOP + 0.2, -0.32), face_down=False,
                     extra=[('dir', 'handR', (1, 0, 0), (0.1, -1, 0.0), 0.3), ('dir', 'handR', (0, -1, 0), (-0.2, 0.15, -1), 0.2)])
    palm['fingR.z'] = 0.4; palm['thumbR.z'] = 0.2
    T.key(0.5, T0); T.key(0.85, palm); T.key(1.45, dict(palm, **{'armR.x': palm['armR.x'] + 0.06, 'head.y': -0.1})); T.key(1.9, T0); T.key(2.4, T0)
    for t, a in ((0.12, 0.16), (0.36, 0.1), (0.58, 0.2), (0.86, 0.09), (1.08, 0.18), (1.34, 0.12), (1.62, 0.2), (1.9, 0.08)):
        T.pulses.append(('jaw.x', t, -a, 0.06, 0.02, 0.08)); T.pulses.append(('head.x', t, -a * 0.12, 0.06, 0.0, 0.12))
    T.blink(1.15, d=0.22)
    # ---- gesture: STAMP. lifts it, inks it, KA-CHUNK on the forms, twice, then the dead stare
    G = Clip('gesture', 2.7, False, B)
    hi = deb_reach(C, dict(B, **{'head.y': 0.14, 'head.x': -0.12, 'chest.y': 0.08}), 'L', desk_pt(0.36, DESK_TOP + 0.36, -0.2))
    G.key(0.28, hi)
    dn = deb_reach(C, dict(hi, **{'chest.x': B['chest.x'] - 0.12, 'head.x': -0.2}), 'L', ink, chans=['armL.x', 'armL.y', 'armL.z', 'foreL.x', 'foreL.y', 'handL.x', 'handL.y', 'handL.z', 'chest.x', 'chest.y'])
    G.key(0.46, dn); G.key(0.58, dict(dn, **{'handL.x': dn['handL.x'] + 0.04}))
    up = deb_reach(C, dict(dn, **{'head.y': -0.06, 'chest.y': -0.04}), 'L', desk_pt(0.0, DESK_TOP + 0.38, -0.38))
    G.key(0.8, up)
    s1 = deb_reach(C, dict(up, **{'chest.x': B['chest.x'] - 0.1, 'head.x': -0.18, 'head.y': -0.12}), 'L', form, chans=['armL.x', 'armL.y', 'armL.z', 'foreL.x', 'foreL.y', 'handL.x', 'handL.y', 'handL.z', 'chest.x', 'chest.y'])
    G.key(0.93, s1); G.key(1.02, dict(s1, **{'chest.x': s1['chest.x'] - 0.02, 'head.x': -0.22}))
    u2 = deb_reach(C, dict(s1, **{'head.x': -0.12}), 'L', desk_pt(-0.05, DESK_TOP + 0.32, -0.33))
    G.key(1.22, u2); G.key(1.36, s1); G.key(1.46, dict(s1, **{'chest.x': s1['chest.x'] - 0.02, 'head.x': -0.24, 'jaw.x': 0.0}))
    look = dict(B, **{'head.x': 0.06, 'head.y': -0.02, 'lidL.x': 0.3, 'lidR.x': 0.28, 'browR.py': 0.01})
    lk = deb_reach(C, look, 'L', desk_pt(0.2, DESK_TOP + 0.12, -0.36))
    G.key(1.85, lk); G.key(2.25, lk); G.key(2.7, B)
    G.blink(2.1, d=0.42)
    G.marks = [(0.5, 'ink'), (0.95, 'stamp'), (1.38, 'stamp')]
    return [I, T, G]


# ================================================================== GUS
GUS = dict(skin=0xc68642, shirt=0x2f7a3a, apron=0xc8a060, apron_dk=0x8a6a38, pants=0x5a4a36, boots=0x6a3a1a, cap=0xd0202a, mesh=0xf2ece0,
           tache=0x4a2a14, brow=0x5a3a24, rag=0xd8262a, chrome=0xdfe4ea, pearl=0xf4ecdc)
GUS_AT = (0.0, -1.0)  # in the counter's frame (x_lobby_whprops 'counter'), facing its +z: behind it, toward the room


def revolver_parts():
    """a chrome .357 with a long barrel and pearl grips, in a gun frame (x side, y up, -z forward, origin at the web of
    the hand); returns [(obj, kind, colour, pat)] and the trigger guard's middle (the spin pivot)"""
    P = []
    ch, bl, pe = GUS['chrome'], 0x2a2a30, GUS['pearl']
    P.append((box((0.017, 0.04, 0.058), (0, 0.022, -0.004), None, bev=0.004, name='frame'), 'metal', ch, 'chrome'))
    P.append((cyl(0.022, 0.044, (0, 0.034, -0.022), None, axis='z', seg=12, bev=0.002, name='cylinder'), 'metal', ch, 'brushed'))
    for i in range(6):
        a = i * math.pi / 3 + math.pi / 6
        P.append((box((0.006, 0.006, 0.036), (math.cos(a) * 0.021, 0.034 + math.sin(a) * 0.021, -0.022), None, rot=(0, 0, a), name='flute'), 'metal', 0x9aa0a8, 'cast'))
    P.append((cyl(0.0095, 0.15, (0, 0.038, -0.12), None, axis='z', seg=12, name='barrel'), 'metal', ch, 'chrome'))
    P.append((box((0.008, 0.007, 0.15), (0, 0.0525, -0.12), None, name='rib'), 'metal', ch, 'brushed'))
    P.append((cyl(0.0065, 0.1, (0, 0.022, -0.1), None, axis='z', seg=10, name='ejector'), 'metal', ch, 'chrome'))
    P.append((box((0.004, 0.012, 0.01), (0, 0.06, -0.188), None, name='sight'), 'metal', ch, 'chrome'))
    P.append((box((0.016, 0.009, 0.062), (0, 0.059, -0.012), None, bev=0.002, name='strap'), 'metal', ch, 'chrome'))
    P.append((box((0.007, 0.024, 0.012), (0, 0.054, 0.03), None, rot=(-0.5, 0, 0), name='hammer'), 'metal', bl, 'cast'))
    P.append((tube([(0, -0.012 + 0.016 * math.sin(a), -0.012 + 0.016 * math.cos(a)) for a in [i * 2 * math.pi / 14 for i in range(14)]], 0.0035, None, seg=6, name='guard', closed=True), 'metal', ch, 'chrome'))
    P.append((box((0.005, 0.02, 0.006), (0, -0.006, -0.01), None, rot=(0.3, 0, 0), name='trigger'), 'metal', bl, 'cast'))
    g = box((0.026, 0.095, 0.034), (0, -0.04, 0.036), None, bev=0.009, seg=3, rot=(-0.32, 0, 0), name='grip')
    P.append((g, 'gloss', pe, 'plastic'))
    for sx in (-1, 1): P.append((ball(0.006, (sx * 0.013, -0.03, 0.033), None, seg=8, rings=6, scale=(0.4, 1, 1), name='medal'), 'metal', 0xe8c050, 'brushed'))
    return P, (0, -0.012, -0.012)


def gus_hands(C, sh):
    """right hand round the revolver (index through the guard, the other three + the thumb ride fingR / thumbR so they
    can let go for the spin), the left fist bunching the shop rag"""
    # the gun frame -> right-hand space: x -> x - 0.031, z(back) -> y + oy, y(up) -> -z + oz (the grip in the fist)
    ox, oy, oz = -0.031, -0.104, -0.044
    to_hand = lambda o: move([o], R=((1, 0, 0), (0, 0, 1), (0, -1, 0)))[0]
    GP, piv = revolver_parts()
    for o, *_ in GP: to_hand(o); move([o], (ox, oy, oz))
    pivot = (ox + piv[0], oy + piv[2], oz - piv[1])
    palm, fing, th = hand_r([(-0.4, -1.5), (-1.45, -1.55), (-1.5, -1.55), (-1.55, -1.5)], (1.0, 0.9), k=1.12)
    allp = palm + [o for f in fing for o in f] + th + [o for o, *_ in GP]
    move(allp, (sh, 0.925, 0))
    C.many(palm + fing[0], 'handR', 'gloss', GUS['skin'], 'skin')
    for f in fing[1:]: C.many(f, 'fingR', 'gloss', GUS['skin'], 'skin')
    C.many(th, 'thumbR', 'gloss', GUS['skin'], 'skin')
    for o, kind, col, pat in GP: C.add(o, 'gun', kind, col, pat)
    # the left: a fist round a red shop rag, a tail of it hanging out
    palm, fing, th = hand_r(FIST, (1.0, 0.9), k=1.12)
    hx, hy, _ = FIST_HOLE
    rag = [blob('rag', (hx * 1.1, hy * 1.12, 0.0), (0.03, 0.03, 0.06), None, seg=14, rings=10, fn=lambda p, n: 0.008 * math.sin(p.x * 220 + p.z * 130) * math.sin(p.y * 180)),
           blob('ragtail', (hx * 1.2, hy * 1.12 - 0.05, 0.05), (0.012, 0.06, 0.035), None, seg=12, rings=10, fn=lambda p, n: 0.005 * math.sin(p.y * 160 + p.z * 90))]
    allp = palm + [o for f in fing for o in f] + th + rag
    mirror(allp); move(allp, (-sh, 0.925, 0))
    C.many(palm + [o for f in fing for o in f] + th, 'handL', 'gloss', GUS['skin'], 'skin')
    C.many(rag, 'handL', 'cloth', GUS['rag'], 'weave')
    return pivot


def make_gus():
    sh = 0.285
    pick0 = (0.034, 1.692, ez(0.034, 1.692) - 0.008)
    J = skeleton(sh=sh, hip=0.11, extra={
        'fingR': ('handR', (sh - 0.004, 0.925 - 0.078 * 1.12, 0)), 'thumbR': ('handR', (sh - 0.012, 0.925 - 0.034, -0.038)),
        'gun': ('handR', (sh - 0.031, 0.925 - 0.116, -0.032)), 'pick': ('jaw', pick0)})  # (the gun turns on the trigger finger: the guard's middle)
    C = Char('gus', J); C.order = order(J)
    sk = GUS['skin']
    # ---- head: stubble, a walrus moustache, bushy brows, a bulb nose, big ears, a NO REFUNDS trucker cap, a toothpick
    stub = lambda p: 0x8a6a4a if (p[1] < 1.72 and p[2] < -0.04 and abs(p[0]) < 0.105) else sk
    face(C, sk, sk, GUS['brow'], lips=0xa85a40, nose=(0.025, 0.03, 0.027), brow=dict(w=0.05, arch=0.004, tilt=-0.012, r=0.0105))
    C.pieces[0]['color'] = stub  # (the egg: five o'clock shadow)
    for P in C.pieces:
        if P['o'].name.startswith('jawplate'): P['color'] = 0x8a6a4a
    C.add(blob('nosebulb', (0, 1.738, ez(0, 1.738) - 0.022), (0.018, 0.016, 0.016), None, seg=12, rings=8), 'head', 'gloss', 0xc8604a, 'skin')
    tache = [(x, 1.708 + 0.012 * (1 - (x / 0.06) ** 2) - (0.028 * ((abs(x) - 0.03) / 0.03) if abs(x) > 0.03 else 0), ez(x, 1.708) - 0.012 + 0.012 * (x / 0.06) ** 2) for x in [i * 0.012 - 0.06 for i in range(11)]]
    C.add(limb('tache', tache, [0.008, 0.013, 0.016, 0.018, 0.019, 0.019, 0.019, 0.018, 0.016, 0.013, 0.008], None, seg=10, squash=(0.8, 1.0)), 'head', 'gloss', GUS['tache'], 'hair')
    pa = Vector(pick0); pb = pa + Vector((0.07, -0.022, -0.035))
    C.add(rod(tuple(pa), tuple(pb), 0.0028, None, seg=5, r1=0.0012, name='pick'), 'pick', 'gloss', 0xe8d0a0, 'plastic')
    for sx in (-1, 1): C.add(blob('earbig', (sx * 0.124, 1.762, 0.01), (0.022, 0.036, 0.026), None, seg=12, rings=8), 'head', 'gloss', sk, 'skin')
    capc = (0, 1.83, 0.008)
    C.add(blob('cap', capc, (0.132, 0.11, 0.142), None, seg=28, rings=16, fn=lambda p, n: -0.12 * max(0.0, -0.01 - p.y) / 0.11 * 2), 'head', 'gloss', GUS['cap'], 'vinyl')
    C.add(blob('capback', (0, 1.84, 0.075), (0.122, 0.07, 0.08), None, seg=20, rings=12, fn=lambda p, n: -0.12 * max(0.0, -0.01 - p.y) / 0.07 * 2), 'head', 'cloth', GUS['mesh'], 'weave')
    C.add(ball(0.012, (0, 1.94, 0.008), None, seg=10, rings=6, name='button'), 'head', 'gloss', GUS['cap'], 'vinyl')
    # the brim: a curved slab out the front, the front panel's text
    def brim():
        bm = bmesh.new(); rows = []
        for j in range(5):
            t = j / 4; zz = -0.115 - t * 0.11; half = 0.11 * (1 - 0.35 * t * t)
            rows.append([bm.verts.new(gv(half * (2 * i / 8 - 1), 1.83 + 0.01 * t - 0.018 * (2 * i / 8 - 1) ** 2, zz + 0.03 * (2 * i / 8 - 1) ** 2)) for i in range(9)])
        for a, b in zip(rows, rows[1:]):
            for i in range(8): bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); o = lib._obj('brim', bm, None)
        so = o.modifiers.new('t', 'SOLIDIFY'); so.thickness = 0.01; so.offset = 0
        for pp in o.data.polygons: pp.use_smooth = True
        return o
    C.add(brim(), 'head', 'gloss', GUS['cap'], 'vinyl')
    decal(C, 'cloth', 'refunds', 64, 24, lambda px: (px.__setitem__(slice(None), hexrgb(0xffe14d)), text_px(px, 'NO', 26, 2, 1, 0x120818), text_px(px, 'REFUNDS', 11, 12, 1, 0xd0202a)))
    C.add(box((0.115, 0.048, 0.006), (0, 1.855, -0.132), None, rot=(-0.38, 0, 0), name='capfront'), 'head', 'cloth', 0xffffff, decal=('refunds', '-z'))
    # ---- body: green work shirt over a barrel chest and a gut, short sleeves, the canvas apron, belt, work pants, boots
    C.add(limb('neck', [(0, 1.5, 0.0), (0, 1.6, 0.0), (0, 1.67, 0.012)], [0.066, 0.06, 0.058], None, seg=14), 'neck', 'gloss', sk, 'skin')
    for sx in (-1, 1): C.add(blob('collar', (sx * 0.05, 1.54, -0.06), (0.045, 0.012, 0.035), None, seg=10, rings=6), 'chest', 'cloth', GUS['shirt'], 'weave')
    C.add(blob('chest', (0, 1.33, 0.01), (0.285, 0.215, 0.17), None, seg=28, rings=18, fn=lambda p, n: 0.012 * max(0.0, -n.z) * math.exp(-(p.x ** 2) / 0.02)), 'chest', 'cloth', GUS['shirt'], 'weave')
    C.add(blob('gut', (0, 1.1, -0.04), (0.255, 0.19, 0.215), None, seg=26, rings=16), blend('spine', 'chest', 1.1, 1.25), 'cloth', GUS['shirt'], 'weave')
    belt = lathe([(0.236, -0.026), (0.248, -0.021), (0.248, 0.021), (0.236, 0.026)], (0, 0, 0), None, seg=28, axis='y', name='belt')
    C.add(move([belt], (0, 0.955, 0.0), R=((1, 0, 0), (0, 1, 0), (0, 0, 0.76)))[0], 'hips', 'gloss', 0x3a2414, 'vinyl')  # (under the gut and the apron)
    C.add(blob('seat', (0, 0.92, 0.0), (0.235, 0.12, 0.17), None, seg=24, rings=12), 'hips', 'cloth', GUS['pants'], 'canvas')
    # apron: follows the chest + gut, bib to the knees; neck strap, ties, a chest pocket of pens, the GUS tag
    def body_z(x, y):
        z1 = 0.01 - 0.17 * math.sqrt(max(0.0, 1 - (x / 0.285) ** 2 - ((y - 1.33) / 0.215) ** 2))
        z2 = -0.04 - 0.215 * math.sqrt(max(0.0, 1 - (x / 0.255) ** 2 - ((y - 1.1) / 0.19) ** 2))
        z3 = -0.17 * math.sqrt(max(0.0, 1 - (x / 0.235) ** 2 - ((y - 0.92) / 0.12) ** 2))
        return min(z1, z2, z3, -0.13)
    def apron():
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); rows = []; NY, NX = 16, 10
        for j in range(NY + 1):
            y = 1.47 - j * (1.47 - 0.5) / NY
            half = 0.13 if y > 1.24 else (0.13 + (1.24 - y) / 0.14 * 0.12 if y > 1.1 else 0.25)
            row = []
            for i in range(NX + 1):
                u = 2 * i / NX - 1; x = u * half
                z = body_z(x, y) - 0.014 if y > 0.86 else min(body_z(x, 0.9) - 0.014, -0.2) - (0.86 - y) * 0.18
                row.append(bm.verts.new(gv(x, y, z)))
            rows.append(row)
        for a, b in zip(rows, rows[1:]):
            for i in range(NX): bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); o = lib._obj('apron', bm, None)
        so = o.modifiers.new('t', 'SOLIDIFY'); so.thickness = 0.008; so.offset = 0
        for pp in o.data.polygons: pp.use_smooth = True
        return o
    def apron_w(p):
        if p[1] > 1.24: return {'chest': 1.0}
        if p[1] > 1.02: t = (p[1] - 1.02) / 0.22; return {'chest': t, 'spine': 1 - t}
        if p[1] > 0.9: t = (p[1] - 0.9) / 0.12; return {'spine': t, 'hips': 1 - t}
        return {'hips': 1.0}
    C.add(apron(), apron_w, 'cloth', GUS['apron'], 'canvas', span=0.9)
    C.add(tube([(-0.12, 1.47, body_z(-0.12, 1.47) - 0.012), (-0.1, 1.56, -0.04), (-0.06, 1.62, 0.04), (0, 1.63, 0.07), (0.06, 1.62, 0.04), (0.1, 1.56, -0.04), (0.12, 1.47, body_z(0.12, 1.47) - 0.012)], 0.008, None, seg=6, name='strap'),
          lambda p: {'chest': 1.0} if p[1] < 1.55 else {'chest': 0.5, 'neck': 0.5}, 'cloth', GUS['apron_dk'], 'canvas')
    ties = [(0.25, 1.1, body_z(0.25, 1.1) + 0.02), (0.27, 1.1, 0.05), (0.2, 1.1, 0.19), (0.06, 1.1, 0.235), (0.0, 1.1, 0.24)]
    for sx in (-1, 1): C.add(tube([(sx * x, y, z) for x, y, z in ties], 0.008, None, seg=6, name='tie'), 'spine', 'cloth', GUS['apron_dk'], 'canvas')
    C.add(blob('bow', (0, 1.1, 0.25), (0.04, 0.02, 0.015), None, seg=10, rings=6), 'spine', 'cloth', GUS['apron_dk'], 'canvas')
    pz = lambda x, y: body_z(x, y) - 0.026
    C.add(box((0.11, 0.09, 0.012), (0.05, 1.35, pz(0.05, 1.35)), None, bev=0.004, rot=(0.22, -0.18, 0), name='pocket'), 'chest', 'cloth', GUS['apron_dk'], 'canvas')
    for i, (dx, col, ht) in enumerate(((0.02, 0x2a4aff, 0.07), (0.045, 0xd0202a, 0.06), (0.075, 0xffd21a, 0.08))):
        C.add(rod((dx, 1.37, pz(dx, 1.37) + 0.006), (dx + 0.004, 1.37 + ht, pz(dx, 1.37 + ht) + 0.01), 0.007, None, seg=6, name='pen'), 'chest', 'gloss', col, 'plastic')
    decal(C, 'cloth', 'gus', 48, 24, lambda px: (px.__setitem__(slice(None), hexrgb(0xffffff)), px.__setitem__((slice(0, 7), slice(None)), hexrgb(0x2f7a3a)), text_px(px, 'GUS', 6, 9, 2, 0x120818)))
    C.add(box((0.08, 0.042, 0.004), (-0.09, 1.36, pz(-0.09, 1.36) + 0.008), None, rot=(0.22, 0.2, -0.05), name='tag'), 'chest', 'cloth', 0xffffff, decal=('gus', '-z'))
    C.add(box((0.24, 0.13, 0.012), (0, 0.98, pz(0, 0.98) + 0.004), None, bev=0.004, rot=(0.15, 0, 0), name='pouch'), 'hips', 'cloth', GUS['apron_dk'], 'canvas')
    for s, sx in (('L', -1), ('R', 1)):
        x = sx * sh
        arm_sleeve(C, s, sh, 0.072, GUS['shirt'], pat='weave', fore=False, short=True)
        C.add(limb('bicep' + s, [(x, 1.33, 0), (x, 1.24, -0.004), (x, 1.17, 0)], [0.058, 0.06, 0.052], None, seg=14), 'arm' + s, 'gloss', sk, 'skin')
        C.add(ball(0.054, (x, 1.17, 0), None, seg=14, rings=10, name='elbow' + s), 'fore' + s, 'gloss', 0xb07838, 'skin')
        C.add(limb('forearm' + s, [(x, 1.17, 0), (x, 1.07, -0.006), (x, 0.95, 0)], [0.05, 0.056, 0.04], None, seg=14), 'fore' + s, 'gloss', sk, 'skin')
    C.add(lathe([(0.036, -0.012), (0.044, -0.012), (0.044, 0.012), (0.036, 0.012)], (-sh, 0.965, 0), None, seg=14, axis='y', name='watch'), 'foreL', 'metal', 0xe0b84a, 'brushed')
    C.add(cyl(0.02, 0.01, (-sh - 0.043, 0.965, 0), None, axis='x', seg=12, name='face'), 'foreL', 'gloss', 0xf4f2ea, 'plastic')
    C.gun_pivot = gus_hands(C, sh)
    for s, sx in (('L', -1), ('R', 1)):
        x = sx * 0.11
        kk = 1.0 if s == 'L' else 0.975; xo = sx * 0.004
        C.add(limb('thigh' + s, [(x + xo, 0.95, 0.0), (x + xo, 0.72, -0.004), (x + xo, 0.5, 0.0)], [0.115 * kk, 0.098 * kk, 0.082 * kk], None, seg=16 if s == 'L' else 15), 'thigh' + s, 'cloth', GUS['pants'], 'canvas')
        C.add(box((0.05, 0.1, 0.11), (x + sx * 0.085, 0.7, 0.0), None, bev=0.012, name='cargo'), 'thigh' + s, 'cloth', 0x4a3c2c, 'canvas')
        C.add(ball(0.072, (x, 0.49, 0), None, seg=14, rings=10, name='knee'), 'shin' + s, 'cloth', GUS['pants'], 'canvas')
        C.add(limb('shin' + s, [(x, 0.49, 0.0), (x, 0.3, 0.004), (x, 0.13, 0.0)], [0.078, 0.07, 0.068], None, seg=16), 'shin' + s, 'cloth', GUS['pants'], 'canvas')
        C.add(blob('boot' + s, (x, 0.07, -0.045), (0.068, 0.07, 0.14), None, seg=16, rings=10, fn=lambda p, n: -0.03 * max(0.0, n.y) * max(0.0, p.z + 0.02) / 0.16), 'foot' + s, 'gloss', GUS['boots'], 'vinyl')
        C.add(box((0.14, 0.03, 0.29), (x, 0.015, -0.045), None, bev=0.008, name='sole'), 'foot' + s, 'gloss', 0x1a1410, 'vinyl')
    return C


def gus_pose(C):
    """standing behind the counter, gut out, feet apart, the left knee bent the wrong way (the house jank)"""
    return {'hips.x': -0.04, 'chest.x': 0.05, 'neck.x': -0.04, 'head.x': 0.0, 'head.z': -0.07, 'thighL.z': -0.07, 'thighR.z': 0.06,
            'thighL.x': -0.24, 'shinL.x': 0.52, 'footL.x': -0.26, 'thighR.y': -0.15, 'thighL.y': 0.2, 'footR.y': 0.0,
            'lidL.x': 0.42, 'lidR.x': 0.36, 'browL.py': -0.003, 'browR.py': -0.001, 'pick.y': 0.0}


def ctr_pt(X, Y, Z):
    """the counter's frame -> Gus's (he stands at GUS_AT facing its +z)"""
    return (-(X - GUS_AT[0]), Y, -(Z - GUS_AT[1]))


def gus_clips(C):
    B = gus_pose(C)
    G0 = np.array(C.J['gun'][1]) * S  # (the gun bone: the trigger guard)
    gunf = lambda P: fk(C, P)['gun']
    def hold(P, at, barrel, up=(0, 1, 0), w=0.35, extra=(), chans=None):
        """put the revolver's guard at `at` with the barrel along `barrel` (the gun bone's -y, its top -z... in hand space)"""
        terms = [('pos', 'gun', (0, 0, 0), at, 1.0), ('dir', 'gun', (0, -1, 0), barrel, w), ('dir', 'gun', (0, 0, -1), up, w * 0.5)]
        sp = fk(C, P)['armR'][:3, 3]; terms.append(('pos', 'foreR', (0, 0, 0), tuple(sp + np.array([0.06, -0.26, -0.08])), 0.1))
        return ik(C, P, terms + list(extra), chans or ['armR.x', 'armR.y', 'armR.z', 'foreR.x', 'foreR.y', 'handR.x', 'handR.y', 'handR.z'])
    def rag(P, at, w_dir=0.2):
        sp = fk(C, P)['armL'][:3, 3]
        terms = [('pos', 'handL', (0.035 * S, -0.075 * S, 0.0), at, 1.0), ('dir', 'handL', (0, 0, 1), (0.3, -0.2, -1), w_dir),
                 ('pos', 'foreL', (0, 0, 0), tuple(sp + np.array([-0.06, -0.26, -0.06])), 0.1)]
        return ik(C, P, terms, ['armL.x', 'armL.y', 'armL.z', 'foreL.x', 'foreL.y', 'handL.x', 'handL.y', 'handL.z'])
    # polishing: the gun across his belly, barrel to his left and a bit up; the rag works the barrel
    gp = (0.05, 1.3, -0.4)
    P = hold(B, gp, (-1, 0.25, -0.35), up=(0, 0.6, -0.2))
    W = fk(C, P); bpos = lambda t: tuple((W['gun'] @ np.array([0, -t * S, -0.04 * S, 1.0]))[:3])
    P0 = rag(P, bpos(0.08)); P1 = rag(P, bpos(0.17))
    C.base = P0
    I = Clip('idle', 6.0, True, P0)
    I.osc += [('chest.x', 0.012, 3.0, 0.0), ('head.x', -0.008, 3.0, 0.5), ('hips.px', 0.006, 6.0, 0.0)]
    for i in range(6): I.key(0.4 + i * 0.4, P1 if i % 2 == 0 else P0)
    I.key(2.8, P0)
    I.key(3.0, {'pick.y': 0.0, 'jaw.x': -0.05}); I.key(3.2, {'pick.y': -0.85, 'pick.z': 0.15, 'jaw.x': 0.0}); I.key(3.4, {'jaw.x': -0.04}); I.key(3.6, {'jaw.x': 0.0})
    I.key(4.3, {'head.y': 0.38, 'head.x': 0.05, 'chest.y': 0.06}); I.key(5.0, {'head.y': 0.36}); I.key(5.4, {'head.y': 0.0, 'head.x': 0.0, 'chest.y': 0.0})
    I.key(5.75, {'pick.y': 0.0, 'pick.z': 0.0, 'jaw.x': -0.04}); I.key(5.9, {'jaw.x': 0.0})
    I.blink(1.1, d=0.2); I.blink(4.25, d=0.18); I.blink(5.6, d=0.2)
    # talk: leans on the counter (the rag hand flat on the rail), gun hand propped up, barrel at the ceiling. gruff
    lean = dict(P0, **{'chest.x': 0.0, 'spine.x': -0.08, 'head.x': -0.05, 'browL.py': -0.006, 'browR.py': -0.004, 'lidL.x': 0.3})
    sp = fk(C, lean)['armL'][:3, 3]
    T0 = ik(C, lean, [('pos', 'handL', (0.02 * S, -0.08 * S, 0.0), ctr_pt(-0.35, 1.16, -0.38), 1.0), ('dir', 'handL', (-1, 0, 0), (0, 1, 0), 0.3),
                      ('pos', 'foreL', (0, 0, 0), tuple(sp + np.array([-0.08, -0.25, -0.1])), 0.08)],
            ['armL.x', 'armL.y', 'armL.z', 'foreL.x', 'foreL.y', 'handL.x', 'handL.y', 'handL.z'])
    T0 = hold(T0, (0.24, 1.42, -0.32), (0.0, 1.0, -0.15), up=(0, 0, 1))
    T = Clip('talk', 2.4, True, T0)
    T1 = hold(dict(T0, **{'head.y': -0.08}), (0.2, 1.5, -0.38), (-0.1, 1.0, -0.3), up=(0, 0, 1))
    T.key(0.7, T1); T.key(1.3, dict(T0, **{'head.x': -0.08})); T.key(1.9, T1)
    for t, a in ((0.1, 0.12), (0.34, 0.08), (0.6, 0.14), (0.95, 0.1), (1.2, 0.13), (1.5, 0.07), (1.75, 0.15), (2.05, 0.09)):
        T.pulses.append(('jaw.x', t, -a, 0.05, 0.03, 0.08)); T.pulses.append(('pick.x', t, a * 0.9, 0.05, 0.03, 0.1))
    T.blink(1.6, d=0.18)
    # gesture: the spin. out in front, fingers off, three turns round the trigger finger, catch, blow the smoke off
    G = Clip('gesture', 2.9, False, P0)
    out = hold(dict(P0, **{'head.x': -0.06, 'head.y': -0.05}), (0.18, 1.32, -0.62), (0, 0, -1), up=(0, 1, 0))
    out = rag(out, (-0.25, 1.05, -0.22))
    G.key(0.3, out)
    G.key(0.42, dict(out, **{'fingR.z': 0.9, 'thumbR.z': 0.6, 'thumbR.y': -0.4}))
    for t, a in ((0.55, -1.2), (0.75, -4.4), (0.95, -7.6), (1.15, -10.6), (1.32, -12.57)): G.key(t, {'gun.x': a})
    G.key(1.42, {'fingR.z': 0.0, 'thumbR.z': 0.0, 'thumbR.y': 0.0, 'gun.x': -12.57})
    W = fk(C, P0); mouth = fk(C, P0)['head'] @ np.array([0, (1.69 - 1.63) * S, -0.17 * S, 1.0])
    blow = hold(dict(P0, **{'head.x': -0.05, 'gun.x': -12.57}), tuple(mouth[:3] + np.array([0.04, -0.2, -0.16])), (0, 1, 0), up=(0, 0, 1))
    blow = rag(blow, (-0.25, 1.05, -0.22))
    G.key(1.75, blow); G.key(1.9, dict(blow, **{'jaw.x': -0.09, 'head.x': -0.12})); G.key(2.2, dict(blow, **{'jaw.x': 0.0, 'head.x': -0.02, 'browL.py': 0.006}))
    G.key(2.9, dict(P0, **{'gun.x': -12.566}))
    G.blink(2.3, d=0.2)
    G.marks = [(0.5, 'spin'), (1.4, 'catch'), (1.92, 'blow')]
    return [I, T, G]


# ================================================================== MARGE
MARGE = dict(skin=0xf2c8a0, thermal=0xd8cdb8, vest=0x5a6a34, vest_dk=0x434f26, pants=0x2a3a6a, boots=0x1c1a20, beanie=0xff7a1a,
             hair=0xe8e8ee, brow=0xc8c8d0, lips=0xb85a5a, board=0x9a6a3a, gum=0xff6ab8)
MARGE_AT = (-0.4, 1.2, 0.2)   # in the crates' frame (x_lobby_whprops 'crates'): sat on the front crate, boots up on the next
MARGE_YAW = math.atan2(9.2, -9.6)  # (facing the middle of the room, like the old Marge)


def sticker_sheet(px):
    """the clipboard's top page: STOCK, lines, check boxes, some ticked, one crossed out hard"""
    h, w = px.shape[:2]; px[:] = hexrgb(0xf8f6ee)
    text_px(px, 'STOCK', 8, 3, 1, 0x120818)
    for i in range(7):
        y = 14 + i * 7
        px[y + 4, 12:w - 4] = hexrgb(0x8ab0e0)
        px[y:y + 5, 4] = px[y:y + 5, 8] = hexrgb(0x120818); px[y, 4:9] = px[y + 4, 4:9] = hexrgb(0x120818)
        if i in (0, 1, 3, 4): px[y + 2, 5] = px[y + 3, 6] = px[y + 2, 7] = px[y + 1, 8] = hexrgb(0xd0202a)
        for k in range(12, w - 8 - (i * 5) % 11): px[y + 2 + (k // 3) % 2, k] = hexrgb(0x3a3a50) if k % 4 else px[y + 2, k]
    px[14 + 2 * 7 + 2, 10:w - 6] = hexrgb(0xd0202a)


def marge_hands(C, sh):
    """left: holds the clipboard by its edge (thumb on the page, fingers under); right: a fist round a fat marker,
    tip out the bottom like a knife"""
    palm, fing, th = hand_r([(-1.25, -1.3), (-1.3, -1.25), (-1.3, -1.2), (-1.2, -1.2)], (0.65, 0.35), k=1.05)
    bd = [box((0.19, 0.008, 0.26), (-0.12, -0.055, 0.0), None, bev=0.003, name='board'),
          box((0.08, 0.018, 0.034), (-0.12, -0.046, -0.112), None, bev=0.004, name='clip'),
          box((0.17, 0.003, 0.21), (-0.12, -0.0495, 0.016), None, name='paper')]
    page = box((0.17, 0.002, 0.21), (-0.12, -0.0462, 0.016), None, name='page')
    allp = palm + [o for f in fing for o in f] + th + bd + [page]
    mirror(allp); move(allp, (-sh, 0.925, 0))
    C.many(palm + [o for f in fing for o in f] + th, 'handL', 'gloss', MARGE['skin'], 'skin')
    C.add(bd[0], 'handL', 'gloss', MARGE['board'], 'vinyl'); C.add(bd[1], 'handL', 'metal', 0xdfe4ea, 'chrome'); C.add(bd[2], 'handL', 'cloth', 0xf0ece0, 'weave')
    decal(C, 'cloth', 'sheet', 44, 64, sticker_sheet)
    C.add(page, 'page', 'cloth', 0xffffff, decal=('sheet', '+y'))
    palm, fing, th = hand_r(FIST, (1.0, 0.9), k=1.05)
    hx, hy, _ = FIST_HOLE
    mk = [cyl(0.0135, 0.13, (hx, hy, 0.012), None, axis='z', seg=10, name='marker'), cyl(0.0145, 0.04, (hx, hy, -0.068), None, axis='z', seg=10, name='cap'),
          rod((hx, hy, 0.077), (hx, hy, 0.094), 0.008, None, seg=8, r1=0.003, name='nib')]
    move(palm + [o for f in fing for o in f] + th + mk, (sh, 0.925, 0))
    C.many(palm + [o for f in fing for o in f] + th, 'handR', 'gloss', MARGE['skin'], 'skin')
    C.add(mk[0], 'handR', 'gloss', 0x1a1a20, 'plastic'); C.add(mk[1], 'handR', 'gloss', MARGE['beanie'], 'plastic'); C.add(mk[2], 'handR', 'gloss', 0x2a2a30, 'plastic')
    return (hx + sh, hy + 0.925, 0.094)  # (the nib, standing)


def make_marge():
    sh = 0.262
    gum0 = (0, 1.69, ez(0, 1.69) - 0.01)
    J = skeleton(sh=sh, hip=0.105, extra={
        'gum': ('jaw', gum0), 'page': ('handL', (-sh + 0.12, 0.925 - 0.0468, -0.1))})
    C = Char('marge', J); C.order = order(J)
    sk = MARGE['skin']
    face(C, sk, 0xe8b490, MARGE['brow'], lips=MARGE['lips'], cheek=0xf09a8a, nose=(0.019, 0.026, 0.021), nose_off=(0.006, 0, 0),
         brow=dict(w=0.046, arch=0.002, tilt=-0.008, r=0.0085))
    for i in range(3): C.add(ball(0.0035, (0.035 + i * 0.008, 1.845 - i * 0.012, ez(0.035 + i * 0.008, 1.845 - i * 0.012) - 0.002), None, seg=6, rings=4, name='scar'), 'head', 'gloss', 0xf8e0d0, 'skin')
    # short silver hair under an orange beanie: rolled cuff, a pom-pom she knitted too
    def crop(p, n):
        low = -0.07 if n.z < 0.3 else -0.125  # (at the back it comes down to the nape)
        return -0.06 * min(1.0, max(0.0, (-n.z - 0.2) / 0.2)) * min(1.0, max(0.0, (0.06 - p.y) / 0.02)) - 0.06 * min(1.0, max(0.0, (low - p.y) / 0.02))
    C.add(blob('hair', (0, 1.8, 0.01), (0.126, 0.15, 0.14), None, fn=crop, seg=24, rings=16), 'head', 'gloss', MARGE['hair'], 'hair')
    C.add(blob('beanie', (0, 1.86, 0.008), (0.135, 0.12, 0.146), None, seg=26, rings=16, fn=lambda p, n: -0.14 * max(0.0, -0.035 - p.y) / 0.12 + 0.003 * math.sin(math.atan2(p.z, p.x) * 18)), 'head', 'cloth', MARGE['beanie'], 'knit')
    C.add(lathe([(0.128, -0.026), (0.142, -0.022), (0.146, 0.0), (0.142, 0.022), (0.13, 0.026)], (0, 1.82, 0.006), None, seg=28, axis='y', name='cuff'), 'head', 'cloth', 0xe8601a, 'knit')
    C.add(blob('pom', (0, 1.99, 0.01), (0.045, 0.04, 0.045), None, seg=14, rings=10, fn=lambda p, n: 0.006 * math.sin(p.x * 200) * math.sin(p.z * 190)), 'head', 'cloth', 0xffd21a, 'fuzz')
    gp = Vector(gum0) + Vector((0, 0, -0.055))
    C.add(blob('gum', tuple(gp), (0.055, 0.052, 0.055), None, seg=16, rings=12), 'gum', 'gloss', MARGE['gum'], 'plastic')
    # ---- body: waffle thermal, the cargo vest (pockets, name tape, a grenade in a knitted cosy), dog tags
    C.add(limb('neck', [(0, 1.5, 0.0), (0, 1.6, 0.0), (0, 1.67, 0.012)], [0.056, 0.052, 0.054], None, seg=14), 'neck', 'gloss', sk, 'skin')
    C.add(lathe([(0.06, -0.02), (0.075, -0.012), (0.075, 0.012), (0.062, 0.02)], (0, 1.54, 0.004), None, seg=20, axis='y', name='crew'), 'chest', 'cloth', MARGE['thermal'], 'weave')
    C.add(blob('thermal', (0, 1.3, 0.008), (0.245, 0.198, 0.15), None, seg=24, rings=16), 'chest', 'cloth', MARGE['thermal'], 'weave')
    vz = lambda x, y: 0.008 - 0.168 * math.sqrt(max(0.0, 1 - (x / 0.262) ** 2 - ((y - 1.3) / 0.225) ** 2))
    def vest(p, n):  # open down the middle a little (the thermal shows), square-ish
        return -0.03 * math.exp(-(p.x ** 2) / 0.0005) * max(0.0, -n.z) * min(1.0, max(0.0, (p.y + 0.02) / 0.1))
    C.add(blob('vest', (0, 1.3, 0.008), (0.262, 0.225, 0.168), None, fn=vest, seg=28, rings=18), 'chest', 'cloth', MARGE['vest'], 'canvas')
    C.add(blob('vest_lo', (0, 1.1, 0.0), (0.232, 0.13, 0.158), None, seg=24, rings=14), blend('spine', 'chest', 1.1, 1.22), 'cloth', MARGE['vest'], 'canvas')
    for sx in (-1, 1):
        for (y, w, h) in ((1.38, 0.09, 0.075), (1.12, 0.1, 0.085)):
            x = sx * 0.11; z = vz(x, y) - (0.016 if y > 1.2 else 0.022)
            C.add(box((w, h, 0.022), (x, y, z), None, bev=0.006, rot=(0.12 if y > 1.2 else -0.05, sx * 0.4, 0), name='pocket'), 'chest' if y > 1.2 else 'spine', 'cloth', MARGE['vest_dk'], 'canvas')
            C.add(box((w + 0.012, 0.027, 0.03), (x, y + h * 0.43, z - 0.006), None, bev=0.005, rot=(0.24 if y > 1.2 else 0.07, sx * 0.43, 0), name='flap'), 'chest' if y > 1.2 else 'spine', 'cloth', MARGE['vest'], 'canvas')
        C.add(box((0.09, 0.03, 0.03), (sx * 0.17, 1.5, -0.02), None, bev=0.008, name='strap'), 'chest', 'cloth', MARGE['vest_dk'], 'canvas')
    decal(C, 'cloth', 'tape', 48, 14, lambda px: (px.__setitem__(slice(None), hexrgb(0x4a5a2a)), text_px(px, 'MARGE', 9, 4, 1, 0x120818)))
    C.add(box((0.085, 0.024, 0.004), (0.11, 1.445, vz(0.11, 1.445) - 0.03), None, rot=(0.12, 0.4, 0), name='nametape'), 'chest', 'cloth', 0xffffff, decal=('tape', '-z'))
    tags = [(-0.045, 1.55, -0.05), (-0.035, 1.49, -0.11), (0.0, 1.455, -0.135), (0.035, 1.49, -0.11), (0.045, 1.55, -0.05)]
    C.add(tube(tags, 0.0025, None, seg=5, name='tagchain'), 'chest', 'metal', 0xdfe4ea, 'chain')
    for i, dx in enumerate((-0.006, 0.01)): C.add(box((0.026, 0.04, 0.004), (dx, 1.425 - i * 0.008, -0.142 - i * 0.004), None, bev=0.004, rot=(0.15, 0.1 * i, 0.12 - 0.25 * i), name='tag'), 'chest', 'metal', 0xc8ccd4, 'brushed')
    gx, gy = -0.17, 1.42; gz = vz(gx, gy) - 0.05
    C.add(blob('cosy', (gx, gy, gz), (0.032, 0.042, 0.032), None, seg=14, rings=10, fn=lambda p, n: 0.003 * math.sin(p.y * 300)), 'chest', 'cloth', MARGE['beanie'], 'knit')
    C.add(ball(0.014, (gx, gy - 0.05, gz), None, seg=8, rings=6, name='cosypom'), 'chest', 'cloth', 0xffd21a, 'fuzz')
    C.add(box((0.012, 0.05, 0.01), (gx + 0.018, gy + 0.045, gz), None, rot=(0, 0, -0.3), name='lever'), 'chest', 'metal', 0x6a7a4a, 'cast')
    C.add(tube([(gx - 0.012 + 0.012 * math.cos(a), gy + 0.05 + 0.012 * math.sin(a), gz - 0.002) for a in [i * 2 * math.pi / 10 for i in range(10)]], 0.0025, None, seg=5, name='ring', closed=True), 'chest', 'metal', 0xdfe4ea, 'chrome')
    C.add(lathe([(0.205, -0.025), (0.22, -0.02), (0.22, 0.02), (0.205, 0.025)], (0, 0.99, 0.0), None, seg=28, axis='y', name='belt'), 'hips', 'cloth', 0x2a2a20, 'canvas')
    C.add(box((0.05, 0.04, 0.014), (0, 0.99, -0.162), None, bev=0.004, name='buckle'), 'hips', 'metal', 0x9aa0a8, 'cast')
    C.add(blob('seat', (0, 0.93, 0.005), (0.215, 0.12, 0.158), None, seg=24, rings=12), 'hips', 'cloth', MARGE['pants'], 'canvas')
    for s, sx in (('L', -1), ('R', 1)):
        x = sx * sh
        arm_sleeve(C, s, sh, 0.064, MARGE['thermal'], pat='weave', cuff=False, fore=False)
        C.add(ball(0.06, (x, 1.17, 0), None, seg=14, rings=10, name='elbow' + s), 'fore' + s, 'cloth', MARGE['thermal'], 'weave')
        C.add(lathe([(0.05, -0.03), (0.064, -0.02), (0.066, 0.0), (0.064, 0.02), (0.05, 0.03)], (x, 1.1, 0), None, seg=16, axis='y', name='roll' + s), 'fore' + s, 'cloth', MARGE['thermal'], 'weave')
        C.add(limb('forearm' + s, [(x, 1.112, 0), (x, 1.04, -0.004), (x, 0.95, 0)], [0.046, 0.048, 0.036], None, seg=14), 'fore' + s, 'gloss', sk, 'skin')
    C.nib = marge_hands(C, sh)
    for s, sx in (('L', -1), ('R', 1)):
        x = sx * 0.105
        C.add(limb('thigh' + s, [(x, 0.95, 0.0), (x, 0.72, -0.004), (x, 0.5, 0.0)], [0.105, 0.092, 0.078], None, seg=16), 'thigh' + s, 'cloth', MARGE['pants'], 'canvas')
        C.add(box((0.045, 0.1, 0.1), (x + sx * 0.078, 0.7, 0.0), None, bev=0.012, name='cargo'), 'thigh' + s, 'cloth', 0x23315a, 'canvas')
        C.add(ball(0.068, (x, 0.49, 0), None, seg=14, rings=10, name='knee'), 'shin' + s, 'cloth', MARGE['pants'], 'canvas')
        C.add(limb('shin' + s, [(x, 0.49, 0.0), (x, 0.32, 0.004), (x, 0.2, 0.0)], [0.072, 0.066, 0.066], None, seg=16), 'shin' + s, 'cloth', MARGE['pants'], 'canvas')
        C.add(limb('bootleg' + s, [(x, 0.24, 0.0), (x, 0.08, 0.0)], [0.07, 0.068], None, seg=16), 'foot' + s, 'gloss', MARGE['boots'], 'vinyl')
        C.add(blob('boot' + s, (x, 0.07, -0.05), (0.064, 0.068, 0.135), None, seg=16, rings=10, fn=lambda p, n: -0.028 * max(0.0, n.y) * max(0.0, p.z + 0.02) / 0.16), 'foot' + s, 'gloss', MARGE['boots'], 'vinyl')
        C.add(blob('sole' + s, (x, 0.018, -0.05), (0.07, 0.02, 0.142), None, seg=16, rings=8), 'foot' + s, 'gloss', 0x2a2420, 'vinyl')
        for i in range(4): C.add(box((0.07, 0.008, 0.01), (x, 0.12 + i * 0.035, -0.072), None, rot=(0, 0, 0.5 * (-1) ** i), name='lace'), 'foot' + s, 'gloss', MARGE['beanie'], 'plastic')
    return C


def marge_pose(C):
    """sat on the crate, legs out along the crates, the right knee bent the wrong way (boot up in the air)"""
    return {'hips.py': -1.0, 'hips.x': 0.1, 'spine.x': -0.03, 'chest.x': -0.04, 'neck.x': 0.02, 'head.z': -0.07, 'head.x': 0.0,
            'thighL.x': 1.47, 'thighR.x': 1.42, 'thighL.z': -0.05, 'thighR.z': 0.05, 'thighL.y': 0.06, 'thighR.y': -0.08,
            'shinL.x': -0.06, 'shinR.x': 0.4, 'footL.x': -0.25, 'footR.x': -0.55, 'footL.y': 0.15, 'footR.y': -0.2,
            'lidL.x': -0.25, 'lidR.x': 0.32, 'browL.py': -0.006, 'browR.py': 0.002, 'gum.s': 0.14}


def marge_clips(C):
    B = marge_pose(C)
    def board(P, centre, face_to, w=0.4, extra=()):
        """the clipboard's middle at `centre`, its page facing `face_to` (a point), held at its left edge"""
        sp = fk(C, P)['armL'][:3, 3]
        bc = (0.12 * S, -0.051 * S, 0.0)
        Wh = fk(C, P)['handL']; cur = (Wh @ np.array([*bc, 1.0]))[:3]
        terms = [('pos', 'handL', bc, centre, 1.0), ('dir', 'handL', (0, 1, 0), tuple(np.array(face_to) - np.array(centre)), w),
                 ('dir', 'handL', (0, 0, -1), (0, 1, 0.2), w * 0.5), ('pos', 'foreL', (0, 0, 0), tuple(sp + np.array([-0.08, -0.24, -0.1])), 0.1)]
        return ik(C, P, terms + list(extra), ['armL.x', 'armL.y', 'armL.z', 'foreL.x', 'foreL.y', 'handL.x', 'handL.y', 'handL.z'])
    def nib(P, at, w=0.2, point=(0, -1, -0.3)):
        sp = fk(C, P)['armR'][:3, 3]
        lp = tuple(np.array([C.nib[0] - 0.262, C.nib[1] - 0.925, C.nib[2]]) * S)
        terms = [('pos', 'handR', lp, at, 1.0), ('dir', 'handR', (0, 0, 1), point, w), ('pos', 'foreR', (0, 0, 0), tuple(sp + np.array([0.08, -0.24, -0.1])), 0.1)]
        return ik(C, P, terms, ['armR.x', 'armR.y', 'armR.z', 'foreR.x', 'foreR.y', 'handR.x', 'handR.y', 'handR.z'])
    head = lambda P: fk(C, P)['head'][:3, 3] + np.array([0, 0.15, -0.1])
    on_board = lambda P, u, v: tuple((fk(C, P)['handL'] @ np.array([(0.12 + u) * S, -0.04 * S, v * S, 1.0]))[:3])  # (a spot on the page: u across, v down)
    P = board(B, (0.02, 0.42, -0.42), head(B))
    P = nib(P, on_board(P, 0.06, 0.09))
    C.base = P
    # idle (7 s): taps the marker on the board, a look round, a bubble of gum (pop), the wrong-knee boot taps the air
    I = Clip('idle', 7.0, True, P)
    I.osc += [('chest.x', 0.012, 3.5, 0.0), ('head.x', -0.006, 3.5, 0.5), ('footR.x', 0.16, 7.0 / 4, 0.0)]
    for t in (0.7, 0.95, 1.2): I.pulses.append(('foreR.x', t, 0.12, 0.06, 0.0, 0.1))
    I.key(1.9, P); I.key(2.4, {'head.y': -0.5, 'head.x': 0.06, 'chest.y': -0.08}); I.key(2.9, {'head.y': -0.55}); I.key(3.3, {'head.y': 0.0, 'head.x': 0.0, 'chest.y': 0.0})
    I.key(3.7, {'gum.s': 0.14, 'jaw.x': 0.0}); I.key(3.9, {'gum.s': 0.3, 'jaw.x': -0.04}); I.key(4.6, {'gum.s': 0.75, 'jaw.x': -0.05}); I.key(5.2, {'gum.s': 1.05, 'head.x': 0.04})
    I.key(5.24, {'gum.s': 0.06, 'head.x': -0.06, 'lidL.x': -1.0, 'lidR.x': -0.9}); I.key(5.5, {'gum.s': 0.1, 'head.x': 0.0, 'lidL.x': B['lidL.x'], 'lidR.x': B['lidR.x'], 'jaw.x': 0.0})
    I.key(6.0, {'gum.s': 0.14})
    I.blink(1.55, d=0.2); I.blink(6.3, d=0.2)
    I.marks = [(5.23, 'pop')]
    # talk: points the marker at you, jabs it on the words, squints harder
    T0 = dict(P, **{'lidL.x': -0.45, 'browL.py': -0.01, 'browR.py': 0.004, 'head.x': -0.04})
    T0 = nib(T0, (0.2, 0.95, -0.62), w=0.4, point=(0, 0.2, -1))
    T = Clip('talk', 2.4, True, T0)
    T.key(1.2, dict(T0, **{'head.y': -0.08})); T.key(1.8, T0)
    for t, a in ((0.1, 0.12), (0.36, 0.09), (0.62, 0.15), (0.92, 0.08), (1.2, 0.13), (1.5, 0.1), (1.78, 0.14), (2.05, 0.07)):
        T.pulses.append(('jaw.x', t, -a, 0.05, 0.03, 0.08)); T.pulses.append(('foreR.x', t, a * 1.1, 0.05, 0.0, 0.12)); T.pulses.append(('head.x', t, -a * 0.25, 0.05, 0.0, 0.12))
    T.blink(1.45, d=0.18)
    # gesture: checks the clipboard. up to her nose, runs the marker down, TICK, flips the page up, a look, one nod
    G = Clip('gesture', 3.0, False, P)
    R0 = dict(P, **{'head.x': -0.22, 'lidL.x': -0.55, 'lidR.x': 0.05, 'chest.x': -0.1})
    R0 = board(R0, (0.0, 0.62, -0.36), head(R0))
    G.key(0.38, nib(R0, on_board(R0, 0.06, -0.06)))
    for t, v in ((0.6, -0.03), (0.78, 0.0), (0.96, 0.03), (1.12, 0.055)): G.key(t, nib(G.last(), on_board(G.last(), 0.065, v)))
    tick = nib(G.last(), on_board(G.last(), -0.075, 0.06)); G.key(1.24, tick)
    G.key(1.32, nib(tick, on_board(tick, -0.04, 0.035)))
    G.key(1.48, {'page.x': -0.4}); G.key(1.7, {'page.x': -2.3}); G.key(1.95, {'page.x': -2.2})
    G.key(2.15, {'page.x': 0.0, 'head.x': 0.04, 'lidL.x': -0.3, 'lidR.x': 0.35}); G.key(2.35, {'head.x': -0.16}); G.key(2.5, {'head.x': 0.02})
    G.key(3.0, P)
    G.marks = [(1.24, 'tick'), (1.5, 'flip')]
    return [I, T, G]


# ================================================================== build, export, sheets
def run(make, clips_fn, file_id, meta_extra, views_extra=()):
    reset()
    C = make()
    C.stamp_face = getattr(C, 'stamp_face', (0.031, -0.069, 0.09))
    clips = clips_fn(C)
    meta = {'kind': 'npc', 'id': C.cid, 'clips': {c.name: {'len': c.length, 'loop': c.loop, 'marks': [[round(t, 3), m] for t, m in c.marks]} for c in clips}, **meta_extra}
    assemble(C, meta)
    if '--qa' in ARGV: qa(C)
    for c in clips: bake(C, c)
    if '--no-export' not in ARGV: export(C, file_id)
    if '--no-sheet' not in ARGV: sheets(C, clips, file_id)
    return C


def sheets(C, clips, file_id):
    ink_on(C)
    idle = clips[0]
    pose_at(C, idle, 0.0)
    W, H = 420, 560
    v = render_views(C, [('FRONT', 0, 0.1, 1.75), ('3/4', 35, 0.12, 1.75), ('SIDE', 90, 0.08, 1.75), ('BACK', 180, 0.1, 1.75), ('3/4 BACK', 215, 0.15, 1.75)], (W, H), file_id)
    lo, hi = bounds(C)
    head = fk(C, idle.sample(0.0))['head'][:3, 3]; hc = (head[0], -head[2], head[1] + 0.13)
    v += render_views(C, [('FACE', 25, 0.05, 0.42, hc)], (W, H), file_id + 'f')
    tile(v, 3, os.path.join(SHEETS, f'{file_id}.jpg'), f'{C.cid.upper()}  turnaround (idle, frame 0)', (W, H))
    # the pose sheet: moments from every clip, from the 3/4 front
    shots = []
    for c in clips:
        ts = [c.length * k for k in ((0.0, 0.3, 0.45, 0.75) if c.loop else (0.1, 0.17, 0.35, 0.52, 0.7, 0.88))]
        for t in ts:
            pose_at(C, c, t)
            shots += [(f'{c.name.upper()}  {t:.2f} S', p) for _, p in render_views(C, [('', 25, 0.12, 1.85)], (W, H), f'{file_id}_{c.name}_{t:.2f}')]
    tile(shots, 7, os.path.join(SHEETS, f'{file_id}_poses.jpg'), f'{C.cid.upper()}  idle / talk / gesture', (W, H))
    ink_off(C)


if __name__ == '__main__' or True:
    if ONLY is None or 'deb' in ONLY:
        run(make_deb, deb_clips, 'x_lobby_deb', {'place': {'prop': 'desk', 'at': [DEB_AT[0], 0, DEB_AT[1]], 'yaw': math.pi},
                                                 'hide': ['stamp'], 'look': {'body': 0.45, 'head': 0.7}})
    if ONLY is None or 'gus' in ONLY:
        run(make_gus, gus_clips, 'x_lobby_gus', {'place': {'prop': 'counter', 'at': [GUS_AT[0], 0, GUS_AT[1]], 'yaw': math.pi}, 'look': {'body': 0.35, 'head': 0.8}})
    if ONLY is None or 'marge' in ONLY:
        run(make_marge, marge_clips, 'x_lobby_marge', {'place': {'prop': 'crates', 'at': list(MARGE_AT), 'yaw': MARGE_YAW}, 'look': {'body': 0.08, 'head': 0.9}})
