# High Noon's western town, rebuilt as a chunky kit (20 Nov 2026). The owner, on the in-game scene: "can you fix the
# scene scenery too? like sprucent up the buildings ... theres these like long rectangle strips ... make those go bye
# bye.. Sicne youre modeling actual western buildsing, can you add blank npcs that are blokey and have cowboy gear like
# hiding in windows and reacting in the backgorund maybe? make two versions so I can see side by side"
#   A  a tight timber main street: false fronts, porches, a two-storey saloon facing the duel, onlookers in its windows
#   B  a wider adobe border town: thick plaster, vigas, an arcade and balconies, onlookers on porches and balconies
# One headless Blender run per version (arenakit: bevelled flat-colour pieces merged into a few big meshes, named
# "<model><n>__<kind>_<hex>" so the game paints each from its name; kinds planks / wood / plaster / shingle / metal /
# fabric / plastic -> WoodPlanks, Wood, Plaster, RoofShingles, Metal, Fabric, SmoothPlastic):
#   blender -b --factory-startup -P highnoon_town.py -- <out dir> A|B [--previews]
# writes <out>/highnoon_town_<v>.glb, <out>/highnoon_town_<v>.json (the onlookers' spots) and preview renders from the
# scene's own lenses. Coordinates: Roblox studs local to the scene's ORIGIN (FinisherScene): the street runs along z,
# the killer stands at (0, 0, 0) facing -z, the victim at (0, 0, -17) facing +z, west is -x. The east side stays open
# from z 9 to z -25: the scene's two side lenses (THE WIDE, FAR SHOT) look west across it from x 25.
import bpy, sys, os, math, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import arenakit as K
from mathutils import Matrix, Vector

ARGS = K.ARGS
OUT = ARGS[0]
VER = ARGS[1] if len(ARGS) > 1 else 'A'
os.makedirs(OUT, exist_ok=True)
# (the factory scene's default cube, camera and light would ride into the .glb: the first town import had the cube at
# the killer's mark)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
rnd = random.Random(1885 if VER == 'A' else 1846)

# ---------------------------------------------------------------- the palette (quiet: weathered wood, faded paint)
C = dict(wl='b39069', wm='8c6a47', wd='5c4532', wg='7d766c', red='8a4c3e', teal='50706b', och='b38f5c', cream='d6c6a3',
         pl='d8bd92', pl2='c6a074', pl3='e0cfae', roof='6a5545', dark='241b15', iron='4b4a47', sand='c9a978', rock='a57d5c',
         cactus='6f7f4f', hay='c7aa62', water='5c7a80', sign='ddcca8', signb='7a5b3d', cloth='9b8a72')
FX = 11.0 if VER == 'A' else 14.5   # the front walls' distance from the street's middle
SPOTS = []                           # the onlookers: { at = (x, y, z) feet, face = (dx, dz), kind, floor }


def Bw(model, col, s, d0, y0, z0, d1, y1, z1, bev=0.18, kind='planks', segs=1):
    """a box in a facade's frame: d = depth behind the front wall (negative = toward the street), side s = -1 west
    (front faces +x) / +1 east (front faces -x)"""
    K.B(model, C.get(col, col), s * (FX + d0), y0, z0, s * (FX + d1), y1, z1, bev=bev, kind=kind, segs=segs)


def wall_with_holes(model, col, s, d0, d1, y0, y1, z0, z1, holes, kind='planks'):
    """a wall panel with rectangular openings [(za, zb, ya, yb)]: split into cells, solid cells merged along each row"""
    zs = sorted({z0, z1} | {h[0] for h in holes} | {h[1] for h in holes})
    ys = sorted({y0, y1} | {h[2] for h in holes} | {h[3] for h in holes})
    for j in range(len(ys) - 1):
        ya, yb = ys[j], ys[j + 1]
        run = None
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]
            cz, cy = (za + zb) / 2, (ya + yb) / 2
            hole = any(h[0] <= cz <= h[1] and h[2] <= cy <= h[3] for h in holes)
            if not hole:
                run = (run[0], zb) if run else (za, zb)
            elif run:
                Bw(model, col, s, d0, ya, run[0], d1, yb, run[1], bev=0.06, kind=kind); run = None
        if run:
            Bw(model, col, s, d0, ya, run[0], d1, yb, run[1], bev=0.06, kind=kind)


def window(model, s, za, zb, ya, yb, frame='wd', shutters=None, muntins=True, deep=0.8):
    """a window's frame proud of the wall: head, sill (wider), jambs; muntins when it's glazed (an onlooker's is open)"""
    Bw(model, frame, s, -0.28, yb, za - 0.35, 0.25, yb + 0.45, zb + 0.35, bev=0.08, kind='wood')        # head
    Bw(model, frame, s, -0.42, ya - 0.32, za - 0.45, 0.25, ya, zb + 0.45, bev=0.08, kind='wood')        # sill
    Bw(model, frame, s, -0.22, ya, za - 0.3, 0.25, yb, za, bev=0.05, kind='wood')                       # jambs
    Bw(model, frame, s, -0.22, ya, zb, 0.25, yb, zb + 0.3, bev=0.05, kind='wood')
    if muntins:
        Bw(model, 'dark', s, 0.35, ya, za, 0.45, yb, zb, bev=0.0, kind='plastic')                       # the dark pane
        Bw(model, frame, s, 0.2, ya, (za + zb) / 2 - 0.09, 0.35, yb, (za + zb) / 2 + 0.09, bev=0.03, kind='wood')
        Bw(model, frame, s, 0.2, (ya + yb) / 2 - 0.09, za, 0.35, (ya + yb) / 2 + 0.09, zb, bev=0.03, kind='wood')
    if shutters:
        w = (zb - za) * 0.5
        Bw(model, shutters, s, -0.32, ya + 0.1, za - 0.35 - w, -0.12, yb - 0.1, za - 0.4, bev=0.06)
        Bw(model, shutters, s, -0.32, ya + 0.1, zb + 0.4, -0.12, yb - 0.1, zb + 0.35 + w, bev=0.06)


