# THE HOUSE (26 Nov 2026, HOLDOUT's lobby): the furniture and the yard's things, as chunky bevelled pieces in flat
# quiet colours (chunky-model-style: a few big rounded shapes; less-colourful-look: warm whites, greys and woods, colour
# only on the store tables and the trampoline's pad). Each kind is drawn in its own frame (standing on y 0, its front
# toward +z) and placed by M = (where it stands) @ (its quarter turns). hunt_house_models.py calls draw(kind, M).
import math
import arenakit as K
from arenakit import Tr, Ry

# ---------------------------------------------------------------- the palette
OAK, WALNUT, PINE, BIRCH = 'a07752', '6f5240', 'b89a76', 'c9b08e'
WHITE, OFFWHITE, CREAM = 'efece5', 'e2ddd2', 'd8cfbd'
SOFA, SOFA2, CUSHION = '9a948a', '7b7e7f', 'c4baa8'   # (judge round 3: SOFA2 read blue)
DARK, STEEL, CHROME = '3c3f44', 'a9aeb2', 'c7cacc'
APPLIANCE = 'e7e5df'
DUVET, BLANKET, PILLOW = 'e6e2d8', 'a89377', 'f0ece4'
GREEN, GREEN2, BARK = '5f7d4a', '6f8f55', '6e5a46'
SOIL, STONE = '5c4a3c', 'b9b1a3'
SCREEN = '23262b'
TABLE_ACCENT = {'vip': 'c2a052', 'coins': '7d9a84', 'cases': '72859c'}   # the store tables' one colour each (muted)
PAD = 'dad5cb'                                                             # the trampoline's pad (round 5: trim off-white)
KICK, SLATE = '6b6e72', '5a5e64'                                           # kick plates; pedestals, the range (judge round 1: no near-blacks)
CANVAS = 'cbc3b4'
CAB, CABDOOR = 'e4dfd4', 'ede9e0'                                          # (judge round 2: the cabinets paler than the walls)                                                          # the umbrellas (judge round 1: colour stays on the tables' skirts)
M_ = 'hp_furn'

def B(col, x0, y0, z0, x1, y1, z1, M, bev=0.25, kind='plastic', model=M_):
    K.B(model, col, x0, y0, z0, x1, y1, z1, bev=bev, kind=kind, M=M)

def C(col, x, y0, z, r, h, M, segs=20, bev=0.15, r2=None, kind='plastic', model=M_):
    K.cyl(model, col, x, y0, z, r, h, segs=segs, bev=bev, r2=r2, kind=kind, M=M)

def blob(col, x, y, z, r, M, sy=0.8, sx=1.0, sz=1.0, model=M_):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    K.put(model, 'plastic', col, bm, M @ Tr(x, y, z))

def legs4(col, x, z, h, M, t=0.45, inset=0.5):
    for sx in (-1, 1):
        for sz in (-1, 1):
            B(col, sx * x - t / 2 - sx * inset, 0, sz * z - t / 2 - sz * inset, sx * x + t / 2 - sx * inset, h, sz * z + t / 2 - sz * inset, M, bev=0.12)

# ---------------------------------------------------------------- living
def sofa(M, w, col=SOFA):
    hw = w / 2
    for sx in (-1, 1):
        for sz in (-1, 1): B(WALNUT, sx * (hw - 1.0) - 0.35, 0, sz * 2.7 - 0.35, sx * (hw - 1.0) + 0.35, 0.8, sz * 2.7 + 0.35, M, bev=0.12)
    B(col, -hw + 0.5, 0.6, -3.4, hw - 0.5, 2.2, 3.3, M, bev=0.5)                     # the base (inside the arms: no seam)
    for i in range(int(round(w / 6))):                                               # seat cushions
        n = int(round(w / 6)); cw = (w - 2.4) / n
        x0 = -hw + 1.2 + i * cw
        B(col, x0 + 0.1, 2.2, -2.0, x0 + cw - 0.1, 2.9, 3.3, M, bev=0.35)
    B(col, -hw, 0.6, -3.5, hw, 5.5, -1.6, M, bev=0.6)                                # the back
    for sx in (-1, 1):                                                                # the arms
        B(col, sx * hw - (1.3 if sx > 0 else 0), 0.6, -3.5, sx * hw + (0 if sx > 0 else 1.3), 4.0, 3.5, M, bev=0.5)
    for k in range(int(round(w / 6))):                                               # back cushions
        n = int(round(w / 6)); cw = (w - 2.6) / n
        x0 = -hw + 1.3 + k * cw
        B(CUSHION if col == SOFA2 else col, x0 + 0.15, 2.9, -1.9, x0 + cw - 0.15, 5.3, -0.9, M, bev=0.4)

def armchair(M): sofa(M, 7.0, SOFA2)

def sectional(M):
    sofa(M @ Tr(0, 0, -4.5), 22.0)
    B(SOFA, 4, 0.6, -1, 11, 2.2, 8, M, bev=0.5); B(SOFA, 4.1, 2.2, -1, 10.9, 2.9, 7.9, M, bev=0.35)
    B(SOFA, 9.7, 0.6, -1, 11, 4.0, 8, M, bev=0.5)

def coffee(M):
    B(WALNUT, -5, 1.6, -3, 5, 2.2, 3, M, bev=0.2)
    B(WALNUT, -4.5, 0.3, -2.5, 4.5, 0.6, 2.5, M, bev=0.1)
    legs4(WALNUT, 5, 3, 1.6, M, t=0.6, inset=0.6)

def media(M):
    B(WALNUT, -8, 0.4, -1.75, 8, 3.0, 1.75, M, bev=0.2)
    for x in (-5.4, 0, 5.4): B(OAK, x - 2.5, 0.8, 1.62, x + 2.5, 2.6, 1.8, M, bev=0.08)
    B(DARK, -7.6, 0, -1.5, 7.6, 0.4, 1.5, M, bev=0.05)

def tvwall(M):
    B('3a3f46', -6.5, -0.1, -0.3, 6.5, 7.1, 0.55, M, bev=0.3)                           # (judge rounds 2 and 8: a real bezel)
    B('5c6670', -5.4, 0.6, 0.35, 5.4, 6.4, 0.5, M, bev=0.03)                         # (round 5: slate glass)

