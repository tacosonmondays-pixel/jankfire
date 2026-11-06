# Business Cards (Card Deck skin): a hand of portrait business cards fanned out of a chrome card case. Real business
# card stock (55 x 85 mm, here x1.5 so they sit on the deck's fan: 0.08 x 0.128), bright white with a hot pink CORP
# header, the backs in CORP pink with the smiley; the case is a real 95 x 62 mm slim card case (x1.0), brushed chrome
# with the lid flipped open behind the cards, an engraved CORP plate and EMPLOYEE OF THE MONTH.
# The fan works like the deck's: card0..card4 are the face meshes weapons.js deals your hand onto (inset in the
# business card, under the header), each card's stock / back / edge are its children, so they follow it.
# run: blender -b --python tools/blender/make_cards_business.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
from sidekit import quad, uv_face, smiley, text_c, one_mat, bake_normals

SW, SH, T, R = 0.08, 0.128, 0.0007, 0.004  # card stock
FW, FH = 0.07, 0.1                         # the face the game paints (inset)
OFF = 0.0095                               # stock centre above the face centre (room for the header)
SUIT_PX = {
    's': ['0001000', '0011100', '0111110', '1111111', '1111111', '0101010', '0011100'],
    'h': ['0110110', '1111111', '1111111', '1111111', '0111110', '0011100', '0001000'],
    'd': ['0001000', '0011100', '0111110', '1111111', '0111110', '0011100', '0001000'],
    'c': ['0011100', '0011100', '1101011', '1111111', '1101011', '0001000', '0011100'],
}


def glyph(px, gl, x0, y0, s, color):
    c = hexrgb(color)
    for ry, row in enumerate(gl):
        for rx, b in enumerate(row):
            if b == '1': px[y0 + ry * s:y0 + (ry + 1) * s, x0 + rx * s:x0 + (rx + 1) * s] = c


def face_px(rank, suit):  # what shows until the game deals your hand onto it (the locker, icons)
    def draw(px):
        h, w = px.shape[:2]
        col = 0xe0202a if suit in 'hd' else 0x111111
        px[:] = hexrgb(0xfbfaf6); px[0] = px[-1] = hexrgb(0xd0d0d0); px[:, 0] = px[:, -1] = hexrgb(0xd0d0d0)
        text_px(px, rank, 3, 3, 1, col); glyph(px, SUIT_PX[suit], 3, 12, 1, col)
        glyph(px, SUIT_PX[suit], w // 2 - 7, h // 2 - 7, 2, col)
    return draw


def outline(w, h, r, n=4, cy=0.0):
    pts = []
    for cx, cy_, a0 in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + cy_ + r * math.sin(a)))
    return pts


def slab_face(P, z, m, name, w, h, cy=0.0, flip=False):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(x, y, z)) for x, y in P]
    f = bm.faces.new(list(reversed(vs)) if flip else vs)
    for lp in f.loops:
        x, y = P[vs.index(lp.vert)]
        lp[uvl].uv = ((0.5 - x / w) if flip else (x / w + 0.5), (y - cy) / h + 0.5)
    bmesh.ops.triangulate(bm, faces=[f])
    return _obj(name, bm, m)


def bcard(i, face_m, front_m, back_m, edge_m):
    """card i: the face mesh (node, its own UVs 0..1) + children: the stock's front (header), its back and edge"""
    fo = slab_face(outline(FW, FH, 0.0025), T / 2 + 0.00025, face_m, f'card{i}', FW, FH)
    P = outline(SW, SH, R, cy=OFF)
    fr = slab_face(P, T / 2, front_m, f'card{i}_front', SW, SH, cy=OFF)
    bk = slab_face(P, -T / 2, back_m, f'card{i}_back', SW, SH, cy=OFF, flip=True)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    lo = [bm.verts.new(gv(x, y, -T / 2)) for x, y in P]; hi = [bm.verts.new(gv(x, y, T / 2)) for x, y in P]
    for k in range(len(P)):
        j = (k + 1) % len(P)
        e = bm.faces.new((lo[k], lo[j], hi[j], hi[k]))
        for lp in e.loops: lp[uvl].uv = (0.5, 0.5)
    ed = _obj(f'card{i}_edge', bm, edge_m)
    for c in (fr, bk, ed): c.parent = fo
    return fo


