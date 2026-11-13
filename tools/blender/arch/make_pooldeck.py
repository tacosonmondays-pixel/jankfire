# Rooftop's pool deck (shared/map.js rooftop() / rooftopSD(): poolDeckArch), the whole party set as one Blender model
# per map, drawn over its own boxes (tools/arch/dump.mjs + dump_deco.mjs), which stay what you bump into. Each piece is
# found by its box and built inside it, from real pool-party kit:
#   the pool's coping: white bullnose stone round the edge, a blue mosaic floor with a dark lane cross (the water stays
#     the game's); sun loungers: an aluminium frame on legs and wheels, a padded cushion in the box's colour, a rolled
#     towel and a pillow at the head; cabanas: teak posts with brass caps, a striped canvas roof peaked over them with a
#     scalloped valance, canvas side panels on rails, curtains tied back at the posts, a daybed with cushions; the DJ:
#     a black flight case with aluminium edges and ball corners, two turntables, a mixer with glowing faders, a laptop
#     (its JANK picture stays the game's); the PA: subs at the bottom, tops with a horn and a cone, grilles, a
#     glowing badge; the light rig: square aluminium truss up both sides and across, moving heads hanging under it with
#     their lenses in the map's colours; festoon strings: steel poles, a sagging wire, bulbs in the map's colours;
#     concrete planters (the palms are props already); an inflatable flamingo and a ring in the pool.
# local frame = the map's (one placement at the origin). y is the world's (the deck at -4).
# run: node tools/arch/dump.mjs rooftop pooldeck tools/blender/arch/boxes/pooldeck.json
#      node tools/arch/dump_deco.mjs rooftop pooldeck tools/blender/arch/boxes/pooldeck_deco.json
#      (the same with rooftop_sd / pooldeck_sd)
#      blender52 -b --python tools/blender/arch/make_pooldeck.py -- [pooldeck|pooldeck_sd]   (both by default)
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
G = {'aosoft': 0.35}  # (cushions lit like the map's boxes: bright, no gloss, soft shadows)
S = {'aosoft': 0.35}  # (the canopy's canvas: light comes through it)
MATS.update({
    'pd_coping': ('trim', '#f4f2ee', {'gloss': 0.5}), 'pd_mosaic': ('trim', '#38c8f0', {'gloss': 0.4}), 'pd_lane': ('trim', '#1a3a7a', {}),
    'pd_alu': ('metalplate', '#f4f6fb', {'gloss': 0.5}), 'pd_rubber': ('tar', '#222026', {}),
    'pd_c_white': ('trim', '#f6f4f0', G), 'pd_c_toypink': ('trim', '#ff6ad5', G), 'pd_c_toyteal': ('trim', '#5ef2e4', G), 'pd_c_toyyellow': ('trim', '#ffe14d', G),
    'pd_towel': ('stucco', '#ffffff', {}), 'pd_towel2': ('stucco', '#4fd8ff', {}),
    'pd_teak': ('planks', '#f0b070', {}), 'pd_brass': ('metalplate', '#e8b840', {'gloss': 0.8, 'metal': 1}),
    'pd_canvas': ('stucco', '#fbf6ee', S), 'pd_stripe': ('stucco', '#ff4fd8', S), 'pd_curtain': ('stucco', '#f6eef6', {}),
    'pd_case': ('tar', '#1d1b22', {'gloss': 0.35}), 'pd_deck': ('metalplate', '#2c2c34', {'gloss': 0.5}), 'pd_platter': ('metalplate', '#c4c8d0', {'gloss': 0.8, 'metal': 1}),
    'pd_vinyl': ('tar', '#0e0e12', {'gloss': 0.9}), 'pd_label': ('trim', '#ff4fd8', {}), 'pd_screen': ('trim', '#4fd8ff', {'glow': True, 'glowcol': '#4fd8ff'}),
    'pd_fader': ('trim', '#39ff14', {'glow': True, 'glowcol': '#39ff14'}), 'pd_cone': ('tar', '#151518', {}), 'pd_grille': ('metalplate', '#2e3038', {}),
    'pd_badge': ('trim', '#ffe14d', {'glow': True, 'glowcol': '#ffd040'}),
    'pd_neonpink': ('trim', '#ff7ae0', {'glow': True, 'glowcol': '#ff4fd8'}), 'pd_neoncyan': ('trim', '#8aeaff', {'glow': True, 'glowcol': '#4fd8ff'}),
    'pd_neonyellow': ('trim', '#fff08a', {'glow': True, 'glowcol': '#ffe14d'}), 'pd_neongreen': ('trim', '#a8ff8a', {'glow': True, 'glowcol': '#39ff14'}),
    'pd_lamp': ('trim', '#fff6d8', {'glow': True, 'glowcol': '#fff0c0'}), 'pd_wire': ('tar', '#26242a', {}),
    'pd_planter': ('concrete', '#e2d8cc', {}), 'pd_soil': ('tar', '#5a4632', {}), 'pd_tilerim': ('trim', '#ff4fd8', {'gloss': 0.5}),
    'pd_flamingo': ('trim', '#ff70b8', {'gloss': 0.9}), 'pd_beak': ('trim', '#ff9a2a', {'gloss': 0.8}), 'pd_black': ('tar', '#141418', {}),
    'pd_ring': ('trim', '#ffe14d', {'gloss': 0.9}), 'pd_ring2': ('trim', '#ff4fd8', {'gloss': 0.9}),
})
NOCAST.update({'pd_canvas', 'pd_stripe', 'pd_lane', 'pd_towel', 'pd_towel2', 'pd_brass', 'pd_curtain', 'pd_platter', 'pd_vinyl', 'pd_label', 'pd_screen', 'pd_fader', 'pd_badge',
               'pd_neonpink', 'pd_neoncyan', 'pd_neonyellow', 'pd_neongreen', 'pd_lamp', 'pd_wire', 'pd_beak', 'pd_black', 'pd_rubber'})
