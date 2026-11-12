# The small buildings on both Warehouse maps, each a shell() (shared/map.js) drawn over its own boxes with the kit's
# dress_shell (walls with every window framed and the doors swung open, the floors, the stairs done properly, the
# roof) plus what makes each one itself:
#   wh_office      the foreman's office in the hall's corner (Warehouse): a two-storey in-plant office in pink
#                  profiled panels, hot pink corners and courses, the stairs to the roof, a railed roof deck, an AC box,
#                  a red light over the door and the foreman's notices
#   wh_office_sd   the same office, one storey, in the middle of S&D's hall
#   wh_booth       the guard booth at the gate (both maps): a teal gatehouse with a red fascia, a CCTV camera on a
#                  bracket, an amber beacon, VISITORS sign
#   wh_dispatch    S&D's dispatch booth: the same family, bigger, a phone and a clock outside
#   wh_siteoffice  the site office in Warehouse's car park: a portable cabin, blue ribbed steel, dark corner posts and
#                  base frame with fork pockets, security grilles over the windows, lifting eyes, an AC box
# The desks, TVs and the cabin's OFFICE board stay the game's. local frame = each shell()'s.
# run: node tools/arch/dump.mjs warehouse wh_office tools/blender/arch/boxes/wh_office.json  (and the same for each id)
#      blender52 -b --python tools/blender/arch/make_wh_offices.py -- [ids...]   (all by default)
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST, dress_shell

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'ofpanel': ('profile', '#ff96d4', {}), 'ofpink': ('trim', '#ff4fd8', {}), 'ofband': ('concrete', '#6a6872', {}), 'ofcarpet': ('carpet', '#e0a848', {}),
    'ofint': ('stucco', '#f2eadc', {}), 'ofteal': ('stucco', '#2ac0b8', {}), 'ofred': ('trim', '#e8302a', {}), 'oftile': ('lino', '#ffffff', {}),
    'ofcabin': ('profile', '#3a7ad0', {}), 'ofdark': ('metalplate', '#3a3e46', {}), 'ofgrey': ('metalplate', '#c8ccd2', {}), 'ofroof': ('tar', '#ffffff', {}),
    'oflamp': ('stucco', '#ff3a2a', {'glow': True, 'glowcol': '#ff3a2a'}), 'ofamber': ('stucco', '#ffb030', {'glow': True}), 'ofglass': ('glass', '#ffffff', {}),
    'ofvent': ('louvre', '#c0c4ca', {}), 'ofblack': ('tar', '#1e1e24', {}),
})
NOCAST.update({'ofpink', 'ofred', 'ofdark', 'ofgrey', 'oflamp', 'ofamber', 'ofglass', 'ofvent', 'ofblack'})
# id: (w, d, floors, F, wall material, ext, int, floor, roof, cap, band, course, corners)
SPEC = {
    'wh_office': (11, 8.4, 2, 3.6, 'magenta', 'ofpanel', 'ofint', 'ofcarpet', 'ofroof', 'ofgrey', 'ofband', 'ofpink', 'ofpink'),
    'wh_office_sd': (8, 10, 1, 3.2, 'magenta', 'ofpanel', 'ofint', 'ofcarpet', 'ofroof', 'ofgrey', 'ofband', 'ofpink', 'ofpink'),
    'wh_booth': (4, 3.4, 1, 2.8, 'toyteal', 'ofteal', 'ofint', 'oftile', 'ofroof', 'ofred', 'ofband', 'ofred', 'ofred'),
    'wh_dispatch': (6, 4.4, 1, 2.9, 'toyteal', 'ofteal', 'ofint', 'oftile', 'ofroof', 'ofred', 'ofband', 'ofred', 'ofred'),
    'wh_siteoffice': (10, 4.2, 1, 3.0, 'containerb', 'ofcabin', 'ofint', 'ofcarpet', 'ofroof', 'ofdark', 'ofdark', 'ofdark', 'ofdark'),
}


