# THE TRAINING V2 KIT (16 Nov 2026): the shaped pieces of the new training area (studio-tools/TrainingV2.luau builds the
# rooms out of plain parts and places these). chunky and clean: few big pieces, rounded edges, flat matte colours, the
# quiet family of the 16 Nov design principles (warm pale greys, mid greys, off-white), amber as the one accent.
# 1 unit = 1 stud, Z up, a model's front faces -Y (Roblox +Z after the import), the floor is z 0 unless said.
#   tv_cover      a chest-high cover wall, 10 x 2.4 x 4.7
#   tv_block      a head-high cover block, 5 x 5 x 7.6
#   tv_target     a big round bullseye for an end wall, 16 across, 1.3 thick (centred on its middle, front -Y)
#   tv_hook       a grapple disc: amber face on a dark plate, 7 x 7 x 1.4 (centred, front -Y)
#   tv_pulpit     the Plinker's round stand, 13.2 across, 2 tall
#   tv_dais       the muster's low round dais with an amber ring, 14 across, 1 tall
#   tv_rib        one rib of the dummy yard's vault: an arc 48 wide, 10 high, 2.4 deep (z 0 = the springing line)
#   tv_frameWide  a thick framed opening 16 wide x 14 high (inside), 4.8 deep, cut top corners
#   tv_frameMid   the same, 12 wide x 12 high
#   tv_lightbar   a light in a chunky housing, 8 x 2.6 x 1.3 (z 0 = its top: it hangs from a ceiling)
#   tv_booth      a firing-booth partition, 1.2 x 5 x 5
#   tv_bench      a plain bench, 8 x 2.2 x 1.9
#   tv_tower      the movement course's tower, 16 x 16 x 28 (deck edge on top)
# run: blender -b --factory-startup -P tools/roblox/training_models.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *
from structkit import _emit

WALL, WALL2, PIER, PIER2, TRIM = 'b9b5ae', 'c4c0b8', '8f9299', '7d8088', 'e2ded5'
DARK, DEEP, AMBER, WHITE, TAN = '4a4e57', '3d414a', 'f0a53a', 'f4f6f8', 'b49a7a'
SLATE = '62666f'
reset()

# ------------------------------------------------------------------ tv_cover
# (16 Nov, the owner: "some of the props dont look super like rivals ones". rework: a barricade, not a slab: a dark
# plinth, a body with a pale panel let into each long face, chunky slate end posts standing proud, a rounded cap rail.
# same box as before: 10 x 2.4 x 4.7)
soft('plastic', DEEP, 10.0, 2.4, 0.7, 0, 0, 0.35, 0.25, pick='all', segs=2, small=0.0)
soft('plastic', PIER, 8.8, 2.1, 3.5, 0, 0, 0.7 + 1.75, 0.35, pick='up', segs=3, small=0.12)
for sy in (-1, 1):
    soft('plastic', WALL2, 7.2, 0.16, 2.3, 0, sy * 1.05, 2.5, 0.25, pick='y', segs=2, small=0.04)
for sx in (-1, 1):
    soft('plastic', SLATE, 1.0, 2.55, 3.7, sx * 4.55, 0, 0.6 + 1.85, 0.35, pick='up', segs=3, small=0.12)
soft('plastic', TRIM, 10.3, 2.7, 0.55, 0, 0, 4.15 + 0.275, 0.25, pick='all', segs=2, small=0.0)
keep('tv_cover')

# ------------------------------------------------------------------ tv_block
# (rework, as tv_cover: a cover pillar. a dark plinth, two body blocks either side of a dark band, a pale panel let into
# every face of each, slate corner guards up all four corners, a rounded cap. same box: 5 x 5 x 7.6)
soft('plastic', DEEP, 5.0, 5.0, 0.6, 0, 0, 0.3, 0.3, pick='all', segs=2, small=0.0)
soft('plastic', PIER2, 4.5, 4.5, 3.1, 0, 0, 0.6 + 1.55, 0.5, pick='up', segs=3, small=0.12)
soft('plastic', DEEP, 4.65, 4.65, 0.5, 0, 0, 3.7 + 0.25, 0.2, pick='all', segs=2, small=0.0)
soft('plastic', PIER2, 4.5, 4.5, 2.85, 0, 0, 4.2 + 1.425, 0.5, pick='up', segs=3, small=0.12)
for z, h in ((2.15, 2.1), (5.625, 1.9)):
    for a in range(4):
        rot = RZ(a * math.pi / 2)
        soft('plastic', WALL2, 2.5, 0.16, h, 0, -2.25, z, 0.2, pick='y', segs=2, small=0.04, M=rot)