E = 0.002


def merge_mats(K, m):
    """fewer draw calls (one per material in the game): small parts take a bigger part's material"""
    for (mat, node) in list(K.geo):
        if mat not in m: continue
        src = K.geo.pop((mat, node)); dst = K._bucket(m[mat], node); b = len(dst['v'])
        dst['v'] += src['v']; dst['uv'] += src['uv']; dst['f'] += [tuple(i + b for i in f) for f in src['f']]
MERGE = {'pd_beak': 'pd_ring', 'pd_brass': 'pd_ring', 'pd_black': 'pd_case', 'pd_rubber': 'pd_case', 'pd_vinyl': 'pd_case', 'pd_cone': 'pd_case', 'pd_wire': 'pd_case',
         'pd_soil': 'pd_case', 'pd_grille': 'pd_deck', 'pd_lane': 'pd_deck', 'pd_label': 'pd_stripe', 'pd_tilerim': 'pd_stripe', 'pd_ring2': 'pd_flamingo',
         'pd_c_toypink': 'pd_flamingo', 'pd_towel2': 'pd_c_toyteal', 'pd_towel': 'pd_canvas', 'pd_curtain': 'pd_canvas', 'pd_c_white': 'pd_canvas',
         'pd_platter': 'pd_alu', 'pd_planter': 'pd_coping', 'pd_badge': 'pd_neonyellow', 'pd_fader': 'pd_neongreen', 'pd_screen': 'pd_neoncyan', 'pd_c_toyyellow': 'pd_ring'}


def bx(K, mn, mx, mat, **kw):
    K.box(tuple(mn), tuple(mx), mat if isinstance(mat, dict) else {'all': mat}, cull=False, **kw)


