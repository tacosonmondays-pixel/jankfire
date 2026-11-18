# BATCH E, PART 2 (18 Nov 2026): NEW kit models for the Card Deck and the Lasso and the things they throw, ported from
# the web game (public/models/w_cards.glb, pj_card.glb, w_lasso.glb; tools/blender/make_cards.py, make_lasso.py are the
# brief for what each thing IS) and built fresh in the kit style (a few big rounded masses, flat colours, a quiet base and
# one accent, every join a flare, a fillet or one continuous solid), as Batches A..D (gun_batch_a.py's Batch,
# gun_batch_d2.py's BatchX). The weapons session's spec: the notes' weapons-batchE-spec.md. gun_set.py loads BUILD.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out dir> cards pj_card lasso pj_loop
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- cards pj_card lasso pj_loop
#   JF_NOZFIX=1 blender -b --factory-startup -P tools/roblox/gun_zfix.py -- cards pj_card lasso pj_loop   (0 pairs)
#   blender -b --factory-startup -P tools/roblox/export_weapons.py -- <kit dir> --kit <out dir>/w_<id>.glb
#   - CARDS   w_cards (a secondary, one hand). A hand of five chunky cards fanned in front of the rest of the deck, the
#             faces toward you (plain off-white: the game draws the hand's suits and ranks on them). The fan is the
#             viewmodel spec's: nodes fan1 .. fan5, left to right, card i (0 .. 4) turned (i - 2) x 0.22 rad in its own
#             plane about the common pivot (0, 0, z), its centre 0.09 m out from it, fan1 nearest you; each node's origin
#             is that pivot on its own card's middle plane. Their backs (toward the target) are dusty blue all over, the
#             pattern in relief (a sunk field round a raised frame line and a raised oval: shape only). Behind them the
#             deck (static): an off-white block with a stack groove every card round its edges, standing 12 mm above
#             the fan (its top edge is the hat seat), its back the bottom card's: an off-white margin round the blue
#             field, frame line and oval. The muzzle is the middle card's top edge. No letters, digits or pips.
#   - PJ_CARD w_pj_card: one card 0.09 x 0.13 m, 3.2 mm thick, rounded corners and a rounded rim, lying flat with its
#             face up (+y) and the nose (its top edge) at -z, origin at its centre. The back (-y) as the deck's (margin,
#             sunk field, frame line, oval). On the face ONE pip at the centre, five variants as nodes the game shows one
#             of (pip_h heart, pip_s spade, pip_c club, pip_d diamond, pip_j a five-point star for the joker), red for
#             h, d and j, near-black for s and c. Every pip is domed (no face of it lies parallel to the card): the red
#             ones sink their rim into the face on a bottom tilted 4.5 degrees; the black ones stand on a cone 1 mm clear
#             of the face, their tops 1 mm above the red tops, so a red pip and a black pip never share a plane.
#   - LASSO   w_lasso (a secondary, one hand). A chunky three-strand rope (its strands a raised twist that turns once
#             every 12 cm: shape, not paint), toned rope tan: a coil of three loops hanging from the fist, each loop's
#             top arcing out above the fist (the middle one highest: the hat seat), turned 30 degrees to face back and
#             left; the tail hangs down behind the fist with a dark whipping and a frayed end. In front of the coil the
#             lariat's loop (node `loop`): a round loop held in the fist like the coils, a plain rope eye (the honda,
#             spot `eye`) low on its right side where the spoke passes through, the spoke running up beside it into the
#             fist (it leaves the fist's bottom at spot `lead`, the node's origin). The loop hangs from the hand, never
#             from its knot (the content rule: nothing that reads as a noose). The muzzle is the loop's centre: hide
#             `loop` on a throw, the game's Beam runs from `lead` to the thrown loop.
#   - PJ_LOOP w_pj_loop: the thrown loop, a plain ring 1.1 m across (the catch radius 0.55 m), the same 25 mm rope
#             lying flat in the x-z plane, origin at the ring's centre; at the back (+z) a small plain eye in the rope
#             itself (no wraps) the rope passes through, then a short stub behind it whose end is spot `eye` (the Beam
#             attaches there). Spots centre, nose (-z), eye. One colour.
# CONTRACT (as Batches A..D): held models carry spots muzzle, grip (where the fist closes) and hat (the seat) plus
# `hatAt` [[x, y, z], size] and `pivots` (the moving nodes' origins) in the file notes; the cards also carry meta.fan
# (the five nodes, left to right) and meta.fanPivot / fanRadius / fanStep, the lasso spots lead and eye. Projectiles
# carry spots centre and nose (pj_loop also eye), kind 'proj', no hat; pj_card carries meta.pips (suit -> node).
# Frame: gunkit's (metres; x right, y up, z back, the muzzle at -z).
# Zones: the card backs' blue _wzA (a wrap paints them: a custom card back), the off-white card bodies _wzN; the rope
# _wzA, its whipping _wzN; pj_card's body _wzA, its field _wzB, the pips _wzN.
# Flicker rule: no face of one look parallel to (within 2.6 degrees) and within 12 mm of a face of another look,
# hidden or not. Colours change on one solid (a split, never a layer). The fan's cards are parallel and 2.8 mm apart,
# so each is one colour a side (white face and rim, a blue back); the two-colour back is only on the deck's far side,
# 16 mm behind the fan. The pips are domed and tiered (above). JF_NOZFIX=1 gun_zfix.py: 0 pairs.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import gunkit
from gunkit import P
from artist_kit import cut, to_mesh, _obj, KEEP
from gun_melee import split, catmull, loft
from gun_batch_d2 import BatchX

