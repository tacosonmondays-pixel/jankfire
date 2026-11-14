# the HUB kit for Roblox in the chunky style (see chunky.py): big simple shapes with rounded edges that drop into the
# places of the hub's older thin pieces (the size of each old piece is in the comment; the swap is done in Studio by
# studio-tools/HubReskin). 1 unit = 1 stud, Z up, the front faces -Y, the floor at z 0.
#   hb_pier      a wall pier for the rotunda, 48 tall, its back flat on the wall      (old pilaster 3 x 48 x 2)
#   hb_portal    a door surround, the same both sides                                 (old portal 17.2 x 19.8 x 2.9)
#   hb_rail      9.5 of balcony rail                                                  (old railing 9.5 x 3.4 x 0.3)
#   hb_ring      the eight-sided balcony edge: a deep beam with lamps under it        (old ring 56 x 1 x 56)
#   hb_screen    a thick bezel for a 22 x 11 screen, the same both sides              (old frame 24.6 x 14.7 x 1.3)
#   hb_hangsign  a housing and two posts for a 13 x 3.6 hanging sign                  (old sign 14 x 9.6 x 1.2)
#   hb_arch      a rib across the pad corridor with two hanging light panels          (old arch 68 x 36 x 2.4)
#   hb_rib       a rib for a hallway with a light bar under it                        (old rib 16 x 20 x 1.6)
#   hb_panel     a round ceiling light                                                (old downlight 1.9 across)
#   hb_droplight a hanging lamp: shade, rod and ceiling cup are separate pieces so the rod can be any length
#   hb_bar       a hanging light bar                                                  (old bar 10 x 2.2 x 1.4)
#   hb_walllight a wall lamp                                                          (old sconce 1.2 x 1.6 x 1.4)
#   hb_slab      a two-tone wall panel                                                (old panel 7 x 6 x 0.5)
#   hb_vending   a vending machine                                                    (old one 3.6 x 6 x 2.8)
# run: blender -b --factory-startup -P tools/roblox/hub_models.py -- <out_dir>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chunky import *
from chunky import _emit, _bevel

PALE, MID, LENS, WARM = 'a4aab8', '5b6478', 'f4f8ff', 'fff1d6'

def octring(kind, hexc, a_in, a_out, z0, z1, bevel=0.2):
    """an eight-sided ring (flats facing the axes), from apothem a_in to a_out"""
    bm = bmesh.new()
    k = 1 / math.cos(math.pi / 8)
    def loop(a, z):
        return [bm.verts.new((a * k * math.sin(math.radians(22.5 + 45 * i)), a * k * math.cos(math.radians(22.5 + 45 * i)), z)) for i in range(8)]
    ob, ot, ib, it = loop(a_out, z0), loop(a_out, z1), loop(a_in, z0), loop(a_in, z1)
    for i in range(8):
        j = (i + 1) % 8
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, Matrix.Identity(4))

def slot(x, y, z, h, w=1.0, face=-1):
    """a light slot on a face looking along Y: a dark housing and a white lens"""
    box('plastic', DARK, w + 1.0, 0.36, h + 1.4, x, y, z, bevel=0.12)
    box('neon', LENS, w, 0.36, h, x, y + face * 0.1, z, bevel=0.1)

# ------------------------------------------------------------------ hb_pier (the wall is at y +1.6)
reset()
box('plastic', DARK, 6.2, 3.6, 3.0, 0, -0.2, 1.5, bevel=0.5)
box('plastic', PALE, 4.2, 3.2, 42.4, 0, 0, 24.0, bevel=0.6)
box('plastic', MID, 5.4, 3.5, 1.3, 0, -0.15, 18.7, bevel=0.3)          # a corbel under the balcony
box('plastic', MID, 5.6, 3.5, 2.8, 0, -0.15, 46.6, bevel=0.6)          # the head
slot(0, -1.6, 10.5, 8.6)
slot(0, -1.6, 32.5, 8.6)
flush('hb_pier')

# ------------------------------------------------------------------ hb_portal (opening 14.2 x 16.9)
reset()
for s in (-1, 1):
    box('plastic', PALE, 1.7, 3.2, 17.2, s * 7.95, 0, 8.6, bevel=0.45)
    box('plastic', DARK, 2.3, 3.6, 1.0, s * 7.95, 0, 0.5, bevel=0.3)
    box('plastic', PINK, 12.0, 0.2, 0.55, 0, s * 1.62, 18.3, bevel=0.08)   # the room's colour, both faces
