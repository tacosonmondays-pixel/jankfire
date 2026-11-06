# Card Deck, its thrown card, the Reverse Card and the Skip Card skin.
# Real playing-card stock: rounded corners, a white core edge, a glossy coated back with our own design (red field, a
# yellow diamond lattice, a white oval with JF in it). The deck's fan is the code model's 0.08 x 0.12 cards (poker size
# x1.3); weapons.js deals your actual hand onto it every frame (card0..card4 = the face meshes, back + edge are their
# children). The thrown card is the big 0.18 x 0.26 one the code flies, flat, the back on both sides.
# Reverse / Skip: thick 0.12 x 0.18 game cards, tilted back like the code's, glossy, the faces in the game's own design.
# run: blender -b --python tools/blender/make_cards.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link

SUIT_PX = {  # 7x7 suit glyphs
    's': ['0001000', '0011100', '0111110', '1111111', '1111111', '0101010', '0011100'],
    'h': ['0110110', '1111111', '1111111', '1111111', '0111110', '0011100', '0001000'],
    'd': ['0001000', '0011100', '0111110', '1111111', '0111110', '0011100', '0001000'],
    'c': ['0011100', '0011100', '1101011', '1111111', '1101011', '0001000', '0011100'],
}


def glyph(px, g, x0, y0, s, color):
    c = hexrgb(color)
    for ry, row in enumerate(g):
        for rx, b in enumerate(row):
            if b == '1': px[y0 + ry * s:y0 + (ry + 1) * s, x0 + rx * s:x0 + (rx + 1) * s] = c


