# Anime muzzle flashes, rendered in Blender (the VFX session, 26 Nov 2026; round 2 after the critic's 5/10, round 1 is
# mflash_bl_r1.py). A flash shows ONE random cell of a 2x2 sheet for a few hundredths of a second (Fx: StartRandom,
# Framerate 0), so each cell is a complete drawing. Pure emitted light: no black ink (it read as soot); the anime two-tone
# is a deeper band of the same tint round every shape's rim (the body layer is two greys: 0.42 at the rim, 0.75 inside).
#   front  seen down the barrel: a soft-lobed hot core (3-5 lobes, no teeth) and 4-6 flame petals (base 25-35 % of their
#          length, concave sides), one or two of them dominant at 2-2.5x the others. The game turns it at random.
#   side   seen from the side, root at the left edge's middle, pointing +X: a gas JET pinched at the muzzle (at most 10 %
#          of the cell's height), blooming to 30-40 % of it at 20-35 % of its length, splitting into 2-3 points between
#          70 and 90 %; 1-2 short side petals near the muzzle; the white fills the bloom and the first 40 %. All four
#          share one length and bloom position (one flash, four versions of it).
# Layers: body (tinted, added + painted under), core (white, added). The ink layer is drawn empty (the sheet set stays
# three layers so the game's code is the same for every flipbook).
#
#   blender -b --factory-startup -P mflash_bl.py -- <spec.json>
# spec: {"out": dir, "view": "front"|"side", "px": 512, "ss": 2, "seed": 9, "variants": 4}
# writes <out>/mflash_<view>_<layer>_<v>.png
import json
import math
import os
import random
import sys

import bpy
import bmesh

spec = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
OUT = spec['out']
VIEW = spec.get('view', 'front')
PX = int(spec.get('px', 512)) * int(spec.get('ss', 2))
NV = int(spec.get('variants', 4))
rng = random.Random(int(spec.get('seed', 9)))
os.makedirs(OUT, exist_ok=True)

scn = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = 48
scn.cycles.use_denoising = False
scn.render.film_transparent = True
scn.render.resolution_x = scn.render.resolution_y = PX
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGBA'
scn.view_settings.view_transform = 'Standard'
scn.view_settings.look = 'None'
scn.world = bpy.data.worlds.new('w')
scn.world.color = (0, 0, 0)
cam_d = bpy.data.cameras.new('cam')
cam_d.type = 'ORTHO'
CELL = 2.0 / 0.86  # the cell spans this many units (everything inside 86 %)
cam_d.ortho_scale = CELL
cam = bpy.data.objects.new('cam', cam_d)
scn.collection.objects.link(cam)
cam.location = (0, 0, 5)
scn.camera = cam


def emissive(name, grey):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (grey, grey, grey, 1)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m


MAT = {'rim': emissive('rim', 0.42), 'body': emissive('body', 0.75), 'core': emissive('core', 1.0)}


def poly(bm, pts):
    if len(pts) >= 3: bm.faces.new([bm.verts.new((x, y, 0)) for x, y in pts])


def petal(ox, oy, a, L, wb, inset=0.0, n=14):
    # a flame petal from (ox, oy) along angle a: base wb wide, concave sides, pointed tip; inset shrinks it towards its
    # own middle line (the rim band is what's left between the two)
    c, s_ = math.cos(a), math.sin(a)
    px, py = -s_, c
    Lr = L * (1 - inset * 0.6)
    A, B = [], []
    for i in range(n + 1):
        s = i / n
        r = Lr * s
        hw = (wb / 2) * (1 - s) ** 1.35 * (1 - inset)
        A.append((ox + c * r + px * hw, oy + s_ * r + py * hw)); B.append((ox + c * r - px * hw, oy + s_ * r - py * hw))
    return A + B[::-1]


def lobes(ox, oy, R, k, ph, inset=0.0, n=48):
    pts = []
    for i in range(n):
        a = i / n * math.tau
        r = R * (1 + 0.16 * math.sin(k * a + ph) + 0.12 * math.sin(a + ph * 1.7)) * (1 - inset)
        pts.append((ox + math.cos(a) * r, oy + math.sin(a) * r))
    return pts


