# Rooftop's roof signs (shared/map.js rooftop() / rooftopSD(): signArch): JANK BANK, HOTEL 4 HOURS and the ☺ CORP flag,
# the steel that holds them, drawn over the posts' boxes (tools/arch/dump.mjs), which stay what you bump into. The
# pictures stay the game's (the map's picture boxes, listed below). From real rooftop sign structures: wide-flange
# posts on bolted base plates, a chrome bezel round the face, angle girts and cross-bracing behind it, kickers down to
# the parapet, a grated catwalk with a rail along the back, gooseneck floodlights over the top shining down on it; the
# hotel's and the flag's faces outlined in neon (pink, cyan). Everything sits behind, around or above the face: nothing
# new to stand on in front of it.
# local frame = the map's (one placement at the origin); the faces look +z (into the roof), the parapet behind them.
# run: node tools/arch/dump.mjs rooftop rt_signs tools/blender/arch/boxes/rt_signs.json
#      node tools/arch/dump.mjs rooftop_sd rt_signs_sd tools/blender/arch/boxes/rt_signs_sd.json
#      blender52 -b --python tools/blender/arch/make_signs.py -- [rt_signs|rt_signs_sd]   (both by default)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'sg_steel': ('metalplate', '#3a3f58', {'gloss': 0.5}), 'sg_chrome': ('metalplate', '#e6e9f0', {'gloss': 0.85, 'metal': 1}),
    'sg_grate': ('metalplate', '#6a6e78', {}), 'sg_lamp': ('stucco', '#fff4d8', {'glow': True, 'glowcol': '#ffe8b0'}),
    'sg_neonpink': ('trim', '#ff7ae0', {'glow': True, 'glowcol': '#ff4fd8'}), 'sg_neoncyan': ('trim', '#8aeaff', {'glow': True, 'glowcol': '#4fd8ff'}),
})
NOCAST.update({'sg_chrome', 'sg_grate', 'sg_lamp', 'sg_neonpink', 'sg_neoncyan'})
# the pictures (shared/map.js: the 'adjankbank' / 'neonhotel' / 'flagcorp' boxes): x0, x1, y0, y1, their back and front z, neon
FACES = {
    'rt_signs': [(-52, -38, 2.2, 6.2, -17.42, -17.38, None), (38, 54, 2.2, 6.2, -17.42, -17.38, 'sg_neonpink')],
    'rt_signs_sd': [(-54, -38, 2.2, 6.2, -57.42, -57.38, None), (38, 54, 2.2, 6.2, -57.42, -57.38, 'sg_neonpink'), (-8, 8, 2.5, 6.8, -69.42, -69.38, 'sg_neoncyan')],
}
PAR = 1.0  # the parapet's top (y), 0.4 behind the posts


def bx(K, mn, mx, mat): K.box(tuple(mn), tuple(mx), mat if isinstance(mat, dict) else {'all': mat}, cull=False)