def ext(b):
    (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']; return x0, y0, z0, x1, y1, z1


def torus(K, c, R, r, mat, n=16, m=6, axis='y'):
    """a doughnut lying flat (axis y): n segments round, each a tube of m sides"""
    cx, cy, cz = c
    for k in range(n):
        a0, a1 = k * math.tau / n, (k + 1) * math.tau / n
        FL.tube(K, (cx + R * math.cos(a0), cy, cz + R * math.sin(a0)), (cx + R * math.cos(a1), cy, cz + R * math.sin(a1)), r, r, mat if isinstance(mat, str) else mat[k % len(mat)], n=m, caps=(False, False))


def ring_z(K, c, R, r, mat, n=16, m=6):
    """a doughnut standing up, facing z (a neon ring round a speaker cone)"""
    cx, cy, cz = c
    for k in range(n):
        a0, a1 = k * math.tau / n, (k + 1) * math.tau / n
        FL.tube(K, (cx + R * math.cos(a0), cy + R * math.sin(a0), cz), (cx + R * math.cos(a1), cy + R * math.sin(a1), cz), r, r, mat, n=m, caps=(False, False))


def blob(K, c, r, mat, sy=1.0, n=8):
    """a squashed ball: two cones (a bulb, a head, a pillow end)"""
    x, y, z = c
    FL.tube(K, (x, y - r * sy, z), (x, y, z), 0.0, r, mat, n=n, caps=(False, False)); FL.tube(K, (x, y, z), (x, y + r * sy, z), r, 0.0, mat, n=n, caps=(False, False))


# ------------------------------------------------------------ the pieces
def pool(K, tiles):
    floor = [b for b in tiles if b['max'][1] - b['min'][1] < 0.06][0]
    x0, y0, z0, x1, y1, z1 = ext(floor)
    K.plain(floor, {'top': 'pd_mosaic', 'side': 'pd_mosaic'}, sub=1.0)
    y = y1 + 0.003; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    for (a0, b0, a1, b1) in ((x0 + 0.6, cz - 0.12, x1 - 0.6, cz + 0.12), (cx - 0.12, z0 + 0.6, cx + 0.12, z1 - 0.6)):  # the lane cross on the floor
        if a1 - a0 > b1 - b0: segs = [(a0, b0, cx - 0.12, b1), (cx + 0.12, b0, a1, b1)]
        else: segs = [(a0, b0, a1, cz - 0.12), (a0, cz + 0.12, a1, b1)]
        for (p, q, r, s) in segs:
            K.box((p, y1 - 0.01, q), (r, y, s), {'top': 'pd_lane', 'side': 'pd_lane'}, cull=False)
    K.box((cx - 0.12, y1 - 0.01, cz - 0.12), (cx + 0.12, y, cz + 0.12), {'top': 'pd_lane', 'side': 'pd_lane'}, cull=False)
    for b in tiles:  # the coping: bullnose (a rounded lip over the water's side)
        if b is floor: continue
        x0, y0, z0, x1, y1, z1 = ext(b)
        K.plain(b, {'top': 'pd_coping', 'side': 'pd_coping'}, sub=1.0)


def lounger(K, b, poolz):
    x0, y0, z0, x1, y1, z1 = ext(b); cx = (x0 + x1) / 2
    zc = (z0 + z1) / 2; head = -1 if zc < poolz else 1  # (the head away from the pool, the feet to it)
    col = 'pd_c_' + b['mat'] if 'pd_c_' + b['mat'] in MATS else 'pd_c_white'
    fy = y0 + 0.24
    for s in (-1, 1):  # side rails, legs, wheels at the foot
        bx(K, (cx + s * 0.44 - 0.025, fy, z0 + 0.05), (cx + s * 0.44 + 0.025, fy + 0.05, z1 - 0.05), 'pd_alu')
        for zz in (z0 + 0.18, z1 - 0.18):
            footz = zz
            if (head > 0 and zz < zc) or (head < 0 and zz > zc):  # the foot end: wheels
                FL.tube(K, (cx + s * 0.44 - 0.03, y0 + 0.09, footz), (cx + s * 0.44 + 0.03, y0 + 0.09, footz), 0.09, 0.09, 'pd_rubber', n=8)
                bx(K, (cx + s * 0.44 - 0.02, y0 + 0.09, footz - 0.02), (cx + s * 0.44 + 0.02, fy, footz + 0.02), 'pd_alu')
            else:
                bx(K, (cx + s * 0.44 - 0.02, y0, footz - 0.02), (cx + s * 0.44 + 0.02, fy, footz + 0.02), 'pd_alu')
    for k in range(int((z1 - z0 - 0.1) / 0.16)):  # slats under the cushion
        z = z0 + 0.1 + k * 0.16
        bx(K, (cx - 0.42, fy + 0.01, z), (cx + 0.42, fy + 0.04, z + 0.1), 'pd_alu')
    bx(K, (cx - 0.4, fy + 0.05, z0 + 0.12), (cx + 0.4, y1 - 0.01, z1 - 0.12), {'top': col, 'side': col})  # the cushion (the box's colour)
    for k in range(1, 5):  # tufting lines across it
        z = z0 + 0.12 + k * (z1 - z0 - 0.24) / 5
        bx(K, (cx - 0.38, y1 - 0.012, z - 0.012), (cx + 0.38, y1 - 0.006, z + 0.012), {'top': 'pd_alu', 'side': 'pd_alu'})
    hz = z1 - 0.32 if head > 0 else z0 + 0.32  # a rolled towel at the head, a folded one at the foot
    FL.tube(K, (cx - 0.33, y1 + 0.07, hz), (cx + 0.33, y1 + 0.07, hz), 0.08, 0.08, 'pd_towel', n=8)
    fz0, fz1 = (z0 + 0.25, z0 + 0.6) if head > 0 else (z1 - 0.6, z1 - 0.25)
    bx(K, (cx - 0.28, y1 - 0.004, fz0), (cx + 0.28, y1 + 0.05, fz1), {'top': 'pd_towel2', 'side': 'pd_towel2'})


def cabana(K, posts, walls, sofa, roof):
    xs = sorted(set(round((p['min'][0] + p['max'][0]) / 2, 3) for p in posts)); zs = sorted(set(round((p['min'][2] + p['max'][2]) / 2, 3) for p in posts))
    for p in posts:  # teak posts on brass shoes, brass caps
        x0, y0, z0, x1, y1, z1 = ext(p)
        bx(K, (x0 - 0.03, y0, z0 - 0.03), (x1 + 0.03, y0 + 0.12, z1 + 0.03), 'pd_brass')
        bx(K, (x0, y0 + 0.12, z0), (x1, y1, z1), {'side': 'pd_teak', 'top': 'pd_brass'})
    rx0, ry0, rz0, rx1, ry1, rz1 = ext(roof)
    cx, cz = (rx0 + rx1) / 2, (rz0 + rz1) / 2; peak = ry1 + 0.9
    # the roof: a frame on the posts, a peaked striped canvas over it, a scalloped valance all round
    bx(K, (rx0 + 0.1, ry0, rz0 + 0.1), (rx1 - 0.1, ry0 + 0.1, rz0 + 0.22), 'pd_teak'); bx(K, (rx0 + 0.1, ry0, rz1 - 0.22), (rx1 - 0.1, ry0 + 0.1, rz1 - 0.1), 'pd_teak')
    bx(K, (rx0 + 0.1, ry0, rz0 + 0.22), (rx0 + 0.22, ry0 + 0.1, rz1 - 0.22), 'pd_teak'); bx(K, (rx1 - 0.22, ry0, rz0 + 0.22), (rx1 - 0.1, ry0 + 0.1, rz1 - 0.22), 'pd_teak')
    corners = [(rx0, rz0), (rx1, rz0), (rx1, rz1), (rx0, rz1)]
    n = 8  # stripes per side
    for i in range(4):
        (ax, az), (bx_, bz) = corners[i], corners[(i + 1) % 4]
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            p0 = Vector((ax + (bx_ - ax) * t0, ry0 + 0.12, az + (bz - az) * t0)); p1 = Vector((ax + (bx_ - ax) * t1, ry0 + 0.12, az + (bz - az) * t1))
            top = Vector((cx, peak, cz))
            FL.tri2(K, [p0, p1, top], 'pd_stripe' if k % 2 else 'pd_canvas')
            # valance: a drop with a scalloped hem (each stripe a tongue)
            d0 = Vector((0, -0.32, 0)); dm = Vector((0, -0.42, 0))
            mid = (p0 + p1) / 2
            FL.both(K, [p0 + d0, p1 + d0, p1, p0], 'pd_stripe' if k % 2 else 'pd_canvas')
            FL.tri2(K, [p0 + d0, mid + dm, p1 + d0], 'pd_stripe' if k % 2 else 'pd_canvas')
    FL.tube(K, (cx, peak - 0.05, cz), (cx, peak + 0.25, cz), 0.04, 0.04, 'pd_brass', n=6); blob(K, (cx, peak + 0.3, cz), 0.07, 'pd_brass', n=6)  # a finial
    for w in walls:  # the side panels: canvas on a rail, a stripe at the top
        x0, y0, z0, x1, y1, z1 = ext(w)
        bx(K, (x0, y0, z0), (x1, y1 - 0.12, z1), {'all': 'pd_canvas'})
        bx(K, (x0 - 0.01, y1 - 0.12, z0 - 0.01), (x1 + 0.01, y1, z1 + 0.01), {'all': 'pd_stripe'})
    for (px, pz) in [(x, z) for x in xs for z in zs]:  # curtains tied back at each post (soft bunches)
        dx = 0.18 if px < cx else -0.18; dz = 0.18 if pz < cz else -0.18
        FL.tube(K, (px + dx, ry0 - 0.32, pz + dz), (px + dx * 0.6, ry0 - 1.3, pz + dz * 0.6), 0.16, 0.07, 'pd_curtain', n=8, caps=(False, False))
        FL.tube(K, (px + dx * 0.6, ry0 - 1.3, pz + dz * 0.6), (px + dx * 1.1, y0_ground + 0.05, pz + dz * 1.1), 0.07, 0.2, 'pd_curtain', n=8, caps=(False, True))
        torus(K, (px + dx * 0.6, ry0 - 1.3, pz + dz * 0.6), 0.08, 0.02, 'pd_stripe', n=8, m=4)
    x0, y0, z0, x1, y1, z1 = ext(sofa)  # the daybed: a teak plinth, a mattress, cushions along the back
    col = 'pd_c_' + sofa['mat'] if 'pd_c_' + sofa['mat'] in MATS else 'pd_c_toyteal'
    bx(K, (x0, y0, z0), (x1, y0 + 0.22, z1), 'pd_teak')
    bx(K, (x0 + 0.03, y0 + 0.22, z0 + 0.03), (x1 - 0.03, y1, z1 - 0.03), {'top': col, 'side': col})
    back = z1 if (z0 + z1) / 2 < cz or True else z0
    for k in range(3):
        px = x0 + 0.4 + k * (x1 - x0 - 0.8) / 2
        bx(K, (px - 0.3, y1 - 0.01, z1 - 0.32), (px + 0.3, y1 + 0.32, z1 - 0.1), {'all': 'pd_c_white' if k == 1 else 'pd_c_toypink'})


def dj(K, case, top, spk, grilles):
    x0, y0, z0, x1, y1, z1 = ext(case)
    K.plain(case, {'top': 'pd_ring', 'side': 'pd_ring'}, sub=1.0)  # (a yellow booth)
    for (a, b_) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):  # aluminium edges and ball corners
        bx(K, (a - 0.02, y0, b_ - 0.02), (a + 0.02, y1 - 0.003, b_ + 0.02), 'pd_alu')
        blob(K, (a, y1, b_), 0.05, 'pd_platter', n=6)
    for yy in (y0 + 0.02, y1 - 0.02):
        bx(K, (x0 + 0.02, yy - 0.02, z1), (x1 - 0.02, yy + 0.02, z1 + 0.02), 'pd_alu'); bx(K, (x0 + 0.02, yy - 0.02, z0 - 0.02), (x0 + 0.5, yy + 0.02, z0), 'pd_alu'); bx(K, (x1 - 0.5, yy - 0.02, z0 - 0.02), (x1 - 0.02, yy + 0.02, z0), 'pd_alu')
    tx0, ty0, tz0, tx1, ty1, tz1 = ext(top)
    K.plain(top, {'top': 'pd_deck', 'side': 'pd_alu'})
    tcz = (tz0 + tz1) / 2
    for sx in (-1.6, 1.6):  # two turntables: plinth, platter, a record, the arm
        tx = (tx0 + tx1) / 2 + sx
        bx(K, (tx - 0.32, ty1, tcz - 0.25), (tx + 0.32, ty1 + 0.06, tcz + 0.25), {'top': 'pd_deck', 'side': 'pd_platter'})
        FL.tube(K, (tx - 0.04, ty1 + 0.06, tcz), (tx - 0.04, ty1 + 0.08, tcz), 0.2, 0.2, 'pd_platter', n=16)
        FL.tube(K, (tx - 0.04, ty1 + 0.08, tcz), (tx - 0.04, ty1 + 0.09, tcz), 0.18, 0.18, 'pd_vinyl', n=16)
        FL.tube(K, (tx - 0.04, ty1 + 0.09, tcz), (tx - 0.04, ty1 + 0.096, tcz), 0.06, 0.06, 'pd_label', n=10)
        FL.bar(K, (tx + 0.24, ty1 + 0.1, tcz - 0.18), (tx + 0.08, ty1 + 0.1, tcz + 0.06), 0.015, 'pd_platter')
    mx = (tx0 + tx1) / 2  # the mixer, its faders glowing
    bx(K, (mx - 0.32, ty1, tcz - 0.26), (mx + 0.32, ty1 + 0.1, tcz + 0.26), {'top': 'pd_deck', 'side': 'pd_platter'})
    for k in range(4): bx(K, (mx - 0.22 + k * 0.14 - 0.015, ty1 + 0.1, tcz - 0.15), (mx - 0.22 + k * 0.14 + 0.015, ty1 + 0.105, tcz + 0.12), {'top': 'pd_fader', 'side': 'pd_fader'})
    lx = (tx0 + tx1) / 2 + 0.85  # a laptop on a stand, its screen to the DJ
    bx(K, (lx - 0.18, ty1, tcz - 0.13), (lx + 0.18, ty1 + 0.025, tcz + 0.13), 'pd_platter')
    q = [(lx - 0.18, ty1 + 0.025, tcz - 0.13), (lx + 0.18, ty1 + 0.025, tcz - 0.13), (lx + 0.18, ty1 + 0.27, tcz - 0.2), (lx - 0.18, ty1 + 0.27, tcz - 0.2)]
    FL.both(K, q, 'pd_platter')
    K.quad([(q[1][0] - 0.02, q[1][1] + 0.02, q[1][2] + 0.004), (q[0][0] + 0.02, q[0][1] + 0.02, q[0][2] + 0.004), (q[3][0] + 0.02, q[3][1] - 0.02, q[3][2] + 0.004), (q[2][0] - 0.02, q[2][1] - 0.02, q[2][2] + 0.004)], 'pd_screen')
    for s in spk:  # PA: a sub at the bottom, a top box with a horn and a cone; the map's grille is where the top's face is
        x0, y0, z0, x1, y1, z1 = ext(s)
        K.plain(s, {'top': 'pd_flamingo', 'side': 'pd_flamingo'})  # (candy pink cabinets, the party's)
        cx = (x0 + x1) / 2; fz = z0  # the front: -z
        bx(K, (x0 - 0.01, y0 + 1.08, z0 - 0.01), (x1 + 0.01, y0 + 1.12, z1 + 0.01), 'pd_alu')  # the seam between the boxes
        for (r, cy) in ((0.42, y0 + 0.55),):  # the sub's big cone
            FL.tube(K, (cx, cy, fz - E), (cx, cy, fz - 0.03), r, r, 'pd_grille', n=16, caps=(False, True))
            ring_z(K, (cx, cy, fz - 0.02), r + 0.03, 0.025, 'pd_neoncyan', n=20)  # a neon ring round it
            FL.tube(K, (cx, cy, fz - 0.03), (cx, cy, fz + 0.12), r * 0.92, 0.08, 'pd_cone', n=16, caps=(False, False), inside=True)
        FL.tube(K, (cx, y0 + 1.42, fz - E), (cx, y0 + 1.42, fz - 0.03), 0.28, 0.28, 'pd_grille', n=14, caps=(False, True))  # the top's cone
        ring_z(K, (cx, y0 + 1.42, fz - 0.02), 0.31, 0.022, 'pd_neoncyan', n=16)
        FL.tube(K, (cx, y0 + 1.42, fz - 0.03), (cx, y0 + 1.42, fz + 0.08), 0.25, 0.05, 'pd_cone', n=14, caps=(False, False), inside=True)
        bx(K, (cx - 0.36, y0 + 1.78, z0 - 0.04), (cx + 0.36, y0 + 2.06, z0 - E), {'all': 'pd_grille'})  # the horn's mouth
        bx(K, (cx - 0.3, y0 + 1.82, z0 - 0.045), (cx + 0.3, y0 + 2.02, z0 - 0.04), {'all': 'pd_cone'})
        bx(K, (x1 - 0.3, y0 + 0.08, z0 - 0.02), (x1 - 0.08, y0 + 0.16, z0 - E), {'all': 'pd_badge'})  # the glowing badge
        for (a, b_) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
            bx(K, (a - 0.015, y0, b_ - 0.015), (a + 0.015, y1 - 0.003, b_ + 0.015), 'pd_alu')


