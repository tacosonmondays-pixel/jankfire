# OVERDUE story props, THE GUT (part 2): the overgrown SUDS & SONS launderette, the Gristle & Sons Biologics sign,
# and the flesh blobs that creep over the Bottom's pastel houses. Wall props: origin bottom centre ON the wall plane
# (z = 0), the prop sticks out toward -z. Each glb also carries *_lod1 meshes (~25% tris) the game draws far away.
# run: blender -b --python tools/blender/make_story_gut2.py [-- --only=launderette,gristlelogo --no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gutkit import *
from gutkit import _image, _obj, _link, _place, _waves, _paint_eye
import make_story_gut as G1  # tongue_obj (importing it does not build: see the __main__ guard there)


def meta_of(id_, **kw):
    d = {'kind': 'prop', 'id': id_, 'story': True, 'district': 'gut'}; d.update(kw); return d


class Atlas:
    """one glossy material whose texture holds painted regions (sign text, portholes, an eye) plus a strip of flat
    colour swatches, so a whole facade keeps a couple of materials."""
    def __init__(self, name, W, H, regions, swatches, rough=0.28, clearcoat=0.7):
        self.W, self.H, self.R, self.sw = W, H, {}, swatches
        px = np.zeros((H, W, 3), dtype=np.float32)
        y0 = H - 8
        for k, c in enumerate(swatches): px[y0:H, k * 8:(k + 1) * 8] = hexrgb(c)
        for key, (x0, y0_, w, h, paint) in regions.items():
            sub = np.zeros((h, w, 3), dtype=np.float32); paint(sub); px[y0_:y0_ + h, x0:x0 + w] = sub
            self.R[key] = (x0, y0_, w, h)
        self.m = mat(name, 0xffffff, rough=rough, clearcoat=clearcoat, tex=_image(name + '_t', np.clip(px, 0, 1)))

    def swatch(self, o, k):
        me = o.data
        if not me.uv_layers: me.uv_layers.new(name='UVMap')
        u, v = (k * 8 + 4) / self.W, 1 - (self.H - 4) / self.H
        for l in me.uv_layers.active.data: l.uv = (u, v)
        o['keepuv'] = 1
        if not len(me.materials): me.materials.append(self.m)
        else: me.materials[0] = self.m
        return o

    def region(self, o, key, proj):
        """proj(game xyz) -> (s, t) in 0..1 (t = 1 at the top of the region)."""
        x0, y0, w, h = self.R[key]
        me = o.data
        if not me.uv_layers: me.uv_layers.new(name='UVMap')
        lay = me.uv_layers.active.data
        for poly in me.polygons:
            for li in poly.loop_indices:
                g = gg(o.matrix_world @ me.vertices[me.loops[li].vertex_index].co)
                s, t = proj(g); s = min(max(s, 0.01), 0.99); t = min(max(t, 0.01), 0.99)
                lay[li].uv = ((x0 + s * w) / self.W, 1 - (y0 + (1 - t) * h) / self.H)
        o['keepuv'] = 1
        if not len(me.materials): me.materials.append(self.m)
        else: me.materials[0] = self.m
        return o


def front_proj(cx, cy, w, h):  # a face seen from -z: viewer's right = +x
    return lambda g: ((g[0] - cx) / w + 0.5, (g[1] - cy) / h + 0.5)


