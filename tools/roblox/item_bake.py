# ITEM BAKE: a gadget skin's rich surface (owner, 18 Nov 2026, of the first Bento Box: "bento box doesnt look very
# good"; main: a legendary skin needs "a rich surface ... rather than flat fills"). Headless Blender 5.3, Cycles CPU.
#
#   blender -b --factory-startup -P tools/roblox/item_bake.py -- <out_dir> <key> [--name=<file>.glb] [--sheet]
#
# A skin builder (tools/roblox/item_skins.py) that sets g.bake = {'pieces': [nodes], 'paint': <name>} gets:
#   - its baked pieces unfolded into ONE 1024 atlas (artist_kit.atlas_uvs: flat projections by facing, turned to pack)
#   - Cycles bakes over them (the other pieces still occlude): the flat colours, the AO, how much each texel looks up,
#     its height in its piece, a convex-edge mask (an AO taken inside the solid), a short crease AO, its position and
#     normal (so paint rules and motifs can be laid in the item's own frame)
#   - a PAINTER (PAINTERS below, by name) that turns those into the albedo, the roughness and a relief height (raised
#     maki-e, rice grains): each skin's own colours by rule and its motifs as smooth signed-distance shapes
#   - a tangent NormalMap baked from a Bevel node (soft rounded edges) over a Bump of the relief
#   - the ColorMap composed like artist_kit's bake (AO and a top-down light multiplied over the albedo, a light line
#     on convex edges, gold lit like a metal), every map padded out from its islands
# and writes K_color.png (sRGB), K_normal.png and K_rough.png (linear) next to the upload glb. Run bake_guard.py on
# the normal and rough maps, then look at every map at full size before uploading (the upload rules: no text, nothing
# letter-like, no barcode or QR-like mosaics).
#
# The upload (export_baked): every piece in the item frame at UNIT scale, named "<key>_<node>__<look>"; the baked pieces
# keep the atlas UVs (the import gives them a SurfaceAppearance with the maps and NoWrap: a wrap leaves them alone),
# pieces in g.own_uv keep their own UVs (the Bento's cloth: the wrap scale, a tiling cloth picture), the rest get the
# wrap unfold. The json carries 'bake' (the baked pieces and the map files) for item_skin_import.luau.
import bpy, bmesh, sys, os, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mathutils import Vector, Matrix
import artist_kit as AK
import gunkit

ATLAS = 1024
SAMPLES = 64
AO_D = 0.03          # the AO's reach over a gadget (metres)
EDGE_D = 0.0022      # the convex-edge finder's reach
BEVEL_R = 0.0016     # the NormalMap's rounded edges
RELIEF_D = 0.00045   # how proud the relief stands (maki-e gold)
PADN = 120           # texels every island's values are pushed out into the gaps (no hard island shapes in the maps)


def lin_hex(h): return np.array([gunkit.lin(c) for c in gunkit.hex_rgb(h)], dtype=np.float32)


def smooth01(x): x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)


# ------------------------------------------------------------------------------------------------ signed distances
def sd_circle(u, v, cu, cv, r): return np.hypot(u - cu, v - cv) - r


def sd_seg(u, v, a, b):
    pu, pv = u - a[0], v - a[1]
    bu, bv = b[0] - a[0], b[1] - a[1]
    h = np.clip((pu * bu + pv * bv) / max(bu * bu + bv * bv, 1e-12), 0, 1)
    return np.hypot(pu - bu * h, pv - bv * h), h


def blossom(u, v, cu, cv, r, rot=0.0):
    """a five-petal plum blossom r across its petals' tips: (the flower's sd, the petal outlines' sd, the eye's sd)"""
    rp = r * 0.42
    d = np.full(u.shape, 1e9, np.float32)
    rims = np.full(u.shape, 1e9, np.float32)
    for k in range(5):
        a = rot + k * 2 * math.pi / 5
        dk = sd_circle(u, v, cu + math.cos(a) * (r - rp), cv + math.sin(a) * (r - rp), rp)
        rims = np.minimum(rims, np.abs(dk))
        d = np.minimum(d, dk)
    eye = sd_circle(u, v, cu, cv, r * 0.2)
    return d, rims, eye