def truss(K, a, b, w=0.3, mat='pd_alu'):
    """square box truss from a to b (centre line): four chords, zigzag lacing on each side"""
    a, b = Vector(a), Vector(b); d = (b - a); L = d.length; d.normalize()
    up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    u = d.cross(up).normalized() * (w / 2); v = u.cross(d).normalized() * (w / 2)
    cs = [u + v, -u + v, -u - v, u - v]
    for c in cs: FL.tube(K, a + c, b + c, 0.022, 0.022, mat, n=6, caps=(True, True))
    n = max(1, int(L / w))
    for i in range(4):
        c0, c1 = cs[i], cs[(i + 1) % 4]
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            p, q = (a + d * L * t0 + c0, a + d * L * t1 + c1) if k % 2 == 0 else (a + d * L * t0 + c1, a + d * L * t1 + c0)
            p = p + (q - p) * 0.06; q = q - (q - p) * 0.06
            FL.bar(K, p, q, 0.014, mat)


def rig(K, posts, bar, lights):
    for p in posts:  # the truss towers on base plates
        x0, y0, z0, x1, y1, z1 = ext(p); cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        bx(K, (cx - 0.4, y0, cz - 0.4), (cx + 0.4, y0 + 0.03, cz + 0.4), {'side': 'pd_alu', 'top': 'pd_alu'})
        truss(K, (cx, y0 + 0.03, cz), (cx, y1 + 0.2, cz))
    x0, y0, z0, x1, y1, z1 = ext(bar)
    truss(K, (x0 - 0.05, (y0 + y1) / 2, (z0 + z1) / 2), (x1 + 0.05, (y0 + y1) / 2, (z0 + z1) / 2))
    for l in lights:  # moving heads hanging under the beam: a yoke, a head, its lens in the bulb's colour
        lx0, ly0, lz0, lx1, ly1, lz1 = ext(l); cx, cy, cz = (lx0 + lx1) / 2, (ly0 + ly1) / 2, (lz0 + lz1) / 2
        lens = {'neonpink': 'pd_neonpink', 'neoncyan': 'pd_neoncyan', 'neonyellow': 'pd_neonyellow', 'neongreen': 'pd_neongreen'}.get(l['mat'], 'pd_lamp')
        bx(K, (cx - 0.1, y0 - 0.12, cz - 0.08), (cx + 0.1, y0 - 0.02, cz + 0.08), 'pd_case')  # the clamp / base
        FL.bar(K, (cx - 0.13, y0 - 0.12, cz), (cx - 0.13, cy - 0.02, cz), 0.025, 'pd_case'); FL.bar(K, (cx + 0.13, y0 - 0.12, cz), (cx + 0.13, cy - 0.02, cz), 0.025, 'pd_case')
        FL.tube(K, (cx, cy + 0.06, cz + 0.06), (cx, cy - 0.12, cz - 0.1), 0.11, 0.13, 'pd_case', n=10)
        FL.tube(K, (cx, cy - 0.121, cz - 0.101), (cx, cy - 0.13, cz - 0.11), 0.1, 0.1, lens, n=10, caps=(False, True))