box('plastic', PALE, 17.6, 3.2, 2.7, 0, 0, 18.25, bevel=0.6)
box('plastic', DARK, 9.6, 2.0, 0.4, 0, 0, 16.86, bevel=0.14)             # a light bar under the head
box('neon', LENS, 8.6, 1.2, 0.2, 0, 0, 16.68, bevel=0.06)
flush('hb_portal')

# ------------------------------------------------------------------ hb_rail (stands on z 0, runs along X)
reset()
for x in (-4.3, 0, 4.3): box('plastic', DARK, 0.6, 0.6, 3.1, x, 0, 1.55, bevel=0.14)
box('plastic', 'c4c8d4', 9.5, 0.8, 0.7, 0, 0, 3.05, bevel=0.24)
box('plastic', MID, 9.0, 0.3, 1.7, 0, 0, 1.45, bevel=0.1)
box('plastic', INK, 9.5, 0.4, 0.45, 0, 0, 0.23, bevel=0.08)
flush('hb_rail')

# ------------------------------------------------------------------ hb_ring (its top is z 0: the balcony floor level)
reset()
octring('plastic', PALE, 22.8, 25.2, -2.6, 0.0, bevel=0.4)                # the deep edge beam you see from below
octring('plastic', DARK, 25.2, 28.0, -1.0, 0.0, bevel=0.15)               # the thin slab behind it
octring('plastic', PINK, 22.72, 22.9, -1.5, -1.1, bevel=0)                # one bold line round the inner face
for i in range(8):
    a = math.radians(45 * i)
    r = Matrix.Rotation(-a, 4, 'Z')
    box('plastic', DARK, 9.0, 1.5, 0.3, 24.0 * math.sin(a), 24.0 * math.cos(a), -2.66, bevel=0.1, rot=r)
    box('neon', LENS, 8.0, 0.9, 0.2, 24.0 * math.sin(a), 24.0 * math.cos(a), -2.78, bevel=0.06, rot=r)
flush('hb_ring')

# ------------------------------------------------------------------ hb_screen (the screen is 22 x 11, centred, z 2.1 .. 13.3)
reset()
box('plastic', DARK, 25.4, 1.6, 2.1, 0, 0, 14.35, bevel=0.5)
box('plastic', DARK, 25.4, 1.6, 2.1, 0, 0, 1.05, bevel=0.5)
for s in (-1, 1):
    box('plastic', DARK, 1.6, 1.6, 11.3, s * 11.9, 0, 7.7, bevel=0.3)
    box('neon', CYAN, 0.8, 0.2, 0.3, 10.2, s * 0.78, 1.0, bevel=0.06)
    box('plastic', PINK, 2.4, 0.2, 0.5, -10.0, s * 0.78, 1.0, bevel=0.08)
flush('hb_screen')

# ------------------------------------------------------------------ hb_hangsign (the sign board is 13 x 3.6, centred on z 2.4)
reset()
box('plastic', DARK, 14.4, 1.3, 0.7, 0, 0, 4.55, bevel=0.22)
box('plastic', DARK, 14.4, 1.3, 0.7, 0, 0, 0.35, bevel=0.22)
for s in (-1, 1):
    box('plastic', DARK, 0.7, 1.3, 3.6, s * 6.85, 0, 2.45, bevel=0.2)
    box('plastic', MID, 0.7, 0.7, 4.8, s * 4.6, 0, 7.2, bevel=0.2)          # posts up to the ceiling
    box('plastic', DARK, 1.6, 1.6, 0.4, s * 4.6, 0, 9.4, bevel=0.14)
flush('hb_hangsign')

# ------------------------------------------------------------------ hb_arch (68 wide, 36 tall)
reset()
for s in (-1, 1):
    box('plastic', PALE, 3.6, 3.6, 32.6, s * 32.2, 0, 16.3, bevel=0.6)
    box('plastic', DARK, 4.6, 4.4, 2.6, s * 31.9, 0, 1.3, bevel=0.45)
    box('plastic', MID, 3.4, 3.4, 3.4, s * 29.3, 0, 31.6, bevel=0.35, rot=RY(math.pi / 4))
    for f in (-1, 1): slot(s * 32.2, f * 1.8, 11.0, 8.0, face=f)
    # a hanging light panel over each side of the walkway
    for dx in (-4, 4): box('plastic', DARK, 0.6, 0.6, 1.5, s * 12 + dx, 0, 31.75, bevel=0.1)
    box('plastic', DARK, 12.4, 4.4, 1.0, s * 12, 0, 30.65, bevel=0.32)
    box('neon', LENS, 10.8, 3.0, 0.3, s * 12, 0, 30.14, bevel=0.1)
box('plastic', PALE, 68, 3.6, 3.6, 0, 0, 34.2, bevel=0.6)
flush('hb_arch')