# the colours (a little darker and greyer than they look in Blender: the game's lamps push them brighter)
CARD = 'dcd8ce'      # the off-white card stock
BACK = '56607a'      # the backs' dusty blue
RED = 'a33b41'       # hearts, diamonds, the joker's star
INK = '25262c'       # spades, clubs
ROPE = 'b09264'      # e0b070 toned
LEATHER = '4b3c32'   # the tail's whipping

PI = math.pi


# ================================================================================================= small helpers
def smooth01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rr_pts(hw, hh, r, m=3, cx=0.0, cy=0.0):
    """a rounded rectangle (half sizes hw, hh, corners r) as 4 (m + 1) points, counter-clockwise"""
    r = max(1e-5, min(r, hw - 1e-5, hh - 1e-5))
    out = []
    for ccx, ccy, a0 in ((hw - r, -hh + r, -PI / 2), (hw - r, hh - r, 0.0), (-hw + r, hh - r, PI / 2), (-hw + r, -hh + r, PI)):
        for k in range(m + 1):
            a = a0 + (PI / 2) * k / m
            out.append((cx + ccx + r * math.cos(a), cy + ccy + r * math.sin(a)))
    return out


def inset_rr(u, v, hw, hh, r):
    """how far (u, v) lies inside a rounded rectangle (negative: outside)"""
    qx, qy = abs(u) - (hw - r), abs(v) - (hh - r)
    return -(math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r)


