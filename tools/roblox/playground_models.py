# THE PLAYGROUND KIT (structure pass, 15 Nov 2026): the secret movement course gets a design of its own. it was a set of
# gridded test blocks on a bright sky; it becomes a floodlit yard at dusk: concrete pylons, decks with a lit amber edge,
# grapple pods hung on cables from light masts. every piece is made to FIT one of the course's blocks (the block stays
# the collision, so pads, hooks and jumps are what they were). chunky style, the serious pass's palette.
# 1 unit = 1 stud, Z up. decks, the stone and the pod are centred on their block's middle (z -8..8); the rest stand on z 0.
#   pg_shaft      one 16 x 16 x 16 length of pylon (stretched in Studio to a block's height, and to 32 wide)
#   pg_collar     the band round a pylon, 17.6 x 17.6 x 2.4
#   pg_footing    a pylon's foot, 22 x 22 x 6
#   pg_deckA..G   a deck 16 thick: A 64x64, B 64x48, C 48x48, D 48x32, E 64x32, F 64x16, G 32x48
#   pg_stone      a stepping stone, 16 x 16 x 16
#   pg_pod        a grapple pod, 16 x 16 x 16, with its cable clamp on top (to z 10.4)
#   pg_masthead   the lamp head on a light mast, 18.6 x 18.6 x 25 (stands on the mast's top)
#   pg_chevron    a painted arrow for a deck, 9 x 7 x 0.12, pointing -Y
#   pg_gantry     a sign gantry, 26 x 2.4 x 15: two posts and a lit beam (the sign hangs in it)
# run: blender -b --factory-startup -P tools/roblox/playground_models.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *
from structkit import _emit

CONC, PALE, MIDC, RIB, GRAPH, DARK = '8b8d93', 'a9abaf', '7d8088', '6a6e77', '4d515a', '34363d'
TOP, AMBERGLOW, AMBER, WARM = '5c6068', 'f0c468', 'd6a738', 'f2dcc0'
reset()

# ------------------------------------------------------------------ pg_shaft (16 cube, no caps: it is stacked and stretched)
soft('concrete', CONC, 16.0, 16.0, 16.0, 0, 0, 8.0, 1.6, pick='up', segs=3, small=0.0)
for a in range(4):
    M = RZ(a * math.pi / 2)
    for sx in (-4.6, 4.6): soft('concrete', CONC, 2.4, 1.0, 16.0, sx, -8.0, 8.0, 0.35, pick='up', segs=2, small=0.0, M=M)
    bx('plastic', RIB, 5.6, 0.3, 16.0, 0, -8.0, 8.0, 0.0, M=M)
keep('pg_shaft')

# ------------------------------------------------------------------ pg_collar / pg_footing
soft('plastic', PALE, 17.6, 17.6, 2.4, 0, 0, 1.2, 2.0, pick='up', segs=3, small=0.25)
keep('pg_collar')
soft('concrete', MIDC, 22.0, 22.0, 4.0, 0, 0, 2.0, 2.4, pick='up', segs=3, small=0.3)
soft('plastic', PALE, 19.0, 19.0, 2.0, 0, 0, 5.0, 2.0, pick='up', segs=3, small=0.25)
keep('pg_footing')

# ------------------------------------------------------------------ decks
def deck(w, d, taper=0.0, body_top=4.7):
    soft('plastic', PALE, w, d, 2.0, 0, 0, 7.0, 2.0, pick='up', segs=3, small=0.18)             # the top plate
    bx('plastic', TOP, w - 4.0, d - 4.0, 0.1, 0, 0, 7.98, 0.0)                                 # its dark tread
    bx('plastic', DARK, w - 1.6, d - 1.6, 1.3, 0, 0, 5.35, 0.0)                                # the shadow gap under it
    bx('neon', AMBERGLOW, w - 1.1, d - 1.1, 0.6, 0, 0, 5.6, 0.08)                            # the lit edge in the gap
    soft('concrete', MIDC, w - 0.7, d - 0.7, body_top + 5.0, 0, 0, (body_top - 5.0) / 2, 1.6, pick='up', segs=3, small=0.2)
    soft('concrete', RIB, w - 3.4 - taper, d - 3.4 - taper, 3.0, 0, 0, -6.5, 1.2, pick='up', segs=2, small=0.3)

for name, (w, d) in (('A', (64, 64)), ('B', (64, 48)), ('C', (48, 48)), ('D', (48, 32)), ('E', (64, 32)), ('F', (64, 16)), ('G', (32, 48))):
    deck(w, d)
    keep('pg_deck' + name)