def post(K, b):
    """a wide-flange column in the post's box (flanges across x, the web along z), a base plate with bolts, a cap"""
    (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']; cx = (x0 + x1) / 2
    bx(K, (x0 - 0.15, y0, z0 - 0.15), (x1 + 0.15, y0 + 0.03, z1 + 0.15), 'sg_steel')
    for (ox, oz) in ((-0.22, -0.22), (0.22, -0.22), (-0.22, 0.22), (0.22, 0.22)):
        FL.tube(K, (cx + ox, y0 + 0.03, (z0 + z1) / 2 + oz), (cx + ox, y0 + 0.07, (z0 + z1) / 2 + oz), 0.03, 0.03, 'sg_chrome', n=6)
    bx(K, (x0, y0 + 0.03, z0), (x0 + 0.04, y1, z1), 'sg_steel'); bx(K, (x1 - 0.04, y0 + 0.03, z0), (x1, y1, z1), 'sg_steel')  # flanges
    bx(K, (cx - 0.015, y0 + 0.03, z0 + 0.001), (cx + 0.015, y1, z1 - 0.001), 'sg_steel')  # the web
    bx(K, (x0 - 0.02, y1, z0 - 0.02), (x1 + 0.02, y1 + 0.03, z1 + 0.02), 'sg_steel')  # the cap


def sign(K, f, posts):
    x0, x1, y0, y1, zb, zf, neon = f
    W = 0.15
    # the bezel: a chrome channel round the face's edges, wrapping its thickness (never over the picture)
    bx(K, (x0 - W, y1, zb - 0.06), (x1 + W, y1 + W, zf + 0.06), 'sg_chrome'); bx(K, (x0 - W, y0 - W, zb - 0.06), (x1 + W, y0, zf + 0.06), 'sg_chrome')
    bx(K, (x0 - W, y0, zb - 0.06), (x0, y1, zf + 0.06), 'sg_chrome'); bx(K, (x1, y0, zb - 0.06), (x1 + W, y1, zf + 0.06), 'sg_chrome')
    # behind: angle girts across, cross-bracing between the posts, kickers to the parapet
    zg0, zg1 = zb - 0.14, zb - 0.07
    for y in (y0 + 0.3, (y0 + y1) / 2, y1 - 0.3):
        bx(K, (x0 + 0.02, y - 0.04, zg0), (x1 - 0.02, y + 0.04, zg1), 'sg_steel')
    pxs = sorted((p['min'][0] + p['max'][0]) / 2 for p in posts)
    zpb = min(p['min'][2] for p in posts)  # the posts' back
    for a, b_ in zip(pxs, pxs[1:]):
        FL.bar(K, (a + 0.22, y0 + 0.4, zg0 - 0.04), (b_ - 0.22, y1 - 0.4, zg0 - 0.04), 0.05, 'sg_steel')
        FL.bar(K, (a + 0.22, y1 - 0.4, zg0 - 0.1), (b_ - 0.22, y0 + 0.4, zg0 - 0.1), 0.05, 'sg_steel')
    for px in pxs:
        FL.bar(K, (px, y0 + 1.8, zpb - 0.03), (px, PAR + 0.03, zpb - 0.55), 0.08, 'sg_steel')
        bx(K, (px - 0.12, PAR, zpb - 0.66), (px + 0.12, PAR + 0.03, zpb - 0.44), 'sg_steel')  # its shoe on the parapet
    # the catwalk along the back at the face's foot: grating on brackets, a rail with posts
    cy = y0 - 0.25; cz0, cz1 = zpb - 0.75, zpb - 0.02
    bx(K, (x0, cy - 0.05, cz0), (x1, cy, cz1), {'top': 'sg_grate', 'bottom': 'sg_grate', 'side': 'sg_steel'})
    n = max(2, int((x1 - x0) / 2.0))
    for k in range(n + 1):
        x = x0 + 0.05 + k * (x1 - x0 - 0.1) / n
        bx(K, (x - 0.025, cy, cz0 + 0.015), (x + 0.025, cy + 0.97, cz0 + 0.055), 'sg_steel')  # (under the top rail)
        FL.bar(K, (x, cy - 0.05, cz0 + 0.05), (x, cy - 0.5, cz1 - 0.02), 0.04, 'sg_steel')  # a bracket under it
    for h in (0.5, 1.0): bx(K, (x0, cy + h - 0.03, cz0 + 0.01), (x1, cy + h, cz0 + 0.06), 'sg_chrome')
    # gooseneck floodlights over the top, reaching out in front and looking back down at the face
    m = max(3, int((x1 - x0) / 4.5))
    for k in range(m):
        x = x0 + (k + 0.5) * (x1 - x0) / m
        top = y1 + W
        FL.bar(K, (x, top - 0.06, (zb + zf) / 2), (x, top + 0.35, (zb + zf) / 2), 0.05, 'sg_steel')  # (its foot inside the bezel)
        FL.bar(K, (x, top + 0.35, (zb + zf) / 2), (x, top + 0.42, zf + 0.75), 0.05, 'sg_steel')
        FL.tube(K, (x, top + 0.48, zf + 0.7), (x, top + 0.28, zf + 0.92), 0.14, 0.16, 'sg_steel', n=8)  # the head, tipped back down
        FL.tube(K, (x, top + 0.281, zf + 0.921), (x, top + 0.27, zf + 0.93), 0.14, 0.14, 'sg_lamp', n=8, caps=(False, True))
    if neon:  # a neon tube round the face, just in front of the bezel
        o = zf + 0.1; r = 0.035; e = 0.06
        FL.bar(K, (x0 - e, y1 + e, o), (x1 + e, y1 + e, o), r * 2, neon); FL.bar(K, (x0 - e, y0 - e, o), (x1 + e, y0 - e, o), r * 2, neon)
        o2 = o - 0.004  # (the uprights a hair deeper than the runs: where they meet, no face shares a plane)
        FL.bar(K, (x0 - e, y0 - e + r + 0.003, o2), (x0 - e, y1 + e - r - 0.003, o2), r * 2, neon); FL.bar(K, (x1 + e, y0 - e + r + 0.003, o2), (x1 + e, y1 + e - r - 0.003, o2), r * 2, neon)
        for x in (x0 + 0.6, x1 - 0.6):  # its stand-offs
            for y in (y1 + e, y0 - e): bx(K, (x - 0.02, y - 0.02, zf + 0.06), (x + 0.02, y + 0.02, o - r), 'sg_chrome')


def build(kind):
    K = Kit(os.path.join(HERE, 'boxes', kind + '.json'), seed=17)
    posts = K.take(lambda b: b['mat'] == 'metal')
    for p in posts: post(K, p)
    for f in FACES[kind]:
        x0, x1, zb = f[0], f[1], f[4]
        sign(K, f, [p for p in posts if x0 <= (p['min'][0] + p['max'][0]) / 2 <= x1 and abs((p['min'][2] + p['max'][2]) / 2 - (zb + 0.02)) < 0.5])
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in FACES] or list(FACES)):
    build(kind)