def porch(model, s, zl, zh, roof_y, deck='wm', post='wd', roof='roof', posts_every=4.2, balcony=False):
    """the boardwalk and its roof on posts (balcony: the roof is a deck with a rail, for the floor above)"""
    Bw(model, deck, s, -3.3, 0.0, zl, 0.05, 0.62, zh, bev=0.1)                       # the deck
    Bw(model, 'wd', s, -3.35, 0.0, zl, -3.05, 0.5, zh, bev=0.06, kind='wood')        # its skirt
    n = max(2, int(round((zh - zl) / posts_every)) + 1)
    for i in range(n):
        z = zl + 0.4 + (zh - zl - 0.8) * i / (n - 1)
        Bw(model, post, s, -3.15, 0.62, z - 0.3, -2.55, roof_y, z + 0.3, bev=0.08, kind='wood')
        # brackets under the beam
        Bw(model, post, s, -2.95, roof_y - 1.1, z - 0.9, -2.75, roof_y - 0.85, z + 0.9, bev=0.05, kind='wood')
    Bw(model, post, s, -3.3, roof_y - 0.5, zl, -2.4, roof_y, zh, bev=0.08, kind='wood')     # the beam
    if balcony:
        Bw(model, deck, s, -3.4, roof_y, zl, 0.05, roof_y + 0.35, zh, bev=0.08)
        Bw(model, post, s, -3.35, roof_y + 1.35, zl, -3.05, roof_y + 1.6, zh, bev=0.06, kind='wood')   # top rail
        Bw(model, post, s, -3.35, roof_y + 0.35, zl, -3.15, roof_y + 0.6, zh, bev=0.04, kind='wood')   # bottom rail
        m = max(3, int((zh - zl) / 1.15))
        for i in range(m + 1):
            z = zl + 0.2 + (zh - zl - 0.4) * i / m
            Bw(model, post, s, -3.32, roof_y + 0.35, z - 0.1, -3.12, roof_y + 1.4, z + 0.1, bev=0.03, kind='wood')
    else:
        # a sloping roof from the wall to the beam
        p = Vector((s * FX, roof_y + 1.0, 0))
        a = s * math.atan2(1.0, 3.6)
        M = K.Tr(p.x, p.y, 0) @ K.Rz(a) @ K.Tr(-p.x, -p.y, 0)
        x0, x1 = sorted((s * (FX + 0.1), s * (FX - 3.75)))
        K.B(model, C[roof], x0, roof_y + 0.85, zl - 0.2, x1, roof_y + 1.15, zh + 0.2, bev=0.06, kind='shingle', M=M)
        Bw(model, 'wd', s, -3.75, roof_y - 0.05, zl - 0.2, -3.5, roof_y + 0.45, zh + 0.2, bev=0.05, kind='wood')  # fascia


def false_front(model, s, zl, zh, h, ff, col, step=True, sign=None):
    """the tall board front over the roof line, a cornice on top, a plain sign board (no words)"""
    if step:
        Bw(model, col, s, -0.05, h, zl, 0.55, h + ff * 0.72, zh)
        Bw(model, col, s, -0.05, h + ff * 0.72, zl + (zh - zl) * 0.22, 0.55, h + ff, zh - (zh - zl) * 0.22)
        Bw(model, 'wd', s, -0.35, h + ff * 0.72 - 0.05, zl - 0.25, 0.6, h + ff * 0.72 + 0.4, zl + (zh - zl) * 0.22 + 0.2, bev=0.08, kind='wood')
        Bw(model, 'wd', s, -0.35, h + ff * 0.72 - 0.05, zh - (zh - zl) * 0.22 - 0.2, 0.6, h + ff * 0.72 + 0.4, zh + 0.25, bev=0.08, kind='wood')
        Bw(model, 'wd', s, -0.4, h + ff - 0.05, zl + (zh - zl) * 0.22 - 0.3, 0.6, h + ff + 0.5, zh - (zh - zl) * 0.22 + 0.3, bev=0.08, kind='wood')
    else:
        Bw(model, col, s, -0.05, h, zl, 0.55, h + ff, zh)
        Bw(model, 'wd', s, -0.45, h + ff - 0.05, zl - 0.3, 0.6, h + ff + 0.55, zh + 0.3, bev=0.08, kind='wood')
        for z in (zl + 0.6, zh - 0.6):   # cornice brackets
            Bw(model, 'wd', s, -0.4, h + ff - 0.8, z - 0.2, -0.05, h + ff - 0.05, z + 0.2, bev=0.05, kind='wood')
    if sign:
        y0, y1 = h + 0.45, h + ff * 0.62
        Bw(model, sign, s, -0.3, y0, zl + 0.9, -0.05, y1, zh - 0.9, bev=0.06, kind='plastic')
        Bw(model, 'signb', s, -0.42, y0 - 0.15, zl + 0.75, -0.25, y0 + 0.12, zh - 0.75, bev=0.05, kind='wood')
        Bw(model, 'signb', s, -0.42, y1 - 0.12, zl + 0.75, -0.25, y1 + 0.15, zh - 0.75, bev=0.05, kind='wood')
        # a plain painted band across the board where letters would be (no words)
        Bw(model, 'signb', s, -0.34, (y0 + y1) / 2 - 0.22, zl + 1.8, -0.28, (y0 + y1) / 2 + 0.22, zh - 1.8, bev=0.0, kind='plastic')