# ------------------------------------------------------------------ pg_stone: a deck in small, its body leaning in
soft('plastic', PALE, 16.0, 16.0, 2.0, 0, 0, 7.0, 2.0, pick='up', segs=3, small=0.18)
bx('plastic', TOP, 12.0, 12.0, 0.1, 0, 0, 7.98, 0.0)
bx('plastic', DARK, 14.4, 14.4, 1.3, 0, 0, 5.35, 0.0)
bx('neon', AMBERGLOW, 14.9, 14.9, 0.6, 0, 0, 5.6, 0.08)
R = 15.3 / math.sqrt(2)
lathe('concrete', MIDC, [(R * 0.86, -8.0), (R * 0.92, -6.5), (R, -2.0), (R, 4.7)], RZ(math.pi / 4), segs=4, bevel=0.5)
keep('pg_stone')

# ------------------------------------------------------------------ pg_pod: the thing you grapple
soft('plastic', GRAPH, 15.6, 15.6, 15.6, 0, 0, 0, 2.6, pick='all', segs=3, small=0.0)
soft('neon', AMBERGLOW, 16.0, 16.0, 1.0, 0, 0, 0, 2.7, pick='up', segs=3, small=0.0)
for a in range(4):
    M = RZ(a * math.pi / 2)
    for zz in (-4.3, 4.3):
        cy('plastic', PALE, 2.6, 0.5, 0, -7.75, zz, axis='y', segs=20, bevel=0.1, M=M)
        cy('plastic', GRAPH, 1.7, 0.56, 0, -7.76, zz, axis='y', segs=20, bevel=0.04, M=M)
cy('plastic', PALE, 4.4, 0.5, 0, 0, -7.75, segs=24, bevel=0.1)
cy('plastic', GRAPH, 3.2, 0.56, 0, 0, -7.76, segs=24, bevel=0.04)
cy('plastic', PALE, 2.6, 1.4, 0, 0, 8.3, segs=16, bevel=0.2)
cy('plastic', GRAPH, 1.5, 1.6, 0, 0, 9.6, segs=12, bevel=0.2)
keep('pg_pod')

# ------------------------------------------------------------------ pg_masthead: the floodlight on a mast's top
soft('plastic', PALE, 17.6, 17.6, 2.4, 0, 0, 1.2, 2.0, pick='up', segs=3, small=0.25)
soft('plastic', GRAPH, 17.0, 17.0, 9.0, 0, 0, 6.9, 2.0, pick='up', segs=3, small=0.25)
for a in range(4):
    M = RZ(a * math.pi / 2)
    soft('neon', WARM, 11.0, 0.5, 5.4, 0, -8.42, 6.9, 0.2, pick='y', segs=2, small=0.0, M=M)
    bx('plastic', DARK, 12.2, 0.4, 6.6, 0, -8.36, 6.9, 0.1, M=M)
soft('plastic', PALE, 18.6, 18.6, 1.4, 0, 0, 12.1, 2.2, pick='up', segs=3, small=0.25)
cy('plastic', GRAPH, 0.8, 10.0, 0, 0, 17.8, segs=10, bevel=0.1)
cy('plastic', PALE, 1.5, 0.6, 0, 0, 13.1, segs=12, bevel=0.15)
ball('neon', AMBERGLOW, 1.3, 0, 0, 23.6)
keep('pg_masthead')

# ------------------------------------------------------------------ pg_chevron: paint on a deck, pointing -Y
pts = [(-4.5, 1.0), (0.0, -3.5), (4.5, 1.0), (4.5, 3.5), (0.0, -1.0), (-4.5, 3.5)]
bm = bmesh.new()
lo_ = [bm.verts.new((u, v, 0.0)) for u, v in pts]
hi_ = [bm.verts.new((u, v, 0.12)) for u, v in pts]
bm.faces.new(hi_); bm.faces.new(lo_[::-1])
for i in range(6):
    j = (i + 1) % 6
    bm.faces.new((lo_[i], lo_[j], hi_[j], hi_[i]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
_emit('plastic_' + AMBER, bm, I4)
keep('pg_chevron')

# ------------------------------------------------------------------ pg_gantry: two posts and a lit beam, 26 wide, 15 tall
for sx in (-12.0, 12.0):
    soft('plastic', GRAPH, 2.0, 2.0, 13.4, sx, 0, 6.7, 0.5, pick='up', segs=2, small=0.15)
    soft('plastic', PALE, 2.8, 2.8, 0.8, sx, 0, 0.4, 0.6, pick='up', segs=2, small=0.15)
soft('plastic', GRAPH, 26.0, 2.4, 1.8, 0, 0, 14.1, 0.5, pick='x', segs=2, small=0.15)
bx('neon', WARM, 22.0, 1.6, 0.25, 0, 0, 13.15, 0.05)
keep('pg_gantry')

export_all('playground.glb')
argv = sys.argv[sys.argv.index('--') + 1:]
if len(argv) > 2: MODELS[:] = [m for m in MODELS if m[0] in argv[2].split(',')]
if len(argv) > 1: preview(argv[1], cols=6, gap=8.0)