def festoon(K, posts, bulbs):
    for p in posts:  # steel poles with a hook and a ring on top
        x0, y0, z0, x1, y1, z1 = ext(p); cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        bx(K, (cx - 0.15, y0, cz - 0.15), (cx + 0.15, y0 + 0.04, cz + 0.15), {'side': 'pd_alu', 'top': 'pd_alu'})
        FL.tube(K, (cx, y0 + 0.04, cz), (cx, y1, cz), 0.05, 0.04, 'pd_alu', n=8)
        blob(K, (cx, y1 + 0.03, cz), 0.05, 'pd_alu', n=6)
    rows = {}
    for b in bulbs: rows.setdefault(round((b['min'][2] + b['max'][2]) / 2, 2), []).append(b)
    for z, bs in rows.items():
        bs.sort(key=lambda b: b['min'][0])
        pts = [Vector(((b['min'][0] + b['max'][0]) / 2, b['max'][1] + 0.05, z)) for b in bs]
        for p, q in zip(pts, pts[1:]): FL.bar(K, p, q, 0.012, 'pd_wire')
        for b, p in zip(bs, pts):
            m = {'neonpink': 'pd_neonpink', 'neoncyan': 'pd_neoncyan', 'neonyellow': 'pd_neonyellow', 'neongreen': 'pd_neongreen'}.get(b['mat'], 'pd_lamp')
            FL.tube(K, p, p - Vector((0, 0.06, 0)), 0.03, 0.03, 'pd_black', n=6)  # the holder
            blob(K, p - Vector((0, 0.16, 0)), 0.09, m, sy=1.25, n=8)  # the bulb


