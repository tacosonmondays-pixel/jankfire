# Yeehaw (lever): a Winchester 1892-pattern carbine (20in / 508 mm round barrel, ~955 mm long, case-hardened receiver
# with the loading gate on the right and a saddle ring on the left, full-length tube magazine under the barrel with a
# barrel band, carbine forend + cap band, straight-grip walnut stock, crescent butt plate, buckhorn rear sight + gold
# bead front, exposed hammer, a LARGE loop lever for spin-cocking). Real millimetres x1.24 so the muzzle (-0.71), sight
# line, lever pin and hammer pin land where the game's code model has them (public/js/riflemodels.js).
# Moving parts: 'lever' (origin on its front pivot pin, +rotation.x throws the loop down and forward = open) and
# 'lhammer' (origin on the hammer pin, +rotation.x rocks the spur back = cocked; it rests down, as fired).
# Made fun: cowboy candy. Candy case-hardening with pink in the colours, a pink leather-wrapped loop, a candy-pink
# crescent butt plate, a gold sheriff star in the stock, rhinestones down the receiver, a tiny lasso on the saddle ring.
# run: blender -b --python tools/blender/make_lever.py            (-- --open renders the lever-thrown sheet, no export)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.24 / 1000
BORE_Y, MUZ_Z = 0.02, -0.71
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)   # (mm back from the muzzle, mm above the bore)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
LEVER_PIV = (0, -0.04, -0.02)
HAMMER_PIV = (0, 0.03, 0.09)
LV_D, LV_H = (LEVER_PIV[2] - MUZ_Z) / S, (LEVER_PIV[1] - BORE_Y) / S     # 556 mm, -48 mm
HM_D, HM_H = (HAMMER_PIV[2] - MUZ_Z) / S, (HAMMER_PIV[1] - BORE_Y) / S   # 645 mm, +8 mm
REAR_D = (-0.2 - MUZ_Z) / S          # 411 mm: the buckhorn
SIGHT_H = (0.06 - BORE_Y) / S        # 32 mm: notch bottom + bead top
OPEN = '--open' in sys.argv


def mover(name, pivot, groups):
    """an empty named `name` at pivot (game coords) the game can move, with one joined mesh per wrap zone under it"""
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    e.location = gv(*pivot)
    for objs, z in groups:
        objs = [o for o in objs if o is not None]
        if not objs: continue
        m = part(objs, f'{name}_wz{z}', pivot=pivot)
        m.parent = e; m.location = (0, 0, 0)
    return e


def taper(o, fn):
    """scale a side() slab's width by fn(mm back from the muzzle): a straight wrist swelling into the butt"""
    for v in o.data.vertices:
        d = (-v.co.y - MUZ_Z) / S
        v.co.x *= fn(d)
    return o


