# Knife skin "Keycard" (w_knife_keycard).
# A ☺ CORP employee ID badge: a CR80 PVC card (85.6 x 54 x 0.76 mm, 3.2 mm corners, a punched lanyard slot) x1.2,
# portrait, clipped through its slot by a chrome lobster claw on a swivel, on a woven lanyard (15 mm strap) that is
# wound round and round into a knife grip, its loop hanging off the butt with the breakaway clasp.
# Held like every knife: the wound strap is the grip (y = 0, the hand over z -0.036 .. +0.08), the card sticks out in
# front where the blade goes (its face = the blade's flat), its long bottom edge ground sharp. muzzle = the front
# bottom corner.
# Made fun (Cruelty Squad flavour): the photo is a smiley, ACCESS: ALL DOORS, a bloody thumbprint, and the back says
# THIS CARD IS PROPERTY OF ☺ CORP. SO ARE YOU.
# run: blender -b --python tools/blender/make_knife_keycard.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj

S = 1.2
CL, CH, CT, CR = 0.0856 * S, 0.054 * S, 0.00076 * S * 1.2, 0.0032 * S  # card length (along z), height, thickness, corner
Z_CB = -0.074            # the card's back edge (badge top, the slot end)
Z_CF = Z_CB - CL         # its front edge
Y_C = -0.004             # card centre height (a little low: edge down, like a blade)
Z_G0, Z_G1 = -0.046, 0.084  # the wound grip


def smiley(px, cx, cy, r, face, ink):
    px_disc(px, cx, cy, r, face)
    px_disc(px, cx, cy, r, ink, r_in=r - 1)
    px_disc(px, cx - r * 0.36, cy - r * 0.25, max(0.8, r * 0.14), ink); px_disc(px, cx + r * 0.36, cy - r * 0.25, max(0.8, r * 0.14), ink)
    px_disc(px, cx, cy, r * 0.62, ink, r_in=r * 0.62 - 1.1, a0=math.radians(100), a1=math.radians(260))


def grime(px, seed, n=40):
    r = np.random.default_rng(seed)
    h, w = px.shape[:2]
    px[:] *= (0.94 + 0.07 * r.random((h, w, 1)))
    for _ in range(n): y, x = r.integers(0, h), r.integers(0, w); px[y, x] *= 0.82


def front_px(W, H):  # portrait badge, row 0 = the slot end
    def draw(px):
        px[:] = hexrgb(0xf4f2ec)
        px[:22] = hexrgb(0xff4fd8)
        smiley(px, 12, 15, 4.5, 0xffe14d, 0x120818)
        text_px(px, 'CORP', 20, 12, 1, 0xffffff)
        px[24:58, 14:50] = hexrgb(0xc8c8d0)  # the photo: a smiley where the face goes
        smiley(px, 32, 39, 11, 0xffe14d, 0x120818)
        px[52:58, 20:44] = hexrgb(0x4a5060)
        text_px(px, 'EMPLOYEE', 8, 62, 1, 0x120818)
        text_px(px, 'NO 00001', 8, 71, 1, 0x7a7a80)
        px[80:88] = hexrgb(0x39ff14)
        text_px(px, 'ALL DOORS', 5, 81, 1, 0x120818)
        r = np.random.default_rng(4)
        x = 8
        while x < W - 8:  # barcode
            wd = int(r.integers(1, 3)); px[91:98, x:x + wd] = hexrgb(0x120818); x += wd + int(r.integers(1, 3))
        for _ in range(7): px_disc(px, 50 + r.normal(0, 3), 70 + r.normal(0, 4), r.uniform(0.6, 1.8), 0x8a0a10)  # a bloody thumbprint
        px_disc(px, 51, 71, 5, 0x9a1018, r_in=3.6); px_disc(px, 51, 71, 2.6, 0x9a1018, r_in=1.6)
        grime(px, 5)
    return draw


def back_px(W, H):
    def draw(px):
        px[:] = hexrgb(0xeae8e2)
        px[16:26] = hexrgb(0x2a2630)  # the magstripe
        for i, ln in enumerate(['THIS CARD', 'IS PROPERTY', 'OF', '', 'SO ARE YOU.']):
            text_px(px, ln, 4, 32 + i * 9, 1, 0x3a3640)
        smiley(px, 23, 54.5, 3.8, 0xffe14d, 0x120818); text_px(px, 'CORP', 29, 51, 1, 0xff4fd8)
        text_px(px, 'IF FOUND', 4, 80, 1, 0x7a7a80); text_px(px, 'KEEP IT', 4, 89, 1, 0x7a7a80)
        grime(px, 6)
    return draw