def branch(u, v, pts, w0, w1):
    """a branch along a polyline, w0 wide at its start tapering to w1"""
    d = np.full(u.shape, 1e9, np.float32)
    n = len(pts) - 1
    for i in range(n):
        dd, h = sd_seg(u, v, pts[i], pts[i + 1])
        t = (i + h) / n
        d = np.minimum(d, dd - (w0 + (w1 - w0) * t) / 2)
    return d


# ------------------------------------------------------------------------------------------------ painters
def paint_bento(m):
    """the Bento Box: black lacquer outside, vermilion inside (the top tier's walls, floor and dividers, the seam's lip,
       the lid's underside), gold inlay lines round the tiers and the lid, gold plum branches on the lid's panel, both
       long sides and the ends, vermilion chopsticks with a gold band; the food its own colours, grainy rice"""
    Pp, N, node, A = m['P'], m['N'], m['node'], m['A']
    x, y, z = Pp[..., 0], Pp[..., 1], Pp[..., 2]
    nx, ny, nz = N[..., 0], N[..., 1], N[..., 2]
    H, W = x.shape
    alb = A.copy()
    rough = np.full((H, W), 0.5, np.float32)
    relief = np.zeros((H, W), np.float32)
    gold = np.zeros((H, W), np.float32)
    X, Z, RC = 0.122, 0.066, 0.026
    def rr_in(hx, hz, rc):   # signed distance to a rounded rectangle seen from above (negative inside)
        qx, qz = np.abs(x) - (hx - rc), np.abs(z) - (hz - rc)
        return np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - rc
    BLACK, SHU_, GOLD_ = lin_hex('2b2527'), lin_hex('8a3a2e'), lin_hex('a88f58')
    body, lid, sticks = node == 'body', node == 'lid', node == 'lidsticks'
    lacq = body | lid
    alb[lacq] = BLACK
    rough[lacq] = 0.2
    # vermilion: the top tier's inside (walls, floor, dividers) below its lip, the seam's lip, the lid's underside
    inside = body & (rr_in(X - 0.0052, Z - 0.0052, RC - 0.0052) < 0) & (y > 0.0035) & (y < 0.0372)
    seam = body & (y > -0.0257) & (y < -0.0178) & (rr_in(X - 0.0025, Z - 0.0025, RC - 0.0025) > -0.0015)
    under = lid & (ny < -0.6) & (y < 0.0425)
    red = inside | seam | under
    alb[red] = SHU_
    rough[red] = 0.28
    # gold inlay lines: round each tier near its top, round the lid's foot, along the lid's rim top
    outer = (rr_in(X, Z, RC) > -0.0035) & (np.abs(ny) < 0.5)
    lines = np.zeros((H, W), np.float32)
    for yc, wd in ((-0.0335, 0.0016), (0.0302, 0.0016), (0.0478, 0.0014)):
        lines = np.maximum(lines, smooth01((wd / 2 - np.abs(y - yc)) / 0.0005 + 0.5))
    lines *= (lacq & outer)
    rim = lid & (ny > 0.8) & (y > 0.0738) & (np.abs(rr_in(X - 0.005, Z - 0.005, RC - 0.005)) < 0.0007)
    lines = np.maximum(lines, rim * 1.0)
    # the plum branches: (face test, (u, v) in metres on that face, [branch polylines], [(u, v, r, turn)])
    motif = np.zeros((H, W), np.float32)
    eyes = np.zeros((H, W), np.float32)
    rims_m = np.zeros((H, W), np.float32)
    def lay(sel, u, v, branches, flowers, buds=()):
        nonlocal motif, eyes, rims_m
        if not sel.any(): return
        uu, vv = u[sel], v[sel]
        d = np.full(uu.shape, 1e9, np.float32)
        for pts, w0, w1 in branches:
            d = np.minimum(d, branch(uu, vv, pts, w0, w1))
        fl = np.full(uu.shape, 1e9, np.float32); rm = np.full(uu.shape, 1e9, np.float32); ey = np.full(uu.shape, 1e9, np.float32)
        for (cu, cv, r, rot) in flowers:
            f, rr, e = blossom(uu, vv, cu, cv, r, rot)
            fl = np.minimum(fl, f); rm = np.minimum(rm, np.where(f < 0, rr, 1e9)); ey = np.minimum(ey, e)
        for (cu, cv, r) in buds:
            fl = np.minimum(fl, sd_circle(uu, vv, cu, cv, r))
        d = np.minimum(d, fl)
        px = 0.00035   # (about half a texel: soft shape edges)
        motif[sel] = np.maximum(motif[sel], smooth01(0.5 - d / px))
        rims_m[sel] = np.maximum(rims_m[sel], smooth01(0.5 - (rm - 0.00025) / px) * (fl < 0))
        eyes[sel] = np.maximum(eyes[sel], smooth01(0.5 - ey / px))
    # the lid's panel, each side of the band (the band covers |x| < 0.025): two sprigs turned half a turn apart
    pan = lid & (ny > 0.8) & (y < 0.0700)
    for s in (-1, 1):
        lay(pan & (s * x > 0.02), s * x, -s * z,
            [([(0.105, -0.05), (0.088, -0.03), (0.072, -0.016), (0.052, 0.006), (0.036, 0.02)], 0.0024, 0.0011),
             ([(0.072, -0.016), (0.084, 0.004), (0.09, 0.016)], 0.0014, 0.0008)],
            [(0.088, -0.03, 0.0085, 0.2), (0.052, 0.006, 0.0072, 0.9), (0.09, 0.016, 0.006, 0.5), (0.098, -0.046, 0.005, 1.4)],
            [(0.036, 0.021, 0.0022), (0.066, -0.002, 0.0018)])
    # the long sides (the back faces first person), a sweeping branch over each tier
    for sz in (-1, 1):
        face = (body) & (sz * nz > 0.75) & (rr_in(X, Z, RC) > -0.002)
        u = sz * x   # (seen from outside, u runs left to right)
        for (y0, y1, mid) in ((-0.081, -0.026, -0.056), (-0.016, 0.036, 0.0075)):
            sel = face & (y > y0) & (y < y1)
            lay(sel, u, y - mid,
                [([(-0.112, -0.0144), (-0.085, -0.0058), (-0.055, 0.0), (-0.02, 0.0022), (0.01, -0.0014), (0.04, 0.0043), (0.07, 0.0101)], 0.0026, 0.001),
                 ([(-0.055, 0.0), (-0.046, 0.0094), (-0.04, 0.013)], 0.0014, 0.0008)],
                [(-0.085, -0.0058, 0.0088, 0.3), (-0.04, 0.0126, 0.0068, 1.1), (-0.008, 0.0014, 0.0078, 0.7),
                 (0.04, 0.0043, 0.0066, 0.1), (0.07, 0.0108, 0.0058, 1.3)],
                [(-0.02, -0.0043, 0.0022), (0.088, 0.0115, 0.0018), (0.022, 0.0086, 0.002)])
    # the ends: one blossom and a twig on each tier
    for sx in (-1, 1):
        face = body & (sx * nx > 0.75)
        for (y0, y1, mid) in ((-0.081, -0.026, -0.056), (-0.016, 0.036, 0.0075)):
            sel = face & (y > y0) & (y < y1)
            lay(sel, -sx * z, y - mid, [([(-0.04, -0.018), (-0.012, -0.004), (0.01, 0.006)], 0.002, 0.0009)],
                [(-0.012, -0.004, 0.0085, 0.4), (0.016, 0.01, 0.006, 1.0)], [(0.032, 0.016, 0.002)])
    g = np.maximum(lines, motif * (lacq & ~red))
    gold = np.maximum(gold, g)
    relief = np.maximum(relief, g)
    # the chopsticks: vermilion, a gold band near the thick end, darker tips
    alb[sticks] = SHU_
    rough[sticks] = 0.26
    band = sticks & (x > 0.066) & (x < 0.0715)
    gold = np.maximum(gold, band * 1.0)
    tip = sticks & (x < -0.074)
    alb[tip] = BLACK
    # the food: its own colours (the slots), rice grains, the omelette browned on top
    food = node == 'food'
    rice = food & (np.abs(alb[..., 0] - lin_hex('e9e5da')[0]) < 0.02) & (np.abs(alb[..., 2] - lin_hex('e9e5da')[2]) < 0.02)
    rough[food] = 0.55
    rough[rice] = 0.7
    gr = np.zeros((H, W), np.float32)
    for k in range(5):   # (grains: overlapping soft ellipses on a jittered lattice in the item frame)
        f = 2 * math.pi / 0.0045 * (1 + 0.37 * k)
        gr += np.sin(x * f + k * 1.7 + np.sin(z * f * 0.61 + k)) * np.sin(z * f * 0.83 + k * 2.3 + np.cos(x * f * 0.5))
    relief[rice] = np.clip(0.5 + 0.12 * gr[rice], 0, 1) * 0.6
    # black sesame on the rice: a few dozen specks scattered (a fixed scatter, no grid)
    rng = np.random.default_rng(3)
    sp = np.zeros((H, W), np.float32)
    top_r = rice & (ny > 0.7)
    for _ in range(26):
        cx_, cz_ = rng.uniform(-0.108, 0.006), rng.uniform(-0.052, 0.05)
        a_ = rng.uniform(0, math.pi)
        du, dv = x - cx_, z - cz_
        q = np.hypot((du * math.cos(a_) + dv * math.sin(a_)) / 0.0016, (-du * math.sin(a_) + dv * math.cos(a_)) / 0.0009)
        sp = np.maximum(sp, smooth01((1 - q) * 3))
    sp *= top_r
    alb = alb * (1 - sp[..., None]) + lin_hex('2a2624') * sp[..., None]
    egg = food & (alb[..., 1] > lin_hex('cfae5c')[1] * 0.9) & (alb[..., 2] < 0.2) & ~rice
    top = egg & (ny > 0.6)
    alb[top] = alb[top] * 0.82 + lin_hex('a8803f') * 0.18
    # gold over everything it covers; the eye of each blossom (lacquer showing) and the petals' fine outlines
    G = gold[..., None]
    alb = alb * (1 - G) + GOLD_ * G
    dk = np.clip(eyes * 0.75 + rims_m * 0.5, 0, 1)[..., None] * (G > 0.5)
    alb = alb * (1 - dk) + (alb * 0.45) * dk
    rough = rough * (1 - gold) + 0.3 * gold
    return {'albedo': alb, 'rough': rough, 'relief': relief, 'gold': gold}


