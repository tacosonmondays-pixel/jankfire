# The lift motor rooms on Rooftop's tower tops (shared/map.js rooftop() / rooftopSD(): a concrete box and its roof
# slab), drawn over their own boxes (tools/arch/dump.mjs), which stay what you bump into. From the real thing: the
# overrun box a lift's motor sits in on top of a tower: cast concrete walls on a tar upstand (the roof membrane turned
# up the wall), a galvanised coping round the slab with a drip edge, gravel on top and a flat hatch, a double steel
# door in a frame under a rain hood with a bulkhead lamp and DANGER signs (node 'door': S&D's tower rooms have none),
# a louvre band for the motor's air, conduits up a wall into a junction box, grime under the drip, the tower's
# colour in a band round the top and a big stencilled lift number in it (paint '@trim': the bank's / security's blue,
# the hotel's / the crashers' pink; the number per placement, nodes v0 / v1 / v2).
# And the antenna on the Rooftop rooms (rt_mast): a red and white lattice mast on a base plate, a dish half way up, the
# red aviation lamp on top (the map's red light), a whip, guy wires down to the roof.
# local frames: liftroom 6 x 10 (x +-3, z +-5), its door on -x, its louvres on +x; liftroom_sd 6 x 6; rt_mast on the
# roof (y 0 = the slab's top), the mast up y.
# run: node tools/arch/dump.mjs rooftop liftroom tools/blender/arch/boxes/liftroom.json
#      node tools/arch/dump.mjs rooftop_sd liftroom_sd tools/blender/arch/boxes/liftroom_sd.json
#      node tools/arch/dump.mjs rooftop rt_mast tools/blender/arch/boxes/rt_mast.json
#      blender52 -b --python tools/blender/arch/make_liftroom.py -- [liftroom|liftroom_sd|rt_mast]   (all by default)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'lr_wall': ('concrete', '#e4dccd', {}), 'lr_base': ('tar', '#6a6470', {}), 'lr_band@trim': ('trim', '#ffffff', {'gloss': 0.5}),
    'lr_coping': ('metalplate', '#c4c8d0', {'gloss': 0.6, 'metal': 1}), 'lr_gravel': ('tar', '#9a9488', {}), 'lr_soffit': ('concrete', '#b8b0a4', {}),
    'lr_door': ('metalplate', '#ffd23a', {'gloss': 0.7}), 'lr_frame': ('metalplate', '#3a3d46', {'gloss': 0.5}), 'lr_steel': ('metalplate', '#a2a8b2', {'gloss': 0.5, 'metal': 1}),
    'lr_louvre': ('louvre', '#8e949e', {}), 'lr_conduit': ('metalplate', '#c8ccd4', {'gloss': 0.4, 'metal': 1}), 'lr_black': ('tar', '#26242a', {}),
    'lr_lamp': ('stucco', '#fff2c8', {'glow': True, 'glowcol': '#ffe0a0'}), 'lr_red': ('trim', '#ff4040', {'glow': True, 'glowcol': '#ff2020'}),
    'lr_mastr': ('metalplate', '#e8322a', {'gloss': 0.6}), 'lr_mastw': ('metalplate', '#f4f2ee', {'gloss': 0.6}), 'lr_wire': ('tar', '#2a2a30', {}),
})
NOCAST.update({'lr_frame', 'lr_steel', 'lr_louvre', 'lr_conduit', 'lr_black', 'lr_lamp', 'lr_red', 'lr_wire', 'lr_door'})
H, TOP, CO = 4.5, 4.8, 0.2  # the walls' height, the slab's top, its overhang
E = 0.002

# stencil digits: cells (x0, y0, x1, y1) on a 3 x 5 grid, none overlapping
DIG = {'1': [(2, 0, 3, 5)], '2': [(0, 4, 3, 5), (2, 3, 3, 4), (0, 2, 3, 3), (0, 1, 1, 2), (0, 0, 3, 1)], '3': [(0, 4, 3, 5), (2, 3, 3, 4), (0, 2, 3, 3), (2, 1, 3, 2), (0, 0, 3, 1)]}


def merge_mats(K, m):
    """fewer draw calls (one per material in the game): small parts take a bigger part's material"""
    for (mat, node) in list(K.geo):
        if mat not in m: continue
        src = K.geo.pop((mat, node)); dst = K._bucket(m[mat], node); b = len(dst['v'])
        dst['v'] += src['v']; dst['uv'] += src['uv']; dst['f'] += [tuple(i + b for i in f) for f in src['f']]
