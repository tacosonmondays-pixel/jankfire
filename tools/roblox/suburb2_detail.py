# SUBURB v2 detail pass (18 Nov 2026). The owner: "Suburb needs a bit more detail but yeah" (it was switched off on 17 Nov
# "until its finished"). What it lacked, by the photos: plain walls, empty rooms, bare lawns. This adds, in the chunky
# kit style (few big rounded shapes, flat quiet colours, one accent: the dusty teal of the front doors):
#   house fronts: lap siding lines, corner boards, a belt course between the floors, a plinth, window sills, slatted
#     shutters by the upstairs front windows, window boxes, gutters and downpipes, porch decks with a step and a lantern
#   interiors (the 8 houses you go through): a kitchen (counters, wall cupboards, a fridge), a living room (sofa, coffee
#     table, rug, a media unit, a bookcase, a floor lamp), a dining table; upstairs a bed, a wardrobe, a desk; skirting,
#     curtains, ceiling lights, pictures (two flat colour fields, nothing written)
#   yards and street: patios with a table and a parasol, a dog kennel, a washing line, a lawn mower, mailboxes on posts
#     at every front path, shrubs by the porches, fire hydrants, gates standing open
#   garages: a hoop over the door, coach lamps, a workbench and storage tubs, bikes against the wall, an air-conditioning
#     unit and a skylight on each flat roof (cover up there)
# Everything you could bump into is a real hit box (furniture stops you and takes shots: cover inside the houses); the
# rest is look only and sits against a wall, overhead or flat. No cars (the owner took them off), no text, no marks on
# any floor you fight on.
#
# The layout (suburb2_layout.py) calls add_hits() before its wall box; the kit (suburb2_models.py) calls dress() with
# arenakit after its own dressing. Both read the same item list (L.DETAIL), so look and hit boxes can't drift apart.
import math

T, UP, WALLTOP, GROOF = 1.2, 12.0, 24.0, 11.0

# the new hit boxes' looks: { Roblox material (impacts), colour (impacts), web material }. New names so the kit's own
# dressers (which pick 'cover', 'wood', 'hedge' boxes by material) leave them alone
HIT_MATS = {
    'furn': ('Fabric', 'a39a90', 'furniture'),
    'furnw': ('WoodPlanks', 'b08e6c', 'furniture'),
    'appl': ('Metal', 'e6e4df', 'metal'),
    'yardw': ('WoodPlanks', 'a3815e', 'wood'),
    'yardc': ('SmoothPlastic', 'b9bcbe', 'cover'),
    'shrub': ('Grass', '5f7a54', 'hedge'),
    'post': ('Metal', 'b7bcc0', 'metal'),
}
FURN_MAT = {'counter': 'furnw', 'fridge': 'appl', 'table': 'furnw', 'sofa': 'furn', 'ctable': 'furnw', 'media': 'furnw',
            'shelf': 'furnw', 'bed': 'furn', 'wardrobe': 'furnw', 'desk': 'furnw'}


# ================================================================ a house's own frame
def frame(h):
    """u across the house from its stair's wall, v in from its front face; returns W, D, X(u), Z(v), box(local) -> world"""
    x0, z0, x1, z1, fr, gs, ss, en = h
    W, D = x1 - x0, z1 - z0
    X = (lambda u: x0 + u) if ss == 'x-' else (lambda u: x1 - u)
    Z = (lambda v: z1 - v) if fr > 0 else (lambda v: z0 + v)

    def box(u0, v0, u1, v1, y0, y1):
        a, b, c, d = X(u0), X(u1), Z(v0), Z(v1)
        return (min(a, b), y0, min(c, d), max(a, b), y1, max(c, d))
    return W, D, X, Z, box


def furniture(h):
    """[(kind, u0, v0, u1, v1, y0, y1)] in the house's frame. Kept clear: the stair (u 1.2-6.2, v 3.2-20) and the walk in
    front of its foot, the line from the front door (u W/2 +-3) to the back door (u W/2+1 .. W/2+7), the upstairs
    landing behind the stair's top, the window over the garage roof (v 10-16 on the far wall), the upstairs spawn
    (u ~12, v 8)"""
    W = h[2] - h[0]
    if W >= 25:   # the 26-wide houses beside the garages
        return [('counter', 1.2, 24.4, 7.6, 26.8, 0, 3.0), ('counter', 1.2, 21.0, 3.6, 24.4, 0, 3.0),
                ('fridge', 7.6, 24.2, 10.2, 26.8, 0, 7.2), ('table', 6.8, 13.0, 9.6, 18.0, 0, 2.6),
                ('sofa', 21.6, 3.8, 24.8, 11.8, 0, 3.2), ('ctable', 16.2, 5.8, 19.0, 9.8, 0, 1.4),
                ('media', 17.4, 1.2, 21.0, 2.6, 0, 2.2), ('shelf', 23.2, 15.0, 24.8, 22.0, 0, 7.0),
                ('bed', 17.6, 19.6, 24.0, 26.8, UP, UP + 2.2), ('wardrobe', 22.4, 1.4, 24.8, 7.4, UP, UP + 7.6),
                ('desk', 1.2, 1.4, 4.0, 6.6, UP, UP + 2.6)]
    return [('counter', 1.2, 20.4, 11.0, 22.8, 0, 3.0), ('sofa', 18.4, 3.8, 20.8, 10.8, 0, 3.2),
            ('ctable', 14.4, 5.6, 16.8, 9.4, 0, 1.4), ('shelf', 19.2, 12.6, 20.8, 18.6, 0, 7.0),
            ('bed', 15.2, 16.4, 20.8, 22.8, UP, UP + 2.2), ('wardrobe', 18.4, 1.4, 20.8, 7.0, UP, UP + 7.6),
            ('desk', 1.2, 1.4, 4.0, 6.6, UP, UP + 2.6)]


# ================================================================ the items (hit boxes + what the kit draws for them)
def _overlaps(b, boxes, pad=0.05):
    for s in boxes:
        if b[0] < s[3] - pad and b[3] > s[0] + pad and b[1] < s[4] - pad and b[4] > s[1] + pad and b[2] < s[5] - pad and b[5] > s[2] + pad:
            return True
    return False


def _rot_overlaps(b, rots):
    """a box against turned boxes, by their bounding circles in plan (conservative)"""
    for r in rots:
        cx, cy, cz, sx, sy, sz = r[:6]
        rr = 0.5 * math.hypot(sx, sz)
        if b[1] < cy + sy / 2 and b[4] > cy - sy / 2:
            nx = min(max(cx, b[0]), b[3]); nz = min(max(cz, b[2]), b[5])
            if math.hypot(cx - nx, cz - nz) < rr - 0.05: return True
    return False


def _mirror(b):
    return (-b[3], b[1], b[2], -b[0], b[4], b[5])


