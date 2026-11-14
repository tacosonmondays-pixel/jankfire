# THE RULES GUY (x_bgn_rulesguy.glb), BOARD GAME NIGHT's host (docs/party/DESIGN.md 1): a mannequin in a mustard
# cardigan holding the rulebook open, upside down. Deadpan: lids at half-mast, flat brows, big round glasses, a neat
# moustache, a comb-over that fools nobody, a pink knit tie, elbow patches, a HELLO MY NAME IS sticker, penny loafers
# (the left knee bends the wrong way, the house jank). The book rides his left hand (palm up under it); the right hand
# is a pointer (pages, the "actually" finger). One skinned mesh on the lobby people's skeleton (lobby/npckit.py), clips
# baked in: idle (reads, tilts his head at the upside down page, turns a page), talk (looks up, the finger),
# gesture (MISREAD THE RULES: spins the book all the way round, studies it, nods. still upside down).
# The board scene puts the figure on the table at meta.boardScale (an action figure); the kitchen lobby, life size.
#   blender52 -b --python tools/blender/bgn/make_rulesguy.py -- [--no-sheet] [--no-export] [--qa]
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(HERE), 'lobby')
sys.path.insert(0, LOBBY)
if '--' not in sys.argv: sys.argv.append('--')
if not any(a.startswith('--only=') for a in sys.argv): sys.argv.append('--only=rulesguy')  # (make_lobby_npcs builds none of its own people then)
import make_lobby_npcs as NP  # noqa: E402  (the face, sleeve and hand kits)
from npckit import *  # noqa

RG = dict(skin=0xf0c49a, cardi=0xf2b630, cardi_dk=0xc88a18, shirt=0xdaf4ff, tie=0xff4fd8, pants=0x463c56, shoes=0x8a4a22, hair=0x8a7a6a,
          brow=0x5a4a3c, book=0xff4fd8, page=0xfff8ea, frames=0x2a1630, patch=0x7a4a2a, button=0x8a5a2a)
SH = 0.25
BOOK = dict(cx=-0.165, cy=-0.064, w=0.15, h=0.21, ang=0.2)  # (in the right hand's frame before the mirror: x toward the thumb side)


def sticker_hello(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0xffffff)
    px[0:9] = hexrgb(0xff3030); text_px(px, 'HELLO', 9, 1, 1, 0xffffff)
    text_px(px, 'RULES', 3, 12, 1, 0x120818); text_px(px, 'GUY', 3, 20, 1, 0x120818)


def sticker_cover(px):
    """the rulebook's cover: RULES in yellow on pink, a die, the box's sparkle. painted the right way up, then turned
    180 degrees: he holds it upside down"""
    h, w = px.shape[:2]; px[:] = hexrgb(0xff4fd8)
    px[2:4, 2:w - 2] = hexrgb(0xffe14d); px[h - 4:h - 2, 2:w - 2] = hexrgb(0xffe14d)
    text_px(px, 'RULES', 4, 8, 2, 0xffe14d)
    text_px(px, 'BGN', 15, 26, 1, 0xffffff)
    for x, y in ((18, 36), (24, 36), (21, 39), (18, 42), (24, 42)): px[y:y + 2, x:x + 2] = hexrgb(0x120818)
    px[:] = px[::-1, ::-1].copy()