MERGE = {'lr_conduit': 'lr_steel', 'lr_base': 'lr_gravel', 'metal': 'lr_steel', 'metaldark': 'lr_frame', 'lr_wire': 'lr_frame'}


def decal_node(K, node, axis, c, s, off, a, y, cell, w, h):
    """Kit.decal_on, into a node (the door's signs go when the door does)"""
    from archkit import KIT
    u0, v0, du, dv = KIT['decals']['cells'][cell]; v0 = 1 - v0 - dv
    ya, yb = y - h / 2, y + h / 2; aa, ab = a - w / 2, a + w / 2
    pts = [(aa, ya), (ab, ya), (ab, yb), (aa, yb)] if (axis == 'x' and s > 0) or (axis == 'z' and s < 0) else [(ab, ya), (aa, ya), (aa, yb), (ab, yb)]
    K.quad([K._P(axis, c, p[0], p[1], s * off) for p in pts], 'decal', uv=[(u0, v0), (u0 + du, v0), (u0 + du, v0 + dv), (u0, v0 + dv)], node=node)


def room(kind):
    K = Kit(os.path.join(HERE, 'boxes', kind + '.json'), seed=5)
    body = K.take(lambda b: b['mat'] == 'concrete')[0]; slab = K.take(lambda b: b['mat'] == 'roofg')[0]
    X = body['max'][0]; Z = body['max'][2]  # half sizes (3, 5 or 3)
    # ---- the walls, the tar upstand at their foot, the colour band under the coping
    K.box(body['min'], body['max'], {'side': 'lr_wall', 'top': None}, sub=1.5)
    def band(y0, y1, o0, o1, mat, node=''):
        """a band round all four faces, o0..o1 proud of them (the long faces carry the corners)"""
        for s in (-1, 1):
            K.box((-X - o1, y0, s * Z + (o0 if s > 0 else -o1)), (X + o1, y1, s * Z + (o1 if s > 0 else -o0)), {'all': mat}, cull=False, node=node)
            K.box((s * X + (o0 if s > 0 else -o1), y0, -Z + o0 + 0.001), (s * X + (o1 if s > 0 else -o0), y1, Z - o0 - 0.001), {'all': mat}, cull=False, node=node)
    band(0.0, 0.32, E, 0.05, 'lr_base')
    band(3.55, 4.05, E, 0.025, 'lr_band@trim')
    # ---- the slab: galvanised coping round its edge, a drip lip under it, gravel on top, the soffit
    K.box(slab['min'], slab['max'], {'top': 'lr_gravel', 'side': 'lr_coping', 'bottom': 'lr_soffit'}, sub=1.5)
    sx, sz = slab['max'][0], slab['max'][2]
    for s in (-1, 1):
        K.box((-sx - 0.025, H - 0.08, s * sz + (0 if s > 0 else -0.025)), (sx + 0.025, H + 0.004, s * sz + (0.025 if s > 0 else 0)), {'all': 'lr_coping'}, cull=False)
        K.box((s * sx + (0 if s > 0 else -0.025), H - 0.08, -sz + 0.001), (s * sx + (0.025 if s > 0 else 0), H + 0.004, sz - 0.001), {'all': 'lr_coping'}, cull=False)
    # a flat roof hatch (it's somewhere you can stand: nothing on top is taller than a hand)
    hx, hz = -1.3, -Z + 1.6
    K.box((hx - 0.5, TOP, hz - 0.5), (hx + 0.5, TOP + 0.14, hz + 0.5), {'side': 'lr_steel', 'top': 'lr_steel'}, cull=False)
    K.box((hx - 0.42, TOP + 0.14, hz - 0.42), (hx + 0.42, TOP + 0.16, hz + 0.42), {'side': 'lr_frame', 'top': 'lr_frame'}, cull=False)
    # ---- the door on -x (node 'door'): a steel frame, two yellow leaves, kick plates, handles, a rain hood, a lamp
    D = 'door'; fx = -X
    def fb(x0, x1, y0, y1, z0, z1, mat): K.box((min(x0, x1), y0, min(z0, z1)), (max(x0, x1), y1, max(z0, z1)), {'all': mat}, cull=False, node=D)
    fb(fx - E, fx - 0.07, 0.32, 2.55, -0.95, -0.82, 'lr_frame'); fb(fx - E, fx - 0.07, 0.32, 2.55, 0.82, 0.95, 'lr_frame'); fb(fx - E, fx - 0.07, 2.42, 2.55, -0.82, 0.82, 'lr_frame')
    for zs in (-1, 1):
        z0, z1 = (-0.81, -0.01) if zs < 0 else (0.01, 0.81)
        fb(fx - E, fx - 0.04, 0.33, 2.41, z0, z1, 'lr_door')
        fb(fx - 0.04, fx - 0.045, 0.36, 0.62, z0 + 0.04, z1 - 0.04, 'lr_steel')  # the kick plate
        zz = -0.12 if zs < 0 else 0.12
        FL.bar(K, (fx - 0.05, 1.25, zz), (fx - 0.11, 1.25, zz), 0.03, 'lr_steel', node=D)
        FL.bar(K, (fx - 0.11, 1.25, zz + zs * 0.016), (fx - 0.11, 1.25, zz + zs * 0.16), 0.03, 'lr_steel', node=D)
        decal_node(K, 'door', 'z', fx, -1, 0.0415, (z0 + z1) / 2, 1.75, 'sign_warn', 0.42, 0.42)  # DANGER on both leaves
    fb(fx - E, fx - 0.42, 2.62, 2.7, -1.1, 1.1, 'lr_steel')  # the rain hood
    fb(fx - 0.38, fx - 0.42, 2.56, 2.62, -1.1, 1.1, 'lr_steel')  # (its drip front)
    fb(fx - E, fx - 0.03, 2.85, 3.15, -0.12, 0.12, 'lr_frame'); fb(fx - 0.03, fx - 0.12, 2.9, 3.1, -0.09, 0.09, 'lr_lamp')  # the bulkhead lamp
    # ---- the louvres on +x: a long band of them in a steel frame (the motor's air)
    lz = min(3.5, Z - 1.0)
    K.box((X + E, 2.35, -lz - 0.08), (X + 0.06, 3.45, lz + 0.08), {'all': 'lr_steel'}, cull=False)
    K.box((X + 0.06, 2.4, -lz), (X + 0.075, 3.4, lz), {'side': 'lr_louvre', 'top': 'lr_steel', 'bottom': 'lr_steel'}, cull=False, tile=0.5)
    # ---- conduits up the +z face into a junction box, along under the band, a meter
    for (cx, r) in ((X - 0.9, 0.035), (X - 1.05, 0.03)):
        FL.tube(K, (cx, 0.32, Z + 0.06), (cx, 1.45, Z + 0.06), r, r, 'lr_conduit', n=6, caps=(False, False))
        FL.tube(K, (cx, 1.95, Z + 0.06), (cx, 3.5, Z + 0.06), r, r, 'lr_conduit', n=6, caps=(False, False))
        for y in (0.9, 2.6, 3.3): K.box((cx - 0.05, y, Z + E), (cx + 0.05, y + 0.04, Z + 0.1), {'all': 'lr_steel'}, cull=False)  # saddle clips
    K.box((X - 1.25, 1.45, Z + E), (X - 0.7, 1.95, Z + 0.16), {'all': 'lr_frame'}, cull=False)  # the junction box
    decal_node(K, '', 'x', Z + 0.16, 1, 0.0015, X - 0.975, 1.7, 'jbox', 0.45, 0.4)
    decal_node(K, '', 'x', Z, 1, 0.0015, X - 1.9, 1.5, 'meter', 0.5, 0.5)
    # ---- grime under the drip, a tag, the lift's number in the band's paint on the long faces
    for s in (-1, 1):
        for a in (-X + 1.0, X - 2.2):
            K.decal_on('x', s * Z, s, 0.012, a, H - 0.05, 'grime_run', w=1.1, h=1.6, anchor='top')
        K.decal_on('z', s * X, s, 0.012, Z - 1.3, H - 0.05, 'grime_run', w=1.0, h=1.4, anchor='top')
    decal_node(K, '', 'x', -Z, -1, 0.0015, X - 1.3, 1.1, 'tag_2', 1.8, 0.9)
    for vi, dch in enumerate('123'):
        for s in (-1, 1):  # both long faces: 1.6 m tall, stencilled in the band's colour below it
            dz = 0.008  # (each placement's digit in its own spot along the wall: they never show together, and never overlap)
            for (x0, y0, x1, y1) in DIG[dch]:
                u = 0.3; ax0 = -X + 0.6 + vi * 1.1
                a0, a1 = ax0 + x0 * u, ax0 + x1 * u; b0, b1 = 1.55 + y0 * u, 1.55 + y1 * u
                if s < 0: a0, a1 = -a1, -a0  # (from -z you look along +z: mirrored round so it reads left to right)
                K.box((a0 + 0.01, b0 + 0.01, s * Z + (E if s > 0 else -dz)), (a1 - 0.01, b1 - 0.01, s * Z + (dz if s > 0 else -E)), {'all': 'lr_band@trim'}, cull=False, node='v%d' % vi)
    merge_mats(K, MERGE)
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