def back_px(px):  # our card back: white margin, red field, yellow diamond lattice, a white oval with JF
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf6f4ee)
    px[2:h - 2, 2:w - 2] = hexrgb(0xc02040)
    yy, xx = np.mgrid[0:h, 0:w]
    lat = (((xx + yy) % 12 == 0) | ((xx - yy) % 12 == 0)) & (xx > 4) & (xx < w - 5) & (yy > 4) & (yy < h - 5)  # sparse: red still reads from far
    px[lat] = hexrgb(0xffd23b)
    px[4, 4:w - 4] = px[h - 5, 4:w - 4] = hexrgb(0xffd23b); px[4:h - 4, 4] = px[4:h - 4, w - 5] = hexrgb(0xffd23b)
    ov = ((xx + 0.5 - w / 2) / (w * 0.3)) ** 2 + ((yy + 0.5 - h / 2) / (h * 0.17)) ** 2
    px[ov < 1.0] = hexrgb(0xffd23b); px[ov < 0.78] = hexrgb(0xf6f4ee)
    text_px(px, 'JF', w // 2 - 5, h // 2 - 3, 1, 0xc02040)


def face_px(rank, suit):
    def draw(px):
        h, w = px.shape[:2]
        col = 0xe0202a if suit in 'hd' else 0x111111
        px[:] = hexrgb(0xfbfaf6); px[0] = px[-1] = hexrgb(0x9a9a9a); px[:, 0] = px[:, -1] = hexrgb(0x9a9a9a)
        text_px(px, rank, 3, 3, 1, col); glyph(px, SUIT_PX[suit], 3, 12, 1, col)
        glyph(px, SUIT_PX[suit], w // 2 - 7, h // 2 - 7, 2, col)
        flip = np.zeros((h, w, 3), dtype=np.float32); flip[:] = px
        text_px(flip, rank, 3, 3, 1, col); glyph(flip, SUIT_PX[suit], 3, 12, 1, col)
        px[h // 2 + 8:, w // 2 + 4:] = flip[::-1, ::-1][h // 2 + 8:, w // 2 + 4:]  # the corner index, upside down
    return draw


def outline(w, h, r, n=4):
    """rounded rectangle, (x, y) points anticlockwise seen from +z"""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def card(name, w, h, t, r, face_m, back_m, edge_m, flat=False):
    """a card in its own node: the face mesh (+z, uvs 0..1 across it) with the back + edge as a child. flat = lying in the
    xz plane face up, top edge forward (-z), the way the code's thrown card flies"""
    P = outline(w, h, r)
    def to3(x, y, z): return gv(x, z, -y) if flat else gv(x, y, z)  # flat: card y -> game -z, card z (thickness) -> game y
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new()
    vs = [bm.verts.new(to3(x, y, t / 2)) for x, y in P]
    f = bm.faces.new(vs)
    for lp in f.loops:
        x, y = P[vs.index(lp.vert)]
        lp[uvl].uv = (x / w + 0.5, y / h + 0.5)
    bmesh.ops.triangulate(bm, faces=[f])
    fo = _obj(name, bm, face_m)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new()
    vb = [bm.verts.new(to3(x, y, -t / 2)) for x, y in P]
    fb = bm.faces.new(list(reversed(vb)))
    for lp in fb.loops:
        x, y = P[vb.index(lp.vert)]
        lp[uvl].uv = (0.5 - x / w, y / h + 0.5)  # reads the right way round from behind
    bmesh.ops.triangulate(bm, faces=[fb])
    vt = [bm.verts.new(to3(x, y, t / 2)) for x, y in P]
    for i in range(len(P)):
        j = (i + 1) % len(P)
        e = bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
        e.material_index = 1
        for lp in e.loops: lp[uvl].uv = (i / len(P), 0.5)
    me = bpy.data.meshes.new(name + '_back'); bm.to_mesh(me); bm.free()
    me.materials.append(back_m); me.materials.append(edge_m)
    bo = _link(bpy.data.objects.new(name + '_back', me))
    bo.parent = fo
    return fo


def stock():
    edge = mat('cd_edge', 0xe8e4da, rough=0.7)
    back = mat('cd_back', 0xffffff, rough=0.25, clearcoat=0.6, tex=tex_canvas('cd_back_t', 32, 48, back_px))
    return edge, back


def deck():
    edge, back = stock()
    hand = [('A', 's'), ('K', 'h'), ('Q', 'c'), ('J', 'd'), ('10', 'h')]
    cards = []
    for i, (rk, st) in enumerate(hand):
        fm = mat(f'cd_face{i}', 0xffffff, rough=0.3, tex=tex_canvas(f'cd_face{i}_t', 32, 48, face_px(rk, st)))
        c = card(f'card{i}', 0.08, 0.12, 0.0007, 0.0055, fm, back, edge)
        a = (i - 2) * 0.22  # the fan weapons.js lays out (it re-places them every frame)
        c.location = gv(math.sin(a) * 0.09, math.cos(a) * 0.09 - 0.07, -0.002 * i)
        c.rotation_euler = Euler((0, a, 0), 'YZX')  # three rotation.z = -a (game z = blender -y)
        cards.append(c)
    meta = {'kind': 'weapon', 'id': 'cards', 'muzzle': [0, 0.05, -0.1], 'fan': [f'card{i}' for i in range(5)],
            'hatAt': [[0, 0.07, -0.004], 0.07]}
    return finish('w_cards', cards, meta)


def thrown():
    edge, _ = stock()
    # satin, not gloss: a thrown card is seen edge-on and far away, where a clear coat washes the red out
    back = mat('cd_back_thrown', 0xffffff, rough=0.55, clearcoat=0.1, tex=tex_canvas('cd_back_thrown_t', 32, 48, back_px))
    c = card('card', 0.18, 0.26, 0.0015, 0.012, back, back, edge, flat=True)
    return finish('pj_card', [c], {'kind': 'proj', 'id': 'card'})


def game_card(fid, skin, node, front_px, back_draw):
    edge = mat(fid + '_edge', 0xf2f0ea, rough=0.6)
    front = mat(fid + '_front', 0xffffff, rough=0.22, clearcoat=0.8, tex=tex_canvas(fid + '_front_t', 64, 96, front_px))
    back = mat(fid + '_backm', 0xffffff, rough=0.22, clearcoat=0.8, tex=tex_canvas(fid + '_back_t', 64, 96, back_draw))
    c = card(node, 0.12, 0.18, 0.003, 0.009, front, back, edge)
    c.rotation_euler = Euler((-0.2, 0, 0), 'XYZ')  # tilted back like the code's (three rotation.x = -0.2)
    meta = {'kind': 'weapon', 'id': 'reverse', 'muzzle': [0, 0.05, -0.05], 'card': node, 'hatAt': [[0, 0.088, 0.02], 0.07]}
    if skin: meta['skin'] = skin
    return finish(fid, [c], meta)


def oval(px, cx, cy, rx, ry, a, color):
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    u = dx * math.cos(a) + dy * math.sin(a); v = -dx * math.sin(a) + dy * math.cos(a)
    px[(u / rx) ** 2 + (v / ry) ** 2 < 1] = hexrgb(color)


def arrow_loop(px, cx, cy, r, w, color, rot=0.0):
    """two chunky curved arrows chasing each other round a circle (the reverse symbol)"""
    for k in range(2):
        a0 = rot + k * math.pi
        for i in range(40):
            a = a0 + 0.25 + (math.pi - 0.9) * i / 39
            px_disc(px, cx + r * math.cos(a), cy + r * math.sin(a), w / 2, color)
        a = a0 + 0.25 + (math.pi - 0.9)
        tx, ty = cx + r * math.cos(a), cy + r * math.sin(a)
        dx, dy = -math.sin(a), math.cos(a)  # travel direction
        for s in range(int(w * 1.6)):
            hw = w * 1.15 * (1 - s / (w * 1.6))
            for q in np.linspace(-hw, hw, 9):
                x = tx + dx * s + math.cos(a) * q; y = ty + dy * s + math.sin(a) * q
                if 0 <= int(x) < px.shape[1] and 0 <= int(y) < px.shape[0]: px[int(y), int(x)] = hexrgb(color)


def reverse_front(px):  # the game's Reverse Card: red, a white tilted oval, two red arrows chasing round it
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf6f4ee); px[3:h - 3, 3:w - 3] = hexrgb(0xe8262b)
    oval(px, w / 2, h / 2, w * 0.36, h * 0.4, -0.5, 0xf6f4ee)
    arrow_loop(px, w / 2, h / 2, w * 0.2, 6, 0xe8262b, rot=-0.5)
    for (x, y, f) in ((5, 5, 1), (w - 15, h - 15, -1)): arrow_loop(px, x + 5, y + 5, 3, 2, 0xf6f4ee, rot=0.3 if f > 0 else 0.3 + math.pi)
    text_px(px, 'NO U', w // 2 - 11, h - 13, 1, 0xf6f4ee)


def skip_front(px):  # the Skip Card: green, a white panel, a ring with a slash
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf6f4ee); px[3:h - 3, 3:w - 3] = hexrgb(0x2a7a3a)
    oval(px, w / 2, h / 2, w * 0.36, h * 0.4, -0.5, 0xf6f4ee)
    px_disc(px, w / 2, h / 2, w * 0.24, 0x2a7a3a, r_in=w * 0.16)
    px_line(px, w / 2 - w * 0.15, h / 2 + w * 0.15, w / 2 + w * 0.15, h / 2 - w * 0.15, 0x2a7a3a, 6)
    for (x, y) in ((9, 9), (w - 9, h - 9)):
        px_disc(px, x, y, 5, 0xf6f4ee, r_in=3); px_line(px, x - 3, y + 3, x + 3, y - 3, 0xf6f4ee, 2)
    text_px(px, 'NOPE', w // 2 - 11, h - 13, 1, 0xf6f4ee)


def game_back(px):  # black with a pink-yellow swoosh and JANK in the middle
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf6f4ee); px[3:h - 3, 3:w - 3] = hexrgb(0x16121c)
    oval(px, w / 2, h / 2, w * 0.36, h * 0.4, -0.5, 0xff4fd8)
    oval(px, w / 2, h / 2, w * 0.3, h * 0.34, -0.5, 0x16121c)
    text_px(px, 'JANK', w // 2 - 11, h // 2 - 3, 1, 0xffe14d)


main_multi(lambda: [(deck(), 'w_cards'), (thrown(), 'pj_card'), (game_card('w_reverse', None, 'card_wzAB', reverse_front, game_back), 'w_reverse'),
                    (game_card('w_reverse_skip', 'reverse_skip', 'skipcard_wzAB', skip_front, game_back), 'w_reverse_skip')], exposure=-1.0)