def star(cx, cy, cz, r, th, m, tips=None):
    """a five-point sheriff star facing -x (the gun's left side), balls on the tips"""
    bm = bmesh.new()
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cz - math.cos(a) * rr, cy + math.sin(a) * rr))  # (game z, game y)
    vs = [bm.verts.new(gv(cx - th / 2, y, z)) for z, y in pts]
    f = bm.faces.new(vs)
    r_ = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=Vector((th, 0, 0)), verts=[e for e in r_['geom'] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('star'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('star', me); bpy.context.scene.collection.objects.link(o); me.materials.append(m)
    bevel(o, th * 0.3, 1, 30)
    out = [o]
    for k in range(0, 10, 2):
        z, y = pts[k]
        out.append(ball(r * 0.16, (cx - th * 0.2, y, z), tips or m, seg=8, rings=6))
    return out


def tex_case(name, size=64, seed=7):
    """case-hardening colours: smooth swirly blotches of straw, blue, purple, pink and grey (soft blends, a bit of grain)"""
    r = np.random.default_rng(seed)
    def smooth_noise(n):
        lo = r.random((n + 1, n + 1))
        t = np.linspace(0, n, size, endpoint=False)
        i = t.astype(int); f = t - i; f = f * f * (3 - 2 * f)
        a = lo[i][:, i] * (1 - f)[None, :] + lo[i][:, i + 1] * f[None, :]
        b = lo[i + 1][:, i] * (1 - f)[None, :] + lo[i + 1][:, i + 1] * f[None, :]
        return a * (1 - f)[:, None] + b * f[:, None]
    n = 0.55 * smooth_noise(4) + 0.3 * smooth_noise(8) + 0.15 * smooth_noise(16)
    n = (n - n.min()) / (np.ptp(n) + 1e-6)
    pal = [hexrgb(c) for c in (0x9a9aa8, 0x6a7290, 0x3a4878, 0x5a4a86, 0x9a5a8a, 0xd8708e, 0xc8a060, 0x8a8a98, 0x7a7a88)]
    x = n * (len(pal) - 1); k = np.clip(x.astype(int), 0, len(pal) - 2); u = (x - k)[:, :, None]
    P = np.stack(pal)
    px = P[k] * (1 - u) + P[k + 1] * u
    px *= (0.9 + 0.2 * r.random((size, size)))[:, :, None]
    px = np.clip(px, 0, 1).astype(np.float32)
    return tex_canvas(name, size, size, lambda c: c.__setitem__(slice(None), px))


def build():
    ch_t = tex_case('lv_case_t')
    case = mat('lv_case', 0x8a8a96, rough=0.22, metal=0.85, tex=ch_t)        # candy case-hardening
    blue = mat('lv_blued', 0x22252e, rough=0.28, metal=0.8)
    dark = mat('lv_dark', 0x121318, rough=0.45, metal=0.5)
    walnut = mat('lv_walnut', 0x7a4520, rough=0.3, clearcoat=0.8, tex=tex_wood('lv_walnut_t', 0x8e4e24, 0x55280e, size=64, seed=21, rings=3))
    fore_w = mat('lv_forend', 0x7a4520, rough=0.32, clearcoat=0.8, tex=tex_wood('lv_forend_t', 0x8e4e24, 0x55280e, size=32, seed=22, rings=2))
    pink = mat('lv_pink', 0xff6b8b, rough=0.18, clearcoat=1.0, tex=tex_noise('lv_pink_t', 0xff6b8b, var=0.05, size=16, speck=0xffb0c0, speck_p=0.05, seed=23))
    leather = mat('lv_leather', 0xff6b8b, rough=0.55, tex=tex_stripes('lv_leather_t', 0xff6b8b, 0xd03e62, size=16, width=2))
    gold = mat('lv_gold', 0xffc83a, rough=0.16, metal=1.0)
    brass = mat('lv_brass', 0xe0ad3c, rough=0.25, metal=1.0)
    bead = mat('lv_bead', 0xffe14d, rough=0.2, metal=0.3, emit=0xffd040, strength=1.8)
    gem_p = mat('lv_gem', 0xff4fd8, rough=0.05, metal=0.2, emit=0xff4fd8, strength=0.5, clearcoat=1.0)
    gem_w = mat('lv_gem_w', 0xffffff, rough=0.04, metal=0.4, clearcoat=1.0)
    rope = mat('lv_rope', 0xd8b070, rough=0.8, tex=tex_stripes('lv_rope_t', 0xd8b070, 0x9a7440, size=8, width=2))
    black = mat('lv_black', 0x050505, rough=0.3)
    parts, lever, ham = [], [], []
    A = parts.append

    # ---------------- round barrel, muzzle crown + bore, front sight (dovetail ramp, blade, gold bead)
    A(lathe([(W(3.3), Z(8)), (W(3.3), Z(0)), (W(7.2), Z(0)), (W(8.3), Z(0.5)), (W(8.3), Z(2)), (W(8.4), Z(120)), (W(9.2), Z(380)), (W(9.8), Z(500))], (0, BORE_Y, 0), blue, seg=16))
    A(side(poly([(26, 7), (54, 7), (54, 11), (30, 14), (26, 12)]), W(8), (0, 0, 0), blue, bev=W(0.8)))
    A(side(poly([(36, 12), (46, 12), (44, SIGHT_H - 3), (40, SIGHT_H - 3)]), W(2.6), (0, 0, 0), blue, bev=W(0.4)))
    A(ball(W(2.4), (0, Y(SIGHT_H - 2.2), Z(41)), bead, seg=10, rings=6))

    # ---------------- tube magazine, its cap, the barrel band near the muzzle, the forend cap band
    TB = -18.5
    A(lathe([(W(7.2), Z(26)), (W(7.2), Z(492))], (0, Y(TB), 0), blue, seg=14))
    A(lathe([(0, Z(16)), (W(5.5), Z(16)), (W(7.4), Z(18)), (W(7.4), Z(27))], (0, Y(TB), 0), blue, seg=14))  # mag cap
    A(cyl(W(1.6), W(16), (0, Y(TB), Z(21)), dark, axis='x', seg=6))  # cap screw
    A(box((W(19), W(36), W(10)), (0, Y(-5), Z(68)), blue, bev=W(4), seg=3))  # barrel band
    A(cyl(W(2), W(21), (0, Y(-9.5), Z(68)), dark, axis='x', seg=6))
    A(box((W(31), W(44), W(11)), (0, Y(-8), Z(299)), blue, bev=W(7), seg=3))  # forend cap

    # ---------------- buckhorn rear sight: dovetail, step elevator, leaf with ears and a V notch
    A(box((W(12), W(5), W(16)), (0, Y(11), Z(REAR_D)), blue, bev=W(0.8)))
    A(side(poly([(REAR_D + 6, 12), (REAR_D + 26, 10), (REAR_D + 26, 13), (REAR_D + 6, 17)]), W(8), (0, 0, 0), blue, bev=W(0.6)))  # elevator ramp
    leaf = [(-12, 10), (12, 10), (13, 26), (17, 36), (16, 41), (11, 34), (3.5, SIGHT_H), (0, SIGHT_H - 2.6), (-3.5, SIGHT_H), (-11, 34), (-16, 41), (-17, 36), (-13, 26)]
    bm = bmesh.new()
    vs = [bm.verts.new(gv(x * S, Y(h), Z(REAR_D) - W(1.2))) for x, h in leaf]
    f = bm.faces.new(vs); r_ = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=gv(0, 0, W(2.4)), verts=[e for e in r_['geom'] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('leaf'); bm.to_mesh(me); bm.free()
    lo = bpy.data.objects.new('leaf', me); bpy.context.scene.collection.objects.link(lo); me.materials.append(blue)
    smooth(lo, 30); bevel(lo, W(0.4), 1, 30)
    A(lo)
    A(box((W(1.6), W(1.6), W(4.4)), (0, Y(SIGHT_H - 3.9), Z(REAR_D)), bead))  # a tiny gold V insert

    # ---------------- forend (walnut, rounded, swells a little toward the receiver)
    fe = side(poly([(304, 3), (488, 4), (488, -31), (304, -30)]), W(30), (0, 0, 0), fore_w, bev=W(8), seg=3)
    A(fe)

    # ---------------- receiver: candy case-hardened, ejection port on top, hammer slot, loading gate, screws
    rc = side(poly([(490, -34), (490, 10), (497, 16), (640, 16), (654, 14), (664, 6), (664, -40), (656, -50), (500, -50), (490, -42)]), W(30), (0, 0, 0), case, bev=W(2.2))
    cut(rc, box((W(14), W(12), W(62)), (0, Y(16), Z(538)), None))  # ejection port (top eject, it's an 1892)
    cut(rc, box((W(9), W(30), W(34)), (0, Y(16), Z(646)), None))  # hammer slot
    A(rc)
    A(box((W(13), W(8), W(60)), (0, Y(10), Z(538)), blue, bev=W(1)))  # the bolt seen through the port
    A(box((W(13), W(4), W(70)), (0, Y(15.4), Z(604)), blue, bev=W(1)))  # bolt top behind the port
    A(side(poly([(549, -29), (585, -29), (590, -26), (591, -16), (586, -12), (549, -12)]), W(1.6), (W(15.3), 0, 0), case, bev=W(0.6)))  # loading gate (right)
    A(cyl(W(2.2), W(1.5), (W(16.2), Y(-21), Z(552)), brass, axis='x', seg=8))
    for d, h in ((520, -32), (616, -30), (646, -38), (600, -6)):
        for sx in (-1, 1): A(cyl(W(2.6), W(1.2), (sx * W(15.3), Y(h), Z(d)), gold, axis='x', seg=8))  # screws
    # tangs: upper over the wrist, lower under it, plus the trigger
    A(side(poly([(652, 14), (734, 8), (738, 4), (664, 3)]), W(15), (0, 0, 0), case, bev=W(1.5)))
    A(side(poly([(662, -36), (740, -34.5), (742, -40), (662, -46)]), W(17), (0, 0, 0), case, bev=W(1.5)))
    A(side(poly([(684, -46), (690, -46), (692, -56), (688, -68), (684, -66), (686, -56)]), W(5), (0, 0, 0), gold, bev=W(0.8)))
    # saddle ring on the left + a tiny lasso hanging off it
    A(cyl(W(4), W(6), (-W(17), Y(-24), Z(632)), blue, axis='x', seg=8))
    A(tube(path_arc((Z(632), Y(-38)), W(13), 0, 360, n=16, x=-W(20.5)), W(1.8), brass, seg=6))
    lx, ly, lz = -W(22.5), Y(-66), Z(633)
    for k, (rr, dz, dy) in enumerate(((12, 0, 0), (13.5, 1.6, -1.2), (11, -1.4, 0.8))):  # the coil, three loops
        A(tube([(lx - W(1.7) * k, ly + W(dy) + W(rr) * math.sin(t), lz + W(dz) + W(rr) * math.cos(t)) for t in [i * math.pi / 8 for i in range(17)]], W(1.4), rope, seg=6))
    A(ball(W(3), (lx - W(1.5), ly + W(13), lz), rope, seg=8, rings=6))  # the knot that ties it on
    A(tube([(lx - W(1), ly + W(14), lz), (-W(21.5), Y(-48), Z(632))], W(1.4), rope, seg=6))
    tail = [(lx - W(2), ly - W(11), lz + W(5)), (lx - W(3), ly - W(22), lz + W(9)), (lx - W(3), ly - W(32), lz + W(7))]
    A(tube(tail, W(1.4), rope, seg=6))
    A(tube([(lx - W(3), ly - W(32) + W(5) * math.cos(t), lz + W(7) + W(4) * math.sin(t)) for t in [i * math.pi / 5 for i in range(11)]], W(1.2), rope, seg=6))  # little noose
    # rhinestones down the left of the receiver
    for k in range(8):
        d = 506 + k * 17
        A(ball(W(2.6), (-W(15.6), Y(-42), Z(d)), gem_p if k % 2 == 0 else gem_w, seg=6, rings=4, scale=(0.6, 1, 1)))

    # ---------------- straight-grip walnut stock, crescent butt plate (candy pink), sheriff star on the left
    crest = [(954, -22), (947, -50), (944, -85), (946, -120), (954, -150)]  # the concave crescent the plate sits on
    stk = side(poly([(664, 3), (738, 4), (772, 0), (954, -22)] + crest[1:] + [(940, -152), (770, -50), (742, -40), (664, -36)]), W(38), (0, 0, 0), walnut, bev=W(6), seg=3)
    taper(stk, lambda d: 0.8 if d < 760 else 0.8 + 0.2 * min(1, (d - 760) / 70))
    A(stk)
    pl = side(poly(crest + [(950, -156), (960, -160), (964, -151), (958, -120), (956, -85), (959, -50), (965, -24), (960, -16), (953, -17)]), W(38), (0, 0, 0), pink, bev=W(2))
    A(pl)
    for d, h in ((951, -40), (949, -130)): A(cyl(W(2.4), W(2), (0, Y(h), Z(d + 2)), gold, axis='z', seg=8))
    for o in star(-W(18.8), Y(-60), Z(850), W(19), W(2.2), gold, tips=gold): A(o)
    A(ball(W(4.2), (-W(20.2), Y(-60), Z(850)), gem_p, seg=8, rings=6, scale=(0.5, 1, 1)))

    # ---------------- the hammer (its own node), resting down
    hm = side(poly([(634, -4), (654, -4), (656, 8), (653, 22), (657, 30), (672, 36), (680, 38), (682, 32), (668, 26), (648, 22), (640, 12)]), W(7), (0, 0, 0), case, bev=W(1))
    ham.append(hm)
    for k in range(4): ham.append(box((W(8.4), W(1.2), W(1.6)), (0, Y(31.5 + k * 1.6), Z(664 + k * 4.2)), dark, rot=(-0.35, 0, 0)))  # checkered spur

    # ---------------- the big loop lever (its own node, pivot on the front pin), pink leather wrap
    outer = [(546, -40), (556, -37), (660, -38), (690, -40), (706, -36.5), (716, -38), (720, -46), (728, -62), (740, -86), (744, -108), (738, -130), (720, -146), (690, -154), (650, -154), (612, -147), (588, -131), (576, -108), (572, -84), (566, -62), (556, -59), (546, -52)]
    hole = [(586, -60), (698, -56), (712, -64), (724, -86), (728, -106), (722, -126), (706, -138), (684, -144), (652, -144), (622, -138), (602, -124), (591, -106), (587, -84)]
    lever.append(side(poly(outer), W(8), (0, 0, 0), case, bev=W(1.2), holes=[poly(hole)]))
    lever.append(cyl(W(4.5), W(11), (0, Y(LV_H), Z(LV_D)), gold, axis='x', seg=10))  # the pivot pin head
    # leather wrap round the front and bottom of the loop
    wrap = [(578, -92), (580, -110), (590, -128), (610, -142), (640, -150), (670, -150), (700, -146), (722, -136)]
    lever.append(sweep([(0, Y(h), Z(d)) for d, h in wrap], [W(r) for r in (5.6, 7.4, 8.0, 8.0, 8.0, 8.0, 7.4, 5.6)], leather, seg=10, squash=(1.0, 0.85)))


    for p in parts + lever + ham:
        uv_box(p, {walnut: 0.09, fore_w: 0.07, case: 0.05}.get(p.data.materials[0] if p.data.materials else None, 0.035))
    WZ = {'lv_walnut': 'a', 'lv_forend': 'a', 'lv_case': 'a', 'lv_pink': 'a', 'lv_blued': 'b', 'lv_dark': 'b'}
    bodies = zone_join(parts, 'lever_body', WZ, default='n')
    def zg(objs):
        g = {}
        for o in objs:
            apply_mods(o); mn = o.data.materials[0].name if o.data.materials else ''
            g.setdefault({'lv_case': 'B', 'lv_dark': 'B', 'lv_leather': 'A'}.get(mn, 'N'), []).append(o)
        return [(v, k) for k, v in sorted(g.items())]
    lv = mover('lever', LEVER_PIV, zg(lever))
    hn = mover('lhammer', HAMMER_PIV, zg(ham))
    meta = {'kind': 'weapon', 'id': 'lever', 'paint': ['lv_pink', 'lv_leather'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(SIGHT_H), 'z': Z(REAR_D)},
            'hatAt': [[0, Y(17), Z(560)], 0.1], 'lever': {'node': 'lever'}, 'lhammer': {'node': 'lhammer'}}
    root = finish('w_lever', bodies + [lv, hn], meta)
    if OPEN:
        lv.rotation_euler.x = 0.95   # + throws it open
        hn.rotation_euler.x = 0.75   # + cocks it
    return root


if OPEN:
    reset(); r = build(); sheet(r, 'w_lever_open', extra_note='LEVER THROWN')
else:
    main(build, 'w_lever')