PAINTERS = {'bento': paint_bento}


# ------------------------------------------------------------------------------------------------ the bake
def bake(g, out_dir, tag):
    """bake g (built, not yet in a scene) as described at the top. Returns (objects, baked objects, info); the scene
       is left holding the item in metres with the atlas UVs on the baked pieces"""
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES
    objs = g.to_scene()
    keys = list(g.pieces.keys())
    for o, (node, slot) in zip(objs, keys): o['node'] = node; o['slot'] = slot
    want = set(g.bake['pieces'])
    baked = [o for o in objs if o['node'] in want]
    for i, o in enumerate(baked): o.pass_index = i + 1
    density, used, over = AK.atlas_uvs(baked, rotate=True)
    w = bpy.data.worlds.new('w'); sc.world = w; w.light_settings.distance = AO_D
    bpy.ops.object.select_all(action='DESELECT')
    for o in baked: o.select_set(True)
    bpy.context.view_layer.objects.active = baked[0]
    imgs = {k: bpy.data.images.new(k, ATLAS, ATLAS, float_buffer=True) for k in ('cover', 'albedo', 'mask1', 'mask2', 'pos', 'nrm', 'pid')}

    def albedo(nodes, links, m):
        rgb = nodes.new('ShaderNodeRGB')
        rgb.outputs[0].default_value = m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
        return rgb.outputs[0]

    def mask1(nodes, links, m):
        a = nodes.new('ShaderNodeAmbientOcclusion'); a.samples = 16; a.inputs['Distance'].default_value = AO_D
        geo = nodes.new('ShaderNodeNewGeometry')
        sn = nodes.new('ShaderNodeSeparateXYZ'); links.new(geo.outputs['Normal'], sn.inputs[0])
        up = nodes.new('ShaderNodeMapRange'); up.inputs['From Min'].default_value = -1; up.inputs['From Max'].default_value = 1
        links.new(sn.outputs['Z'], up.inputs['Value'])
        tc = nodes.new('ShaderNodeTexCoord'); sg = nodes.new('ShaderNodeSeparateXYZ')
        links.new(tc.outputs['Generated'], sg.inputs[0])
        c = nodes.new('ShaderNodeCombineXYZ')
        links.new(a.outputs['AO'], c.inputs['X']); links.new(up.outputs['Result'], c.inputs['Y']); links.new(sg.outputs['Z'], c.inputs['Z'])
        return c.outputs[0]

    def mask2(nodes, links, m):
        ai = nodes.new('ShaderNodeAmbientOcclusion'); ai.samples = 16; ai.inside = True; ai.only_local = True
        ai.inputs['Distance'].default_value = EDGE_D
        a = nodes.new('ShaderNodeAmbientOcclusion'); a.samples = 16; a.inputs['Distance'].default_value = 0.006
        c = nodes.new('ShaderNodeCombineXYZ')
        links.new(ai.outputs['AO'], c.inputs['X']); links.new(a.outputs['AO'], c.inputs['Y'])
        return c.outputs[0]

    def pos(nodes, links, m):
        geo = nodes.new('ShaderNodeNewGeometry'); return geo.outputs['Position']

    def nrm(nodes, links, m):
        geo = nodes.new('ShaderNodeNewGeometry')
        mp = nodes.new('ShaderNodeVectorMath'); mp.operation = 'MULTIPLY_ADD'
        links.new(geo.outputs['Normal'], mp.inputs[0]); mp.inputs[1].default_value = (0.5, 0.5, 0.5); mp.inputs[2].default_value = (0.5, 0.5, 0.5)
        return mp.outputs[0]

    def pid(nodes, links, m):
        oi = nodes.new('ShaderNodeObjectInfo')
        mt = nodes.new('ShaderNodeMath'); mt.operation = 'DIVIDE'; mt.inputs[1].default_value = 64.0
        links.new(oi.outputs['Object Index'], mt.inputs[0])
        c = nodes.new('ShaderNodeCombineXYZ'); links.new(mt.outputs[0], c.inputs['X'])
        return c.outputs[0]

    def cover(nodes, links, m):
        rgb = nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = (1, 1, 1, 1); return rgb.outputs[0]

    sc.cycles.samples = 1
    AK._bake_emit(baked, imgs['cover'], cover, margin=0)
    for k, fn in (('albedo', albedo), ('pos', pos), ('nrm', nrm)):
        AK._bake_emit(baked, imgs[k], fn)
    AK._bake_emit(baked, imgs['pid'], pid, margin=0)
    sc.cycles.samples = SAMPLES
    for k, fn in (('mask1', mask1), ('mask2', mask2)):
        AK._bake_emit(baked, imgs[k], fn)
    px = {k: AK._pixels(im) for k, im in imgs.items()}
    on = px['cover'][..., 0] > 0.5
    Pb = px['pos'][..., :3]
    Nb = px['nrm'][..., :3] * 2 - 1
    # (Blender -> the item frame: x, z, -y)
    Pi = np.stack([Pb[..., 0], Pb[..., 2], -Pb[..., 1]], axis=-1)
    Ni = np.stack([Nb[..., 0], Nb[..., 2], -Nb[..., 1]], axis=-1)
    ids = np.rint(px['pid'][..., 0] * 64).astype(np.int32)
    names = np.array([''] + [o['node'] for o in baked])
    node = names[np.clip(ids, 0, len(baked))]
    node[~on] = ''
    A = px['albedo'][..., :3]
    paint = PAINTERS[g.bake['paint']]({'P': Pi, 'N': Ni, 'node': node, 'A': A, 'on': on})
    # ---- the NormalMap: Bevel (soft edges) over a Bump of the relief, baked in tangent space
    rel = AK._pad(np.clip(paint['relief'], 0, 1)[..., None], on, n=6)[..., 0]
    rel = _blur(rel, 1.0)
    rimg = bpy.data.images.new('relief', ATLAS, ATLAS, float_buffer=True)
    rimg.colorspace_settings.name = 'Non-Color'
    rimg.pixels.foreach_set(np.ascontiguousarray(np.stack([rel, rel, rel, np.ones_like(rel)], axis=-1), dtype=np.float32).ravel())
    nimg = bpy.data.images.new('normal', ATLAS, ATLAS, float_buffer=True)
    nimg.colorspace_settings.name = 'Non-Color'
    keep = {}
    for o in baked:
        for i, m in enumerate(o.data.materials):
            t = keep.get(m.name)
            if t is None:
                t = m.copy(); keep[m.name] = t
                nt = t.node_tree
                bsdf = nt.nodes['Principled BSDF']
                tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = rimg; tx.interpolation = 'Cubic'
                bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Distance'].default_value = RELIEF_D
                bp.inputs['Strength'].default_value = 1.0
                nt.links.new(tx.outputs['Color'], bp.inputs['Height'])
                bv = nt.nodes.new('ShaderNodeBevel'); bv.samples = 16; bv.inputs['Radius'].default_value = BEVEL_R
                nt.links.new(bp.outputs['Normal'], bv.inputs['Normal'])
                nt.links.new(bv.outputs['Normal'], bsdf.inputs['Normal'])
                out = nt.nodes.new('ShaderNodeTexImage'); out.image = nimg; out.select = True; nt.nodes.active = out
            o.data.materials[i] = t
    sc.cycles.samples = 16
    bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=12, margin_type='EXTEND', use_clear=True)
    back = {t.name: bpy.data.materials[n] for n, t in keep.items()}
    for o in baked:
        for i, m in enumerate(o.data.materials): o.data.materials[i] = back[m.name]
    nrm_t = AK._pixels(nimg)[..., :3]
    # ---- the ColorMap
    M1, M2 = px['mask1'], px['mask2']
    aom, upf, hgt = M1[..., 0], M1[..., 1], M1[..., 2]
    inside, crease = M2[..., 0], M2[..., 1]
    edge = np.clip((0.86 - inside) / 0.5, 0, 1) ** 1.2
    shade = (1 - 0.55 * (1 - aom)) * (1 - 0.3 * (1 - crease))
    face = np.where(upf >= 0.5, 0.98 + 0.1 * ((upf - 0.5) * 2) ** 1.2, 0.98 - 0.2 * ((0.5 - upf) * 2) ** 1.2)
    mult = shade * face * (1 + 0.14 * (hgt - 0.5))
    alb = paint['albedo']
    lum = alb[..., 0] * 0.2126 + alb[..., 1] * 0.7152 + alb[..., 2] * 0.0722
    mult = 1 + (mult - 1) * (1 + 0.5 * np.clip((0.09 - lum) / 0.05, 0, 1) - 0.35 * np.clip((lum - 0.25) / 0.25, 0, 1))
    mult = np.clip(mult, 0.55, 1.15)
    gl = paint['gold'][..., None]
    # gold lit like a metal: brighter where it looks up, a warm sheen toward the light, darker in its folds
    gmult = (0.62 + 0.62 * np.clip(upf, 0, 1) ** 1.5)[..., None] * (0.65 + 0.35 * aom)[..., None]
    col_lin = alb * (mult[..., None] * (1 - gl) + gmult * gl)
    col = AK._srgb(col_lin)
    lift = edge * (0.16 * (1 - paint['gold']) + 0.3 * paint['gold'])
    col = col + (1 - col) * lift[..., None]
    one = np.ones(on.shape, np.float32)[..., None]
    base = os.path.join(out_dir, tag)
    AK._save_png(base + '_color.png', np.concatenate([AK._pad(np.clip(col, 0, 1), on, n=PADN), one], axis=2))
    nt_ = AK._pad(nrm_t, on, n=PADN)
    flat = ~_grow(on, PADN + 4)
    nt_[flat] = (0.5, 0.5, 1.0)
    AK._save_png(base + '_normal.png', np.concatenate([nt_, one], axis=2), 'Non-Color')
    rgh = AK._pad(np.clip(paint['rough'], 0.05, 1)[..., None], on, n=PADN)[..., 0]
    rgh = np.where(_grow(on, PADN + 4), rgh, 0.3)
    AK._save_png(base + '_rough.png', np.concatenate([np.stack([rgh] * 3, axis=-1), one], axis=2), 'Non-Color')
    for im in list(imgs.values()) + [rimg, nimg]: bpy.data.images.remove(im)
    info = {'atlas': ATLAS, 'texels_per_m': round(density, 1), 'atlas_used': round(used, 3), 'uv_overlap': round(over, 4),
            'pieces': [o['node'] for o in baked], 'maps': {k: tag + '_%s.png' % k for k in ('color', 'normal', 'rough')},
            'seconds': round(time.time() - t0, 1)}
    print('BAKED %s in %.1fs: %.0f texels/m, atlas %.0f%% used, %.2f%% overlap' % (tag, time.time() - t0, density, used * 100, over * 100))
    return objs, baked, info