def items(SOLID, ROT, HOUSES, GARAGES):
    """every detail item: dict(kind, box (world), mat, house (or None), side (+1 east / -1 west for the mirrored ones))"""
    out = []
    # furniture in the houses you go through
    for h in HOUSES:
        if not h[7]: continue
        W, D, X, Z, box = frame(h)
        for (k, u0, v0, u1, v1, y0, y1) in furniture(h):
            out.append(dict(kind=k, box=box(u0, v0, u1, v1, y0, y1), mat=FURN_MAT[k], house=h, local=(u0, v0, u1, v1, y0, y1)))
    # at every enterable house's front: a mailbox by the path's end, shrubs either side of the porch; a patio table out back
    for h in HOUSES:
        if not h[7]: continue
        W, D, X, Z, box = frame(h)
        cand = [('mailbox', (W / 2 + 2.3, -6.0, W / 2 + 3.3, -5.0, 0, 4.4), 'post'),
                ('shrub', (0.5, -1.9, 2.5, -0.1, 0, 2.4), 'shrub'),
                ('shrub', (W - 2.5, -1.9, W - 0.5, -0.1, 0, 2.4), 'shrub'),
                ('patio', (W / 2 - 5.0, D + 1.6, W / 2 - 2.0, D + 4.6, 0, 2.4), 'yardw')]
        for (k, l, m) in cand:
            b = box(*l)
            if _overlaps(b, [s[:6] for s in SOLID]) or _rot_overlaps(b, ROT): continue
            out.append(dict(kind=k, box=b, mat=m, house=h, local=l))
    # garages (west ones; mirrored east): roof clutter, a workbench behind the north one, tubs by the south one
    west = []
    for (x0, z0, x1, z1, fr) in GARAGES:
        if x0 >= 0: continue
        if fr > 0:   # the north garage: the outside stair runs up its east side; the house's window is at its west edge
            west += [('ac', (-53.0, GROOF, -45.4, -50.4, GROOF + 2.4, -43.0), 'yardc'),
                     ('skylight', (-57.6, GROOF, -31.4, -54.4, GROOF + 1.2, -27.6), 'yardc'),
                     ('bench', (-59.0, 0, -48.6, -53.0, 3.2, -46.0), 'yardw')]
        else:        # the south garage: the trampoline lands at (-54, 41); the house's window is at its west edge, z 34-40
            west += [('ac', (-53.0, GROOF, 26.0, -50.4, GROOF + 2.4, 28.4), 'yardc'),
                     ('skylight', (-52.6, GROOF, 30.4, -49.4, GROOF + 1.2, 34.0), 'yardc'),
                     ('tubs', (-48.0, 0, 30.6, -46.2, 3.0, 35.0), 'yardc')]
    # yards and street (west half; mirrored)
    west += [('kennel', (-36.6, 0, -77.4, -33.0, 3.6, -73.8), 'yardw'),
             ('linepost', (-84.9, 0, 63.4, -84.1, 7.0, 64.2), 'yardw'),
             ('linepost', (-84.9, 0, 83.4, -84.1, 7.0, 84.2), 'yardw'),
             ('mower', (-14.4, 0, 70.0, -12.4, 1.8, 72.8), 'yardc'),
             ('hydrant', (-63.4, 0, -13.6, -62.6, 2.6, -12.8), 'post'),
             ('hydrant', (-40.4, 0, 12.8, -39.6, 2.6, 13.6), 'post')]
    for (k, b, m) in west:
        for side, bb in ((-1, b), (1, _mirror(b))):
            if _overlaps(bb, [s[:6] for s in SOLID]) or _rot_overlaps(bb, ROT): continue
            out.append(dict(kind=k, box=bb, mat=m, house=None, side=side))
    return out


def add_hits(MATS, SOLID, ROT, HOUSES, GARAGES, module):
    """(the layout) the detail items into SOLID, their looks into MATS; the list kept on the layout as DETAIL"""
    MATS.update(HIT_MATS)
    its = items(SOLID, ROT, HOUSES, GARAGES)
    for it in its:
        b = it['box']
        SOLID.append((b[0], b[1], b[2], b[3], b[4], b[5], it['mat']))
    module.DETAIL = its
    return its


# ================================================================ the kit (Blender, arenakit)
TRIM, GLASS, DOOR = 'f2efe8', '2e3842', '5f8b89'
SIDING = ['dcd6c8', 'c9d0cb', 'ccd2d8', 'd9cfc6']
SHUT, GUT, DARK = '737c84', 'e4e1da', '4c5056'
WOOD, WOOD2, DECK = 'a5835f', '8a6c4e', 'b39b7c'
STONE, STONE2 = 'cfc9bd', 'bdb7ab'
CAB, CTOP, FRIDGE = 'e3ded3', 'a9a6a0', 'e9e7e2'
FWOOD, FWOOD2 = 'b08e6c', '94765a'
SOFA = ['9c958c', '8f989e', 'a6998a', '949c8e']
DUVET = ['b2bcbf', 'c6bba9', 'b8b2bd', 'b9c2b0']
RUG, CURT, CANVAS1, CANVAS2 = '9a8f81', 'cfc7b9', 'b9c6cd', '9ea78f'
TV, BOOKS = '33373c', ['8d7f72', '7d8a8f', 'a39275', '8a8f7b', '9b8580', 'b3a991']
LEAF, LEAF2, HEDGE, FLOWER = '6c8758', '617c4f', '5c7552', ['b8a2a6', 'c4b9a0', 'a9b2c2']
MAILC, POST, HYD, TUB = 'b7bcc0', '8a6c4e', '93625a', ['7f8c93', '8c9384', 'a3a8ab']
GLOW = 'fff1df'


def shade(hx, f):
    r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
    return '%02x%02x%02x' % (max(0, min(255, int(r * f))), max(0, min(255, int(g * f))), max(0, min(255, int(b * f))))


def siding_for(x0, z0):
    return SIDING[int(abs(round(x0 / 7.0)) + abs(round(z0 / 11.0))) % len(SIDING)]