for sx in (-1, 1):
    for sy in (-1, 1):
        soft('plastic', SLATE, 0.95, 0.95, 6.6, sx * 2.1, sy * 2.1, 0.55 + 3.3, 0.35, pick='up', segs=3, small=0.1)
soft('plastic', TRIM, 5.3, 5.3, 0.55, 0, 0, 7.05 + 0.275, 0.3, pick='all', segs=2, small=0.0)
keep('tv_block')

# ------------------------------------------------------------------ tv_target (front -Y, centred)
# (16 Nov, the flicker list: the rings' backs all lay in one plane. each ring's back is now 0.04 in from the last)
for k, (r, t, col) in enumerate(((8.0, 1.0, TRIM), (6.5, 1.15, DARK), (5.0, 1.25, TRIM), (3.4, 1.3, DARK), (1.8, 1.35, AMBER))):
    front, back = -(t - 0.5), 0.5 - 0.04 * k
    cy('plastic', col, r, back - front, 0, (front + back) / 2, 0, axis='y', segs=40, bevel=0.18)
keep('tv_target')

# ------------------------------------------------------------------ tv_hook (front -Y, centred)
soft('plastic', DARK, 7.0, 0.8, 7.0, 0, 0.3, 0, 1.2, pick='y', segs=3, small=0.1)
cy('plastic', PIER, 3.1, 1.1, 0, -0.15, 0, axis='y', segs=32, bevel=0.2)
cy('plastic', AMBER, 2.5, 1.3, 0, -0.25, 0, axis='y', segs=32, bevel=0.2)
cy('plastic', DARK, 0.9, 1.4, 0, -0.3, 0, axis='y', segs=20, bevel=0.15)
keep('tv_hook')

# ------------------------------------------------------------------ tv_pulpit (top at z 2)
lathe('plastic', DEEP, [(6.0, 0.0), (6.0, 0.6), (0.0, 0.6)], segs=40, bevel=0.0)
lathe('plastic', PIER, [(6.2, 0.55), (6.2, 1.55), (0.0, 1.55)], segs=40, bevel=0.0)
cy('plastic', TRIM, 6.6, 0.45, 0, 0, 1.775, segs=48, bevel=0.2)
cy('plastic', PIER2, 4.6, 0.06, 0, 0, 2.0, segs=40, bevel=0.0)
keep('tv_pulpit')

# ------------------------------------------------------------------ tv_dais (top at z 1)
cy('plastic', PIER2, 7.0, 0.5, 0, 0, 0.25, segs=48, bevel=0.15)
cy('plastic', TRIM, 5.6, 0.5, 0, 0, 0.75, segs=48, bevel=0.15)
lathe('neon', AMBER, ring_prof(4.4, 0.32, 8), segs=48, cap=False, M=T(0, 0, 0.98))
cy('plastic', PIER, 3.2, 0.08, 0, 0, 1.0, segs=40, bevel=0.0)
keep('tv_dais')

# ------------------------------------------------------------------ tv_rib: span 48, rise 10, 1.8 deep, 2.4 wide
SPAN, RISE, DEPTH, WIDE = 48.0, 10.0, 1.8, 2.4
R = (SPAN * SPAN / 4 + RISE * RISE) / (2 * RISE)
th0 = math.asin(SPAN / 2 / R)
cz = RISE - R
N = 24
outer = [(R * math.sin(th0 - 2 * th0 * i / N), cz + R * math.cos(th0 - 2 * th0 * i / N)) for i in range(N + 1)]
inner = [((R - DEPTH) * math.sin(-th0 + 2 * th0 * i / N), cz + (R - DEPTH) * math.cos(-th0 + 2 * th0 * i / N)) for i in range(N + 1)]
prism('plastic', PIER, outer + inner, WIDE, bevel=0.25, segs=2)
keep('tv_rib')

# ------------------------------------------------------------------ frames: an inverted U with cut top corners
def frame(name, W, H, jamb=2.4, head=2.4, cut=2.6, depth=4.8):
    pts = [(-W / 2 - jamb, 0.0), (-W / 2 - jamb, H + head), (W / 2 + jamb, H + head), (W / 2 + jamb, 0.0),
           (W / 2, 0.0), (W / 2, H - cut), (W / 2 - cut, H), (-W / 2 + cut, H), (-W / 2, H - cut), (-W / 2, 0.0)]
    prism('plastic', PIER, pts, depth, bevel=0.3, segs=2)
    for sx in (-1, 1):  # a darker foot on each jamb
        bx('plastic', DEEP, jamb + 0.3, depth + 0.3, 1.2, sx * (W / 2 + jamb / 2), 0, 0.6, 0.12)
    # a pale reveal band round the inside of the head
    bx('plastic', TRIM, W - 2 * cut + 0.2, depth + 0.1, 0.5, 0, 0, H + 0.2, 0.12)  # (0.05 proud of the opening's top: flicker list)
    keep(name)

