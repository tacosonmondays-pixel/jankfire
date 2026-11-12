# The mech hero kit, art side: decals every mech gets for free (a unit number, stencils, warning labels and jank
# sponsor stickers in the house voice) placed automatically on the biggest flat plates of a cut Tripo body, and the
# skin / spray slots (decal_slots in the meta + mk_spray_* markers) where the game can project a player's spray later.
# One shared atlas image and one decal material per mech (alpha-tested): a handful of extra draw calls, not one each.
#   import herokit; herokit.decorate(mk, pieces, posed_world, number='07')   (tripo_swap.py, before to_joint)
import math
import numpy as np
from mechkit import *

AW, AH = 1024, 512
# (name, x, y, w, h) cells in the atlas (pixels); the unit number cell is drawn per mech
CELLS = {
    'number': (0, 0, 384, 192), 'nostep': (384, 0, 320, 96), 'hot': (704, 0, 320, 128), 'tri': (384, 96, 128, 128),
    'cola': (512, 128, 320, 144), 'bread': (832, 128, 192, 192), 'washme': (0, 192, 320, 96), 'pilot': (0, 288, 384, 96),
    'piloting': (384, 272, 448, 112), 'serial': (0, 384, 320, 64), 'stripe': (320, 384, 704, 64),
}
# what goes where: (joint names to try, decal, size in metres (w), how many). The first joint that has a fitting
# plate gets it; mirrored pairs take one each side
# and which way it likes to face (out = the outer side, away from the middle; front / back; None = any outward plate)
PLAN = [
    (['shoulder_L', 'upperarm_L'], 'number', 0.62, 'out'), (['shoulder_R', 'upperarm_R'], 'cola', 0.55, 'out'),
    (['chest', 'hatch'], 'pilot', 0.42, 'front'), (['chest'], 'tri', 0.22, 'front'), (['thigh_L'], 'nostep', 0.40, 'front'),
    (['thigh_R'], 'nostep', 0.40, 'front'), (['shin_R'], 'washme', 0.42, 'back'), (['shin_L'], 'bread', 0.32, 'out'),
    (['backpack', 'chest'], 'hot', 0.40, 'back'), (['forearm_L', 'forearm_R'], 'serial', 0.34, 'out'),
    (['hips', 'waist', 'skirt_L'], 'piloting', 0.46, 'back'),
]
SPRAY = [['chest', 'hatch'], ['shoulder_R', 'shoulder_L', 'thigh_R']]
TORSO = {'hips', 'waist', 'chest', 'hatch', 'backpack', 'neck', 'head'}  # (two spray / skin slots: the best plates there)