def onlooker(s, z, y, d, kind, floor):
    """a spot for a blank cowboy: feet at (x, y, z), facing the street"""
    SPOTS.append({'at': [round(s * (FX + d), 3), round(y, 3), round(z, 3)], 'face': [-s, 0], 'kind': kind, 'floor': floor})


RD = 6.4   # a timber building's room: from the front wall's back (0.7) to its dark back wall, studs
OD = 3.4   # where an onlooker stands in it (its feet), from the front. (20 Nov, the clip check: the clips swing the body
           # well off its spot - the knockdown's lowest puts the head 2.3 studs forward, the guard leans it 2 back - so
           # the room holds that swing both ways: ~0.4 clear in front at the duck, ~0.6 behind at the guard)


def timber(model, s, zl, zh, two=False, col='wl', ff=3.4, sign='sign', style='store', npc=()):
    """a timber false-front building: hollow behind its front wall (the windows show a dark room; an onlooker can
    stand in it), a porch or a balcony, a pitched roof behind the false front"""
    D = 11.0
    h = 16.6 if two else 9.6
    Bw(model, 'rock', s, -0.2, 0, zl, D, 0.7, zh, bev=0.15, kind='plastic')               # the footing
    # the openings in the front wall: a door in the middle, a window each side; upstairs, two or three windows
    w = zh - zl
    zc = (zl + zh) / 2
    dh = 1.6 if style == 'saloon' else 1.25
    door = (zc - dh, zc + dh, 0.7, 7.4 if style == 'saloon' else 7.2)
    # a window each side of the door, as wide as the room there allows (narrow fronts get narrow windows)
    room = w / 2 - dh - 0.8 - 0.9
    ww = min(2.8, room)
    wins = []
    if ww >= 1.3:
        a = zl + 0.9 + (room - ww) / 2
        wins = [(a, a + ww, 2.9, 6.5), (zh - (a - zl) - ww, zh - (a - zl), 2.9, 6.5)]
    holes = [door] + wins
    ups = []
    if two:
        n = 3 if w >= 11 else 2
        for i in range(n):
            c = zl + w * (i + 1) / (n + 1)
            ups.append((c - 1.15, c + 1.15, 10.4, 14.2))
        holes += ups
    wall_with_holes(model, col, s, 0.0, 0.7, 0.7, h, zl, zh, holes)
    # the room behind: a dark back wall, the floor between, side panels; the body behind that. (RD deep: 1.9 at first,
    # 20 Nov - an onlooker's hat brim alone is 2 studs across, so their poses passed through the walls; the owner: "the
    # people are clipped into the buildings")
    Bw(model, 'dark', s, RD, 0.7, zl, RD + 0.4, h, zh, bev=0.0, kind='plastic')
    Bw(model, 'wd', s, 0.7, 0.7, zl, RD, 0.9, zh, bev=0.0)
    Bw(model, col, s, 0.7, 0.7, zl, RD, h, zl + 0.3, bev=0.0)          # (the room's ends: the wall's colour outside)
    Bw(model, col, s, 0.7, 0.7, zh - 0.3, RD, h, zh, bev=0.0)
    if two:
        Bw(model, 'wd', s, 0.7, 8.2, zl, RD, 8.6, zh, bev=0.0)                             # the upstairs floor
    Bw(model, col, s, RD + 0.4, 0.7, zl, D, h - 0.3, zh, bev=0.25)                          # the body
    # the pitched roof behind the false front (its ridge runs back from the street, at h + rise)
    rise = 2.2
    p = (s * (FX + (D + 0.6) / 2), h + rise)
    for side in (-1, 1):
        a = side * math.atan2(rise, w / 2)
        M = K.Tr(p[0], p[1], zc) @ K.Rx(a) @ K.Tr(-p[0], -p[1], -zc)
        zz = (zc, zh + 0.5) if side > 0 else (zl - 0.5, zc)
        x0, x1 = sorted((s * (FX + 0.5), s * (FX + D + 0.5)))
        K.B(model, C['roof'], x0, h + rise - 0.15, zz[0], x1, h + rise + 0.2, zz[1], bev=0.06, kind='shingle', M=M)
    # corner boards, a plinth board
    for z in (zl, zh - 0.5):
        Bw(model, 'wd', s, -0.18, 0.7, z, 0.3, h, z + 0.5, bev=0.06, kind='wood')
    Bw(model, 'wd', s, -0.15, 0.7, zl, 0.3, 1.2, zh, bev=0.05, kind='wood')
    # the door
    za, zb, ya, yb = door
    Bw(model, 'wd', s, -0.3, yb, za - 0.4, 0.25, yb + 0.5, zb + 0.4, bev=0.08, kind='wood')
    Bw(model, 'wd', s, -0.25, ya, za - 0.32, 0.25, yb, za, bev=0.05, kind='wood')
    Bw(model, 'wd', s, -0.25, ya, zb, 0.25, yb, zb + 0.32, bev=0.05, kind='wood')
    if style == 'saloon':   # batwing doors, half height, standing open a little
        for (a0, a1) in ((za + 0.05, zc - 0.05), (zc + 0.05, zb - 0.05)):
            Bw(model, 'wm', s, 0.1, 2.6, a0, 0.3, 5.8, a1, bev=0.08)
            Bw(model, 'wd', s, 0.05, 5.5, a0, 0.32, 5.9, a1, bev=0.05, kind='wood')
    elif 'door' not in npc:
        Bw(model, 'wd', s, 0.35, ya, za, 0.55, yb, zb, bev=0.06)                           # a shut door
        Bw(model, 'iron', s, 0.15, 3.6, zb - 0.55, 0.35, 3.85, zb - 0.3, bev=0.04, kind='metal')
    for i, (a, b, c, d) in enumerate(wins):
        open_ = ('win%d' % i) in npc
        window(model, s, a, b, c, d, shutters=None if style == 'saloon' else ('wm' if col != 'wm' else 'wd'), muntins=not open_)
        if open_:
            onlooker(s, (a + b) / 2, 0.9, OD, 'window', 0)
    for i, (a, b, c, d) in enumerate(ups):
        open_ = ('up%d' % i) in npc
        window(model, s, a, b, c, d, muntins=not open_)
        if open_:
            onlooker(s, (a + b) / 2, 8.6, OD, 'window', 1)
    if 'door' in npc:
        onlooker(s, zc, 0.9, OD, 'door', 0)
    false_front(model, s, zl, zh, h, ff if not two else 2.6, col, step=(rnd.random() < 0.5) and not two, sign=sign)
    porch(model, s, zl, zh, 8.0 if two else 7.6, balcony=two)
    return h