def tex_brick(name, base=0xe88a7a, mortar=0xf6d8c8, size=64, seed=1):
    r = np.random.default_rng(seed)
    px = np.zeros((size, size, 3), dtype=np.float32)
    px[:] = hexrgb(mortar)
    bh, bw = 8, 16
    for row in range(size // bh):
        off = (bw // 2) * (row % 2)
        for col in range(-1, size // bw + 1):
            x0 = col * bw + off; y0 = row * bh
            c = hexrgb(base) * r.uniform(0.85, 1.1)
            if r.random() < 0.12: c = hexrgb(0xd06a8a)
            xs, xe = max(0, x0 + 1), min(size, x0 + bw - 1)
            if xe > xs: px[y0 + 1:y0 + bh - 1, xs:xe] = c
    px *= (0.94 + 0.1 * r.random((size, size)))[:, :, None]
    return _image(name, np.clip(px, 0, 1))


# ---------------------------------------------------------------- 7. the SUDS & SONS launderette, grown over
def _ld_sign(px):
    px[:] = hexrgb(0x2fb8a8)
    px[1:3, :] = hexrgb(0xffe14d); px[-3:-1, :] = hexrgb(0xffe14d)
    text_px(px, 'SUDS & SONS', 30, 6, 2, 0x1a1030)
    text_px(px, 'SUDS & SONS', 29, 5, 2, 0xffe14d)
    text_px(px, 'LAUNDERETTE  COIN OP', 36, 25, 1, 0xfff4e0)
    px_disc(px, 14, 19, 9, 0xfff4e0); px_disc(px, 14, 19, 6, 0x9fd8ff)  # a little porthole logo each end
    px_disc(px, 177, 19, 9, 0xfff4e0); px_disc(px, 177, 19, 6, 0x9fd8ff)


def _ld_suds(px):
    rng = np.random.default_rng(71)
    h, w = px.shape[:2]
    px[:] = hexrgb(0x3a7ad8)
    px[: h // 2] = hexrgb(0x6aaef0)
    for k in range(26):
        px_disc(px, rng.uniform(0, w), rng.uniform(h * 0.25, h * 0.7), rng.uniform(2, 6), 0xffffff)
    px_disc(px, w * 0.3, h * 0.3, 5, 0xe8f4ff)
    px[h // 2 + 6:h // 2 + 10, 10:24] = hexrgb(0xff4fd8)  # a pink sock going round


def _ld_card(px):
    px[:] = hexrgb(0xfff4e0)
    px[0, :] = px[-1, :] = hexrgb(0xff4fd8); px[:, 0] = px[:, -1] = hexrgb(0xff4fd8)
    text_px(px, 'SERVICE', 3, 3, 1, 0x1a1030)
    text_px(px, 'WASH', 3, 12, 1, 0x1a1030)
    text_px(px, '2 TEETH', 3, 22, 1, 0xd8203a)


def _ld_stripes(px):
    h, w = px.shape[:2]
    for x in range(w): px[:, x] = hexrgb(0x9ff0d8 if (x // 8) % 2 == 0 else 0xffb3c7)
    px[h - 6:, :] *= 0.85


LD_SW = [0xfff8ee, 0xc8ccd4, 0x2a1030, 0x2fb8a8, 0xffe14d, 0x9ff0d8, 0x5a0c26, 0xf8ecd2, 0x8a6a5a, 0xff4fd8, 0x3a3346, 0xd8203a]
# 0 machine white, 1 chrome, 2 black, 3 teal, 4 yellow, 5 mint tile, 6 throat, 7 tooth, 8 frame brown, 9 pink, 10 dark, 11 red


def build_launderette(M):
    AT = Atlas('ld_atlas', 192, 112, {'sign': (0, 0, 192, 40, _ld_sign), 'eye': (0, 40, 64, 64, _paint_eye), 'suds': (64, 40, 64, 64, _ld_suds),
                                      'card': (128, 40, 48, 32, _ld_card), 'stripes': (128, 72, 64, 32, _ld_stripes)}, LD_SW)
    brick = mat('ld_brick', 0xffffff, rough=0.45, clearcoat=0.3, tex=tex_brick('ld_brick_t', seed=72))
    glass = mat('ld_glass', 0xbff4ff, rough=0.05, alpha=0.28, clearcoat=1.0)
    flesh, vein = M['flesh'], M['vein']
    P = []; A = P.append
    sw = lambda o, k: A(AT.swatch(o, k))
    D = 0.6  # facade depth off the wall
    def brk(w, h, x, y, d=D, z=None):
        o = box((w, h, d), (x, y, -d / 2 if z is None else z), brick, bev=0.025, seg=1); uv_box(o, 1.0); o['keepuv'] = 1; A(o); return o
    brk(0.45, 5.0, -3.775, 2.5)            # left pier
    brk(1.0, 5.0, 0.3, 2.5)                # middle pier
    brk(1.8, 5.0, 3.1, 2.5)                # right pier
    brk(3.55, 2.1, -1.875, 3.95)           # over the window
    brk(1.4, 2.6, 1.5, 3.7)                # over the door
    sw(box((3.5, 0.7, 0.2), (-1.875, 0.35, -0.48), None, bev=0.02, seg=1), 3)  # teal stall riser under the window
    sw(box((8.1, 0.25, 0.75), (0, 4.88, -0.375), None, bev=0.03, seg=1), 0)    # cornice
    # the fascia sign, proud of the brick, on a yellow frame
    sg = box((6.4, 0.86, 0.12), (-0.55, 3.55, -0.68), None, bev=0.02, seg=1)
    bpy.context.view_layer.update(); A(AT.region(sg, 'sign', front_proj(-0.55, 3.55, 6.4, 0.86)))
    sw(box((6.6, 1.02, 0.08), (-0.55, 3.55, -0.6), None, bev=0.02, seg=1), 4)
    # the shop window: interior wall of mint tiles, four front loaders, a pane of glass, a white frame
    sw(box((3.55, 2.2, 0.05), (-1.875, 1.8, -0.03), None), 5)
    for k, x in enumerate((-3.25, -2.45, -1.65, -0.85)):
        sw(box((0.7, 0.92, 0.38), (x, 0.92 + 0.0, -0.25), None, bev=0.04, seg=1), 0)   # body (stands on the shop floor; the riser hides its feet)
        sw(box((0.66, 0.12, 0.05), (x, 1.33, -0.45), None, bev=0.01, seg=1), 10)       # control strip
        sw(cyl(0.035, 0.05, (x + 0.22, 1.33, -0.48), None, axis='z', seg=6), 4)        # knob
        A(AT.swatch(lathe([(0.25, -0.02), (0.27, 0.0), (0.25, 0.03), (0.2, 0.03), (0.19, 0.0)], (x, 0.95, -0.465), None, seg=14, axis='z', cap=False, name='ld_ring'), 1))
        if k == 1:  # this one has an eye in it, looking at you
            A(AT.region(eyeball(None, 0.19, (x, 0.95, -0.42), rot=(-math.pi / 2 + 0.15, 0, 0), name='ld_eye'), 'eye',
                        lambda g, x=x: ((g[0] - x) / 0.4 + 0.5, (g[1] - 0.95) / 0.4 + 0.5)))
        else:
            dk = cyl(0.2, 0.02, (x, 0.95, -0.46), None, axis='z', seg=14); bpy.context.view_layer.update()
            A(AT.region(dk, 'suds', lambda g, x=x: ((g[0] - x) / 0.42 + 0.5, (g[1] - 0.95) / 0.42 + 0.5)))
        if k == 2:  # a length of intestine spilling out of the door like a stray sock, down to the floor
            A(sweep([(x - 0.05, 0.9, -0.47), (x - 0.12, 0.85, -0.53), (x - 0.2, 0.75, -0.52), (x - 0.18, 0.6, -0.5), (x - 0.25, 0.45, -0.47)],
                    [0.06, 0.07, 0.07, 0.065, 0.06], flesh, seg=6, name='ld_gut'))
    for k, x in enumerate((-3.05, -2.05, -1.05)):  # a row of stacked dryers above, one door hanging open
        sw(box((0.9, 0.7, 0.34), (x, 1.82, -0.23), None, bev=0.03, seg=1), 0)
        A(AT.swatch(lathe([(0.22, -0.02), (0.24, 0.0), (0.22, 0.03), (0.18, 0.03), (0.17, 0.0)], (x, 1.8, -0.415), None, seg=12, axis='z', cap=False, name='ld_ring2'), 1))
        dk = cyl(0.18, 0.02, (x, 1.8, -0.41), None, axis='z', seg=12); bpy.context.view_layer.update()
        A(AT.region(dk, 'suds', lambda g, x=x: ((g[0] - x) / 0.38 + 0.5, (g[1] - 1.8) / 0.38 * 0.4 + 0.75)))
    sw(box((3.4, 0.06, 0.4), (-1.875, 2.2, -0.22), None), 8)  # a shelf with the detergent
    for k, x in enumerate((-3.3, -2.9, -2.1, -1.5, -0.7)):
        sw(box((0.18, 0.3, 0.14), (x, 2.38, -0.25), None, bev=0.02, seg=1), (9, 4, 3, 9, 11)[k])
    card = box((0.42, 0.28, 0.01), (-0.5, 2.62, -0.47), None); bpy.context.view_layer.update()
    A(AT.region(card, 'card', front_proj(-0.5, 2.62, 0.42, 0.28)))
    gl = box((3.4, 2.04, 0.02), (-1.875, 1.8, -0.5), glass); uv_box(gl, 1.0); gl['keepuv'] = 1; A(gl)
    for xx in (-3.6, -0.15): sw(box((0.1, 2.2, 0.12), (xx + (0.05 if xx < 0 else -0.05) * (1 if xx < -1 else 1), 1.8, -0.52), None, bev=0.01, seg=1), 0)
    sw(box((3.55, 0.1, 0.14), (-1.875, 2.85, -0.53), None, bev=0.01, seg=1), 0)
    sw(box((3.55, 0.08, 0.16), (-1.875, 0.74, -0.54), None, bev=0.01, seg=1), 0)
    sw(box((0.08, 2.1, 0.1), (-1.875, 1.8, -0.53), None), 0)  # the glazing bar in the middle
    # the door: a throat inside, fleshy lips for jambs, the tongue lolling out onto the pavement
    sw(box((1.4, 2.4, 0.05), (1.5, 1.2, -0.06), None), 6)
    for xx in (0.82, 2.18):
        A(sweep([(xx, 0.0, -0.62), (xx + (0.03 if xx < 1.5 else -0.03), 0.8, -0.66), (xx, 1.6, -0.64), (xx + (0.12 if xx < 1.5 else -0.12), 2.3, -0.63), (1.5 + (xx - 1.5) * 0.35, 2.48, -0.62)],
                [0.16, 0.2, 0.18, 0.16, 0.13], flesh, seg=8, name='ld_jamb'))
    tg = G1.tongue_obj(M, 'ld_tg', s=0.82, pos=(1.5, 0.0, -0.6))
    for o in tg[1:]: bpy.data.objects.remove(o, do_unlink=True)  # no papillae at this size
    tg[0].data.materials[1] = tg[0].data.materials[0]  # one material for the whole tongue here (fewer draws)
    A(tg[0])
    # the awning: striped canvas on a slope, a gum along its front edge with teeth hanging off it
    aw = box((6.1, 0.06, 0.62), (-0.75, 3.0, -0.92), None, rot=(-0.32, 0, 0)); bpy.context.view_layer.update()
    A(AT.region(aw, 'stripes', lambda g: ((g[0] + 3.8) / 6.1, (g[2] + 1.23) / 0.65)))
    val = box((6.1, 0.22, 0.04), (-0.75, 2.8, -1.21), None); bpy.context.view_layer.update()
    A(AT.region(val, 'stripes', lambda g: ((g[0] + 3.8) / 6.1, (g[1] - 2.69) / 0.24 * 0.3)))
    A(sweep([(-3.85, 2.72, -1.22), (-2.0, 2.7, -1.24), (0.0, 2.73, -1.23), (1.4, 2.7, -1.24), (2.35, 2.72, -1.22)], [0.1, 0.12, 0.12, 0.12, 0.1], flesh, seg=8, name='ld_gum'))
    rnd = random.Random(73)
    for k in range(15):
        x = -3.6 + k * 0.42 + rnd.uniform(-0.05, 0.05)
        if k % 3 == 1: t = canine(None, pos=(x, 2.76, -1.23), rot=(math.pi + rnd.uniform(-0.15, 0.15), 0, rnd.uniform(-0.2, 0.2)), s=rnd.uniform(1.0, 1.25), name='ld_tooth', seed=k)
        else: t = molar(None, pos=(x, 2.78, -1.23), rot=(math.pi + rnd.uniform(-0.1, 0.1), rnd.uniform(0, 1), 0), s=rnd.uniform(0.85, 1.0), name='ld_tooth', seed=k)
        sw(t, 7)
    # skin growing over the brick: a big creep down from the top left over the sign's end, one round the right pier's
    # foot, a smear across the cornice; veins crawl over the sign
    def wallclamp(p): return (p[0], max(p[1], -0.03), min(p[2], -0.02))
    tl = meta([((-3.6, 4.6, -0.6), 0.75), ((-3.2, 4.3, -0.65), 0.7), ((-3.75, 3.8, -0.6), 0.6), ((-3.7, 3.2, -0.6), 0.45), ((-3.65, 2.6, -0.6), 0.35),
               ((-3.6, 2.15, -0.62), 0.28), ((-2.6, 4.75, -0.6), 0.55), ((-3.0, 3.7, -0.72), 0.4), ((-2.4, 3.6, -0.74), 0.32)], res=0.1, m=flesh, target=650, name='ld_skin_tl', clamp=wallclamp)
    lump(tl, 0.04, 3.0, seed=7); A(tl)
    br = meta([((3.5, 0.2, -0.6), 0.7), ((2.9, 0.15, -0.62), 0.55), ((3.8, 0.8, -0.6), 0.5), ((3.4, 1.15, -0.62), 0.4), ((2.6, 0.6, -0.6), 0.32), ((3.9, 1.6, -0.6), 0.3)],
              res=0.1, m=flesh, target=480, name='ld_skin_br', clamp=wallclamp)
    lump(br, 0.04, 3.0, seed=8); A(br)
    tr = meta([((2.2, 5.0, -0.5), 0.45), ((2.8, 4.95, -0.55), 0.5), ((3.4, 4.9, -0.5), 0.45), ((3.85, 4.6, -0.6), 0.4), ((3.75, 4.1, -0.6), 0.3)],
              res=0.1, m=flesh, target=380, name='ld_skin_tr', clamp=wallclamp)
    lump(tr, 0.04, 3.0, seed=9); A(tr)
    # an eye grown into the right pier, under the skin
    A(AT.region(eyeball(None, 0.22, (3.35, 2.05, -0.62), rot=(-math.pi / 2 + 0.1, 0, 0.15), name='ld_eye2'), 'eye',
                lambda g: ((g[0] - 3.35) / 0.44 + 0.5, (g[1] - 2.05) / 0.44 + 0.5)))
    A(torus(0.22, 0.08, flesh, (3.35, 2.05, -0.6), rot=(math.pi / 2, 0, 0), n=12, k=4, name='ld_lid', wob=lambda a: 1 + 0.3 * max(0, math.sin(a))))
    for k, pts in enumerate(([(-3.2, 4.0, -0.76), (-2.6, 3.85, -0.77), (-1.9, 3.5, -0.77), (-1.2, 3.65, -0.77), (-0.4, 3.35, -0.77), (0.3, 3.3, -0.77)],
                             [(-3.0, 3.55, -0.77), (-2.4, 3.3, -0.77), (-1.6, 3.2, -0.77), (-0.9, 3.3, -0.77)],
                             [(-2.8, 4.6, -0.78), (-1.8, 4.5, -0.8), (-0.6, 4.55, -0.8), (0.6, 4.4, -0.78), (1.6, 4.5, -0.78), (2.4, 4.75, -0.7)],
                             [(3.6, 1.1, -0.66), (3.3, 1.6, -0.64), (3.0, 2.4, -0.63), (2.7, 3.1, -0.65), (2.6, 3.4, -0.75), (2.4, 3.7, -0.77)])):
        A(sweep(pts, [0.08 - 0.035 * i / (len(pts) - 1) for i in range(len(pts))], vein, seg=5, name='ld_vein'))
    mirror_parts(P)  # built as drawn on paper; flipped so the sign reads from the street (the door ends up on the right)
    parts = pack(P, 'launderette', 1.0)
    return finish_lod('s_launderette', parts, meta_of('launderette', mount='wall', wallZ=0, col=[8, 5, 0.6], door=[-1.5, 0, -0.6],
                      ramp=[[-1.5, 0.64, -0.1], [-1.5, 0.18, -2.75]], lights=[[1.9, 1.8, -0.3, 0x9fd8ff]],
                      note='origin bottom centre on the wall plane; facade 0.6 m deep, awning + teeth to z -1.3, tongue door to z -2.9'), ratio=0.25)


# ---------------------------------------------------------------- 11. Gristle & Sons Biologics sign
def _gl_text(px):
    px[:] = hexrgb(0xfff3d0)
    px[2:5, :] = hexrgb(0x8a2a4a); px[-5:-2, :] = hexrgb(0x8a2a4a)
    text_px(px, 'GRISTLE', 20, 10, 4, 0x8a2a4a)
    text_px(px, '& SONS', 34, 42, 4, 0x8a2a4a)
    text_px(px, 'BIOLOGICS', 50, 72, 2, 0xff4f7a)
    text_px(px, 'WE LOVE YOU BACK', 56, 87, 1, 0x5b3a8f)


GL_SW = [0xffe14d, 0xd8203a, 0xffc9a8, 0xffffff, 0x1a1030, 0xff8aa8, 0x7a3a28, 0xc8ccd4, 0x8a2a4a, 0xf8ecd2, 0x4fd8ff]
# 0 yellow, 1 red, 2 skin, 3 white, 4 ink, 5 cheek pink, 6 wood/mustache, 7 steel, 8 liver, 9 tooth, 10 cyan


def build_gristlelogo(M):
    AT = Atlas('gl_atlas', 192, 168, {'text': (0, 0, 192, 96, _gl_text), 'eye': (0, 96, 64, 64, _paint_eye)}, GL_SW, rough=0.22, clearcoat=0.9)
    flesh, vein = M['flesh'], M['vein']
    P = []; A = P.append
    sw = lambda o, k: A(AT.swatch(o, k))
    # the words panel
    tp = box((3.0, 1.6, 0.22), (1.1, 1.25, -0.11), None, bev=0.04, seg=1); bpy.context.view_layer.update()
    A(AT.region(tp, 'text', front_proj(1.1, 1.25, 3.0, 1.6)))
    sw(box((3.16, 1.76, 0.12), (1.1, 1.25, -0.06), None, bev=0.03, seg=1), 1)
    # the badge: a yellow disc in a red rim, the smiling butcher-doctor on it
    bx, by = -1.35, 1.32
    sw(cyl(1.15, 0.26, (bx, by, -0.13), None, axis='z', seg=28, bev=0.03), 0)
    sw(torus(1.15, 0.1, None, (bx, by, -0.26), rot=(math.pi / 2, 0, 0), n=28, k=6, name='gl_rim'), 1)
    sw(ball(0.52, (bx, by - 0.05, -0.3), None, scale=(1.0, 1.08, 0.42), seg=16, rings=10, name='gl_head'), 2)
    for ex in (-1, 1):
        sw(ball(0.12, (bx + ex * 0.3, by - 0.17, -0.5), None, scale=(1, 0.7, 0.35), seg=10, rings=6, name='gl_cheek'), 5)
        sw(sweep([(bx + ex * 0.27 - 0.1, by + 0.08, -0.5), (bx + ex * 0.27, by + 0.14, -0.53), (bx + ex * 0.27 + 0.1, by + 0.08, -0.5)], 0.028, None, seg=6, name='gl_eyeline'), 4)  # happy shut eyes
        sw(ball(0.15, (bx + ex * 0.53, by - 0.02, -0.36), None, scale=(0.5, 1, 0.5), seg=8, rings=6, name='gl_ear'), 2)
        # handlebar moustache
        sw(sweep([(bx + ex * 0.02, by - 0.13, -0.55), (bx + ex * 0.15, by - 0.16, -0.55), (bx + ex * 0.28, by - 0.12, -0.52), (bx + ex * 0.36, by - 0.02, -0.48), (bx + ex * 0.32, by + 0.03, -0.47)],
                 [0.05, 0.055, 0.045, 0.03, 0.02], None, seg=6, name='gl_tache'), 6)
    sw(ball(0.09, (bx, by - 0.06, -0.55), None, scale=(1, 0.85, 0.8), seg=8, rings=6, name='gl_nose'), 5)
    # the huge grin, with teeth
    smile = [(bx + 0.33 * math.sin(math.radians(a)), by - 0.3 - 0.1 * math.cos(math.radians(a)), -0.5) for a in range(-80, 81, 20)]
    sw(sweep(smile, 0.035, None, seg=6, name='gl_smile'), 4)
    sw(box((0.42, 0.07, 0.03), (bx, by - 0.36, -0.49), None, bev=0.01, seg=1), 9)
    # a white butcher's paper hat, a head mirror on a band
    sw(lathe([(0.42, 0.0), (0.45, 0.12), (0.5, 0.28), (0.44, 0.38), (0.25, 0.43), (0.0, 0.44)], (bx, by + 0.36, -0.28), None, seg=14, axis='y', name='gl_hat'), 3)
    sw(cyl(0.14, 0.04, (bx + 0.16, by + 0.3, -0.53), None, axis='z', seg=12, bev=0.01), 7)
    sw(cyl(0.05, 0.05, (bx + 0.16, by + 0.3, -0.56), None, axis='z', seg=8), 4)
    # coat collar and bow tie
    for ex in (-1, 1):
        sw(box((0.32, 0.22, 0.06), (bx + ex * 0.17, by - 0.62, -0.33 - 0.012 * ex), None, rot=(0, 0, ex * 0.6), bev=0.02, seg=1), 3)
        sw(lathe([(0.0, 0.0), (0.09, 0.05), (0.1, 0.2), (0.0, 0.22)], (bx + ex * 0.02, by - 0.58, -0.42), None, seg=8, axis='x', rot=(0, 0, 0) if ex > 0 else (0, math.pi, 0), name='gl_bow'), 1)
    # the cleaver, raised in a cheerful wave
    cl = box((0.42, 0.3, 0.05), (bx + 0.78, by + 0.55, -0.4), None, rot=(0, 0, -0.35), bev=0.015, seg=1); sw(cl, 7)
    sw(box((0.09, 0.32, 0.07), (bx + 0.66, by + 0.27, -0.4), None, rot=(0, 0, -0.35), bev=0.02, seg=1), 6)
    sw(ball(0.11, (bx + 0.61, by + 0.12, -0.42), None, seg=8, rings=6, name='gl_fist'), 2)
    # skin grown over the lower right of the words and the bottom of the badge, veins across, an eye, two teeth
    def wallclamp(p): return (p[0], max(p[1], -0.03), min(p[2], -0.02))
    s1 = meta([((2.2, 0.45, -0.25), 0.7), ((1.6, 0.35, -0.28), 0.6), ((2.4, 1.05, -0.25), 0.55), ((1.1, 0.5, -0.3), 0.45), ((2.45, 1.6, -0.22), 0.4),
               ((0.6, 0.25, -0.28), 0.35), ((2.45, 0.0, -0.2), 0.45), ((1.9, -0.05, -0.2), 0.4)], res=0.09, m=flesh, target=700, name='gl_skin1', clamp=wallclamp)
    lump(s1, 0.035, 3.0, seed=3); A(s1)
    s2 = meta([((-1.9, 0.25, -0.35), 0.55), ((-1.3, 0.15, -0.38), 0.45), ((-2.4, 0.6, -0.3), 0.42), ((-0.8, 0.3, -0.32), 0.3), ((-2.5, 1.05, -0.28), 0.3)],
              res=0.09, m=flesh, target=450, name='gl_skin2', clamp=wallclamp)
    lump(s2, 0.035, 3.0, seed=4); A(s2)
    A(AT.region(eyeball(None, 0.2, (1.85, 0.6, -0.62), rot=(-math.pi / 2 + 0.05, 0, -0.1), name='gl_eye'), 'eye',
                lambda g: ((g[0] - 1.85) / 0.4 + 0.5, (g[1] - 0.6) / 0.4 + 0.5)))
    for k, (x, y, a) in enumerate(((1.25, 0.15, 0.3), (-1.6, 0.05, -0.2))):
        sw(canine(None, pos=(x, y + 0.12, -0.38), rot=(-math.pi / 2 + 0.6, 0, a), s=0.8, name='gl_tooth', seed=k), 9)
    for pts in ([(2.3, 1.75, -0.3), (2.0, 1.95, -0.24), (1.5, 1.8, -0.24), (0.9, 1.97, -0.24), (0.2, 1.85, -0.24)],
                [(1.3, 0.85, -0.3), (0.8, 1.1, -0.24), (0.1, 1.0, -0.24), (-0.4, 1.2, -0.24)],
                [(-0.55, 0.3, -0.38), (-0.3, 0.6, -0.3), (-0.2, 1.1, -0.27), (-0.1, 1.6, -0.25)]):
        A(sweep(pts, [0.07 - 0.03 * i / (len(pts) - 1) for i in range(len(pts))], vein, seg=5, name='gl_vein'))
    mirror_parts(P)  # so the words read from the street, the badge on the viewer's left
    parts = pack(P, 'gristlelogo', 0.5)
    return finish_lod('s_gristlelogo', parts, meta_of('gristlelogo', mount='wall', wallZ=0, col=[5.0, 2.6, 0.6],
                      note='origin bottom centre on the wall plane; put it 4-8 m up a campus building'), ratio=0.25)


# ---------------------------------------------------------------- 12. flesh blobs (creep over the Bottom's houses)
def _blob_bits(M, P, bvh, rnd, n_pus, teeth, eyes, veins, sz, wall=False):
    A = P.append
    def surf(p, off): return onsurf(bvh, p, off)
    for k in range(n_pus):  # pustules, half sunk (they breathe with the blob)
        q, n = surf((rnd.uniform(-sz[0], sz[0]), rnd.uniform(0.3, sz[1]), -rnd.uniform(0.5, 1.0) * sz[2] - 0.5 if wall else rnd.uniform(-sz[2], sz[2])), 0.0)
        r = rnd.uniform(0.08, 0.15)
        A(ball(r, tuple(Vector(q) + Vector(n) * r * 0.35), M['pus'], seg=6, rings=4, name='fb_pus'))
    for k, p in enumerate(teeth):
        q, n = surf(p, 0.0); N = Vector(n)
        f = molar if k % 2 else canine
        A(orient_to(f(M['enamel'], s=1.1, name='fb_tooth', seed=k), tuple(Vector(q) - N * 0.12), n))
    for p, r in eyes:
        q, n = surf(p, 0.0); N = Vector(n)
        A(orient_to(eyeball(M['eye'], r, name='fb_eye'), tuple(Vector(q) - N * r * 0.2), n))
        A(orient_to(torus(r * 1.02, r * 0.3, M['flesh'], n=10, k=4, name='fb_lid', wob=lambda a: 1 + 0.4 * max(0, math.sin(a))), tuple(Vector(q) + N * r * 0.05), n))
    for k, (p, d, st) in enumerate(veins):
        pts = crawl(bvh, p, d, st, 0.28, 0.025, seed=k + 3, wig=0.35)
        A(sweep(pts, [0.06 - 0.03 * i / (len(pts) - 1) for i in range(len(pts))], M['vein'], seg=4, name='fb_vein'))


def build_fleshblob_a(M):
    rnd = random.Random(121)
    balls = [((0, 0.2, 0), 1.25), ((0.7, 0.5, 0.3), 0.95), ((-0.75, 0.35, -0.25), 0.9), ((0.2, 0.95, -0.2), 0.75), ((-0.3, 0.7, 0.6), 0.7),
             ((1.15, 0.1, -0.5), 0.6), ((-1.2, 0.05, 0.6), 0.55), ((0.5, 1.25, 0.25), 0.45), ((-0.15, 0.0, -1.0), 0.6), ((0.9, 0.0, 0.9), 0.5)]
    o = meta(balls, res=0.1, m=M['flesh'], target=600, name='fb_a', clamp=lambda p: (p[0], max(p[1], -0.03), p[2]))
    lump(o, 0.05, 2.4, seed=12)
    P = [o]
    bvh = bvh_of(o)
    _blob_bits(M, P, bvh, rnd, 4, [(0.9, 0.6, -0.7), (-0.6, 0.5, -0.9)], [((0.1, 1.1, -0.7), 0.17)],
               [((-1.0, 0.4, -0.3), (1, 0.6, 0), 9), ((0.8, 0.3, 0.6), (-0.4, 1, -0.3), 8), ((0.2, 1.3, 0.1), (1, -0.6, 0.2), 7)], (1.0, 1.1, 0.9))
    parts = pack(P, 'fleshblob_a', 0.6)
    return finish_lod('s_fleshblob_a', parts, meta_of('fleshblob_a', col=[2.6, 1.5, 2.3], note='a mound for gardens, porches and roofs'), ratio=0.25, drop=('enamel', 'pus'))


def build_fleshblob_b(M):
    rnd = random.Random(122)
    # a wall splat: flat back on the wall (z = 0), a big mass at head height, drips down to the ground, a tendril up
    balls = [((0, 1.9, -0.2), 0.9), ((0.55, 1.6, -0.2), 0.75), ((-0.6, 2.1, -0.18), 0.7), ((0.25, 2.45, -0.15), 0.6), ((-0.2, 1.3, -0.2), 0.65),
             ((0.75, 1.05, -0.12), 0.32), ((0.8, 0.7, -0.1), 0.24), ((0.82, 0.45, -0.1), 0.2), ((0.84, 0.25, -0.1), 0.22),
             ((-0.45, 0.9, -0.12), 0.34), ((-0.48, 0.55, -0.1), 0.25), ((-0.5, 0.2, -0.12), 0.27), ((-0.6, 0.0, -0.15), 0.4), ((-0.2, 0.0, -0.12), 0.32),
             ((0.2, 0.9, -0.1), 0.24), ((0.22, 0.65, -0.08), 0.18), ((-0.9, 2.6, -0.12), 0.35), ((-1.05, 2.95, -0.1), 0.28)]
    o = meta(balls, res=0.09, m=M['flesh'], target=640, name='fb_b', clamp=lambda p: (p[0], max(p[1], -0.03), min(p[2], 0.0)))
    lump(o, 0.04, 2.6, seed=13, mask=lambda p: min(1, -p[2] * 4))
    P = [o]
    bvh = bvh_of(o)
    _blob_bits(M, P, bvh, rnd, 4, [(0.6, 1.4, -0.8), (-0.7, 1.9, -0.8)], [((0.1, 2.0, -1.0), 0.18)],
               [((-0.5, 2.3, -0.8), (1, -0.4, 0), 8), ((0.6, 1.9, -0.8), (0.2, -1, 0), 8), ((-0.3, 1.1, -0.7), (-0.3, -1, 0), 6)], (0.8, 2.6, 0.6), wall=True)
    for p in P:  # nothing pokes through the wall behind it
        apply_mods(p)
        for v in p.data.vertices:
            g = gg(p.matrix_world @ v.co)
            if g[2] > 0.0: v.co = p.matrix_world.inverted() @ gv(g[0], g[1], 0.0)
    parts = pack(P, 'fleshblob_b', 0.6)
    return finish_lod('s_fleshblob_b', parts, meta_of('fleshblob_b', mount='wall', wallZ=0, col=[2.4, 3.1, 0.9], note='origin bottom centre on the wall plane'),
                      ratio=0.25, drop=('enamel', 'pus'))


BUILDS = {'launderette': build_launderette, 'gristlelogo': build_gristlelogo, 'fleshblob_a': build_fleshblob_a, 'fleshblob_b': build_fleshblob_b}
EXPO = {'gristlelogo': -1.8, 'launderette': -1.7}


def build():
    only = argv_only()
    M = gut_mats()
    out = []
    for k, f in BUILDS.items():
        if only and k not in only: continue
        out.append((f(M), 'story/s_' + k, k))
    return out


run_multi_lod(build, EXPO)