def front(v):
    n = rng.randint(4, 6)
    base = rng.uniform(0, math.tau)
    D = 1.0  # the longest petal reaches the cell's 86 % line
    petals = []
    big = rng.sample(range(n), rng.choice((1, 2)))
    for i in range(n):
        a = base + (i + rng.uniform(-0.18, 0.18)) / n * math.tau
        L = D * (rng.uniform(0.92, 1.0) if i in big else rng.uniform(0.56, 0.68))
        petals.append((a, L, L * rng.uniform(0.27, 0.34)))
    R = rng.uniform(0.27, 0.31)
    k, ph = rng.randint(3, 5), rng.uniform(0, math.tau)
    shapes = {'rim': [], 'body': [], 'core': []}
    for a, L, w in petals:
        shapes['rim'].append(petal(0, 0, a, L, w))
        shapes['body'].append(petal(0, 0, a, L, w, inset=0.16))
        shapes['core'].append(petal(0, 0, a, L * 0.5, w * 0.55))
    shapes['rim'].append(lobes(0, 0, R, k, ph))
    shapes['body'].append(lobes(0, 0, R, k, ph, inset=0.1))
    shapes['core'].append(lobes(0, 0, R * 0.78, k, ph))
    return shapes


# the side jet's family: one length and one bloom position for all four drawings (each within 15 %)
JET_L = 1.86
BLOOM_AT = 0.27


def jet_outline(ox, oy, L, H, at, scale_w=1.0, s_end=1.0, n=48, et=1.15, eb=1.15, bump=0.0, bump_at=0.5):
    # pinched at the muzzle (0.1 of H), the bloom at `at`, a long taper to the tip; the top and bottom edges taper with
    # their own exponents and one of them carries a soft bump (no symmetric leaf)
    top, bot = [], []
    for i in range(n + 1):
        s = s_end * i / n
        if s < at: wt = wb = 0.1 + 0.9 * math.sin(s / at * math.pi / 2) ** 1.4
        else: wt, wb = ((1 - s) / (1 - at)) ** et, ((1 - s) / (1 - at)) ** eb
        b = bump * math.exp(-((s - bump_at) / 0.12) ** 2)
        top.append((ox + L * s, oy + H / 2 * (wt + max(b, 0)) * scale_w)); bot.append((ox + L * s, oy - H / 2 * (wb + max(-b, 0)) * scale_w))
    return top + bot[::-1]