def dress_opening(self, axis, c, t, a0, a1, y0, y1, door, trim, frames, sill, shards, doors):
    """the kit's dress_opening (archkit.py), with the jamb casings stopping under the head casing (no overlap where they
    meet) and the sill grime a hair closer to the wall"""
    r = self.rng
    side = self.outward(axis, c, a0, a1, y0, y1, t)
    cw, cd = 0.09, 0.035
    for s in [1, -1]:
        o0, o1 = (t / 2, t / 2 + cd) if s > 0 else (-t / 2 - cd, -t / 2)
        if frames:
            self.wbox(axis, c, a0 - cw, a0, y0 if door else y0 - 0.02, y1, o0, o1, {'all': trim})
            self.wbox(axis, c, a1, a1 + cw, y0 if door else y0 - 0.02, y1, o0, o1, {'all': trim})
            self.wbox(axis, c, a0 - cw - 0.02, a1 + cw + 0.02, y1, y1 + cw + 0.03, o0 - (0.02 if s < 0 else 0), o1 + (0.02 if s > 0 else 0), {'all': trim})
        if not door and sill and s == (side or 1):
            so0, so1 = (t / 2, t / 2 + 0.09) if s > 0 else (-t / 2 - 0.09, -t / 2)
            self.wbox(axis, c, a0 - cw - 0.04, a1 + cw + 0.04, y0 - 0.05, y0, so0, so1, {'all': trim})
            if r.random() < 0.5: self.decal_on(axis, c, s, t / 2 + 0.002, (a0 + a1) / 2, y0 - 0.06, 'grime_run', w=(a1 - a0) * 0.9, h=min(1.0, y0 - 0.1), anchor='top')
    if not door and shards:
        for (ca, cy, da, dy) in ((a0, y0, 1, 1), (a1, y0, -1, 1), (a0, y1, 1, -1), (a1, y1, -1, -1)):
            if r.random() < 0.55:
                L1, L2 = 0.12 + r.random() * 0.22, 0.1 + r.random() * 0.25
                pA = self._P(axis, c, ca, cy, 0.0); pB = self._P(axis, c, ca + da * L1, cy, 0.0); pC = self._P(axis, c, ca, cy + dy * L2, 0.0)
                self.tri([pA, pB, pC], 'glass'); self.tri([pA, pC, pB], 'glass')
    if door and doors and t >= 0.15:
        w = a1 - a0
        leaves = [(a0, 1)] if w < 1.3 else [(a0, 1), (a1, -1)]
        lw = w / len(leaves)
        s_in = -side if side else 1
        for hinge, d in leaves:
            o = s_in * (t / 2 + 0.02)
            p0 = self._P(axis, c, hinge, y0 + 0.02, o); far = self._P(axis, c, hinge - d * lw * 0.98, y0 + 0.02, o + s_in * 0.12)
            self.slab_between(p0, far, min(2.2, y1 - y0 - 0.06), 0.045, 'door')


Kit.dress_opening = dress_opening