frame('tv_frameWide', 16.0, 14.0)
frame('tv_frameMid', 12.0, 12.0)

# ------------------------------------------------------------------ tv_lightbar (z 0 = its top)
soft('plastic', DARK, 8.0, 2.6, 1.1, 0, 0, -0.55, 0.45, pick='all', segs=2, small=0.0)
bx('neon', WHITE, 7.0, 1.8, 0.3, 0, 0, -1.15, 0.08)
keep('tv_lightbar')

# ------------------------------------------------------------------ tv_booth
# (rework: a framed divider, not a slab: a dark foot, a slate post at each end, a pale panel between, a rounded rail.
# same box: 1.2 x 5 x 5)
soft('plastic', DEEP, 1.2, 5.0, 0.5, 0, 0, 0.25, 0.2, pick='all', segs=2, small=0.0)
for sy in (-1, 1):
    soft('plastic', SLATE, 1.2, 0.8, 4.2, 0, sy * 2.1, 0.5 + 2.1, 0.3, pick='up', segs=3, small=0.1)
soft('plastic', WALL2, 0.7, 3.5, 3.7, 0, 0, 0.5 + 1.85, 0.15, pick='all', segs=2, small=0.0)
soft('plastic', TRIM, 1.4, 5.2, 0.45, 0, 0, 4.55 + 0.225, 0.2, pick='all', segs=2, small=0.0)
keep('tv_booth')

# ------------------------------------------------------------------ tv_bench
# (rework: a thick rounded seat over a dark rim, on two solid pedestals with feet. same box: 8 x 2.2 x 1.9)
soft('plastic', TAN, 8.0, 2.2, 0.45, 0, 0, 1.45 + 0.225, 0.2, pick='all', segs=2, small=0.0)
soft('plastic', DARK, 7.5, 1.9, 0.25, 0, 0, 1.2 + 0.125, 0.1, pick='all', segs=2, small=0.0)
for sx in (-2.8, 2.8):
    soft('plastic', PIER2, 1.0, 1.7, 1.0, sx, 0, 0.25 + 0.5, 0.3, pick='up', segs=3, small=0.08)
    soft('plastic', DEEP, 1.5, 2.0, 0.25, sx, 0, 0.125, 0.1, pick='all', segs=2, small=0.0)
keep('tv_bench')

# ------------------------------------------------------------------ tv_tower: 16 x 16 x 28, its deck on top
soft('plastic', WALL2, 16.0, 16.0, 27.0, 0, 0, 13.5, 1.6, pick='up', segs=3, small=0.15)
for zb in (9.0, 18.0):
    soft('plastic', TRIM, 16.6, 16.6, 0.9, 0, 0, zb, 1.8, pick='up', segs=3, small=0.15)
for a in range(4):
    M = RZ(a * math.pi / 2)
    for z0, z1 in ((1.2, 8.2), (9.8, 17.2), (18.8, 26.2)):
        bx('plastic', PIER, 9.0, 0.4, z1 - z0, 0, -7.9, (z0 + z1) / 2, 0.1, M=M)
bx('plastic', DEEP, 15.6, 15.6, 0.6, 0, 0, 0.3, 0.05)
bx('neon', AMBER, 16.3, 16.3, 0.5, 0, 0, 26.75, 0.1)
soft('plastic', TRIM, 17.0, 17.0, 1.0, 0, 0, 27.5, 0.9, pick='up', segs=3, small=0.25)
keep('tv_tower')

# ------------------------------------------------------------------ tv_crown: the muster's ceiling (8 sides; z 0 = its floor)
# a 45-degree cove off the wall tops (apothem 20 at z 16 to 16 at z 20), a flat ring to the lantern (apothem 12), the
# lantern's drum up to z 32 and its cap. lathe() with 8 segments makes an octagon; turned an eighth so a side faces -Y
K8 = 1.0 / math.cos(math.pi / 8)
def oct8(kind, col, prof):
    pts = [(a * K8, z) for a, z in prof]
    lathe(kind, col, pts + [pts[0]], M=RZ(math.pi / 8), segs=8, cap=False)
