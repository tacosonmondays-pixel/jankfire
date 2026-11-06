# OVERDUE: the ruin kit + THE COMMUTE (the wastes between districts, DESIGN §4.11, ART_BIBLE §4 ruin rules, §6 #25/#29):
# the Unpaid's filing-cabinet barricades and office-chair scrap, burning ☺buck barrels, a raider tent on cubicle walls,
# pastel rubble heaps, a blast-shadowed shopfront wall, jersey barriers, a melted cone, the ☺ CORP street clock stopped
# at 17:29, a wrecked ☺ CORP walker tank (the landmark), paper-storm drifts, a tyre stack with a raider flag and a
# skeleton still wearing its lanyard. readable decay: bright, pastel, candy rust, grime as small texture only.
# -> public/models/story/s_<id>.glb (full mesh + s_<id>_lod1 at <= 25% tris) + tools/blender/sheets/story/s_<id>.jpg
# run: blender -b --python tools/blender/make_story_ruins.py [-- --only filecab,cone] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bottom_kit import *
from sidekit import quad, one_mat, seg7

PINK, YEL, TEAL, MINT, LILAC, PEACH = 0xffb3c7, 0xffe58a, 0x5fd3c6, 0xa8f0d0, 0xc9a8ff, 0xffc49a
HOT, MAG, CYAN, GREEN, RED, INK = 0xff4fd8, 0xff00dc, 0x4fd8ff, 0x39ff14, 0xff3030, 0x141018
RUST, RUST2, TAR, PAPER, MANILA = 0xd2642a, 0x8a3a1e, 0x8a8278, 0xfbf8f0, 0xf2d48a
CONC = [0xf4c4cc, 0xbfe8d8, 0xfbe6a6, 0xd9cdf2, 0xf6d2b4, 0xe8e2d8]  # pastel concrete: pink, mint, butter, lilac, peach, bone
CMT = {'district': 'commute'}


def plain(name, col, rough=0.5, metal=0.0, cc=0.0, var=0.08, speck=None, p=0.0, seed=1, size=16):
    return mat(name, col, rough=rough, metal=metal, clearcoat=cc, tex=tex_noise(name + '_t', col, var=var, size=size, speck=speck, speck_p=p, seed=seed))


def tiled(objs, size=0.25):
    for o in objs: uv_tile(o, size)
    return objs


def fit(o, rect, **kw):
    uv_fit(o, rect, **kw)
    return o


# ------------------------------------------------------------ textures with alpha (spray paint, torn posters, flags)
def rgba_image(name, w, h, draw):
    """draw(px, al) paints h x w x 3 colour and an h x w alpha (0 = see-through): alpha-clipped decals"""
    px = np.zeros((h, w, 3), np.float32); al = np.zeros((h, w), np.float32)
    draw(px, al)
    img = bpy.data.images.new(name, w, h, alpha=True)
    rgba = np.ones((h, w, 4), np.float32); rgba[:, :, :3] = np.clip(px, 0, 1)[::-1]; rgba[:, :, 3] = al[::-1]
    img.pixels.foreach_set(rgba.ravel()); img.file_format = 'PNG'; img.pack()
    return img


def decal_mat(name, img, rough=0.55, cc=0.0):
    """alpha-clipped (glTF MASK) material: spray tags and torn paper keep hard pixel edges"""
    m = mat(name, 0xffffff, rough=rough, clearcoat=cc, tex=img)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; t = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    m.blend_method = 'CLIP'; m.alpha_threshold = 0.5
    try: m.shadow_method = 'CLIP'
    except Exception: pass
    return m


def spray(px, al, mask, col, seed=1, over=0.35, drips=3, dl=(3, 9)):
    """a spray-can tag from a boolean mask: hard core, speckled overspray round it, a few runs dripping down"""
    r = np.random.default_rng(seed); h, w = mask.shape
    grow = mask.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
        grow |= np.roll(np.roll(mask, dy, 0), dx, 1)
    halo = grow & ~mask & (r.random((h, w)) < over)
    c = hexrgb(col)
    px[mask] = c * (0.92 + 0.08 * r.random((int(mask.sum()), 1))); al[mask] = 1
    px[halo] = c * 0.85; al[halo] = 1
    ys, xs = np.nonzero(mask)
    if len(xs):
        for k in range(drips):
            i = r.integers(len(xs)); x, y = xs[i], ys[i]
            while y + 1 < h and mask[y + 1, x]: y += 1
            L = int(r.integers(dl[0], dl[1] + 1))
            px[y:min(h, y + L), x] = c; al[y:min(h, y + L), x] = 1
            if y + L < h: px[y + L, x] = c; al[y + L, x] = 1


def text_mask(h, w, s, x0, y0, scale, lower=False, wob=0, seed=1):
    m = np.zeros((h, w, 3), np.float32)
    if lower: write(m, s, x0, y0, scale, 0xffffff, wob=wob, seed=seed)
    else: text_px(m, s, x0, y0, scale, 0xffffff)
    return m[:, :, 0] > 0.5


def ring_mask(h, w, cx, cy, r, t):
    y, x = np.mgrid[0:h, 0:w]; d = np.hypot(x + 0.5 - cx, y + 0.5 - cy)
    return (d <= r) & (d >= r - t)


def line_mask(h, w, x0, y0, x1, y1, t):
    m = np.zeros((h, w, 3), np.float32); px_line(m, x0, y0, x1, y1, 0xffffff, t)
    return m[:, :, 0] > 0.5


def crossed_smiley(h, w, cx, cy, r, t=2.0):
    """the Unpaid's mark: a sprayed ☺ (ring, eyes, grin) with a big X through it"""
    m = ring_mask(h, w, cx, cy, r, t)
    y, x = np.mgrid[0:h, 0:w]
    for ex in (-0.36, 0.36): m |= np.hypot(x + 0.5 - (cx + ex * r), y + 0.5 - (cy - 0.25 * r)) <= max(1.0, r * 0.13)
    d = np.hypot(x + 0.5 - cx, y + 0.5 - (cy + 0.02 * r)); ang = np.arctan2(x + 0.5 - cx, -(y + 0.5 - cy))
    m |= (d <= r * 0.6) & (d >= r * 0.6 - t * 0.9) & (np.abs(ang) > math.pi * 0.62)
    m |= line_mask(h, w, cx - r * 1.05, cy - r * 1.05, cx + r * 1.05, cy + r * 1.05, t * 1.2)
    m |= line_mask(h, w, cx + r * 1.05, cy - r * 1.05, cx - r * 1.05, cy + r * 1.05, t * 1.2)
    return m


def paper_lines(px, seed=1, ink=0x7a7f90, step=3, margin=3, title=None):
    """a form: ruled grey lines of 'text', a darker title bar"""
    r = random.Random(seed); h, w = px.shape[:2]
    if title is not None: px[2:4, margin:w - margin] = hexrgb(title)
    for y in range(6 if title is not None else 3, h - 2, step):
        x1 = w - margin - r.randint(0, w // 3)
        px[y, margin:x1] = px[y, margin:x1] * 0.4 + hexrgb(ink) * 0.6


def stamp(px, word, x0, y0, col=0xd0182a, scale=1, box_=True):
    tw_ = len(word) * 6 - 1
    text_px(px, word, x0, y0, scale, col)
    if box_:
        h, w = px.shape[:2]
        x1, y1 = min(w - 1, x0 + tw_ * scale + 1), min(h - 1, y0 + 7 * scale + 1)
        px[max(0, y0 - 2), max(0, x0 - 2):x1 + 1] = hexrgb(col); px[y1, max(0, x0 - 2):x1 + 1] = hexrgb(col)
        px[max(0, y0 - 2):y1 + 1, max(0, x0 - 2)] = hexrgb(col); px[max(0, y0 - 2):y1 + 1, x1] = hexrgb(col)


# ------------------------------------------------------------ UVs per face direction
def uv_dir(o, rects, default=(0, 0, 1, 1), lo=None, hi=None):
    """like uv_fit (each face seen straight on, stretched over the object's bounds) but each facing direction
    ('+x' '-x' '+y' '-y' '+z' '-z') gets its own atlas rect"""
    apply_mods(o); bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world; R = mw.to_3x3()
    blo, bhi = game_bbox(o); lo = lo or blo; hi = hi or bhi
    d = [max(hi[k] - lo[k], 1e-6) for k in range(3)]
    for pg in me.polygons:
        nb = R @ pg.normal; n = (nb.x, nb.z, -nb.y)
        ax = max(range(3), key=lambda k: abs(n[k]))
        key = ('+' if n[ax] > 0 else '-') + 'xyz'[ax]
        u0, v0, u1, v1 = rects.get(key, default)
        for li in pg.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            g = ((p.x - lo[0]) / d[0], (p.z - lo[1]) / d[1], (-p.y - lo[2]) / d[2])
            if ax == 0: u, w = ((1 - g[2]) if n[0] > 0 else g[2]), g[1]
            elif ax == 2: u, w = ((1 - g[0]) if n[2] < 0 else g[0]), g[1]
            else: u, w = g[0], 1 - g[2]
            uv[li].uv = (u0 + u * (u1 - u0), v0 + w * (v1 - v0))
    return o


def xf(objs, **kw):
    """bottom_kit.xform, after a view-layer update (a fresh object's matrix_world is stale until then)"""
    bpy.context.view_layer.update()
    return xform(objs, **kw)


def deform(o, f):
    """move every vertex: f(game point) -> game point (melting, bending, sinking)"""
    apply_mods(o); bpy.context.view_layer.update()
    me = o.data; mw = o.matrix_world; inv = mw.inverted()
    for v in me.vertices:
        w = mw @ v.co; g = f((w.x, w.z, -w.y)); v.co = inv @ gv(*g)
    me.update()
    return o


def chunk(size, pos, m, rect, seed=1, rot=None, jit=0.18, bev=0.0):
    """a broken concrete lump: a box with its corners shoved about (12 tris), seen-straight-on UVs into rect"""
    r = random.Random(seed)
    o = box(size, pos, m, rot=rot or (r.uniform(-0.5, 0.5), r.uniform(0, 6.28), r.uniform(-0.5, 0.5)), name='chunk')
    for v in o.data.vertices:
        v.co.x *= 1 + r.uniform(-jit, jit); v.co.y *= 1 + r.uniform(-jit, jit); v.co.z *= 1 + r.uniform(-jit, jit)
    o.data.update()
    if bev: bevel(o, bev, 1)
    uv_fit(o, rect)
    return o


def bent_rebar(p0, d, L, m, bend=0.6, seed=1, n=4, r=0.012):
    """a rebar stub: out of the concrete along d, then kinked over"""
    rr = random.Random(seed); D = Vector(d).normalized()
    side = D.cross(Vector((0.3, 1, 0.2))).normalized()
    pts = []
    for i in range(n + 1):
        t = i / n; k = bend * t * t
        q = Vector(p0) + D * (L * t) + side * (k * L * 0.6) + Vector((0, -k * L * 0.4, 0))
        pts.append(tuple(q + Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-1, 1))) * 0.006 * i))
    return sweep(pts, r, m, seg=4, name='rebar')


def lanyard_on(pts, strap_m, rect_strap, badge_m, rect_badge, end, rot=(0, 0, 0), w=0.017):
    """a lanyard strap along pts (game points) with its badge card hanging at end"""
    st = sweep(pts, w / 2, strap_m, seg=4, squash=(1.0, 0.25), name='lanyard')
    uv_fit(st, rect_strap, mode='front')
    clip = box((0.014, 0.025, 0.006), (end[0], end[1] + 0.012, end[2]), badge_m, rot=rot)
    card = box((0.058, 0.085, 0.004), (end[0], end[1] - 0.042, end[2]), badge_m, rot=rot, name='badge')
    uv_fit(clip, rect_badge); uv_fit(card, rect_badge)
    return [st, clip, card]