def strap_px(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xff4fd8)
    px[0] = px[-1] = hexrgb(0xd02aa8)
    for x0 in range(2, w, 32):
        smiley(px, x0 + 4, h / 2, 3.2, 0xffffff, 0xff4fd8)
        text_px(px, 'CORP', x0 + 10, (h - 7) // 2, 1, 0xffffff)
    r = np.random.default_rng(8)
    px[:] *= (0.9 + 0.12 * r.random((h, w, 1)))  # woven


def ribbon(pts, wdirs, width, thick, m, name, nrm=None, tile=0.06):
    """a flat strap along pts (game points), wide along wdirs, thick along nrm (default: across the path), u = length"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    P = [Vector(p) for p in pts]; rows = []; acc = [0.0]
    for i in range(1, len(P)): acc.append(acc[-1] + (P[i] - P[i - 1]).length)
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        w = Vector(wdirs[i]); w = (w - t * t.dot(w)).normalized()
        n = Vector(nrm[i]) if nrm else t.cross(w).normalized()
        rows.append([bm.verts.new(gv(*(p + w * a * width / 2 + n * b * thick / 2))) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    V = [0.0, 1.0, 1.0, 0.0]
    for i in range(len(rows) - 1):
        for k in range(4):
            kk = (k + 1) % 4
            f = bm.faces.new((rows[i][k], rows[i][kk], rows[i + 1][kk], rows[i + 1][k]))
            for lp, (ii, kv) in zip(f.loops, ((i, k), (i, kk), (i + 1, kk), (i + 1, k))):
                lp[uvl].uv = (acc[ii] / tile, V[kv] if k % 2 == 0 else 0.5)
    for r in (rows[0], rows[-1]): bm.faces.new(r)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m); smooth(o, 40)
    return o


def build():
    W, H = 64, 100
    front = mat('kc_front', 0xffffff, rough=0.32, clearcoat=0.6, tex=tex_canvas('kc_front_t', H, W, lambda px: px.__setitem__(slice(None), np.rot90(_portrait(front_px(W, H), W, H), -1))))
    back = mat('kc_back', 0xffffff, rough=0.4, clearcoat=0.4, tex=tex_canvas('kc_back_t', H, W, lambda px: px.__setitem__(slice(None), np.rot90(_portrait(back_px(W, H), W, H), 1))))
    core = mat('kc_core', 0xf8f6f0, rough=0.45)
    sharp = mat('kc_sharp', 0xeaf8ff, rough=0.06, metal=0.6, clearcoat=1.0)
    chrome = mat('kc_chrome', 0xf0f2f6, rough=0.06, metal=1.0)
    strap = mat('kc_strap', 0xffffff, rough=0.8, tex=tex_canvas('kc_strap_t', 64, 12, strap_px))
    clasp = mat('kc_clasp', 0x1a1620, rough=0.4, clearcoat=0.4)

    # ---- the card: a rounded slab with the slot punched through, front / back / edge materials
    def rr(z0, y0, z1, y1, r, n=5):
        pts = []
        for cz, cy, a0 in ((z1 - r, y1 - r, 0), (z0 + r, y1 - r, 90), (z0 + r, y0 + r, 180), (z1 - r, y0 + r, 270)):
            for k in range(n + 1):
                a = math.radians(a0 + 90 * k / n); pts.append((cz + r * math.cos(a), cy + r * math.sin(a)))
        return pts
    z0, z1, y0, y1 = Z_CF, Z_CB, Y_C - CH / 2, Y_C + CH / 2
    slot = rr(Z_CB - 0.0105, Y_C - 0.0082, Z_CB - 0.0062, Y_C + 0.0082, 0.0019, 3)
    card = side(list(reversed(rr(z0, y0, z1, y1, CR))), CT, (0, 0, 0), core, name='card', holes=[slot])
    apply_mods(card)
    for mm in (front, back): card.data.materials.append(mm)
    me = card.data
    if not me.uv_layers: me.uv_layers.new()
    uvl = me.uv_layers.active.data
    for f in me.polygons:
        if abs(f.normal.x) < 0.9: continue
        f.material_index = 1 if f.normal.x < 0 else 2
        for li in f.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            gz, gy = -v.y, v.z
            u = (gz - z0) / CL if f.normal.x < 0 else (z1 - gz) / CL
            uvl[li].uv = (u, (gy - y0) / CH)
    # the sharpened edge: the bottom edge ground into a bevel (the white core shows, and it glints)
    bm = bmesh.new(); rows = []
    for zz in (z0 + 0.0016, z1 - CR - 0.001):
        rows.append([bm.verts.new(gv(*p)) for p in ((-CT / 2, y0 + 0.0004, zz), (CT / 2, y0 + 0.0004, zz), (0.0, y0 - 0.0026, zz))])
    for k in range(3): bm.faces.new((rows[0][k], rows[0][(k + 1) % 3], rows[1][(k + 1) % 3], rows[1][k]))
    for r in rows: bm.faces.new(r)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    edge = _obj('edge', bm, sharp)
    # the front-bottom corner ground to a point to match
    tip = box((CT, 0.006, 0.006), (0, y0 + 0.0005, z0 + 0.0022), sharp, rot=(math.pi / 4, 0, 0), name='tipgrind')
    for o in (edge, tip): uv_box(o, 0.03)

    # ---- the lobster claw through the slot, its swivel, the split ring
    zc = Z_CB - 0.0084
    loop = [(0.0052 * math.sin(2 * math.pi * k / 20) * (0.7 if k > 10 else 1.0), Y_C + 0.0, zc + 0.0115 - 0.0115 * math.cos(2 * math.pi * k / 20) * 1.0) for k in range(20)]
    claw = tube(loop, 0.0012, chrome, seg=8, name='claw', closed=True)
    trig = box((0.0022, 0.0022, 0.004), (0.0052, Y_C, zc + 0.0115), chrome, bev=0.0006, name='claw_trig')
    swiv = cyl(0.0024, 0.007, (0, Y_C, zc + 0.026), chrome, axis='z', seg=12, bev=0.0006, name='swivel')
    ring = lathe([(0.0042, -0.0009), (0.005, 0.0), (0.0042, 0.0009), (0.0034, 0.0), (0.0042, -0.0009)], (0, Y_C * 0.5, zc + 0.033), chrome, seg=18, axis='x', name='splitring', cap=False)
    for o in (claw, trig, swiv, ring): uv_box(o, 0.03)

    # ---- the grip: the lanyard wound round a core, 15 mm strap, each turn overlapping the last
    core_o = cyl(0.0098, Z_G1 - Z_G0, (0, 0, (Z_G0 + Z_G1) / 2), strap, axis='z', seg=14, name='gripcore')
    uv_box(core_o, 0.03)
    turns, n = 8.6, 24
    Rg = 0.0108
    pts, wd, nr = [], [], []
    tot = int(turns * n)
    for i in range(tot + 1):
        th = 2 * math.pi * i / n
        z = Z_G0 + 0.006 + (Z_G1 - Z_G0 - 0.012) * i / tot
        sw = 1 + 0.06 * math.sin(math.pi * i / tot)  # a slight swell in the middle of the fist
        rx, ry = Rg * 0.86 * sw, Rg * 1.08 * sw
        pts.append((rx * math.cos(th), ry * math.sin(th), z)); wd.append((0, 0, 1)); nr.append((math.cos(th), math.sin(th), 0))
    wrap = ribbon(pts, wd, 0.0165, 0.0011, strap, 'wrap', nrm=nr, tile=0.064)
    # the lanyard loop off the butt: down and round under the fist, closed with the breakaway clasp
    lp = []
    for k in range(25):
        t = k / 24; a = math.pi * 2 * t
        lp.append((0.0, -0.004 - 0.034 * (1 - math.cos(a)) * 0.5 - 0.02 * math.sin(math.pi * t) ** 2, Z_G1 - 0.002 + 0.02 * math.sin(a) + 0.02 * t * (1 - t)))
    lanyard = ribbon(lp, [(1, 0, 0)] * len(lp), 0.0145, 0.0011, strap, 'lanyard', tile=0.064)
    bot = lp[12]
    cl = box((0.017, 0.007, 0.016), (bot[0], bot[1], bot[2]), clasp, bev=0.0015, name='clasp')
    tail = box((0.0165, 0.0028, 0.006), (0, -0.001, Z_G1 + 0.0005), strap, bev=0.0008, name='tail')
    uv_box(cl, 0.03); uv_box(tail, 0.03)
    WZ = {'kc_strap': 'a', 'kc_clasp': 'a', 'kc_core': 'b', 'kc_chrome': 'b', 'kc_sharp': 'b', 'kc_front': 'n', 'kc_back': 'n'}
    parts = zone_join([card, edge, tip, claw, trig, swiv, ring, core_o, wrap, lanyard, cl, tail], 'keycard', WZ, default='b')
    meta = {'kind': 'weapon', 'id': 'knife', 'skin': 'knife_keycard', 'paint': ['kc_strap'], 'muzzle': [0, y0 - 0.002, z0 + 0.001], 'hatAt': [[0, 0.0128, 0.028], 0.05]}
    return finish('w_knife_keycard', parts, meta)


def _portrait(draw, W, H):
    px = np.zeros((H, W, 3), dtype=np.float32); draw(px); return px


main(build, 'w_knife_keycard', exposure=-0.4)
