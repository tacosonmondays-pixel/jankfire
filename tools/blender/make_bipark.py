# JANKFIRE Battle Island: PETAL PARK, Port Jankton's cherry-blossom park (shared/battleisland.js pjPark(), the PK and BT
# tables: same numbers here), and the island's two park trees. Each is built over its own boxes in its placement's frame
# (y 0 = the ground) and carries meta.box = those boxes' extent. Visual only: the boxes collide.
#   p_bi_blossom  a cherry tree (sakura): a dark twisted trunk with cherry-bark bands forking into crooked spreading limbs,
#                 a dense canopy of six big pink clumps (each a cluster of puffs), lit pale pink on top and deep rose
#                 underneath (painted into the vertex colours), a drift of fallen petals round its foot
#   p_bi_leafy    a clustered leafy park tree: a grey-brown trunk, limbs you can see between the clumps, six round green
#                 clumps lit yellow-green on top, cool and dark underneath
#   p_pj_park     the park set (one model): a pale paved plaza with a pink stone border, terracotta paths with white kerbs,
#                 a tiled fountain (a bowl, a falling water curtain, a pink blossom on top), hedge planters and flower beds
#                 in clean painted boxes, cast-iron benches with honey slats, three park lamps with pink banners, the
#                 PETAL PARK gate, and a sign on the planter that says NO CLIMBING THE TREES (YOU WILL)
# The trees are their own instanced props (spun per copy round the trunk): the park leaves their lawns empty.
# run: blender52 -b --python tools/blender/make_bipark.py -- [--only=blossom,leafy,park] [--qa] [--no-sheet]
#      [--no-export] [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas, uv_trim, uv_fit, box_between
from make_portjankton import swatches, box_at
from lib import *
from lib import _obj
import lib
_argv = sys.argv; sys.argv = [_argv[0], '--', '--only=__none__']  # (make_trees builds every tree when imported: none)
import make_trees as TR
sys.argv = _argv

V3 = Vector
TAU = 2 * math.pi
ONLY = MK.ONLY
lib.FONT.setdefault('(', ['00010', '00100', '01000', '01000', '01000', '00100', '00010'])
lib.FONT.setdefault(')', ['01000', '00100', '00010', '00010', '00010', '00100', '01000'])

# shared/battleisland.js BT: each tree's boxes (trunk half-width and top; two crossed bars in the crown, each narrower
# than 1.2 m so loot never lands up there; their tops)
BT = dict(blossom=dict(t=0.3, th=3.4, bl=1.3, bw=0.55, top=5.3), leafy=dict(t=0.35, th=4.0, bl=1.5, bw=0.55, top=6.3))
# shared/battleisland.js PK: the park, in its own frame (x east, z south, the plaza's middle at the origin)
PK = dict(plaza=5.0, edge=(13.0, 11.0), path=1.5, hedge=1.1, bed=0.95,
          planters=[[-4.8, -4.8, -3.3, -3.3, 0], [3.3, -4.8, 4.8, -3.3, 0], [-4.8, 3.3, -3.3, 4.8, 0], [3.3, 3.3, 4.8, 4.8, 0],  # x0 z0 x1 z1, 0 = flower bed, 1 = hedge
                    [-11.6, -2.35, -6.2, -1.55, 1], [-11.6, 1.55, -6.2, 2.35, 1], [-2.35, 6.2, -1.55, 10.2, 1], [1.55, 6.2, 2.35, 10.2, 1]],
          benches=[[-2.4, -4.35, 0], [4.35, -2.4, 1], [2.4, 4.35, 2], [-4.35, 2.4, 3]],  # x z, facing: 0 +z, 1 -x, 2 -z, 3 +x
          bench=[1.6, 0.55, 0.5, 0.12, 0.95],  # length, depth, seat box top, back thickness, back top
          lamps=[[-6.3, -1.5], [6.3, 1.5], [-1.5, 6.3]], lampT=0.12, lampH=3.6,
          fountain=dict(r=1.7, rim=0.3, h=0.55, floor=0.12, ped=0.25, top=1.9),
          arch=dict(x=-13.0, z0=1.75, z1=2.35, t=0.3, h=4.3, hz=2.9, h0=3.0, h1=4.8),
          sign=dict(x=-11.68, z0=-2.55, z1=-1.5, y0=1.22, y1=1.8),
          kiosk=[-12.6, 8.3, -10.0, 10.3, 3.0], cup=[-11.55, 9.3, 0.45, 0.5])  # the tea kiosk: x0 z0 x1 z1 height (it faces +x); the roof's teacup: x z half-size height
PROPS = []
def prop(fid):
    def reg(fn): PROPS.append((fid, fn)); return fn
    return reg


# ------------------------------------------------------------ the flow: make_market's run_prop + a hook after the AO bake
def run_bi(fid, fn):
    lib.reset(); lib._mats.clear()
    d = fn()
    lo, hi = V3(d['box'][0]), V3(d['box'][1])
    for p in d['lod0'] + d['lod1']:
        apply_mods(p)
        bpy.context.view_layer.objects.active = p
        for s in bpy.context.view_layer.objects.selected: s.select_set(False)
        p.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if MK.opt('qa'):
        MK.qa(d['lod0'], fid + ':lod0', eps=d.get('eps', 0.001)); MK.qa(d['lod1'], fid + ':lod1', eps=d.get('eps', 0.001))
    tally = {}
    for p in d['lod0']: k = p.name.split('.')[0]; tally[k] = tally.get(k, 0) + MK.tris_of([p])
    print(f'JF_TRIS {fid}:', sorted(tally.items(), key=lambda kv: -kv[1]))
    print(f'JF_PARTS {fid}: lod0 {MK.tris_of(d["lod0"])} tris in {len(d["lod0"])} parts, lod1 {MK.tris_of(d["lod1"])} tris')
    l0 = join(d['lod0'], fid + '_lod0'); l1 = join(d['lod1'], fid + '_lod1')
    for o in (l0, l1):
        bpy.context.view_layer.objects.active = o
        for s in bpy.context.view_layer.objects.selected: s.select_set(False)
        o.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    MK.box_report(l0, lo, hi, fid + ' lod0'); MK.box_report(l1, lo, hi, fid + ' lod1')
    bake_ao([l0], dist=d.get('ao', 0.4), lo=d.get('aolo', 0.45)); bake_ao([l1], dist=d.get('ao', 0.4), lo=d.get('aolo', 0.45))
    if d.get('post'): d['post'](l0, l1)
    meta = dict(id=fid[2:], lod=d.get('lod', 50), tint=False, size=[round(hi[i] - lo[i], 3) for i in range(3)],
                box=[[round(v, 3) for v in lo], [round(v, 3) for v in hi]])
    meta.update(d.get('meta', {}))
    root = prop_finish(fid, [l0], [l1], meta)
    t0, t1 = prop_stats(root)
    mats0 = [m.name for m in l0.data.materials]; mats1 = [m.name for m in l1.data.materials]
    print(f'JF_MATS {fid}: lod0 {mats0} lod1 {mats1}  meta {json.dumps(meta)}')
    if not MK.opt('no-export'): export(root, fid)
    if MK.opt('preview'): MK.preview(root, fid, MK.opt('preview'), focus=d.get('focus', ()))
    elif not MK.opt('no-sheet'): MK.sheet4(root, fid, t0, t1, len(mats0), len(mats1), **d.get('sheet', {}))
    return root


def shade_canopy(o, names, under, top=(1.0, 1.0, 1.0), kg=0.45):
    """the canopy's light, painted into the AO colours (the game multiplies them in): each puff lit on top and shaded
    under (its normal), the whole crown lighter up top (its height): `under` = the multiplier at the darkest"""
    me = o.data; ca = me.color_attributes.get('AO')
    idx = {i for i, m in enumerate(me.materials) if m and m.name in names}
    zs = [me.vertices[v].co.z for p in me.polygons if p.material_index in idx for v in p.vertices]
    if not zs: return
    z0, z1 = min(zs), max(zs)
    for p in me.polygons:
        if p.material_index not in idx: continue
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index]
            t = kg * (v.co.z - z0) / max(z1 - z0, 1e-6) + (1 - kg) * (0.5 + 0.5 * v.normal.z)
            t = max(0.0, min(1.0, t)); t = t * t * (3 - 2 * t)
            c = ca.data[li].color; k = [under[i] + (top[i] - under[i]) * t for i in range(3)]
            ca.data[li].color = (c[0] * k[0], c[1] * k[1], c[2] * k[2], 1.0)