def side(v):
    # round 4: the jet's front is a CONVEX curve with triangular tongues growing out of it (V notches between them, no
    # straight wall); the white is a hot bulb with curved edges, widest at the bloom, the unequal prongs leaving from it
    ox, oy = -1.0, 0.0
    L = JET_L * rng.uniform(0.94, 1.04)
    H = CELL * rng.uniform(0.32, 0.38)
    at = rng.uniform(0.4, 0.5)
    et, eb = rng.uniform(0.35, 0.55), rng.uniform(0.35, 0.55)
    xc = 0.7  # the corners of the front, as a share of L
    shapes = {'rim': [], 'body': [], 'core': []}

    def half(s_, e):  # the jet's half height at s_ (pinched at the muzzle, the bloom at `at`, a slow taper)
        if s_ < at: return H / 2 * (0.1 + 0.9 * math.sin(s_ / at * math.pi / 2) ** 1.4)
        return H / 2 * ((1 - s_) / (1 - at)) ** e

    n = rng.choice((3, 4))
    lens = [1.0] + [rng.uniform(0.55, 0.8) for _ in range(n - 1)]
    rng.shuffle(lens)
    bulge = L * rng.uniform(0.08, 0.12)
    ht, hb = half(xc, et), half(xc, eb)

    def outline(scale_y, scale_x):
        top, bot = [], []
        for i in range(31):
            s_ = xc * i / 30
            x = ox + L * s_ * scale_x
            top.append((x, oy + half(s_, et) * scale_y)); bot.append((x, oy - half(s_, eb) * scale_y))
        # the front: from the top corner over a convex arc to the bottom corner, tongues out of it
        front = []
        xs = ox + L * xc * scale_x
        for k in range(n + 1):
            phi = math.pi / 2 - math.pi * k / n  # +90 .. -90 degrees: the notches, then the corners
            hy = ht if phi > 0 else hb
            nx, ny = xs + bulge * scale_x * math.cos(phi), oy + hy * scale_y * math.sin(phi)
            if 0 < k < n:
                # a notch, set back into the curve by 40-60 % of the neighbouring tongue's length
                depth = L * 0.3 * min(lens[k - 1], lens[k]) * rng.uniform(0.4, 0.6) * 0.5
                nx -= depth * scale_x
            front.append((nx, ny))
            if k < n:
                # the tongue between this notch and the next: its tip out along the curve's normal, leaning forward
                phm = math.pi / 2 - math.pi * (k + 0.5) / n
                hy2 = ht if phm > 0 else hb
                bx, by = xs + bulge * scale_x * math.cos(phm), oy + hy2 * scale_y * math.sin(phm)
                dx, dy = math.cos(phm) * 0.6 + 1.0, math.sin(phm) * 0.45  # (the outer tongues at most about 20 degrees)
                dl = math.hypot(dx, dy)
                tl = L * 0.3 * lens[k] * (0.92 if scale_y < 1 else 1.0)
                front.append((bx + dx / dl * tl * scale_x, by + dy / dl * tl * scale_y))
        return top + front[1:-1] + bot[::-1]

    shapes['rim'].append(outline(1.0, 1.0))
    shapes['body'].append(outline(0.84, 0.965))
    # at most one side petal, a real flame petal angled 45-60 degrees forward
    if rng.random() < 0.75:
        sgn = rng.choice((-1, 1))
        a = sgn * math.radians(rng.uniform(45, 60))
        pl = L * rng.uniform(0.2, 0.26)
        x0 = ox + L * rng.uniform(0.06, 0.12)
        shapes['rim'].append(petal(x0, oy, a, pl, pl * 0.42))
        shapes['body'].append(petal(x0, oy, a, pl, pl * 0.42, inset=0.2))
    # the white: a hot bulb following the outline at ~65 % of its height, widest at the bloom, rounding off at ~0.55,
    # then two UNEQUAL prongs off the axis leaving from it
    top, bot = [], []
    s_end = at + 0.12
    for i in range(41):
        s_ = s_end * i / 40
        k = 0.65 * (1 if s_ < at else math.sqrt(max(0.0, 1 - ((s_ - at) / (s_end - at)) ** 2)))
        top.append((ox + L * s_, oy + half(s_, et) * k)); bot.append((ox + L * s_, oy - half(s_, eb) * k))
    shapes['core'].append(top + bot[::-1])
    off = H * rng.uniform(0.04, 0.08) * rng.choice((-1, 1))
    long_l = L * rng.uniform(0.24, 0.3)
    shapes['core'].append(petal(ox + L * (at + 0.02), oy + off, math.radians(rng.uniform(2, 6)) * (1 if off > 0 else -1), long_l, H * 0.26))
    shapes['core'].append(petal(ox + L * at, oy - off * 0.7, -math.radians(rng.uniform(4, 9)) * (1 if off > 0 else -1), long_l / rng.uniform(1.3, 1.5), H * 0.22))
    return shapes


for v in range(NV):
    shapes = front(v) if VIEW == 'front' else side(v)
    for layer in ('body', 'core', 'ink'):
        for o in [o for o in bpy.data.objects if o.type == 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
        groups = (('rim', 0.0), ('body', 0.01)) if layer == 'body' else ((('core', 0.0),) if layer == 'core' else ())
        for g, z in groups:
            bm = bmesh.new()
            for pts in shapes[g]: poly(bm, pts)
            me = bpy.data.meshes.new(g)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(g, me)
            ob.location.z = z
            ob.data.materials.append(MAT[g])
            scn.collection.objects.link(ob)
        scn.render.filepath = os.path.join(OUT, 'mflash_%s_%s_%02d.png' % (VIEW, layer, v))
        bpy.ops.render.render(write_still=True)
print('done', VIEW)