def _blur(a, sigma):
    r = max(1, int(3 * sigma))
    k = np.exp(-(np.arange(-r, r + 1) ** 2) / (2 * sigma * sigma)); k /= k.sum()
    out = a.copy()
    for ax in (0, 1):
        out = sum(np.roll(out, i - r, axis=ax) * k[i] for i in range(2 * r + 1))
    return out


def _grow(m, n):
    out = m.copy()
    for _ in range(n):
        out = out | np.roll(out, 1, 0) | np.roll(out, -1, 0) | np.roll(out, 1, 1) | np.roll(out, -1, 1)
    return out


# ------------------------------------------------------------------------------------------------ the upload
def export_baked(key, out_dir, name):
    import item_skins as K
    import item_models2 as B
    import rbxglb, gun_uvs
    g = K.BUILD_SKINS[key]()
    tag = key.replace('@', '_')
    objs, baked, binfo = bake(g, out_dir, tag)
    lo, hi = g.bounds()
    own = getattr(g, 'own_uv', set())
    unf = [o for o in objs if o not in baked and o['node'] not in own]
    if unf: gun_uvs.unwrap(unf, B.UV_SCALE)
    for o in objs:
        o.matrix_world = Matrix.Diagonal(Vector((K.UNIT, K.UNIT, K.UNIT, 1.0)))
        o.name = '%s_%s__%s' % (key, o['node'], B.old.look(g.slots[o['slot']]))
    rbxglb.turn_for_roblox(objs)
    path = os.path.join(out_dir, name)
    size = rbxglb.export_glb(path, tangents=True)
    info = {key: {'lo': lo, 'hi': hi, 'tris': g.tris(), 'pieces': ['%s__%s' % k for k in g.pieces],
                  'grip': g.spots.get('grip'), 'gripRot': g.spots.get('gripRot'), 'wrap': K.SKIN_WRAP.get(key),
                  'name': K.SKINS[key][0], 'rarity': K.SKINS[key][1], 'skin': tag, 'item': key.split('@')[0],
                  'bake': binfo, 'own_uv': sorted(own)}}
    json.dump({'unit': K.UNIT, 'items': info}, open(os.path.join(out_dir, name.replace('.glb', '.json')), 'w'), indent=1)
    print('WROTE', path, size, 'bytes', g.tris(), 'tris')
    return path