def paint_badge(px, name_='INTERN', seed=1):
    """an office ID card: white card, cyan band with ☺ CORP, a mugshot square, a name"""
    h, w = px.shape[:2]
    px[:] = hexrgb(0xfdfdfb); px[0:h // 5] = hexrgb(CYAN)
    smiley(px, w * 0.2, h // 10, max(1.5, h / 14), face=YEL, ink=INK)
    px[h // 4:h // 4 + h // 3, w // 5:w // 5 + w // 2] = hexrgb(0xc8d0dc)
    px_disc(px, w // 5 + w // 4, h // 4 + h // 6, w / 7, 0xf2c8a0)
    text_px(px, name_[:max(1, (w - 2) // 6)], 1, h - 9, 1, INK)


# ================================================================================================ filing cabinet
def metal_paint(px, seed, base=0xf6f4f0, chips=6, scratches=10, rust=True):
    """glossy enamel that's been through the end of the world: faint grain, light scratches to bare grey metal, a few
    candy-rust chips with runs bleeding down from them"""
    r = random.Random(seed); h, w = px.shape[:2]
    crust(px, base, 0.03, seed=seed, block=4)
    for _ in range(scratches):
        x, y = r.uniform(0, w), r.uniform(0, h); a = r.uniform(-0.6, 0.6) + (math.pi / 2 if r.random() < 0.3 else 0)
        L = r.uniform(3, 10); px_line(px, x, y, x + math.cos(a) * L, y + math.sin(a) * L, 0xc4c6cc, 1)
    if rust:
        for _ in range(chips):
            x, y, rr = r.uniform(2, w - 2), r.uniform(2, h - 8), r.uniform(0.7, 1.7)
            for k in range(r.randint(1, 2)):  # runs bleeding down, fading out
                xx = int(x + r.uniform(-rr, rr) * 0.6); y0 = int(y); L = r.randint(4, 12)
                for j in range(L):
                    if 0 <= xx < w and y0 + j < h:
                        t = 0.5 * (1 - j / L); px[y0 + j, xx] = px[y0 + j, xx] * (1 - t) + hexrgb(0xc8783a) * t
            px_disc(px, x, y, rr + 0.7, 0xb4aca4); px_disc(px, x, y, rr, RUST)


def build_filecab():
    W, H, D = 0.5, 1.35, 0.7
    FZ = -D / 2
    ys = [0.04 + k * 0.325 + 0.155 for k in range(4)]  # drawer centres, bottom to top
    row = lambda y: int(round((1 - y / H) * 128))
    # body atlas (paint: white base, tinted per instance): front, side, top, drawer fronts
    A = Atlas('fc_paint_t', 256, 128)
    fr = A.sub(0, 0, 48, 128); metal_paint(fr, 1, chips=3)
    for y in ys:  # the shadow gaps round each drawer
        for yy in (y + 0.155, y - 0.155): fr[max(0, row(yy) - 1):row(yy) + 1, 1:47] = hexrgb(0x3a3440)
    fr[row(0.04):, :] = fr[row(0.04):, :] * 0.6 + hexrgb(0x3a3440) * 0.4  # the kick plate
    fr[row(ys[1] + 0.15):row(ys[1] - 0.15), 2:46] = hexrgb(0x2a2430)  # the slot the open drawer came out of
    fr[row(ys[1] + 0.15):row(ys[1] + 0.15) + 3, 2:46] = hexrgb(0x15121a)
    sd = A.sub(48, 0, 64, 128); metal_paint(sd, 2, chips=7, scratches=16)
    for y in (30, 62, 94): sd[y, 2:62] *= 0.86; sd[y + 1, 2:62] = sd[y + 1, 2:62] * 0.9 + 0.1  # pressed ribs
    tp = A.sub(112, 0, 48, 64); metal_paint(tp, 3, chips=2); px_disc(tp, 30, 40, 9, 0xb09a88, r_in=7.4)  # a mug ring
    for k in range(4):
        x, y = 160 + (k % 2) * 48, (k // 2) * 32
        dr = A.sub(x, y, 48, 32); metal_paint(dr, 10 + k, chips=1 + k % 2, scratches=4)
        dr[0, :] *= 0.8; dr[-1, :] *= 0.72; dr[:, 0] *= 0.85; dr[:, -1] *= 0.85
        dr[6:9, 14:34] = hexrgb(0x2a2430)  # the recess behind the pull
    A.fill(112, 64, 32, 32, 0x7a7684)
    R = dict(fr=A.rect(0, 0, 48, 128), sd=A.rect(48, 0, 64, 128), tp=A.rect(112, 0, 48, 64),
             dr=[A.rect(160 + (k % 2) * 48, (k // 2) * 32, 48, 32) for k in range(4)])
    BOX = {'-z': R['fr'], '+z': R['sd'], '+x': R['sd'], '-x': R['sd'], '+y': R['tp'], '-y': R['tp']}
    paint = mat('fc_paint', 0xffffff, rough=0.25, clearcoat=0.7, tex=A.image())
    chrome = plain('fc_chrome', 0xe8ecf4, rough=0.12, metal=1.0, var=0.05, seed=5)
    # paper atlas: manila folders, forms, a DENIED stamp, drawer label cards, the lanyard strap and badge
    P = Atlas('fc_paper_t', 128)
    mf = P.sub(0, 0, 64, 32); crust(mf, MANILA, 0.05, seed=3); mf[0:4, 40:60] = hexrgb(0xe8c470); mf[0:4, 41:59] *= 0.97
    write(mf, 'q3', 44, 0, 1, 0x7a5a20)
    fm = P.sub(64, 0, 32, 40); crust(fm, PAPER, 0.03, seed=4); paper_lines(fm, 2, title=0x4fa8d8)
    dn = P.sub(96, 0, 32, 40); crust(dn, 0xfff3c2, 0.03, seed=5); paper_lines(dn, 3); stamp(dn, 'DENIED', 1, 18, 0xd0182a)
    for k, t in enumerate(['overdue', 'late', 'later', 'never']):
        lb = P.sub(k * 32, 40, 32, 12); lb[:] = hexrgb(0xfffdf4); write(lb, t, 16 - tw(t) // 2, 3, 1, 0x1a2a8a, wob=1, seed=k)
    stp = P.sub(0, 56, 8, 64); stripes(stp, [HOT, HOT, YEL], 3); stp[:, 0] = stp[:, -1] = hexrgb(0xb02aa0)
    bd = P.sub(8, 56, 24, 36); paint_badge(bd, 'TODD')
    paper = mat('fc_paper', 0xffffff, rough=0.6, tex=P.image())
    PR = dict(mf=P.rect(0, 0, 64, 32), fm=P.rect(64, 0, 32, 40), dn=P.rect(96, 0, 32, 40),
              lb=[P.rect(k * 32, 40, 32, 12) for k in range(4)], strap=P.rect(0, 56, 8, 64), badge=P.rect(8, 56, 24, 36))
    # spray tags (alpha clipped): UNPAID / keep out down the left side, the crossed ☺ on the top drawer, "no files"
    def tags(px, al):
        m = text_mask(64, 128, 'UNPAID', 4, 4, 3) | text_mask(64, 128, 'keep out', 16, 36, 2, lower=True, wob=1, seed=9)
        spray(px[0:64, 0:128], al[0:64, 0:128], m, HOT, seed=3, drips=6)
        spray(px[64:128, 0:64], al[64:128, 0:64], crossed_smiley(64, 64, 32, 32, 22, 3.2), 0x1a1a1a, seed=5, drips=4)
        m3 = text_mask(64, 64, 'no', 6, 10, 3, lower=True, wob=1, seed=2) | text_mask(64, 64, 'files', 2, 36, 2, lower=True, wob=1, seed=4)
        spray(px[64:128, 64:128], al[64:128, 64:128], m3, CYAN, seed=6, drips=3)
    sp = decal_mat('fc_spray', rgba_image('fc_spray_t', 128, 128, tags))
    O, L = [], []
    # the body: subdivided so it can take a kick, then bevelled
    body = box((W, H, D), (0, H / 2, 0), paint, name='cab'); subdiv(body, 1)
    dent(body, (W / 2, 0.95, 0.05), 0.34, 0.06); dent(body, (0.12, H, -0.25), 0.28, 0.045); dent(body, (-0.25, 0.25, 0.3), 0.22, 0.03)
    bevel(body, 0.016, 1); uv_dir(body, BOX); O.append(body)
    L.append(uv_dir(box((W, H, D), (0, H / 2, 0), paint), BOX))
    def furniture(y, z, k, tilt=(0, 0, 0)):
        """the pull (a chrome cup handle) and the label frame with its card"""
        out = [box((0.2, 0.034, 0.036), (0, y + 0.045, z - 0.016), chrome, taper=(0.86, 0.6), rot=tilt, name='pull'),
               box((0.12, 0.046, 0.008), (0, y + 0.105, z - 0.002), chrome, rot=tilt, name='frame')]
        lc = quad((0, y + 0.105, z - 0.0085), 0.1, 0.032, paper, 'z', sx=-1); uv_remap(lc, PR['lb'][k])
        return out + [lc]
    for k, y in enumerate(ys):
        if k == 1: continue  # this one hangs open (below)
        tilt = (0, 0, 0.01 * (k - 1.5))
        f = box((0.455, 0.302, 0.024), (0, y, FZ - 0.011), paint, rot=tilt, taper=(1.0, 0.985)); uv_fit(f, R['dr'][k]); O.append(f)
        L.append(fit(box((0.455, 0.302, 0.024), (0, y, FZ - 0.011), paint, rot=tilt), R['dr'][k]))
        O += furniture(y, FZ - 0.023, k, tilt)
    # the open drawer: slid out, the left runner gone so it droops and twists, files spilling out
    y2 = ys[1]; out = 0.36; z2 = FZ - out
    dr = [box((0.455, 0.302, 0.024), (0, y2, z2 - 0.011), paint, name='dfront')]
    tr = box((0.42, 0.24, 0.6), (0, y2 - 0.015, z2 + 0.3), paint, name='tray')
    bm = bmesh.new(); bm.from_mesh(tr.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9 or f.normal.y > 0.9], context='FACES'); bm.to_mesh(tr.data); bm.free()
    uv_fit(tr, A.rect(112, 64, 32, 32)); dr.append(tr)
    dr += furniture(y2, z2 - 0.023, 1)
    for i, (x, a, h_) in enumerate(((-0.12, 0.25, 0.34), (0.0, -0.1, 0.3), (0.13, -0.32, 0.33))):  # folders standing up
        fo = box((0.012, h_, 0.3), (x, y2 - 0.133 + h_ / 2, z2 + 0.25 + i * 0.07), paper, rot=(0, 0.2 * i - 0.1, a)); uv_fit(fo, PR['mf'])
        dr.append(fo)
    # a form hanging over the lip, one sticking up
    fz0 = z2 - 0.024
    dp = sheet_grid([[(0.02 + c * 0.105, y2 + 0.1, fz0 + 0.12) for c in range(3)],
                     [(0.015 + c * 0.105, y2 + 0.158, fz0 + 0.004) for c in range(3)],
                     [(0.03 + c * 0.1, y2 + 0.04, fz0 - 0.022 - 0.01 * c) for c in range(3)]], paper, 'drape')
    uv_remap(dp, PR['dn']); face_toward(dp, (0, 0.5, -1)); dr.append(dp)
    up = sheet_grid([[(-0.2, y2 + 0.3, z2 + 0.18), (0.0, y2 + 0.33, z2 + 0.16)], [(-0.2, y2 + 0.0, z2 + 0.26), (0.0, y2 + 0.02, z2 + 0.24)]], paper, 'up')
    uv_remap(up, PR['fm']); face_toward(up, (0, 0, -1)); dr.append(up)
    uv_fit(dr[0], R['dr'][1])
    xf(dr, rot=(-0.13, 0.07, 0.05), pivot=(0, y2, FZ - 0.05))
    O += dr
    ld = fit(box((0.455, 0.3, 0.6), (0, y2 - 0.02, z2 + 0.29), paint), R['dr'][1]); xf([ld], rot=(-0.13, 0.07, 0.05), pivot=(0, y2, FZ - 0.05)); L.append(ld)
    # spilled paper fanned on the floor
    for i, (x, z, a, rect) in enumerate(((-0.12, -0.88, 0.4, 'fm'), (0.16, -0.92, -0.7, 'dn'), (0.02, -1.08, 1.3, 'fm'), (-0.32, -0.62, -0.2, 'dn'), (0.3, -0.62, 0.9, 'fm'))):
        mid = [[(-0.105, 0.012 + 0.03 * (i % 2), -0.0), (0.105, 0.012, 0.0)]] if i % 2 else []
        sh = sheet_grid([[(-0.105, 0.004 + 0.002 * i, 0.15), (0.105, 0.004 + 0.002 * i, 0.15)]] + mid +
                        [[(-0.105, 0.004 + 0.003 * i, -0.15), (0.105, 0.006 + 0.002 * i, -0.15)]], paper, 'sheet')
        xf([sh], rot=(0, a, 0), move=(x, 0, z)); uv_remap(sh, PR[rect]); face_toward(sh, (0, 1, 0)); O.append(sh)
    for x, z, a in ((0.0, -0.55, 0.15),):
        fo = box((0.32, 0.012, 0.24), (x, 0.006, z), paper, rot=(0, a, 0.0)); uv_fit(fo, PR['mf']); O.append(fo)
    # spray tags
    t1 = quad((-W / 2 - 0.0025, 0.86, 0.0), 0.66, 0.33, sp, 'x', sx=-1); uv_remap(t1, (0, 0.5, 1, 1)); O.append(t1)
    yt = ys[3]
    t2 = quad((0.0, yt - 0.06, FZ - 0.0255), 0.2, 0.2, sp, 'z', sx=-1); uv_remap(t2, (0, 0, 0.5, 0.5)); O.append(t2)
    t3 = quad((W / 2 + 0.0025, 0.42, 0.05), 0.42, 0.42, sp, 'x', sx=1); uv_remap(t3, (0.5, 0, 1, 0.5)); O.append(t3)
    # a lanyard knotted round the top pull, its badge dangling over the drawer
    hy = yt + 0.045; hz = FZ - 0.056
    pts = [(-0.045, hy + 0.012, hz + 0.02), (-0.04, hy + 0.02, hz - 0.012), (-0.03, hy - 0.03, hz - 0.016), (-0.018, hy - 0.13, hz - 0.006),
           (0.0, hy - 0.175, hz), (0.02, hy - 0.12, hz - 0.008), (0.04, hy - 0.02, hz - 0.016), (0.05, hy + 0.012, hz + 0.02)]
    st = sweep(pts, 0.0085, paper, seg=3, squash=(1.0, 0.3), name='lanyard'); uv_fit(st, PR['strap'], mode='front'); O.append(st)
    card = box((0.058, 0.085, 0.004), (0.0, hy - 0.22, hz + 0.002), paper, rot=(0.08, 0, 0.1), name='badge'); uv_fit(card, PR['badge']); O.append(card)
    return O, dict(CMT, _lod=L, paint=['fc_paint'], col=[0.5, 1.35, 0.7], note='barricade piece: stack, line up, tip over')


# ================================================================================================ traffic cone
def build_cone():
    A = Atlas('cn_t', 64, 32)
    body = A.sub(0, 0, 64, 32); crust(body, 0xff6a1a, 0.05, seed=2)
    for x0, x1 in ((24, 33), (38, 44)): crust(body[:, x0:x1], 0xf8f8f2, 0.04, seed=x0)  # the reflective collars (u = up)
    body[:, 50:] = body[:, 50:] * 0.6 + hexrgb(0x5a2008) * 0.4  # scorched where it melted
    body[:, 58:] = hexrgb(0x3a1608)
    grime(body[:, 0:20], 0x9a5a3a, 0.15, seed=3, blob=4)
    base = A.fill(0, 28, 8, 4, 0x2a262c)
    m = mat('cn_plastic', 0xffffff, rough=0.3, clearcoat=0.5, tex=A.image())
    prof = [(0.142, 0.03), (0.128, 0.13), (0.11, 0.25), (0.091, 0.37), (0.071, 0.48), (0.05, 0.58), (0.031, 0.66), (0.0, 0.72)]
    c = lathe(prof, (0, 0, 0), m, seg=8, axis='y', name='cone', cap=False)
    uv_cyl(c, axis='y', a0=0.0, a1=0.75)
    for l in c.data.uv_layers.active.data: l.uv = (l.uv[0] * 0.9, 0.45 + l.uv[1] * 0.25)
    def melt(p):  # the top half slumped over to +x like a candle that got too close to a barrel
        x, y, z = p
        t = max(0.0, (y - 0.32) / 0.4)
        bulge = 1 + 0.12 * math.exp(-((y - 0.5) / 0.08) ** 2) * (1 if x > 0 else 0.4)
        return (x * bulge + 0.11 * t * t, y - 0.06 * t * t * t, z * (1 + 0.1 * t))
    deform(c, melt)
    b = box((0.37, 0.03, 0.37), (0, 0.015, 0), m, taper=(0.98, 1.0)); uv_fit(b, base)
    for v in b.data.vertices:  # one melted corner of the base droops
        if v.co.x > 0.1 and v.co.y < -0.1: v.co.z -= 0.012
    return [c, b], dict(CMT, col=[0.37, 0.72, 0.37])


# ================================================================================================ jersey barrier
def build_jersey():
    Lx = 3.0
    A = Atlas('jb_t', 128)
    fr = A.sub(0, 0, 128, 40); crust(fr, 0xd6cbbb, 0.07, seed=4, speck=[(0xa89c8c, 0.05), (0xece4d6, 0.04)])
    grime(fr, 0xa8907a, 0.1, seed=6, blob=8)
    for k in range(0, 128, 2): fr[33 + (k % 5 == 0):40, k] *= 0.8  # road grime splashed up the foot
    def hazard(px):
        h, w = px.shape[:2]; y, x = np.mgrid[0:h, 0:w]
        k = ((x + y) // 5) % 2 == 0
        px[k] = px[k] * 0.3 + hexrgb(0xff5a1a) * 0.7
        px[~k] = px[~k] * 0.4 + hexrgb(0xfff4e0) * 0.6
    hazard(fr[4:26, 0:14]); hazard(fr[4:26, 114:128])
    text_px(fr, 'HWY 9', 20, 8, 1, 0x2a2630); text_px(fr, 'BRIDGE 4', 20, 17, 1, 0x2a2630)
    smiley(fr, 74, 13, 5, face=0xffd84a, ink=0x2a2630); text_px(fr, 'ROADS', 82, 10, 1, 0x2a2630)
    write(fr, 'lane closed', 14, 26, 1, HOT, wob=1, seed=3, bold=True)
    write(fr, 'forever', 84, 26, 1, HOT, wob=1, seed=4, bold=True)
    tp = A.sub(0, 40, 128, 16); crust(tp, 0xd2c6b4, 0.06, seed=7); tp[:, ::23] *= 0.85
    en = A.sub(0, 56, 32, 32); crust(en, 0xc8bcac, 0.07, seed=8)
    cn = mat('jb_concrete', 0xffffff, rough=0.62, tex=A.image())
    hz, top, c = 0.305, 0.81, 0.018
    poly = [(-hz, 0.0), (-hz, 0.075 - c), (-hz + c, 0.075), (-0.127, 0.33), (-0.077, top - c), (-0.077 + c, top),
            (0.077 - c, top), (0.077, top - c), (0.127, 0.33), (hz - c, 0.075), (hz, 0.075 - c), (hz, 0.0)]
    o = side(poly, Lx, (0, 0, 0), cn, name='jersey')
    # chipped: a bite out of the top corner at one end, two lifting slots through the foot
    cut(o, box((0.4, 0.4, 0.4), (1.52, 0.84, -0.04), None, rot=(0.5, 0.7, 0.4)))
    for x in (-0.75, 0.75): cut(o, box((0.34, 0.1, 1.0), (x, 0.05, 0), None))
    one_mat([o])
    R = {'-z': A.rect(0, 0, 128, 40), '+z': A.rect(0, 0, 128, 40), '+y': A.rect(0, 40, 128, 16), '-y': A.rect(0, 40, 128, 16), '+x': A.rect(0, 56, 32, 32), '-x': A.rect(0, 56, 32, 32)}
    uv_dir(o, R)
    L = [uv_dir(side(poly[:1] + poly[2:4] + poly[5:7] + poly[8:10] + poly[11:], Lx, (0, 0, 0), cn, name='jl'), R)]
    return [o], dict(CMT, _lod=L, col=[3.0, 0.81, 0.61])


# ================================================================================================ fire barrel
def uv_height(o, y0, y1, rect, u=0.5):
    """u = round the thing (by angle), v = up: for flames that fade from white-hot to red tips"""
    apply_mods(o); me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world
    for pg in me.polygons:
        for li in pg.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            a = (math.atan2(-p.y, p.x) / (2 * math.pi)) % 1.0
            w = min(1, max(0, (p.z - y0) / (y1 - y0)))
            uv[li].uv = (rect[0] + (0.2 + 0.6 * a) * (rect[2] - rect[0]), rect[1] + w * (rect[3] - rect[1]))
    return o


def flame(c, h, r, m, rect, n=5, st=4, twist=0.7, lean=(0.0, 0.0), seed=1, y0=None):
    """a chunky low-poly flame tongue: a twisted star section shrinking to a point, leaning with the draught"""
    rr = random.Random(seed)
    cs = [Vector((c[0] + lean[0] * (i / st) ** 2, c[1] + h * i / st, c[2] + lean[1] * (i / st) ** 2)) for i in range(st + 1)]
    def ring(i, t):
        R = r * (1 - t) ** 0.8 * (1 + 0.25 * math.sin(t * 3.0)) + 0.004
        return [(math.cos(2 * math.pi * k / (2 * n) + twist * i) * R * (1.0 if k % 2 == 0 else 0.5 + 0.1 * rr.random()),
                 math.sin(2 * math.pi * k / (2 * n) + twist * i) * R * (1.0 if k % 2 == 0 else 0.5 + 0.1 * rr.random())) for k in range(2 * n)]
    o = loft(cs[:-1], lambda i, t: ring(i, i / st), m, name='flame', cap=False, up=(0, 0, 1), close=(False, False))
    # pinch: a tip vertex fan
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    top = [v for v in bm.verts if abs(v.co.z - cs[-2].y) < 1e-4]
    fs = [f for f in bm.faces if all(abs(v.co.z - cs[-2].y) < 1e-4 for v in f.verts)]
    bmesh.ops.delete(bm, geom=fs, context='FACES_ONLY')
    tip = bm.verts.new(gv(*cs[-1]))
    top.sort(key=lambda v: math.atan2(v.co.y - (-cs[-2].z), v.co.x - cs[-2].x))
    for i in range(len(top)):
        try: bm.faces.new((top[i], top[(i + 1) % len(top)], tip))
        except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = False
    return uv_height(o, c[1], c[1] + h, rect)


def build_firebarrel():
    # the drum: faded teal paint over candy rust, a ☺BUCKS stencil, soot licking down from the rim
    A = Atlas('fb_drum_t', 128)
    sd = A.sub(0, 0, 128, 64)
    crust(sd, 0x3fa8b0, 0.06, seed=3, block=4)
    r = np.random.default_rng(5)
    nz = np.kron(r.random((5, 9)), np.ones((16, 16)))[:64, :128] * 0.45 + np.kron(r.random((17, 33)), np.ones((4, 4)))[:64, :128] * 0.35 + r.random((64, 128)) * 0.2
    yy = np.mgrid[0:64, 0:128][0] / 64
    rust = nz + 0.35 * yy ** 2 > 0.72  # rust eats the paint, worse near the ground
    sd[rust] = hexrgb(RUST) * (0.85 + 0.3 * nz[rust, None])
    deep = nz + 0.35 * yy ** 2 > 0.92; sd[deep] = hexrgb(RUST2)
    m = np.zeros((64, 128, 3), np.float32)  # the stencil on one side, the small print on the other, bridges cut in
    smiley(m, 10, 30, 7, face=0xffffff, ink=0x000000, ring=0xffffff); text_px(m, 'BUCKS', 20, 26, 2, 0xffffff)
    text_px(m, 'NOW', 91, 22, 1, 0xffffff); text_px(m, 'WORTHLESS', 72, 32, 1, 0xffffff)
    mask = m[:, :, 0] > 0.9
    mask[:, 22:70:12] = False
    sd[mask] = sd[mask] * 0.25 + hexrgb(0xfff8ee) * 0.75
    soot = (yy < 0.22)[:, :, None] * (1 - yy[:, :, None] / 0.22)
    lick = (r.random((64, 128)) < 0.5)[:, :, None]
    sd[:] = sd * (1 - soot * 0.85 * (0.7 + 0.3 * lick)) + hexrgb(0x1a1210) * soot * 0.85 * (0.7 + 0.3 * lick)
    for y in (22, 42): sd[y, :] *= 0.75  # the rolling hoops' shadow
    lid = A.sub(0, 64, 32, 32); crust(lid, RUST2, 0.12, seed=7, speck=RUST, p=0.2)
    drum = mat('fb_drum', 0xffffff, rough=0.45, metal=0.35, clearcoat=0.3, tex=A.image())
    # fire: emissive gradient (white-hot bottom -> orange -> red tips) + an ember bed swatch
    F = Atlas('fb_fire_t', 32, 64)
    for y in range(64):
        t = y / 63  # image row 0 = top of the flame
        c = np.array(hexrgb(0xff2a10)) * (1 - t) + np.array(hexrgb(0xffb020)) * t if t < 0.6 else np.array(hexrgb(0xffb020)) * (1 - (t - 0.6) / 0.4) + np.array(hexrgb(0xfff6c0)) * ((t - 0.6) / 0.4)
        F.px[y, 0:16] = c
    bed = F.sub(16, 0, 16, 64); crust(bed, 0x3a0a06, 0.2, seed=4, speck=[(0xff6a10, 0.25), (0xffd040, 0.08)])
    fire = mat('fb_fire', 0xffffff, rough=0.8, emit=0xffffff, strength=2.5, tex=F.image(), emit_tex=True)
    FL = F.rect(0, 0, 16, 64); BED = F.rect(16, 0, 16, 64)
    # ☺bucks: pink-and-mint bills, a smiley portrait, burnt edges
    N = Atlas('fb_note_t', 64, 32)
    for k in range(2):
        b = N.sub(0, k * 16, 64, 16); crust(b, 0x9fe8c4 if k == 0 else 0xffc2dc, 0.05, seed=10 + k)
        b[1, 1:63] = b[14, 1:63] = hexrgb(0x2a7a5a if k == 0 else 0xc0306a); b[1:15, 1] = b[1:15, 62] = b[1, 1]
        smiley(b, 32, 8, 5, face=YEL, ink=INK); text_px(b, '1' if k == 0 else '5', 4, 4, 1, 0x2a5a4a); text_px(b, '00', 50, 4, 1, 0x2a5a4a)
        b[:, 56:] = b[:, 56:] * 0.3 + hexrgb(0x1a0c08) * 0.7; b[::3, 54] = hexrgb(0xff7a20)  # the burnt end
    note = mat('fb_note', 0xffffff, rough=0.6, tex=N.image())
    NR = [N.rect(0, 0, 64, 16), N.rect(0, 16, 64, 16)]
    O = []
    R0 = 0.286
    prof = [(R0, 0.0), (R0, 0.27), (0.298, 0.283), (R0, 0.296), (R0, 0.555), (0.298, 0.568), (R0, 0.581), (R0, 0.832),
            (0.296, 0.851), (0.27, 0.851), (0.27, 0.74)]
    d = lathe(prof, (0, 0, 0), drum, seg=10, axis='y', name='drum')
    uv_can(d, 0, 0, 0.0, 0.851, A.rect(0, 0, 128, 64), A.rect(0, 64, 32, 32), turn=0.3)
    multi_mat(d, [drum, fire], lambda n, c: 1 if (n[1] > 0.7 and c[1] > 0.7) else 0)
    me = d.data; uvl = me.uv_layers.active.data  # the ember bed's UVs: a top-down patch of the coal swatch
    for pg in me.polygons:
        if pg.material_index == 1:
            for li in pg.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                uvl[li].uv = (BED[0] + (v.x / 0.6 + 0.5) * (BED[2] - BED[0]), BED[1] + (v.y / 0.6 + 0.5) * (BED[3] - BED[1]))
    dent(d, (0.2, 0.42, -0.22), 0.16, 0.035); dent(d, (-0.29, 0.75, 0.05), 0.14, 0.03)
    O.append(d)
    # air holes chiselled round the bottom, glowing from the fire inside
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        nx, nz_ = math.cos(a), math.sin(a)
        q = quad((0, 0, 0), 0.07, 0.05, fire, 'z', sx=-1); uv_remap(q, (BED[0], 0.45, BED[2], 0.55))
        xf([q], rot=(0, -a - math.pi / 2, 0), move=(nx * (R0 + 0.0025), 0.12, -nz_ * (R0 + 0.0025)))
        O.append(q)
    # flames out of the top, embers above them
    O.append(flame((0.0, 0.73, 0.0), 0.62, 0.2, fire, FL, n=4, st=4, twist=0.6, lean=(0.06, 0.04), seed=1))
    O.append(flame((0.1, 0.74, -0.08), 0.36, 0.1, fire, FL, n=4, st=3, twist=-0.8, lean=(0.08, -0.05), seed=2))
    O.append(flame((-0.12, 0.74, 0.08), 0.42, 0.11, fire, FL, n=4, st=3, twist=0.9, lean=(-0.07, 0.03), seed=3))
    rr = random.Random(4)
    for k in range(5):
        p = (rr.uniform(-0.25, 0.25), rr.uniform(1.15, 1.75), rr.uniform(-0.25, 0.25))
        e = ball(0.014 + rr.random() * 0.008, p, fire, seg=3, rings=2, name='ember'); uv_remap(e, (FL[0], FL[1] + 0.85 * (FL[3] - FL[1]), FL[2], FL[3])) if e.data.uv_layers else uv_fit(e, (FL[0], 0.9, FL[2], 0.98))
        O.append(e)
    # ☺bucks feeding the fire: stuck in the rim, curled, one blown onto the ground
    for k, (x, y, z, ry, rx, rz) in enumerate(((0.17, 0.84, 0.14, 0.6, -0.5, 0.3), (-0.2, 0.84, -0.13, 2.2, 0.6, -0.2), (0.02, 0.85, 0.22, -0.4, -0.9, 0.0))):
        b = sheet_grid([[(-0.1, 0.0, -0.045), (0.0, 0.012, -0.045), (0.1, 0.0, -0.045)], [(-0.1, 0.0, 0.045), (0.0, 0.012, 0.045), (0.1, 0.0, 0.045)]], note, 'note')
        uv_remap(b, NR[k % 2]); xf([b], rot=(rx, ry, rz), move=(x, y, z)); O.append(b)
    g = sheet_grid([[(-0.1, 0.004, -0.045), (0.0, 0.02, -0.045), (0.1, 0.004, -0.045)], [(-0.1, 0.004, 0.045), (0.0, 0.02, 0.045), (0.1, 0.004, 0.045)]], note, 'note')
    uv_remap(g, NR[1]); xf([g], rot=(0, 0.9, 0), move=(0.38, 0, -0.3)); face_toward(g, (0, 1, 0)); O.append(g)
    L = [lathe([(0.286, 0.0), (0.29, 0.851), (0.27, 0.851), (0.27, 0.74)], (0, 0, 0), drum, seg=8, axis='y', name='dl'),
         flame((0.0, 0.73, 0.0), 0.62, 0.2, fire, FL, n=3, st=2, twist=0.6, lean=(0.06, 0.04), seed=1)]
    uv_can(L[0], 0, 0, 0.0, 0.851, A.rect(0, 0, 128, 64), A.rect(0, 64, 32, 32), turn=0.3)
    return O, dict(CMT, _lod=L, col=[0.6, 0.86, 0.6], lights=[[0, 1.05, 0, 0xff8a2a]], glow=['fb_fire'], note='warm: Unpaid sit round it')


# ================================================================================================ office chair
def build_officechair():
    # fabric (paint: tinted per instance): weave, seams, a coffee stain, the tear the foam comes out of
    F = Atlas('oc_paint_t', 64)
    for k in range(2):
        fb = F.sub(k * 32, 0, 32, 64); crust(fb, 0xf4f2f4, 0.05, seed=3 + k); fb[::2, :] *= 0.94; fb[:, ::2] *= 0.96
        fb[1, :] = fb[62, :] = fb[:, 1] = fb[:, 30] = hexrgb(0xc8c4cc)  # piping
    fb = F.sub(32, 0, 32, 64)  # the seat top: a coffee ring, the split the foam comes out of
    px_disc(fb, 22, 18, 5, 0xc8b49a, r_in=3.8)
    px_line(fb, 5, 42, 14, 54, 0x2a2026, 3); px_line(fb, 6, 43, 13, 53, 0xffd84a, 1.2)
    FP, FS = F.rect(0, 0, 32, 64), F.rect(32, 0, 32, 64)
    paint = mat('oc_paint', 0xffffff, rough=0.85, tex=F.image())
    # bits: black plastic, yellow foam, strap webbing, duct tape
    B = Atlas('oc_bits_t', 64)
    pl = B.sub(0, 0, 32, 32); crust(pl, 0x2a2830, 0.08, seed=4, speck=0x4a4652, p=0.08)
    fo = B.sub(32, 0, 32, 32); crust(fo, 0xffd84a, 0.12, seed=5, speck=0xf0b830, p=0.2)
    st = B.sub(0, 32, 32, 32); stripes(st, [0x3a6ad8, 0x2a4aa8], 2, horizontal=False); st[:, 15:17] = hexrgb(0xffe14d)
    tp = B.sub(32, 32, 32, 32); crust(tp, 0xb8bcc4, 0.1, seed=6); tp[::5, :] *= 0.9
    bits = mat('oc_bits', 0xffffff, rough=0.4, clearcoat=0.3, tex=B.image())
    PL, FO, ST, TP = B.rect(0, 0, 32, 32), B.rect(32, 0, 32, 32), B.rect(0, 32, 32, 32), B.rect(32, 32, 32, 32)
    chrome = plain('oc_chrome', 0xdfe3ec, rough=0.15, metal=1.0, var=0.05, seed=7)
    sp = decal_mat('oc_spray', rgba_image('oc_spray_t', 64, 64, lambda px, al: spray(px, al, crossed_smiley(64, 64, 32, 32, 24, 3.5), 0xff3030, seed=2, drips=4)))
    O = []
    for k in range(5):  # the five-star base: legs out from the hub, a castor under each tip (but the front one)
        a = 2 * math.pi * k / 5
        lg = box((0.05, 0.035, 0.3), (0, 0.085, -0.17), bits, taper=(0.7, 0.8), name='leg'); uv_fit(lg, PL)
        xf([lg], rot=(0, a, 0)); O.append(lg)
        if k:
            c = cyl(0.03, 0.045, (0, 0.03, -0.3), bits, axis='x', seg=5, name='castor'); uv_fit(c, PL)
            xf([c], rot=(0, a, 0)); O.append(c)
    O.append(fit(cyl(0.045, 0.07, (0, 0.095, 0), bits, axis='y', seg=6), PL))
    O.append(cyl(0.026, 0.3, (0, 0.27, 0), chrome, axis='y', seg=6))
    O.append(fit(box((0.2, 0.05, 0.22), (0, 0.43, 0.01), bits), PL))
    O.append(fit(box((0.48, 0.03, 0.46), (0, 0.465, 0), bits), PL))
    seat = pillow((0.5, 0.09, 0.48), (0, 0.515, -0.005), paint, puff=0.2, top=1.2); uv_dir(seat, {'+y': FS}, FP); O.append(seat)
    fm = ball(0.07, (-0.12, 0.56, -0.12), bits, scale=(1.2, 0.6, 1.0), seg=6, rings=4, name='foam'); jitter(fm, 0.015, seed=3); uv_fit(fm, FO); O.append(fm)
    tq = quad((0.1, 0.56, 0.0), 0.06, 0.4, bits, 'y'); uv_remap(tq, TP); xf([tq], rot=(0.0, 0.5, 0.05), pivot=(0.1, 0.56, 0.0)); O.append(tq)  # duct tape over the other split
    # the back: bar bent, shell flopped back, two belts bolted on so a raider can wear it as a back plate
    O.append(sweep([(0, 0.43, 0.1), (0, 0.44, 0.26), (0, 0.52, 0.32), (0, 0.62, 0.33)], 0.022, chrome, seg=4, squash=(0.5, 1.0), name='bar'))
    bk = []
    bk.append(fit(box((0.46, 0.56, 0.03), (0, 0.88, 0.34), bits), PL))
    cu = pillow((0.44, 0.52, 0.08), (0, 0.88, 0.3), paint, puff=0.18, pinch=0.06); uv_fit(cu, FP); bk.append(cu)
    for x in (-0.12, 0.12):
        stp = sweep([(x, 1.1, 0.35), (x, 1.06, 0.47), (x, 0.84, 0.5), (x, 0.68, 0.36)], 0.022, bits, seg=3, squash=(0.25, 1.0), name='strap')
        uv_fit(stp, ST); bk.append(stp)
    t = quad((0.0, 0.84, 0.3575), 0.3, 0.3, sp, 'z', sx=1); bk.append(t)
    xf(bk, rot=(0.32, 0.04, -0.05), pivot=(0, 0.62, 0.33)); O += bk
    O.append(fit(box((0.04, 0.2, 0.06), (0.245, 0.56, 0.02), bits), PL))  # the one armrest left
    O.append(fit(box((0.075, 0.035, 0.26), (0.245, 0.675, 0.0), bits, taper=(0.9, 0.8)), PL))
    O.append(fit(box((0.04, 0.07, 0.06), (-0.245, 0.5, 0.02), bits, rot=(0.0, 0.0, 0.25)), PL))  # the snapped one
    # one castor gone: it sits on the bare leg tip and leans into it, the back castors off the floor
    th = math.asin(0.0675 / 0.218)
    xf(O, rot=(-th, 0, 0), pivot=(0, 0, -0.102))
    xf(O, rot=(0, 0.55, 0))
    return O, dict(CMT, paint=['oc_paint'], col=[0.66, 1.1, 0.7], note='wrecked swivel chair, leans on the missing castor; raider back-plate straps')


# ================================================================================================ tyre stack
def ring_mesh(sec, seg, m, rect, pos=(0, 0, 0), name='ring', jit=0.0, seed=1):
    """a closed ring (tyres): cross-section sec = [(radius, y)] loop, swept round game y. UVs: u round, v across the
    section, into rect (the seam gets its own u = 1 column so the tread wraps cleanly)"""
    r = random.Random(seed); bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    n = len(sec); V = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; k = 1 + r.uniform(-jit, jit)
        V.append([bm.verts.new(gv(pos[0] + math.cos(a) * rr * k, pos[1] + y, pos[2] + math.sin(a) * rr * k)) for rr, y in sec])
    u0, v0, u1, v1 = rect
    for i in range(seg):
        for j in range(n):
            q = (V[i][j], V[(i + 1) % seg][j], V[(i + 1) % seg][(j + 1) % n], V[i][(j + 1) % n])
            f = bm.faces.new(q)
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                lp[uvl].uv = (u0 + ii / seg * (u1 - u0), v0 + jj / n * (v1 - v0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 70)
    return o


def build_tirestack():
    T = Atlas('ts_rubber_t', 128)
    looks = [(0x2a282e, None), (0xff6fae, None), (0xffd84a, None), (0x2a282e, 0xf4f0e8)]  # black, raider-pink, yellow, whitewall
    for k, (col, wall) in enumerate(looks):
        px = T.sub(0, k * 24, 128, 24)
        crust(px, col, 0.08, seed=20 + k, speck=0x4a4652 if col == 0x2a282e else 0x2a282e, p=0.06 if col == 0x2a282e else 0.03)
        # v rows across the section (inner-bottom -> outer-bottom -> tread -> outer-top -> inner): tread blocks in the middle
        tr = px[8:16]; tr[:, ::4] *= 0.55; tr[2:4, 2::8] *= 0.6
        if col != 0x2a282e: grime(px, 0x2a282e, 0.22, seed=k, blob=4)  # the paint's worn through to black
        if wall: px[3:5, :] = hexrgb(wall); px[19:21, :] = hexrgb(wall)
        text_px(px, 'RETREAD', 10, 17, 1, 0x5a5860 if col == 0x2a282e else 0x2a282e); text_px(px, 'RETREAD', 74, 17, 1, 0x5a5860 if col == 0x2a282e else 0x2a282e)
    cone = T.sub(0, 96, 32, 32); crust(cone, 0xff6a1a, 0.06, seed=9); cone[10:16, :] = hexrgb(0xf8f8f2)
    rub = mat('ts_rubber', 0xffffff, rough=0.55, clearcoat=0.25, tex=T.image())
    metal = plain('ts_pipe', 0xc87a4a, rough=0.4, metal=0.6, var=0.18, speck=RUST2, p=0.2, seed=11)
    def flag(px, al):
        h, w = px.shape[:2]
        crust(px, 0xffe14d, 0.06, seed=3); al[:] = 1
        y, x = np.mgrid[0:h, 0:w]
        rag = (x > w - 10 + 6 * np.sin(y * 0.9) + 3 * np.cos(y * 2.3))  # the frayed fly end
        al[rag] = 0
        spray(px, al, crossed_smiley(h, w, 30, 28, 18, 3.0), INK, seed=4, drips=3, over=0.2)
        spray(px, al, text_mask(h, w, 'unpaid', 8, 50, 1, lower=True), 0xff3030, seed=5, drips=1, over=0.1)
        px[:, 0:3] = hexrgb(0xf0c030)  # the hem round the pole
    fl = decal_mat('ts_flag', rgba_image('ts_flag_t', 64, 64, flag), rough=0.8)
    O = []
    rr = random.Random(5)
    lay = [(0.0, 0.0, 0), (0.05, -0.03, 1), (-0.03, 0.04, 2), (0.02, 0.0, 3)]
    for k, (dx, dz, look) in enumerate(lay):
        y = 0.1 + k * 0.198
        o = ring_mesh([(0.205, -0.075), (0.3, -0.1), (0.325, 0.0), (0.3, 0.1), (0.205, 0.075)], 8, rub, T.rect(0, look * 24, 128, 24), (0, 0, 0), name='tyre', jit=0.025, seed=k)
        xf([o], rot=(rr.uniform(-0.05, 0.05), rr.uniform(0, 3), rr.uniform(-0.05, 0.05)), move=(dx, y, dz)); O.append(o)
    # the flag pole: a bent scaffold pipe down the middle, a traffic cone jammed on top as the finial
    top = (0.06, 2.45, 0.02)
    O.append(sweep([(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.03, 1.9, 0.01), top], 0.024, metal, seg=4, name='pole'))
    cn = lathe([(0.075, 0.0), (0.045, 0.12), (0.0, 0.24)], (top[0], top[1] - 0.04, top[2]), rub, seg=6, axis='y', cap=False, name='cone')
    uv_fit(cn, T.rect(0, 96, 32, 32)); O.append(cn)
    pts = []
    for rr_ in range(3):
        row = []
        for c in range(4):
            x = 0.005 + c * 0.24; yy = 2.36 - rr_ * 0.21 - 0.03 * c * c * 0.3
            row.append((top[0] + x, yy, top[2] + 0.07 * math.sin(c * 1.7 + rr_ * 0.5) * (c / 3) ** 0.7))
        pts.append(row)
    f = sheet_grid(pts, fl, 'flag'); O.append(f)
    # a tie knotted round the pole under the flag, an office trophy
    O.append(sweep([(top[0] - 0.03, 1.62, top[2]), (top[0] + 0.0, 1.6, top[2] - 0.035), (top[0] + 0.05, 1.5, top[2] - 0.04), (top[0] + 0.08, 1.32, top[2] - 0.02)],
                   [0.012, 0.014, 0.02, 0.03], rub, seg=3, squash=(1.0, 0.25), name='tie'))
    uv_fit(O[-1], T.rect(0, 30, 128, 2))
    return O, dict(CMT, col=[0.7, 0.8, 0.7], note='raider camp marker: the flag pole sticks up to 2.5 m')


# ================================================================================================ skeleton in a lanyard
def build_skeleton_lanyard():
    B = Atlas('sk_bone_t', 64)
    pb = B.sub(0, 0, 32, 32); crust(pb, 0xf0e2c4, 0.06, seed=3, speck=0xc8b890, p=0.08)
    fc = B.sub(32, 0, 32, 32); crust(fc, 0xf0e2c4, 0.05, seed=4)  # the skull's face (seen from -z)
    for ex in (10, 22):
        px_disc(fc, ex, 15, 5.2, 0x2a2030); px_disc(fc, ex - 1.5, 13.5, 1.2, 0x5a4a6a)
    fc[21:25, 15:17] = hexrgb(0x2a2030); fc[22:24, 14:18] = hexrgb(0x2a2030)  # the nose hole
    fc[27:29, 9:23] = hexrgb(0x2a2030); fc[25:31, 10:23:3] = hexrgb(0x2a2030)  # top teeth
    jw = B.sub(0, 32, 32, 16); crust(jw, 0xf0e2c4, 0.05, seed=5); jw[0:4, 4:28] = hexrgb(0xfffdf4); jw[0:5, 4:28:4] = hexrgb(0x2a2030)
    bone = mat('sk_bone', 0xffffff, rough=0.35, clearcoat=0.5, tex=B.image())
    PB, FC, JW = B.rect(0, 0, 32, 32), B.rect(32, 0, 32, 32), B.rect(0, 32, 32, 16)
    def ribs(px, al):
        h, w = px.shape[:2]
        crust(px, 0xf0e2c4, 0.05, seed=6)
        for k in range(5):  # rib bands with gaps between (see-through), the sternum down the middle
            y0 = 6 + k * 10; al[y0:y0 + 6, :] = 1
        al[:, 29:35] = 1; al[:4, :] = 1; al[58:, :] = 0
        px[al > 0] *= 1.0
    rib = decal_mat('sk_ribs', rgba_image('sk_ribs_t', 64, 64, ribs), rough=0.35, cc=0.5)
    C = Atlas('sk_cloth_t', 64)
    tie = C.sub(0, 0, 16, 64); stripes(tie, [0xff3030, 0xff3030, 0xffe14d], 3); tie[:] = np.roll(tie, 1, axis=1)
    stp = C.sub(16, 0, 8, 64); stripes(stp, [CYAN, CYAN, 0x2a8ad8], 3)
    bd = C.sub(24, 0, 24, 36); paint_badge(bd, 'TEMP')
    mg = C.sub(24, 36, 40, 28); crust(mg, 0xfdfdfb, 0.03, seed=7); text_px(mg, '#1', 3, 4, 2, 0xff4fd8); write(mg, 'intern', 3, 19, 1, INK)
    cloth = mat('sk_cloth', 0xffffff, rough=0.5, clearcoat=0.3, tex=C.image())
    TIE, STP, BD, MG = C.rect(0, 0, 16, 64), C.rect(16, 0, 8, 64), C.rect(24, 0, 24, 36), C.rect(24, 36, 40, 28)
    O = []
    def bonerod(a, b, r=0.022, knob=False):
        o = rod(a, b, r, bone, seg=4, r1=r * 0.85); uv_fit(o, PB); out = [o]
        if knob: out.append(fit(ball(r * 1.55, b, bone, seg=4, rings=3, name='knob'), PB))
        return out
    # pelvis + spine (slumped, leaning back into the wall at +z)
    O.append(fit(ball(0.1, (0, 0.11, 0.08), bone, scale=(1.3, 0.7, 0.9), seg=6, rings=4, name='pelvis'), PB))
    sp_ = [(0, 0.14, 0.12), (0, 0.3, 0.18), (0.005, 0.45, 0.19), (0.02, 0.57, 0.15), (0.04, 0.63, 0.11)]
    O.append(fit(sweep(sp_, 0.024, bone, seg=3, name='spine'), PB))
    cage = ball(0.14, (0, 0.0, 0), rib, scale=(1.0, 1.15, 0.78), seg=8, rings=5, name='ribcage'); uv_fit(cage, (0, 0, 1, 1), mode='front')
    xf([cage], rot=(-0.2, 0, 0.04), move=(0.004, 0.42, 0.12)); O.append(cage)
    # the skull: big and round (cartoon), face texture on the front, jaw hanging open a bit, head lolled sideways
    sk = ball(0.13, (0, 0, 0), bone, scale=(1.0, 0.95, 1.05), seg=8, rings=6, name='skull'); uv_dir(sk, {'-z': FC}, PB)
    jaw = box((0.15, 0.05, 0.11), (0, -0.1, -0.05), bone, taper=(0.8, 1.0), name='jaw'); uv_dir(jaw, {'-z': JW, '+y': JW}, PB)
    xf([jaw], rot=(0.25, 0, 0), pivot=(0, -0.08, 0.04))
    xf([sk, jaw], rot=(-0.3, 0.3, -0.38), move=(0.07, 0.74, 0.06)); O += [sk, jaw]
    # legs: the right one stretched out, the left knee up
    for hip, knee, ank, toe in (((0.09, 0.1, 0.05), (0.12, 0.13, -0.35), (0.14, 0.07, -0.72), (0.2, 0.15, -0.82)),
                                ((-0.09, 0.1, 0.05), (-0.16, 0.38, -0.25), (-0.14, 0.07, -0.45), (-0.16, 0.06, -0.6))):
        O += bonerod(hip, knee, 0.028, knob=True) + bonerod(knee, ank, 0.024)
        O.append(fit(rod(ank, toe, 0.03, bone, seg=4, r1=0.042, name='foot'), PB))
    # arms: the right one flopped on the floor, the left one on the knee, still holding its mug
    for sh, el, wr, hand in (((0.15, 0.5, 0.16), (0.24, 0.27, 0.12), (0.27, 0.04, 0.02), (0.28, 0.03, -0.015)),
                             ((-0.15, 0.5, 0.16), (-0.24, 0.33, -0.04), (-0.18, 0.43, -0.22), (-0.17, 0.44, -0.27))):
        O += bonerod(sh, el, 0.022, knob=True) + bonerod(el, wr, 0.018)
        O.append(fit(box((0.06, 0.03, 0.08), hand, bone, rot=(0.2, 0.3, 0.1), taper=(1.2, 1.0), name='hand'), PB))
    mug = lathe([(0.04, -0.045), (0.042, 0.045), (0.036, 0.045), (0.034, 0.0)], (-0.17, 0.47, -0.29), cloth, seg=6, axis='y', cap=True, name='mug')
    uv_can(mug, -0.17, -0.29, 0.425, 0.515, MG, (MG[0], MG[1], MG[0] + 0.01, MG[1] + 0.01), turn=-1.4); O.append(mug)
    O.append(fit(sweep([(-0.21, 0.5, -0.29), (-0.23, 0.48, -0.29), (-0.23, 0.45, -0.29), (-0.21, 0.44, -0.29)], 0.008, cloth, seg=3, name='mugh'), MG))
    # the tie (knot at the neck, flopped onto the lap) and the lanyard with its TEMP badge
    tie_ = sweep([(0.02, 0.58, 0.06), (0.015, 0.53, 0.012), (0.005, 0.44, -0.012), (-0.01, 0.34, -0.005), (-0.02, 0.25, -0.03), (-0.03, 0.2, -0.12)],
                 [0.012, 0.016, 0.022, 0.026, 0.03, 0.03], cloth, seg=3, squash=(1.0, 0.22), name='tie')
    uv_fit(tie_, TIE, mode='front'); O.append(tie_)
    O.append(fit(box((0.035, 0.03, 0.03), (0.02, 0.585, 0.07), cloth, rot=(0.3, 0, 0)), TIE))
    ly = sweep([(-0.06, 0.6, 0.14), (-0.075, 0.53, 0.04), (-0.055, 0.44, -0.005), (-0.03, 0.37, -0.02), (0.0, 0.345, -0.025), (0.035, 0.37, -0.02),
                (0.06, 0.45, -0.005), (0.08, 0.53, 0.04), (0.07, 0.6, 0.14)], 0.008, cloth, seg=3, squash=(1.0, 0.3), name='lanyard')
    uv_fit(ly, STP, mode='front'); O.append(ly)
    O.append(fit(box((0.06, 0.088, 0.004), (0.005, 0.29, -0.03), cloth, rot=(0.15, 0, 0.12), name='badge'), BD))
    return O, dict(CMT, col=[0.6, 0.9, 1.0], note='sits on the ground with its back against a wall or car at z = +0.25')


# ================================================================================================ paper drift
def build_paperdrift():
    P = Atlas('pd_paper_t', 128)
    pile = P.sub(0, 0, 64, 64)
    crust(pile, 0xf2efe6, 0.05, seed=3)
    r = random.Random(4)
    for k in range(70):  # the drift's own surface: overlapping sheets, forms and shreds seen from above
        x, y, w, h = r.randint(-4, 60), r.randint(-4, 60), r.randint(6, 12), r.randint(8, 14)
        if r.random() < 0.3: w, h = r.randint(2, 3), r.randint(10, 18)  # a shred
        c = r.choice([0xfbf8f0, 0xfbf8f0, 0xfff3c2, 0xeaf2ff, 0xffd8e4])
        sub = pile[max(0, y):max(0, y + h), max(0, x):max(0, x + w)]
        if sub.size:
            sub[:] = hexrgb(c) * (0.92 + 0.08 * r.random()); sub[::3] *= 0.93
            sub[-1:, :] *= 0.8
    forms = []
    for k, (col, hdr, st) in enumerate(((PAPER, 0x4fa8d8, 'DENIED'), (0xfff3c2, None, None), (PAPER, 0xff4fd8, None), (0xeaf2ff, 0x2a8ad8, 'DENIED'),
                                         (0xffd8e4, None, 'LATE'), (PAPER, 0x39b04a, None), (0xfff3c2, 0xff8a2a, 'DENIED'), (PAPER, None, None))):
        x, y = 64 + (k % 4) * 16, (k // 4) * 24
        f = P.sub(x, y, 16, 22); crust(f, col, 0.03, seed=10 + k); paper_lines(f, k, step=2, margin=2, title=hdr)
        if st: f[8:11, 2:14] = hexrgb(0xd0182a); f[9, 3:13:2] = hexrgb(0xffd0d0)  # a tiny red stamp
        forms.append(P.rect(x, y, 16, 22))
    big = P.sub(64, 48, 64, 24); crust(big, PAPER, 0.03, seed=30); paper_lines(big, 5, step=3, margin=3, title=0x4fa8d8); stamp(big, 'DENIED', 14, 10, 0xd0182a)
    big2 = P.sub(64, 72, 64, 24); crust(big2, 0xfff3c2, 0.03, seed=31); paper_lines(big2, 6, step=3, margin=3); stamp(big2, 'OVERDUE', 10, 10, 0xd0182a)
    shred = P.sub(0, 64, 64, 8); crust(shred, PAPER, 0.03, seed=32); shred[:, ::2] *= 0.94; shred[3, :] *= 0.8
    paper = mat('pd_paper', 0xffffff, rough=0.7, tex=P.image())
    BIG = [P.rect(64, 48, 64, 24), P.rect(64, 72, 64, 24)]
    O = []
    # the drift: a low wind-blown mound, steeper on the windward side, a ragged edge
    Rx, Rz = 1.5, 1.05
    def hgt(u):  # u = 0 centre .. 1 edge
        return 0.3 * max(0.0, 1 - u * u) ** 1.4
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); seg = 12; rings = [0.0, 0.35, 0.65, 0.88, 1.0]
    rr = random.Random(7)
    def P3(a, u):
        e = 1 + 0.1 * math.sin(a * 3 + 1) + 0.06 * math.sin(a * 7)
        x, z = math.cos(a) * Rx * u * e, math.sin(a) * Rz * u * e
        y = hgt(u) * (1 + 0.25 * math.cos(a)) + (rr.uniform(-0.015, 0.015) if 0 < u < 1 else 0)
        return (x, y if u < 1 else 0.0, z)
    V = [[bm.verts.new(gv(*P3(2 * math.pi * i / seg, u))) for i in range(seg)] for u in rings[1:]]
    c = bm.verts.new(gv(0, hgt(0) * 1.1, 0))
    for i in range(seg): bm.faces.new((c, V[0][(i + 1) % seg], V[0][i]))
    for a, b_ in zip(V, V[1:]):
        for i in range(seg): bm.faces.new((a[i], a[(i + 1) % seg], b_[(i + 1) % seg], b_[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0: f.normal_flip()
    mound = lib._obj('drift', bm, paper); smooth(mound, 50)
    me = mound.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    R0 = P.rect(0, 0, 64, 64); uv = me.uv_layers.active.data
    for pg in me.polygons:
        for li in pg.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (R0[0] + (v.x / 3.4 + 0.5) * (R0[2] - R0[0]), R0[1] + (v.y / 3.4 + 0.5) * (R0[3] - R0[1]))
    O.append(mound)
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(mound, bpy.context.evaluated_depsgraph_get())
    def ground(x, z):
        hit = bvh.ray_cast(gv(x, 2.0, z), Vector((0, 0, -1)))
        return hit[0].z if hit[0] is not None else 0.0
    # loose sheets on top: each one bent over the surface, one corner tucked in, the other lifting in the wind
    rs = random.Random(11)
    for k in range(30):
        a = rs.uniform(0, 6.28); u = rs.uniform(0.0, 0.8) ** 0.7
        cx, cz = math.cos(a) * Rx * u * 0.8, math.sin(a) * Rz * u * 0.8
        big_ = k < 3
        w, h = (0.3, 0.42) if big_ else (0.21, 0.29)
        yaw = rs.uniform(0, 6.28); ca, sa = math.cos(yaw), math.sin(yaw)
        lift = rs.uniform(0.0, 0.06)
        rows = []
        for j, t in enumerate((-0.5, 0.0, 0.5) if k % 3 == 0 else (-0.5, 0.5)):
            row = []
            for s_ in (-0.5, 0.5):
                x, z = cx + (s_ * w) * ca - (t * h) * sa, cz + (s_ * w) * sa + (t * h) * ca
                y = ground(x, z) + (0.015 if t < 0.5 else 0.015 + lift) - (0.035 if (j == 0 and s_ < 0) else 0)
                row.append((x, y, z))
            rows.append(row)
        sh = sheet_grid(rows, paper, 'sheet')
        uv_remap(sh, BIG[k % 2] if big_ else rs.choice(forms)); face_toward(sh, (0, 1, 0)); O.append(sh)
    for k in range(10):  # shreds: long thin strips curling off the top
        a = rs.uniform(0, 6.28); u = rs.uniform(0.1, 0.8)
        cx, cz = math.cos(a) * Rx * u, math.sin(a) * Rz * u; yaw = rs.uniform(0, 6.28)
        L_ = rs.uniform(0.25, 0.45); dx, dz = math.cos(yaw) * L_ / 2, math.sin(yaw) * L_ / 2
        nx, nz = -math.sin(yaw) * 0.012, math.cos(yaw) * 0.012
        y0, y1 = ground(cx - dx, cz - dz) - 0.01, ground(cx + dx, cz + dz) + rs.uniform(0.02, 0.08)
        sh = sheet_grid([[(cx - dx - nx, y0, cz - dz - nz), (cx - dx + nx, y0, cz - dz + nz)], [(cx + dx - nx, y1, cz + dz - nz), (cx + dx + nx, y1, cz + dz + nz)]], paper, 'shred')
        uv_remap(sh, P.rect(0, 64, 64, 8)); face_toward(sh, (0, 1, 0)); O.append(sh)
    lm = mound.copy(); lm.data = mound.data.copy(); bpy.context.scene.collection.objects.link(lm)
    return O, dict(CMT, _lod=[lm], col=[3.2, 0.32, 2.2], note='paper storm drift: walkable, low; scatter on roads and in dead traffic')


# ================================================================================================ rubble heaps
def conc_atlas(name, size=128):
    """pastel concrete swatches (32 px each): crust + aggregate specks, a painted face stripe on some, broken grey core,
    pink bathroom tiles, the dusty gravel of the heap itself"""
    A = Atlas(name, size)
    R = {}
    for k, c in enumerate(CONC):
        x, y = (k % 4) * 32, (k // 4) * 32
        px = A.sub(x, y, 32, 32); crust(px, c, 0.07, seed=40 + k, speck=[(0x9a948c, 0.05), (0xfffaf0, 0.04)])
        if k % 2 == 0: px[4:9, :] = hexrgb([0x5fd3c6, 0xff6fae, 0xffd84a][k // 2]) * 0.95  # an old painted band
        px[28:, :] *= 0.85
        R['c%d' % k] = A.rect(x, y, 32, 32)
    core = A.sub(64, 32, 32, 32); crust(core, 0xb8b0a6, 0.1, seed=50, speck=[(0x7a746c, 0.12), (0xe8e0d4, 0.06)]); R['core'] = A.rect(64, 32, 32, 32)
    tl = A.sub(96, 32, 32, 32); tl[:] = hexrgb(0xffa8c0)
    tl[::8, :] = hexrgb(0xe8e0e4); tl[:, ::8] = hexrgb(0xe8e0e4); crust(tl[2:6, 10:14], 0xb8b0a6, 0.1, seed=3); R['tile'] = A.rect(96, 32, 32, 32)
    gr = A.sub(0, 64, 128, 64); crust(gr, 0xb4a294, 0.12, seed=51, block=2,
                                      speck=[(0xf4c4cc, 0.08), (0xbfe8d8, 0.07), (0xfbe6a6, 0.07), (0x8a827a, 0.08), (0xfdfaf4, 0.04)])
    grime(gr, 0xa89480, 0.15, seed=52, blob=6); R['gravel'] = A.rect(0, 64, 128, 64)
    return A, R


def heap(Rx, Rz, H, m, rect, peak=(0.0, 0.0), seg=12, rings=(0.3, 0.6, 0.85, 1.0), seed=1, rough=0.08):
    """a lumpy rubble mound (top-down planar UVs into rect), its rim on the ground"""
    rr = random.Random(seed); bm = bmesh.new()
    def P3(a, u):
        e = 1 + 0.12 * math.sin(a * 3 + seed) + 0.07 * math.sin(a * 5 + 2 * seed)
        x, z = math.cos(a) * Rx * u * e, math.sin(a) * Rz * u * e
        y = H * max(0.0, 1 - u * u) ** 0.9 * (1 + rr.uniform(-rough, rough) * 3 if 0 < u < 1 else 1)
        return (x + peak[0] * (1 - u), y if u < 1 else 0.0, z + peak[1] * (1 - u))
    V = [[bm.verts.new(gv(*P3(2 * math.pi * i / seg + rr.uniform(-0.1, 0.1), u))) for i in range(seg)] for u in rings]
    c = bm.verts.new(gv(peak[0], H, peak[1]))
    for i in range(seg): bm.faces.new((c, V[0][(i + 1) % seg], V[0][i]))
    for a, b_ in zip(V, V[1:]):
        for i in range(seg): bm.faces.new((a[i], a[(i + 1) % seg], b_[(i + 1) % seg], b_[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0: f.normal_flip()
    o = lib._obj('heap', bm, m); smooth(o, 40)
    me = o.data; me.uv_layers.new(name='UVMap'); uv = me.uv_layers.active.data
    S = 2 * max(Rx, Rz) * 1.3
    for pg in me.polygons:
        for li in pg.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (rect[0] + (v.x / S + 0.5) * (rect[2] - rect[0]), rect[1] + (v.y / S + 0.5) * (rect[3] - rect[1]))
    return o


def surface(o):
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())
    def f(x, z):
        hit = bvh.ray_cast(gv(x, 20.0, z), Vector((0, 0, -1)))
        return hit[0].z if hit[0] is not None else 0.0
    return f


def scatter_chunks(ground, m, R, n, Rx, Rz, seed=1, big=(0.25, 0.55), keys=None):
    rr = random.Random(seed); out = []
    keys = keys or ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'core', 'c0', 'c2']
    for k in range(n):
        a = rr.uniform(0, 6.28); u = rr.uniform(0.0, 1.0) ** 0.6
        x, z = math.cos(a) * Rx * u, math.sin(a) * Rz * u
        s = rr.uniform(*big) * (1.25 - 0.5 * u)
        size = (s * rr.uniform(0.8, 1.6), s * rr.uniform(0.4, 0.9), s * rr.uniform(0.8, 1.3))
        y = ground(x, z) + size[1] * 0.12
        out.append(chunk(size, (x, y, z), m, R[rr.choice(keys)], seed=seed * 100 + k))
    return out


def slab_with_rebar(size, pos, rot, m, rect, rebar_m, seed=1, bars=3):
    """a broken floor slab: a bevelled box, rebar sticking out of its broken edge and bent over"""
    o = box(size, (0, 0, 0), m, bev=0.02, seg=1, name='slab'); apply_mods(o); uv_fit(o, rect)
    out = [o]; rr = random.Random(seed)
    for k in range(bars):
        x = (k + 0.5) / bars * size[0] - size[0] / 2 + rr.uniform(-0.04, 0.04)
        out.append(bent_rebar((x, rr.uniform(-0.3, 0.3) * size[1], -size[2] / 2 + 0.05), (rr.uniform(-0.2, 0.2), rr.uniform(-0.1, 0.4), -1), rr.uniform(0.35, 0.7), rebar_m, bend=rr.uniform(0.3, 1.0), seed=seed + k))
    xf(out, rot=rot, move=pos)
    return out


def mannequin_hand(m, base, ring_m):
    """a shop mannequin's arm reaching out of the rubble, flashing a peace sign"""
    bx, by, bz = base; O = []
    O.append(rod((bx, by - 0.1, bz), (bx + 0.05, by + 0.42, bz - 0.04), 0.055, m, seg=6, r1=0.045, name='forearm'))
    O.append(cyl(0.05, 0.035, (bx + 0.052, by + 0.44, bz - 0.042), ring_m, axis='y', seg=6, name='wristjoint'))
    palm = box((0.1, 0.12, 0.04), (bx + 0.06, by + 0.53, bz - 0.05), m, taper=(1.0, 0.9), name='palm', rot=(0.0, 0.0, -0.1))
    O.append(palm)
    for dx, ang, L in ((-0.025, 0.25, 0.13), (0.015, -0.18, 0.14)):  # the V
        a0 = (bx + 0.06 + dx, by + 0.58, bz - 0.05)
        O.append(rod(a0, (a0[0] - math.sin(ang) * L, a0[1] + math.cos(ang) * L, a0[2] - 0.01), 0.013, m, seg=4, r1=0.011, name='finger'))
    for dx in (0.045,):  # ring + little finger curled down, the thumb across them
        O.append(box((0.04, 0.035, 0.05), (bx + 0.06 + dx - 0.01, by + 0.585, bz - 0.07), m, name='curl'))
    O.append(rod((bx + 0.012, by + 0.5, bz - 0.06), (bx + 0.06, by + 0.565, bz - 0.085), 0.013, m, seg=4, name='thumb'))
    return O


def build_rubble(variant):
    def b():
        A, R = conc_atlas('rb_conc_t')
        cm = mat('rb_concrete', 0xffffff, rough=0.7, tex=A.image())
        rebar = plain('rb_rebar', RUST, rough=0.45, metal=0.5, var=0.18, speck=RUST2, p=0.25, seed=21)
        O = []
        if variant == 'a':
            hp = heap(1.5, 1.2, 0.95, cm, R['gravel'], peak=(0.2, 0.1), seed=3); O.append(hp)
            g = surface(hp)
            O += scatter_chunks(g, cm, R, 24, 1.35, 1.05, seed=5)
            O += slab_with_rebar((1.3, 0.16, 0.8), (-0.45, 0.55, 0.25), (0.35, 0.6, -0.25), cm, R['c1'], rebar, seed=7, bars=3)
            O += slab_with_rebar((0.9, 0.14, 0.6), (0.75, 0.25, -0.5), (-0.2, 2.4, 0.3), cm, R['tile'], rebar, seed=9, bars=2)
            # a broken piece of a big ☺ CORP sign: half the face, one eye, the end of the grin
            S = Atlas('rb_sign_t', 64)
            sg = S.sub(0, 0, 64, 64); sg[:] = hexrgb(0x2a2430); smiley(sg, 40, 34, 30, face=0xffe14d, ink=0x2a2030, ring=0xfff6d0)
            grime(sg, 0xb08a30, 0.12, seed=4, blob=6); crust(S.sub(0, 0, 64, 4), 0xd8d0c4, 0.06, seed=2)
            sm = mat('rb_sign', 0xffffff, rough=0.3, clearcoat=0.7, tex=S.image())
            pl = side_x([(-0.45, -0.4), (0.15, -0.45), (0.42, -0.2), (0.46, 0.18), (0.25, 0.44), (0.0, 0.22), (-0.2, 0.36), (-0.4, 0.05)], 0.07, (0, 0, 0), sm, bev=0.012, seg=1)
            uv_dir(pl, {'-z': (0, 0, 1, 1), '+z': (0, 0, 1, 1)}, (0, 0.94, 1, 1))
            xf([pl], rot=(-0.55, 0.35, 0.18), move=(0.35, 0.95, -0.35)); O.append(pl)
            meta = dict(CMT, col=[3.0, 1.1, 2.4], note='rubble heap with a broken ☺ sign; climbable (treat as a ramp)')
        else:
            hp = heap(1.4, 1.25, 0.8, cm, R['gravel'], peak=(-0.15, 0.0), seed=8); O.append(hp)
            g = surface(hp)
            O += scatter_chunks(g, cm, R, 26, 1.3, 1.1, seed=11)
            O += slab_with_rebar((1.4, 0.18, 0.7), (0.4, 0.5, 0.3), (-0.3, -0.5, 0.35), cm, R['c3'], rebar, seed=13, bars=3)
            O += slab_with_rebar((0.8, 0.12, 0.5), (-0.9, 0.3, -0.3), (0.2, 1.2, -0.3), cm, R['c4'], rebar, seed=15, bars=2)
            for k in range(3): O.append(bent_rebar((rr_ := [-0.3, 0.2, 0.6][k], g([-0.3, 0.2, 0.6][k], -0.2) - 0.05, -0.2), (0.2 * k - 0.2, 1, -0.2), 0.7 + 0.2 * k, rebar, bend=0.6 + 0.3 * k, seed=20 + k))
            # a shop mannequin's arm sticking up out of the heap, flashing a peace sign
            M = Atlas('rb_mq_t', 32)
            crust(M.sub(0, 0, 32, 32), 0xf2c8b0, 0.03, seed=5); M.px[24:, :] = hexrgb(0x8a8492)
            mq = mat('rb_mannequin', 0xffffff, rough=0.25, clearcoat=0.8, tex=M.image())
            hx, hz = -0.25, -0.35
            hand = mannequin_hand(mq, (hx, g(hx, hz), hz), mq)
            for o in hand: uv_fit(o, M.rect(0, 0, 32, 22))
            uv_fit(hand[1], M.rect(0, 24, 32, 8))
            O += hand
            meta = dict(CMT, col=[2.8, 1.0, 2.5], note='rubble heap, a mannequin hand waving out of it; climbable (treat as a ramp)')
        for o in O:
            if o.data.materials and o.data.materials[0] == rebar: uv_tile(o, 0.3)
        return O, meta
    return b


# ================================================================================================ broken shopfront wall
def tri_face(pts, m, name='shard'):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    f = bm.faces.new([bm.verts.new(gv(*p)) for p in pts])
    for lp, uv in zip(f.loops, ((0.1, 0.1), (0.9, 0.2), (0.5, 0.9), (0.2, 0.8))): lp[uvl].uv = uv
    return lib._obj(name, bm, m)


def build_brokenwall():
    W2, HT, T = 3.0, 4.0, 0.3
    A = Atlas('bw_wall_t', 256)
    FH = 171
    fr = A.sub(0, 0, 256, FH)
    X = lambda x: int(round((W2 - x) / (2 * W2) * 256))  # seen from the front (-z): +x is on the left
    Y = lambda y: int(round((1 - y / HT) * FH))
    crust(fr, 0xffc49a, 0.05, seed=3, speck=[(0xe8a880, 0.05), (0xfff0e0, 0.03)])  # peach plaster
    fr[Y(0.55):, :] = hexrgb(0x9ff0d4)  # the stall riser: mint tiles
    rz = fr[Y(0.55):, :]; rz[::6, :] = hexrgb(0xe8f4ee); rz[:, ::6] = hexrgb(0xe8f4ee); rz[0:2, :] = hexrgb(0x5fb8a0)
    r = random.Random(5)
    for _ in range(6):  # plaster fallen off, pastel brick behind
        x, y, w, h = r.randint(0, 236), r.randint(10, 100), r.randint(10, 22), r.randint(6, 14)
        sub = fr[y:y + h, x:x + w]; sub[:] = hexrgb(0xe88a8a); sub[::4, :] = hexrgb(0xf4d8cc)
        for k in range(0, h, 4): sub[k:k + 4, (k * 3) % 8::8] = hexrgb(0xf4d8cc)
    for _ in range(9):  # cracks down from the broken top
        x, y = r.uniform(10, 246), r.uniform(0, 30)
        for k in range(5):
            nx, ny = x + r.uniform(-6, 6), y + r.uniform(4, 10); px_line(fr, x, y, nx, ny, 0x6a4a4a, 1); x, y = nx, ny
    # the blast: a bleached flash round a person-shaped shadow (mid-stride, coffee in one hand, briefcase in the other)
    cx, cy = X(0.38), Y(1.0)
    yy, xx = np.mgrid[0:FH, 0:256]; d = np.hypot((xx - cx) / 1.3, yy - cy)
    flash = np.clip(1 - d / 70, 0, 1)[:, :, None]; soot = (np.clip((d - 50) / 40, 0, 1) * np.clip(1 - (d - 50) / 90, 0, 1))[:, :, None]
    fr[:] = fr * (1 - flash * 0.45) + hexrgb(0xfff8ec) * flash * 0.45
    fr[:] = fr * (1 - soot * 0.55) + hexrgb(0x3a2a30) * soot * 0.55
    sh = np.zeros((FH, 256, 3), np.float32)
    hx, top = X(0.38), Y(1.78)
    px_disc(sh, hx, top + 5, 5, 0xffffff)  # head
    px_line(sh, hx, top + 10, hx - 1, top + 38, 0xffffff, 10)  # torso
    px_line(sh, hx - 1, top + 36, hx - 9, top + 58, 0xffffff, 5); px_line(sh, hx - 9, top + 58, hx - 12, top + 72, 0xffffff, 4)  # back leg
    px_line(sh, hx + 1, top + 36, hx + 8, top + 56, 0xffffff, 5); px_line(sh, hx + 8, top + 56, hx + 13, top + 70, 0xffffff, 4)  # front leg
    px_line(sh, hx + 3, top + 14, hx + 12, top + 26, 0xffffff, 3.5); px_line(sh, hx + 12, top + 26, hx + 14, top + 16, 0xffffff, 3)  # arm up: coffee
    sh[top + 9:top + 16, hx + 12:hx + 18] = 1.0
    px_line(sh, hx - 3, top + 14, hx - 10, top + 34, 0xffffff, 3.5); sh[top + 34:top + 44, hx - 17:hx - 4] = 1.0  # briefcase
    m_ = sh[:, :, 0] > 0.5
    fr[m_] = hexrgb(0x2a1c2e) * (0.9 + 0.1 * np.random.default_rng(3).random((int(m_.sum()), 1)))
    write(fr, 'ted from', X(0.38) - 23, Y(2.25), 1, 0x2a2030, wob=1, seed=8); write(fr, 'accounts', X(0.38) - 23, Y(2.25) + 9, 1, 0x2a2030, wob=1, seed=9)  # someone wrote his name under it
    bk = A.sub(0, 171, 128, 64); crust(bk, 0xd8d0c8, 0.06, seed=7, speck=0xb8b0a8, p=0.06); grime(bk, 0x9a8a80, 0.15, seed=4, blob=8)
    ed = A.sub(128, 171, 64, 32); crust(ed, 0xc8bcb0, 0.1, seed=8, speck=[(0xe88a8a, 0.2), (0x8a827a, 0.1)])
    fs = A.sub(128, 203, 128, 24); crust(fs, 0x4fd8ff, 0.05, seed=9); fs[0:2, :] = fs[-2:, :] = hexrgb(0xffffff)
    text_px(fs, 'ARGAIN BIN', 6, 5, 2, 0xffe14d); grime(fs, 0x2a6a8a, 0.12, seed=3, blob=4)
    lt = A.sub(192, 171, 16, 24); crust(lt, 0x4fd8ff, 0.05, seed=10); text_px(lt, 'B', 3, 5, 2, 0xffe14d)
    cc = A.sub(208, 171, 32, 32); crust(cc, 0xffc49a, 0.08, seed=11, speck=[(0x9a948c, 0.08)]); cc[24:, :] = hexrgb(0xb8b0a6)
    aw = A.sub(0, 235, 128, 21); stripes(aw, [0xff4fd8, 0xffffff], 8, horizontal=False); grime(aw, 0x8a6a7a, 0.15, seed=2, blob=4)
    wall = mat('bw_wall', 0xffffff, rough=0.7, tex=A.image())
    RF, RB, RE = A.rect(0, 0, 256, FH), A.rect(0, 171, 128, 64), A.rect(128, 171, 64, 32)
    metal = plain('bw_metal', 0xd8dce4, rough=0.25, metal=0.9, var=0.1, speck=RUST, p=0.08, seed=12)
    rebar = metal
    glass = mat('bw_glass', 0x9fe8ff, rough=0.05, alpha=0.45)
    def poster(px, al):
        h, w = px.shape[:2]; crust(px, 0xffe14d, 0.04, seed=3); al[:] = 1
        text_px(px, 'SALE', 4, 8, 3, 0xff3030); write(px, 'everything', 4, 40, 1, INK); write(px, 'must go', 10, 50, 1, INK)
        text_px(px, '70', 14, 66, 2, 0xff3030); px_disc(px, 44, 72, 6, 0xff3030); text_px(px, '%', 40, 69, 1, 0xffffff)
        y, x = np.mgrid[0:h, 0:w]
        al[(x + (h - y) * 0.9 > w + 18)] = 0  # torn corner
        al[(y > h - 10 + 4 * np.sin(x * 0.7))] = 0  # ragged bottom
        al[(np.abs(x - 50 - (y - 20) * 0.3) < 3) & (y > 20) & (y < 60)] = 0  # a rip
    pm = decal_mat('bw_poster', rgba_image('bw_poster_t', 64, 96, poster), rough=0.5)
    O = []
    outline = [(-3.0, 0.0), (1.0, 0.0), (1.0, 2.3), (2.0, 2.3), (2.0, 0.0), (3.0, 0.0), (3.0, 2.2), (2.7, 2.6), (2.4, 2.45), (2.1, 3.0), (1.75, 2.85),
               (1.45, 3.5), (0.9, 3.38), (0.6, 3.9), (0.1, 3.74), (-0.4, 4.0), (-1.0, 3.84), (-1.5, 4.0), (-2.2, 3.7), (-2.6, 3.95), (-3.0, 3.62)]
    win = [(-2.5, 0.55), (-0.25, 0.55), (-0.25, 2.5), (-2.5, 2.5)]
    w_ = side_x(outline, T, (0, 0, 0), wall, holes=[win], bev=0.02, seg=1, name='wall')
    one_mat([w_]); uv_dir(w_, {'-z': RF, '+z': RB, '+y': RE, '-y': RE, '+x': RE, '-x': RE}, lo=[-3.0, 0.0, -0.15], hi=[3.0, 4.0, 0.15])
    O.append(w_)
    # shop window: an aluminium frame, a mullion, broken glass left in the corners
    fz = -0.06
    for size, pos in (((2.35, 0.08, 0.1), (-1.375, 0.59, fz)), ((2.35, 0.08, 0.1), (-1.375, 2.46, fz)), ((0.08, 1.86, 0.09), (-2.46, 1.525, fz)),
                      ((0.08, 1.86, 0.09), (-0.29, 1.525, fz)), ((0.06, 1.8, 0.08), (-1.4, 1.525, fz))):
        O.append(box(size, pos, metal))
    for pts in (((-2.42, 2.42, fz), (-1.9, 2.42, fz), (-2.42, 1.7, fz)), ((-0.33, 0.63, fz), (-0.33, 1.4, fz), (-0.9, 0.63, fz)),
                ((-1.36, 2.42, fz), (-0.8, 2.42, fz), (-1.1, 2.05, fz)), ((-2.42, 0.63, fz), (-1.85, 0.63, fz), (-2.1, 0.95, fz)),
                ((-1.44, 0.63, fz), (-1.44, 1.2, fz), (-1.7, 0.63, fz))):
        O.append(tri_face(pts, glass))
    # the fascia sign, its last letter hanging by a corner
    fsx = box((4.3, 0.55, 0.12), (-0.85, 3.05, -0.21), wall, bev=0.02, seg=1); uv_dir(fsx, {'-z': A.rect(128, 203, 128, 24)}, A.rect(128, 203, 128, 3)); O.append(fsx)
    nl = box((0.32, 0.44, 0.05), (1.48, 2.6, -0.3), wall, rot=(0.1, 0.0, 0.7)); uv_dir(nl, {'-z': A.rect(192, 171, 16, 24)}, A.rect(192, 171, 16, 3)); O.append(nl)
    O.append(rod((1.28, 2.78, -0.28), (1.36, 2.84, -0.27), 0.012, metal, seg=4))
    # a torn awning hanging off its arms over the window
    for x in (-2.4, -0.4):
        O.append(rod((x, 2.62, -0.15), (x + 0.05, 2.2, -0.95), 0.022, metal, seg=4))
    aw_ = sheet_grid([[(-2.55 + c * 0.55, 2.66 - 0.02 * c, -0.16) for c in range(5)], [(-2.55 + c * 0.55, 2.42 - 0.08 * c, -0.62) for c in range(5)],
                      [(-2.5 + c * 0.5, 2.02 - 0.25 * c * c / 4 - 0.06 * c, -0.98) for c in range(5)]], wall, 'awning')
    uv_remap(aw_, A.rect(0, 235, 128, 21)); face_toward(aw_, (0, 1, -0.4)); O.append(aw_)
    # the SALE poster on the right pier, its corner peeling
    pq = quad((2.5, 1.35, -0.152), 0.62, 0.93, pm, 'z', sx=-1); O.append(pq)
    fl = sheet_grid([[(2.69, 1.12, -0.1545), (2.81, 1.0, -0.1545)], [(2.75, 1.0, -0.2), (2.82, 0.92, -0.24)]], pm, 'peel'); uv_remap(fl, (0.7, 0.0, 0.95, 0.2)); O.append(fl)
    # rebar out of the broken top, rubble at the foot
    for k, (x, y) in enumerate(((-2.6, 3.9), (-1.6, 3.95), (-0.45, 3.95), (0.6, 3.85), (1.5, 3.45), (2.15, 2.95))):
        O.append(bent_rebar((x, y - 0.1, 0.0), (0.1 * (k % 3 - 1), 1, 0.1), 0.45 + 0.1 * (k % 3), rebar, bend=0.5 + 0.2 * (k % 2), seed=30 + k, r=0.014))
    rr = random.Random(9)
    for k in range(9):
        x = rr.uniform(-2.9, 2.9)
        if 1.0 < x < 2.0: x -= 1.2
        sz = rr.uniform(0.18, 0.45)
        O.append(chunk((sz * 1.4, sz * 0.7, sz), (x, sz * 0.25, rr.uniform(-0.6, -0.25)), wall, A.rect(208, 171, 32, 32), seed=60 + k))
    for o in O:
        if o.data.materials and o.data.materials[0] == metal: uv_tile(o, 0.3)
    L = [side_x(outline, T, (0, 0, 0), wall, holes=[win], name='wl')]
    one_mat(L); uv_dir(L[0], {'-z': RF, '+z': RB, '+y': RE, '-y': RE, '+x': RE, '-x': RE}, lo=[-3.0, 0.0, -0.15], hi=[3.0, 4.0, 0.15])
    fl_ = box((4.3, 0.55, 0.12), (-0.85, 3.05, -0.21), wall); uv_dir(fl_, {'-z': A.rect(128, 203, 128, 24)}, A.rect(128, 203, 128, 3)); L.append(fl_)
    for size, pos in (((2.35, 0.08, 0.1), (-1.375, 0.59, fz)), ((2.35, 0.08, 0.1), (-1.375, 2.46, fz)), ((0.06, 1.8, 0.08), (-1.4, 1.525, fz))):
        L.append(uv_tile(box(size, pos, metal), 0.3))
    L.append(quad((2.5, 1.35, -0.152), 0.62, 0.93, pm, 'z', sx=-1))
    return O, dict(CMT, _lod=L, col=[6.0, 4.0, 0.3], note='ruin wall section, front = -z; the window and door are open (collide as 3 boxes: left pier+riser, pier, right pier)')


# ================================================================================================ the broken street clock
def paint_dial(px, seed, hit=(0.72, 0.3), hole=True):
    """a ☺ CORP public clock face: ticks, 12/3/6/9, the logo, cracked from an impact, a chunk of glass gone"""
    h, w = px.shape[:2]; c = w / 2; R = w / 2 - 1
    px[:] = hexrgb(0x2a2430)
    px_disc(px, c, c, R, 0x4fd8ff); px_disc(px, c, c, R - 4, 0xfdfdf8)
    for k in range(60):
        a = 2 * math.pi * k / 60; L = 9 if k % 5 == 0 else 4; t = 2.6 if k % 5 == 0 else 1.0
        r0 = R - 7
        px_line(px, c + math.sin(a) * r0, c - math.cos(a) * r0, c + math.sin(a) * (r0 - L), c - math.cos(a) * (r0 - L), 0x1a2a5a, t)
    for txt, a in (('12', 0), ('3', 90), ('6', 180), ('9', 270)):
        rr_ = R - 26; x = c + math.sin(math.radians(a)) * rr_; y = c - math.cos(math.radians(a)) * rr_
        text_px(px, txt, int(x - (len(txt) * 6 - 1)), int(y - 7), 2, 0x1a2a5a)
    smiley(px, c, c - 21, 5, face=0xffe14d, ink=0x1a2a5a); text_px(px, 'CORP', int(c - 11), int(c - 14), 1, 0x1a2a5a)
    text_px(px, 'PUBLIC TIME', int(c - 32), int(c + 22), 1, 0x4fa8d8)
    rnd = random.Random(seed); hx, hy = hit[0] * w, hit[1] * h  # the cracks, radiating out of the impact
    for k in range(9):
        a = rnd.uniform(0, 6.28); x, y = hx, hy
        for j in range(5):
            a += rnd.uniform(-0.4, 0.4); L = rnd.uniform(6, 16); nx, ny = x + math.cos(a) * L, y + math.sin(a) * L
            px_line(px, x, y, nx, ny, 0x8a9ab0, 1); px_line(px, x + 0.6, y + 0.6, nx + 0.6, ny + 0.6, 0xffffff, 0.6); x, y = nx, ny
    for rr_ in (7, 13):
        for k in range(14):
            a0 = rnd.uniform(0, 6.28); px_line(px, hx + math.cos(a0) * rr_, hy + math.sin(a0) * rr_, hx + math.cos(a0 + 0.35) * rr_, hy + math.sin(a0 + 0.35) * rr_, 0x8a9ab0, 1)
    if hole:
        pts = [(hx + math.cos(a) * (5 + 2 * math.sin(a * 3)), hy + math.sin(a) * (5 + 2 * math.sin(a * 3))) for a in np.linspace(0, 6.28, 12)]
        for x, y in pts: px_line(px, hx, hy, x, y, 0x2a2430, 3)
    grime(px, 0xd8d0c0, 0.04, seed=seed, blob=3)


def build_brokenclock():
    A = Atlas('ck_t', 256)
    paint_dial(A.sub(0, 0, 128, 128), 3)
    paint_dial(A.sub(128, 0, 128, 128), 5, hit=(0.3, 0.62), hole=False)
    pl = A.sub(0, 128, 64, 64); crust(pl, 0xf6f8fa, 0.04, seed=6, speck=[(0xb8c0c8, 0.03), (RUST, 0.01)])
    pl[:, 26:38] = hexrgb(0x4fd8ff); pl[:, 25] = pl[:, 38] = hexrgb(0x2a8ab8)  # the ☺ CORP stripe up the pole
    for y in range(40, 64, 3): pl[y, :] = pl[y, :] * 0.85 + hexrgb(0x8a8078) * 0.15  # road splash
    pq = A.sub(64, 128, 96, 32); crust(pq, 0x2a8ab8, 0.04, seed=7); pq[1, :] = pq[-2, :] = hexrgb(0xd8e8f0)
    smiley(pq, 9, 15, 6, face=0xffe14d, ink=INK); text_px(pq, 'CORP PUBLIC TIME', 19, 5, 1, 0xffffff)
    write(pq, 'please be punctual', 19, 17, 1, 0xd8f0ff)
    bs = A.sub(160, 128, 96, 64); crust(bs, 0xe8ecf0, 0.06, seed=8, speck=[(0xb8c0c8, 0.06)]); grime(bs, 0xa8a098, 0.15, seed=9, blob=6)
    m = text_mask(64, 96, 'times up', 1, 10, 2, lower=True, wob=1, seed=2); m |= text_mask(64, 96, 'off duty', 1, 38, 2, lower=True, wob=1, seed=3)
    sp_p = np.zeros((64, 96, 3), np.float32); sp_a = np.zeros((64, 96), np.float32); spray(sp_p, sp_a, m, HOT, seed=4, drips=5)
    bs[sp_a > 0] = sp_p[sp_a > 0]
    fn = A.sub(0, 192, 64, 64); fn[:] = hexrgb(0xffe14d); smiley(fn, 32, 32, 30, face=0xffe14d, ink=0x1a1a2a, ring=0x1a1a2a)
    px_line(fn, 8, 8, 30, 26, 0x6a5a20, 1.5)  # a crack across the smile
    hd = A.sub(64, 160, 96, 32); crust(hd, 0xf6f8fa, 0.04, seed=10); hd[:, 40:56] = hexrgb(0x4fd8ff)
    en = mat('ck_enamel', 0xffffff, rough=0.25, clearcoat=0.8, tex=A.image())
    PL, PQ, BS, FN, HD = A.rect(0, 128, 64, 64), A.rect(64, 128, 96, 32), A.rect(160, 128, 96, 64), A.rect(0, 192, 64, 64), A.rect(64, 160, 96, 32)
    chrome = plain('ck_chrome', 0xe8ecf4, rough=0.12, metal=1.0, var=0.04, seed=11)
    navy = plain('ck_hands', 0x1a2a5a, rough=0.3, var=0.05, seed=12)
    L_ = Atlas('ck_lcd_t', 64, 16)
    L_.px[:] = hexrgb(0x1a0608)
    seg7(L_.px, '17', 4, 3, 8, 10, 2, 0xff3030, gap=3, ghost=0x3a1010); seg7(L_.px, '29', 34, 3, 8, 10, 2, 0xff3030, gap=3, ghost=0x3a1010)
    L_.px[5:7, 28:30] = hexrgb(0xff3030); L_.px[9:11, 28:30] = hexrgb(0xff3030)
    lcd = mat('ck_lcd', 0xffffff, rough=0.2, emit=0xffffff, strength=1.6, tex=L_.image(), emit_tex=True)
    O = []
    # the plinth
    O.append(uv_dir(box((0.62, 0.5, 0.62), (0, 0.25, 0), en, bev=0.02, seg=1), {}, BS))
    O.append(fit(box((0.72, 0.07, 0.72), (0, 0.535, 0), chrome, bev=0.012, seg=1), PL))
    pq_ = quad((0, 0.3, -0.3125), 0.5, 0.17, en, 'z', sx=-1); uv_remap(pq_, PQ); O.append(pq_)
    # the pole: fluted base, bent by something big going past
    bend = lambda p: (p[0] + 0.28 * max(0.0, (p[1] - 0.6) / 3.5) ** 2, p[1], p[2])
    pole = lathe([(0.17, 0.57), (0.12, 0.72), (0.095, 0.86), (0.088, 1.6), (0.084, 2.4), (0.08, 3.1), (0.076, 3.8), (0.076, 4.05)], (0, 0, 0), en, seg=10, axis='y', name='pole', cap=False)
    uv_cyl(pole, axis='y', a0=0.57, a1=4.05)
    for l in pole.data.uv_layers.active.data: l.uv = (PL[0] + (l.uv[1] + 0.5) * (PL[2] - PL[0]), PL[1] + l.uv[0] * (PL[3] - PL[1]))
    deform(pole, bend); O.append(pole)
    for y in (0.86, 2.4):
        c = lathe([(0.1, -0.03), (0.12, 0.0), (0.1, 0.03)], (0, y, 0), chrome, seg=10, axis='y', name='collar', cap=False); deform(c, bend); O.append(c)
    top = bend((0, 4.05, 0))
    # the LCD under the head, still showing the moment it all stopped
    lb = box((0.46, 0.15, 0.08), (top[0] - 0.01, 3.72, -0.07), en, bev=0.01, seg=1); uv_fit(lb, HD); O.append(lb)
    lq = quad((top[0] - 0.01, 3.72, -0.111), 0.4, 0.1, lcd, 'z', sx=-1); O.append(lq)
    # the head: a two-faced drum hanging askew off its yoke, chrome bezels, the hands stopped at 17:29
    H = []
    cy = 4.56
    dr = cyl(0.44, 0.2, (0, cy, 0), en, axis='z', seg=16, name='drum')
    uv_dir(dr, {'-z': A.rect(0, 0, 128, 128), '+z': A.rect(128, 0, 128, 128)}, HD, lo=[-0.44, cy - 0.44, -0.1], hi=[0.44, cy + 0.44, 0.1])
    H.append(dr)
    for z in (-0.1, 0.1): H.append(torus(0.44, 0.03, (0, cy, z), chrome, axis='z', seg=16, sides=3, name='bezel'))
    H.append(fit(box((0.18, 0.12, 0.16), (0, cy - 0.47, 0), en, bev=0.015, seg=1), HD))
    def hands(z, sgn):
        out = []
        for th, L, w in ((2 * math.pi * 29 / 60, 0.36, 0.028), (2 * math.pi * (5 + 29 / 60) / 12, 0.24, 0.04)):
            hb = box((w, L, 0.012), (0, cy + L / 2 - 0.05, z), navy, name='hand')
            xf([hb], rot=(0, 0, sgn * th), pivot=(0, cy, z)); out.append(hb)
            z += 0.012 * (-1 if sgn > 0 else 1)
        out.append(cyl(0.03, 0.03, (0, cy, z), chrome, axis='z', seg=8, name='pin'))
        return out
    H += hands(-0.112, 1) + hands(0.112, -1)
    # the ☺ finial on top, knocked crooked
    st = rod((0, cy + 0.47, 0), (0.03, cy + 0.66, 0), 0.025, chrome, seg=6); H.append(st)
    fd = cyl(0.17, 0.05, (0.05, cy + 0.82, 0), en, axis='z', seg=12, name='finial'); uv_dir(fd, {'-z': FN, '+z': FN}, A.rect(0, 192, 64, 4), lo=[-0.12, cy + 0.65, -0.025], hi=[0.22, cy + 0.99, 0.025])
    xf([fd], rot=(0, 0.2, -0.35), pivot=(0.03, cy + 0.66, 0)); H.append(fd)
    xf(H, rot=(0.04, 0, -0.16), move=(top[0], 0, 0), pivot=(0, 4.07, 0))
    O += H
    O.append(fit(box((0.14, 0.1, 0.14), (top[0], 4.07, 0), chrome, bev=0.01, seg=1), PL))
    # a cable torn out of the head, dangling
    O.append(sweep([(top[0] + 0.05, 4.1, 0.05), (top[0] + 0.14, 3.8, 0.09), (top[0] + 0.12, 3.3, 0.1), (top[0] + 0.05, 2.95, 0.06), (top[0] + 0.08, 2.75, 0.02)], 0.012, navy, seg=4, name='cable'))
    for o in O:
        if o.data.materials and o.data.materials[0] in (chrome, navy) and o.name.startswith(('box', 'rod', 'cable', 'collar', 'bezel', 'pin', 'torus', 'hand', 'cyl')): uv_tile(o, 0.3)
    L = [uv_dir(box((0.62, 0.5, 0.62), (0, 0.25, 0), en), {}, BS)]
    lp = lathe([(0.17, 0.57), (0.09, 0.86), (0.08, 2.4), (0.076, 4.05)], (0, 0, 0), en, seg=6, axis='y', name='lpole', cap=False)
    uv_cyl(lp, axis='y', a0=0.57, a1=4.05)
    for l in lp.data.uv_layers.active.data: l.uv = (PL[0] + (l.uv[1] + 0.5) * (PL[2] - PL[0]), PL[1] + l.uv[0] * (PL[3] - PL[1]))
    deform(lp, bend); L.append(lp)
    L.append(fit(box((0.46, 0.15, 0.08), (top[0] - 0.01, 3.72, -0.07), en), HD))
    ld = cyl(0.46, 0.22, (0, cy, 0), en, axis='z', seg=10, name='ldrum')
    uv_dir(ld, {'-z': A.rect(0, 0, 128, 128), '+z': A.rect(128, 0, 128, 128)}, HD, lo=[-0.46, cy - 0.46, -0.11], hi=[0.46, cy + 0.46, 0.11])
    lf = cyl(0.17, 0.05, (0.05, cy + 0.82, 0), en, axis='z', seg=8); uv_dir(lf, {'-z': FN, '+z': FN}, A.rect(0, 192, 64, 4), lo=[-0.12, cy + 0.65, -0.025], hi=[0.22, cy + 0.99, 0.025])
    xf([lf], rot=(0, 0.2, -0.35), pivot=(0.03, cy + 0.66, 0))
    lst = rod((0, cy + 0.4, 0), (0.03, cy + 0.68, 0), 0.03, chrome, seg=4); uv_tile(lst, 0.3)
    lyk = uv_tile(box((0.18, 0.2, 0.16), (0, cy - 0.5, 0), chrome), 0.3)
    xf([ld, lf, lst, lyk], rot=(0.04, 0, -0.16), move=(top[0], 0, 0), pivot=(0, 4.07, 0)); L += [ld, lf, lst, lyk]
    L.append(uv_tile(box((0.14, 0.12, 0.14), (top[0], 4.07, 0), chrome), 0.3))
    return O, dict(CMT, _lod=L, col=[0.72, 5.0, 0.72], lights=[[0.2, 3.72, -0.15, 0xff3030]], glow=['ck_lcd'], time='17:29',
                   note='☺ CORP public clock, stopped at 17:29 (the end of the world); face = -z, the back face shows the same time')


# ================================================================================================ the Unpaid tent
def build_raidertent():
    # cubicle partitions: grey-blue office fabric in a silver frame, memos pinned on, a motivational cat
    P = Atlas('rt_panel_t', 128)
    fb = P.sub(0, 0, 64, 80); crust(fb, 0x7f9ec4, 0.06, seed=3); fb[::2, :] *= 0.95; fb[:, ::3] *= 0.97
    fb[0:3, :] = fb[-3:, :] = hexrgb(0xd8dce4); fb[:, 0:3] = fb[:, -3:] = hexrgb(0xd8dce4)
    r = random.Random(4)
    for k in range(5):
        x, y = r.randint(6, 46), r.randint(8, 60); c = r.choice([0xfff3a0, 0xffd0e0, 0xfbf8f0])
        fb[y:y + 10, x:x + 10] = hexrgb(c); fb[y + 3:y + 9:2, x + 2:x + 8] = hexrgb(0x8a8a9a); fb[y, x + 4:x + 6] = hexrgb(0xff3030)
    ps = P.sub(64, 0, 64, 80); crust(ps, 0x7f9ec4, 0.06, seed=5); ps[0:3, :] = ps[-3:, :] = hexrgb(0xd8dce4); ps[:, 0:3] = ps[:, -3:] = hexrgb(0xd8dce4)
    pp = ps[10:50, 12:52]; pp[:] = hexrgb(0x2a3a6a); px_disc(pp, 20, 15, 9, 0xffb43a); px_disc(pp, 16, 13, 1.5, INK); px_disc(pp, 24, 13, 1.5, INK)
    pp[2:6, 16:24] = hexrgb(0x9a7a5a); px_line(pp, 12, 8, 14, 3, 0xffb43a, 2); px_line(pp, 28, 8, 26, 3, 0xffb43a, 2)  # the cat, hanging on
    write(ps, 'hang in', 14, 52, 1, 0xffffff); write(ps, 'there', 18, 61, 1, 0xffffff)
    ed = P.sub(0, 80, 32, 16); crust(ed, 0xd8dce4, 0.04, seed=6)
    pn = mat('rt_panel', 0xffffff, rough=0.75, tex=P.image())
    FAB, POS, EDG = P.rect(0, 0, 64, 80), P.rect(64, 0, 64, 80), P.rect(0, 80, 32, 16)
    # the tarp: an old ☺ CORP recruitment banner, grommets, a tape patch, a burnt hole
    def tarp(px, al):
        h, w = px.shape[:2]; crust(px, 0xf4f8fa, 0.05, seed=7); al[:] = 1
        px[0:20, :] = hexrgb(0x4fd8ff); px[h - 14:, :] = hexrgb(0x4fd8ff)
        smiley(px, 22, 62, 16, face=0xffe14d, ink=INK)
        text_px(px, "WE'RE", 46, 42, 2, 0x1a2a5a); text_px(px, 'HIRING!', 46, 62, 2, 0xff4fd8)
        text_px(px, 'CORP CAREERS', 30, 90, 1, 0x2a8ab8)
        for x in range(4, w, 16): px_disc(px, x, 4, 2, 0xc8ccd4, r_in=0.8); px_disc(px, x, h - 5, 2, 0xc8ccd4, r_in=0.8)
        grime(px, 0xa8a090, 0.12, seed=8, blob=8)
        px[98:110, 70:110] = hexrgb(0xb8bcc4); px[98:110:3, 70:110] *= 0.9  # duct-tape patch
        y, x = np.mgrid[0:h, 0:w]; d = np.hypot(x - 104, y - 30)
        px[(d < 11)] = hexrgb(0x2a1a14); al[d < 8] = 0  # burnt through
        spray(px, al, text_mask(h, w, 'NOT', 46, 24, 2), 0xff3030, seed=3, drips=3)  # "WE'RE NOT HIRING!"
    tp = decal_mat('rt_tarp', rgba_image('rt_tarp_t', 128, 128, tarp), rough=0.5, cc=0.2)
    # bits: the cardboard sign, crate wood, cinder block, mattress ticking, rope, cone, badges
    B = Atlas('rt_bits_t', 128)
    sg = B.sub(0, 0, 128, 48); crust(sg, 0xc8995a, 0.06, seed=9); grime(sg, 0x8a6a3a, 0.1, seed=3, blob=4)
    write(sg, 'NO VACANCIES.', 4, 8, 1, 0x1a1a20, wob=1, seed=2, bold=True); write(sg, 'NO SALARIES.', 30, 22, 1, 0xc0182a, wob=1, seed=3, bold=True)
    write(sg, 'ask inside', 60, 36, 1, 0x1a1a20, wob=1, seed=4)
    wood(B.sub(0, 48, 64, 32), 0xd8b070, 0x9a6a30, seed=9, rings=4)
    crust(B.sub(64, 48, 32, 32), 0xb8b4ac, 0.1, seed=10, speck=0x8a867e, p=0.15)
    mt = B.sub(96, 48, 32, 32); stripes(mt, [0xf4eee4, 0xf4eee4, 0x5f8ad8], 2, horizontal=False); grime(mt, 0xc8a878, 0.2, seed=5, blob=4)
    crust(B.sub(0, 80, 32, 16), 0xe8d8a8, 0.1, seed=11)  # rope
    cn = B.sub(32, 80, 32, 32); crust(cn, 0xff6a1a, 0.05, seed=12); cn[:, 14:20] = hexrgb(0xf8f8f2); cn[:, 22:25] = hexrgb(0xf8f8f2)
    bd = B.sub(64, 80, 24, 36); paint_badge(bd, 'INTERN')
    st = B.sub(88, 80, 8, 48); stripes(st, [HOT, YEL], 3)
    kr = B.sub(96, 112, 32, 16); crust(kr, 0xff3a4a, 0.05, seed=14); kr[2:4, :] = hexrgb(0xffb0b8)
    bits = mat('rt_bits', 0xffffff, rough=0.6, clearcoat=0.2, tex=B.image())
    SG, WD, CB, MT, RP, CN, BD, ST = (B.rect(0, 0, 128, 48), B.rect(0, 48, 64, 32), B.rect(64, 48, 32, 32), B.rect(96, 48, 32, 32), B.rect(0, 80, 32, 16),
                                      B.rect(32, 80, 32, 32), B.rect(64, 80, 24, 36), B.rect(88, 80, 8, 48))
    chrome = plain('rt_chrome', 0xdde2ea, rough=0.15, metal=1.0, var=0.06, seed=13)
    F = Atlas('rt_fire_t', 8, 32)
    for y in range(32):
        t = y / 31; F.px[y] = hexrgb(0xff3a10) * (1 - t) + hexrgb(0xfff0a0) * t
    fire = mat('rt_fire', 0xffffff, rough=0.8, emit=0xffffff, strength=2.5, tex=F.image(), emit_tex=True)
    O = []
    def panel(cx, cz, ry, w=1.2, h=1.5, tex=FAB, lean=0.0):
        p_ = box((w, h, 0.06), (0, h / 2 + 0.06, 0), pn, bev=0.012, seg=1, name='panel')
        uv_dir(p_, {'-z': tex, '+z': FAB}, EDG)
        ft = fit(box((0.08, 0.06, 0.5), (-w / 2 + 0.22, 0.03, 0), chrome), EDG); ft2 = fit(box((0.08, 0.06, 0.5), (w / 2 - 0.22, 0.03, 0), chrome), EDG)
        xf([p_, ft, ft2], rot=(lean, ry, 0), move=(cx, 0, cz))
        return [p_, ft, ft2]
    O += panel(-0.6, 0.95, 0.0) + panel(0.6, 0.95, 0.0, tex=POS)
    O += panel(-1.22, 0.32, math.pi / 2) + panel(1.24, 0.3, -math.pi / 2 + 0.12, lean=0.05)
    # the tarp over it all, held up at the front by two broom handles, drooping down the sides
    rows, cols = 5, 7; pts = []
    for i in range(rows):
        t = i / (rows - 1); row = []
        for j in range(cols):
            u = j / (cols - 1) * 2 - 1; x = u * 1.6; z = 1.08 - t * 2.4
            y = 1.62 + 0.2 * t - 0.14 * math.sin(math.pi * t) * (1 - u * u)
            if abs(u) > 0.7: y -= (abs(u) - 0.7) / 0.3 * 0.6
            y += 0.03 * math.sin(3.1 * x + 5 * t)
            row.append((x + 0.04 * math.sin(4 * t) * abs(u), y, z))
        pts.append(row)
    tr = sheet_grid(pts, tp, 'tarp'); face_toward(tr, (0, 1, 0)); O.append(tr)
    for x in (-1.07, 1.07):
        O.append(rod((x, 0.0, -1.2), (x, 1.83, -1.2), 0.022, chrome, seg=5, name='pole'))
        O.append(fit(sweep(bend_path((x, 1.8, -1.2), (x * 1.5, 0.2, -1.9), 0.06, 4), 0.008, bits, seg=3, name='rope'), RP))
        O.append(fit(box((0.39, 0.19, 0.19), (x * 1.5, 0.095, -1.92), bits, rot=(0, 0.3 * x, 0)), CB))
    # the sign, hung off the front edge between the poles
    O.append(fit(sweep([(-0.5, 1.81, -1.2), (-0.45, 1.6, -1.22), (0.45, 1.6, -1.22), (0.5, 1.81, -1.2)], 0.007, bits, seg=3, name='string'), RP))
    sgn = box((1.15, 0.43, 0.02), (0, 1.38, -1.23), bits, rot=(0.06, 0, -0.04)); uv_dir(sgn, {'-z': SG}, B.rect(0, 0, 128, 2)); O.append(sgn)
    # lanyards strung across the front like bunting
    bun = bend_path((-1.07, 1.72, -1.21), (1.07, 1.72, -1.21), 0.12, 6)
    O.append(fit(sweep(bun, 0.006, bits, seg=3, name='bunting'), ST))
    for k in (1, 2, 4, 5):
        x, y, z = bun[k]
        if abs(x) < 0.55: continue
        q = quad((x, y - 0.06, z - 0.004), 0.06, 0.09, bits, 'z', sx=-1); uv_remap(q, BD); O.append(q)
    # out front: a cone, an upturned crate with a kettle over a tiny fire; inside: a mattress
    cone = lathe([(0.14, 0.03), (0.1, 0.25), (0.06, 0.48), (0.0, 0.7)], (0, 0, 0), bits, seg=8, axis='y', cap=False, name='cone')
    uv_cyl(cone, axis='y', a0=0.0, a1=0.75)
    for l in cone.data.uv_layers.active.data: l.uv = (CN[0] + l.uv[0] * (CN[2] - CN[0]), CN[1] + (0.5 + 0.4 * l.uv[1]) * (CN[3] - CN[1]))
    cb = fit(box((0.37, 0.03, 0.37), (0, 0.015, 0), bits), B.rect(32, 108, 32, 4))
    xf([cone, cb], rot=(0, 0.4, 0), move=(-1.45, 0, -1.4)); O += [cone, cb]
    O.append(fit(box((0.45, 0.32, 0.35), (0.55, 0.16, -1.55), bits, bev=0.01, seg=1, rot=(0, 0.2, 0)), WD))
    O.append(fit(box((0.39, 0.19, 0.19), (0.55, 0.415, -1.55), bits, rot=(0, -0.3, 0)), CB))
    O.append(flame((0.55, 0.5, -1.55), 0.16, 0.07, fire, (0, 0, 1, 1), n=4, st=2, twist=0.6, seed=4))
    KR = B.rect(96, 112, 32, 16)
    kt = lathe([(0.11, 0.0), (0.12, 0.05), (0.115, 0.12), (0.08, 0.18), (0.03, 0.2), (0.0, 0.215)], (0.55, 0.53, -1.55), bits, seg=8, axis='y', name='kettle')
    dent(kt, (0.66, 0.6, -1.6), 0.07, 0.015); uv_fit(kt, KR); O.append(kt)
    O.append(fit(rod((0.47, 0.58, -1.55), (0.37, 0.7, -1.55), 0.016, bits, seg=4, r1=0.01, name='spout'), KR))
    O.append(sweep([(0.5, 0.72, -1.55), (0.53, 0.81, -1.55), (0.6, 0.81, -1.55), (0.63, 0.72, -1.55)], 0.01, bits, seg=3, name='khandle'))
    uv_fit(O[-1], WD)
    mt_ = pillow((0.9, 0.14, 1.85), (-0.45, 0.07, 0.0), bits, puff=0.15, top=1.3, rot=(0, 0.06, 0.0)); uv_fit(mt_, MT); O.append(mt_)
    for o in O:
        if o.data.materials and o.data.materials[0] == chrome: uv_tile(o, 0.3)
    return O, dict(CMT, col=[3.2, 1.9, 2.6], lights=[[0.55, 0.62, -1.55, 0xff8a2a]], glow=['rt_fire'],
                   sign='NO VACANCIES. NO SALARIES.', note='raider camp tent, open to -z; the cone/crate/kettle stand out front (to z = -2)')


# ================================================================================================ the wrecked ☺ CORP walker tank
def wm_atlases():
    A = Atlas('wm_hull_t', 256)
    def enamel(px, seed, stripe=None):
        crust(px, 0xf6f8fa, 0.03, seed=seed, block=4, speck=[(0xc8d0d8, 0.02)])
        r = random.Random(seed); h, w = px.shape[:2]
        for _ in range(int(w * h / 600)):  # chipped paint down to grey primer, a few candy-rust chips
            x, y, rr = r.uniform(0, w), r.uniform(0, h), r.uniform(0.8, 2.4)
            px_disc(px, x, y, rr, 0x9aa4ae if r.random() < 0.7 else RUST)
        if stripe: px[stripe[0]:stripe[1], :] = hexrgb(0x4fd8ff); px[stripe[1]:stripe[1] + 2, :] = hexrgb(0x2a8ab8)
    sd = A.sub(0, 0, 256, 96); enamel(sd, 3, stripe=(56, 66))
    for x in range(0, 256, 32): sd[:, x] = sd[:, x] * 0.7 + hexrgb(0x5a6470) * 0.3  # panel seams
    sd[30, :] = sd[30, :] * 0.7 + hexrgb(0x5a6470) * 0.3
    for x in range(4, 256, 8): sd[33, x] = sd[54, x] = hexrgb(0x8a949e)  # rivets
    smiley(sd, 80, 18, 10, face=0xffe14d, ink=INK); text_px(sd, 'CORP', 94, 12, 2, 0x1a2a5a)
    text_px(sd, '2ND CUSTOMER SATISFACTION DIV.', 40, 40, 1, 0x1a2a5a); text_px(sd, 'C-7', 196, 8, 3, 0x1a2a5a)
    for k in range(5): smiley(sd, 160 + k * 7, 20, 3, face=0xffe14d, ink=INK)  # kill tally: five little smileys
    def hazard(px):
        h, w = px.shape[:2]; y, x = np.mgrid[0:h, 0:w]; k = ((x + y) // 4) % 2 == 0
        px[k] = hexrgb(0xffe14d); px[~k] = hexrgb(0x1a1a20)
    hazard(sd[70:92, 0:24]); hazard(sd[70:92, 232:256])
    r = np.random.default_rng(4); y, x = np.mgrid[0:96, 0:256]
    for cx, cy, rr in ((140, 70, 22), (30, 30, 16), (230, 60, 18)):  # scorch from the hits
        d = np.hypot(x - cx, (y - cy) * 1.3); t = np.clip(1 - d / rr, 0, 1)[:, :, None] * (0.6 + 0.4 * r.random((96, 256, 1)))
        sd[:] = sd * (1 - t * 0.8) + hexrgb(0x2a2228) * t * 0.8
    for cx, cy in ((150, 64), (138, 76), (146, 80), (36, 24), (226, 56)):  # bullet holes
        px_disc(sd, cx, cy, 2.6, 0xd8dce4); px_disc(sd, cx, cy, 1.6, 0x1a1418)
    dk = A.sub(0, 96, 128, 64); enamel(dk, 5)
    for y_ in range(4, 64, 6):
        for x_ in range(4 + (y_ // 6 % 2) * 3, 128, 6): dk[y_, x_] = hexrgb(0xc8d0d8)  # non-slip dimples
    dk[:, 62:66] = hexrgb(0x4fd8ff)
    pn = A.sub(128, 96, 64, 64); enamel(pn, 6); pn[0:3, :] = hexrgb(0x4fd8ff); pn[-3:, :] = hexrgb(0x4fd8ff)
    for x_ in range(5, 64, 10): pn[6, x_] = pn[57, x_] = hexrgb(0x8a949e)
    dm = A.sub(192, 96, 64, 64); enamel(dm, 7, stripe=(40, 48)); text_px(dm, 'C-7', 22, 14, 1, 0x1a2a5a)
    fc = A.sub(0, 160, 96, 96); fc[:] = hexrgb(0xffe14d)
    smiley(fc, 48, 48, 46, face=0xffe14d, ink=0x1a1a2a, ring=0xd8a820)
    px_disc(fc, 64, 36, 9, 0xffe14d)  # the right eye: shot out, a ragged hole with cracks
    for k in range(9):
        a = k * 0.7; px_line(fc, 64, 36, 64 + math.cos(a) * 13, 36 + math.sin(a) * 13, 0x6a5010, 1)
    for a in np.linspace(0, 6.28, 14): px_line(fc, 64, 36, 64 + math.cos(a) * (5 + 2 * math.sin(a * 3)), 36 + math.sin(a) * (5 + 2 * math.sin(a * 3)), 0x0a0a0e, 3)
    grime(fc, 0xb08a20, 0.1, seed=8, blob=6)
    rim = A.fill(96, 160, 32, 32, 0xe8c030)
    ln = A.sub(128, 160, 32, 32); ln[:] = hexrgb(0x1a2030); px_disc(ln, 16, 16, 12, 0x2a4a6a); px_disc(ln, 12, 12, 3, 0x9ad8ff)
    px_line(ln, 6, 20, 26, 8, 0xc8e0f0, 1)
    vt = A.sub(160, 160, 48, 48); enamel(vt, 9); vt[6:42, 6:42] = hexrgb(0x2a3038); vt[6:42:4, 6:42] = hexrgb(0x8a949e)
    hull = mat('wm_hull', 0xffffff, rough=0.25, clearcoat=0.8, tex=A.image())
    R = dict(side=A.rect(0, 0, 256, 96), deck=A.rect(0, 96, 128, 64), panel=A.rect(128, 96, 64, 64), dome=A.rect(192, 96, 64, 64),
             face=A.rect(0, 160, 96, 96), rim=A.rect(96, 160, 32, 32), lens=A.rect(128, 160, 32, 32), vent=A.rect(160, 160, 48, 48))
    G = Atlas('wm_metal_t', 64)
    crust(G.sub(0, 0, 64, 32), 0x4a5260, 0.08, seed=10, speck=[(0x6a7480, 0.08), (RUST, 0.03)])
    gb = G.sub(0, 32, 64, 32); crust(gb, 0x4a5260, 0.08, seed=11); gb[:, 20:28] = hexrgb(0x4fd8ff); gb[:, 44:48] = hexrgb(0x4fd8ff)
    metal = mat('wm_metal', 0xffffff, rough=0.35, metal=0.7, clearcoat=0.3, tex=G.image())
    chrome = plain('wm_chrome', 0xe4e8f0, rough=0.12, metal=1.0, var=0.05, seed=12)
    glow = mat('wm_glow', 0xff2a2a, rough=0.3, emit=0xff2a2a, strength=3.0)
    D = Atlas('wm_dirt_t', 128)
    crust(D.sub(0, 0, 128, 96), 0xcfae8c, 0.06, seed=13, block=4, speck=[(0xb89474, 0.06), (0xe8d0b0, 0.04), (0x8a8278, 0.02), (0xfbf8f0, 0.01)])
    grime(D.sub(0, 0, 128, 96), 0x9a7050, 0.12, seed=14, blob=8)
    crust(D.sub(0, 96, 64, 32), 0x5a5660, 0.08, seed=15, speck=[(0x8a8690, 0.1), (0xf0e8a0, 0.02)])  # tarmac
    dirt = mat('wm_dirt', 0xffffff, rough=0.85, tex=D.image())
    DR = dict(dirt=D.rect(0, 0, 128, 96), tar=D.rect(0, 96, 64, 32))
    def tags(px, al):
        spray(px[0:48, 0:128], al[0:48, 0:128], text_mask(48, 128, 'UNPAID', 6, 8, 3), HOT, seed=3, drips=6)
        spray(px[48:96, 0:128], al[48:96, 0:128], text_mask(48, 128, 'intern was here', 2, 6, 1, lower=True, wob=1) | text_mask(48, 128, 'no refunds', 10, 26, 2, lower=True, wob=1, seed=3), CYAN, seed=4, drips=4)
        spray(px[0:64, 128:192], al[0:64, 128:192], crossed_smiley(64, 64, 32, 32, 24, 3.5), 0x1a1a1a, seed=5, drips=4)
        m = np.zeros((32, 64), bool)
        for k in range(6): m |= line_mask(32, 64, 4 + k * 6, 4, 4 + k * 6, 26, 2)
        m |= line_mask(32, 64, 1, 22, 38, 8, 2)
        spray(px[64:96, 128:192], al[64:96, 128:192], m, YEL, seed=6, drips=2)
        fl = px[96:160, 0:96]; fa = al[96:160, 0:96]  # the raider flag
        crust(fl, 0xffe14d, 0.06, seed=7); fa[:] = 1
        y, x = np.mgrid[0:64, 0:96]; fa[x > 86 + 6 * np.sin(y * 0.8)] = 0
        sp_ = crossed_smiley(64, 96, 40, 30, 20, 3.5); fl[sp_] = hexrgb(INK)
        fl[text_mask(64, 96, 'unpaid', 22, 54, 1, lower=True)] = hexrgb(0xff3030); fl[:, 0:3] = hexrgb(0xd0a020)
        paint_badge(px[96:132, 96:120], 'INTERN'); al[96:132, 96:120] = 1
        paint_badge(px[96:132, 120:144], 'TEMP'); al[96:132, 120:144] = 1
        px[132:160, 96:104] = hexrgb(HOT); al[132:160, 96:104] = 1
    spray_m = decal_mat('wm_spray', rgba_image('wm_spray_t', 192, 160, tags), rough=0.5, cc=0.3)
    W, H_ = 192, 160
    SR = lambda x, y, w, h: (x / W, 1 - (y + h) / H_, (x + w) / W, 1 - y / H_)
    S = dict(unpaid=SR(0, 0, 128, 48), intern=SR(0, 48, 128, 48), cross=SR(128, 0, 64, 64), tally=SR(128, 64, 64, 32), flag=SR(0, 96, 96, 64),
             b1=SR(96, 96, 24, 36), b2=SR(120, 96, 24, 36), strap=SR(96, 132, 8, 28))
    return dict(hull=hull, metal=metal, chrome=chrome, glow=glow, dirt=dirt, spray=spray_m), R, G, DR, S


def build_warmech():
    M, R, G, DR, S = wm_atlases()
    hull, metal, chrome, glow, dirt, sp = M['hull'], M['metal'], M['chrome'], M['glow'], M['dirt'], M['spray']
    GM, GB = G.rect(0, 0, 64, 32), G.rect(0, 32, 64, 32)
    L = []  # the hull, built level (nose = +x, belly at y 0), then tipped onto its broken front-left leg and sunk
    side_poly = [(-3.0, 0.25), (-2.6, 0.0), (2.3, 0.0), (3.15, 0.55), (3.05, 1.0), (2.3, 1.45), (-2.8, 1.45), (-3.15, 1.1)]
    hb = side_x(side_poly, 3.0, (0, 0, 0), hull, bev=0.12, seg=2, name='hull')
    uv_dir(hb, {'-z': R['side'], '+z': R['side'], '+y': R['deck']}, R['panel']); L.append(hb)
    for z in (-1.56, 1.56):  # armour skirts
        sk = side_x([(-2.7, 0.15), (2.2, 0.15), (2.7, 0.6), (2.5, 1.2), (-2.6, 1.2), (-2.9, 0.8)], 0.12, (0, 0, z), hull, bev=0.03, seg=1, name='skirt')
        uv_dir(sk, {'-z': R['side'], '+z': R['side']}, R['panel'], lo=[-3.15, 0.0, -1.62], hi=[3.15, 1.45, 1.62]); L.append(sk)
    L.append(uv_dir(box((4.2, 0.32, 2.3), (-0.3, 1.6, 0), hull, bev=0.08, seg=1), {'+y': R['deck']}, R['panel']))
    rear = box((1.1, 0.8, 2.2), (-2.75, 1.65, 0), hull, bev=0.08, seg=1); uv_dir(rear, {'+y': R['vent'], '-x': R['vent']}, R['panel']); L.append(rear)
    for z in (-0.6, 0.6):
        L.append(fit(cyl(0.16, 1.1, (-3.05, 2.4, z), metal, axis='y', seg=8, bev=0.02), GM))
        L.append(fit(cyl(0.2, 0.12, (-3.05, 2.95, z), chrome, axis='y', seg=8), GM))
    # hip housings for the four legs
    hips = [(sx * 2.05, 0.62, sz * 1.62) for sx in (1, -1) for sz in (-1, 1)]
    for hx, hy, hz in hips:
        L.append(fit(cyl(0.58, 0.55, (hx, hy, hz + 0.18 * (1 if hz > 0 else -1)), metal, axis='z', seg=12, bev=0.04), GM))
        L.append(fit(cyl(0.3, 0.12, (hx, hy, hz + 0.5 * (1 if hz > 0 else -1)), chrome, axis='z', seg=10), GM))
    # the nose sensor head: three lenses, one still glowing red
    L.append(uv_dir(box((0.7, 0.62, 1.3), (3.05, 1.05, 0), hull, bev=0.06, seg=1, rot=(0, 0, -0.25)), {}, R['panel']))
    for k, z in enumerate((-0.42, 0.0, 0.42)):
        ln = cyl(0.16 if k != 1 else 0.2, 0.14 if k != 1 else 0.18, (3.42, 1.12, z), glow if k == 0 else hull, axis='x', seg=10)
        if k: uv_dir(ln, {'+x': R['lens']}, R['rim'])
        L.append(ln)
    for x in (-1.4, 0.9):
        L.append(uv_dir(cyl(0.34, 0.08, (x, 1.8, 0.75), hull, axis='y', seg=10, bev=0.02), {}, R['panel']))
    # the turret: a ring, a dome with the C-7 band, the giant smiley on its face, the gun out of its grin
    tx = -0.25
    L.append(fit(cyl(1.32, 0.36, (tx, 1.9, 0), metal, axis='y', seg=16, bev=0.03), GM))
    dome = lathe([(1.4, 0.0), (1.42, 0.25), (1.28, 0.62), (0.95, 0.9), (0.45, 1.05), (0.0, 1.08)], (tx, 2.05, 0), hull, seg=16, axis='y', name='dome', cap=False)
    uv_cyl(dome, axis='y', a0=2.05, a1=3.13)
    for l in dome.data.uv_layers.active.data: l.uv = (R['dome'][0] + ((l.uv[1] + 0.5) % 1.0) * (R['dome'][2] - R['dome'][0]), R['dome'][1] + l.uv[0] * (R['dome'][3] - R['dome'][1]))
    L.append(dome)
    face = cyl(1.2, 0.18, (0, 0, 0), hull, axis='z', seg=20, name='face')
    uv_dir(face, {'-z': R['face']}, R['rim'], lo=[-1.2, -1.2, -0.09], hi=[1.2, 1.2, 0.09])
    xf([face], rot=(-0.14, 0, 0.06), move=(tx, 2.72, -1.42)); L.append(face)
    mant = box((0.9, 0.6, 0.7), (tx, 2.3, -1.5), metal, bev=0.05, seg=1, rot=(-0.14, 0, 0)); uv_fit(mant, GM); L.append(mant)
    for zs in (-1, 1):  # turret cheeks with spotlights
        L.append(uv_dir(box((1.6, 0.6, 0.5), (tx - 0.2, 2.4, zs * 1.15), hull, bev=0.06, seg=1, rot=(0, 0.25 * zs, 0)), {}, R['panel']))
    L.append(uv_dir(box((0.36, 0.3, 0.3), (tx + 0.9, 2.85, 1.05), hull, bev=0.03, seg=1), {'-z': R['lens'], '+x': R['lens']}, R['panel']))
    L.append(fit(sweep([(tx - 0.9, 3.0, 0.6), (tx - 1.0, 4.2, 0.65), (tx - 1.5, 4.9, 0.7), (tx - 2.2, 4.95, 0.72)], 0.03, metal, seg=4, name='antenna'), GM))  # bent antenna
    # the raider lookout: an office chair bolted to the turret roof
    L.append(fit(box((0.5, 0.08, 0.5), (tx - 0.4, 3.62, -0.2), metal), GM)); L.append(fit(rod((tx - 0.4, 3.12, -0.2), (tx - 0.4, 3.6, -0.2), 0.04, metal, seg=5), GM))
    L.append(fit(box((0.5, 0.6, 0.08), (tx - 0.62, 3.95, -0.2), metal, rot=(0, 0, 0.3)), GM))
    # the raider flag on the turret, the hatch thrown open
    L.append(rod((tx + 0.5, 3.0, 0.4), (tx + 0.62, 5.6, 0.48), 0.04, metal, seg=5))
    uv_fit(L[-1], GM)
    fp = [[(tx + 0.62 + c * 0.42, 5.5 - r_ * 0.38 - 0.05 * c, 0.48 + 0.12 * math.sin(c * 1.6 + r_)) for c in range(5)] for r_ in range(3)]
    flg = sheet_grid(fp, sp, 'flag'); uv_remap(flg, S['flag']); L.append(flg)
    L.append(uv_dir(cyl(0.4, 0.08, (tx + 0.62, 3.3, -0.05), hull, axis='z', seg=10), {}, R['panel']))  # the hatch, flipped up
    # graffiti on the -z flank and the turret back
    for key, c, w, h in (('unpaid', (0.6, 0.85, -1.63), 2.4, 0.9), ('intern', (-1.6, 0.6, -1.63), 2.0, 0.75), ('tally', (2.2, 0.85, -1.63), 0.9, 0.45)):
        q = quad(c, w, h, sp, 'z', sx=-1); uv_remap(q, S[key]); L.append(q)
    q = quad((-1.6, 0.85, 1.63), 1.1, 1.1, sp, 'z', sx=1); uv_remap(q, S['cross']); L.append(q)
    for o in L:
        if o.data.materials and o.data.materials[0] in (metal, chrome) and not o.data.uv_layers: uv_tile(o, 0.5)
    TILT = dict(rot=(-0.1, 0.0, -0.13), move=(0.0, -0.22, 0.0))
    xf(L, **TILT)
    f = mpt(**TILT)
    O = list(L)
    # legs, splayed out like a squashed bug; the front-left one (+x, -z) snapped at the knee
    for k, (hx, hy, hz) in enumerate(hips):
        sx, sz = (1 if hx > 0 else -1), (1 if hz > 0 else -1)
        h0 = f((hx, hy, hz + 0.45 * sz))
        knee = (h0[0] + sx * 0.9, h0[1] + 1.55, h0[2] + sz * 1.4)
        foot = (h0[0] + sx * 1.9, 0.18, h0[2] + sz * 2.9)
        side = Vector((sx * 0.0, 0, sz)).cross(Vector(knee) - Vector(h0)).normalized() * 0.32
        if k == 0:  # snapped: the thigh ends in a torn stump, wires sparking out of it
            brk = tuple(h0[i] + (knee[i] - h0[i]) * 0.72 for i in range(3))
            O.append(fit(rod(h0, brk, 0.44, metal, seg=6, r1=0.38, bev=0.04), GB))
            st = cyl(0.38, 0.2, brk, metal, axis='y', seg=6); jitter(st, 0.07, seed=4); uv_fit(st, GM); O.append(st)
            for j in range(3):
                O.append(sweep([brk, (brk[0] + 0.2 * j - 0.2, brk[1] + 0.3, brk[2] - 0.15), (brk[0] + 0.35 * j - 0.3, brk[1] + 0.2 - 0.25 * j, brk[2] - 0.4)], 0.025,
                               [chrome, glow, metal][j], seg=4, name='wire'))
            O.append(ball(0.07, (brk[0] - 0.3 + 0.35 * 0, brk[1] + 0.2, brk[2] - 0.4), glow, seg=4, rings=3, name='spark'))
            # the rest of the leg, lying in the dirt in front
            sh0, sh1 = (4.6, 0.25, -3.1), (5.6, 0.3, -4.6)
            O.append(fit(rod(sh0, sh1, 0.3, metal, seg=6, r1=0.25, bev=0.04), GB))
            O.append(fit(rod((sh0[0] - 0.3, 0.3, sh0[2] - 0.2), (sh0[0] + 0.3, 0.3, sh0[2] + 0.2), 0.38, metal, seg=10, bev=0.03), GM))
            pad = cyl(0.62, 0.26, (0, 0, 0), hull, axis='y', seg=8, bev=0.04); uv_fit(pad, R['panel'])
            xf([pad], rot=(1.2, 0.5, 0.2), move=(sh1[0] + 0.25, 0.4, sh1[2] - 0.35)); O.append(pad)
            continue
        O.append(fit(rod(h0, knee, 0.44, metal, seg=6, r1=0.38, bev=0.04), GB))
        O.append(fit(rod(tuple(Vector(knee) - side * 1.3), tuple(Vector(knee) + side * 1.3), 0.5, metal, seg=10, bev=0.03), GM))
        O.append(fit(rod(knee, (foot[0], foot[1] + 0.2, foot[2]), 0.4, hull, seg=6, r1=0.3, bev=0.04), R['panel']))
        O.append(uv_dir(box((0.7, 0.5, 0.7), (knee[0], knee[1] + 0.45, knee[2]), hull, bev=0.05, seg=1, rot=(0.2 * sz, 0.6 * sx * sz, -0.2 * sx)), {}, R['panel']))  # knee armour
        pad = cyl(0.62, 0.26, (foot[0], foot[1], foot[2]), hull, axis='y', seg=8, bev=0.04); uv_fit(pad, R['panel']); O.append(pad)
        for t in (-0.6, 0.0, 0.6):  # toes
            a = math.atan2(sz, sx) + t
            O.append(fit(box((0.7, 0.18, 0.28), (foot[0] + math.cos(a) * 0.75, 0.09, foot[2] + math.sin(a) * 0.75), metal, rot=(0, -a, 0), taper=(1, 0.7)), GM))
        # the hydraulic ram from the hull to the thigh
        p0 = f((hx - sx * 0.6, hy + 0.7, hz + 0.2 * sz)); p1 = tuple(h0[i] + (knee[i] - h0[i]) * 0.55 for i in range(3))
        mid = tuple((p0[i] + p1[i]) / 2 for i in range(3))
        O.append(rod(p0, mid, 0.13, metal, seg=6)); uv_fit(O[-1], GM)
        O.append(rod(mid, p1, 0.075, chrome, seg=6))
    # the gun: out of the grin, then wilted like a dead flower, its muzzle dug into the road
    m0 = f((tx, 2.12, -1.45))
    path = [m0, (m0[0], m0[1] + 0.1, m0[2] - 1.2), (m0[0] + 0.04, m0[1] + 0.16, m0[2] - 2.4), (m0[0] + 0.1, m0[1] + 0.05, m0[2] - 3.4),
            (m0[0] + 0.18, m0[1] - 0.45, m0[2] - 4.2), (m0[0] + 0.26, m0[1] - 1.2, m0[2] - 4.75), (m0[0] + 0.3, m0[1] - 1.9, m0[2] - 5.0), (m0[0] + 0.32, 0.05, m0[2] - 5.1)]
    gun = sweep(path, [0.36, 0.34, 0.46, 0.32, 0.3, 0.3, 0.3, 0.3], metal, seg=10, name='gun')
    uv_tile(gun, 0.6); O.append(gun)
    mz = rod((path[-1][0], 0.05, path[-1][2]), (path[-1][0] + 0.02, -0.55, path[-1][2] - 0.1), 0.38, metal, seg=10); uv_fit(mz, GB); O.append(mz)
    for t in (2, 4):  # the Unpaid hung their tyres and lanyards off it
        tq = ring_mesh([(0.3, -0.08), (0.42, -0.1), (0.44, 0.1), (0.3, 0.08)], 8, metal, GM, name='tyre')
        xf([tq], rot=(1.25, 0, 0.1 * t), move=(path[t][0], path[t][1] - 0.15, path[t][2])); O.append(tq)
    bun = bend_path((path[1][0], path[1][1] + 0.3, path[1][2]), (f((tx + 0.6, 3.0, -0.6))), 0.5, 6)
    O.append(sweep(bun, 0.018, sp, seg=3, name='cord')); uv_fit(O[-1], S['strap'])
    for k in (2, 3, 4):
        x, y, z = bun[k]; q = quad((x, y - 0.16, z), 0.2, 0.3, sp, 'x', sx=-1); uv_remap(q, S['b1' if k % 2 else 'b2']); O.append(q)
    # the ground it sank into: a dirt mound pushed up round the hull, slabs of tarmac broken up round it
    gr = heap(4.9, 3.8, 0.45, dirt, DR['dirt'], peak=(0.6, -0.5), seg=16, rings=(0.3, 0.55, 0.78, 0.92, 1.0), seed=5, rough=0.03); O.append(gr)
    rr = random.Random(8)
    for k in range(12):
        a = rr.uniform(0, 6.28); u = rr.uniform(0.75, 1.15)
        x, z = math.cos(a) * 4.6 * u, math.sin(a) * 3.6 * u
        sz_ = rr.uniform(0.6, 1.3)
        O.append(chunk((sz_, 0.14, sz_ * 0.8), (x, 0.05, z), dirt, DR['tar'], seed=80 + k, rot=(rr.uniform(-0.4, 0.4), rr.uniform(0, 6), rr.uniform(-0.4, 0.4))))
    return O, dict(CMT, col=[7.0, 3.2, 5.0], lights=[[3.3, 0.85, -0.45, 0xff2a2a]], glow=['wm_glow'], landmark=True,
                   note='landmark: a dead ☺ CORP walker (C-7) on the Commute; face = -z; the gun droops to z ~ -6; climbable hull')


BUILDERS = [
    ('filecab', build_filecab), ('cone', build_cone), ('jersey', build_jersey), ('firebarrel', build_firebarrel),
    ('officechair', build_officechair), ('tirestack', build_tirestack), ('skeleton_lanyard', build_skeleton_lanyard), ('paperdrift', build_paperdrift),
    ('rubble_a', build_rubble('a')), ('rubble_b', build_rubble('b')), ('brokenwall', build_brokenwall), ('brokenclock', build_brokenclock),
    ('raidertent', build_raidertent), ('warmech', build_warmech),
]
if __name__ == '__main__':
    run(BUILDERS, {'paperdrift': dict(exposure=-1.9), 'skeleton_lanyard': dict(exposure=-1.2), 'jersey': dict(exposure=-1.1), 'rubble_a': dict(exposure=-1.3), 'rubble_b': dict(exposure=-1.3), 'brokenclock': dict(exposure=-1.2), 'warmech': dict(exposure=-1.0)})