def planter(K, b):
    x0, y0, z0, x1, y1, z1 = ext(b)
    K.plain(b, {'side': 'pd_planter', 'top': 'pd_soil'})
    w = 0.16  # a tiled rim round the top (a ring: the soil shows in the middle)
    for (p, q) in (((x0 - 0.04, z0 - 0.04), (x1 + 0.04, z0 + w)), ((x0 - 0.04, z1 - w), (x1 + 0.04, z1 + 0.04)), ((x0 - 0.04, z0 + w), (x0 + w, z1 - w)), ((x1 - w, z0 + w), (x1 + 0.04, z1 - w))):
        bx(K, (p[0], y1 - 0.1, p[1]), (q[0], y1 + 0.03, q[1]), {'side': 'pd_tilerim', 'top': 'pd_tilerim', 'bottom': 'pd_tilerim'})
    K.solids.append(((x0 + 0.01, y0, z0 + 0.01), (x1 - 0.01, y1 + 0.02, z1 - 0.01)))


def floats(K, deco):
    pink = [b for b in deco if b['mat'] in ('toypink', 'toyorange')]
    if pink:
        body = max(pink, key=lambda b: (b['max'][0] - b['min'][0]) * (b['max'][2] - b['min'][2]))
        x0, y0, z0, x1, y1, z1 = ext(body); cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
        torus(K, (cx, cy, cz), 0.45, 0.2, 'pd_flamingo', n=14, m=8)  # the ring body
        blob(K, (cx - 0.45, cy + 0.05, cz), 0.18, 'pd_flamingo', n=8)  # the tail
        neck = [Vector((cx + 0.45, cy + 0.1, cz)), Vector((cx + 0.55, cy + 0.55, cz)), Vector((cx + 0.5, cy + 0.95, cz)), Vector((cx + 0.62, cy + 1.2, cz))]
        for p, q in zip(neck, neck[1:]): FL.tube(K, p, q, 0.11, 0.1, 'pd_flamingo', n=8, caps=(False, False))
        blob(K, (cx + 0.66, cy + 1.25, cz), 0.14, 'pd_flamingo', n=8)
        FL.tube(K, (cx + 0.75, cy + 1.25, cz), (cx + 0.98, cy + 1.12, cz), 0.06, 0.02, 'pd_beak', n=6)
        FL.tube(K, (cx + 0.9, cy + 1.155, cz), (cx + 1.0, cy + 1.11, cz), 0.03, 0.01, 'pd_black', n=6)
        for s in (-1, 1): blob(K, (cx + 0.7, cy + 1.32, cz + s * 0.11), 0.03, 'pd_black', n=6)
    ring = [b for b in deco if b['mat'] == 'toyyellow']
    if ring:
        xs = [v for b in ring for v in (b['min'][0], b['max'][0])]; zs = [v for b in ring for v in (b['min'][2], b['max'][2])]
        cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2; cy = (ring[0]['min'][1] + ring[0]['max'][1]) / 2
        torus(K, (cx, cy, cz), 0.55, 0.14, ['pd_ring', 'pd_ring', 'pd_ring2', 'pd_ring2'], n=16, m=8)