def adobe(model, s, zl, zh, two=False, col='pl', npc=(), arcade=True, balcony=False):
    """an adobe building: thick plaster with soft edges, vigas out of the front, deep windows with wood lintels, an
    arcade of plaster piers and arches in front (or a wooden balcony on posts)"""
    D = 11.0
    h = 15.8 if two else 9.4
    w = zh - zl
    zc = (zl + zh) / 2
    door = (zc - 1.3, zc + 1.3, 0.4, 7.0)
    wins = [(zl + 1.6, zl + 3.8, 2.8, 6.2), (zh - 3.8, zh - 1.6, 2.8, 6.2)]
    ups = []
    if two:
        n = 3 if w >= 11 else 2
        for i in range(n):
            c = zl + w * (i + 1) / (n + 1)
            ups.append((c - 1.0, c + 1.0, 9.8, 13.4))
    wall_with_holes(model, col, s, 0.0, 0.9, 0.0, h, zl, zh, [door] + wins + ups, kind='plaster')
    Bw(model, 'dark', s, 2.7, 0.0, zl, 3.1, h, zh, bev=0.0, kind='plastic')
    Bw(model, 'pl2', s, 0.9, 0.0, zl, 2.7, 0.3, zh, bev=0.0, kind='plaster')
    Bw(model, col, s, 0.9, 0.0, zl, 2.7, h, zl + 0.35, bev=0.0, kind='plaster')
    Bw(model, col, s, 0.9, 0.0, zh - 0.35, 2.7, h, zh, bev=0.0, kind='plaster')
    if two:
        Bw(model, 'wd', s, 0.9, 7.9, zl, 2.7, 8.3, zh, bev=0.0)
    Bw(model, col, s, 3.1, 0.0, zl, D, h, zh, bev=0.5, kind='plaster', segs=2)
    # the parapet, soft and stepped, a band of plaster
    Bw(model, col, s, -0.1, h, zl, 1.2, h + 1.4, zh, bev=0.45, kind='plaster', segs=2)
    Bw(model, col, s, -0.1, h + 1.4, zc - w * 0.18, 1.2, h + 2.4, zc + w * 0.18, bev=0.45, kind='plaster', segs=2)
    Bw(model, 'pl2', s, -0.25, 0.0, zl - 0.1, 0.4, 1.0, zh + 0.1, bev=0.3, kind='plaster', segs=2)   # the base band
    # vigas: the roof beams' ends out of the wall
    m = max(3, int(w / 2.2))
    for i in range(m):
        z = zl + 1.0 + (w - 2.0) * i / (m - 1)
        K.cylx('vigas', C['wd'], s * (FX - 1.0), s * (FX + 0.6), h - 1.0, z, 0.32, segs=10, bev=0.08, kind='wood')
    # canales (spouts)
    for z in (zl + 1.2, zh - 1.2):
        Bw(model, 'wm', s, -1.3, h + 0.2, z - 0.3, 0.2, h + 0.55, z + 0.3, bev=0.06, kind='wood')
    # the door: a heavy plank door set deep, a wood lintel
    za, zb, ya, yb = door
    Bw(model, 'wd', s, -0.25, yb, za - 0.6, 0.95, yb + 0.55, zb + 0.6, bev=0.1, kind='wood')
    if 'door' not in npc:
        Bw(model, 'wm', s, 0.6, ya, za, 0.85, yb, zb, bev=0.06)
        for k in range(3):
            Bw(model, 'iron', s, 0.5, 1.4 + k * 2.1, za + 0.2, 0.62, 1.6 + k * 2.1, zb - 0.2, bev=0.03, kind='metal')
    else:
        onlooker(s, zc, 0.3, 1.5, 'door', 0)
    for i, (a, b, c, d) in enumerate(wins):
        Bw(model, 'wd', s, -0.25, d, a - 0.5, 0.95, d + 0.45, b + 0.5, bev=0.08, kind='wood')     # lintel
        Bw(model, 'pl2', s, -0.35, c - 0.35, a - 0.3, 0.95, c, b + 0.3, bev=0.15, kind='plaster')   # sill
        if ('win%d' % i) in npc:
            onlooker(s, (a + b) / 2, 0.3, 1.7, 'window', 0)
        else:   # a turned wood grille
            Bw(model, 'dark', s, 0.75, c, a, 0.85, d, b, bev=0.0, kind='plastic')
            for k in range(4):
                zz = a + (b - a) * (k + 0.5) / 4
                K.cyl('grille', C['wd'], s * (FX + 0.5), c, zz, 0.09, d - c, segs=8, bev=0.03, kind='wood')
    for i, (a, b, c, d) in enumerate(ups):
        Bw(model, 'wd', s, -0.25, d, a - 0.45, 0.95, d + 0.4, b + 0.45, bev=0.08, kind='wood')
        if ('up%d' % i) in npc:
            onlooker(s, (a + b) / 2, 8.3, 1.7, 'window', 1)
        else:
            Bw(model, 'dark', s, 0.75, c, a, 0.85, d, b, bev=0.0, kind='plastic')
            Bw(model, 'teal', s, -0.2, c, a - 1.0, 0.0, d, a - 0.1, bev=0.06)            # shutters, faded
            Bw(model, 'teal', s, -0.2, c, b + 0.1, 0.0, d, b + 1.0, bev=0.06)
    if arcade:
        # piers and arches: a portal along the front (the deck is beaten earth, a step of plaster)
        Bw(model, 'pl2', s, -3.6, 0.0, zl, 0.0, 0.35, zh, bev=0.2, kind='plaster')
        n = max(2, int(round(w / 4.4)))
        piers = [zl + 0.5 + (w - 1.0) * i / n for i in range(n + 1)]
        top = 7.6
        for z in piers:
            Bw(model, col, s, -3.6, 0.35, z - 0.5, -2.6, top, z + 0.5, bev=0.25, kind='plaster', segs=2)
        for a, b in zip(piers, piers[1:]):
            # an opening between piers: a lintel with soft corner fillets
            Bw(model, col, s, -3.6, top - 1.6, a + 0.5, -2.6, top, b - 0.5, bev=0.3, kind='plaster', segs=2)
            Bw(model, col, s, -3.6, top - 2.4, a + 0.5, -2.6, top - 1.5, a + 1.3, bev=0.3, kind='plaster', segs=2)
            Bw(model, col, s, -3.6, top - 2.4, b - 1.3, -2.6, top - 1.5, b - 0.5, bev=0.3, kind='plaster', segs=2)
        # the portal's flat roof: vigas and a plank deck on top
        Bw(model, 'wd', s, -3.8, top, zl - 0.1, 0.0, top + 0.5, zh + 0.1, bev=0.1, kind='wood')
        if balcony:
            Bw(model, 'wm', s, -3.8, top + 0.5, zl, 0.0, top + 0.75, zh, bev=0.06)
            Bw(model, 'wd', s, -3.75, top + 1.75, zl, -3.45, top + 2.0, zh, bev=0.06, kind='wood')
            m2 = max(3, int(w / 1.2))
            for i in range(m2 + 1):
                z = zl + 0.2 + (w - 0.4) * i / m2
                Bw(model, 'wd', s, -3.72, top + 0.75, z - 0.11, -3.5, top + 1.8, z + 0.11, bev=0.03, kind='wood')
    return h