def bookcase(M, w=8.0, h=12.0):
    hw = w / 2
    B(WHITE, -hw, 0, -1.25, hw, h, -0.9, M, bev=0.1)                                 # the back
    for sx in (-1, 1): B(WHITE, sx * hw - (0.5 if sx > 0 else 0), 0, -1.25, sx * hw + (0 if sx > 0 else 0.5), h, 1.25, M, bev=0.15)
    B(WHITE, -hw, h - 0.6, -1.25, hw, h, 1.35, M, bev=0.15)
    B(WHITE, -hw, 0, -1.25, hw, 0.8, 1.25, M, bev=0.1)
    n = int(h // 2.8)
    pairs = [('8a7a68', 'a99a84'), ('6d7a80', '8e989b'), ('7d6a5c', 'b5a58c'), ('98a09a', '7b8580')]
    yb = 0.8 + (h - 1.4) / n                                                           # closed doors along the bottom
    for sx in (-1, 1): B(OFFWHITE, (0.15 if sx > 0 else -hw + 0.55), 0.9, 1.0, (hw - 0.55 if sx > 0 else -0.15), yb - 0.35, 1.45, M, bev=0.12)
    for i in range(1, n):
        y = 0.8 + i * (h - 1.4) / n
        B(WHITE, -hw + 0.5, y - 0.2, -1.2, hw - 0.5, y, 1.2, M, bev=0.05)
        if i == 1: continue
        ca, cb = pairs[i % len(pairs)]
        x = -hw + 0.8
        g = 0
        while x < hw - 1.6:                                                            # books in groups of 3-5, no titles
            nb = 3 + ((i + g) % 3)
            for b_ in range(nb):
                bw = 0.6 + ((i * 3 + g * 5 + b_ * 7) % 3) * 0.1
                bh = 2.0 + ((i + g * 3 + b_ * 2) % 4) * 0.2
                if x + bw > hw - 0.7: break
                B(ca if b_ % 2 else cb, x, y, -0.8, x + bw, y + bh, 0.6, M, bev=0.06)
                x += bw + 0.05
            g += 1
            if (i + g) % 3 == 0 and x < hw - 2.6:                                         # one big object in the gap
                C('b9b1a3', x + 1.0, y, -0.1, 0.7, 1.6, M, segs=14, bev=0.2, r2=0.5); x += 2.2
            else:
                x += 1.1

def shelfwide(M): bookcase(M, 14.0, 9.0)

def hearth(M):
    # the fireplace (it stands against the west wall; front +z = into the room): a stone hearth, a chunky surround and
    # a mantel shelf, the firebox dark; the TV hangs over it
    B(STONE, -5, 0, -1.0, 5, 0.6, 3.0, M, bev=0.15)
    B(OFFWHITE, -5.5, 0, -2.0, -3.2, 6.2, 0.4, M, bev=0.2); B(OFFWHITE, 3.2, 0, -2.0, 5.5, 6.2, 0.4, M, bev=0.2)
    B(OFFWHITE, -5.5, 4.4, -2.0, 5.5, 6.2, 0.4, M, bev=0.2)
    B(WALNUT, -6.2, 6.2, -2.0, 6.2, 6.8, 0.9, M, bev=0.15)                            # the mantel
    B('5a534d', -3.2, 0.6, -2.0, 3.2, 4.4, -0.2, M, bev=0.05)                         # the firebox (round 4: mid grey)
    B('e07a3a', -2.4, 0.6, -1.7, 2.4, 1.05, -0.4, M, bev=0.15, kind='neon')            # embers (judge round 4: a real glow)
    for sx in (-1, 1): B(OFFWHITE, sx * 3.6 - 0.4, 0, -0.2, sx * 3.6 + 0.4, 4.4, 0.7, M, bev=0.2)   # the surround's chamfered jambs
    for z in (-1.3, -0.5): B(BARK, -2.2, 0.6, z - 0.35, 2.2, 1.3, z + 0.35, M, bev=0.3)   # two logs
    for (x, h) in ((-1.25, 2.2), (0.1, 3.0), (1.35, 2.0)):                                # (rounds 5 and 8) three flame tongues
        K.plate(M_, 'ff9446', [(x - 0.75, 0.0), (x + 0.75, 0.0), (x + 0.1, h)], 0.3, M @ Tr(0, 1.2, -1.0), bev=0.06, kind='neon')

def rug(M, w=24, d=16, col='b4a893', edge='8e8170'):
    B(edge, -w / 2, 0, -d / 2, w / 2, 0.08, d / 2, M, bev=0.03)
    B(col, -w / 2 + 0.8, 0.02, -d / 2 + 0.8, w / 2 - 0.8, 0.1, d / 2 - 0.8, M, bev=0.03)

def rugsmall(M): rug(M, 12, 8, '6f7373', '5d6162')

def lamp(M):
    C(SLATE, 0, 0, 0, 1.3, 0.45, M, bev=0.15)
    C(STEEL, 0, 0.45, 0, 0.3, 6.0, M, segs=12, bev=0.08)
    C(CREAM, 0, 6.4, 0, 1.6, 2.6, M, r2=1.15, bev=0.15)

def plant(M):
    C('c9c3b6', 0, 0, 0, 1.2, 2.4, M, r2=1.0, bev=0.2)
    C(SOIL, 0, 2.2, 0, 1.05, 0.3, M, bev=0.05)
    blob(GREEN, 0, 3.6, 0, 1.6, M, sy=0.9); blob(GREEN2, 0.6, 4.7, 0.3, 1.1, M); blob(GREEN, -0.5, 5.2, -0.3, 0.9, M)

def piano(M):
    B('2e2c2b', -5, 0, -2, 5, 8, 0.4, M, bev=0.3)
    B('2e2c2b', -5, 2.4, 0.4, 5, 4.0, 2.0, M, bev=0.2)
    B(WHITE, -4.6, 4.0, 0.5, 4.6, 4.3, 1.9, M, bev=0.05)
    for i in range(14): B('1d1c1c', -4.4 + i * 0.66, 4.3, 0.6, -4.1 + i * 0.66, 4.45, 1.3, M, bev=0.02) if i % 7 not in (2, 6) else None
    for sx in (-1, 1): B('2e2c2b', sx * 4.6 - 0.4, 0, 0.4, sx * 4.6 + 0.4, 2.4, 1.8, M, bev=0.1)
    B('2e2c2b', -3, 0, 3.2, 3, 2.6, 4.6, M, bev=0.2)                                  # the stool

def pingpong(M):
    B('4d6b5a', -7.5, 3.9, -4.25, 7.5, 4.4, 4.25, M, bev=0.1)
    B(WHITE, -0.08, 4.4, -4.25, 0.08, 4.46, 4.25, M, bev=0.0)                         # the centre line (a stripe in the top)
    B(DARK, -0.15, 4.4, -4.6, 0.15, 5.4, 4.6, M, bev=0.05)                            # the net
    for x in (-6, 6): B(DARK, x - 0.5, 0, -3.5, x + 0.5, 3.9, 3.5, M, bev=0.15)

def beanbag(M):
    blob('8c7f70', 0, 1.4, 0, 2.3, M, sy=0.65); blob('8c7f70', 0, 2.2, -0.9, 1.6, M, sy=0.7)

def toychest(M):
    B(PINE, -3, 0, -1.5, 3, 2.6, 1.5, M, bev=0.3)
    B(BIRCH, -3.1, 2.6, -1.6, 3.1, 3.0, 1.6, M, bev=0.2)
    for sx in (-1, 1): B(DARK, sx * 3.05 - 0.15, 1.6, -0.5, sx * 3.05 + 0.15, 2.0, 0.5, M, bev=0.05)

# ---------------------------------------------------------------- kitchen and dining
def counter(M, w=4.0, top='d9d4ca'):
    hw = w / 2
    B(KICK, -hw, 0, -1.6, hw, 0.6, 1.4, M, bev=0.05)                                    # (full width: the runs read as one)
    B(CAB, -hw, 0.6, -2, hw, 5.0, 1.6, M, bev=0.12)                                    # the cabinet
    B(CABDOOR, -hw + 0.2, 0.9, 1.55, hw - 0.2, 4.7, 1.75, M, bev=0.1)                  # its door
    B(STEEL, -0.6, 3.9, 1.75, 0.6, 4.1, 1.95, M, bev=0.05)                             # the handle
    B(top, -hw, 5.0, -2, hw, 5.4, 2.0, M, bev=0.08)                                    # the worktop

def island(M):
    B(CAB, -7.6, 0.6, -3.1, 7.6, 5.0, 3.1, M, bev=0.15)
    B(KICK, -7.2, 0, -2.8, 7.2, 0.6, 2.8, M, bev=0.05)
    B('d9d4ca', -8, 5.0, -3.5, 8, 5.4, 3.5, M, bev=0.1)
    for sx in (-1, 1): B('d9d4ca', sx * 8 - (0.45 if sx > 0 else 0), 0, -3.5, sx * 8 + (0 if sx > 0 else 0.45), 5.0, 3.5, M, bev=0.08)   # waterfall ends
    for x in (-5, 0, 5):
        B(CABDOOR, x - 2.2, 0.9, -3.25, x + 2.2, 4.7, -3.05, M, bev=0.08)
        B(CABDOOR, x - 2.2, 0.9, 3.05, x + 2.2, 4.7, 3.3, M, bev=0.08)                    # (judge round 3: the stool side too)
    B('d9d4ca', -7.6, 4.2, 3.0, 7.6, 5.0, 3.35, M, bev=0.08)                             # a drawer rail under the top

def stool(M):
    C(WALNUT, 0, 3.4, 0, 1.25, 0.6, M, bev=0.2)                                         # a pedestal stool (judge round 1)
    C('6e747c', 0, 0.3, 0, 0.4, 3.1, M, segs=12, bev=0.08)
    C('6e747c', 0, 0, 0, 1.1, 0.3, M, segs=18, bev=0.1)
    C('6e747c', 0, 1.4, 0, 0.85, 0.18, M, segs=16, bev=0.05)

def fridge(M):
    B(APPLIANCE, -3, 0, -2.5, 3, 12, 2.2, M, bev=0.35)
    B('dcdad3', -2.85, 0.2, 2.2, 2.85, 6.6, 2.5, M, bev=0.15)                          # the lower door (fixed)
    B(STEEL, 2.2, 3.0, 2.5, 2.5, 6.0, 2.75, M, bev=0.05)
    # the upper door is HuntBuild's moving piece (hx_fridgedoor), hung at 6.8..11.8

def stove(M):
    counter(M, 5.0, '2f3135')
    B(SLATE, -2.4, 1.0, 1.7, 2.4, 4.4, 1.9, M, bev=0.08)                               # the oven door
    for (x, z) in ((-1.2, -0.9), (1.2, -0.9), (-1.2, 0.9), (1.2, 0.9)): C('1c1d20', x, 5.4, z, 0.8, 0.1, M, segs=16, bev=0.02)
    B(APPLIANCE, -2.5, 8.6, -2.0, 2.5, 10.4, 0.2, M, bev=0.2)                          # the hood

def sinkunit(M):
    counter(M, 12.0)                                                                    # (12: the back wall's run has no gaps)
    B('aeb3b6', -2.8, 4.6, -1.3, 2.8, 5.45, 1.3, M, bev=0.15)                          # the basin's rim
    B('6d7276', -2.4, 4.4, -1.0, 2.4, 5.42, 1.0, M, bev=0.1)                           # the basin
    C(CHROME, 0, 5.4, -1.6, 0.25, 2.2, M, segs=10, bev=0.05)                           # the tap
    B(CHROME, -0.2, 7.2, -1.7, 0.2, 7.5, -0.6, M, bev=0.08)

def banquette(M):
    # the kitchen's breakfast nook (judge round 1): a built-in bench, its back to the wall, a long cushion
    B(OFFWHITE, -6, 0, -1.5, 6, 2.4, 1.5, M, bev=0.2)
    B(KICK, -5.8, 0, 1.1, 5.8, 0.5, 1.55, M, bev=0.05)
    B(OFFWHITE, -6, 0, -1.5, 6, 6.2, -0.6, M, bev=0.25)
    B(SOFA, -5.8, 2.4, -0.6, 5.8, 3.1, 1.5, M, bev=0.35)
    for x in (-3, 3): B(CUSHION, x - 2.8, 3.1, -0.6, x + 2.8, 5.8, 0.2, M, bev=0.4)
    for sx in (-1, 1): B(OFFWHITE, sx * 6 - (0.6 if sx > 0 else 0), 0, -1.5, sx * 6 + (0 if sx > 0 else 0.6), 4.0, 1.6, M, bev=0.2)

def nooktable(M):
    B(OAK, -5, 4.6, -2.2, 5, 5.3, 2.2, M, bev=0.25)
    for x in (-3, 3):
        C(SLATE, x, 0.3, 0, 0.45, 4.3, M, segs=12, bev=0.08)
        B(SLATE, x - 0.6, 0, -1.8, x + 0.6, 0.4, 1.8, M, bev=0.15)

def pantry(M):
    B(KICK, -2.5, 0, -1.6, 2.5, 0.6, 1.4, M, bev=0.05)
    B(CAB, -2.5, 0.6, -2, 2.5, 12.0, 1.6, M, bev=0.15)
    for (y0, y1) in ((0.9, 6.6), (6.9, 11.7)):
        for sx in (-1, 1): B(CABDOOR, (0.1 if sx > 0 else -2.3), y0, 1.55, (2.3 if sx > 0 else -0.1), y1, 1.75, M, bev=0.1)
    for sx in (-1, 1): B(STEEL, sx * 0.5 - 0.1, 5.4, 1.75, sx * 0.5 + 0.1, 8.0, 1.95, M, bev=0.05)

def diningtable(M):
    B(OAK, -9, 4.6, -4, 9, 5.4, 4, M, bev=0.25)
    for (x, z) in ((-8.1, -3.1), (8.1, -3.1), (-8.1, 3.1), (8.1, 3.1)): B(OAK, x - 0.4, 0, z - 0.4, x + 0.4, 4.6, z + 0.4, M, bev=0.12)
    B(OAK, -7.8, 3.9, -0.3, 7.8, 4.5, 0.3, M, bev=0.08)

CHAIRWOOD = '957f68'   # (judge round 3: oak chairs read mustard under the pendants)
def chair(M):
    B(CHAIRWOOD, -1.4, 2.4, -1.4, 1.4, 2.9, 1.4, M, bev=0.15)
    B('b9ae9c', -1.25, 2.9, -1.2, 1.25, 3.2, 1.25, M, bev=0.12)                        # the seat pad
    for (x, z) in ((-1.1, -1.1), (1.1, -1.1), (-1.1, 1.1), (1.1, 1.1)): B(CHAIRWOOD, x - 0.25, 0, z - 0.25, x + 0.25, 2.4, z + 0.25, M, bev=0.08)
    B(CHAIRWOOD, -1.4, 2.9, -1.4, 1.4, 6.0, -1.0, M, bev=0.18)                               # the back

def sideboard(M):
    B(WALNUT, -7, 0.6, -1.5, 7, 5, 1.5, M, bev=0.2)
    for x in (-4.6, 0, 4.6): B(OAK, x - 2.1, 1.0, 1.42, x + 2.1, 4.6, 1.6, M, bev=0.08)
    for x in (-6.4, 6.4): B(DARK, x - 0.25, 0, -1.2, x + 0.25, 0.6, 1.2, M, bev=0.05)
    C('c6b8a0', -3.5, 5.0, 0, 0.9, 2.2, M, r2=0.6, bev=0.1)                            # a vase
    C('8d9c95', 3.0, 5.0, 0, 0.7, 1.2, M, bev=0.1)

# ---------------------------------------------------------------- bathrooms
def toilet(M):
    B(WHITE, -1.4, 0, -2.5, 1.4, 4.0, -1.3, M, bev=0.35)                               # the cistern
    C(WHITE, 0, 0, 0.3, 1.2, 1.6, M, r2=0.8, segs=18, bev=0.2)
    B(WHITE, -1.4, 1.6, -1.4, 1.4, 2.6, 2.2, M, bev=0.5)                               # the bowl
    B(OFFWHITE, -1.35, 2.6, -1.3, 1.35, 2.8, 2.25, M, bev=0.4)                         # the seat
    B(CHROME, 0.6, 3.6, -1.25, 1.0, 3.8, -1.1, M, bev=0.05)

def basin(M):
    B(WHITE, -2, 3.6, -1.5, 2, 5.0, 1.5, M, bev=0.45)
    C(WHITE, 0, 0, -0.6, 0.6, 3.6, M, r2=0.45, segs=14, bev=0.1)
    C(CHROME, 0, 5.0, -1.1, 0.2, 1.0, M, segs=10, bev=0.05)

def vanity(M):
    B(WALNUT, -5, 0.4, -2, 5, 4.4, 1.8, M, bev=0.2)
    for x in (-2.4, 2.4): B(OAK, x - 2.2, 0.8, 1.75, x + 2.2, 4.1, 1.95, M, bev=0.08)
    B(WHITE, -5, 4.4, -2, 5, 5.0, 2.0, M, bev=0.12)
    for x in (-2.4, 2.4):
        B('d6d8d8', x - 1.6, 4.6, -1.2, x + 1.6, 5.05, 1.2, M, bev=0.2)
        C(CHROME, x, 5.0, -1.6, 0.18, 1.0, M, segs=10, bev=0.05)
    B('c9d2d6', -4.6, 6.2, -2.0, 4.6, 11.0, -1.8, M, bev=0.15)                         # the mirror (flat, no picture)
    B(WHITE, -4.9, 6.0, -2.0, 4.9, 6.2, -1.7, M, bev=0.05)

def bathtub(M):
    B(WHITE, -3.5, 0, -7.5, 3.5, 3.6, 7.5, M, bev=0.5)
    B('dfe2e2', -2.7, 1.2, -6.7, 2.7, 3.65, 6.7, M, bev=0.6)                           # the inside
    C(CHROME, 0, 3.6, -7.0, 0.2, 1.2, M, segs=10, bev=0.05)

def shower(M):
    B('c9d6da', -4, 0, -4, 4, 12, -3.6, M, bev=0.05, kind='glass')

# ---------------------------------------------------------------- bedrooms
def bed(M, w, l, head=9.0, frame=WALNUT, duvet=DUVET):
    hw, hl = w / 2, l / 2
    for (x, z) in ((-hw + 0.5, -hl + 0.5), (hw - 0.5, -hl + 0.5), (-hw + 0.5, hl - 0.5), (hw - 0.5, hl - 0.5)):
        B(frame, x - 0.45, 0, z - 0.45, x + 0.45, 3.4, z + 0.45, M, bev=0.12)
    B(frame, -hw, 2.6, -hl, hw, 3.4, hl, M, bev=0.25)                                  # the frame (clear underneath)
    B('ece8de', -hw + 0.3, 3.4, -hl + 0.3, hw - 0.3, 4.4, hl - 0.3, M, bev=0.4)        # the mattress
    B(duvet, -hw + 0.1, 4.0, -hl + 3.6, hw - 0.1, 4.9, hl - 0.05, M, bev=0.45)         # the duvet
    B(BLANKET, -hw, 4.6, hl - 4.5, hw, 5.0, hl + 0.05, M, bev=0.3)                     # the throw at its foot
    for k in range(int(w // 5) or 1):                                                  # pillows
        n = int(w // 5) or 1; pw = (w - 1.6) / n
        x0 = -hw + 0.8 + k * pw
        B(PILLOW, x0 + 0.1, 4.3, -hl + 0.8, x0 + pw - 0.1, 5.4, -hl + 3.2, M, bev=0.45)
    B(frame, -hw - 0.3, 0, -hl - 0.6, hw + 0.3, head, -hl, M, bev=0.35)                 # the headboard
    B(SOFA, -hw + 0.4, 4.6, -hl - 0.05, hw - 0.4, head - 0.8, -hl + 0.3, M, bev=0.35)   # its padded panel

def bedking(M): bed(M, 14, 17)
def beddouble(M): bed(M, 11, 15, 8.0, OAK, 'dcd8cc')

def bunk(M):
    for (x, z) in ((-3.6, -7.1), (3.6, -7.1), (-3.6, 7.1), (3.6, 7.1)): B(PINE, x - 0.4, 0, z - 0.4, x + 0.4, 12, z + 0.4, M, bev=0.15)
    for y in (3.4, 8.6):
        B(PINE, -4, y, -7.5, 4, y + 1.0, 7.5, M, bev=0.2)
        B('ece8de', -3.6, y + 1.0, -7.1, 3.6, y + 1.7, 7.1, M, bev=0.3)
        B('8aa0a8' if y < 5 else 'b9a07e', -3.7, y + 1.4, -4.0, 3.7, y + 2.1, 7.15, M, bev=0.35)
        B(PILLOW, -3, y + 1.6, -6.8, 3, y + 2.5, -4.6, M, bev=0.35)
    B(PINE, -4, 10.6, -7.5, 4, 11.4, -7.0, M, bev=0.1); B(PINE, -4, 10.6, 7.0, 4, 11.4, 7.5, M, bev=0.1)
    B(PINE, 3.6, 10.6, -7.1, 4.0, 11.4, 2.0, M, bev=0.1)                               # the top bunk's rail
    for y in (1.5, 3.5, 5.5, 7.5, 9.5): B(PINE, 3.7, y, 3.4, 4.2, y + 0.35, 6.8, M, bev=0.08)   # the ladder's rungs

def nightstand(M):
    B(WALNUT, -1.75, 0, -1.5, 1.75, 3.2, 1.5, M, bev=0.2)
    B(OAK, -1.5, 1.6, 1.4, 1.5, 3.0, 1.6, M, bev=0.08)
    C(CREAM, 0.4, 3.2, -0.3, 0.6, 0.3, M, bev=0.05); C(STEEL, 0.4, 3.5, -0.3, 0.1, 1.2, M, segs=8, bev=0.02)
    C(CREAM, 0.4, 4.6, -0.3, 0.9, 1.2, M, r2=0.6, bev=0.08)

def dresser(M):
    B(OAK, -5, 0.4, -1.75, 5, 5, 1.75, M, bev=0.2)
    for y in (1.0, 2.4, 3.8):
        for x in (-2.45, 2.45): B(BIRCH, x - 2.3, y, 1.7, x + 2.3, y + 1.2, 1.9, M, bev=0.08)
    for x in (-4.6, 4.6): B(DARK, x - 0.3, 0, -1.5, x + 0.3, 0.4, 1.5, M, bev=0.05)

def wardrobe(M):
    B(WHITE, -4, 0, -2, 4, 11, 2, M, bev=0.25)
    for x in (-2, 2): B(OFFWHITE, x - 1.85, 0.4, 1.95, x + 1.85, 10.6, 2.15, M, bev=0.1)
    for x in (-0.4, 0.4): B(STEEL, x - 0.1, 4.6, 2.15, x + 0.1, 6.6, 2.35, M, bev=0.04)

def desk(M):
    B(OAK, -6, 4.0, -3, 6, 4.6, 3, M, bev=0.2)
    for x in (-5.5, 5.5): B(WHITE, x - 0.5, 0, -2.8, x + 0.5, 4.0, 2.8, M, bev=0.15)
    B(WHITE, 2.0, 0.4, -2.8, 5.0, 4.0, 2.6, M, bev=0.15)                               # the drawers
    B(DARK, -2.2, 4.6, -2.4, 2.2, 7.6, -2.1, M, bev=0.12)                              # a screen
    B('2f3236', -1.9, 4.9, -2.12, 1.9, 7.3, -2.05, M, bev=0.02)
    B(DARK, -0.3, 4.6, -2.6, 0.3, 5.2, -2.0, M, bev=0.05)

def officechair(M):
    C(DARK, 0, 0, 0, 1.4, 0.35, M, segs=10, bev=0.1)
    C(STEEL, 0, 0.35, 0, 0.2, 2.2, M, segs=8, bev=0.05)
    B('4b5157', -1.4, 2.5, -1.4, 1.4, 3.1, 1.4, M, bev=0.3)
    B('4b5157', -1.3, 3.1, -1.6, 1.3, 6.0, -1.1, M, bev=0.35)

def filing(M):
    B('9aa0a6', -1.5, 0, -2, 1.5, 5, 2, M, bev=0.15)
    for y in (0.4, 2.6): B('aeb4b9', -1.3, y, 1.95, 1.3, y + 2.0, 2.1, M, bev=0.06)

def shoeisland(M):
    B(WHITE, -4, 0, -2.5, 4, 3.6, 2.5, M, bev=0.2); B(OAK, -4.2, 3.6, -2.7, 4.2, 4.0, 2.7, M, bev=0.15)

def rail(M):
    for x in (-5.8, 5.8): B(STEEL, x - 0.15, 0, -0.15, x + 0.15, 9, 0.15, M, bev=0.03)
    B(STEEL, -5.8, 8.45, -0.12, 5.8, 8.75, 0.12, M, bev=0.03)
    cols = ['8a8f96', 'b0a089', '6f7d74', 'c2b7a4', '7d6f66', '9aa3ab']
    for i in range(9):
        x = -4.8 + i * 1.2
        B(cols[i % len(cols)], x - 0.45, 3.6 + (i % 3) * 0.6, -1.0, x + 0.45, 8.4, 1.0, M, bev=0.25)

def pooltable(M):
    B('4f6e5f', -6.4, 4.4, -3.4, 6.4, 5.0, 3.4, M, bev=0.1)                            # the cloth
    B(WALNUT, -7, 3.2, -4, 7, 5.3, -3.4, M, bev=0.2); B(WALNUT, -7, 3.2, 3.4, 7, 5.3, 4, M, bev=0.2)
    B(WALNUT, -7, 3.2, -4, -6.4, 5.3, 4, M, bev=0.2); B(WALNUT, 6.4, 3.2, -4, 7, 5.3, 4, M, bev=0.2)
    B(WALNUT, -6, 0, -3, 6, 3.2, 3, M, bev=0.4)
    for (x, z, c) in ((-2, 0.5, 'e8e4da'), (2.5, -1, 'c8643c'), (3.2, 0.6, '3c5a8c'), (1.8, 1.4, 'd0a23c')):
        K.sphere(M_, c, 0, 0, 0, 0.35, 12, 8) if False else C(c, x, 5.0, z, 0.35, 0.6, M, segs=12, bev=0.25)

def console(M):
    B(DARK, -1.2, 3.0, -0.8, 1.2, 3.6, 0.8, M, bev=0.15)

def bench(M):
    B(OAK, -4, 2.4, -1.25, 4, 3.0, 1.25, M, bev=0.2)
    for x in (-3.4, 3.4): B(OAK, x - 0.35, 0, -1.0, x + 0.35, 2.4, 1.0, M, bev=0.1)
    B(OAK, -3.4, 0.6, -1.0, 3.4, 0.9, 1.0, M, bev=0.08)

def coatrack(M):
    B(WALNUT, -3, 5.2, -0.45, 3, 6.0, 0.15, M, bev=0.12)
    for x in (-2.2, -0.75, 0.75, 2.2): B(STEEL, x - 0.15, 5.4, 0.15, x + 0.15, 5.7, 0.7, M, bev=0.05)
    for (x, c) in ((-2.2, '6f7a80'), (0.75, 'a08a6a')): B(c, x - 1.0, 1.6, 0.2, x + 1.0, 5.6, 1.2, M, bev=0.45)

def washer(M):
    B(APPLIANCE, -2.5, 0, -2.5, 2.5, 5.5, 2.5, M, bev=0.3)
    C('c9ccce', 0, 2.6, 2.45, 1.6, 0.2, M, segs=20, bev=0.08) if False else None
    K.cylz(M_, 'c9ccce', 0, 0, 0, 0, 1.0) if False else None
    B('c9ccce', -1.6, 1.0, 2.45, 1.6, 4.2, 2.6, M, bev=0.6)
    B('3f4246', -1.1, 1.5, 2.55, 1.1, 3.7, 2.65, M, bev=0.4)

# ---------------------------------------------------------------- the garage
def car(M):
    # (27 Nov, the vehicles pass: the web game's hatchback in flat colours with blank plates, fitted to this footprint;
    # the hit boxes are unchanged. The old rounded-block car is car_blocks, one line away)
    import vehicle_port as VP
    VP.hunt_car(M_, M)

def car_blocks(M):
    BODY = '7c8790'
    B(BODY, -4.5, 0.9, -10, 4.5, 4.2, 10, M, bev=1.1)                                 # the body
    B(BODY, -4.0, 4.0, -5.0, 4.0, 7.0, 4.0, M, bev=1.2)                               # the cabin
    B('3a4048', -3.7, 4.4, -5.2, 3.7, 6.6, 4.2, M, bev=1.0)                           # the glass band (dark)
    for (x, z) in ((-4.0, -6.2), (4.0, -6.2), (-4.0, 6.4), (4.0, 6.4)):
        K.cylx(M_, '25272a', x - 0.8, x + 0.8, 1.7, z, 1.7) if False else None
        B('25272a', x - 0.85, 0, z - 1.7, x + 0.85, 3.4, z + 1.7, M, bev=1.0)          # the tyres (rounded blocks)
    B('d9d4c8', -3.6, 2.4, 9.85, -2.0, 3.2, 10.1, M, bev=0.2); B('d9d4c8', 2.0, 2.4, 9.85, 3.6, 3.2, 10.1, M, bev=0.2)
    B('a8454a', -3.6, 2.6, -10.1, -2.0, 3.2, -9.85, M, bev=0.2); B('a8454a', 2.0, 2.6, -10.1, 3.6, 3.2, -9.85, M, bev=0.2)

def workbench(M):
    B(OAK, -7, 4.6, -2, 7, 5.4, 2, M, bev=0.2)
    for x in (-6.4, 6.4): B('7a7f84', x - 0.4, 0, -1.6, x + 0.4, 4.6, 1.6, M, bev=0.1)
    B('7a7f84', -6.4, 1.0, -1.6, 6.4, 1.4, 1.6, M, bev=0.05)
    B('9aa0a6', -6.8, 5.4, -2.0, 6.8, 11.0, -1.7, M, bev=0.1)                          # the pegboard
    B('b85c3c', -4, 5.4, -1.2, -1.6, 6.6, 0.6, M, bev=0.25)                            # a toolbox
    B(DARK, 1.5, 5.4, -0.8, 3.5, 6.0, 0.8, M, bev=0.15)

def shelving(M):
    for (x, z) in ((-5.8, -1.3), (5.8, -1.3), (-5.8, 1.3), (5.8, 1.3)): B('7a7f84', x - 0.2, 0, z - 0.2, x + 0.2, 11, z + 0.2, M, bev=0.05)
    for y in (0.5, 3.8, 7.1, 10.4):
        B('8e9499', -6, y, -1.5, 6, y + 0.3, 1.5, M, bev=0.05)
    for (x, y, c) in ((-3.5, 0.8, 'b09a78'), (0.5, 0.8, '8d9c95'), (3.8, 4.1, 'b09a78'), (-2, 4.1, '9aa3ab'), (2, 7.4, 'a28d6e'), (-4, 7.4, '7a868e')):
        B(c, x - 1.6, y, -1.2, x + 1.6, y + 2.4, 1.2, M, bev=0.2)

def freezer(M):
    B(APPLIANCE, -4, 0, -2.25, 4, 4.6, 2.25, M, bev=0.35); B('dcdad3', -4.05, 4.6, -2.3, 4.05, 5.0, 2.3, M, bev=0.25)

def bikes(M):
    for (x, c) in ((-2.2, '5d7a8c'), (2.2, '8c6a5d')):
        for z in (-2.6, 2.6): K.ring(M_, DARK, 0, 0, 0, 0, 1.1, 1.4) if False else B(DARK, x - 0.2, 0, z - 1.4, x + 0.2, 2.8, z + 1.4, M, bev=0.5)
        B(c, x - 0.15, 1.3, -2.4, x + 0.15, 2.0, 2.4, M, bev=0.08); B(c, x - 0.15, 1.3, -0.4, x + 0.15, 3.4, 0.2, M, bev=0.08)
        B(DARK, x - 0.3, 3.4, -0.7, x + 0.3, 3.7, 0.5, M, bev=0.1)

def golfbag(M):
    C('3f5a4c', 0, 0, 0, 1.0, 4.0, M, segs=14, bev=0.2)
    for (x, z) in ((-0.4, -0.3), (0.3, -0.4), (0.0, 0.4)):
        B(STEEL, x - 0.08, 4.0, z - 0.08, x + 0.08, 5.4, z + 0.08, M, bev=0.02); B(DARK, x - 0.3, 5.2, z - 0.2, x + 0.3, 5.7, z + 0.3, M, bev=0.12)

def bins(M):
    for x in (-1.8, 1.8):
        B('4f5d55', x - 1.6, 0, -1.6, x + 1.6, 4.6, 1.6, M, bev=0.35); B('44514a', x - 1.75, 4.6, -1.75, x + 1.75, 5.0, 1.75, M, bev=0.2)

# ---------------------------------------------------------------- the patio and the garden
def storetable(M, tab='vip'):
    # (owner, 27 Nov: "Outside the new items aren't there it's just game passes for standard mode and coins for Robux")
    # plain tables now: HOUSE HUNT's own items stand on them (HuntProps.tables, the intro kit's hiT_ pieces); the shop's
    # crown, coins and case are gone (the shop stays in the menu)
    acc = '8a6f50'
    tab = 'items'
    B(OAK, -5, 4.6, -2.5, 5, 5.2, 2.5, M, bev=0.2)
    for x in (-4.4, 4.4): B(OAK, x - 0.35, 0, -2.0, x + 0.35, 4.6, 2.0, M, bev=0.1)
    B(OAK, -4.9, 1.2, 2.2, 4.9, 4.6, 2.45, M, bev=0.08)                                # the skirt
    B(OAK, -4.9, 1.2, -2.45, 4.9, 4.6, -2.2, M, bev=0.08)
    B(acc, -4.95, 3.7, 2.35, 4.95, 4.5, 2.6, M, bev=0.08)                              # its one colour: a band (judge round 1)
    B(acc, -4.95, 3.7, -2.6, 4.95, 4.5, -2.35, M, bev=0.08)
    if tab == 'vip':
        B('7c6a4c', -1.6, 5.2, -1.2, 1.6, 6.0, 1.2, M, bev=0.25)
        C(acc, 0, 6.0, 0, 1.0, 0.5, M, segs=16, bev=0.15)
        for k in range(5):
            a = k * 2 * math.pi / 5
            B(acc, math.cos(a) * 0.8 - 0.18, 6.5, math.sin(a) * 0.8 - 0.18, math.cos(a) * 0.8 + 0.18, 7.2, math.sin(a) * 0.8 + 0.18, M, bev=0.08)
    elif tab == 'coins':
        for (x, z, n) in ((-1.6, 0, 5), (0.4, -0.6, 3), (1.8, 0.6, 7)):
            for i in range(n): C('c7a64e', x, 5.2 + i * 0.32, z, 0.75, 0.3, M, segs=16, bev=0.08)
    elif tab == 'cases':
        B('8a6f50', -1.8, 5.2, -1.4, 1.8, 7.8, 1.4, M, bev=0.3)
        B('5f6468', -1.9, 6.3, -1.5, 1.9, 6.7, 1.5, M, bev=0.1)
        B(acc, -0.4, 6.0, 1.35, 0.4, 7.0, 1.55, M, bev=0.1)

def umbrella(M, tab='vip'):
    acc = CANVAS
    C(WHITE, 0, 0, 0, 0.3, 10.2, M, segs=10, bev=0.08)
    C(STONE, 0, 0, 0, 1.2, 0.5, M, segs=16, bev=0.15)
    K.lathe(M_, acc, [(0.0, 11.2), (1.5, 10.9), (6.0, 9.2), (6.0, 8.9), (0.0, 8.9)], 0, 0, 0) if False else None
    import bmesh
    bm = bmesh.new()
    prof = [(0.25, 11.25), (1.4, 11.0), (6.0, 9.3), (6.05, 8.95)]
    segs = 8
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * i / segs), h, r * math.sin(2 * math.pi * i / segs))) for i in range(segs)] for r, h in prof]
    top = bm.verts.new((0, 11.4, 0))
    for i in range(segs): bm.faces.new((top, rings[0][(i + 1) % segs], rings[0][i]))
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bot = bm.verts.new((0, 8.95, 0))
    for i in range(segs): bm.faces.new((bot, rings[-1][i], rings[-1][(i + 1) % segs]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    K.put(M_, 'plastic', acc, bm, M)

def grill(M):
    B('46484c', -3, 2.6, -1.75, 3, 4.6, 1.75, M, bev=0.4)
    B('3e4044', -3, 4.6, -1.75, 3, 5.8, 1.75, M, bev=0.7)
    for x in (-2.6, 2.6): B(STEEL, x - 0.2, 0, -1.4, x + 0.2, 2.6, 1.4, M, bev=0.05)
    B(STEEL, -2.6, 0.8, -1.4, 2.6, 1.0, 1.4, M, bev=0.03)
    B(OAK, 3, 3.8, -1.5, 5, 4.1, 1.5, M, bev=0.1)

def patiotable(M):
    C('e6dccb', 0, 3.6, 0, 3.0, 0.7, M, segs=24, bev=0.3)                              # (round 6: chunky)
    C('e6dccb', 0, 0, 0, 0.8, 3.6, M, segs=14, bev=0.15)
    C('d8cebd', 0, 0, 0, 1.8, 0.5, M, segs=18, bev=0.2)

def patiochair(M):
    B('e6dccb', -1.5, 0, -1.5, 1.5, 2.6, 1.5, M, bev=0.5)                               # (round 6: a tub chair, not a bistro chair)
    B('e6dccb', -1.5, 2.6, -1.5, 1.5, 4.6, -0.7, M, bev=0.4)
    B(CUSHION, -1.2, 2.6, -0.8, 1.2, 3.0, 1.3, M, bev=0.2)

def lounger(M):
    B(WHITE, -2, 1.4, -5, 2, 1.8, 3, M, bev=0.2)
    B(CUSHION, -1.8, 1.8, -4.8, 1.8, 2.3, 2.8, M, bev=0.3)
    B(CUSHION, -1.8, 1.8, 2.6, 1.8, 2.6, 5.0, M, bev=0.3) if False else None
    B(WHITE, -2, 1.4, 3, 2, 4.4, 4.6, M, bev=0.3)
    for (x, z) in ((-1.7, -4.6), (1.7, -4.6), (-1.7, 4.0), (1.7, 4.0)): B(WHITE, x - 0.2, 0, z - 0.2, x + 0.2, 1.4, z + 0.2, M, bev=0.05)

def trampoline(M):
    # the frame (a steel ring on six legs), the padded ring in its one colour, the dark mat. HuntBuild's invisible mat
    # part carries the Trampoline attribute
    r = 13.0
    K.ring(M_, STEEL, 0, 2.0, 2.45, 0, r - 0.2, r + 0.4, segs=48) if False else None
    import bmesh
    def ring_(col, r0, r1, y0, y1, segs=48):
        bm = bmesh.new()
        vs = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            ca, sa = math.cos(a), math.sin(a)
            vs.append([bm.verts.new((rr * ca, yy, rr * sa)) for (rr, yy) in ((r0, y0), (r1, y0), (r1, y1), (r0, y1))])
        for k in range(segs):
            a_, b_ = vs[k], vs[(k + 1) % segs]
            for j in range(4): bm.faces.new((a_[j], a_[(j + 1) % 4], b_[(j + 1) % 4], b_[j]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        K.put(M_, 'plastic', col, bm, M)
    ring_(STEEL, r - 0.3, r + 0.3, 1.9, 2.5)
    ring_(PAD, r - 3.2, r + 0.5, 2.5, 3.2)                                              # the pad over the springs
    C('5a6068', 0, 2.2, 0, r - 3.0, 0.4, M, segs=48, bev=0.1)                           # the mat (round 6: slate)
    ring_('dad5cb', r - 0.4, r + 0.3, 0.0, 1.9)                                         # (round 6: a solid skirt, no thin legs)


def tree(M):
    C(BARK, 0, 0, 0, 2.2, 15, M, segs=12, r2=1.5, bev=0.3)
    for (x, y, z, r, sy) in ((0, 13.0, 0, 3.2, 0.8),):
        C(BARK, 0, 12, 0, 1.5, 4, M, segs=10, r2=1.0, bev=0.2)
    for (x, y, z, r, c) in ((0, 21, 0, 11, GREEN), (6.5, 18, 3.5, 7.5, GREEN2), (-6.5, 18.5, -2.5, 8, GREEN2), (2.5, 26.5, -2.0, 7.5, GREEN),
                            (-3, 17, 6, 6.5, GREEN), (4, 17.5, -6.5, 6.5, GREEN)):
        blob(c, x, y, z, r, M, sy=0.78)

def treebench(M):
    import bmesh
    for k in range(6):
        a = k * math.pi / 3
        Mr = M @ Ry(a)
        B(OAK, -2.2, 2.4, 3.2, 2.2, 2.9, 5.6, Mr, bev=0.15)
        B(OAK, -0.3, 0, 4.1, 0.3, 2.4, 4.7, Mr, bev=0.08)

def shed(M):
    W_ = '8d9a8f'
    for (x0, x1, z0, z1) in ((-11, 11, -8, -7), (-11, -3, 7, 8), (3, 11, 7, 8), (-11, -10, -8, 8), (10, 11, -8, 8)):
        B(W_, x0, 0, z0, x1, 10, z1, M, bev=0.1)
    B(WHITE, -3.6, 0, 7.6, -3.0, 8.4, 8.4, M, bev=0.1); B(WHITE, 3.0, 0, 7.6, 3.6, 8.4, 8.4, M, bev=0.1)
    B(WHITE, -3.6, 8.0, 7.6, 3.6, 8.6, 8.4, M, bev=0.1)
    for sz in (-1, 1):                                                                  # a gable roof along x (judge round 1: its ridge was
        Mr = M @ Tr(0, 10 + 8.0 * math.tan(math.radians(24)), 0) @ K.Rx(sz * math.radians(24))   # under the wall tops, unseen)
        B('6a6e74', -12, -0.3, 0 if sz > 0 else -9.8, 12, 0.3, 9.8 if sz > 0 else 0, Mr, bev=0.1)
    for sx in (-1, 1):                                                                  # the gable ends
        K.plate(M_, W_, [(-8.0, 10.0), (8.0, 10.0), (0.0, 13.4)], 1.0, M @ Tr(sx * 11.0 + (1.0 if sx < 0 else 0.0), 0, 0) @ Ry(-math.pi / 2), bev=0.05)
    B(WHITE, -11.2, 10, -8.2, 11.2, 10.6, 8.2, M, bev=0.1)
    B(W_, -10.6, 10.5, -0.4, 10.6, 14.0, 0.4, M, bev=0.1) if False else None
    B('b9d2d8', 4.5, 4.5, 7.95, 8.5, 7.5, 8.15, M, bev=0.05, kind='glass')            # a window by the door
    B(WHITE, 4.3, 4.3, 7.9, 8.7, 4.6, 8.3, M, bev=0.05)
    B('6f5f4e', -9.5, 0, -6.5, -4, 5.4, -4.5, M, bev=0.2)                              # a potting bench inside
    golfbag(M @ Tr(8.5, 0, -6.0))

def firepit(M):
    # the lawn's middle (judge round 1: big things in the big garden): a stone ring with logs, four chunky benches round it
    import bmesh
    segs = 28
    bm = bmesh.new()
    vs = []
    for k in range(segs):
        a = 2 * math.pi * k / segs
        ca, sa = math.cos(a), math.sin(a)
        vs.append([bm.verts.new((rr * ca, yy, rr * sa)) for (rr, yy) in ((2.4, 0.0), (3.6, 0.0), (3.6, 1.5), (2.4, 1.5))])
    for k in range(segs):
        a_, b_ = vs[k], vs[(k + 1) % segs]
        for j in range(4): bm.faces.new((a_[j], a_[(j + 1) % 4], b_[(j + 1) % 4], b_[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    K.put(M_, 'plastic', 'a59d90', bm, M)
    C('4a4744', 0, 0, 0, 2.45, 0.5, M, segs=24, bev=0.05)
    for k in range(3):
        Mr = M @ Ry(k * math.pi / 3)
        B(BARK, -1.8, 0.5, -0.35, 1.8, 1.2, 0.35, Mr, bev=0.3)
    for (x0, z0, x1, z1) in ((-9.6, -9.6, -2.6, -7.8), (2.6, -9.6, 9.6, -7.8), (-9.6, 7.8, -2.6, 9.6), (2.6, 7.8, 9.6, 9.6),
                             (-9.6, -7.8, -7.8, 7.8), (7.8, -7.8, 9.6, 7.8)):             # seat walls, ways in front and back
        B(STONE, x0, 0, z0, x1, 1.8, z1, M, bev=0.3)
        B('8d7c6b', x0 - 0.15, 1.8, z0 - 0.15, x1 + 0.15, 2.4, z1 + 0.15, M, bev=0.25)

def deck(M):
    # the raised deck the fire court stands on (judge round 2: the garden had no centre and no height), two steps
    # toward the house on +z
    B('9c8a78', -12, 0, -12, 12, 1.5, 12, M, bev=0.2)                                 # (judge round 4: not orange)
    B(STONE, -12.2, 0, -12.2, 12.2, 1.0, 12.2, M, bev=0.15)
    for x in (-12, 12): B(WHITE, x - 0.6, 0, -12.6, x + 0.6, 1.7, 12.6, M, bev=0.2) if False else None
    B('9c8a78', -3, 0, 12, 3, 1.0, 13.5, M, bev=0.15)
    B('9c8a78', -3, 0, 13.5, 3, 0.5, 15.0, M, bev=0.15)

def lamppost(M):
    # the front walk's lamp posts (judge round 2)
    B(WHITE, -0.75, 0, -0.75, 0.75, 6.2, 0.75, M, bev=0.2)                                # (judge round 4: 1.5-stud posts)
    B(STONE, -1.25, 0, -1.25, 1.25, 1.0, 1.25, M, bev=0.25)
    B(DARK, -1.15, 6.2, -1.15, 1.15, 6.6, 1.15, M, bev=0.12)
    B('f3e9d6', -0.95, 6.6, -0.95, 0.95, 8.4, 0.95, M, bev=0.2, kind='neon')
    B(DARK, -1.3, 8.4, -1.3, 1.3, 9.0, 1.3, M, bev=0.25)

def playhouse(M):
    # a kids' cabin on a deck (judge round 1): a door you can walk through, a window each side, a gable roof
    WALLC, ROOFC = 'd9d4c6', '6a6e74'
    B(OAK, -7, 0, -6, 7, 0.8, 7.2, M, bev=0.2)                                          # the deck (its front a porch)
    for (x0, x1, z0, z1) in ((-6, 6, -5, -4.2), (-6, -5.2, -5, 5), (5.2, 6, -5, 5), (-6, -1.8, 4.2, 5), (1.8, 6, 4.2, 5)):
        B(WALLC, x0, 0.8, z0, x1, 8.8, z1, M, bev=0.15)
    B(WALLC, -1.8, 6.8, 4.2, 1.8, 8.8, 5, M, bev=0.15)                                  # over the door
    for (x0, x1) in ((-2.4, -1.8), (1.8, 2.4)): B(WHITE, x0, 0.8, 4.9, x1, 7.2, 5.3, M, bev=0.1)
    B(WHITE, -2.4, 6.8, 4.9, 2.4, 7.4, 5.3, M, bev=0.1)
    for sx in (-1, 1):                                                                  # windows: grey glass on the side walls, white sills
        xo = sx * 6.0
        B('7d8792', min(xo, xo + sx * 0.12), 3.6, -2.0, max(xo, xo + sx * 0.12), 6.4, 2.0, M, bev=0.04)
        B(WHITE, min(xo, xo + sx * 0.4), 3.2, -2.4, max(xo, xo + sx * 0.4), 3.6, 2.4, M, bev=0.1)
        B(WHITE, min(xo, xo + sx * 0.3), 6.4, -2.4, max(xo, xo + sx * 0.3), 6.8, 2.4, M, bev=0.1)
    for sz in (-1, 1):                                                                  # a gable roof along x (ridge 11.69: Rx(+a) takes +z down)
        Mr = M @ Tr(0, 8.8 + 5.0 * math.tan(math.radians(30)), 0) @ K.Rx(sz * math.radians(30))
        B(ROOFC, -7.2, -0.35, 0 if sz > 0 else -6.6, 7.2, 0.35, 6.6 if sz > 0 else 0, Mr, bev=0.15)
    for sx in (-1, 1):                                                                  # the gable ends
        K.plate(M_, WALLC, [(-5.0, 8.8), (5.0, 8.8), (0.0, 11.6)], 0.8, M @ Tr(sx * 5.6 + 0.4, 0, 0) @ Ry(-math.pi / 2), bev=0.05)
    for x in (-6.4, 6.4): B(WHITE, x - 0.45, 0.8, 6.3, x + 0.45, 8.6, 7.1, M, bev=0.12)   # porch posts

def flowerbed(M):
    B(WALNUT, -10, 0, -2, 10, 1.2, 2, M, bev=0.15)
    B(SOIL, -9.6, 1.0, -1.6, 9.6, 1.4, 1.6, M, bev=0.1)
    for i in range(6):
        x = -8 + i * 3.2
        blob(GREEN if i % 2 else GREEN2, x, 2.4, 0, 1.6, M, sy=0.8)
        if i % 2 == 0: blob('c7b9a6', x + 0.8, 3.6, 0.3, 0.5, M, sy=0.9)

def hedge(M):
    B('5a7444', -10, 0, -2, 10, 4.4, 2, M, bev=0.9)
    B('5e7948', -9.7, 3.6, -1.7, 9.7, 4.9, 1.7, M, bev=0.6)

def hedgetall(M):
    # (judge round 3) the side fences' screen: a tall rounded box hedge, the front hedges' family
    B('56703f', -10, 0, -2.2, 10, 7.4, 2.2, M, bev=1.1)
    B('5c7745', -9.6, 6.2, -1.8, 9.6, 8.2, 1.8, M, bev=0.8)

def playfort(M):
    # (judge round 3: height in the garden) a raised fort: a deck 5.8 up on four posts, half walls, a gable roof, a
    # stair down its front (+z, toward the house) and a slide off its east side (+x)
    POST, DECKC, WALLC, ROOFC, SLIDEC = 'b7a083', 'a08870', 'd9d4c6', '6a6e74', '8a949c'
    for (x, z) in ((-4.3, -4.3), (4.3, -4.3), (-4.3, 4.3), (4.3, 4.3)):
        B(POST, x - 0.75, 0, z - 0.75, x + 0.75, 12.4, z + 0.75, M, bev=0.25)
    B(DECKC, -5.4, 5.0, -5.4, 5.4, 5.8, 5.4, M, bev=0.2)                                # the deck
    B(POST, -5.0, 4.3, -5.0, 5.0, 5.0, 5.0, M, bev=0.15)                                # its joists' band
    B(WALLC, -5.0, 5.8, -5.0, 5.0, 8.6, -4.3, M, bev=0.2)                               # the half walls (back, sides)
    B(WALLC, -5.0, 5.8, -5.0, -4.3, 8.6, 5.0, M, bev=0.2)
    B(WALLC, 4.3, 5.8, -5.0, 5.0, 8.6, 0.4, M, bev=0.2)                                 # (east: the slide's gap at z 0.4..3.6)
    B(WALLC, 4.3, 5.8, 3.6, 5.0, 8.6, 5.0, M, bev=0.2)
    for (x0, x1) in ((-5.0, -1.9), (1.9, 5.0)): B(WALLC, x0, 5.8, 4.3, x1, 8.6, 5.0, M, bev=0.2)   # front, the stair's gap
    for (x0, z0, x1, z1) in ((-5.2, -5.2, 5.2, -4.1), (-5.2, -5.2, -4.1, 5.2), (4.1, -5.2, 5.2, 0.4), (4.1, 3.6, 5.2, 5.2),
                             (-5.2, 4.1, -1.9, 5.2), (1.9, 4.1, 5.2, 5.2)):
        B('f2efe8', x0, 8.6, z0, x1, 9.0, z1, M, bev=0.15)                               # the walls' white caps
    for k in range(5):                                                                  # the stair: five chunky steps
        y = 5.8 * (k + 1) / 6.0
        z = 5.4 + (4 - k) * 1.5
        B(DECKC, -1.8, 0, z, 1.8, y, z + 1.5, M, bev=0.15)
    for sz in (-1, 1):                                                                  # the gable roof along x (Rx(+a): +z down)
        Mr = M @ Tr(0, 12.4 + 6.2 * math.tan(math.radians(28)), 0) @ K.Rx(sz * math.radians(28))
        B(ROOFC, -6.4, -0.4, 0 if sz > 0 else -7.0, 6.4, 0.4, 7.0 if sz > 0 else 0, Mr, bev=0.2)
    for sx in (-1, 1):                                                                  # the gable ends
        K.plate(M_, WALLC, [(-5.0, 12.4), (5.0, 12.4), (0.0, 12.4 + 5.0 * math.tan(math.radians(28)))], 0.6,
                M @ Tr(sx * 4.6 + 0.3, 0, 0) @ Ry(-math.pi / 2), bev=0.05)
    # the slide: a tilted chute from the deck's east gap down to the lawn, with rails
    ang = math.atan2(5.8 - 0.6, 8.0)
    Ms = M @ Tr(5.0, 5.8, 2.0) @ K.Rz(-ang)
    ln = math.hypot(8.0, 5.2)
    B(SLIDEC, 0, -0.35, -1.5, ln, 0.0, 1.5, Ms, bev=0.15)
    for sz in (-1, 1): B(SLIDEC, 0, -0.35, sz * 1.5 - (0.35 if sz > 0 else 0), ln, 1.1, sz * 1.5 + (0 if sz > 0 else 0.35), Ms, bev=0.15)
    B(POST, 12.2, 0, 0.6, 13.6, 0.6, 3.4, M, bev=0.15)                                  # its foot

def hedge42(M):
    # (judge round 4) one piece each side of the front walk: no seam
    B('5a7444', -21, 0, -2, 21, 4.4, 2, M, bev=0.9)
    B('5e7948', -20.7, 3.6, -1.7, 20.7, 4.9, 1.7, M, bev=0.6)

def mailbox(M):
    B(WHITE, -0.4, 0, -0.4, 0.4, 3.6, 0.4, M, bev=0.1)
    B('4f5d55', -0.8, 3.6, -1.2, 0.8, 5.0, 1.2, M, bev=0.5)

def hoop(M):
    # over the garage door, on the wall: a backboard on a bracket, the rim and a chunky net
    B(STEEL, -0.4, 12.5, -0.2, 0.4, 13.3, 2.2, M, bev=0.1)
    B(WHITE, -3, 13, 2.0, 3, 17, 2.4, M, bev=0.2)
    B(DARK, -1.0, 13.8, 2.4, 1.0, 14.0, 2.5, M, bev=0.02)
    import bmesh
    K.ring(M_, 'b8643a', 0, 13.6, 13.9, 0, 1.3, 1.55, segs=24) if False else None
    bm = bmesh.new()
    segs = 24
    vs = []
    for k in range(segs):
        a = 2 * math.pi * k / segs
        vs.append([bm.verts.new((rr * math.cos(a), yy, rr * math.sin(a))) for (rr, yy) in ((1.3, 13.6), (1.55, 13.6), (1.55, 13.9), (1.3, 13.9))])
    for k in range(segs):
        a_, b_ = vs[k], vs[(k + 1) % segs]
        for j in range(4): bm.faces.new((a_[j], a_[(j + 1) % 4], b_[(j + 1) % 4], b_[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    K.put(M_, 'plastic', 'b8643a', bm, M @ Tr(0, 0, 3.9))
    C('e6e3da', 0, 11.6, 3.9, 1.0, 2.0, M, segs=16, r2=1.4, bev=0.05)

def hose(M):
    B('4f6e5f', -1.2, 0, -0.6, 1.2, 0.4, 0.6, M, bev=0.1)
    C('4f6e5f', 0, 0.4, 0, 1.3, 1.6, M, segs=18, bev=0.25)

def swingset(M):
    # two A-frames (a pair of legs each end, splayed), the top beam, two swings hung on chunky ropes
    for x in (-9.9, 9.9):
        for s in (-1, 1):
            K.B(M_, 'b7a083', -0.75, 0, -0.75, 0.75, 13.0, 0.75, bev=0.25, M=M @ Tr(x, 0, s * 3.6) @ K.Rx(-s * math.radians(16)))
        K.B(M_, 'b7a083', x - 0.55, 4.0, -2.8, x + 0.55, 5.0, 2.8, bev=0.15, M=M)
    K.B(M_, '9e8a70', -11.2, 12.0, -0.85, 11.2, 13.7, 0.85, bev=0.3, M=M)
    for sx in (-4.0, 4.0):
        for dz in (-0.9, 0.9): K.B(M_, DARK, sx - 1.1 - 0.1, 2.9, dz - 0.1, sx - 1.1 + 0.1, 12.3, dz + 0.1, bev=0.03, M=M) if False else None
        for dx in (-1.1, 1.1): K.B(M_, '9e8a70', sx + dx - 0.35, 2.9, -0.35, sx + dx + 0.35, 12.0, 0.35, bev=0.1, M=M)
        K.B(M_, '5d6f63', sx - 1.6, 2.3, -0.9, sx + 1.6, 3.0, 0.9, bev=0.25, M=M)

def pergola(x0, x1, z0, z1, top):
    # (not a FURN kind: hunt_house_models.py draws it from the layout's PERGOLA)
    I = K.I4
    for px in (x0, (x0 + x1) / 2, x1):
        for pz in (z0, z1):
            K.B('hh_yard', 'e9e4da', px - 1.1, 0.0, pz - 1.1, px + 1.1, top - 1.8, pz + 1.1, bev=0.25)
            K.B('hh_yard', 'e9e4da', px - 1.5, 0.0, pz - 1.5, px + 1.5, 0.9, pz + 1.5, bev=0.25)
    for pz in (z0, z1):
        K.B('hh_yard', 'b7a083', x0 - 2.2, top - 1.9, pz - 0.85, x1 + 2.2, top - 0.2, pz + 0.85, bev=0.3)
    x = x0 - 1.0
    while x <= x1 + 1.0:
        K.B('hh_yard', 'a89274', x - 0.8, top - 0.6, z0 - 2.2, x + 0.8, top + 1.4, z1 + 2.2, bev=0.3)
        x += 6.4                                                                        # (judge round 2: fewer, deeper)

# ---------------------------------------------------------------- the table of kinds
DRAW = {
    'sofa3': lambda M: sofa(M, 18.0), 'sofa2': lambda M: sofa(M, 12.0, SOFA2), 'sectional': sectional, 'armchair': armchair,
    'coffee': coffee, 'media': media, 'tvwall': tvwall, 'bookcase': bookcase, 'shelfwide': shelfwide, 'hearth': hearth,
    'rug': rug, 'rugsmall': rugsmall, 'lamp': lamp, 'plant': plant, 'piano': piano, 'pingpong': pingpong, 'beanbag': beanbag,
    'toychest': toychest, 'counter': counter, 'island': island, 'stool': stool, 'fridge': fridge, 'stove': stove,
    'sinkunit': sinkunit, 'diningtable': diningtable, 'chair': chair, 'sideboard': sideboard, 'toilet': toilet, 'basin': basin,
    'vanity': vanity, 'bathtub': bathtub, 'shower': shower, 'bedking': bedking, 'beddouble': beddouble, 'bunk': bunk,
    'nightstand': nightstand, 'dresser': dresser, 'wardrobe': wardrobe, 'desk': desk, 'officechair': officechair,
    'filing': filing, 'shoeisland': shoeisland, 'rail': rail, 'pooltable': pooltable, 'console': console, 'bench': bench,
    'coatrack': coatrack, 'car': car, 'workbench': workbench, 'shelving': shelving, 'freezer': freezer, 'washer': washer,
    'bikes': bikes, 'golfbag': golfbag, 'grill': grill, 'patiotable': patiotable, 'patiochair': patiochair,
    'lounger': lounger, 'trampoline': trampoline, 'tree': tree, 'treebench': treebench, 'shed': shed,
    'flowerbed': flowerbed, 'hedge': hedge, 'mailbox': mailbox, 'hoop': hoop, 'hose': hose, 'bins': bins,
    'swingset': swingset, 'banquette': banquette, 'nooktable': nooktable, 'pantry': pantry, 'firepit': firepit,
    'playhouse': playhouse, 'deck': deck, 'lamppost': lamppost, 'hedgetall': hedgetall, 'playfort': playfort, 'hedge42': hedge42,
}

def draw(kind, cx, y, cz, turn, tab=None):
    M = Tr(cx, y, cz) @ Ry(turn * math.pi / 2)
    if kind == 'storetable': storetable(M, tab); return
    if kind == 'umbrella': umbrella(M, tab); return
    fn = DRAW.get(kind)
    if fn: fn(M)
    else: print('NO DRAWING FOR', kind)