def build(kind):
    w, d, floors, F, wm, ext, intm, floor, roof, cap, band, course, corners = SPEC[kind]
    K = Kit(os.path.join(HERE, 'boxes', kind + '.json'), seed=len(kind))
    dress_shell(K, w, d, floors, F, ext, intm=intm, floor=floor, roof=roof, cap=cap, band=band, course=course, corners=corners, wall_mat=wm)
    hw, hd, top = w / 2, d / 2, floors * F + 0.3
    E = 0.152  # out from a wall's centre plane to a hair past its face
    box = lambda mn, mx, m: K.box(mn, mx, m if isinstance(m, dict) else {'all': m}, cull=False)
    # a fascia round the roof's edge (the shells here have no parapet, or a low one) and a coping
    if kind != 'wh_office':
        yt = floors * F  # the walls' tops stick out past the roof slab and overlap at the corners: under the fascia, dropped
        for (mat, node), g in K.geo.items():
            if mat == 'trim': g['f'] = [f for f in g['f'] if not all(abs(g['v'][i][1] - yt) < 1e-4 for i in f)]
        box((-hw - 0.08, top - 0.32, -hd - 0.08), (hw + 0.08, top + 0.04, -hd + 0.1), cap)
        box((-hw - 0.08, top - 0.32, hd - 0.1), (hw + 0.08, top + 0.04, hd + 0.08), cap)
        box((-hw - 0.08, top - 0.32, -hd + 0.1), (-hw + 0.1, top + 0.04, hd - 0.1), cap)
        box((hw - 0.1, top - 0.32, -hd + 0.1), (hw + 0.08, top + 0.04, hd - 0.1), cap)
    if kind in ('wh_office', 'wh_office_sd'):
        # a red light over the front door, the foreman's notices, an AC box on the side wall with its drip
        box((-0.2, 2.62, -hd - 0.17), (0.2, 2.82, -hd - 0.15), 'ofdark')
        FL.tube(K, (0, 2.72, -hd - 0.17), (0, 2.72, -hd - 0.27), 0.09, 0.09, 'oflamp', n=8)
        sa = 1.6 if kind == 'wh_office' else 3.4  # (between the door and the windows)
        K.decal_on('x', -hd, -1, E, sa, 1.5, 'sign_help', w=0.55, h=0.55)
        K.decal_on('x', -hd, -1, E, -sa + 0.05, 1.45, 'poster_2', w=0.5, h=0.75)
        K.decal_on('z', hw, 1, E, -hd + 1.2, 1.6, 'meter', w=0.45, h=0.45)
        box((hw + 0.15, 2.3, -0.5), (hw + 0.6, 2.9, 0.5), {'all': 'ofgrey', 'px': 'ofvent'})
        K.decal_on('z', hw, 1, E, 0, 2.3, 'grime_run', w=0.8, h=1.4, anchor='top')
    if kind == 'wh_office':
        # the roof deck's railing (the stairs come up through the roof) and a vent stack
        y = top + 0.06
        for (a, b) in (((-hw + 0.1, -hd + 0.1), (hw - 0.1, -hd + 0.1)), ((hw - 0.1, -hd + 0.1), (hw - 0.1, hd - 0.1)), ((-hw + 0.1, -hd + 0.1), (-hw + 0.1, hd - 0.1))):
            FL.bar(K, (a[0], y + 1.0, a[1]), (b[0], y + 1.0, b[1]), 0.05, 'ofpink')
            FL.bar(K, (a[0], y + 0.5, a[1]), (b[0], y + 0.5, b[1]), 0.035, 'ofgrey')
        for x in (-hw + 0.1, -hw / 3, hw / 3, hw - 0.1):
            for z in (-hd + 0.1, hd - 0.1): FL.bar(K, (x, y, z), (x, y + 1.02, z), 0.04, 'ofgrey')
        FL.tube(K, (hw - 1.2, y, hd - 1.2), (hw - 1.15, y + 1.3, hd - 1.2), 0.12, 0.12, 'ofgrey', n=8)
        FL.tube(K, (hw - 1.15, y + 1.3, hd - 1.2), (hw - 1.15, y + 1.48, hd - 1.2), 0.24, 0.08, 'ofdark', n=8)
    if kind in ('wh_booth', 'wh_dispatch'):
        # an amber beacon on the roof, a CCTV camera on a bracket off the front corner, the VISITORS sign
        FL.tube(K, (hw - 0.5, top + 0.04, -hd + 0.5), (hw - 0.5, top + 0.1, -hd + 0.5), 0.14, 0.14, 'ofdark', n=8)
        FL.tube(K, (hw - 0.5, top + 0.1, -hd + 0.5), (hw - 0.5, top + 0.32, -hd + 0.5), 0.1, 0.08, 'ofamber', n=8, caps=(False, True))
        FL.bar(K, (-hw - 0.08, 2.5, -hd - 0.08), (-hw - 0.45, 2.55, -hd - 0.45), 0.05, 'ofdark')
        box((-hw - 0.62, 2.38, -hd - 0.62), (-hw - 0.32, 2.58, -hd - 0.3), 'ofgrey')
        FL.tube(K, (-hw - 0.47, 2.48, -hd - 0.62), (-hw - 0.47, 2.48, -hd - 0.66), 0.06, 0.06, 'ofblack', n=8)
        K.decal_on('x', -hd, -1, E, -hw + 0.6 if kind == 'wh_booth' else -hw + 1.0, 1.55, 'sign_help', w=0.5, h=0.5)
        if kind == 'wh_dispatch':
            box((hw - 0.9, 1.2, -hd - 0.27), (hw - 0.6, 1.6, -hd - 0.18), 'ofred')  # the phone
            FL.tube(K, (-hw + 1.6, 2.4, -hd - 0.18), (-hw + 1.6, 2.4, -hd - 0.24), 0.2, 0.2, 'ofgrey', n=10)  # the clock
            FL.tube(K, (-hw + 1.6, 2.4, -hd - 0.24), (-hw + 1.6, 2.4, -hd - 0.245), 0.17, 0.17, 'ofint', n=10, caps=(False, True))
    if kind == 'wh_siteoffice':
        # the cabin's base frame with fork pockets, lifting eyes on the roof's corners, grilles over the windows, an AC box
        for (z, s) in ((-hd, -1), (hd, 1)):
            for x in (-hw / 3, hw / 3):
                K.quad([(x - 0.4, 0.05, z + s * 0.185), (x + 0.4, 0.05, z + s * 0.185), (x + 0.4, 0.25, z + s * 0.185), (x - 0.4, 0.25, z + s * 0.185)][::(1 if s > 0 else -1)], 'ofblack')
        for sx in (-1, 1):
            for sz in (-1, 1):
                FL.tube(K, (sx * (hw - 0.2), top + 0.04, sz * (hd - 0.2) - 0.05), (sx * (hw - 0.2), top + 0.04, sz * (hd - 0.2) + 0.05), 0.12, 0.12, 'ofdark', n=8)
        for (axis, c, t, _), bs in K.walls([b for b in K.boxes if b['mat'] == wm], tmax=0.31).items():  # security grilles
            so = 1 if c > 0 else -1
            P = (lambda a, y, o: (a, y, c + o)) if axis == 'x' else (lambda a, y, o: (c + o, y, a))
            for (a0, a1, y0, y1, isdoor) in K.openings(axis, bs):
                if isdoor: continue
                o = so * (t / 2 + 0.06)
                n = int((a1 - a0) / 0.14)
                for k in range(1, n):
                    aa = a0 + k * (a1 - a0) / n
                    FL.bar(K, P(aa, y0 - 0.06, o), P(aa, y1 + 0.06, o), 0.022, 'ofdark')
                for yy in (y0 + 0.02, (y0 + y1) / 2, y1 - 0.02): FL.bar(K, P(a0 - 0.06, yy, o + so * 0.015), P(a1 + 0.06, yy, o + so * 0.015), 0.028, 'ofdark')
        box((-hw - 0.55, 1.9, -0.6), (-hw - 0.15, 2.5, 0.6), {'all': 'ofgrey', 'nx': 'ofvent'})
        K.decal_on('z', -hw, -1, E, 1.6, 1.5, 'sign_warn', w=0.5, h=0.5)
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in SPEC] or list(SPEC)):
    build(kind)