oct8('plastic', TRIM, [(20.0, 16.0), (16.0, 20.0), (16.0, 21.2), (24.5, 21.2), (24.5, 16.0)])
oct8('plastic', 'aeaba5', [(16.0, 20.0), (12.05, 20.0), (12.05, 21.2), (16.0, 21.2)])  # (its inside face inside the drum)
oct8('plastic', WALL2, [(12.0, 20.05), (12.0, 32.05), (13.6, 32.05), (13.6, 20.05)])  # (its foot inside the ring: flicker list)
oct8('plastic', TRIM, [(12.0, 20.0), (11.4, 20.0), (11.4, 20.9), (12.0, 20.9)])
lathe('plastic', 'aeaba5', [(13.6 * K8, 32.0), (0.0, 32.0), (0.0, 33.6), (13.6 * K8, 33.6), (13.6 * K8, 32.0)], M=RZ(math.pi / 8), segs=8, cap=False)
keep('tv_crown')

# ------------------------------------------------------------------ tv_vault: one 16-long bay of the yard's barrel vault
# the same arc as tv_rib (span 48, rise 10; z 0 = the springing line), 1 thick outward, 16 long along Y
VN = 32
vo = [((R + 1.0) * math.sin(th0 - 2 * th0 * i / VN), cz + (R + 1.0) * math.cos(th0 - 2 * th0 * i / VN)) for i in range(VN + 1)]
vi = [(R * math.sin(-th0 + 2 * th0 * i / VN), cz + R * math.cos(-th0 + 2 * th0 * i / VN)) for i in range(VN + 1)]
prism('plastic', 'aeaba5', vo + vi, 16.0, bevel=0.0)
keep('tv_vault')

# ------------------------------------------------------------------ rework 1 (judge round 1, 16 Nov)
SLATE = '5f646e'  # mid slate in place of near-black on bases and housings
# tv_towerOct: the course's tower as one big eight-sided piece (cut corners), 16 across the flats, 28 tall
oct8('plastic', SLATE, [(8.15, 0.0), (8.15, 0.95), (0.0, 0.95), (0.0, 0.0)])  # (its top inside the body: flicker list)
oct8('plastic', WALL2, [(8.0, 0.9), (8.0, 27.05), (0.0, 27.05), (0.0, 0.9)])  # (its top inside the trim cap: flicker list)
for zb in (9.0, 18.0):
    oct8('plastic', TRIM, [(8.45, zb - 0.45), (8.45, zb + 0.45), (7.9, zb + 0.45), (7.9, zb - 0.45)])
oct8('plastic', TRIM, [(8.7, 27.0), (8.7, 28.0), (0.0, 28.0), (0.0, 27.0)])
for a in range(8):
    M = RZ(a * math.pi / 4)
    for z0, z1 in ((1.8, 8.0), (9.9, 17.1), (18.9, 26.2)):
        bx('plastic', PIER, 3.8, 0.4, z1 - z0, 0, -7.95, (z0 + z1) / 2, 0.12, M=M)
keep('tv_towerOct')

# tv_ring: a grapple point: a plain amber hoop on a thick stem. z 0 = where the stem meets the beam; it hangs down
cy('plastic', SLATE, 1.1, 0.6, 0, 0, -0.3, segs=20, bevel=0.15)
cy('plastic', PIER, 0.55, 3.2, 0, 0, -1.9, segs=16, bevel=0.1)
cy('plastic', PIER, 0.9, 0.8, 0, 0, -3.45, segs=16, bevel=0.15)
for a in (0.0, math.pi / 2):
    bx('plastic', PIER, 4.4, 0.45, 0.45, 0, 0, -3.45, 0.1, rot=RZ(a))
lathe('plastic', AMBER, ring_prof(2.3, 0.55, 10), segs=32, cap=False, M=T(0, 0, -3.45))
keep('tv_ring')

# tv_hoop (rework 3: the ring on a stem read as a valve wheel): a flat amber hoop held flush under a beam by a slate
# boss in its middle. z 0 = the beam's underside; it hangs 1.3
cy('plastic', SLATE, 1.5, 0.5, 0, 0, -0.25, segs=24, bevel=0.15)
cy('plastic', PIER, 0.8, 0.9, 0, 0, -0.75, segs=20, bevel=0.15)
lathe('plastic', AMBER, ring_prof(2.4, 0.55, 10), segs=36, cap=False, M=T(0, 0, -0.75))
for a in (0.0, math.pi / 3, 2 * math.pi / 3):
    bx('plastic', SLATE, 4.2, 0.35, 0.3, 0, 0, -0.5, 0.06, rot=RZ(a))  # (tops 0.05 under the stem's: flicker list)
keep('tv_hoop')

export_all('training_v2.glb')
if len(sys.argv) > sys.argv.index('--') + 2:
    preview(sys.argv[sys.argv.index('--') + 2], cols=5)