# ------------------------------------------------------------ painting (rows top-down, numpy)
def paint_cherry_bark(px, r0, r1, c0, c1, seed):
    """cherry bark: dark plum-brown, a few soft grooves, the pale horizontal lenticel bands cherries have"""
    TR.paint_bark(px, r0, r1, c0, c1, 0x4e2e34, 0x22121a, 0x76545a, seed, grooves=4, var=0.1, wob=0.8, knots=1)
    rng = np.random.default_rng(seed + 1); h, w = r1 - r0, c1 - c0
    for k in range(int(h * w / 90)):
        y, x, L = int(rng.integers(0, h)), int(rng.integers(0, w)), int(rng.integers(2, 5))
        for i in range(L): px[r0 + y, c0 + (x + i) % w] = px[r0 + y, c0 + (x + i) % w] * 0.5 + hexrgb(0x8a6e6c) * 0.5
    for y in range(3, h, 9): px[r0 + y, c0:c1] *= 0.86  # the rings round the trunk, soft


def paint_canopy(px, r0, r1, c0, c1, base, hi, lo, petal, dark, seed, petals=0.05, darks=0.05, sp=1):
    """foliage, painted: big soft blots between three tones (low frequency, matte, clean), a sprinkle of light
    specks (petals or leaves catching the sun) and a few darker ones"""
    rng = np.random.default_rng(seed); h, w = r1 - r0, c1 - c0
    n = 0.65 * TR.vnoise(h, w, 3, 3, rng) + 0.35 * TR.vnoise(h, w, 6, 6, rng)
    B, Hc, Lc = hexrgb(base), hexrgb(hi), hexrgb(lo)
    t = np.clip((n - 0.5) * 2.2, -1, 1)[:, :, None]
    reg = np.where(t > 0, B + (Hc - B) * t, B + (B - Lc) * t)
    s = TR.speckle(h, w, rng, sp)
    reg[s > 1 - petals] = hexrgb(petal)
    s2 = TR.speckle(h, w, rng, sp)
    reg[s2 < darks] = hexrgb(dark)
    px[r0:r1, c0:c1] = np.clip(reg, 0, 1)


def paint_drift(px, r0, r1, c0, c1, seed):
    """fallen petals on the grass, seen from above: pink petals over pale pink, a few white ones"""
    rng = np.random.default_rng(seed); h, w = r1 - r0, c1 - c0
    n = TR.vnoise(h, w, 4, 4, rng)
    reg = hexrgb(0xffb6dc)[None, None] * (0.92 + 0.12 * n[:, :, None])
    s = TR.speckle(h, w, rng)
    reg[s > 0.86] = hexrgb(0xff8ac6); reg[s < 0.08] = hexrgb(0xfff0f8); reg[(s > 0.45) & (s < 0.5)] = hexrgb(0xf06aae)
    px[r0:r1, c0:c1] = np.clip(reg, 0, 1)


# ------------------------------------------------------------ tree helpers
def spline(pts, n=3):
    """catmull-rom through game points, n sub-steps a span: limbs bend instead of kinking"""
    P = [V3(p) for p in pts]; out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(P[-1])
    return [tuple(p) for p in out]


def limb(name, m, pts, r0, r1, seg=6, n=3):
    """a tapering bough along a smooth curve (r0 at the root, r1 at the tip)"""
    sp = spline(pts, n); L = len(sp)
    o = sweep(sp, [r0 + (r1 - r0) * (i / (L - 1)) ** 0.8 for i in range(L)], m, seg=seg, name=name, cap=True)
    return TR.bake_tf(o)


def twisted_trunk(name, m, prof, seg, twist, lean, flare=(0.0, 0.5, 3, 0.0)):
    """a lathe trunk, twisted (radians a metre) and leaning (game x, z a metre, eased in), buttress lobes at the foot:
    flare = (amount, height, lobes, phase)"""
    o = TR.bake_tf(lathe(prof, (0, 0, 0), m, seg=seg, axis='y', name=name, cap=False))
    amt, fh, lobes, ph = flare
    def f(p):
        a = math.atan2(p.z, p.x); r = math.hypot(p.x, p.z)
        if p.y < fh and amt: r += amt * ((fh - p.y) / fh) ** 2 * max(0.0, math.cos(lobes * a + ph)) ** 2
        a += twist * p.y
        k = p.y * p.y / (p.y + 1.0)
        return V3((math.cos(a) * r + lean[0] * k, p.y, math.sin(a) * r + lean[1] * k))
    return TR.edit_verts(o, f)


def clumps(pfx, m, spec, seed, seg=6, rings=4, depth=0.42, squash=0.86, wob=0.35):
    """the canopy: each clump a core with puffs sunk into it in rings (laid out like make_trees.puff_crown), then the
    faces hidden inside another lump dropped, once, over every lump of every clump (clumps overlap; culling an already
    culled, open lump against the rest would punch holes): spec = [(centre, radii, puff radius range, layout)]"""
    lumps = []
    for k, (c, R, rad, lay) in enumerate(spec):
        rnd = random.Random(seed + k * 7)
        lumps.append(TR.lump(c, R, m, f'{pfx}{k}_core', seg=seg, rings=rings, rot=(0, 0.2, 0)))
        for la, cnt, ph in lay:
            for i in range(cnt):
                yk = max(-1.0, min(1.0, la + rnd.uniform(-0.06, 0.06)))
                rr = math.sqrt(max(0.0, 1 - yk * yk)); a = math.radians(ph) + TAU * i / max(cnt, 1) + rnd.uniform(-wob, wob)
                d = V3((math.cos(a) * rr, yk, math.sin(a) * rr))
                p = V3((c[0] + d.x * R[0], c[1] + d.y * R[1], c[2] + d.z * R[2]))
                r = rnd.uniform(*rad)
                p -= V3((d.x / R[0], d.y / R[1], d.z / R[2])).normalized() * r * depth  # (along the core's normal)
                lumps.append(TR.lump(tuple(p), (r, r * squash, r), m, f'{pfx}{k}_{la}_{i}', seg=seg, rings=rings,
                                     rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(0, 3), rnd.uniform(-0.3, 0.3))))
    return TR.cull_inside(lumps)