def build():
    edge = mat('bc_edge', 0xf4f2ec, rough=0.7)
    def front_draw(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xfbfaf6)
        px[:15] = hexrgb(0xff4fd8); px[15:17] = hexrgb(0xffe14d)
        smiley(px, 8, 7.5, 5.6)
        text_px(px, 'CORP', 16, 4, 1, 0xffffff)
        px[-3:-2, 6:w - 6] = hexrgb(0xff4fd8)
    front = mat('bc_front', 0xffffff, rough=0.35, clearcoat=0.4, tex=tex_canvas('bc_front_t', 50, 80, front_draw))
    def back_draw(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xff4fd8)
        px[2:h - 2, 2] = px[2:h - 2, w - 3] = hexrgb(0xffe14d); px[2, 2:w - 2] = px[h - 3, 2:w - 2] = hexrgb(0xffe14d)
        smiley(px, w / 2, h * 0.38, 15)
        text_c(px, 'CORP', w / 2, int(h * 0.62), 1, 0xffffff)
        text_c(px, 'WE ARE', w / 2, int(h * 0.75), 1, 0x2a2433)
        text_c(px, 'HAPPY', w / 2, int(h * 0.75) + 9, 1, 0x2a2433)
    back = mat('bc_back', 0xffffff, rough=0.25, clearcoat=0.7, tex=tex_canvas('bc_back_t', 50, 80, back_draw))
    hand = [('A', 's'), ('K', 'h'), ('Q', 'c'), ('J', 'd'), ('10', 'h')]
    cards = []
    for i, (rk, st) in enumerate(hand):
        fm = mat(f'bc_face{i}', 0xffffff, rough=0.3, tex=tex_canvas(f'bc_face{i}_t', 32, 46, face_px(rk, st)))
        c = bcard(i, fm, front, back, edge)
        a = (i - 2) * 0.22  # the fan weapons.js lays out (it re-places them every frame)
        c.location = gv(math.sin(a) * 0.09, math.cos(a) * 0.09 - 0.07, -0.002 * i)
        c.rotation_euler = Euler((0, a, 0), 'YZX')
        cards.append(c)
    # ---------------- the card case: brushed chrome, rounded, held low; the lid flipped open behind the cards
    def brushed_draw(px):
        r = np.random.default_rng(5); h, w = px.shape[:2]
        n = 0.7 * np.repeat(r.random((h, 1)), w, axis=1) + 0.3 * r.random((h, w))
        px[:] = hexrgb(0xc9ced6) * (0.92 + 0.14 * n[:, :, None])
    chrome = mat('bc_chrome', 0xffffff, rough=0.22, metal=1.0, tex=tex_canvas('bc_chrome_t', 32, 32, brushed_draw))
    polish = mat('bc_polish', 0xe2e6ec, rough=0.08, metal=1.0)
    dark = mat('bc_dark', 0x1c1820, rough=0.5)
    def plate_draw(px):
        px[:] = hexrgb(0xd8dce2); px[:1] = px[-1:] = px[:, :1] = px[:, -1:] = hexrgb(0x8a8e96)
        smiley(px, 10, 10.5, 7.5, face=0xd8dce2, ink=0x4a4e56)
        text_px(px, 'CORP', 21, 3, 1, 0x4a4e56)
        text_px(px, 'EMPLOYEE OF', 21, 11, 1, 0x4a4e56)
        text_c(px, 'THE MONTH', 44, 19, 1, 0xd0287a)
    plate = mat('bc_plate', 0xffffff, rough=0.18, metal=0.9, tex=tex_canvas('bc_plate_t', 88, 28, plate_draw))
    CY, CZ = -0.058, 0.0075  # case centre (it sits just in front of the fan's bottom)
    parts = []
    A = parts.append
    A(box((0.098, 0.064, 0.009), (0, CY, CZ), chrome, bev=0.0035, seg=3, name='case'))
    A(box((0.092, 0.003, 0.007), (0, CY + 0.032, CZ - 0.0004), dark, name='mouth'))  # the open top, dark inside
    A(box((0.099, 0.004, 0.0094), (0, CY + 0.029, CZ), polish, bev=0.0012, name='lip'))
    A(box((0.098, 0.064, 0.003), (0, CY - 0.002, -0.0035), chrome, bev=0.0012, rot=(0.1, 0, 0), name='lid'))  # folded right round behind
    A(cyl(0.0025, 0.094, (0, CY + 0.031, 0.001), polish, axis='x', seg=10, name='hinge'))
    pl = quad((0, CY - 0.004, CZ + 0.0047), 0.066, 0.021, plate, axis='z', name='plate')
    parts_n = [pl]

    for p in parts: apply_mods(p); uv_box(p, 0.05)
    one_mat(parts)
    bake_normals(parts)
    body = join(parts, 'bc_case_wzA')
    dn = join(parts_n, 'bc_case_plate_wzN')
    meta = {'kind': 'weapon', 'id': 'cards', 'skin': 'cards_business', 'muzzle': [0, 0.05, -0.1], 'fan': [f'card{i}' for i in range(5)],
            'hatAt': [[0, 0.083, -0.004], 0.07]}
    return finish('w_cards_business', cards + [body, dn], meta)


main(build, 'w_cards_business', exposure=-0.6)