def preview(key, out_dir, views=None, open_lid=False):
    """renders of the baked skin wearing its maps (and the cloth's tile if one is next to them), for the sheet"""
    import item_skins as K
    import item_sheet as S
    g = K.BUILD_SKINS[key]()
    tag = key.replace('@', '_')
    objs, baked, binfo = bake(g, out_dir, tag)
    base = os.path.join(out_dir, tag)
    ci = bpy.data.images.load(base + '_color.png')
    ni = bpy.data.images.load(base + '_normal.png'); ni.colorspace_settings.name = 'Non-Color'
    ri = bpy.data.images.load(base + '_rough.png'); ri.colorspace_settings.name = 'Non-Color'
    mat = bpy.data.materials.new('baked'); mat.use_nodes = True
    nt = mat.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexImage'); tc.image = ci; nt.links.new(tc.outputs['Color'], b.inputs['Base Color'])
    tr = nt.nodes.new('ShaderNodeTexImage'); tr.image = ri; nt.links.new(tr.outputs['Color'], b.inputs['Roughness'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = ni
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    for o in baked:
        o.data.materials.clear(); o.data.materials.append(mat)
    cloth = os.path.join(out_dir, 'cloth_tile_color.png')
    if os.path.exists(cloth):
        cm = bpy.data.materials.new('cloth'); cm.use_nodes = True
        cn = cm.node_tree; cb = cn.nodes['Principled BSDF']
        t1 = cn.nodes.new('ShaderNodeTexImage'); t1.image = bpy.data.images.load(cloth); cn.links.new(t1.outputs['Color'], cb.inputs['Base Color'])
        cb.inputs['Roughness'].default_value = 0.85
        cnp = os.path.join(out_dir, 'cloth_tile_normal.png')
        if os.path.exists(cnp):
            t2 = cn.nodes.new('ShaderNodeTexImage'); t2.image = bpy.data.images.load(cnp); t2.image.colorspace_settings.name = 'Non-Color'
            n2 = cn.nodes.new('ShaderNodeNormalMap'); cn.links.new(t2.outputs['Color'], n2.inputs['Color']); cn.links.new(n2.outputs['Normal'], cb.inputs['Normal'])
        for o in objs:
            if o['node'] in getattr(g, 'own_uv', set()):
                o.data.materials.clear(); o.data.materials.append(cm)
    if open_lid:   # (the game's swing: every lid* part about the lid's front bottom edge, -1.95 rad at full open)
        hz, hy = g.spots['hinge'][2], g.spots['hinge'][1]
        for o in objs:
            if o['node'].startswith('lid'):
                o.matrix_world = (Matrix.Translation((0, -hz, hy)) @ Matrix.Rotation(-1.95, 4, 'X') @ Matrix.Translation((0, hz, -hy))) @ o.matrix_world
    for view, vn in (views or ((S.FRONT, 'front'), (S.BACK, 'back'), (S.HAND, 'hand'))):
        if open_lid: vn = 'open_' + vn
        for c in [c for c in bpy.data.objects if c.type in ('CAMERA', 'LIGHT')]: bpy.data.objects.remove(c)
        S.render(g, os.path.join(out_dir, '%s_baked_%s.png' % (tag, vn)), view, objs=objs)


S_HAND = (0.25, -0.85, 0.75)

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out_dir, key = argv[0], argv[1]
    os.makedirs(out_dir, exist_ok=True)
    if '--sheet' in argv:
        preview(key, out_dir)
    elif '--open' in argv:
        preview(key, out_dir, views=((S_HAND, 'hand'), ((0.3, -0.55, 1.0), 'top')), open_lid=True)
    else:
        nm = ([a[7:] for a in argv[2:] if a.startswith('--name=')] or [key.replace('@', '_') + '_v2.glb'])[0]
        export_baked(key, out_dir, nm)
