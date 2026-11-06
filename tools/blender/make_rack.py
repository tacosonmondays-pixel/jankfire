# Pallet rack, the Warehouse kind: a 6 m bay (upright frame at x = 0, orange step beams front and back, wire decks at
# 2.25 / 4.65 / 7.05 m so the tops line up with the map's walkable deck boxes) and a lone end frame. Blue teardrop
# uprights with zig-zag bracing. Nodes 'bay' and 'frame' in one file (the map picks one per placement).
# run: blender -b --python tools/blender/make_rack.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

DEPTH_Z = (-1.1, 1.1)  # upright centres (map uprights: z-1.2..z-1.0 and z+1.0..z+1.2)
H = 7.3
LEVELS = (2.25, 4.65, 7.05)  # deck tops (map decks: lvl + 2 .. lvl + 2.25)


def frame(blue, steel, ox=0):
    P = []
    def holes(px):
        px[:] = hexrgb(0x1f5fd0)
        for y in range(2, 64, 6): px[y:y + 2, 3:5] = hexrgb(0x0a1a40)
    up = mat('rk_upright', 0x1f5fd0, rough=0.3, clearcoat=0.5, tex=tex_canvas('rk_up_t', 8, 64, holes))
    for z in DEPTH_Z:
        P.append(box((0.1, H, 0.09), (ox, H / 2, z), up, bev=0.012))
        P.append(box((0.16, 0.02, 0.16), (ox, 0.01, z), steel))
    n = 8
    for k in range(n):  # zig-zag bracing between the two uprights
        y0, y1 = 0.15 + k * (H - 0.3) / n, 0.15 + (k + 1) * (H - 0.3) / n
        za, zb = (DEPTH_Z[0] + 0.05, DEPTH_Z[1] - 0.05) if k % 2 == 0 else (DEPTH_Z[1] - 0.05, DEPTH_Z[0] + 0.05)
        P.append(tube([(ox, y0, za), (ox, y1, zb)], 0.018, blue, seg=6))
    for y in (0.15, H - 0.15): P.append(box((0.04, 0.04, 2.1), (ox, y, 0), blue))
    return P


def build():
    blue = mat('rk_blue', 0x1f5fd0, rough=0.3, clearcoat=0.5)
    orange = mat('rk_beam', 0xff6a00, rough=0.28, clearcoat=0.6)
    steel = mat('rk_steel', 0x7a7e86, rough=0.35, metal=0.8)
    def grid(px):
        px[:] = hexrgb(0x2a2c30)
        px[::4, :] = hexrgb(0x9aa0aa); px[:, ::4] = hexrgb(0x9aa0aa)
    deck = mat('rk_deck', 0x8a9098, rough=0.4, metal=0.6, tex=tex_canvas('rk_deck_t', 32, 32, grid))
    def warn(px):
        px[:] = hexrgb(0xffe14d); text_px(px, 'MAX 1000KG', 2, 2, 1, 0x111111); text_px(px, 'PROBABLY', 2, 11, 1, 0xe0102a)
    sign = mat('rk_sign', 0xffffff, rough=0.4, tex=tex_canvas('rk_sign_t', 64, 20, warn))
    bay = frame(blue, steel)
    for top in LEVELS:
        if top > H: continue
        for z in (DEPTH_Z[0] - 0.06, DEPTH_Z[1] + 0.06):
            bay.append(box((5.9, 0.14, 0.06), (3.0, top - 0.09, z), orange, bev=0.012))
            for x in (0.07, 5.93): bay.append(box((0.05, 0.22, 0.08), (x, top - 0.09, z), steel))
        bay.append(box((5.8, 0.025, 2.3), (3.0, top - 0.0125, 0), deck))
        for x in (1.0, 2.0, 3.0, 4.0, 5.0): bay.append(box((0.04, 0.05, 2.26), (x, top - 0.05, 0), steel))
    bay.append(box((0.6, 0.18, 0.005), (3.0, LEVELS[0] - 0.09, DEPTH_Z[0] - 0.095), sign, rot=(0, math.pi, 0)))
    for p in bay: uv_box(p, 0.25)
    b = part(bay, 'bay', pivot=(0, 0, 0))
    f = frame(blue, steel, ox=0)
    for p in f: uv_box(p, 0.25)
    fr = part(f, 'frame', pivot=(0, 0, 0))
    fr.location.x += 7.5  # beside the bay in the file (the game resets each variant to its own origin)
    return finish('p_rack', [b, fr], {'kind': 'prop', 'id': 'rack', 'variants': ['bay', 'frame']})


main(build, 'p_rack')