# ---------------------------------------------------------------- props
def barrel(x, z, col='wm', y0=0.0):
    K.lathe('barrel', C[col], [(0, 0), (0.62, 0), (0.75, 0.6), (0.78, 1.0), (0.75, 1.4), (0.62, 2.0), (0, 2.0)], x, y0, z, segs=16, kind='wood')
    for y in (0.35, 1.65):
        K.ring('barrel', C['iron'], x, y0 + y, y0 + y + 0.14, z, 0.0, 0.8, segs=16, kind='metal')


def crate(x, z, size=1.4, yaw=0.0):
    K.Bc('crate', C['wl'], x, size / 2, z, size, size, size, bev=0.08, kind='planks', yaw=yaw)
    K.Bc('crate', C['wd'], x, size / 2, z, size + 0.06, 0.25, size + 0.06, bev=0.05, kind='wood', yaw=yaw)


def trough(x, z, along='z'):
    if along == 'z':
        K.B('trough', C['wd'], x - 0.7, 0, z - 1.8, x + 0.7, 1.0, z + 1.8, bev=0.1, kind='wood')
        K.B('trough', C['water'], x - 0.55, 0.85, z - 1.65, x + 0.55, 0.92, z + 1.65, bev=0.0, kind='plastic')
    else:
        K.B('trough', C['wd'], x - 1.8, 0, z - 0.7, x + 1.8, 1.0, z + 0.7, bev=0.1, kind='wood')
        K.B('trough', C['water'], x - 1.65, 0.85, z - 0.55, x + 1.65, 0.92, z + 0.55, bev=0.0, kind='plastic')


def hitching(x, z0, z1):
    for z in (z0, z1):
        K.B('rail', C['wd'], x - 0.22, 0, z - 0.22, x + 0.22, 3.0, z + 0.22, bev=0.08, kind='wood')
    K.cylz('rail', C['wm'], z0 - 0.3, z1 + 0.3, x, 2.75, 0.17, segs=10, bev=0.05, kind='wood')


def water_tower(x, z, h=14.0):
    for dx, dz in ((-2.2, -2.2), (2.2, -2.2), (-2.2, 2.2), (2.2, 2.2)):
        K.B('tower', C['wd'], x + dx - 0.3, 0, z + dz - 0.3, x + dx + 0.3, h, z + dz + 0.3, bev=0.08, kind='wood')
    for y in (h * 0.35, h * 0.7):
        K.B('tower', C['wd'], x - 2.5, y, z - 2.5, x + 2.5, y + 0.3, z - 2.1, bev=0.05, kind='wood')
        K.B('tower', C['wd'], x - 2.5, y, z + 2.1, x + 2.5, y + 0.3, z + 2.5, bev=0.05, kind='wood')
    K.cyl('tower', C['wm'], x, h, z, 3.4, 5.2, segs=28, bev=0.15, kind='planks')
    for y in (h + 0.8, h + 2.6, h + 4.4):
        K.ring('tower', C['iron'], x, y, y + 0.18, z, 0.0, 3.48, segs=28, kind='metal')
    K.lathe('tower', C['roof'], [(3.7, 0), (2.5, 1.0), (0.4, 2.2), (0, 2.25)], x, h + 5.2, z, segs=28, kind='shingle')


