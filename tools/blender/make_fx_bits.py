# x_fx_bits: the little things guns and hits throw out, as real meshes the game instances (public/js/bits.js).
#   bit_casing  a fired 5.56 NATO case, real size: 44.7 mm, 9.6 mm rim with the extractor groove, the body tapering to
#               the shoulder, a 6.4 mm neck, an open mouth you can see into, the primer in the head (brass, cartridge red)
#   bit_shell   a fired 12 gauge 2 3/4in hull: 70 mm, 16 mm brass head with its rim and primer, a fluted red hull,
#               the six-point crimp opened up a bit from the shot
#   bit_marble  a 16 mm glass marble with a cat's-eye swirl (white: the game tints each one its palette colour)
#   bit_chunk_a/b/c  rubble: a knobbly lump, a broken brick corner, a plaster flake (pale: tinted by the surface hit)
# each node's origin is its middle (they spin round it). laid out in a row for the sheet; the game reads each one
# on its own. run: blender -b --python tools/blender/make_fx_bits.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *


def build():
    brass = mat('fb_brass', 0xd9a53a, rough=0.28, metal=0.95, tex=tex_noise('fb_brass_t', 0xd9a53a, var=0.07, size=16, speck=0x9a6a1a, speck_p=0.06, seed=901))
    brass_dk = mat('fb_brass_dark', 0x8a5a1a, rough=0.4, metal=0.9)
    primer = mat('fb_primer', 0xc8a070, rough=0.3, metal=1.0)
    red = mat('fb_hull', 0xd02424, rough=0.32, clearcoat=0.8, tex=tex_stripes('fb_hull_t', 0xd02424, 0xb01c1c, size=32, width=3, diag=False))
    glass = mat('fb_marble', 0xffffff, rough=0.06, clearcoat=1.0, tex=tex_canvas('fb_swirl', 32, 32, lambda px: swirl(px)))
    rubble = mat('fb_rubble', 0xd8d2c6, rough=0.9, tex=tex_noise('fb_rubble_t', 0xd8d2c6, var=0.16, size=16, speck=0x8a8478, speck_p=0.12, seed=902))
    parts = []

    # ---- 5.56 case: the head at +z, the mouth at -z, 44.7 mm overall, centred
    L = 0.0447; b, f = L / 2, -L / 2
    prof = [(0.0, b), (0.0047, b), (0.0048, b - 0.0008), (0.0042, b - 0.0016), (0.0042, b - 0.0026), (0.0048, b - 0.0036),
            (0.0045, b - 0.0365), (0.0033, b - 0.0395), (0.0032, f), (0.0027, f), (0.0027, f + 0.012)]
    case = lathe(prof, m=brass, seg=14, name='case_body'); uv_cyl(case, 'z')
    pr = cyl(0.0019, 0.0006, pos=(0, 0, b + 0.0001), m=primer, axis='z', seg=10, name='case_primer')
    parts.append(place(part([case, pr], 'bit_casing', pivot=(0, 0, 0)), (-0.09, 0, 0)))

    # ---- 12 ga hull: brass head +z, the crimp end -z, 70 mm
    L = 0.070; b, f = L / 2, -L / 2
    head = lathe([(0.0, b), (0.0103, b), (0.0103, b - 0.0015), (0.0094, b - 0.002), (0.0094, b - 0.016), (0.0091, b - 0.0165)], m=brass, seg=16, name='sh_head')
    hull = lathe([(0.0091, b - 0.016), (0.0093, b - 0.017), (0.0093, f + 0.006), (0.0090, f + 0.002), (0.0060, f), (0.0030, f + 0.004), (0.0, f + 0.006)], m=red, seg=16, name='sh_hull'); uv_cyl(hull, 'z')
    pr2 = cyl(0.0032, 0.0008, pos=(0, 0, b + 0.0002), m=primer, axis='z', seg=12, name='sh_primer')
    ring = cyl(0.0095, 0.0012, pos=(0, 0, b - 0.0164), m=brass_dk, axis='z', seg=16, name='sh_ring')  # (the head's rolled edge)
    parts.append(place(part([head, hull, pr2, ring], 'bit_shell', pivot=(0, 0, 0)), (-0.03, 0, 0)))

    # ---- marble: 16 mm
    mb = ball(0.008, m=glass, seg=16, rings=10, name='marble')
    uv_sphere_wrap(mb)
    parts.append(place(part([mb], 'bit_marble', pivot=(0, 0, 0)), (0.02, 0, 0)))

    # ---- rubble: three shapes, ~6-8 cm (the game scales them per hit)
    a = ball(0.032, m=rubble, seg=7, rings=5, name='lump', scale=(1.1, 0.8, 0.95))
    jitter(a, 0.007, seed=11, along_normal=False); flat(a)
    parts.append(place(part([a], 'bit_chunk_a', pivot=(0, 0, 0)), (0.07, 0, 0)))
    c = box((0.07, 0.035, 0.045), m=rubble, bev=0.002, name='brick', taper=(0.55, 0.8))
    jitter(c, 0.003, seed=12, along_normal=False); flat(c)
    parts.append(place(part([c], 'bit_chunk_b', pivot=(0, 0, 0)), (0.15, 0, 0)))
    d = side([(-0.035, 0.0), (-0.01, 0.028), (0.03, 0.022), (0.038, -0.01), (0.005, -0.03), (-0.028, -0.02)], 0.012, m=rubble, name='flake')
    jitter(d, 0.002, seed=13, along_normal=False); flat(d)
    parts.append(place(part([d], 'bit_chunk_c', pivot=(0, 0, 0)), (0.23, 0, 0)))

    for p in parts:
        if p.name.startswith('bit_chunk'): uv_box(p, 0.05)
    return finish('x_fx_bits', parts, dict(id='x_fx_bits', kind='fx', bits=[p.name for p in parts]))


def place(o, pos):  # move a finished part (origin already at its middle) to its spot in the row
    o.location = gv(*pos)
    return o


def flat(o):  # faceted: rubble reads as broken, not melted
    for p in o.data.polygons: p.use_smooth = False
    return o


def uv_sphere_wrap(o):  # simple lat/long uv so the swirl wraps round the marble
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co.normalized()
            uv[li].uv = (0.5 + math.atan2(v.y, v.x) / (2 * math.pi), 0.5 + math.asin(max(-1, min(1, v.z))) / math.pi)


def swirl(px):  # a white marble with a pale grey cat's-eye vane: the game's tint makes it any colour
    h, w = px.shape[:2]
    for y in range(h):
        for x in range(w):
            t = x / w * 2 * math.pi
            band = abs(((y / h) - 0.5 - 0.22 * math.sin(t * 2)) * 6.0)
            k = 0.55 if band < 0.5 else 1.0
            px[y, x] = (k, k, k)


if __name__ == '__main__':
    main(build, 'x_fx_bits', views=('persp', 'top', 'front'))