def build(kind):
    global y0_ground
    K = Kit(os.path.join(HERE, 'boxes', kind + '.json'), seed=13)
    deco = json.load(open(os.path.join(HERE, 'boxes', kind + '_deco.json')))['boxes']
    K.ground = -4.0; y0_ground = -4.0
    bs = K.boxes
    tiles = [b for b in bs if b['mat'] == 'tile']; pool(K, tiles)
    fl = [b for b in tiles if b['max'][1] - b['min'][1] < 0.06][0]; poolz = (fl['min'][2] + fl['max'][2]) / 2
    for b in bs:
        if b['mat'] in ('white', 'toypink', 'toyteal', 'toyyellow') and abs(b['max'][1] - b['min'][1] - 0.45) < 0.01: lounger(K, b, poolz)
    posts = [b for b in bs if b['mat'] == 'wood' and b['max'][1] - b['min'][1] > 2]
    roofs = [b for b in deco if b['mat'] == 'cloth']
    for r in roofs:
        rx0, ry0, rz0, rx1, ry1, rz1 = ext(r)
        inn = lambda b: rx0 - 0.1 <= b['min'][0] and b['max'][0] <= rx1 + 0.1 and rz0 - 0.1 <= b['min'][2] and b['max'][2] <= rz1 + 0.1
        cabana(K, [p for p in posts if inn(p)], [b for b in bs if b['mat'] == 'cloth' and inn(b)], [b for b in bs if b['mat'] == 'toyteal' and abs(b['max'][1] - b['min'][1] - 0.5) < 0.01 and inn(b)][0], r)
    tires = sorted([b for b in bs if b['mat'] == 'tire'], key=lambda b: -(b['max'][0] - b['min'][0]))
    top = [b for b in bs if b['mat'] == 'metal' and b['max'][1] - b['min'][1] < 0.15][0]
    dj(K, tires[0], top, tires[1:], [b for b in deco if b['mat'] == 'grid'])
    tall = [b for b in bs if b['mat'] == 'metal' and b['max'][1] - b['min'][1] > 3]
    rigposts = [b for b in tall if b['max'][1] - b['min'][1] > 3.9]
    lightposts = [b for b in tall if b not in rigposts]
    bar = [b for b in deco if b['mat'] == 'metal' and b['max'][0] - b['min'][0] > 5]
    if rigposts and bar:
        rl = [b for b in deco if b['mat'].startswith('neon') and abs((b['min'][2] + b['max'][2]) / 2 - (bar[0]['min'][2] + bar[0]['max'][2]) / 2) < 0.05]
        rig(K, rigposts, bar[0], rl)
    else: rl = []
    bulbs = [b for b in deco if (b['mat'].startswith('neon') or b['mat'] == 'lamp') and b not in rl]
    festoon(K, lightposts, bulbs)
    for b in bs:
        if b['mat'] == 'stone': planter(K, b)
    floats(K, deco)
    for b in bs:  # anything left would be drawn plain: there shouldn't be any
        if not b.get('_done') and b['mat'] not in ('tile', 'white', 'toypink', 'toyteal', 'toyyellow', 'wood', 'cloth', 'tire', 'metal', 'stone'): print('left:', b)
    merge_mats(K, MERGE)
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in ('pooldeck', 'pooldeck_sd')] or ['pooldeck', 'pooldeck_sd']):
    build(kind)