def sticker_pages(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0xfff8ea)
    for i in range(9):
        y = 4 + i * 6
        n = w - 6 - (i * 7) % 13
        for x in range(3, n): px[y + (x // 4) % 2, x] = hexrgb(0x6a5a7a) if x % 5 else px[y, x]
    text_px(px, '7', w - 7, h - 9, 1, 0xff3030)


def book_parts(C):
    """the open rulebook in the right hand's frame (mirrored onto the left with the hand): covers, page blocks, the
    page that turns (on its own bone at the spine)"""
    b = BOOK; out = []
    for side in (-1, 1):
        ex = b['cx'] + side * b['w'] / 2; lift = math.sin(b['ang']) * b['w'] / 2
        cov = box((b['w'], 0.006, b['h']), (ex, b['cy'] + lift, 0.0), None, bev=0.0025, rot=(0, 0, -side * b['ang']), name='cover')
        pg = box((b['w'] - 0.008, 0.014, b['h'] - 0.01), (ex - side * 0.002, b['cy'] + lift + 0.0095, 0.0), None, bev=0.002, rot=(0, 0, -side * b['ang']), name='pages')
        top = box((b['w'] - 0.012, 0.0006, b['h'] - 0.016), (ex - side * 0.002, b['cy'] + lift + 0.0179, 0.0), None, rot=(0, 0, -side * b['ang']), name='leaf')
        out += [(cov, 'gloss', RG['book'], 'vinyl', ('cover', '-y')), (pg, 'cloth', RG['page'], 'weave', None), (top, 'cloth', 0xffffff, None, ('pages', '+y'))]
    spine = cyl(0.009, b['h'], (b['cx'], b['cy'] - 0.003, 0.0), None, axis='z', seg=10, name='spine')
    out.append((spine, 'gloss', RG['book'], 'vinyl', None))
    return out


def page_part(C):
    b = BOOK
    side = 1; ex = b['cx'] + side * (b['w'] - 0.014) / 2; lift = math.sin(b['ang']) * b['w'] / 2
    p = box((b['w'] - 0.014, 0.0012, b['h'] - 0.02), (ex, b['cy'] + lift + 0.0199, 0.0), None, rot=(0, 0, -side * b['ang']), name='page')
    return p


def rg_hands(C, sh):
    """left: palm up under the book, thumb over the page; right: the pointer (index straight, the rest curled)"""
    palm, fing, th = hand_r([(-0.55, -0.35), (-0.6, -0.4), (-0.65, -0.45), (-0.7, -0.5)], (0.75, 0.4), k=1.05)
    bk = book_parts(C)
    pg = page_part(C)
    allp = palm + [o for f in fing for o in f] + th + [o for o, *_ in bk] + [pg]
    mirror(allp); move(allp, (-sh, 0.925, 0))
    C.many(palm + [o for f in fing for o in f] + th, 'handL', 'gloss', RG['skin'], 'skin')
    for o, kind, col, pat, dec in bk:
        if dec: C.add(o, 'book', kind, col, decal=dec)
        else: C.add(o, 'book', kind, col, pat)
    C.add(pg, 'page', 'cloth', 0xffffff, decal=('pages', '+y'))
    palm, fing, th = hand_r([(-0.05, -0.08), (-1.45, -1.6), (-1.5, -1.6), (-1.45, -1.55)], (0.9, 1.0), k=1.05)
    move(palm + [o for f in fing for o in f] + th, (sh, 0.925, 0))
    C.many(palm + [o for f in fing for o in f] + th, 'handR', 'gloss', RG['skin'], 'skin')


def make_rulesguy():
    sh = SH
    b = BOOK
    spine_l = (-sh - b['cx'], 0.925 + b['cy'], 0.0)  # (the spine after the mirror, standing)
    J = skeleton(sh=sh, hip=0.1, extra={'book': ('handL', spine_l), 'page': ('book', spine_l)})
    C = Char('rulesguy', J); C.order = order(J)
    sk = RG['skin']
    NP.face(C, sk, sk, RG['brow'], lips=0xc87a6a, nose=(0.02, 0.03, 0.024), brow=dict(w=0.046, arch=0.0, tilt=0.0, r=0.0078))
    # the comb-over: hair round the sides and back below the crown, three strands combed over the top
    def fringe(p, n):
        top = min(1.0, max(0.0, (p.y + 0.005) / 0.03)); front = min(1.0, max(0.0, (-n.z - 0.25) / 0.2))
        return -0.07 * max(top, front)
    C.add(blob('hair', (0, 1.775, 0.012), (0.127, 0.14, 0.14), None, fn=fringe, seg=24, rings=16), 'head', 'gloss', RG['hair'], 'hair')
    for i, dz in enumerate((-0.045, -0.012, 0.022)):
        pts = []
        for k in range(9):
            x = -0.12 + k * 0.03; y = HEAD_C[1] + HEAD_R[1] * math.sqrt(max(0.0, 1 - (x / HEAD_R[0]) ** 2 - (dz / HEAD_R[2]) ** 2)) * 0.995
            pts.append((x, y + 0.002, dz + 0.004 * math.sin(k)))
        C.add(limb('strand', pts, [0.004] * 9, None, seg=6, squash=(0.6, 1.0)), 'head', 'gloss', RG['hair'], 'hair')
    # big round glasses (dark frames, no lenses: the deadpan eyes show), a neat moustache
    for sx in (-1, 1):
        cx = sx * 0.045; cz = ez(cx, 1.787) - 0.016
        C.add(tube([(cx + 0.034 * math.cos(a), 1.787 + 0.03 * math.sin(a), cz) for a in [i * 2 * math.pi / 16 for i in range(16)]], 0.0042, None, seg=6, name='rim', closed=True), 'head', 'gloss', RG['frames'], 'plastic')
        C.add(tube([(sx * 0.079, 1.79, cz + 0.004), (sx * 0.118, 1.79, -0.02), (sx * 0.125, 1.775, 0.06)], 0.0032, None, seg=5, name='temple'), 'head', 'gloss', RG['frames'], 'plastic')
    rz = ez(0.045, 1.787) - 0.016  # (the rims' plane: the bridge joins them there)
    C.add(tube([(-0.0125, 1.792, rz), (0.0, 1.797, rz - 0.004), (0.0125, 1.792, rz)], 0.0032, None, seg=5, name='bridge'), 'head', 'gloss', RG['frames'], 'plastic')
    C.add(limb('tache', [(x, 1.716 - 0.004 * (x / 0.03) ** 2, ez(x, 1.716) - 0.008) for x in (-0.034, -0.017, 0.0, 0.017, 0.034)], [0.004, 0.008, 0.009, 0.008, 0.004], None, seg=8, squash=(0.7, 1.0)), 'head', 'gloss', RG['brow'], 'hair')
    # ---- body: shirt + collar + the pink knit tie under a V-neck mustard cardigan, buttons, pockets, the sticker
    C.add(limb('neck', [(0, 1.5, 0.0), (0, 1.6, 0.0), (0, 1.67, 0.012)], [0.056, 0.052, 0.054], None, seg=14), 'neck', 'gloss', sk, 'skin')
    C.add(blob('shirt', (0, 1.31, 0.01), (0.235, 0.2, 0.15), None, seg=24, rings=16), 'chest', 'cloth', RG['shirt'], 'weave')
    for sx in (-1, 1): C.add(box((0.05, 0.012, 0.045), (sx * 0.035, 1.525, -0.07), None, bev=0.004, rot=(0.55, sx * 0.5, sx * 0.35), name='collar'), 'chest', 'cloth', RG['shirt'], 'weave')
    tz = lambda y: 0.01 - 0.15 * math.sqrt(max(0.0, 1 - ((y - 1.31) / 0.2) ** 2)) - 0.012
    C.add(limb('tie', [(0, 1.5, tz(1.5) + 0.006), (0, 1.4, tz(1.4)), (0, 1.27, tz(1.27)), (0, 1.17, tz(1.17) + 0.005)], [0.016, 0.022, 0.026, 0.024], None, seg=8, squash=(0.35, 1.0)), 'chest', 'cloth', RG['tie'], 'knit')
    C.add(blob('knot', (0, 1.505, tz(1.505) + 0.002), (0.016, 0.014, 0.012), None, seg=10, rings=6), 'chest', 'cloth', RG['tie'], 'knit')
    def vneck(p, n):  # the V: open down the front to the buttons
        y = p.y + 1.31; half = max(0.0, (y - 1.2)) * 0.42
        return -0.035 * max(0.0, -n.z) * min(1.0, max(0.0, (half - abs(p.x)) / 0.015)) if y > 1.2 else 0.0
    C.add(blob('cardi', (0, 1.31, 0.01), (0.255, 0.215, 0.165), None, fn=vneck, seg=28, rings=18), 'chest', 'cloth', RG['cardi'], 'knit')
    C.add(blob('cardi_lo', (0, 1.1, 0.0), (0.238, 0.15, 0.158), None, seg=24, rings=14), blend('spine', 'chest', 1.1, 1.22), 'cloth', RG['cardi'], 'knit')
    cz = lambda x, y, r=(0.255, 0.215, 0.165), c=1.31: 0.01 - r[2] * math.sqrt(max(0.0, 1 - (x / r[0]) ** 2 - ((y - c) / r[1]) ** 2))
    for y in (1.19, 1.11, 1.03):
        z = cz(0, y) if y > 1.15 else 0.0 - 0.158 * math.sqrt(max(0.0, 1 - ((y - 1.1) / 0.15) ** 2))
        C.add(ball(0.011, (0.0, y, z - 0.004), None, seg=10, rings=6, scale=(1, 1, 0.5), name='button'), 'spine' if y < 1.15 else 'chest', 'gloss', RG['button'], 'plastic')
    for sx in (-1, 1):
        x = sx * 0.12; z = -0.158 * math.sqrt(max(0.0, 1 - (x / 0.238) ** 2 - ((1.05 - 1.1) / 0.15) ** 2)) - 0.012
        C.add(box((0.085, 0.075, 0.014), (x, 1.05, z), None, bev=0.006, rot=(-0.1, sx * 0.45, 0), name='pocket'), 'spine', 'cloth', RG['cardi_dk'], 'knit')
    decal(C, 'cloth', 'hello', 40, 28, sticker_hello)
    decal(C, 'cloth', 'pages', 40, 60, sticker_pages)
    decal(C, 'gloss', 'cover', 48, 52, sticker_cover)
    C.add(box((0.07, 0.048, 0.003), (0.12, 1.38, cz(0.12, 1.38) - 0.006), None, rot=(0.25, 0.42, 0.05), name='hello'), 'chest', 'cloth', 0xffffff, decal=('hello', '-z'))
    C.add(lathe([(0.21, -0.025), (0.222, -0.02), (0.222, 0.02), (0.21, 0.025)], (0, 0.985, 0.0), None, seg=28, axis='y', name='belt'), 'hips', 'gloss', 0x3a2414, 'vinyl')
    C.add(blob('seat', (0, 0.93, 0.005), (0.215, 0.12, 0.158), None, seg=24, rings=12), 'hips', 'cloth', RG['pants'], 'weave')
    for s, sx in (('L', -1), ('R', 1)):
        NP.arm_sleeve(C, s, sh, 0.068, RG['cardi'], pat='knit')
        C.add(blob('patch' + s, (sx * sh, 1.17, 0.06), (0.045, 0.06, 0.02), None, seg=12, rings=8), 'fore' + s, 'cloth', RG['patch'], 'canvas')
    rg_hands(C, sh)
    for s, sx in (('L', -1), ('R', 1)):
        x = sx * 0.1
        C.add(limb('thigh' + s, [(x, 0.95, 0.0), (x, 0.72, -0.004), (x, 0.5, 0.0)], [0.1, 0.088, 0.075], None, seg=16), 'thigh' + s, 'cloth', RG['pants'], 'weave')
        C.add(box((0.006, 0.4, 0.004), (x, 0.73, -0.088), None, name='crease'), 'thigh' + s, 'cloth', 0x5a5070, 'weave')
        C.add(ball(0.066, (x, 0.49, 0), None, seg=14, rings=10, name='knee'), 'shin' + s, 'cloth', RG['pants'], 'weave')
        C.add(limb('shin' + s, [(x, 0.49, 0.0), (x, 0.3, 0.004), (x, 0.11, 0.0)], [0.07, 0.064, 0.066], None, seg=16), 'shin' + s, 'cloth', RG['pants'], 'weave')
        C.add(blob('shoe' + s, (x, 0.055, -0.045), (0.058, 0.055, 0.135), None, seg=16, rings=10, fn=lambda p, n: -0.02 * max(0.0, n.y) * max(0.0, p.z + 0.02) / 0.16), 'foot' + s, 'gloss', RG['shoes'], 'vinyl')
        C.add(box((0.08, 0.012, 0.024), (x, 0.088, -0.1), None, bev=0.004, rot=(-0.4, 0, 0), name='strap'), 'foot' + s, 'gloss', 0x6a3418, 'vinyl')
        C.add(cyl(0.008, 0.002, (x, 0.093, -0.106), None, axis='z', seg=10, rot=(-0.4, 0, 0), name='penny'), 'foot' + s, 'metal', 0xd88a4a, 'brushed')
        C.add(box((0.12, 0.018, 0.28), (x, 0.009, -0.045), None, bev=0.006, name='sole'), 'foot' + s, 'gloss', 0x2a1a14, 'vinyl')
    return C


def rg_pose(C):
    """stands a bit stooped over the book, feet together-ish, the left knee bent the wrong way"""
    return {'chest.x': 0.04, 'neck.x': 0.12, 'head.x': 0.22, 'head.z': 0.0, 'thighL.x': -0.18, 'shinL.x': 0.36, 'footL.x': -0.18,
            'thighL.z': -0.04, 'thighR.z': 0.04, 'thighR.y': -0.12, 'thighL.y': 0.1, 'lidL.x': 0.05, 'lidR.x': 0.05, 'browL.py': -0.002, 'browR.py': -0.002}


def rg_clips(C):
    B = rg_pose(C)
    sl = np.array(C.J['book'][1]) * S
    def book(P, centre, up_to, w=0.45):
        """the book's spine at `centre`, its pages facing `up_to` (a point: his face), its top edge pointing down (upside down)"""
        sp = fk(C, P)['armL'][:3, 3]
        terms = [('pos', 'book', (0, 0, 0), centre, 12.0), ('dir', 'book', (0, 1, 0), tuple(np.array(up_to) - np.array(centre)), w),
                 ('dir', 'book', (0, 0, -1), (0, 0.3, 1), w * 0.4), ('pos', 'foreL', (0, 0, 0), tuple(sp + np.array([-0.06, -0.28, -0.1])), 0.08)]
        return ik(C, P, terms, ['armL.x', 'armL.y', 'armL.z', 'foreL.x', 'foreL.y', 'handL.x', 'handL.y', 'handL.z'])
    tip = (0.0, -0.165 * S, -0.03 * S)  # (the right index fingertip, in the hand's rest space)
    def point(P, at, w=0.25, d=(0, -0.2, -1)):
        sp = fk(C, P)['armR'][:3, 3]
        terms = [('pos', 'handR', tip, at, 12.0), ('dir', 'handR', (0, -1, 0), d, w), ('pos', 'foreR', (0, 0, 0), tuple(sp + np.array([0.08, -0.26, -0.08])), 0.08)]
        return ik(C, P, terms, ['armR.x', 'armR.y', 'armR.z', 'foreR.x', 'foreR.y', 'handR.x', 'handR.y', 'handR.z'])
    face = lambda P: fk(C, P)['head'][:3, 3] + np.array([0.0, 0.12 * S, -0.12 * S])
    P = book(B, (0.02, 1.3 * S, -0.36 * S), face(B))
    on_page = lambda P, u, v: tuple((fk(C, P)['book'] @ np.array([u * S, 0.03 * S, v * S, 1.0]))[:3])
    P = point(P, on_page(P, 0.09, 0.04), d=(0, -1, -0.3))
    P = dict(P, **{'armR.x': P.get('armR.x', 0) * 0.7})  # (the right hand hangs back a little: reading, not pointing)
    P = point(P, (0.22 * S, 1.02 * S, -0.12 * S), w=0.1, d=(0, -1, 0))
    C.base = P
    # idle: reads. tilts his head right round to read it the wrong way up, a long blink, turns a page with the finger
    I = Clip('idle', 6.4, True, P)
    I.osc += [('chest.x', 0.01, 3.2, 0.0), ('head.x', -0.006, 3.2, 0.4)]
    I.key(1.4, {'head.z': 0.0}); I.key(1.9, {'head.z': 0.42, 'head.y': 0.06, 'browL.py': 0.006}); I.key(2.9, {'head.z': 0.46}); I.key(3.3, {'head.z': 0.0, 'head.y': 0.0, 'browL.py': -0.002})
    turn0 = point(P, on_page(P, 0.12, 0.02), w=0.2, d=(0, -1, -0.4))
    I.key(3.9, turn0); I.key(4.1, dict(turn0, **{'page.z': 0.0}))
    I.key(4.55, dict(point(turn0, on_page(P, -0.09, 0.0), w=0.2, d=(0, -1, -0.4)), **{'page.z': 2.85}))
    I.key(4.75, {'page.z': 2.95}); I.key(5.4, dict(P, **{'page.z': 0.0}))  # (the page snaps back: it was the same page)
    I.blink(0.9, d=0.25); I.blink(3.5, d=0.6, depth=0.9); I.blink(5.9, d=0.22)
    I.marks = [(4.3, 'page')]
    # talk: looks up over the glasses, the finger up ("actually"), the book drops a little
    T0 = dict(P, **{'head.x': -0.02, 'neck.x': 0.02, 'lidL.x': 0.1, 'lidR.x': 0.1, 'browL.py': 0.004, 'browR.py': 0.004})
    T0 = book(T0, (0.02, 1.2 * S, -0.34 * S), face(B), w=0.3)
    T0 = point(T0, (0.2 * S, 1.6 * S, -0.3 * S), w=0.4, d=(0, 1, -0.1))
    T = Clip('talk', 2.4, True, T0)
    T1 = point(dict(T0, **{'head.y': -0.06}), (0.21 * S, 1.66 * S, -0.32 * S), w=0.4, d=(0, 1, -0.2))
    T.key(0.8, T1); T.key(1.4, dict(T0, **{'head.x': -0.05})); T.key(2.0, T1)
    for t, a in ((0.1, 0.1), (0.36, 0.07), (0.62, 0.12), (0.95, 0.08), (1.22, 0.11), (1.5, 0.06), (1.78, 0.12), (2.05, 0.08)):
        T.pulses.append(('jaw.x', t, -a, 0.05, 0.03, 0.08)); T.pulses.append(('handR.x', t, a * 0.8, 0.05, 0.0, 0.12))
    T.blink(1.6, d=0.22)
    # gesture: MISREAD THE RULES. the book comes up, turns all the way round (360: still upside down), he studies it, one nod
    G = Clip('gesture', 3.0, False, P)
    up = book(dict(P, **{'head.x': 0.1}), (0.0, 1.38 * S, -0.42 * S), face(B), w=0.3)
    up = point(up, (0.16 * S, 1.38 * S, -0.48 * S), w=0.2, d=(-1, 0, -0.3))
    G.key(0.35, up)
    for t, a in ((0.55, 1.2), (0.8, 3.1), (1.05, 4.9), (1.25, 6.283)): G.key(t, {'book.y': a})
    G.key(1.6, {'head.z': -0.3, 'head.x': 0.18, 'browL.py': 0.008, 'browR.py': -0.003}); G.key(2.1, {'head.z': -0.32})
    G.key(2.3, {'head.z': 0.0, 'head.x': 0.3}); G.key(2.45, {'head.x': 0.08}); G.key(2.6, {'head.x': 0.22})
    G.key(3.0, dict(P, **{'book.y': 6.283}))
    G.blink(1.5, d=0.25)
    G.marks = [(0.6, 'spin'), (2.35, 'nod')]
    return [I, T, G]


if __name__ == '__main__':
    NP.run(make_rulesguy, rg_clips, 'x_bgn_rulesguy', {'look': {'body': 0.3, 'head': 0.8}, 'boardScale': 1.45, 'hide': []})