def mast():
    K = Kit(os.path.join(HERE, 'boxes', 'rt_mast.json'), seed=9)
    K.take(lambda b: True)
    R = 0.22; legs = [Vector((R * math.cos(a), 0, R * math.sin(a))) for a in (math.pi / 2, math.pi / 2 + math.tau / 3, math.pi / 2 + 2 * math.tau / 3)]
    K.box((-0.36, 0, -0.36), (0.36, 0.05, 0.36), {'side': 'lr_steel', 'top': 'lr_steel'}, cull=False)  # the base plate
    for p in legs: K.box((p.x - 0.05, 0.05, p.z - 0.05), (p.x + 0.05, 0.12, p.z + 0.05), {'all': 'lr_frame'}, cull=False)  # bolts / shoes
    top = 6.0
    for k in range(6):  # the legs, banded red and white a metre at a time (aviation paint)
        y0, y1 = (0.12 if k == 0 else 0.05 + k), min(top, 0.05 + k + 1)  # (standing on their shoes)
        for p in legs: FL.tube(K, (p.x, y0, p.z), (p.x, y1, p.z), 0.028, 0.028, 'lr_mastr' if k % 2 == 0 else 'lr_mastw', n=6, caps=(False, False))
    y, i = 0.12, 0
    while y < top - 0.3:  # zigzag bracing between the legs: up one way, then back (each stops short of the next)
        for j in range(3):
            a, b = legs[j], legs[(j + 1) % 3]
            if i % 2: a, b = b, a
            p0 = Vector((a.x * 0.94, y + 0.04, a.z * 0.94)); p1 = Vector((b.x * 0.94, y + 0.46, b.z * 0.94))
            FL.bar(K, p0, p1, 0.014, 'lr_mastw' if int(y) % 2 else 'lr_mastr')
        y += 0.5; i += 1
    FL.tube(K, (0, top, 0), (0, top + 0.04, 0), 0.3, 0.3, 'lr_frame', n=8)  # the cap plate
    FL.tube(K, (0, top + 0.04, 0), (0, top + 0.14, 0), 0.12, 0.12, 'lr_frame', n=8, caps=(False, False))
    FL.tube(K, (0, top + 0.14, 0), (0, top + 0.36, 0), 0.15, 0.06, 'lr_red', n=10)  # the red aviation lamp (the map's red light)
    FL.bar(K, (0.2, top + 0.042, 0), (0.2, top + 1.1, 0), 0.02, 'lr_steel')  # a whip aerial (standing on the cap plate)
    FL.dish(K, (0.3, 3.3, 0.0), (1.0, 0.15, -0.2), r=0.42)  # a dish half way up, looking out over the city
    FL.bar(K, (0.32, 3.4, 0.0), (0.24, 0.1, 0.05), 0.02, 'lr_wire')  # its coax down the mast
    for (ax, az) in ((2.5, 1.2), (-2.5, 1.2), (0.0, -2.8)):  # guy wires to plates on the roof
        p = Vector((ax, 0, az)); leg = min(legs, key=lambda q: (q - p).length)
        FL.bar(K, (leg.x, 4.6, leg.z), (ax, 0.06, az), 0.014, 'lr_wire')
        K.box((ax - 0.1, 0, az - 0.1), (ax + 0.1, 0.06, az + 0.1), {'side': 'lr_steel', 'top': 'lr_steel'}, cull=False)
    merge_mats(K, MERGE)
    K.finish(os.path.join(OUTDIR, 'rt_mast.glb'))


for kind in ([a for a in argv if a in ('liftroom', 'liftroom_sd', 'rt_mast')] or ['liftroom', 'liftroom_sd', 'rt_mast']):
    if kind == 'rt_mast': mast()
    else: room(kind)