def _label(px, cell, bg, fg, s, scale, border_col=None, stripes_col=None):
    x, y, w, h = CELLS[cell]
    sub = px[y:y + h, x:x + w]
    if bg is not None: fill(sub, 4, 4, w - 4, h - 4, bg)
    if stripes_col: stripes(sub, 4, 4, w - 4, max(8, h // 4), stripes_col, 0x101010, 10); stripes(sub, 4, h - max(8, h // 4), w - 4, h - 4, stripes_col, 0x101010, 10)
    if border_col is not None:
        for t in range(4): fill(sub, t, t, w - t, t + 1, border_col); fill(sub, t, h - t - 1, w - t, h - t, border_col); fill(sub, t, t, t + 1, h - t, border_col); fill(sub, w - t - 1, t, w - t, h - t, border_col)
    lines = s.split('\n'); lh = 8 * scale; y0 = (h - lh * len(lines)) // 2 + scale
    for i, ln in enumerate(lines):
        sc = scale if text_w(ln, scale) < w - 16 else max(1, int(scale * (w - 16) / text_w(ln, scale)))
        text_c(sub, ln, w // 2, y0 + i * lh, sc, fg)


def atlas(number='07'):
    """the decal sheet (rgba, transparent between the labels)"""
    px = canvas(AW, AH)
    x, y, w, h = CELLS['number']; sub = px[y:y + h, x:x + w]  # (the unit number: a big stencil, gaps cut through it)
    sc = min(22, int((w - 20) / max(1, text_w(number, 1))), int((h - 20) / 7)); text_c(sub, number, w // 2, (h - 7 * sc) // 2, sc, 0xf6f2ea)
    for gx in range(0, w, sc * 6): sub[:, gx + sc * 2:gx + sc * 2 + max(2, sc // 5), 3] = 0
    _label(px, 'nostep', 0xffd23a, 0x111111, 'NO STEP', 6, 0x111111)
    _label(px, 'hot', 0xffd23a, 0x111111, 'CAUTION\nHOT', 5, None, 0xffd23a)
    x, y, w, h = CELLS['tri']; sub = px[y:y + h, x:x + w]
    poly(sub, [(w / 2, 6), (w - 6, h - 8), (6, h - 8)], 0x111111); poly(sub, [(w / 2, 20), (w - 18, h - 16), (18, h - 16)], 0xffd23a)
    text_c(sub, '!', w // 2, 44, 8, 0x111111)
    _label(px, 'cola', 0xe8202a, 0xffffff, 'JANK COLA\nNOW 0% WATER', 5, 0xffffff)
    x, y, w, h = CELLS['bread']; sub = px[y:y + h, x:x + w]  # (a round sponsor badge)
    yy, xx = np.mgrid[0:h, 0:w]; r = ((xx - w / 2) ** 2 + (yy - h / 2) ** 2) ** 0.5
    sub[r < w / 2 - 4, :3] = hexrgb(0x111111); sub[r < w / 2 - 4, 3] = 1; sub[r < w / 2 - 12, :3] = hexrgb(0xffd23a)
    text_c(sub, 'POWERED', w // 2, 52, 3, 0x111111); text_c(sub, 'BY', w // 2, 80, 3, 0x111111); text_c(sub, 'BREAD', w // 2, 108, 5, 0xb35a1f)
    _label(px, 'washme', None, 0xe8e2d6, 'WASH ME', 7)
    _label(px, 'pilot', 0xf6f2ea, 0x111111, 'PILOT INSIDE\nPROBABLY', 5, 0xe8202a)
    _label(px, 'piloting', 0xf6f2ea, 0x111111, 'HOW IS MY PILOTING?\nCALL 0800-JANK', 4, 0x111111)
    _label(px, 'serial', 0x1b1b22, 0xd8d8d8, f'MK-{number.replace("/", "")} LOT 404', 3, 0x8a8a90)
    x, y, w, h = CELLS['stripe']; stripes(px, x, y + 8, x + w, y + h - 8, 0xffd23a, 0x111111, 16)
    crust(px, 0.05, seed=3, p=0.01)
    return px


def flat_panels(o, min_area=0.02, tol=0.985):
    """flat regions of a mesh (connected faces within ~10 degrees of the first, or tol = a looser cosine for gently
    curved plates; game space): (area, centre, mean normal, faces)"""
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bm.faces.ensure_lookup_table()
    seen = [False] * len(bm.faces); out = []
    for f in bm.faces:
        if seen[f.index] or f.calc_area() < 1e-6: continue
        n0 = f.normal.copy(); seen[f.index] = True; st = [f]; mem = []
        while st:
            a = st.pop(); mem.append(a)
            for e in a.edges:
                for g in e.link_faces:
                    if not seen[g.index] and g.normal.dot(n0) > tol: seen[g.index] = True; st.append(g)
        area = sum(x.calc_area() for x in mem)
        if area < min_area: continue
        c = sum((x.calc_center_median() * x.calc_area() for x in mem), V((0, 0, 0))) / area
        nm = sum((x.normal * x.calc_area() for x in mem), V((0, 0, 0)))
        out.append((area, g_of(c), g_of(nm.normalized() if nm.length > 1e-6 else n0), len(mem)))
    bm.free()
    out.sort(key=lambda r: -r[0])
    return out


def _up_for(normal, rest_up):
    """the decal's up: the joint's rest up, flattened onto the plate (or its forward if the plate faces up)"""
    n = norm(normal); u = sub(rest_up, mul(n, dot(rest_up, n)))
    if sum(x * x for x in u) < 0.05: u = sub((0, 0, -1), mul(n, dot((0, 0, -1), n)))
    return norm(u)


def decorate(mk, pieces, posed_world, number='07', plan=PLAN, spray=SPRAY):
    """stamps the plan onto the cut pieces (cut-pose world space, before to_joint) and finds the spray slots.
    Returns (decal count, slots) where slots are in the cut pose (tripo_swap moves them to rest)"""
    img = image_rgba(f'{mk.prefix}_decals', atlas(number))
    m = tex_mat(f'{mk.prefix}_decalmat', img, rough=0.42, clip=True, cc=0.5)
    used, made = set(), 0
    centre = lambda j: g_of(posed_world[j].translation)
    trees = [(o, BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())) for o in pieces.values() if o is not None and o.type == 'MESH']
    def exposed(c, n, reach=1.6):  # (nothing of the mech in front of the plate: a ray straight out of it hits nothing)
        p, d = V(gv(*c)), V(gv(*n)).normalized()
        p = p + d * 0.03
        for o, t in trees:
            Mi = o.matrix_world.inverted()
            if t.ray_cast(Mi @ p, (Mi.to_3x3() @ d).normalized(), reach)[0] is not None: return False
        return True
    def best(j, w, h, avoid=(), face=None, strict=False, tol=0.985, see=False, steep=0.75):
        o = pieces.get(j)
        if o is None: return None
        rot = posed_world[j].to_3x3(); rest_up = g_of(rot @ gv(0, 1, 0))
        want = {'front': (0, 0, -1), 'back': (0, 0, 1)}.get(face)
        if face == 'out': want = (1 if centre(j)[0] >= 0 else -1, 0, 0)
        if want: want = g_of(rot @ gv(*want))  # (the joint's own front / side, as it is turned in the cut pose)
        cands = []
        for area, c, n, _ in flat_panels(o, tol=tol):
            if any(sum((a - b) ** 2 for a, b in zip(c, p)) < 0.09 for p in avoid): continue
            out = sub(c, (0, c[1], 0) if j in TORSO else centre(j))  # (torso plates: out from the body's middle line)
            if dot(out, n) < 0 or abs(n[1]) > steep: continue  # (facing out of the body, not straight up or down)
            if see and not exposed(c, n): continue
            cands.append((area, dot(n, want) if want else 1.0, c, n))
        # the plates that really face that way, the decal shrunk a little if it must; else any outward plate it fits
        for k, ok in ((1.0, 0.55), (0.8, 0.55), (0.62, 0.55)) + (() if strict else ((1.0, -2), (0.8, -2), (0.62, -2))):
            good = [r for r in cands if r[1] >= ok and r[0] >= w * h * k * k * 1.2]
            if good:
                _, _, c, n = max(good, key=lambda r: r[0] * (1 + r[1]))
                return c, n, _up_for(n, rest_up), k
        return None
    placed, slots = [], []
    # the spray / skin slots first (the biggest outward plates on the chest and a shoulder or thigh): the stickers
    # then keep off them, so a spray never lands on top of one
    for joints in spray:
        for j in joints:
            r = best(j, 0.42, 0.42, placed, 'front' if j in TORSO else 'out', tol=0.8, see=True, steep=0.5)  # (a spray can wrap a curved plate; one you can see)
            if r: slots.append({'name': f'spray_{len(slots)}', 'joint': j, 'at': r[0], 'dir': r[1], 'up': r[2], 'size': round(0.6 * r[3], 2)}); placed.append(r[0]); break
    for joints, cell, w, face in plan:
        x, y, cw, ch = CELLS[cell]; h = w * ch / cw
        tries = [(j, True) for j in joints] + [(j, False) for j in joints]  # (a plate facing the right way on any of them first)
        for j, strict in tries:
            r = best(j, w, h, placed, face, strict)
            if not r: continue
            c, n, u, k = r
            d = decal([pieces[j]], c, n, u, w * k, h * k, m, name=f'dc_{cell}', reach=0.25)
            if d is None: continue
            uv = d.data.uv_layers['UVMap'].data  # (the patch's 0..1 -> its cell in the atlas)
            for l in uv: l.uv = ((x + l.uv[0] * cw) / AW, 1 - (y + (1 - l.uv[1]) * ch) / AH)
            lib.join([pieces[j], d], pieces[j].name); placed.append(c); made += 1
            print(f'JF_DECAL {cell} on {j} at {tuple(round(v, 2) for v in c)} facing {tuple(round(v, 2) for v in n)} ({w * k:.2f} m)')
            break
    print('JF_SPRAY', ' '.join(f"{sl['name']} on {sl['joint']} ({sl['size']} m)" for sl in slots) or 'none')
    return made, slots