def cactus(x, z, h=4.0):
    K.cyl('cactus', C['cactus'], x, 0, z, 0.45, h, segs=12, bev=0.4)
    K.cyl('cactus', C['cactus'], x + 0.9, h * 0.45, z, 0.32, h * 0.32, segs=10, bev=0.3)
    K.cylx('cactus', C['cactus'], x, x + 0.9, h * 0.45, z, 0.3, segs=10, bev=0.15)


def mesa(x, z, sx, sy, sz):
    K.B('mesa', C['rock'], x - sx / 2, 0, z - sz / 2, x + sx / 2, sy * 0.75, z + sz / 2, bev=1.5, kind='plastic', segs=2)
    K.B('mesa', C['rock'], x - sx / 2 + 1.5, sy * 0.75, z - sz / 2 + 2, x + sx / 2 - 2, sy, z + sz / 2 - 1.5, bev=1.2, kind='plastic', segs=2)


def wagon(x, z):
    K.B('wagon', C['wm'], x - 1.6, 1.6, z - 3.2, x + 1.6, 2.0, z + 3.2, bev=0.1, kind='planks')
    for sx in (-1, 1):
        K.B('wagon', C['wd'], x + sx * 1.6 - 0.15, 2.0, z - 3.2, x + sx * 1.6 + 0.15, 3.0, z + 3.2, bev=0.06, kind='wood')
    for dz in (-2.2, 2.2):
        for sx in (-1, 1):
            K.cylx('wagon', C['wd'], x + sx * 1.75, x + sx * 2.0, 1.4, z + dz, 1.4, segs=20, bev=0.08, kind='wood')   # the wheels, upright
            K.cylx('wagon', C['wm'], x + sx * 1.7, x + sx * 2.1, 1.4, z + dz, 0.3, segs=10, bev=0.05, kind='wood')   # hubs
    K.cylx('wagon', C['wd'], x - 1.9, x + 1.9, 1.4, z - 2.2, 0.15, segs=8)
    K.cylx('wagon', C['wd'], x - 1.9, x + 1.9, 1.4, z + 2.2, 0.15, segs=8)


# ---------------------------------------------------------------- the onlookers' gear (attached in game)
GEAR_Y = -40.0   # the gear parks under the street; the game moves its copies onto the onlookers (centres: hat 0, -40, 0;
                 # bandana 4, -40, 0; vest 8, -40, 0)
def gear():
    # a cowboy hat: a wide curled brim and a pinched crown (about a head wide)
    K.lathe('gearhat', C['cloth'], [(0, 0.0), (1.05, 0.0), (1.12, 0.12), (1.0, 0.16), (0.62, 0.16), (0.6, 0.9), (0.5, 1.02), (0, 0.98)], 0, GEAR_Y, 0, segs=24, kind='fabric')
    K.ring('gearhat', C['wd'], 0, GEAR_Y + 0.16, GEAR_Y + 0.32, 0, 0.0, 0.63, segs=24, kind='fabric')
    # a bandana: a folded triangle under the chin
    K.plate('gearbandana', C['red'], [(-0.62, 0.0), (0.62, 0.0), (0.0, -0.75)], 0.12, K.Tr(4, GEAR_Y, 0), bev=0.04, kind='fabric')
    # a vest: front panels and a back over the torso (in game sized to the UpperTorso)
    K.B('gearvest', C['wd'], 8 - 1.05, GEAR_Y - 0.95, -0.62, 8 - 0.1, GEAR_Y + 0.95, -0.5, bev=0.06, kind='fabric')
    K.B('gearvest', C['wd'], 8 + 0.1, GEAR_Y - 0.95, -0.62, 8 + 1.05, GEAR_Y + 0.95, -0.5, bev=0.06, kind='fabric')
    K.B('gearvest', C['wd'], 8 - 1.05, GEAR_Y - 0.95, 0.5, 8 + 1.05, GEAR_Y + 0.95, 0.62, bev=0.06, kind='fabric')