def dress(L):
    """dress every detail item and the facades/interiors. call after the map's own dressing (needs bpy: arenakit)"""
    import arenakit as K
    from arenakit import cyl, cylx, cylz, ring, plate, light, Tr, Ry
    from mathutils import Vector

    def B(*a, **k):   # small detail: one bevel segment (half the triangles of the kit's two; the same look at play range)
        k.setdefault('segs', 1)
        return K.B(*a, **k)

    def blob(*a, **k):
        k.setdefault('sub', 1)
        k['sub'] = min(k['sub'], 1)
        return K.blob(*a, **k)

    # ------------------------------------------------------------ helpers on a face
    def face_strips(m, col, axis, c, sgn, a0, a1, levels, holes, M=None):
        """siding lines on a face: axis 'x' (face at z = c, facing sgn z) or 'z' (at x = c); from a0 to a1 along it;
        one strip per level y, cut round holes [(h0, h1, y0, y1)]"""
        for y in levels:
            spans = [(a0, a1)]
            for (h0, h1, hy0, hy1) in holes:
                if y + 0.22 <= hy0 or y >= hy1: continue
                nsp = []
                for (s0, s1) in spans:
                    if h1 <= s0 or h0 >= s1: nsp.append((s0, s1)); continue
                    if h0 > s0: nsp.append((s0, h0))
                    if h1 < s1: nsp.append((h1, s1))
                spans = nsp
            for (s0, s1) in spans:
                if s1 - s0 < 0.6: continue
                if axis == 'x': B(m, col, s0, y, c - 0.03 * sgn, s1, y + 0.22, c + 0.07 * sgn, bev=0.0, M=M)
                else: B(m, col, c - 0.03 * sgn, y, s0, c + 0.07 * sgn, y + 0.22, s1, bev=0.0, M=M)

    # lap siding on the upper storey only (over the belt course); the ground floor stays smooth over its plinth
    LEVELS = [y for y in [13.3 + 1.9 * k for k in range(6)] if y < 22.6]

    def room_for(wins, lo, hi):
        """which sides of each window [(u0, u1)] on a face (lo..hi between the corner boards) have room for a shutter"""
        ws = sorted(wins)
        out = []
        for i, (u0, u1) in enumerate(ws):
            left = (u0 - (ws[i - 1][1] if i > 0 else lo)) >= (5.0 if i > 0 else 2.8)
            right = ((ws[i + 1][0] if i + 1 < len(ws) else hi) - u1) >= (5.0 if i + 1 < len(ws) else 2.8)
            out.append((u0, u1, left, right))
        return out

    def shutters(m, axis, c, sgn, u0, u1, y0, y1, M=None, sides=(True, True)):
        for (a, b) in [ab for ab, ok in zip(((u0 - 2.3, u0 - 0.55), (u1 + 0.55, u1 + 2.3)), sides) if ok]:
            if axis == 'x':
                B(m, SHUT, a, y0, c, b, y1, c + 0.18 * sgn, bev=0.06, M=M)
                for k in range(1, 4):
                    yy = y0 + (y1 - y0) * k / 4
                    B(m, shade(SHUT, 0.86), a + 0.15, yy - 0.1, c + 0.1 * sgn, b - 0.15, yy + 0.1, c + 0.24 * sgn, bev=0.0, M=M)
            else:
                B(m, SHUT, c, y0, a, c + 0.18 * sgn, y1, b, bev=0.06, M=M)
                for k in range(1, 4):
                    yy = y0 + (y1 - y0) * k / 4
                    B(m, shade(SHUT, 0.86), c + 0.1 * sgn, yy - 0.1, a + 0.15, c + 0.24 * sgn, yy + 0.1, b - 0.15, bev=0.0, M=M)

    def sill(m, axis, c, sgn, u0, u1, y0, M=None):
        if axis == 'x': B(m, TRIM, u0 - 0.75, y0 - 0.42, c, u1 + 0.75, y0 - 0.05, c + 0.75 * sgn, bev=0.1, M=M)
        else: B(m, TRIM, c, y0 - 0.42, u0 - 0.75, c + 0.75 * sgn, y0 - 0.05, u1 + 0.75, bev=0.1, M=M)

    def window_box(m, axis, c, sgn, u0, u1, y0, M=None):
        """a planter under a ground-floor window: a wooden box and low muted flowers"""
        if axis == 'x':
            B(m, WOOD2, u0 - 0.2, y0 - 1.3, c, u1 + 0.2, y0 - 0.45, c + 0.95 * sgn, bev=0.12, M=M)
            B(m, LEAF2, u0, y0 - 0.55, c + 0.1 * sgn, u1, y0 - 0.15, c + 0.85 * sgn, bev=0.15, M=M)
            for i in range(3):
                uu = u0 + (u1 - u0) * (i + 0.5) / 3
                B(m, FLOWER[i % 3], uu - 0.45, y0 - 0.3, c + 0.25 * sgn, uu + 0.45, y0 + 0.15, c + 0.7 * sgn, bev=0.12, M=M)
        else:
            B(m, WOOD2, c, y0 - 1.3, u0 - 0.2, c + 0.95 * sgn, y0 - 0.45, u1 + 0.2, bev=0.12, M=M)
            B(m, LEAF2, c + 0.1 * sgn, y0 - 0.55, u0, c + 0.85 * sgn, y0 - 0.15, u1, bev=0.15, M=M)

    def gutters(m, x0, z0, x1, z1, M=None):
        for (zz, s) in ((z1, 1), (z0, -1)):
            za, zb = zz + s * 1.0, zz + s * 1.6
            B(m, GUT, x0 - 1.2, WALLTOP - 0.75, min(za, zb), x1 + 1.2, WALLTOP - 0.2, max(za, zb), bev=0.12, M=M)
            for xx in (x0 + 0.95, x1 - 0.95):   # downpipes by the corner boards, a dog-leg up to the gutter
                cyl(m, GUT, xx, 0.15, zz + s * 0.42, 0.24, WALLTOP - 1.3, segs=6, bev=0.0, M=M)
                B(m, GUT, xx - 0.24, WALLTOP - 1.35, min(zz + s * 0.2, zz + s * 1.3), xx + 0.24, WALLTOP - 0.85, max(zz + s * 0.2, zz + s * 1.3), bev=0.08, M=M)

    def corner_boards(m, x0, z0, x1, z1, M=None):
        for xx in (x0, x1):
            for zz in (z0, z1):
                B(m, TRIM, xx - 0.32, 0.0, zz - 0.32, xx + 0.32, WALLTOP - 1.0, zz + 0.32, bev=0.06, M=M)

    def belt(m, x0, z0, x1, z1, M=None):
        B(m, TRIM, x0 - 0.16, 11.25, z0 - 0.16, x1 + 0.16, 12.05, z1 + 0.16, bev=0.05, M=M)

    def lantern(m, x, y, z, nx, nz, with_light=True, M=None):
        """a wall lantern at (x, y, z) on a face whose outward normal is (nx, nz)"""
        cx, cz = x + nx * 0.45, z + nz * 0.45
        B(m, DARK, cx - 0.32, y - 0.6, cz - 0.32, cx + 0.32, y + 0.6, cz + 0.32, bev=0.08, M=M)
        B('sb_glow', GLOW, cx - 0.22, y - 0.4, cz - 0.22, cx + 0.22, y + 0.4, cz + 0.22, bev=0.04, kind='neon', M=M)
        B(m, DARK, cx - 0.42, y + 0.6, cz - 0.42, cx + 0.42, y + 0.8, cz + 0.42, bev=0.06, M=M)
        if with_light:
            p = Vector((cx + nx * 0.6, y - 0.2, cz + nz * 0.6))
            if M is not None: p = (M @ Vector((p.x, p.y, p.z, 1.0))).xyz
            light('point', p.x, p.y, p.z, (0, -1, 0), 0.7, 14, 0, 'ffdcb0')

    # ------------------------------------------------------------ the houses you go through: fronts
    def enterable_front(h):
        x0, z0, x1, z1, fr, gs, ss, en = h
        W, D, X, Z, box = frame(h)
        col = siding_for(x0, z0)
        dark = shade(col, 0.9)
        m = 'sb_house'
        inside = lambda b: b[0] >= x0 - 0.01 and b[3] <= x1 + 0.01 and b[2] >= z0 - 0.01 and b[5] <= z1 + 0.01 and b[4] <= WALLTOP + 0.01
        for b in L.SOLID:
            if b[6] != 'house' or not inside(b): continue
            thin_z = (b[5] - b[2]) < (b[3] - b[0])
            if thin_z:
                if abs(b[5] - z1) < 0.01: c, sg = z1, 1
                elif abs(b[2] - z0) < 0.01: c, sg = z0, -1
                else: continue
                a0, a1 = max(b[0], x0 + 0.5), min(b[3], x1 - 0.5)
                face_strips(m, dark, 'x', c, sg, a0, a1, [y for y in LEVELS if b[1] - 0.01 <= y and y + 0.22 <= b[4] + 0.01 and y >= 1.6], [])
                if b[1] < 0.01: B(m, shade(col, 0.82), a0, 0.0, c - 0.03 * sg, a1, 1.45, c + 0.14 * sg, bev=0.04)   # plinth
                # skirting inside
                ci = b[2] if sg > 0 else b[5]
                for yb in (0.0, UP):
                    if b[1] <= yb + 0.01 and b[4] >= yb + 0.6:
                        B('sb_inside', TRIM, max(b[0], x0 + T), yb, ci - 0.12 * sg, min(b[3], x1 - T), yb + 0.6, ci + 0.02 * sg, bev=0.0)
            else:
                if abs(b[3] - x1) < 0.01: c, sg = x1, 1
                elif abs(b[0] - x0) < 0.01: c, sg = x0, -1
                else: continue
                a0, a1 = b[2], b[5]
                face_strips(m, dark, 'z', c, sg, a0, a1, [y for y in LEVELS if b[1] - 0.01 <= y and y + 0.22 <= b[4] + 0.01 and y >= 1.6], [])
                if b[1] < 0.01: B(m, shade(col, 0.82), c - 0.03 * sg, 0.0, a0, c + 0.14 * sg, 1.45, a1, bev=0.04)
                ci = b[0] if sg > 0 else b[3]
                for yb in (0.0, UP):
                    if b[1] <= yb + 0.01 and b[4] >= yb + 0.6:
                        B('sb_inside', TRIM, ci - 0.12 * sg, yb, a0, ci + 0.02 * sg, yb + 0.6, a1, bev=0.0)
        corner_boards(m, x0, z0, x1, z1)
        belt(m, x0, z0, x1, z1)
        gutters(m, x0, z0, x1, z1)
        # the real openings: sills outside, shutters by the upstairs front windows, curtains inside
        zf = z1 if fr > 0 else z0
        mine = [o for o in L.OPENS if o[6] == 'window' and o[0] >= x0 - 0.01 and o[3] <= x1 + 0.01 and o[2] >= z0 - 0.01 and o[5] <= z1 + 0.01]
        fronts = [(o[0], o[3]) for o in mine if (o[5] - o[2]) < (o[3] - o[0]) and abs((o[5] if fr > 0 else o[2]) - zf) < 0.01]
        sides_of = {(a, b): (l, r) for (a, b, l, r) in room_for(fronts, x0 + 0.4, x1 - 0.4)}
        for o in mine:
            ox0, oy0, oz0, ox1, oy1, oz1, kind = o
            thin_z = (oz1 - oz0) < (ox1 - ox0)
            if thin_z:
                c, sg = (z1, 1) if abs(oz1 - z1) < 0.01 else (z0, -1)
                sill(m, 'x', c, sg, ox0, ox1, oy0)
                if abs(c - zf) < 0.01: shutters(m, 'x', c, sg, ox0, ox1, oy0 - 0.2, oy1 + 0.2, sides=sides_of.get((ox0, ox1), (False, False)))
                ci = c - sg * T
                for (a, b2) in ((ox0 - 1.5, ox0 - 0.45), (ox1 + 0.45, ox1 + 1.5)):
                    B('sb_inside', CURT, a, oy0 - 0.8, ci - 0.45 * sg, b2, oy1 + 0.6, ci - 0.1 * sg, bev=0.12)
                B('sb_inside', FWOOD2, ox0 - 1.7, oy1 + 0.6, ci - 0.4 * sg, ox1 + 1.7, oy1 + 0.85, ci - 0.15 * sg, bev=0.05)
            else:
                c, sg = (x1, 1) if abs(ox1 - x1) < 0.01 else (x0, -1)
                sill(m, 'z', c, sg, oz0, oz1, oy0)
                ci = c - sg * T
                for (a, b2) in ((oz0 - 1.5, oz0 - 0.45), (oz1 + 0.45, oz1 + 1.5)):
                    B('sb_inside', CURT, ci - 0.45 * sg, oy0 - 0.8, a, ci - 0.1 * sg, oy1 + 0.6, b2, bev=0.12)
                B('sb_inside', FWOOD2, ci - 0.4 * sg, oy1 + 0.6, oz0 - 1.7, ci - 0.15 * sg, oy1 + 0.85, oz1 + 1.7, bev=0.05)
        # the fake ground-floor windows (suburb2_models draws them at x0+5 and x1-5): sills and, at the front, window boxes
        sgf = 1 if fr > 0 else -1
        for (zface, sg) in ((zf, sgf), (z0 if fr > 0 else z1, -sgf)):
            for u in (x0 + 5.0, x1 - 5.0):
                sill(m, 'x', zface, sg, u - 2.2, u + 2.2, 3.5)
                if zface == zf: window_box(m, 'x', zface, sg, u - 2.2, u + 2.2, 3.5)
        # the porch: a deck, a step, a lantern by the door
        mid = (x0 + x1) / 2
        z_out = zf + sgf * 4.4
        B('sb_yard', DECK, mid - 4.4, 0.0, min(zf, z_out), mid + 4.4, 0.22, max(zf, z_out), bev=0.06)
        n = 4
        for i in range(1, n):
            xx = mid - 4.4 + 8.8 * i / n
            B('sb_yard', shade(DECK, 0.86), xx - 0.05, 0.2, min(zf, z_out), xx + 0.05, 0.25, max(zf, z_out), bev=0.0)
        z_st = z_out + sgf * 1.1
        B('sb_yard', STONE2, mid - 1.8, 0.0, min(z_out, z_st), mid + 1.8, 0.12, max(z_out, z_st), bev=0.05)
        lantern(m, mid + 3.85, 7.0, zf, 0, sgf)

    # ------------------------------------------------------------ the solid houses (cul-de-sac, head of the green): fronts
    def solid_front(col, x0, z0, x1, z1, fr, M=None):
        m = 'sb_house'
        dark = shade(col, 0.9)
        W, D = x1 - x0, z1 - z0
        zf = z1 if fr > 0 else z0
        sgn = 1 if fr > 0 else -1
        zb = z0 if fr > 0 else z1
        mid = (x0 + x1) / 2
        # the window rects house_solid_look draws (suburb2_models), as holes for the siding and places for sills
        for (zface, sg) in ((zf, sgn), (zb, -sgn)):
            n = max(1, int(W // 8))
            holes, wins = [], []
            for i in range(n):
                u = x0 + W * (i + 0.5) / n
                for (y0, y1) in ((3.5, 8.5), (14.5, 19.5)):
                    if zface == zf and y0 < 10 and abs(u - mid) < 5: continue
                    holes.append((u - 2.75, u + 2.75, y0 - 0.6, y1 + 0.6)); wins.append((u, y0, y1))
            ups = {}
            if zface == zf:
                holes.append((mid - 4.6, mid + 4.6, 0, 11.2))      # the door and the porch
                ups = {(a, b): (l, r) for (a, b, l, r) in room_for([(u - 2.6, u + 2.6) for (u, y0, y1) in wins if y0 > 10], x0 + 0.4, x1 - 0.4)}
                holes += [(a - (2.35 if l else 0.15), b + (2.35 if r else 0.15), 13.9, 20.1) for (a, b), (l, r) in ups.items()]
            face_strips(m, dark, 'x', zface, sg, x0 + 0.5, x1 - 0.5, [y for y in LEVELS if y >= 1.4], holes, M=M)
            for (u, y0, y1) in wins:
                sill(m, 'x', zface, sg, u - 2.2, u + 2.2, y0, M=M)
                if zface == zf and y0 > 10: shutters(m, 'x', zface, sg, u - 2.2, u + 2.2, y0 - 0.2, y1 + 0.2, M=M, sides=ups.get((u - 2.6, u + 2.6), (False, False)))
                if zface == zf and y0 < 10: window_box(m, 'x', zface, sg, u - 2.2, u + 2.2, y0, M=M)
        for (xface, sg) in ((x0, -1), (x1, 1)):
            n = max(1, int(D // 10))
            holes = []
            for i in range(n):
                u = z0 + D * (i + 0.5) / n
                holes.append((u - 2.55, u + 2.55, 13.9, 20.1))
                sill(m, 'z', xface, sg, u - 2.0, u + 2.0, 14.5, M=M)
            face_strips(m, dark, 'z', xface, sg, z0 + 0.5, z1 - 0.5, [y for y in LEVELS if y >= 1.4], holes, M=M)
        corner_boards(m, x0, z0, x1, z1, M=M)
        belt(m, x0, z0, x1, z1, M=M)
        gutters(m, x0, z0, x1, z1, M=M)
        lantern(m, mid + 3.85, 7.0, zf, 0, sgn, M=M)

    # ------------------------------------------------------------ furniture (the hit boxes' looks) and the rest inside
    def furn_look(it):
        h = it['house']
        W, D, X, Z, box = frame(h)
        u0, v0, u1, v1, y0, y1 = it['local']
        k = it['kind']
        mi = 'sb_inside'
        i_h = int(abs(h[0]) // 7 + abs(h[1]) // 5)

        def BL(col, a0, b0, a1, b1, c0, c1, bev=0.15, kind='plastic'):
            bb = box(a0, b0, a1, b1, c0, c1)
            B(mi, col, bb[0], bb[1], bb[2], bb[3], bb[4], bb[5], bev=bev, kind=kind)

        if k == 'counter':
            BL(CAB, u0, v0, u1, v1, y0, y1 - 0.25, bev=0.08)
            BL(CTOP, u0 - 0.05, v0 - 0.1, u1, v1, y1 - 0.25, y1, bev=0.06)
            n = max(1, int(max(u1 - u0, v1 - v0) / 2.4))
            long_u = (u1 - u0) >= (v1 - v0)
            for i in range(n):   # door fronts: a line between each and a small handle
                if long_u:
                    a = u0 + (u1 - u0) * i / n
                    BL(shade(CAB, 0.9), a + 0.04, v0 - 0.06, a + 0.12, v0 + 0.02, 0.3, y1 - 0.45, bev=0.0)
                    BL(DARK, a + (u1 - u0) / n * 0.5 - 0.3, v0 - 0.14, a + (u1 - u0) / n * 0.5 + 0.3, v0 - 0.02, y1 - 0.8, y1 - 0.62, bev=0.03)
                else:
                    a = v0 + (v1 - v0) * i / n
                    BL(shade(CAB, 0.9), u1 - 0.02, a + 0.04, u1 + 0.06, a + 0.12, 0.3, y1 - 0.45, bev=0.0)
            if long_u:   # wall cupboards over the back run, a sink in it
                BL(CAB, u0, v1 - 1.3, u1, v1, 6.4, 9.4, bev=0.1)
                BL(shade(CAB, 0.9), u0, v1 - 1.36, u1, v1 - 1.28, 6.5, 9.3, bev=0.0)
                mu = (u0 + u1) / 2
                BL('8f9499', mu - 1.2, v0 + 0.5, mu + 1.2, v0 + 1.7, y1 - 0.35, y1 + 0.02, bev=0.05)
                BL(GUT, mu - 0.12, v1 - 0.6, mu + 0.12, v1 - 0.3, y1, y1 + 1.0, bev=0.05)
            else:        # the hob on the side run
                mv = (v0 + v1) / 2
                BL(TV, u0 + 0.3, mv - 1.2, u1 - 0.3, mv + 1.2, y1 - 0.02, y1 + 0.06, bev=0.02)
        elif k == 'fridge':
            BL(FRIDGE, u0, v0, u1, v1, y0, y1, bev=0.25)
            BL(shade(FRIDGE, 0.88), u0 + 0.05, v0 - 0.04, u1 - 0.05, v0 + 0.02, 4.6, 4.7, bev=0.0)
            BL('9fa2a5', u1 - 0.55, v0 - 0.2, u1 - 0.35, v0 - 0.02, 2.4, 4.2, bev=0.04)
            BL('9fa2a5', u1 - 0.55, v0 - 0.2, u1 - 0.35, v0 - 0.02, 5.0, 6.4, bev=0.04)
        elif k == 'table':
            BL(FWOOD, u0, v0, u1, v1, y1 - 0.3, y1, bev=0.1)
            for (a, b2) in ((u0 + 0.3, v0 + 0.3), (u1 - 0.6, v0 + 0.3), (u0 + 0.3, v1 - 0.6), (u1 - 0.6, v1 - 0.6)):
                BL(FWOOD2, a, b2, a + 0.3, b2 + 0.3, 0, y1 - 0.3, bev=0.04)
            for (b0, b1) in ((v0 - 1.6, v0 - 0.3), (v1 + 0.3, v1 + 1.6)):   # chairs at its ends (look only, tucked in)
                mu = (u0 + u1) / 2
                BL(FWOOD, mu - 0.75, b0, mu + 0.75, b1, 1.5, 1.75, bev=0.08)
                BL(FWOOD2, mu - 0.75, b0 if b0 < v0 else b1 - 0.25, mu + 0.75, (b0 + 0.25) if b0 < v0 else b1, 1.75, 3.6, bev=0.08)
                for (a, c) in ((mu - 0.7, b0 + 0.05), (mu + 0.45, b0 + 0.05), (mu - 0.7, b1 - 0.3), (mu + 0.45, b1 - 0.3)):
                    BL(FWOOD2, a, c, a + 0.25, c + 0.25, 0, 1.5, bev=0.0)
        elif k == 'sofa':
            col = SOFA[i_h % len(SOFA)]
            BL(shade(col, 0.85), u0 + 0.1, v0 + 0.1, u1 - 0.1, v1 - 0.1, 0.0, 0.5, bev=0.1)
            BL(col, u0, v0, u1, v1, 0.5, 1.6, bev=0.35)
            BL(col, u1 - 1.0, v0, u1, v1, 1.6, y1, bev=0.4)                              # the back, against the wall
            BL(col, u0, v0, u1 - 0.9, v0 + 0.8, 1.6, 2.4, bev=0.35); BL(col, u0, v1 - 0.8, u1 - 0.9, v1, 1.6, 2.4, bev=0.35)
            vm = (v0 + v1) / 2
            BL(shade(col, 1.06), u0 + 0.1, v0 + 0.85, u1 - 1.0, vm - 0.05, 1.6, 2.05, bev=0.25)
            BL(shade(col, 1.06), u0 + 0.1, vm + 0.05, u1 - 1.0, v1 - 0.85, 1.6, 2.05, bev=0.25)
            BL(shade(col, 1.12), u1 - 1.6, v0 + 1.2, u1 - 0.9, v0 + 2.6, 2.0, 3.2, bev=0.3)   # a cushion
            # a rug under the coffee table and a floor lamp in the corner (look only)
            BL(RUG, u0 - 6.2, v0 + 0.4, u0 - 0.6, v1 - 0.4, 0.0, 0.06, bev=0.02)
            BL(DARK, u1 - 0.9, v0 - 1.4, u1 - 0.5, v0 - 1.0, 0.0, 5.6, bev=0.05)
            BL('e9dcc4', u1 - 1.4, v0 - 1.9, u1 - 0.0, v0 - 0.5, 5.2, 6.6, bev=0.2)
        elif k == 'ctable':
            BL(FWOOD, u0, v0, u1, v1, y1 - 0.3, y1, bev=0.12)
            BL(FWOOD2, u0 + 0.3, v0 + 0.3, u1 - 0.3, v1 - 0.3, 0.0, y1 - 0.3, bev=0.08)
            BL(BOOKS[i_h % len(BOOKS)], u0 + 0.6, v0 + 0.8, u0 + 1.6, v0 + 2.0, y1, y1 + 0.25, bev=0.03)
        elif k == 'media':
            BL(FWOOD, u0, v0, u1, v1, y0, y1, bev=0.12)
            BL(shade(FWOOD, 0.85), u0 + 0.2, v1 - 0.04, u1 - 0.2, v1 + 0.02, 0.3, y1 - 0.3, bev=0.0)
            BL(TV, u0 + 0.3, v0 + 0.3, u1 - 0.3, v0 + 0.55, y1 + 0.2, y1 + 2.6, bev=0.05)
            BL(DARK, (u0 + u1) / 2 - 0.4, v0 + 0.25, (u0 + u1) / 2 + 0.4, v0 + 0.9, y1, y1 + 0.2, bev=0.03)
        elif k == 'shelf':
            BL(FWOOD2, u0, v0, u1, v1, y0, y1, bev=0.12)
            for j, yy in enumerate((0.5, 2.6, 4.7)):
                BL(shade(FWOOD2, 0.7), u0 - 0.02, v0 + 0.25, u0 + 0.05, v1 - 0.25, yy, yy + 1.7, bev=0.0)
                n = 4
                for i in range(n):
                    a = v0 + 0.35 + (v1 - v0 - 0.7) * i / n
                    hh = 1.1 + 0.4 * ((i * 7 + j * 3) % 3) / 2
                    BL(BOOKS[(i + j + i_h) % len(BOOKS)], u0 - 0.15, a + 0.05, u0 + 0.9, a + (v1 - v0 - 0.7) / n - 0.1, yy, yy + hh, bev=0.0)
            BL('8d8a80', u0 - 0.3, v1 + 0.3, u0 + 1.0, v1 + 1.6, 0.0, 1.4, bev=0.25)   # a plant pot by it
            blob(mi, LEAF, *_w(box, u0 + 0.35, v1 + 0.95, 2.4), 1.2, sy=1.1, sub=2)
        elif k == 'bed':
            BL(FWOOD, u0, v0, u1, v1, y0, y0 + 0.9, bev=0.12)
            BL('ece9e2', u0 + 0.15, v0 + 0.15, u1 - 0.15, v1 - 0.4, y0 + 0.9, y0 + 1.7, bev=0.3)
            BL(DUVET[i_h % len(DUVET)], u0 + 0.05, v0 + 0.05, u1 - 0.05, v1 - 2.6, y0 + 1.5, y0 + 2.2, bev=0.35)
            for (a, b2) in ((u0 + 0.5, (u0 + u1) / 2 - 0.2), ((u0 + u1) / 2 + 0.2, u1 - 0.5)):
                BL('f2efe8', a, v1 - 2.3, b2, v1 - 0.7, y0 + 1.7, y0 + 2.4, bev=0.3)
            BL(FWOOD2, u0 - 0.1, v1 - 0.45, u1 + 0.1, v1, y0, y0 + 4.4, bev=0.15)   # headboard
            BL(FWOOD, u0 - 2.2, v1 - 2.0, u0 - 0.3, v1 - 0.1, y0, y0 + 1.9, bev=0.12)   # a bedside table and its lamp (look only)
            BL(DARK, u0 - 1.4, v1 - 1.2, u0 - 1.1, v1 - 0.9, y0 + 1.9, y0 + 2.9, bev=0.03)
            BL('e9dcc4', u0 - 1.8, v1 - 1.6, u0 - 0.7, v1 - 0.5, y0 + 2.8, y0 + 3.6, bev=0.15)
            BL(RUG, u0 - 4.4, v0 + 0.6, u0 - 0.4, v1 - 2.4, y0, y0 + 0.06, bev=0.02)
            # a picture over the bed: two flat colour fields in a frame, nothing written
            mu = (u0 + u1) / 2
            BL(FWOOD2, mu - 2.0, v1 - 0.15, mu + 2.0, v1 + 0.05, y0 + 5.2, y0 + 8.0, bev=0.05)
            BL(CANVAS1, mu - 1.7, v1 - 0.22, mu + 1.7, v1 - 0.1, y0 + 6.7, y0 + 7.7, bev=0.0)
            BL(CANVAS2, mu - 1.7, v1 - 0.22, mu + 1.7, v1 - 0.1, y0 + 5.5, y0 + 6.7, bev=0.0)
        elif k == 'wardrobe':
            BL(FWOOD, u0, v0, u1, v1, y0, y1, bev=0.15)
            vm = (v0 + v1) / 2
            for (b0, b1) in ((v0 + 0.15, vm - 0.05), (vm + 0.05, v1 - 0.15)):
                BL(shade(FWOOD, 1.06), u0 - 0.08, b0, u0 + 0.05, b1, y0 + 0.4, y1 - 0.4, bev=0.04)
            BL(DARK, u0 - 0.2, vm - 0.5, u0 - 0.05, vm - 0.3, y0 + 3.4, y0 + 4.6, bev=0.03)
            BL(DARK, u0 - 0.2, vm + 0.3, u0 - 0.05, vm + 0.5, y0 + 3.4, y0 + 4.6, bev=0.03)
        elif k == 'desk':
            BL(FWOOD, u0, v0, u1, v1, y1 - 0.25, y1, bev=0.08)
            BL(FWOOD2, u0, v0, u0 + 0.3, v1, y0, y1 - 0.25, bev=0.04)
            BL(FWOOD2, u1 - 0.9, v0, u1, v0 + 1.4, y0, y1 - 0.25, bev=0.06)
            BL(FWOOD2, u1 - 0.9, v1 - 1.4, u1, v1, y0, y1 - 0.25, bev=0.06)
            BL(TV, u0 + 0.6, v0 + 1.6, u0 + 1.9, v0 + 3.4, y1, y1 + 0.12, bev=0.03)      # a closed laptop
            BL('e9dcc4', u0 + 0.5, v1 - 1.3, u0 + 1.3, v1 - 0.5, y1, y1 + 1.6, bev=0.12)  # a desk lamp
            BL(FWOOD2, u1 + 0.4, (v0 + v1) / 2 - 0.8, u1 + 1.9, (v0 + v1) / 2 + 0.8, y0 + 1.5, y0 + 1.75, bev=0.06)   # chair (look only)
            BL(FWOOD2, u1 + 1.65, (v0 + v1) / 2 - 0.8, u1 + 1.9, (v0 + v1) / 2 + 0.8, y0 + 1.75, y0 + 3.5, bev=0.06)

    def _w(box, u, v, y):
        bb = box(u, v, u, v, y, y)
        return bb[0], y, bb[2]

    def interior_extras(h):
        """per house you go through: ceiling lights (the kit's lights already sit there), a picture by the sofa"""
        x0, z0, x1, z1, fr, gs, ss, en = h
        W, D, X, Z, box = frame(h)
        mi = 'sb_inside'
        mx, mz = (x0 + x1) / 2, (z0 + z1) / 2
        for yc in (UP - 0.8, WALLTOP - 0.4):
            cyl(mi, TRIM, mx, yc - 0.35, mz, 1.3, 0.35, segs=12, bev=0.0)
            cyl('sb_glow', GLOW, mx, yc - 0.42, mz, 1.0, 0.1, segs=12, bev=0.0, kind='neon')
        # a picture on the far wall, over the sofa
        uw = W - T
        vm = 7.8
        for (col, a, b2, c0, c1) in ((FWOOD2, uw - 0.2, uw + 0.05, 5.2, 8.2), (CANVAS1, uw - 0.28, uw - 0.15, 6.6, 7.9), (CANVAS2, uw - 0.28, uw - 0.15, 5.5, 6.6)):
            w = 2.0 if col == FWOOD2 else 1.7
            bb = box(a, vm - w, b2, vm + w, c0, c1)
            B(mi, col, bb[0], bb[1], bb[2], bb[3], bb[4], bb[5], bev=0.05 if col == FWOOD2 else 0.0)

    # ------------------------------------------------------------ outdoor items
    def outdoor(it):
        k, b = it['kind'], it['box']
        x0, y0, z0, x1, y1, z1 = b
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        my = 'sb_yard'
        if k == 'mailbox':
            cyl(my, POST, cx, 0, cz, 0.22, 3.4, segs=8, bev=0.05)
            B(my, MAILC, x0, 3.3, z0 - 0.3, x1, 4.1, z1 + 0.3, bev=0.3)
            B(my, shade(MAILC, 0.85), x1 - 0.05, 3.9, cz - 0.1, x1 + 0.12, 4.6, cz + 0.1, bev=0.03)   # its flag, down
        elif k == 'shrub':
            blob('sb_hedge', HEDGE, cx, 1.2, cz, 1.25, sy=0.95, sub=2, sx=1.0, sz=0.8)
            blob('sb_hedge', LEAF2, cx + 0.3, 1.8, cz - 0.1, 0.8, sy=0.9, sub=2)
        elif k == 'patio':
            h = it['house']
            W, D, X, Z, box = frame(h)
            sb = box(W / 2 - 6.0, D + 0.05, W / 2 + 8.0, D + 6.8, 0.0, 0.14)
            B(my, STONE, sb[0], sb[1], sb[2], sb[3], sb[4], sb[5], bev=0.05)
            r = 1.45
            cyl(my, WOOD, cx, y1 - 0.25, cz, r, 0.25, segs=20, bev=0.08)
            cyl(my, WOOD2, cx, 0, cz, 0.16, y1 - 0.25, segs=8, bev=0.03)
            cyl(my, WOOD2, cx, 0, cz, 0.7, 0.2, segs=12, bev=0.05)
            cyl(my, POST, cx, y1, cz, 0.1, 4.6, segs=6, bev=0.0)                       # the parasol
            from arenakit import lathe
            lathe(my, 'c9c0ae', [(0, y1 + 4.3), (3.3, y1 + 3.6), (3.3, y1 + 3.45), (0, y1 + 4.15)], cx, 0, cz, segs=12)
            for (dx, dz) in ((-2.2, 0), (2.2, 0)):                                     # two chairs (look only)
                B(my, WOOD, cx + dx - 0.7, 1.4, cz + dz - 0.7, cx + dx + 0.7, 1.65, cz + dz + 0.7, bev=0.08)
                B(my, WOOD2, cx + dx - 0.7 + (1.15 if dx > 0 else 0), 1.65, cz - 0.7, cx + dx - 0.45 + (1.15 if dx > 0 else 0), 3.3, cz + 0.7, bev=0.06)
                for (a, c) in ((-0.6, -0.6), (0.4, -0.6), (-0.6, 0.4), (0.4, 0.4)):
                    B(my, WOOD2, cx + dx + a, 0, cz + c, cx + dx + a + 0.2, 1.4, cz + c + 0.2, bev=0.0)
        elif k == 'ac':
            B(my, 'c4c6c7', x0, y0, z0, x1, y1 - 0.15, z1, bev=0.25)
            cyl(my, DARK, cx, y1 - 0.2, cz, 0.95, 0.1, segs=18, bev=0.02)
            B(my, shade('c4c6c7', 0.9), x0 + 0.2, y0, z0 - 0.06, x1 - 0.2, y1 - 0.4, z0 + 0.02, bev=0.0)
            cylx(my, '9fa2a5', x1, x1 + 2.4, y0 + 0.4, cz, 0.16, segs=8, bev=0.0)
        elif k == 'skylight':
            B(my, TRIM, x0, y0, z0, x1, y1 - 0.1, z1, bev=0.15)
            B(my, '8fa3ad', x0 + 0.35, y1 - 0.15, z0 + 0.35, x1 - 0.35, y1 + 0.02, z1 - 0.35, bev=0.05, kind='glass')
        elif k == 'bench':
            B(my, WOOD, x0, y1 - 0.3, z0, x1, y1, z1, bev=0.08)
            for xx in (x0 + 0.2, x1 - 0.5):
                for zz in (z0 + 0.2, z1 - 0.5):
                    B(my, WOOD2, xx, 0, zz, xx + 0.3, y1 - 0.3, zz + 0.3, bev=0.03)
            B(my, WOOD2, x0 + 0.2, 0.8, z0 + 0.3, x1 - 0.2, 1.0, z1 - 0.3, bev=0.04)
            B(my, '8a8f94', x0 + 0.6, y1, z0 + 0.6, x0 + 2.2, y1 + 0.9, z0 + 1.6, bev=0.12)   # a toolbox
            B(my, 'b7a98f', x0 + 0.2, y1 + 1.2, z1 - 0.12, x1 - 0.2, y1 + 4.0, z1 + 0.02, bev=0.04)   # a pegboard on the wall
            for i in range(5):
                B(my, DARK, x0 + 0.8 + i * 1.1, y1 + 2.2, z1 - 0.35, x0 + 1.0 + i * 1.1, y1 + 3.4, z1 - 0.1, bev=0.02)
        elif k == 'tubs':
            for i in range(3):
                za = z0 + i * (z1 - z0) / 3
                B(my, TUB[i % 3], x0, 0, za + 0.05, x1, 1.4, za + (z1 - z0) / 3 - 0.05, bev=0.15)
                B(my, shade(TUB[i % 3], 0.85), x0 - 0.05, 1.35, za, x1 + 0.05, 1.5, za + (z1 - z0) / 3, bev=0.06)
            B(my, TUB[1], x0 + 0.1, 1.5, z0 + 0.2, x1 - 0.1, 2.85, z0 + (z1 - z0) / 2 - 0.1, bev=0.15)
            B(my, shade(TUB[1], 0.85), x0 + 0.05, 2.85, z0 + 0.15, x1 - 0.05, 3.0, z0 + (z1 - z0) / 2 - 0.05, bev=0.06)
        elif k == 'kennel':
            B(my, WOOD, x0, 0, z0, x1, 2.4, z1, bev=0.15)
            B(my, DARK, x0 - 0.04, 0.2, cz - 0.7, x0 + 0.02, 1.8, cz + 0.7, bev=0.0)   # its doorway (a dark panel)
            pts = [(-(z0 - 0.4), 2.3), (-(z0 - 0.4), 2.55), (-cz, 3.75), (-(z1 + 0.4), 2.55), (-(z1 + 0.4), 2.3), (-cz, 3.45)]
            plate(my, '6f7276', pts, (x1 - x0) + 0.8, Tr(x0 - 0.4, 0, 0) @ Ry(math.pi / 2), bev=0.08)
            B(my, WOOD, x0, 2.35, z0 + 0.1, x1, 3.0, z1 - 0.1, bev=0.1)
        elif k == 'linepost':
            B(my, WOOD2, x0, 0, z0, x1, y1, z1, bev=0.08)
            B(my, WOOD2, cx - 1.6, y1 - 0.5, cz - 0.15, cx + 1.6, y1 - 0.2, cz + 0.15, bev=0.05)
            if cz < 70:   # (one line per pair, from the first post): three cords and some washing
                for dx in (-1.3, 0.0, 1.3):
                    B(my, 'd8d4cc', cx + dx - 0.04, y1 - 0.55, cz, cx + dx + 0.04, y1 - 0.47, cz + 20.0, bev=0.0)
                for (dx, zz, w, col) in ((-1.3, 5.0, 2.4, 'c6cdd2'), (0.0, 8.5, 2.0, 'd9cfc0'), (1.3, 12.0, 2.6, 'b8c2b1'), (0.0, 15.5, 1.8, 'cbbfb5')):
                    B(my, col, cx + dx - 0.05, y1 - 0.5 - w * 0.9, cz + zz, cx + dx + 0.05, y1 - 0.5, cz + zz + w, bev=0.0)
        elif k == 'mower':
            B(my, '6f7a6b', x0, 0.4, z0, x1, 1.3, z1 - 0.8, bev=0.25)
            for (a, c) in ((x0 + 0.1, z0 + 0.4), (x1 - 0.1, z0 + 0.4), (x0 + 0.1, z1 - 1.3), (x1 - 0.1, z1 - 1.3)):
                cylx(my, DARK, a - 0.12, a + 0.12, 0.38, c, 0.38, segs=10, bev=0.02)
            for xx in (x0 + 0.2, x1 - 0.35):
                B(my, DARK, xx, 1.1, z1 - 1.0, xx + 0.15, 3.4, z1 - 0.85, bev=0.02)
            B(my, DARK, x0 + 0.2, 3.3, z1 - 1.0, x1 - 0.2, 3.45, z1 - 0.85, bev=0.02)
        elif k == 'hydrant':
            cyl(my, HYD, cx, 0, cz, 0.42, 2.0, segs=12, bev=0.08)
            cyl(my, HYD, cx, 2.0, cz, 0.3, 0.45, segs=12, bev=0.1)
            cylx(my, HYD, cx - 0.65, cx + 0.65, 1.4, cz, 0.16, segs=8, bev=0.03)
            cyl(my, shade(HYD, 0.85), cx, 0, cz, 0.5, 0.2, segs=12, bev=0.04)

    # ------------------------------------------------------------ garages: a hoop, coach lamps, bikes
    def garage_extras():
        my = 'sb_yard'
        for (x0, z0, x1, z1, fr) in L.GARAGES:
            zf = z1 if fr > 0 else z0
            sg = 1 if fr > 0 else -1
            cx = (x0 + x1) / 2
            for xx in (x0 + 0.65, x1 - 0.65):   # coach lamps either side of the door (no light: the street lamps do it)
                B(my, DARK, xx - 0.3, 6.6, zf + sg * 0.05, xx + 0.3, 7.8, zf + sg * 0.55, bev=0.06)
                B('sb_glow', GLOW, xx - 0.2, 6.8, zf + sg * 0.15, xx + 0.2, 7.6, zf + sg * 0.5, bev=0.03, kind='neon')
            if fr > 0:   # a hoop on the north garages' parapet, over the door
                B(my, 'e6e4de', cx - 2.2, 10.0, zf + sg * 0.15, cx + 2.2, 12.9, zf + sg * 0.45, bev=0.1)
                B(my, shade('e6e4de', 0.8), cx - 0.9, 10.4, zf + sg * 0.42, cx + 0.9, 11.6, zf + sg * 0.5, bev=0.0)
                B(my, DARK, cx - 0.18, 10.15, zf + sg * 0.45, cx + 0.18, 10.45, zf + sg * 1.1, bev=0.03)
                ring(my, '8a8f94', cx, 10.2, 10.38, zf + sg * 1.85, 0.75, 0.9, segs=18)
            else:        # bikes against the south garages' street-side corner (look only, flat to the wall)
                xw = x1 if x0 < 0 else x0          # (the wall facing the passage beside it: x1 on the west, x0 on the east)
                sx = 1 if x0 < 0 else -1
                for i, zz in enumerate((zf - sg * 15.0, zf - sg * 18.0)):
                    for dz in (-1.15, 1.15):
                        cylx(my, DARK, xw + sx * (0.3 + 0.35 * i) - 0.06, xw + sx * (0.3 + 0.35 * i) + 0.06, 1.1, zz + dz, 1.05, segs=16, bev=0.0)
                    B(my, ['7d8a8f', '8c8476'][i], xw + sx * (0.3 + 0.35 * i) - 0.06, 1.1, zz - 1.1, xw + sx * (0.3 + 0.35 * i) + 0.06, 1.3, zz + 1.1, bev=0.0)
                    B(my, ['7d8a8f', '8c8476'][i], xw + sx * (0.3 + 0.35 * i) - 0.06, 1.1, zz - 0.2, xw + sx * (0.3 + 0.35 * i) + 0.06, 2.4, zz + 0.0, bev=0.0)
                    B(my, DARK, xw + sx * (0.3 + 0.35 * i) - 0.25, 2.4, zz - 0.45, xw + sx * (0.3 + 0.35 * i) + 0.25, 2.55, zz + 0.25, bev=0.03)
            # roof: a vent pipe
            cyl(my, '9fa2a5', x0 + 1.4, GROOF, (z0 + z1) / 2, 0.3, 1.8, segs=10, bev=0.05)

    # ------------------------------------------------------------ gates standing open against the fences
    def gates():
        mf = 'sb_fence'
        runs = {}   # (the gate gaps sit between fence runs on the same line)
        for (x0, z0, x1, z1) in L.FENCES:
            along_x = (x1 - x0) > (z1 - z0)
            key = ('x', round((z0 + z1) / 2, 2)) if along_x else ('z', round((x0 + x1) / 2, 2))
            runs.setdefault(key, []).append((x0, x1) if along_x else (z0, z1))
        for (ax, c), spans in runs.items():
            spans.sort()
            for (a, b), (a2, b2) in zip(spans, spans[1:]):
                gap = a2 - b
                if not (3.0 < gap < 8.0): continue
                # the leaf swung open along the fence's line, beside the far post (on the outer side, 0.3 off)
                g0, g1 = a2, a2 + gap * 0.9
                if ax == 'z':
                    B(mf, TRIM, c + 0.35, 0.9, g0 + 0.1, c + 0.55, 1.25, g1, bev=0.0)
                    B(mf, TRIM, c + 0.35, 2.4, g0 + 0.1, c + 0.55, 2.75, g1, bev=0.0)
                    n = int((g1 - g0) / 0.95)
                    for i in range(n):
                        u = g0 + (g1 - g0) * (i + 0.5) / n
                        B(mf, TRIM, c + 0.38, 0.15, u - 0.2, c + 0.52, 3.0, u + 0.2, bev=0.0)
                else:
                    B(mf, TRIM, g0 + 0.1, 0.9, c + 0.35, g1, 1.25, c + 0.55, bev=0.0)
                    B(mf, TRIM, g0 + 0.1, 2.4, c + 0.35, g1, 2.75, c + 0.55, bev=0.0)
                    n = int((g1 - g0) / 0.95)
                    for i in range(n):
                        u = g0 + (g1 - g0) * (i + 0.5) / n
                        B(mf, TRIM, u - 0.2, 0.15, c + 0.38, u + 0.2, 3.0, c + 0.52, bev=0.0)

    # ------------------------------------------------------------ go
    M_bulb = lambda cx, cz, face: Tr(cx, 0, cz) @ Ry(math.pi / 2 - face)   # (suburb2_models.M_bulb: the bulb houses' frame)
    for h in L.HOUSES:
        x0, z0, x1, z1, fr, gs, ss, en = h
        if en:
            enterable_front(h)
            interior_extras(h)
        else:
            solid_front(siding_for(x0, z0), x0, z0, x1, z1, fr)
    for (cx, cz, face, w, dpt) in L.BULB_HOUSES:
        solid_front(siding_for(cx, cz), -w / 2, -dpt / 2, w / 2, dpt / 2, +1, M=M_bulb(cx, cz, face))
    for it in L.DETAIL:
        if it['house'] is not None and it['kind'] in FURN_MAT: furn_look(it)
        else: outdoor(it)
    garage_extras()
    gates()