# ------------------------------------------------------------------ hb_rib (16 wide, 20 tall, opening 13.4 x 17.6)
reset()
for s in (-1, 1):
    box('plastic', PALE, 1.3, 3.0, 17.8, s * 7.35, 0, 8.9, bevel=0.4)
    box('plastic', DARK, 1.7, 3.4, 0.9, s * 7.35, 0, 0.45, bevel=0.25)
    box('plastic', MID, 1.5, 2.8, 1.5, s * 6.3, 0, 17.2, bevel=0.2, rot=RY(math.pi / 4))
box('plastic', PALE, 16, 3.0, 2.4, 0, 0, 18.8, bevel=0.5)
box('plastic', DARK, 9.0, 2.0, 0.4, 0, 0, 17.42, bevel=0.14)
box('neon', LENS, 8.0, 1.2, 0.2, 0, 0, 17.24, bevel=0.06)
flush('hb_rib')

# ------------------------------------------------------------------ hb_panel (hangs from z 0)
reset()
cyl('plastic', DARK, 1.6, 0.7, 0, 0, -0.35, segs=20, bevel=0.2)
cyl('neon', 'fff4e0', 1.15, 0.2, 0, 0, -0.74, segs=20, bevel=0.06)
flush('hb_panel')

# ------------------------------------------------------------------ hb_droplight (the ceiling is z 0; the rod here is 4 long)
reset()
cyl('plastic', '3a3d4a', 0.9, 0.4, 0, 0, -0.2, segs=14, bevel=0.12)       # the cup on the ceiling
box('plastic', INK, 0.45, 0.45, 4.0, 0, 0, -2.4, bevel=0.1)               # the rod (z -0.4 .. -4.4)
cyl('plastic', DARK, 1.5, 1.6, 0, 0, -5.2, segs=18, bevel=0.3)            # the shade
cyl('neon', WARM, 1.15, 0.2, 0, 0, -6.04, segs=18, bevel=0.06)
flush('hb_droplight')

# ------------------------------------------------------------------ hb_bar (hangs from z 0, runs along X)
reset()
for x in (-3.4, 3.4): box('plastic', DARK, 0.5, 0.5, 1.3, x, 0, -0.65, bevel=0.1)
box('plastic', DARK, 10.4, 2.6, 0.9, 0, 0, -1.65, bevel=0.3)
box('neon', LENS, 9.0, 1.6, 0.25, 0, 0, -2.08, bevel=0.08)
flush('hb_bar')

# ------------------------------------------------------------------ hb_walllight (the wall is at y +0.45)
reset()
box('plastic', DARK, 1.5, 0.45, 3.0, 0, 0.22, 1.5, bevel=0.16)
box('neon', 'ffcf8a', 0.9, 0.5, 2.3, 0, -0.2, 1.5, bevel=0.18)
flush('hb_walllight')

# ------------------------------------------------------------------ hb_slab (the wall is at y +0.25)
reset()
box('plastic', '8a90a0', 7.0, 0.45, 6.0, 0, 0.02, 3.0, bevel=0.18)
box('plastic', PALE, 5.4, 0.3, 4.4, 0, -0.26, 3.0, bevel=0.12)
flush('hb_slab')

# ------------------------------------------------------------------ hb_vending (the wall is at y +1.4)
reset()
box('plastic', PINK, 3.6, 2.8, 5.7, 0, 0, 3.15, bevel=0.4)
box('plastic', INK, 3.2, 2.4, 0.4, 0, 0, 0.2, bevel=0.1)                  # feet
box('plastic', '1f2a3a', 2.0, 0.2, 3.4, -0.55, -1.42, 3.7, bevel=0.1)     # the window
for i, c in enumerate((CYAN, YEL, 'f4f8ff')):
    box('neon', c, 1.6, 0.2, 0.3, -0.55, -1.5, 2.6 + i * 1.05, bevel=0.06)
    for k in (-0.5, 0, 0.5): cyl('plastic', 'e8ecf4', 0.2, 0.55, -0.55 + k, -1.5, 3.06 + i * 1.05, segs=8, bevel=0.05)
box('plastic', INK, 0.8, 0.2, 1.7, 1.25, -1.42, 3.9, bevel=0.08)          # the coin panel
box('plastic', YEL, 0.4, 0.2, 0.4, 1.25, -1.5, 4.3, bevel=0.08)
box('plastic', INK, 2.8, 0.2, 0.8, 0, -1.42, 1.1, bevel=0.1)              # the flap
box('neon', LENS, 3.0, 0.2, 0.5, 0, -1.42, 5.55, bevel=0.1)               # the lit sign band
flush('hb_vending')