def slab(pts2, n0, n1, M):
    """a polygon [(u, v)] in a card's own plane pushed from n0 to n1 along its normal; M: card (u, v, n) -> weapon"""
    bm = bmesh.new()
    A = [bm.verts.new(P(*(M @ Vector((u, v, n0))))) for u, v in pts2]
    B = [bm.verts.new(P(*(M @ Vector((u, v, n1))))) for u, v in pts2]
    n = len(pts2)
    bm.faces.new(A); bm.faces.new(B[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([A[i], B[i], B[j], A[j]])
    return _obj(bm)


def ellipse_pts(a, b, n=20):
    return [(a * math.cos(2 * PI * i / n), b * math.sin(2 * PI * i / n)) for i in range(n)]


# ================================================================================================= a card
def card_solid(M, W, H, T, R, BV, m=3, rim=3):
    """a card W x H, T thick, corners R, its rim rounded BV: lofted through rounded-rectangle sections from the face
       (-n) to the back (+n). M: card (u, v, n) -> weapon frame"""
    prof = []
    for j in range(rim + 1):        # the face's rounded edge, from the face out to full size
        th = (PI / 2) * j / rim
        prof.append((BV - BV * math.sin(th), -T / 2 + BV - BV * math.cos(th)))
    for j in range(rim + 1):        # up to the back's rounded edge
        th = (PI / 2) * j / rim
        prof.append((BV - BV * math.cos(th), T / 2 - BV + BV * math.sin(th)))
    st = [[tuple(M @ Vector((u, v, n))) for u, v in rr_pts(W / 2 - dl, H / 2 - dl, R - dl, m)] for dl, n in prof]
    return loft(st)


# the back's pattern: margin, frame line inset and width, the oval's half axes, the field's depth (metres)
BACK_PAT = {'big': dict(MW=0.006, FI=0.0034, FW=0.0016, OV=(0.0115, 0.0175), DR=0.0005),
            'hand': dict(MW=0.0058, FI=0.0032, FW=0.0015, OV=(0.011, 0.017), DR=0.0007)}


def back_cutters(M, W, H, R, n_top, pat, m=3):
    """the two cutters that sink the back's field (n_top - DR) round a raised frame line and a raised oval"""
    MW, FI, FW, (oa, ob), DR = pat['MW'], pat['FI'], pat['FW'], pat['OV'], pat['DR']
    field = slab(rr_pts(W / 2 - MW, H / 2 - MW, max(R - MW, 0.0015), m), n_top - DR, n_top + 0.002, M)
    fo = slab(rr_pts(W / 2 - MW - FI, H / 2 - MW - FI, max(R - MW - FI, 0.0011), m), n_top - DR - 0.001, n_top + 0.003, M)
    fi = slab(rr_pts(W / 2 - MW - FI - FW, H / 2 - MW - FI - FW, max(R - MW - FI - FW, 0.0008), m), n_top - DR, n_top + 0.002, M)
    ov = slab(ellipse_pts(oa, ob), n_top - DR - 0.001, n_top + 0.003, M)
    return [to_mesh(cut(field, fo)), to_mesh(cut(fi, ov))]


def field_test(M, W, H, R, n_top, pat):
    """the split test for a two-colour back's blue: the sunk field's floor and every wall in it (the margin, the frame
       line's top and the oval's top stay off-white)"""
    Mi = M.inverted()
    MW, DR = pat['MW'], pat['DR']
    def test(c, n):
        q = Mi @ Vector(c)
        return n_top - DR - 2e-4 < q.z < n_top - 1e-4 and inset_rr(q.x, q.y, W / 2, H / 2, R) > MW - 3e-4
    return test


def mono_test(M, W, H, R, n_top, pat, BV):
    """the split test for a one-colour back: everything on the back inside the rim"""
    Mi = M.inverted()
    DR = pat['DR']
    def test(c, n):
        q = Mi @ Vector(c)
        return q.z > n_top - DR - 2e-4 and inset_rr(q.x, q.y, W / 2, H / 2, R) > BV - 1e-4
    return test


def patterned_card(g, node, M, W, H, T, R, BV, pat, zone_card='N', zone_back='A', mono=False):
    o = card_solid(M, W, H, T, R, BV)
    o = cut(o, *back_cutters(M, W, H, R, T / 2, pat))
    test = mono_test(M, W, H, R, T / 2, pat, BV) if mono else field_test(M, W, H, R, T / 2, pat)
    rest, field = split(o, test)
    g.put('%s_wz%s__card' % (node, zone_card), rest); g.put('%s_wz%s__back' % (node, zone_back), field)


# ================================================================================================= the hand (w_cards)
CW, CH, CR = 0.09, 0.13, 0.0085        # a held card: the thrown card's size
CT, CBV = 0.0026, 0.0008               # its thickness, its rim
NDECK = 6                              # the deck block reads as six cards (five stack grooves)
FAN_R, FAN_STEP, FAN_GAP = 0.09, 0.22, 0.0028
FAN_Z0 = 0.0016                        # the back card's middle plane (its back 0.3 mm clear of the deck's front)
DECK_Y = 0.108                         # the deck's middle: its top 12 mm over the fan's highest corner
FLIP = Matrix.Rotation(PI, 4, 'Y')     # card (u, v, n) turned so its back (+n) faces the target (-z)


def fan_matrix(i):
    """fan card i (0 .. 4, left to right): card (u, v, n) -> weapon. turned (i - 2) FAN_STEP about the common pivot
       (0, 0) in its plane, its centre FAN_R out, card 0 nearest you"""
    a = (i - 2) * FAN_STEP
    zi = FAN_Z0 + (4 - i) * FAN_GAP
    return Matrix.Translation((0.0, 0.0, zi)) @ Matrix.Rotation(-a, 4, 'Z') @ Matrix.Translation((0.0, FAN_R, 0.0)) @ FLIP, zi


def deck_block(W, H, R, D, BV, YC, m=3):
    """the deck: one loft along z from its back (-D, the bottom card's back) to its front (0, the top card's face),
       rounded at both faces, a V stack groove every card thickness round its edges"""
    prof = []
    for j in range(4):
        th = (PI / 2) * j / 3
        prof.append((-D + BV - BV * math.cos(th), BV - BV * math.sin(th)))
    for i in range(1, NDECK):
        zg = -D + i * CT
        prof += [(zg - 0.0005, 0.0), (zg, 0.0004), (zg + 0.0005, 0.0)]
    for j in range(4):
        th = (PI / 2) * j / 3
        prof.append((-BV + BV * math.sin(th), BV - BV * math.cos(th)))
    st = [[(x, YC + y, z) for x, y in rr_pts(W / 2 - dl, H / 2 - dl, R - dl, m)] for z, dl in prof]
    return loft(st)


def cards():
    """THE CARD DECK (see the file's header)"""
    gunkit.use_style('B')
    g = BatchX('w_cards')
    g.slot('card', CARD); g.slot('back', BACK)
    pat = BACK_PAT['hand']
    D = NDECK * CT
    # ---- the deck block (static), the bottom card's back on its far (-z) side
    Md = Matrix.Translation((0.0, DECK_Y, -D)) @ FLIP     # (card (u, v, n): n 0 on the deck's back, + outward)
    dk = deck_block(CW, CH, CR, D, CBV, DECK_Y)
    dk = cut(dk, *back_cutters(Md, CW, CH, CR, 0.0, pat))
    rest, field = split(dk, field_test(Md, CW, CH, CR, 0.0, pat))
    g.put('deck_wzN__card', rest); g.put('deck_wzA__back', field)
    # ---- the fan: five cards, their faces toward you, their backs one blue
    for i in range(5):
        M, zi = fan_matrix(i)
        patterned_card(g, 'fan%d' % (i + 1), M, CW, CH, CT, CR, CBV, pat, mono=True)
        g.origins['fan%d' % (i + 1)] = (0.0, 0.0, round(zi, 5))
    M3, _ = fan_matrix(2)
    g.spots = {'grip': (0.0, 0.035, -0.001), 'muzzle': tuple(round(x, 4) for x in (M3 @ Vector((0.0, CH / 2, 0.0))))}
    # the hat seat: the deck's top edge, on the flat between two stack grooves (the fan's corners stand 12 mm lower)
    g.hat = ((0.0, round(DECK_Y + CH / 2, 4), round(-D + 3.5 * CT, 4)), 0.05)
    g.extra['fan'] = ['fan%d' % k for k in range(1, 6)]
    g.extra['fanPivot'] = [0.0, 0.0]
    g.extra['fanRadius'] = FAN_R
    g.extra['fanStep'] = FAN_STEP
    return g.done()


# ================================================================================================= the thrown card
PW, PH, PR, PT, PBV = 0.09, 0.13, 0.0085, 0.0032, 0.0009


def heart_pts(w, n=24):
    """a heart w wide, centred, its cusp up: the classic curve resampled evenly along its length"""
    k = w / 32.0
    dense = []
    for i in range(720):
        t = 2 * PI * i / 720
        dense.append(Vector((16 * math.sin(t) ** 3 * k, (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t) + 2.5) * k)))
    S = [0.0]
    for a, b in zip(dense, dense[1:] + dense[:1]): S.append(S[-1] + (b - a).length)
    out, j = [], 0
    for i in range(n):
        s = S[-1] * i / n
        while S[j + 1] < s: j += 1
        f = (s - S[j]) / (S[j + 1] - S[j])
        p = dense[j].lerp(dense[(j + 1) % 720], f)
        out.append((p.x, p.y))
    return out


def centroid(pts):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        c = x0 * y1 - x1 * y0
        a += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
    return (cx / (3 * a), cy / (3 * a))


def diamond_pts(hw, hh, bow, per=5):
    """a rhombus, its sides bowed in by `bow` at their middles"""
    C = [(0.0, hh), (hw, 0.0), (0.0, -hh), (-hw, 0.0)]
    out = []
    for i in range(4):
        a, b = Vector(C[i]), Vector(C[(i + 1) % 4])
        nrm = Vector(((b - a).y, -(b - a).x)).normalized()   # (into the shape: the corners run clockwise)
        for j in range(per):
            t = j / per
            p = a.lerp(b, t) + nrm * (bow * math.sin(PI * t))
            out.append((p.x, p.y))
    return out


def star_pts(ro, ri, per=2):
    C = []
    for i in range(10):
        a = PI / 2 + PI * i / 5
        r = ro if i % 2 == 0 else ri
        C.append(Vector((r * math.cos(a), r * math.sin(a))))
    out = []
    for i in range(10):
        a, b = C[i], C[(i + 1) % 10]
        for j in range(per):
            p = a.lerp(b, j / per)
            out.append((p.x, p.y))
    return out


def stem_pts(top, neck, foot_y, foot_hw):
    """a spade's or club's stem: a narrow neck flaring to a foot, its bottom bowed up a little"""
    pts = [(-neck, top), (neck, top)]
    for j in range(1, 4):                      # the right side flaring out (concave)
        t = j / 4
        pts.append((neck + (foot_hw - neck) * t ** 2.2, top + (foot_y - top) * t))
    pts.append((foot_hw, foot_y))
    pts.append((0.0, foot_y + 0.0012))
    pts.append((-foot_hw, foot_y))
    for j in range(3, 0, -1):
        t = j / 4
        pts.append((-(neck + (foot_hw - neck) * t ** 2.2), top + (foot_y - top) * t))
    return pts


def circle_pts(c, r, n):
    return [(c[0] + r * math.cos(2 * PI * i / n), c[1] + r * math.sin(2 * PI * i / n)) for i in range(n)]


FACE = PT / 2
# the two pip tiers (heights above the card's middle plane; the face is at FACE): (s, h) rings from the bottom up, h a
# number or a function of (u, v). Red: its rim sunk into the face on a bottom tilted 4.5 degrees, a short wall, a dome
# whose every facet leans 4 degrees or more. Black: a cone from 1 mm into the card up to a rim 1 mm clear of the
# face, a wall, a dome 1 mm above the red tier's top (red and black never share a plane, and neither shares the card's)
RED_TIER = [(1.0, lambda u, v: 0.0003 + math.tan(math.radians(4.5)) * v), (1.0, FACE + 0.00025), (0.62, FACE + 0.0008), (0.0, FACE + 0.0014)]
INK_TIER = [(0.0, FACE - 0.001), (1.0, FACE + 0.001), (1.0, FACE + 0.0024), (0.62, FACE + 0.00295), (0.0, FACE + 0.0036)]


def dome(pts2, levels, c2=None):
    """a solid of rings: the outline pts2 [(u, v)] (u right, v up the card toward the nose) scaled about c2 by s at
       height h (weapon y), u -> x, v -> -z. a first ring of s 1 is capped flat (on its own plane)"""
    c2 = c2 or centroid(pts2)
    bm = bmesh.new()
    rings = []
    for s, h in levels:
        hf = h if callable(h) else (lambda u, v, h=h: h)
        if s < 1e-6:
            rings.append([bm.verts.new(P(c2[0], hf(*c2), -c2[1]))])
        else:
            ring = []
            for u, v in pts2:
                uu, vv = c2[0] + s * (u - c2[0]), c2[1] + s * (v - c2[1])
                ring.append(bm.verts.new(P(uu, hf(uu, vv), -vv)))
            rings.append(ring)
    n = len(pts2)
    for A, B in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            if len(A) == 1: bm.faces.new([A[0], B[j], B[i]])
            elif len(B) == 1: bm.faces.new([A[i], A[j], B[0]])
            else: bm.faces.new([A[i], A[j], B[j], B[i]])
    if len(rings[0]) > 1: bm.faces.new(rings[0])
    if len(rings[-1]) > 1: bm.faces.new(rings[-1][::-1])
    return _obj(bm)


def shift(pts, dv):
    return [(u, v + dv) for u, v in pts]


def pip_solids(suit):
    """the solids of one pip (centred on the card, about 24 mm), and its slot. a spade or club is a few domes that
       overlap in one colour (no boolean: a union left flat slivers level with the card where the domes met)"""
    if suit == 'h':
        return [dome(heart_pts(0.0235, 24), RED_TIER)], 'red'
    if suit == 'd':
        return [dome(diamond_pts(0.0105, 0.0145, 0.0011), RED_TIER, (0.0, 0.0))], 'red'
    if suit == 'j':
        return [dome(star_pts(0.0145, 0.0062), RED_TIER, (0.0, 0.0))], 'red'
    if suit == 's':
        body = [(u, -v) for u, v in heart_pts(0.0235, 20)]          # the heart upside down: its point up
        body = shift(body, 0.0038)                                   # (the whole spade centred: body over a stem)
        cusp = min(v for u, v in body if abs(u) < 1e-6)
        parts = [dome(body, INK_TIER), dome(stem_pts(cusp + 0.0035, 0.0016, -0.0145, 0.0068), INK_TIER)]
        return parts, 'ink'
    if suit == 'c':
        dv = -0.0006
        lobes = [circle_pts((0.0, 0.0068 + dv), 0.0066, 12), circle_pts((-0.0074, -0.0022 + dv), 0.0066, 12),
                 circle_pts((0.0074, -0.0022 + dv), 0.0066, 12)]
        parts = [dome(p, INK_TIER) for p in lobes]
        parts.append(dome(stem_pts(0.0008 + dv, 0.0019, -0.0145, 0.0066), INK_TIER))
        return parts, 'ink'
    raise ValueError(suit)


PIPS = ('h', 's', 'c', 'd', 'j')


def pj_card():
    """the thrown card (see the file's header)"""
    gunkit.use_style('B')
    g = BatchX('w_pj_card', kind='proj')
    g.slot('card', CARD); g.slot('back', BACK); g.slot('red', RED); g.slot('ink', INK)
    # card (u, v, n) -> weapon: u -> -x, v (its top) -> -z (the nose), n (its back) -> -y (a proper turn, face up)
    M = Matrix(((-1, 0, 0, 0), (0, 0, -1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    patterned_card(g, 'card', M, PW, PH, PT, PR, PBV, BACK_PAT['big'], zone_card='A', zone_back='B')
    for s in PIPS:
        solids, slot = pip_solids(s)
        g.put('pip_%s_wzN__%s' % (s, slot), *solids)
        g.origins['pip_' + s] = (0.0, FACE, 0.0)
    g.spots = {'centre': (0.0, 0.0, 0.0), 'nose': (0.0, 0.0, -PH / 2)}
    g.extra['pips'] = {s: 'pip_' + s for s in PIPS}
    return g.done()


# ================================================================================================= rope
STRAND = (0.0, 0.2, 1.0, 0.2)     # a strand's crest, its shoulder, the groove, the next shoulder (x the lobe depth)


def resample_var(pts, step_at):
    """an even-ish polyline along pts: each step step_at(point) long. returns (points, their arc lengths on pts)"""
    pts = [Vector(p) for p in pts]
    S = [0.0]
    for a, b in zip(pts, pts[1:]): S.append(S[-1] + (b - a).length)
    out, sl = [pts[0].copy()], [0.0]
    s, j = 0.0, 0
    while True:
        s += step_at(out[-1])
        if s >= S[-1] - 1e-9: break
        while j < len(S) - 2 and S[j + 1] < s: j += 1
        f = (s - S[j]) / max(S[j + 1] - S[j], 1e-12)
        out.append(pts[j].lerp(pts[j + 1], f)); sl.append(s)
    if S[-1] - sl[-1] < 0.35 * step_at(pts[-1]) and len(out) > 2:
        out.pop(); sl.pop()
    out.append(pts[-1].copy()); sl.append(S[-1])
    return out, sl


def rope_bms(pts, rad, lobe, tags, lay, sides=12, caps=(True, True)):
    """a rope along pts (weapon frame), parallel-transported: per point radius, lobe depth and tag; its three strands
       turn once every `lay` metres; rounded end caps. returns {tag: bmesh} (open shells sharing their seams, smooth)"""
    n = len(pts)
    S = [0.0]
    for a, b in zip(pts, pts[1:]): S.append(S[-1] + (b - a).length)
    T = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    up = Vector((0, 1, 0)) if abs(T[0].y) < 0.9 else Vector((1, 0, 0))
    Nv = (up - T[0] * T[0].dot(up)).normalized()
    bm = bmesh.new()
    rings, ftags = [], []
    def ring(c, Nv, B, psi, r, lk):
        return [bm.verts.new(P(*(c + (Nv * math.cos(psi + 2 * PI * k / sides) + B * math.sin(psi + 2 * PI * k / sides)) *
                                 r * (1 - lk * STRAND[k % 4])))) for k in range(sides)]
    frames = []
    for i in range(n):
        Nv = (Nv - T[i] * T[i].dot(Nv)).normalized()
        B = T[i].cross(Nv)
        frames.append((Nv.copy(), B))
        rings.append(ring(pts[i], Nv, B, 2 * PI * S[i] / lay, rad[i], lobe[i]))
    def band(A, Bq, tag):
        # (two triangles a quad, cut along its shorter diagonal: with the strands turning about a side a station that
        # diagonal runs along the strand, so the twist reads as clean ridges, not lumps)
        for k in range(sides):
            kk = (k + 1) % sides
            if (A[k].co - Bq[kk].co).length <= (A[kk].co - Bq[k].co).length:
                bm.faces.new([A[k], A[kk], Bq[kk]]); bm.faces.new([A[k], Bq[kk], Bq[k]])
            else:
                bm.faces.new([A[k], A[kk], Bq[k]]); bm.faces.new([A[kk], Bq[kk], Bq[k]])
            ftags.append(tag); ftags.append(tag)
    for i in range(n - 1):
        band(rings[i], rings[i + 1], tags[i])
    for end, i, sg in ((0, 0, -1.0), (1, n - 1, 1.0)):
        if not caps[end]: continue
        Nv, B = frames[i]
        psi = 2 * PI * S[i] / lay
        last = rings[i]
        for off, k in ((0.42, 0.84), (0.75, 0.5)):
            rr = ring(pts[i] + T[i] * sg * off * rad[i], Nv, B, psi, rad[i] * k, lobe[i] * k)
            if end == 0: band(rr, last, tags[i])
            else: band(last, rr, tags[i])
            last = rr
        tip = bm.verts.new(P(*(pts[i] + T[i] * sg * 0.9 * rad[i])))
        for k in range(sides):
            kk = (k + 1) % sides
            bm.faces.new([last[k], last[kk], tip] if end == 1 else [last[kk], last[k], tip]); ftags.append(tags[i])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.faces.ensure_lookup_table()
    out = {}
    for tag in sorted(set(ftags)):
        b2 = bm.copy()
        b2.faces.ensure_lookup_table()
        gone = [b2.faces[i] for i, t in enumerate(ftags) if t != tag]
        bmesh.ops.delete(b2, geom=gone, context='FACES')
        for f in b2.faces: f.smooth = True
        out[tag] = b2
    bm.free()
    return out


def add_bm(g, piece, bm):
    """fold a finished bmesh into a piece (kept smooth: ArtGun.done keeps a piece's own shading)"""
    node, slot = piece.split('__')
    g.slots[slot]
    key = (node, slot)
    if key not in g.pieces:
        g.pieces[key] = bm
        return
    me = bpy.data.meshes.new('add'); KEEP.append(me)
    bm.to_mesh(me); bm.free()
    g.pieces[key].from_mesh(me)


def frame3(d, w):
    d = Vector(d).normalized()
    w = Vector(w); w = (w - d * d.dot(w)).normalized()
    return d, w, d.cross(w)


def loop_ctrl(H, d, w, RE, PITCH, loop, run, theta_s=300.0, n_eye=12):
    """a lariat loop's control points, from the rope's end (the honda: a plain eye, a helix of theta_s degrees round
       the running line H + t d, RE out, PITCH along) round the loop (weapon points, leaving the eye's inner side
       heading d) back along the running line through the eye, then the running part `run` (weapon points).
       returns (points, index of the last eye point)"""
    H = Vector(H)
    d, w, N = frame3(d, w)
    pts = []
    for i in range(n_eye + 1):
        f = i / n_eye
        th = math.radians(theta_s) * (1 - f)
        pts.append(H + (w * math.cos(th) + N * math.sin(th)) * RE + d * (-PITCH / 2 + PITCH * f))
    pts += [Vector(p) for p in loop]
    pts += [H - d * (PITCH / 2 + 0.03), H - d * (PITCH / 2 + 0.012), H, H + d * (PITCH / 2 + 0.012)]
    pts += [Vector(p) for p in run]
    return pts, n_eye


def rope_along(ctrl, n, step_at, prof, caps=(True, True), lay=0.12, sides=12):
    """a rope through control points: catmull (n a span), resampled by step_at; prof(s, s_total) -> (radius, lobe, tag)"""
    dense = [Vector(p) for p in catmull([tuple(p) for p in ctrl], n=n)]
    pts, sl = resample_var(dense, step_at)
    L = sl[-1]
    rad, lob, tags = [], [], []
    for s in sl:
        r, lk, t = prof(s, L)
        rad.append(r); lob.append(lk); tags.append(t)
    return rope_bms(pts, rad, lob, tags, lay, sides, caps), dense, sl


def arc_len(dense, upto):
    return sum((b - a).length for a, b in zip(dense[:upto], dense[1:upto + 1]))


def eye_prof(R, s_eye, k=0.85):
    """a rope whose first s_eye metres (the honda's eye) are a little thinner, round, easing into the strands"""
    def prof(s, L):
        if s <= s_eye: return R * k, LOBE * 0.5, 'rope'
        f = smooth01((s - s_eye) / 0.02)
        return R * (k + (1 - k) * f), LOBE * (0.5 + 0.5 * f), 'rope'
    return prof


# ================================================================================================= the lasso
RR = 0.012                 # the held rope's radius (24 mm)
LOBE = 0.16                # the strands' groove depth (x the radius)
SA = 0.018                 # the two strands of a coil loop through the fist, either side of its middle
SA3 = 0.015                # the lariat loop's two strands through the fist
YA, YF = 0.05, -0.05       # the fist's top and bottom (the box fist: 9 x 10 x 9 cm round the grip at the origin)
ZP = [0.039, 0.013, -0.013, -0.042]      # the four planes through the fist: the tail's arc, loops A, B, C; the lariat loop
LIFT = [0.0, 0.008, 0.003, -0.003]       # each plane's top arc lifted (B's highest: the hat sits on it)
BETA = [7.0, 2.0, -4.0, -3.0]            # each plane fanned about its own normal through the grip (degrees)
SPLAY = [-7.0, 0.0, 0.0]                 # each coil loop's lower part swung back (-) / forward (+) below the fist (degrees)
LOOPS = [(0.058, 0.16), (0.064, 0.175), (0.06, 0.165)]   # each coil loop's half width and depth below the fist
YAW = -30.0                # the coil turned about y: its loops face back and left (first person sees them, the side view too)
LC, LRAD, LTH = (0.0, -0.158), 0.09, -40.0   # the lariat loop: its centre and radius on plane 3, the honda's angle on it
NRE, NPITCH = 0.024, 0.022                   # the honda's eye: its radius round the spoke, its pitch


def lerp_list(L, t):
    i = max(0, min(len(L) - 2, int(math.floor(t))))
    f = t - i
    return L[i] + (L[i + 1] - L[i]) * max(0.0, min(1.0, f))


def yawed(v):
    a = math.radians(YAW)
    return Vector((v.x * math.cos(a) + v.z * math.sin(a), v.y, -v.x * math.sin(a) + v.z * math.cos(a)))


def coil_point(x, y, tau, loop=None):
    """a point of the coil drawn flat (x, y) on plane tau (fractional between planes): to the weapon frame"""
    z = lerp_list(ZP, tau)
    b = math.radians(lerp_list(BETA, tau))
    if loop is not None and y < YF:
        sg = math.radians(SPLAY[loop]) * smooth01((YF - y) / 0.04)
        dy = y - YF
        y, z = YF + dy * math.cos(sg), z + dy * math.sin(sg)
    return yawed(Vector((x * math.cos(b) - y * math.sin(b), x * math.sin(b) + y * math.cos(b), z)))


def arc_half(j, side, sa=SA):
    """plane j's top arc: side +1 the right half (top -> right foot), -1 the left half (left foot -> top)"""
    yc = YA + LIFT[j]
    angs = (90, 60, 30, 0) if side > 0 else (180, 150, 120, 90)
    return [(sa * math.cos(math.radians(a)), yc + sa * math.sin(math.radians(a))) for a in angs]


def loop_2d(j):
    wk, hk = LOOPS[j]
    return [(SA + 0.011, YF - 0.026), (0.75 * wk, YF - 0.06), (wk, YF - 0.1), (0.93 * wk, YF - hk + 0.035),
            (0.55 * wk, YF - hk + 0.006), (0.0, YF - hk), (-0.55 * wk, YF - hk + 0.007), (-0.93 * wk, YF - hk + 0.037),
            (-wk, YF - 0.1), (-0.75 * wk, YF - 0.06), (-SA - 0.011, YF - 0.026)]


TAIL = [(-0.02, -0.118, 0.079), (-0.023, -0.09, 0.078), (-0.027, -0.055, 0.074), (-0.029, -0.02, 0.068),
        (-0.029, 0.018, 0.063), (-0.025, YA - 0.003, 0.054)]


def coil_ctrl():
    """the static coil's control points: the tail end (hanging behind the fist) up and over into plane 0's arc, then
       loops A, B, C (each: the right half of its arc, down the right strand, the loop, up the left strand moving one
       plane forward in the fist); it ends in the fist on C's left strand, leaning into the lariat loop's"""
    pts = [yawed(Vector(p)) for p in TAIL]
    for x, y in arc_half(0, -1): pts.append(coil_point(x, y, 0.0))
    for j in range(3):
        for x, y in arc_half(j, 1)[1:]: pts.append(coil_point(x, y, j))
        pts.append(coil_point(SA, YA - 0.02, j)); pts.append(coil_point(SA, YF + 0.012, j))
        for x, y in loop_2d(j): pts.append(coil_point(x, y, j, loop=j))
        pts.append(coil_point(-SA, YF + 0.01, j))
        if j < 2:
            pts.append(coil_point(-SA, -0.012, j + 0.5))
            pts.append(coil_point(-SA, YA - 0.022, j + 1))
            for x, y in arc_half(j + 1, -1): pts.append(coil_point(x, y, j + 1))
        else:
            pts.append(coil_point(-SA, -0.01, 2.3))
            pts.append(coil_point(-SA, 0.02, 2.6))
    return pts


def in_fist(p):
    return math.hypot(p.x, p.z) < 0.065 and -0.045 < p.y < 0.045


def lariat_ctrl():
    """the lariat loop (node `loop`) on plane 3: the honda's eye low on the loop's right side, the loop leaving it up
       the right side into the fist, over its arc, down the left strand, round the bottom and back through the eye;
       the spoke on up beside the loop's right side into the fist. returns (points, index of the last eye point, the
       lead, the eye, the loop's centre)"""
    to3 = lambda x, y: coil_point(x, y, 3)
    th = math.radians(LTH)
    radial = Vector((math.cos(th), math.sin(th)))
    tang = Vector((-math.sin(th), math.cos(th)))                       # counter-clockwise: up the right side
    E2 = Vector(LC) + radial * (LRAD + NRE)                            # the eye's axis: outside the loop by NRE
    H = to3(*E2)
    d = (to3(*(E2 + tang * 0.01)) - H).normalized()
    w = (to3(*(E2 - radial * 0.01)) - H).normalized()
    loop = [to3(LC[0] + LRAD * math.cos(math.radians(a)), LC[1] + LRAD * math.sin(math.radians(a))) for a in (-22, -2)]
    rise = [(0.068, -0.112), (0.04, -0.085), (0.022, -0.068), (SA3, YF - 0.002), (SA3, YF + 0.01)]   # (up into the fist)
    loop += [to3(x, y) for x, y in rise] + [to3(SA3, YA - 0.02)]
    loop += [to3(x, y) for x, y in arc_half(3, 1, SA3)[::-1][1:]] + [to3(x, y) for x, y in arc_half(3, -1, SA3)[::-1][1:]]
    loop += [to3(-SA3, YA - 0.02), to3(-SA3, YF + 0.01), to3(-SA3 - 0.008, YF - 0.024)]
    for a in (162, 182, 205, 228, 250, 268):                           # down the left side, round the bottom
        f = math.radians(a)
        loop.append(to3(LC[0] + LRAD * math.cos(f), LC[1] + LRAD * math.sin(f)))
    # the spoke: on along d past the eye, up outside the loop's right side 27 mm off it, into the fist beside its
    # right strand
    run = [to3(LC[0] + (LRAD + 0.026) * math.cos(math.radians(a)), LC[1] + (LRAD + 0.026) * math.sin(math.radians(a))) for a in (-12, 4)]
    for (x0, y0), (x1, y1) in zip(rise[:2], rise[1:3]):
        t = Vector((x1 - x0, y1 - y0)).normalized()
        run.append(to3(x0 + t.y * 0.031, y0 - t.x * 0.031))
    lead2 = (SA3 + 0.03, YF - 0.004)
    run += [to3(*lead2), to3(SA3 + 0.029, -0.015), to3(SA3 + 0.027, 0.005)]
    pts, ie = loop_ctrl(H, d, w, NRE, NPITCH, loop, run)
    return pts, ie, to3(*lead2), H, to3(*LC)


def lasso():
    """THE LASSO (see the file's header)"""
    gunkit.use_style('B')
    g = BatchX('w_lasso')
    g.slot('rope', ROPE); g.slot('leather', LEATHER)
    step = lambda p: 0.025 if in_fist(p) else 0.01   # (the strands turn one side a station: lay 0.12 / 12)
    # ---- the coil (static): the frayed tail end, its whipping, then the three loops
    def tail_prof(s, L):
        if s < 0.022:                                   # the frayed end: the strands splay, the rope fattens
            f = smooth01(s / 0.022)
            return RR * (1.14 - 0.14 * f), 0.42 - (0.42 - LOBE) * f, 'rope'
        if 0.03 <= s < 0.05:                            # the whipping: a round dark band, a little proud
            return RR * 1.07, 0.0, 'leather'
        if 0.026 <= s < 0.03: return RR, LOBE * (1 - smooth01((s - 0.026) / 0.004)), 'rope'
        if 0.05 <= s < 0.056: return RR, LOBE * smooth01((s - 0.05) / 0.006), 'rope'
        return RR, LOBE, 'rope'
    bms, _, _ = rope_along(coil_ctrl(), 6, step, tail_prof)
    for tag, bm in bms.items(): add_bm(g, 'coil_wz%s__%s' % ('A' if tag == 'rope' else 'N', tag), bm)
    # ---- the lariat loop (node `loop`): one rope, the honda's eye a plain turn of it
    lctrl, ie, lead, eye, centre = lariat_ctrl()
    s_eye = arc_len([Vector(p) for p in catmull([tuple(p) for p in lctrl], n=6)], ie * 6)
    step_l = lambda p: 0.025 if in_fist(p) else (0.0075 if (p - eye).length < 0.045 else 0.01)
    bms, _, _ = rope_along(lctrl, 6, step_l, eye_prof(RR, s_eye))
    for tag, bm in bms.items(): add_bm(g, 'loop_wzA__' + tag, bm)
    g.origins['loop'] = tuple(round(x, 5) for x in lead)
    # ---- spots: the grip round the bundle, the muzzle at the loop's centre, the lead where the spoke leaves the fist
    # (the game's Beam starts there once the loop is thrown), the eye at the honda
    g.spots = {'grip': (0.0, 0.0, 0.0), 'muzzle': tuple(round(x, 4) for x in centre), 'lead': tuple(round(x, 4) for x in lead),
               'eye': tuple(round(x, 4) for x in eye)}
    top = coil_point(0.0, YA + LIFT[1] + SA, 1)
    g.hat = ((round(top.x, 4), round(top.y + RR * 0.97, 4), round(top.z, 4)), 0.065)
    return g.done()


# ================================================================================================= the thrown loop
LR = 0.0125                # 25 mm rope
LRC = 0.5375               # the ring's centre line (1.1 m across its outside: the catch radius 0.55 m)
LRE, LPITCH = 0.025, 0.023


def pj_loop():
    """the thrown loop (see the file's header)"""
    gunkit.use_style('B')
    g = BatchX('w_pj_loop', kind='proj')
    g.slot('rope', ROPE)
    H = Vector((0.0, 0.0, LRC + LRE))
    d, w = Vector((-1.0, 0.0, 0.0)), Vector((0.0, 0.0, -1.0))
    # the ring: a circle of radius LRC round the origin, leaving the eye's inner side (0, 0, LRC) heading -x
    loop = []
    for a in range(10, 351, 14):  # (every 14 degrees: catmull rounds it)
        f = math.radians(a)
        loop.append(Vector((-LRC * math.sin(f), 0.0, LRC * math.cos(f))))
    loop.append(H - d * 0.08 + w * LRE * 0.43)
    stub_end = H + d * (LPITCH / 2 + 0.034) - w * 0.05
    run = [H + d * (LPITCH / 2 + 0.03) - w * 0.012, H + d * (LPITCH / 2 + 0.034) - w * 0.032, stub_end]
    ctrl, ie = loop_ctrl(H, d, w, LRE, LPITCH, loop, run)
    s_eye = arc_len([Vector(p) for p in catmull([tuple(p) for p in ctrl], n=6)], ie * 6)
    step = lambda p: 0.009 if (p - H).length < 0.09 else 0.05
    bms, _, _ = rope_along(ctrl, 6, step, eye_prof(LR, s_eye), lay=0.54)
    for tag, bm in bms.items(): add_bm(g, 'loop_wzA__' + tag, bm)
    g.spots = {'centre': (0.0, 0.0, 0.0), 'nose': (0.0, 0.0, round(-(LRC + LR), 4)), 'eye': tuple(round(x, 4) for x in stub_end)}
    return g.done()


BUILD = {'cards': cards, 'pj_card': pj_card, 'lasso': lasso, 'pj_loop': pj_loop}