# ---------------------------------------------------------------- the two towns
def town_A():
    # west row (front faces +x), north (z > 0) to south; the saloon faces the duel (z -4 .. -16)
    timber('west', -1, 32, 42, col='wg', sign='sign', npc=())                         # the general store
    timber('west', -1, 24, 31, col='red', sign='cream', npc=())                       # a narrow shop
    timber('west', -1, 12, 23.5, two=True, col='wl', sign='sign', npc=('up1',))       # the hotel
    trough(-7.0, 7.0)
    hitching(-6.6, 3.0, 9.0)
    timber('west', -1, -17, -3, two=True, col='wm', sign='sign', style='saloon', npc=('up0', 'up2', 'door'))
    timber('west', -1, -26, -18, col='cream', sign='sign', npc=('win0',))            # the sheriff's
    timber('west', -1, -37, -27, col='teal', sign='cream', npc=())                    # the assay office
    timber('west', -1, -48, -38, col='wl', sign='sign', npc=())
    # east row (front faces -x): north block, the open gap z 9 .. -25, south block
    timber('east', 1, 31, 43, col='wm', sign='sign', npc=())                          # the livery's front
    timber('east', 1, 20, 30, two=True, col='wg', sign='cream', npc=())               # boarding house
    timber('east', 1, 10, 19, col='och', sign='sign', npc=())                         # the barber (its window's onlooker gone, 20 Nov: 1.4 studs from the room's end at a 1.5-stud window, no pose fit)
    timber('east', 1, -38, -26, col='red', sign='sign', npc=())                       # the bank
    timber('east', 1, -48, -39, col='wl', sign='cream', npc=())
    # the gap: a low corral, a trough, hay, barrels on the boardwalk ends
    for (xa, za), (xb, zb) in (((13.0, 7.0), (13.0, 3.5)), ((13.0, -20.5), (13.0, -23.0)), ((13.0, 7.0), (22.0, 7.0)), ((13.0, -23.0), (22.0, -23.0))):
        n = max(2, int(math.hypot(xb - xa, zb - za) / 3) + 1)
        for k in range(n):
            u = k / (n - 1)
            K.B('corral', C['wd'], xa + (xb - xa) * u - 0.14, 0, za + (zb - za) * u - 0.14, xa + (xb - xa) * u + 0.14, 2.4, za + (zb - za) * u + 0.14, bev=0.05, kind='wood')
        for y in (1.1, 2.05):
            K.B('corral', C['wm'], min(xa, xb) - 0.12, y, min(za, zb) - 0.12, max(xa, xb) + 0.12, y + 0.24, max(za, zb) + 0.12, bev=0.05, kind='wood')
    trough(9.4, 5.5)
    K.B('hay', C['hay'], 16.0, 0, -22.0, 18.2, 1.3, -20.4, bev=0.3, kind='fabric')
    K.B('hay', C['hay'], 18.0, 0, 4.8, 19.6, 1.3, 6.8, bev=0.3, kind='fabric')
    barrel(-8.9, 14.0, y0=0.62); barrel(-8.3, 13.0, 'wd', y0=0.62); barrel(-8.9, -19.2, y0=0.62); barrel(8.9, 11.0, y0=0.62)
    # barrels on the west boardwalk by the saloon. (The cowboy who hid behind the hotel's barrels is gone, 20 Nov: the
    # boardwalk between the barrels and the wall is 1.3 studs deep and a body 2.2 - no pose of his fit without passing
    # through one or the other; the clip check)
    barrel(-8.2, -2.4, y0=0.62); barrel(-8.4, -1.0, 'wd', y0=0.62)
    crate(-9.4, 33.0); crate(-8.8, 34.0, 1.0, 0.4); crate(9.5, -27.5)
    water_tower(-26.0, -6.0, 15.0)
    # the street's ends: a church across the south, a barn across the north
    K.B('church', C['cream'], -7, 0, -72, 7, 11, -60, bev=0.3, kind='planks')
    for side in (-1, 1):
        a = side * math.atan2(4.0, 7.0)
        M = K.Tr(0, 15, -66) @ K.Rz(a) @ K.Tr(0, -15, 66)
        K.B('church', C['roof'], *((0, 14.8, -72.4, 8.2, 15.2, -59.6) if side < 0 else (-8.2, 14.8, -72.4, 0, 15.2, -59.6)), bev=0.06, kind='shingle', M=M)
    K.plate('church', C['cream'], [(-7.0, 11.0), (7.0, 11.0), (0.0, 15.0)], 0.3, K.Tr(0, 0, -60.3), bev=0.05, kind='planks')
    K.B('church', C['cream'], -1.8, 11, -62.5, 1.8, 19, -59.0, bev=0.2, kind='planks')
    K.lathe('church', C['roof'], [(2.4, 0), (0.2, 4.0), (0, 4.05)], 0, 19, -60.8, segs=4, kind='shingle')
    K.B('church', C['wd'], -1.3, 0, -60.1, 1.3, 6.0, -59.8, bev=0.1, kind='wood')
    K.B('barn', C['red'], -9, 0, 58, 9, 12, 70, bev=0.3, kind='planks')
    for side in (-1, 1):
        a = side * math.atan2(5.0, 9.0)
        M = K.Tr(0, 17, 64) @ K.Rz(a) @ K.Tr(0, -17, -64)
        K.B('barn', C['roof'], *((0, 16.8, 57.6, 10.4, 17.2, 70.4) if side < 0 else (-10.4, 16.8, 57.6, 0, 17.2, 70.4)), bev=0.06, kind='shingle', M=M)
    K.plate('barn', C['red'], [(-9.0, 12.0), (9.0, 12.0), (0.0, 17.0)], 0.3, K.Tr(0, 0, 57.7), bev=0.05, kind='planks')
    K.B('barn', C['wd'], -3.5, 0, 57.7, 3.5, 8.0, 58.1, bev=0.1, kind='wood')
    K.B('barn', C['cream'], -3.4, 3.9, 57.6, 3.4, 4.3, 57.9, bev=0.05, kind='wood')