def drift(name, m, rect, W, H, n=28, r=(0.9, 1.9), y=0.025, seed=3):
    """fallen petals round the foot: one flat scalloped splat (a fan from the trunk), blown longer one way"""
    rnd = random.Random(seed); bm = bmesh.new()
    c = bm.verts.new(gv(0, y, 0)); ring = []
    ph = [rnd.uniform(0, TAU) for _ in range(3)]
    for k in range(n):
        a = TAU * k / n
        rr = r[0] + (r[1] - r[0]) * (0.5 + 0.25 * math.sin(a + ph[0]) + 0.15 * math.sin(2 * a + ph[1]) + 0.1 * math.sin(3 * a + ph[2]))
        rr *= 0.9 if k % 2 else 1.04  # (the scallops: petals at the edge)
        ring.append(bm.verts.new(gv(math.cos(a) * rr, y, math.sin(a) * rr)))
    for k in range(n): bm.faces.new((c, ring[(k + 1) % n], ring[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    for p in o.data.polygons:
        if p.normal.z < 0: p.flip()
    TR.uv_region(o, rect, W, H, proj='up', ppm=10, umode='fold', vmode='fold')
    return o


def bars(t, kind):
    """the crown's two crossed collision bars and the trunk box: the extent (meta.box)"""
    b = BT[kind]
    return ((-b['bl'], 0.0, -b['bl']), (b['bl'], b['top'], b['bl']))


# ============================================================ p_bi_blossom
@prop('p_bi_blossom')
def build_blossom():
    W = H = 64
    px = np.zeros((H, W, 3), np.float32)
    paint_cherry_bark(px, 0, 32, 0, W, 101)  # (full width: tiles round the trunk)
    paint_canopy(px, 32, 64, 0, 32, 0xff8cc8, 0xffb2da, 0xee6cb4, 0xffcce8, 0xe05aa4, 103, petals=0.035, darks=0.03, sp=1)
    paint_drift(px, 32, 64, 32, 64, 105)
    tex = TR.img('bib_t', px)
    bark = mat('bib_bark', 0xffffff, rough=0.5, clearcoat=0.25, tex=tex)
    bloom = mat('bib_bloom', 0xffffff, rough=0.82, tex=tex)
    TR.cull(bark, bloom)
    BARK, BLOOM, DRIFT = (0, 32, 0, W), (32, 64, 0, 32), (32, 64, 32, 64)
    # ---- the trunk: short, thick, twisted, leaning a little, buttress lobes; forks at 1.7 m
    trunk = twisted_trunk('bib_trunk', bark, [(0.4, -0.02), (0.31, 0.25), (0.26, 0.8), (0.24, 1.5), (0.2, 2.05)], 9, 0.35, (0.12, 0.05), flare=(0.16, 0.55, 3, 0.4))
    TR.jit(trunk, 0.012, 5, keep_y_below=0.01)
    # the limbs: crooked, spreading wide and low (cherries go out more than up), each into a clump; twigs under them
    L = [limb('bib_l0', bark, [(0.12, 1.55, 0.0), (0.6, 2.05, 0.22), (1.15, 2.45, 0.3), (1.55, 2.95, 0.5), (1.85, 3.3, 0.62)], 0.17, 0.06),
         limb('bib_l1', bark, [(0.1, 1.6, 0.05), (-0.45, 2.15, 0.35), (-0.85, 2.55, 0.5), (-1.3, 3.0, 0.82), (-1.6, 3.45, 0.95)], 0.16, 0.06),
         limb('bib_l2', bark, [(0.15, 1.7, 0.0), (0.2, 2.35, -0.45), (0.38, 2.95, -0.82), (0.3, 3.55, -1.25), (0.32, 4.0, -1.45)], 0.15, 0.06),
         limb('bib_l3', bark, [(0.16, 1.8, 0.04), (0.02, 2.6, 0.12), (-0.25, 3.35, 0.05), (-0.38, 4.2, 0.18)], 0.14, 0.05),
         limb('bib_l4', bark, [(0.55, 2.1, 0.2), (1.0, 2.35, -0.3), (1.55, 2.75, -0.85), (2.0, 3.05, -1.3)], 0.09, 0.04, seg=5),
         limb('bib_l5', bark, [(-0.4, 2.1, 0.32), (-0.95, 2.45, -0.15), (-1.45, 2.95, -0.75), (-1.75, 3.25, -1.05)], 0.09, 0.04, seg=5)]
    tw = [((1.2, 2.45, 0.3), (1.45, 2.75, 1.05)), ((-0.85, 2.55, 0.5), (-1.35, 2.85, 1.45)), ((0.38, 2.95, -0.82), (-0.3, 3.2, -1.7)),
          ((1.55, 2.75, -0.85), (2.6, 2.95, -1.05)), ((1.55, 2.95, 0.5), (2.65, 3.25, 0.35)), ((-1.3, 3.0, 0.82), (-2.45, 3.25, 0.65))]
    T = [limb(f'bib_tw{i}', bark, [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.08, (a[2] + b[2]) / 2), b], 0.045, 0.02, seg=4, n=2) for i, (a, b) in enumerate(tw)]
    # ---- the canopy: six big clumps, a wide umbrella (2.75..5.9 m), each a cluster of puffs
    lay = [(-0.35, 6, 10), (0.15, 5, 40), (0.62, 3, 20), (1.0, 1, 0)]
    spec = [((1.9, 3.65, 0.65), (1.45, 0.88, 1.3), (0.46, 0.62), lay),
            ((-1.75, 3.85, 0.95), (1.4, 0.92, 1.3), (0.46, 0.62), lay),
            ((0.35, 4.35, -1.45), (1.45, 0.95, 1.25), (0.47, 0.63), lay),
            ((-0.35, 4.95, 0.2), (1.3, 0.85, 1.25), (0.46, 0.6), [(-0.2, 6, 30), (0.4, 5, 0), (1.0, 1, 0)]),
            ((2.15, 3.35, -1.35), (1.0, 0.7, 0.95), (0.42, 0.56), [(-0.2, 4, 0), (0.55, 3, 30)]),
            ((-1.85, 3.5, -1.15), (1.0, 0.72, 0.95), (0.42, 0.56), [(-0.2, 4, 15), (0.55, 3, 50)])]
    lumps = clumps('bib_c', bloom, spec, 11)
    for o in lumps: TR.uv_region(o, BLOOM, W, H, proj='box', ppm=16)
    for o in [trunk] + L + T: TR.uv_region(o, BARK, W, H, proj='cyl', ppm=14, umode='tile', vmode='fold', arc_r=0.24)
    dr = drift('bib_drift', bloom, DRIFT, W, H, seed=7)
    lod0 = [join([trunk] + L + T, 'bib_wood'), join(lumps, 'bib_crown'), dr]
    # ---- lod1: a blob a clump (on the clumps' own extents), the trunk and three limbs as 4-sided rods
    far = []
    for k, (c, R, _, _) in enumerate(spec):
        cx, cy, cz = c; rx, ry, rz = R[0] + 0.45, R[1] + 0.4, R[2] + 0.45
        b = TR.blob(f'bib_far{k}', bloom, [(cy - ry * 0.75, rx * 0.72, 6, 0, cx, cz, 1, rz / rx), (cy, rx, 7, 25, cx, cz, 1, rz / rx), (cy + ry * 0.6, rx * 0.8, 6, 50, cx, cz, 1, rz / rx)],
                    bottom=(cx, cy - ry, cz), top=(cx, cy + ry, cz), noise=0.06, seed=k)
        TR.uv_region(b, BLOOM, W, H, proj='box', ppm=10); far.append(b)
    ft = TR.bake_tf(lathe([(0.32, 0.0), (0.22, 1.8)], (0, 0, 0), bark, seg=4, axis='y', name='bib_ftrunk', cap=False))
    fl = [limb(f'bib_fl{i}', bark, p, 0.15, 0.07, seg=4, n=1) for i, p in enumerate(([(0.1, 1.6, 0), (1.0, 2.5, 0.3), (1.85, 3.3, 0.62)], [(0, 1.6, 0), (-0.85, 2.55, 0.5), (-1.6, 3.45, 0.95)], [(0.1, 1.7, 0), (0.3, 2.9, -0.8), (0.32, 3.9, -1.4)]))]
    for o in [ft] + fl: TR.uv_region(o, BARK, W, H, proj='cyl', ppm=14, umode='tile', vmode='fold', arc_r=0.24)
    lod1 = [join(far, 'bib_fcrown'), join([ft] + fl, 'bib_fwood')]
    for o in lod0 + lod1:
        for p in o.data.polygons: p.use_smooth = True
    post = lambda l0, l1: [shade_canopy(o, {'bib_bloom'}, (0.74, 0.44, 0.68), kg=0.42) for o in (l0, l1)]
    return dict(lod0=lod0, lod1=lod1, box=bars(0, 'blossom'), ao=0.9, aolo=0.55, lod=70, post=post, sheet=dict(exposure=-0.7),
                focus=[((0, 2.4, 0), (1.0, -0.15, 0.6), 7.0), ((0, 4.2, 0), (0.6, 0.9, 0.5), 10.0), ((0, 1.0, 0), (-0.4, 0.3, 1.0), 4.5)])


# ============================================================ p_bi_leafy
@prop('p_bi_leafy')
def build_leafy():
    W = H = 64
    px = np.zeros((H, W, 3), np.float32)
    TR.paint_bark(px, 0, 32, 0, W, 0x6e5848, 0x2e2420, 0x9a8676, 201, grooves=7, var=0.1, wob=1.2, knots=3)
    paint_canopy(px, 32, 64, 0, 32, 0x7fd23a, 0xb0e850, 0x56b236, 0xd8fa86, 0x3f9a3a, 203, petals=0.035, darks=0.03)
    paint_canopy(px, 32, 64, 32, 64, 0x6cc43a, 0xa0e04c, 0x48a63a, 0xccf47a, 0x388e3a, 204, petals=0.03, darks=0.035)
    tex = TR.img('bil_t', px)
    bark = mat('bil_bark', 0xffffff, rough=0.55, clearcoat=0.2, tex=tex)
    leaf = mat('bil_leaf', 0xffffff, rough=0.8, tex=tex)
    TR.cull(bark, leaf)
    BARK, LEAF, LEAF2 = (0, 32, 0, W), (32, 64, 0, 32), (32, 64, 32, 64)
    trunk = twisted_trunk('bil_trunk', bark, [(0.44, -0.02), (0.34, 0.3), (0.29, 1.0), (0.27, 2.2), (0.22, 2.9)], 9, 0.08, (-0.04, 0.06), flare=(0.18, 0.6, 4, 0.2))
    TR.jit(trunk, 0.01, 6, keep_y_below=0.01)
    L = [limb('bil_l0', bark, [(0.05, 2.3, 0.0), (0.55, 3.0, 0.3), (1.2, 3.6, 0.65), (1.75, 4.15, 0.92)], 0.17, 0.07),
         limb('bil_l1', bark, [(0.0, 2.4, 0.05), (-0.6, 3.1, 0.25), (-1.2, 3.75, 0.45), (-1.65, 4.3, 0.6)], 0.17, 0.07),
         limb('bil_l2', bark, [(0.05, 2.5, -0.05), (0.15, 3.3, -0.6), (0.2, 4.0, -1.15), (0.22, 4.6, -1.5)], 0.16, 0.06),
         limb('bil_l3', bark, [(0.0, 2.7, 0.0), (0.05, 3.8, 0.1), (0.0, 5.0, 0.12), (0.02, 5.7, 0.1)], 0.16, 0.06),
         limb('bil_l4', bark, [(0.0, 2.2, -0.05), (-0.55, 2.8, -0.6), (-1.05, 3.3, -1.05), (-1.3, 3.65, -1.25)], 0.1, 0.045, seg=5),
         limb('bil_l5', bark, [(0.05, 2.2, -0.05), (0.7, 2.75, -0.5), (1.25, 3.25, -0.85), (1.55, 3.55, -1.0)], 0.1, 0.045, seg=5)]
    tw = [((1.2, 3.6, 0.65), (2.2, 3.85, 1.4)), ((-1.2, 3.75, 0.45), (-2.3, 3.95, 1.05)), ((0.2, 4.0, -1.15), (-0.6, 4.3, -2.1)),
          ((0.55, 3.0, 0.3), (0.4, 3.7, 1.55))]
    T = [limb(f'bil_tw{i}', bark, [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.1, (a[2] + b[2]) / 2), b], 0.055, 0.025, seg=4, n=2) for i, (a, b) in enumerate(tw)]
    lay = [(-0.3, 5, 0), (0.3, 5, 36), (0.85, 2, 10)]
    spec = [((1.95, 4.45, 1.0), (1.4, 1.0, 1.35), (0.58, 0.76), lay),
            ((-1.85, 4.65, 0.7), (1.4, 1.0, 1.35), (0.58, 0.76), lay),
            ((0.25, 4.95, -1.75), (1.45, 1.05, 1.3), (0.6, 0.78), lay),
            ((0.0, 6.15, 0.15), (1.45, 0.98, 1.4), (0.6, 0.78), [(-0.2, 5, 20), (0.45, 4, 0), (1.0, 1, 0)]),
            ((-1.45, 3.85, -1.45), (0.95, 0.72, 0.95), (0.44, 0.58), [(-0.2, 5, 0), (0.55, 3, 30)]),
            ((1.75, 3.75, -1.15), (0.95, 0.72, 0.9), (0.44, 0.58), [(-0.2, 5, 15), (0.55, 3, 50)])]
    lumps = clumps('bil_c', leaf, spec, 21)
    for i, o in enumerate(lumps): TR.uv_region(o, LEAF if i % 3 else LEAF2, W, H, proj='box', ppm=16)
    for o in [trunk] + L + T: TR.uv_region(o, BARK, W, H, proj='cyl', ppm=14, umode='tile', vmode='fold', arc_r=0.27)
    lod0 = [join([trunk] + L + T, 'bil_wood'), join(lumps, 'bil_crown')]
    far = []
    for k, (c, R, _, _) in enumerate(spec):
        cx, cy, cz = c; rx, ry = R[0] + 0.45, R[1] + 0.42; rz = R[2] + 0.45
        b = TR.blob(f'bil_far{k}', leaf, [(cy - ry * 0.75, rx * 0.72, 6, 0, cx, cz, 1, rz / rx), (cy, rx, 7, 25, cx, cz, 1, rz / rx), (cy + ry * 0.6, rx * 0.8, 6, 50, cx, cz, 1, rz / rx)],
                    bottom=(cx, cy - ry, cz), top=(cx, cy + ry, cz), noise=0.06, seed=k + 3)
        TR.uv_region(b, LEAF, W, H, proj='box', ppm=10); far.append(b)
    ft = TR.bake_tf(lathe([(0.34, 0.0), (0.22, 2.6)], (0, 0, 0), bark, seg=4, axis='y', name='bil_ftrunk', cap=False))
    fl = [limb(f'bil_fl{i}', bark, p, 0.16, 0.07, seg=4, n=1) for i, p in enumerate(([(0.05, 2.3, 0), (1.2, 3.6, 0.65), (1.75, 4.15, 0.92)], [(0, 2.4, 0), (-1.2, 3.75, 0.45), (-1.65, 4.3, 0.6)], [(0.05, 2.5, 0), (0.2, 4.0, -1.15), (0.22, 4.6, -1.5)]))]
    for o in [ft] + fl: TR.uv_region(o, BARK, W, H, proj='cyl', ppm=14, umode='tile', vmode='fold', arc_r=0.27)
    lod1 = [join(far, 'bil_fcrown'), join([ft] + fl, 'bil_fwood')]
    for o in lod0 + lod1:
        for p in o.data.polygons: p.use_smooth = True
    post = lambda l0, l1: [shade_canopy(o, {'bil_leaf'}, (0.42, 0.6, 0.68), kg=0.42) for o in (l0, l1)]
    return dict(lod0=lod0, lod1=lod1, box=bars(0, 'leafy'), ao=1.0, aolo=0.55, lod=70, post=post, sheet=dict(exposure=-0.7),
                focus=[((0, 3.0, 0), (1.0, -0.2, 0.6), 8.0), ((0, 5.0, 0), (0.6, 0.9, 0.5), 11.0)])


# ============================================================ p_pj_park
def park_boxes():
    """the park's collision boxes in its frame, exactly as shared/battleisland.js pjPark() adds them: (lo, hi)"""
    out = []
    for x0, z0, x1, z1, k in PK['planters']: out.append(((x0, 0, z0), (x1, PK['hedge'] if k else PK['bed'], z1)))
    L, D, st, bt, bh = PK['bench']
    for x, z, f in PK['benches']:
        for (a0, b0, a1, b1, y0, y1) in ((-L / 2, -D / 2, L / 2, D / 2, 0, st), (-L / 2, -D / 2, L / 2, -D / 2 + bt, st, bh)):
            pts = [rot_f(a, b, f) for a in (a0, a1) for b in (b0, b1)]
            out.append(((x + min(p[0] for p in pts), y0, z + min(p[1] for p in pts)), (x + max(p[0] for p in pts), y1, z + max(p[1] for p in pts))))
    t = PK['lampT']
    for x, z in PK['lamps']: out.append(((x - t, 0, z - t), (x + t, PK['lampH'], z + t)))
    F = PK['fountain']; r, w = F['r'], F['rim']
    out += [((-r, 0, -r), (r, F['h'], -r + w)), ((-r, 0, r - w), (r, F['h'], r)), ((-r, 0, -r + w), (-r + w, F['h'], r - w)), ((r - w, 0, -r + w), (r, F['h'], r - w)),
            ((-r + w, 0, -r + w), (r - w, F['floor'], r - w)), ((-F['ped'], 0, -F['ped']), (F['ped'], F['top'], F['ped']))]
    a = PK['arch']
    for s_ in (-1, 1): out.append(((a['x'] - a['t'], 0, min(s_ * a['z0'], s_ * a['z1'])), (a['x'] + a['t'], a['h'], max(s_ * a['z0'], s_ * a['z1']))))
    out.append(((a['x'] - a['t'] + 0.05, a['h0'], -a['hz']), (a['x'] + a['t'] - 0.05, a['h1'], a['hz'])))
    g = PK['sign']; out.append(((g['x'] - 0.05, g['y0'], g['z0']), (g['x'] + 0.05, g['y1'], g['z1'])))
    x0, z0, x1, z1, kh = PK['kiosk']; out.append(((x0, 0, z0), (x1, kh, z1)))
    cx, cz, cr, ch = PK['cup']; out.append(((cx - cr, kh, cz - cr), (cx + cr, kh + ch, cz + cr)))
    return out


def rot_f(a, b, f):
    """a bench-frame point (a along the seat, b toward its front: the bench faces +z) turned to face f (0 +z, 1 -x,
    2 -z, 3 +x), the way three turns things (rotation.y)"""
    t = bench_xf(f); c, s_ = round(math.cos(t)), round(math.sin(t))
    return (a * c + b * s_, -a * s_ + b * c)


def bench_xf(f):
    """the bench frame -> park frame turn, game y (radians)"""
    return {0: 0.0, 1: -math.pi / 2, 2: math.pi, 3: math.pi / 2}[f]


def turn_place(objs, ang, at):
    """turn parts about game y by ang (three's rotation.y) and move them to at (x, z): baked into the meshes"""
    R = Matrix.Rotation(ang, 4, 'Z')  # (blender z = game y)
    for o in objs:
        TR.bake_tf(o); o.data.transform(R); o.data.transform(Matrix.Translation(gv(at[0], 0, at[1]))); o.data.update()
    return objs


def grid_slab(name, M, A, key, x0, z0, x1, z1, y, cell):
    """a paved top at height y over x0..x1, z0..z1: quads on a world grid of `cell` metres, each one mapped onto the
    atlas cell `key` (it tiles, so the paving runs on seamlessly across quads and slabs); no sides (the kerbs and the
    border stand on the edges)"""
    u0, v0, u1, v1 = A.uvrect(key)
    def cuts(a, b):
        return sorted({round(a, 5), round(b, 5)} | {round(k * cell, 5) for k in range(math.ceil(a / cell + 1e-6), math.floor(b / cell - 1e-6) + 1)})
    xs, zs = cuts(x0, x1), cuts(z0, z1)
    bm = bmesh.new(); V = {(x, z): bm.verts.new(gv(x, y, z)) for x in xs for z in zs}
    uvl = bm.loops.layers.uv.new('UVMap')
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            a, b, c, d = (xs[i], zs[j]), (xs[i], zs[j + 1]), (xs[i + 1], zs[j + 1]), (xs[i + 1], zs[j])
            f = bm.faces.new([V[a], V[b], V[c], V[d]])
            if f.normal.z < 0: f.normal_flip()
            gx, gz = math.floor((xs[i] + xs[i + 1]) / 2 / cell) * cell, math.floor((zs[j] + zs[j + 1]) / 2 / cell) * cell
            for lp in f.loops:
                X, Z = lp.vert.co.x, -lp.vert.co.y
                lp[uvl].uv = (u0 + (u1 - u0) * (X - gx) / cell, v1 - (v1 - v0) * (Z - gz) / cell)
    return _obj(name, bm, M)


def ring_prism(name, M, outer, inner, y0, y1, bottom=False):
    """a wall round a chamfered square: outer / inner = (half size, chamfer); outside, inside and top faces"""
    def loop(h, c, y):
        pts = [(h, -h + c), (h, h - c), (h - c, h), (-h + c, h), (-h, h - c), (-h, -h + c), (-h + c, -h), (h - c, -h)]
        return [bm.verts.new(gv(x, y, z)) for x, z in pts]
    bm = bmesh.new()
    O0, O1, I0, I1 = loop(*outer, y0), loop(*outer, y1), loop(*inner, y0), loop(*inner, y1)
    n = 8
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((O0[k], O0[j], O1[j], O1[k])); bm.faces.new((I0[j], I0[k], I1[k], I1[j])); bm.faces.new((O1[k], O1[j], I1[j], I1[k]))
        if bottom: bm.faces.new((O0[j], O0[k], I0[k], I0[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, M)


def cham_disc(name, M, h, c, y):
    """a flat chamfered square (water, the basin's floor), facing up, as a fan"""
    bm = bmesh.new()
    pts = [(h, -h + c), (h, h - c), (h - c, h), (-h + c, h), (-h, h - c), (-h, -h + c), (-h + c, -h), (h - c, -h)]
    ctr = bm.verts.new(gv(0, y, 0)); R = [bm.verts.new(gv(x, y, z)) for x, z in pts]
    for k in range(8):
        f = bm.faces.new((ctr, R[k], R[(k + 1) % 8]))
        if f.normal.z < 0: f.normal_flip()
    return _obj(name, bm, M)


def tri_ngons(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    ng = [f for f in bm.faces if len(f.verts) > 4]
    if ng: bmesh.ops.triangulate(bm, faces=ng)
    bm.to_mesh(o.data); bm.free(); o.data.update()
    return o


def drop_bottom(o):
    """faces pointing straight down (a thing's underside, on the paving): nobody sees them"""
    return TR.kill_faces(TR.bake_tf(o), lambda c, n: n.y < -0.95)


def paint_pave(px):  # pale cream slabs, 2 x 2 a cell, each its own tone, soft grout
    h, w = px.shape[:2]; r = np.random.default_rng(301); s = h // 2
    for j, i, c in ((0, 0, 0xf6f0e4), (0, 1, 0xf0e6d6), (1, 0, 0xeee4d2), (1, 1, 0xf4ecde)):
        px[j * s:(j + 1) * s, i * s:(i + 1) * s] = hexrgb(c)
    px[:] *= 0.975 + 0.035 * r.random((h, w, 1))
    px[::s] = hexrgb(0xd6c8b2); px[:, ::s] = hexrgb(0xd6c8b2)
    px[1::s] *= 1.02


def paint_terra(px):  # terracotta pavers, running bond, light mortar
    h, w = px.shape[:2]; r = np.random.default_rng(303)
    for row in range(h // 4):
        off = (row % 2) * 4
        for k in range(w // 8):
            c = hexrgb(0xd8663e) * r.uniform(0.92, 1.05)
            for x in range(8): px[row * 4:(row + 1) * 4, (off + k * 8 + x) % w] = c
            px[row * 4:(row + 1) * 4, (off + k * 8) % w] = hexrgb(0xeccaa8)
    px[::4] = hexrgb(0xeccaa8)
    px[:] *= 0.98 + 0.03 * r.random((h, w, 1))


def paint_tiles(px):  # glazed tiles (the fountain): sea-glass teal, white grout, a few lighter ones
    h, w = px.shape[:2]; r = np.random.default_rng(305)
    for y in range(0, h, 8):
        for x in range(0, w, 8): px[y:y + 8, x:x + 8] = hexrgb(0x3cc8d8 if r.random() > 0.2 else 0x6edcea)
    px[1::8] *= 1.08
    px[::8] = hexrgb(0xf4f2ee); px[:, ::8] = hexrgb(0xf4f2ee)


def paint_clean_text(lines, bg, fg, border, scale=1):
    """a crisp painted sign: flat colour, a border, centred 5x7 text (no wear: a brand-new park)"""
    def d(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(bg)
        if border is not None: px[:2] = px[-2:] = hexrgb(border); px[:, :2] = px[:, -2:] = hexrgb(border)
        lh = 8 * scale; y0 = (h - lh * len(lines)) // 2 + scale // 2
        for i, s_ in enumerate(lines):
            text_px(px, s_, max(0, (w - (len(s_) * 6 - 1) * scale) // 2), y0 + i * lh, scale, fg)
    return d


def paint_banner(px):  # the lamp banners: hot pink, a white five-petal blossom, a yellow middle, a hem
    from make_pjstreet import pix
    px[:] = hexrgb(0xff4fd8)
    pix(px, ['...WW...', '..WWWW..', 'WW.WW.WW', 'WWWYYWWW', '.WWYYWW.', '..WWWW..', '.WW..WW.', '.W....W.'], 2, 7, 1 if px.shape[1] < 16 else 1, {'W': 0xfff4fa, 'Y': 0xffe14d})
    px[-3:] = hexrgb(0xffe14d); px[:2] = hexrgb(0xb02a96)


@prop('p_pj_park')
def build_park():
    fid = 'pjk'
    A = Atlas(fid + '_atlas', 128, 256)
    A.cell('sign', 128, 24, paint_clean_text(['PETAL PARK'], 0xffe14d, 0xd81e9a, 0x1c1c22, scale=2))
    A.cell('pave', 32, 32, paint_pave); A.cell('terra', 32, 32, paint_terra)
    A.cell('hedge', 32, 32, lambda px: paint_canopy(px, 0, 32, 0, 32, 0x4cb83a, 0x72d04a, 0x3a9a36, 0xa8ec6a, 0x2e8034, 307, petals=0.03, darks=0.04))
    A.cell('tile', 32, 32, paint_tiles)
    A.cell('joke', 72, 32, paint_clean_text(['NO CLIMBING', 'THE TREES', '(YOU WILL)'], 0xfdfbf6, 0x1c1c22, 0xff4fd8))
    A.cell('banner', 16, 32, paint_banner)
    A.cell('slat', 16, 8, MK.paint_wood(0xdc9c58, 0xb07038, 309))
    swatches(A, (('cream', 0xfbf6ec, 0.02, None), ('pinkpaint', 0xff5cc8, 0.02, None), ('border', 0xf2a2b8, 0.03, None), ('iron', 0x1e3a48, 0.03, None),
                 ('soil', 0x5a3e2c, 0.08, None), ('leafbed', 0x3fae3a, 0.06, None), ('petal', 0xff8ccc, 0.03, None), ('flowery', 0xffe14d, 0.03, None),
                 ('flowerw', 0xfdf6fa, 0.02, None), ('floor', 0x1aa8c0, 0.04, None), ('gold', 0xffc83a, 0.03, None), ('cherry', 0xe8304a, 0.02, None),
                 ('water1', 0x6ad8f0, 0.02, None), ('pave1', 0xf2eadc, 0.01, None), ('terra1', 0xd8683e, 0.02, None), ('tea', 0xf7a8c8, 0.02, None)))
    A.cell('ksign', 96, 20, paint_clean_text(['PETAL TEA'], 0xff4fd8, 0xfdfbf6, 0xffe14d, scale=2))
    A.cell('menu', 64, 40, paint_clean_text(['TEA ...... 2', 'MORE TEA . 3', 'PETALS FREE', '(FLOOR)'], 0x1c1c22, 0xfdfbf6, 0xff4fd8))
    A.cell('stripeh', 32, 16, lambda px: [px.__setitem__(slice(i * 2, i * 2 + 2), hexrgb(0xff4fd8 if i % 2 else 0xfdfbf6)) for i in range(8)])
    A.cell('stripev', 32, 16, lambda px: [px.__setitem__((slice(None), slice(i * 4, i * 4 + 4)), hexrgb(0xff4fd8 if i % 2 else 0xfdfbf6)) for i in range(8)])
    M = mat(fid, 0xffffff, rough=0.42, tex=A.image(), clearcoat=0.35)
    GL = mat('glow', 0xfff4dc, emit=0xfff4dc, strength=2.5)
    GZ = mat(fid + '_water', 0x7fe4ff, rough=0.05, metal=0.0, alpha=0.5)
    P, Q = [], []
    def bk(lo, hi, key, name, bev=0.0, m=None, far=False, bottom=True):
        o = box(tuple(hi[i] - lo[i] for i in range(3)), tuple((hi[i] + lo[i]) / 2 for i in range(3)), m or M, bev=bev, name=name, seg=1)
        uv_fit(o, A, key)
        if not bottom: drop_bottom(o)
        (Q if far else P).append(o); return o
    def hedge_uv(o): return TR.uv_region(o, cellrect(A, 'hedge'), A.w, A.h, proj='box', ppm=26)
    PY, ZY = 0.05, 0.07  # the paths' and the plaza's top (a few cm over the grass: no fighting with the ground)
    pl, (ex, ez), pw = PK['plaza'], PK['edge'], PK['path']
    # ---- the plaza: pale paving, a pink stone border; the four terracotta paths out to the park's edges, white kerbs
    P.append(grid_slab(fid + '_plaza', M, A, 'pave', -pl, -pl, pl, pl, ZY, 1.25))
    bw = 0.15
    for lo, hi in (((-pl - bw, -0.03, -pl - bw), (pl + bw, 0.095, -pl + bw)), ((-pl - bw, -0.03, pl - bw), (pl + bw, 0.095, pl + bw)),
                   ((-pl - bw, -0.03, -pl + bw), (-pl + bw, 0.095, pl - bw)), ((pl - bw, -0.03, -pl + bw), (pl + bw, 0.095, pl - bw))):
        bk(lo, hi, 'border', fid + '_border', bev=0.01)
    kw = 0.06
    for ax in ('x', 'z'):
        e = ex if ax == 'x' else ez
        for s_ in (-1, 1):
            a0, a1 = sorted((s_ * pl, s_ * e))
            if ax == 'x': P.append(grid_slab(fid + '_path', M, A, 'terra', a0, -pw, a1, pw, PY, 1.2))
            else: P.append(grid_slab(fid + '_path', M, A, 'terra', -pw, a0, pw, a1, PY, 1.2))
            k0, k1 = sorted((s_ * (pl + bw - 0.05), s_ * (e + kw)))
            for side_ in (-1, 1):
                c = side_ * pw
                if ax == 'x': bk((k0, -0.03, c - kw), (k1, 0.085, c + kw), 'white', fid + '_kerb')
                else: bk((c - kw, -0.03, k0), (c + kw, 0.085, k1), 'white', fid + '_kerb')
            ee = s_ * e; ext = 2.45 if (ax == 'x' and s_ < 0) else pw + kw + 0.02  # (the gate's end kerb runs on under the pillars)
            if ax == 'x': bk((ee - kw - 0.01, -0.035, -ext), (ee + kw + 0.01, 0.09, ext), 'white', fid + '_kerb')
            else: bk((-ext, -0.035, ee - kw - 0.01), (ext, 0.09, ee + kw + 0.01), 'white', fid + '_kerb')
    # ---- planters: clean painted boxes, a pink band, a white rim; box hedges, or flower beds on the plaza's corners
    rnd = random.Random(5)
    for x0, z0, x1, z1, k in PK['planters']:
        y0 = ZY - 0.01 if max(abs(x0), abs(x1)) <= pl and max(abs(z0), abs(z1)) <= pl else -0.02
        bk((x0, y0, z0), (x1, 0.5, z1), 'cream', fid + '_planter', bev=0.015, bottom=False)
        bk((x0 - 0.015, 0.36, z0 - 0.015), (x1 + 0.015, 0.44, z1 + 0.015), 'pinkpaint', fid + '_band')
        bk((x0 - 0.04, 0.5, z0 - 0.04), (x1 + 0.04, 0.58, z1 + 0.04), 'white', fid + '_rim', bev=0.015)
        if k:
            hg = bk((x0 + 0.07, 0.57, z0 + 0.07), (x1 - 0.07, PK['hedge'], z1 - 0.07), 'hedge', fid + '_hedge', bev=0.07, bottom=False); hedge_uv(hg)
        else:
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            o = TR.lump((cx, 0.6, cz), ((x1 - x0) / 2 - 0.08, 0.2, (z1 - z0) / 2 - 0.08), M, fid + '_bed', seg=8, rings=4); uv_fit(o, A, 'leafbed'); P.append(o)
            TR.kill_faces(o, lambda c, n: c.y < 0.57)
            for i in range(8):
                a = TAU * i / 7 + rnd.uniform(-0.2, 0.2); rr = 0 if i == 7 else rnd.uniform(0.3, 0.48)
                fx, fz = cx + math.cos(a) * rr, cz + math.sin(a) * rr
                o = ball(0.11, (fx, 0.78 - rr * 0.18, fz), M, scale=(1, 0.7, 1), seg=6, rings=3, name=fid + '_flower'); uv_fit(o, A, ['petal', 'flowery', 'flowerw', 'petal'][i % 4]); P.append(o)
    # ---- the fountain: a tiled basin with a white coping, the water, a pedestal and bowl, a falling curtain, a blossom on top
    F = PK['fountain']; r, w = F['r'], F['rim']
    o = ring_prism(fid + '_basin', M, (r, 0.35), (r - w, 0.25), ZY - 0.01, F['h'] - 0.06); TR.uv_region(o, cellrect(A, 'tile'), A.w, A.h, proj='box', ppm=26); P.append(o)
    o = ring_prism(fid + '_coping', M, (r + 0.05, 0.37), (r - w - 0.04, 0.24), F['h'] - 0.06, F['h'] + 0.03, bottom=True); uv_fit(o, A, 'white'); P.append(o)
    o = cham_disc(fid + '_floor', M, r - w + 0.02, 0.25, F['floor']); uv_fit(o, A, 'floor'); P.append(o)
    o = cham_disc(fid + '_water', GZ, r - w + 0.01, 0.25, F['h'] - 0.17); uv_fit(o, A, 'water1'); P.append(o)
    o = lathe([(0.32, F['floor'] - 0.02), (0.32, 0.2), (0.22, 0.3), (0.16, 0.6), (0.13, 1.0), (0.2, 1.1)], (0, 0, 0), M, seg=12, axis='y', name=fid + '_ped'); uv_fit(o, A, 'white'); P.append(o)
    o = lathe([(0.12, 1.06), (0.5, 1.14), (0.78, 1.28), (0.8, 1.35), (0.72, 1.35), (0.45, 1.27), (0.0, 1.25)], (0, 0, 0), M, seg=14, axis='y', name=fid + '_bowl', cap=False); uv_fit(o, A, 'white'); P.append(o)
    o = cyl(0.72, 0.01, (0, 1.31, 0), GZ, axis='y', seg=14, name=fid + '_bowlwater', cap=True); uv_fit(o, A, 'water1'); P.append(o)
    o = lathe([(0.79, 1.3), (0.81, 1.0), (0.84, F['h'] - 0.17)], (0, 0, 0), GZ, seg=14, axis='y', name=fid + '_curtain', cap=False); uv_fit(o, A, 'water1'); P.append(o)
    o = lathe([(0.1, 1.24), (0.08, 1.48), (0.12, 1.54), (0.05, 1.6)], (0, 0, 0), M, seg=8, axis='y', name=fid + '_spout'); uv_fit(o, A, 'white'); P.append(o)
    for i in range(5):  # the blossom finial: five fat petals tipped up round a yellow middle
        a = TAU * i / 5
        o = ball(0.19, (math.cos(a) * 0.16, 1.7, math.sin(a) * 0.16), M, scale=(1.0, 0.32, 0.62), seg=8, rings=4, name=fid + '_petal',
                 rot=(0, -a, 0.35)); uv_fit(o, A, 'petal'); P.append(o)
    o = ball(0.08, (0, 1.76, 0), M, seg=8, rings=4, name=fid + '_pistil'); uv_fit(o, A, 'flowery'); P.append(o)
    # ---- benches: honey slats on cast-iron ends, armrests
    L_, D_, st, bt, bh = PK['bench']
    prof = [(0.27, 0.0), (0.2, 0.0), (0.16, 0.36), (-0.12, 0.36), (-0.16, 0.0), (-0.24, 0.0), (-0.21, 0.4), (-0.27, 0.93), (-0.21, 0.96),
            (-0.14, 0.48), (0.24, 0.44), (0.29, 0.42)]
    for bx_, bz_, f in PK['benches']:
        parts = []
        for sx in (-1, 1):
            o = side(prof, 0.05, (sx * (L_ / 2 - 0.1), 0, 0), M, name=fid + '_benchend'); tri_ngons(o); uv_fit(o, A, 'iron'); parts.append(o)
            parts.append(rod((sx * (L_ / 2 - 0.1), 0.43, 0.25), (sx * (L_ / 2 - 0.1), 0.66, 0.24), 0.022, M, seg=6, name=fid + '_armpost'))
            parts.append(rod((sx * (L_ / 2 - 0.1), 0.66, 0.29), (sx * (L_ / 2 - 0.1), 0.7, -0.16), 0.026, M, seg=6, name=fid + '_arm'))
            for p in parts[-2:]: uv_fit(p, A, 'iron')
        for zz, yy in ((0.21, 0.455), (0.09, 0.46), (-0.03, 0.465), (-0.15, 0.47)):
            o = box((L_ - 0.02, 0.035, 0.1), (0, yy, zz), M, name=fid + '_slat'); uv_fit(o, A, 'slat'); parts.append(o)
        tilt = math.atan(0.146)
        for t_ in (0.6, 0.73, 0.86):
            zc = -0.137 - (t_ - 0.48) * 0.146  # (half into the iron ends' back)
            o = box((L_ - 0.02, 0.1, 0.03), (0, t_, zc), M, rot=(-tilt, 0, 0), name=fid + '_back'); uv_fit(o, A, 'slat'); parts.append(o)
        P += turn_place(parts, bench_xf(f), (bx_, bz_))
    # ---- lamps: an iron post, a glowing globe, a pink banner on an arm toward the path
    for (lx, lz), arm in zip(PK['lamps'], ((0, 1), (0, -1), (1, 0))):
        o = lathe([(0.17, -0.02), (0.17, 0.12), (0.1, 0.2), (0.07, 0.5), (0.055, 3.0), (0.09, 3.04), (0.09, 3.1)], (lx, 0, lz), M, seg=8, axis='y', name=fid + '_post'); uv_fit(o, A, 'iron'); P.append(o)
        o = ball(0.21, (lx, 3.3, lz), GL, seg=10, rings=6, name=fid + '_globe'); uv_fit(o, A, 'white'); P.append(o)
        o = lathe([(0.25, 3.46), (0.18, 3.56), (0.04, 3.66)], (lx, 0, lz), M, seg=8, axis='y', name=fid + '_cap'); uv_fit(o, A, 'iron'); P.append(o)
        o = ball(0.05, (lx, 3.69, lz), M, seg=6, rings=4, name=fid + '_knob'); uv_fit(o, A, 'gold'); P.append(o)
        o = rod((lx, 3.06, lz), (lx, 3.14, lz), 0.1, M, seg=8, name=fid + '_collar'); uv_fit(o, A, 'gold'); P.append(o)
        ax_, az_ = arm
        o = rod((lx, 2.6, lz), (lx + ax_ * 0.62, 2.6, lz + az_ * 0.62), 0.018, M, seg=5, name=fid + '_barm'); uv_fit(o, A, 'iron'); P.append(o)
        bl0, bh0 = (lx + ax_ * 0.12, 1.75, lz + az_ * 0.12), (lx + ax_ * 0.56, 2.605, lz + az_ * 0.56)
        o = bk((min(bl0[0], bh0[0]) - (0.012 if ax_ == 0 else 0), bl0[1], min(bl0[2], bh0[2]) - (0.012 if az_ == 0 else 0)),
               (max(bl0[0], bh0[0]) + (0.012 if ax_ == 0 else 0), bh0[1], max(bl0[2], bh0[2]) + (0.012 if az_ == 0 else 0)), 'banner', fid + '_banner')
        uv_fit(o, A, 'pinkpaint', sel=lambda p, Pp: abs(MK._gn(p.normal).y) > 0.5)
    # ---- the gate: pink pillars on white plinths, a tie beam, the PETAL PARK board, an arched cherry-red lintel
    G = PK['arch']; gx, gt = G['x'], G['t']
    for s_ in (-1, 1):
        z0, z1 = sorted((s_ * G['z0'], s_ * G['z1']))
        bk((gx - gt - 0.06, -0.02, z0 - 0.06), (gx + gt + 0.06, 0.5, z1 + 0.06), 'white', fid + '_plinth', bev=0.02, bottom=False)
        bk((gx - gt, 0.5, z0), (gx + gt, G['h'], z1), 'pinkpaint', fid + '_pillar', bev=0.03)
        bk((gx - gt - 0.05, G['h0'] - 0.3, z0 - 0.05), (gx + gt + 0.05, G['h0'] - 0.18, z1 + 0.05), 'white', fid + '_collar', bev=0.01)
    bk((gx - 0.12, G['h0'], -G['z0']), (gx + 0.12, G['h0'] + 0.2, G['z0']), 'pinkpaint', fid + '_tie', bev=0.015)
    sg = bk((gx - 0.06, G['h0'] + 0.24, -G['z0']), (gx + 0.06, G['h0'] + 0.24 + 0.66, G['z0']), 'sign', fid + '_sign', bev=0.008)
    uv_fit(sg, A, 'cherry', sel=lambda p, Pp: abs(MK._gn(p.normal).x) < 0.5)
    bk((gx - 0.08, G['h0'] + 0.9, -G['z0']), (gx + 0.08, G['h'], G['z0']), 'pinkpaint', fid + '_post2', bev=0.01)
    # the lintel: a bar along z, its middle sprung up (an arch), the ends flicked up a little more
    lin = box((0.56, 0.3, 2 * G['hz']), (gx, G['h'] + 0.15, 0), M, name=fid + '_lintel'); TR.bake_tf(lin)
    bm = bmesh.new(); bm.from_mesh(lin.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 1, 0))
    for zc in (-2.0, -1.0, 1.0, 2.0): bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, -zc, 0), plane_no=(0, 1, 0))
    for v in bm.verts:
        z = -v.co.y; t_ = z / G['hz']
        v.co.z += 0.2 * (1 - t_ * t_) + 0.16 * max(0.0, abs(t_) - 0.7) / 0.3
    bm.to_mesh(lin.data); bm.free(); lin.data.update(); tri_ngons(lin); uv_fit(lin, A, 'cherry'); P.append(lin)
    for s_ in (-1, 1):  # gold knobs on the lintel's flicked-up ends
        zf = s_ * (G['hz'] - 0.25); t_ = zf / G['hz']; yt = G['h'] + 0.3 + 0.2 * (1 - t_ * t_) + 0.16 * max(0.0, abs(t_) - 0.7) / 0.3
        o = ball(0.17, (gx, yt + 0.13, zf), M, seg=10, rings=6, name=fid + '_finial'); uv_fit(o, A, 'gold'); P.append(o)
    # ---- the tea kiosk in the south-west corner: a pink booth, its hatch and counter toward the plaza under a striped
    # awning, a menu on the side, cups out, PETAL TEA on the roof's edge and a giant teacup up there
    x0, z0, x1, z1, kh = PK['kiosk']; zm = (z0 + z1) / 2; fx = x1 - 0.35
    bk((x0, -0.02, z0), (fx, kh - 0.25, z1), 'pinkpaint', fid + '_kbody', bev=0.02, bottom=False)
    bk((fx - 0.02, -0.02, z0), (x1, 1.0, z1), 'cream', fid + '_kcounter', bev=0.015, bottom=False)
    bk((fx - 0.05, 1.0, z0 - 0.05), (x1 + 0.1, 1.08, z1 + 0.05), 'white', fid + '_ktop', bev=0.012)
    for za, zb in ((z0, z0 + 0.16), (z1 - 0.16, z1)): bk((fx - 0.02, 1.08, za), (x1 - 0.12, kh - 0.25, zb), 'pinkpaint', fid + '_kpost')
    bk((fx - 0.03, 1.08, z0 + 0.16), (fx + 0.01, kh - 0.26, z1 - 0.16), 'iron', fid + '_khatch')
    bk((x0 - 0.1, kh - 0.25, z0 - 0.1), (x1 + 0.1, kh, z1 + 0.1), 'white', fid + '_kroof', bev=0.02)
    aw = box_between((x1 + 0.08, kh - 0.3, zm), (x1 + 0.85, kh - 0.72, zm), z1 - z0 + 0.3, 0.04, M, fid + '_awning'); uv_fit(aw, A, 'stripeh'); P.append(aw)
    bk((x1 + 0.82, kh - 0.98, z0 - 0.15), (x1 + 0.86, kh - 0.7, z1 + 0.15), 'stripev', fid + '_valance')
    for zz in (z0 + 0.1, z1 - 0.1): P.append(rod((x1 - 0.14, kh - 0.9, zz), (x1 + 0.6, kh - 0.62, zz), 0.02, M, seg=5, name=fid + '_kbrace')); uv_fit(P[-1], A, 'iron')
    bk((x0 + 0.25, 1.15, z1 - 0.01), (fx - 0.25, 2.05, z1 + 0.03), 'menu', fid + '_menu', bev=0.006)
    sg2 = bk((x1 - 0.05, kh, z0 + 0.15), (x1 + 0.03, kh + 0.5, z1 - 0.15), 'ksign', fid + '_ksign', bev=0.006)
    uv_fit(sg2, A, 'pinkpaint', sel=lambda p, Pp: MK._gn(p.normal).x < 0.5)
    for i, zz in enumerate((zm - 0.5, zm, zm + 0.45)):  # cups out on the counter
        o = lathe([(0.04, 1.08), (0.055, 1.18), (0.0, 1.17)], (x1 - 0.08, 0, zz), M, seg=7, axis='y', name=fid + '_kcup'); uv_fit(o, A, 'white'); P.append(o)
    cx, cz, cr, ch = PK['cup']  # the roof's teacup: a saucer, the cup, pink tea, a handle
    o = lathe([(0.0, kh - 0.01), (0.56, kh + 0.01), (0.62, kh + 0.08), (0.52, kh + 0.06), (0.0, kh + 0.05)], (cx, 0, cz), M, seg=14, axis='y', name=fid + '_saucer'); uv_fit(o, A, 'white'); P.append(o)
    o = lathe([(0.2, kh + 0.04), (0.36, kh + 0.14), (0.44, kh + 0.34), (0.47, kh + ch), (0.42, kh + ch), (0.38, kh + 0.33)], (cx, 0, cz), M, seg=14, axis='y', name=fid + '_teacup', cap=False); uv_fit(o, A, 'white'); P.append(o)
    o = cyl(0.39, 0.02, (cx, kh + 0.38, cz), M, axis='y', seg=14, name=fid + '_tea'); uv_fit(o, A, 'tea'); P.append(o)
    from make_portjankton import ring
    P.append(ring((cx + 0.5, kh + 0.3, cz), 0.13, 0.035, M, A, 'white', fid + '_handle', axis='z', n=10))
    o = lathe([(0.452, kh + 0.37), (0.468, kh + 0.4), (0.462, kh + 0.43)], (cx, 0, cz), M, seg=14, axis='y', name=fid + '_band2', cap=False); uv_fit(o, A, 'pinkpaint'); P.append(o)
    # ---- the sign on the hedge's end: two posts, the board facing the gate
    S_ = PK['sign']
    for zz in (S_['z0'] + 0.18, S_['z1'] - 0.18):
        o = rod((S_['x'] + 0.05, 0.55, zz), (S_['x'] + 0.05, S_['y1'] - 0.02, zz), 0.028, M, seg=6, name=fid + '_spost'); uv_fit(o, A, 'white'); P.append(o)
    jb = bk((S_['x'] - 0.02, S_['y0'] + 0.08, S_['z0']), (S_['x'] + 0.03, S_['y1'], S_['z1']), 'joke', fid + '_joke', bev=0.006)
    uv_fit(jb, A, 'pinkpaint', sel=lambda p, Pp: MK._gn(p.normal).x > -0.5)
    for p in P: lib.smooth(p, 35)
    # ---- lod1: the paving as plain slabs, the planters as blocks, the basin, the gate
    bk((-pl - bw, 0.0, -pl - bw), (pl + bw, 0.1, pl + bw), 'pave1', fid + '1_plaza', far=True, bottom=False)
    for lo, hi in (((-ex, 0.0, -pw - kw), (-pl - bw + 0.02, 0.08, pw + kw)), ((pl + bw - 0.02, 0.0, -pw - kw), (ex, 0.08, pw + kw)),
                   ((-pw - kw, 0.0, -ez), (pw + kw, 0.08, -pl - bw + 0.02)), ((-pw - kw, 0.0, pl + bw - 0.02), (pw + kw, 0.08, ez))):
        bk(lo, hi, 'terra1', fid + '1_path', far=True, bottom=False)
    for x0, z0, x1, z1, k in PK['planters']:
        o = bk((x0 - 0.03, 0.0, z0 - 0.03), (x1 + 0.03, PK['hedge'] if k else 0.8, z1 + 0.03), 'cream', fid + '1_planter', far=True, bottom=False)
        uv_fit(o, A, 'leafbed' if k else 'petal', sel=lambda p, Pp: MK._gn(p.normal).y > 0.5)
    o = TR.bake_tf(lathe([(r + 0.04, 0.0), (r + 0.04, F['h'] + 0.03), (0.3, F['h'] - 0.17), (0.25, 1.5), (0.0, 1.85)], (0, 0, 0), M, seg=8, axis='y', name=fid + '1_fountain', cap=False))
    uv_fit(o, A, 'water1'); Q.append(o)
    for s_ in (-1, 1):
        z0, z1 = sorted((s_ * G['z0'], s_ * G['z1']))
        bk((gx - gt, 0.0, z0), (gx + gt, G['h'], z1), 'pinkpaint', fid + '1_pillar', far=True, bottom=False)
    o = bk((gx - 0.2, G['h0'], -G['hz']), (gx + 0.2, G['h1'], G['hz']), 'sign', fid + '1_head', far=True)
    uv_fit(o, A, 'cherry', sel=lambda p, Pp: abs(MK._gn(p.normal).x) < 0.5)
    for p in P + Q: tri_ngons(p)
    bx = park_boxes(); lo = tuple(min(b[0][i] for b in bx) for i in range(3)); hi = tuple(max(b[1][i] for b in bx) for i in range(3))
    return dict(lod0=P, lod1=Q, box=(lo, hi), ao=0.7, aolo=0.5, lod=110, eps=0.001, sheet=dict(exposure=-1.2),
                focus=[((0, 1.0, 0), (0.7, 0.45, 1.0), 6.0), ((-13, 2.5, 0), (-1.0, 0.1, 0.3), 9.0), ((-2.4, 0.5, -4.35), (0.2, 0.3, 1.0), 2.6),
                       ((-6.3, 2.3, -1.5), (0.6, 0.1, 1.0), 4.0), ((4.0, 0.7, 4.0), (0.6, 0.6, 1.0), 3.5), ((-11.3, 2.0, 9.3), (1.0, 0.35, -0.45), 6.5)])


def cellrect(A, key):
    """an atlas cell as make_trees' (r0, r1, c0, c1) rect"""
    x0, y0, x1, y1 = A.r[key]
    return (y0, y1, x0, x1)


# ------------------------------------------------------------ main
if __name__ == '__main__':
    todo = [(f, fn) for f, fn in PROPS if not ONLY or f[5:] in ONLY or f[2:] in ONLY or f in ONLY]
    for fid, fn in todo:
        run_bi(fid, fn)