def town_B():
    # a wider street: adobe buildings with arcades and balconies; the hotel's balcony faces the duel
    adobe('west', -1, 30, 42, col='pl', npc=())
    adobe('west', -1, 16, 29, two=True, col='pl3', npc=('up0',), balcony=True)
    onlooker(-1, 21.0, 8.25, -3.0, 'balcony', 1)
    adobe('west', -1, -18, -2, two=True, col='pl', npc=('door',), balcony=True)          # the hotel: balcony onlookers
    onlooker(-1, -6.5, 8.25, -3.0, 'balcony', 1)
    onlooker(-1, -13.0, 8.25, -3.0, 'balcony', 1)
    adobe('west', -1, -30, -19, col='pl2', npc=('win1',))
    adobe('west', -1, -46, -31, col='pl3', npc=())
    adobe('east', 1, 30, 43, col='pl2', npc=())
    adobe('east', 1, 10, 29, two=True, col='pl', npc=(), balcony=True)
    onlooker(1, 13.5, 0.35, -3.0, 'porch', 0)                                         # in the arcade, by a pier
    adobe('east', 1, -40, -26, col='pl3', npc=())
    adobe('east', 1, -50, -41, col='pl', npc=(), arcade=False)
    # the gap (the side lenses look across it from x 25: nothing stands in their lines): a well at its south end,
    # a cart on the street's east edge to the north
    wz = -20.5
    K.lathe('well', C['pl2'], [(0, 0), (1.6, 0), (1.6, 1.3), (1.25, 1.3), (1.25, 0.2), (0, 0.2)], 18.0, 0, wz, segs=24, kind='plaster')
    for dz in (-1.3, 1.3):
        K.B('well', C['wd'], 17.85, 1.2, wz + dz - 0.15, 18.15, 4.4, wz + dz + 0.15, bev=0.06, kind='wood')
    K.cylz('well', C['wd'], wz - 1.5, wz + 1.5, 18.0, 4.2, 0.16, segs=8)
    K.B('well', C['roof'], 16.6, 4.4, wz - 1.8, 19.4, 4.75, wz + 1.8, bev=0.08, kind='shingle')
    wagon(8.6, 21.0)
    barrel(-11.8, 12.0); barrel(-11.2, 11.0, 'wd'); barrel(12.0, -24.5)
    crate(-12.0, -21.0); crate(11.9, 31.5, 1.2, 0.3)
    water_tower(26.0, 30.0, 13.0)
    # the ends: a mission front to the south, a mesa-backed corral gate north
    K.B('mission', C['pl3'], -9, 0, -74, 9, 12, -62, bev=0.6, kind='plaster', segs=2)
    K.B('mission', C['pl3'], -4.0, 12, -63.5, 4.0, 17, -62, bev=0.6, kind='plaster', segs=2)
    K.B('mission', C['pl3'], -1.8, 17, -63.2, 1.8, 19.5, -62, bev=0.5, kind='plaster', segs=2)
    K.B('mission', C['wd'], -1.6, 0, -62.1, 1.6, 7.0, -61.8, bev=0.1, kind='wood')
    for x in (-6, 6):
        K.B('mission', C['pl2'], x - 1.6, 0, -62.6, x + 1.6, 14, -61.0, bev=0.5, kind='plaster', segs=2)
    for x in (-6.0, 6.0):
        K.B('gate', C['wd'], x - 0.4, 0, 60.0, x + 0.4, 7.0, 60.8, bev=0.1, kind='wood')
    K.B('gate', C['wd'], -6.4, 6.4, 60.0, 6.4, 7.2, 60.8, bev=0.1, kind='wood')


# ---------------------------------------------------------------- run
if VER == 'A':
    town_A()
else:
    town_B()
gear()
# the kit's origin marker: the game pivots the uploaded model on it (its centre is the scene's ORIGIN + (0, -60, 0))
K.B('kitorigin', 'ff00ff', -0.25, -60.25, -0.25, 0.25, -59.75, 0.25, bev=0.0, kind='plastic')
for at, size in (((-80, -30), (40, 22, 60)), ((-60, 70), (30, 16, 40)), ((85, -40), (36, 26, 50)), ((95, 40), (50, 18, 36)), ((0, -150), (90, 30, 40))):
    mesa(at[0], at[1], *size)
for at, h in (((-20, 50), 4.4), ((24, 14), 3.4), ((-30, -40), 3.8), ((30, -34), 4.2)):
    cactus(at[0], at[1], h)

# the onlookers' spots, for the game (client/FinisherScene: EXTRA.highnoon.town)
json.dump({'version': VER, 'spots': SPOTS}, open(os.path.join(OUT, 'highnoon_town_%s.json' % VER), 'w'), indent=1)
print('SPOTS', len(SPOTS))

# --boxes: every piece near the street as its box (Roblox local, min and max), before the merge - the onlookers' clip
# check builds the town from these as plain blocks (the merged meshes' collision shapes are whole buildings)
if '--boxes' in K.FLAGS:
    boxes = []
    for (model, key), items in K.PIECES.items():
        if model in ('kitorigin',) or model.startswith('gear'):
            continue
        for bm, M in items:
            vs = [M @ v.co for v in bm.verts]
            lo = [min(v[i] for v in vs) for i in range(3)]
            hi = [max(v[i] for v in vs) for i in range(3)]
            if hi[1] < -5 or max(abs(lo[0]), abs(hi[0])) > 45 or max(abs(lo[2]), abs(hi[2])) > 45:
                continue
            boxes.append([model, key.split('_')[0]] + [round(x, 3) for x in lo + hi])
    json.dump(boxes, open(os.path.join(OUT, 'highnoon_town_%s_boxes.json' % VER), 'w'))
    print('BOXES', len(boxes))

# previews from the scene's own lenses (Roblox local: position, look-at, vertical fov), stand-ins at the duel marks
VIEWS = [("wide", (25, 1.1, 1.5), (0, 4.0, -7.0), 26), ("far", (26.7, 2.1, -8.5), (0, 3.0, -8.5), 33),
         ("victim_hand", (-3.1, 2.0, -18.9), (2.0, 6.0, 8.0), 38), ("killer_hand", (3.1, 2.0, 1.9), (-4.0, 5.0, -16.0), 40),
         ("draw", (3.1, 1.1, 3.1), (-1.3, 3.5, -10.0), 70), ("overhead", (-11.1, 32, -8.5), (0, 0, -8.5), 42)]
views = []
for name, cp, tp, vfov in VIEWS:
    hf = 2 * math.atan(math.tan(math.radians(vfov) / 2) * 1000 / 560)
    views.append((name, cp, tp, 18 / math.tan(hf / 2)))
if '--previews' in K.FLAGS:
    for z in (0.0, -17.0):   # stand-ins, about an R15 body
        K.B('standin', 'e8e2d6', -0.6, 0, z - 0.35, 0.6, 5.2, z + 0.35, bev=0.25, kind='plastic')
K.finish('highnoon_town_' + VER, OUT, preview_dir=os.path.join(OUT, 'previews') if '--previews' in K.FLAGS else None,
         views=views, prefix='town_' + VER, sky=(0.62, 0.74, 0.86), sun_rot=(52, 0, -170), sun_energy=3.6)
