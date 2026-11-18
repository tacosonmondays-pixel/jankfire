# CURRENCY ICONS (18 Nov 2026). The owner: "for tickets can you model tickets and coins like flat 3d ones maybe? that
# will be the icon, maybe a small pack for 99 robux another one with like a sack of coins for 499 robux maybe another
# for 1999 robux thats like a small chest of coins with some on the ground and then a 4500 robux one with like multiple
# chests and sacks". Headless Blender, the kit's chunky look (few big rounded shapes, flat colours, soft bevels):
#   COIN    a thick gold coin: a chunky rounded rim round a sunk face with a raised five-point star on both sides (no text,
#           no currency sign, nothing like any platform's coin)
#   TICKET  a flat 3D Crate Ticket in the HUD's own colours (QuestUI TICKET 226,219,201 and TICKET_INK 120,112,98): a
#           rounded slip with a half-round notch in each end, a perforation line of plain round dots a third of the way
#           along, a raised star on the big part
#   PACKS   the same coin in four scenes, each plainly bigger than the last:
#             pack_99    a short stack and a few coins lying by it
#             pack_499   a tied cloth sack, coins spilling out of its mouth onto the ground
#             pack_1999  a small open wooden chest heaped with coins, a few on the ground
#             pack_4500  two chests (one open, heaped) and two sacks round a big pile of coins
# Renders (Cycles CPU, soft studio light):
#   pack_*.png   512 x 512 on the VIP pass icon's backdrop (dark slate, a warm gold glow behind the subject)
#   coin.png, ticket.png   256 x 256 on a transparent background (HUD and shop)
#   currency_sheet.png     all six side by side (the contact sheet)
#   blender -b --factory-startup -P tools/blender/currency_icons.py -- roblox/docs/money/icons [coin ticket pack_99 ...]
# (roblox/docs/money/icons is the owner-approved folder for shop product icons; render straight into it, never copy)
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix, Euler

GOLD = (0.86, 0.6, 0.18)
GOLD_DEEP = (0.62, 0.4, 0.1)
TICKET = tuple(c / 255 for c in (226, 219, 201))
TICKET_INK = tuple(c / 255 for c in (120, 112, 98))
WOOD = (0.33, 0.2, 0.11)
WOOD_D = (0.22, 0.13, 0.07)
IRON = (0.16, 0.16, 0.17)
CLOTH = (0.55, 0.42, 0.27)
ROPE = (0.42, 0.3, 0.17)


EXPOSURE = -0.8


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ------------------------------------------------------------------------------------------------ materials
_MATS = {}


def mat(name, col, metal=0.0, rough=0.5, srgb=True):
    if name in _MATS: return _MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    c = lin(col) if srgb else col
    b.inputs['Base Color'].default_value = (*c, 1.0)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    _MATS[name] = m
    return m


def gold(): return mat('gold', GOLD, metal=1.0, rough=0.32)


# ------------------------------------------------------------------------------------------------ helpers
def obj(name, bm, material=None, smooth=True, bevel=0.0, segs=2):
    me = bpy.data.meshes.new(name)
    bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if material: o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth = smooth
    if smooth:
        try: o.data.set_sharp_from_angle(angle=math.radians(40))
        except Exception: pass
    if bevel > 0:
        m = o.modifiers.new('bev', 'BEVEL'); m.width = bevel; m.segments = segs; m.limit_method = 'ANGLE'
        m.angle_limit = math.radians(35)
    if smooth:
        try:
            o.modifiers.new('ws', 'WEIGHTED_NORMAL').keep_sharp = True
        except Exception:
            pass
    return o


def lathe(prof, segs=64):
    """a profile [(r, z)] turned about z"""
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r < 1e-6: rings.append([bm.verts.new((0, 0, z))])
        else: rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) == 1: bm.faces.new([a[0], b[i], b[j]])
            elif len(b) == 1: bm.faces.new([a[i], a[j], b[0]])
            else: bm.faces.new([a[i], a[j], b[j], b[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def star_pts(R, r, n=5, rot=math.pi / 2):
    pts = []
    for k in range(2 * n):
        a = rot + math.pi * k / n
        rr = R if k % 2 == 0 else r
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return pts


def prism2d(pts, z0, z1):
    """a flat outline [(x, y)] (counter-clockwise) pushed from z0 to z1"""
    bm = bmesh.new()
    A = [bm.verts.new((x, y, z0)) for x, y in pts]
    B = [bm.verts.new((x, y, z1)) for x, y in pts]
    n = len(pts)
    bm.faces.new(A[::-1]); bm.faces.new(B)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([A[i], A[j], B[j], B[i]])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    return bm


# ------------------------------------------------------------------------------------------------ the coin
_COIN = None


def coin_mesh():
    """the coin, radius 1, 0.3 thick, lying flat (z up): one mesh shared by every coin"""
    global _COIN
    if _COIN: return _COIN
    prof = [(0.0, 0.1), (0.78, 0.1), (0.8, 0.11), (0.84, 0.148), (0.93, 0.152), (0.985, 0.12), (1.0, 0.07), (1.0, -0.07),
            (0.985, -0.12), (0.93, -0.152), (0.84, -0.148), (0.8, -0.11), (0.78, -0.1), (0.0, -0.1)]
    o = obj('coin_body', lathe(prof, 72), gold(), bevel=0.0)
    parts = [o]
    for sz in (1, -1):
        s = obj('coin_star', prism2d(star_pts(0.56, 0.24), 0.07 * sz if sz > 0 else -0.155, 0.155 if sz > 0 else -0.07), gold(),
                smooth=False, bevel=0.035, segs=3)
        parts.append(s)
    for p in parts:
        bpy.context.view_layer.objects.active = p
        for m in list(p.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    coin = bpy.context.view_layer.objects.active
    coin.name = 'COIN'
    _COIN = coin.data
    bpy.data.objects.remove(coin, do_unlink=True)
    return _COIN


def coin(at, rot=(0, 0, 0), s=1.0):
    o = bpy.data.objects.new('coin', coin_mesh())
    bpy.context.scene.collection.objects.link(o)
    o.location = at; o.rotation_euler = Euler(rot); o.scale = (s, s, s)
    return o


# ------------------------------------------------------------------------------------------------ the ticket
def ticket(at=(0, 0, 0), rot=(0, 0, 0), s=1.0):
    W, H, T, R = 2.2, 1.1, 0.14, 0.14
    # the outline: a rounded rectangle with a half-round notch in the middle of each short end
    pts = []
    def arc(cx, cy, r, a0, a1, n):
        return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]
    hw, hh, nr = W / 2, H / 2, 0.2
    pts += arc(hw - R, -hh + R, R, -math.pi / 2, 0, 6)
    pts += arc(hw, 0.0, nr, -math.pi / 2, -3 * math.pi / 2, 12)        # (the right notch, cut inward)
    pts += arc(hw - R, hh - R, R, 0, math.pi / 2, 6)
    pts += arc(-hw + R, hh - R, R, math.pi / 2, math.pi, 6)
    pts += arc(-hw, 0.0, nr, math.pi / 2, -math.pi / 2, 12)            # (the left notch)
    pts += arc(-hw + R, -hh + R, R, math.pi, 3 * math.pi / 2, 6)
    clean = [pts[0]]
    for p in pts[1:]:
        if (Vector(p) - Vector(clean[-1])).length > 1e-5: clean.append(p)
    if (Vector(clean[0]) - Vector(clean[-1])).length < 1e-5: clean.pop()
    body = obj('ticket', prism2d(clean, -T / 2, T / 2), mat('ticket', TICKET, rough=0.55), smooth=False, bevel=0.04, segs=3)
    parts = [body]
    # the perforation: a line of plain round dots, sunk into both faces, a third of the way along
    px = -hw + W * 0.33
    for k in range(7):
        y = -hh + 0.16 + (H - 0.32) * k / 6
        for sz in (1, -1):
            d = lathe([(0.0, 0.0), (0.045, 0.0), (0.045, 0.012), (0.0, 0.012)], 16)
            dob = obj('perf', d, mat('ink', TICKET_INK, rough=0.6))
            dob.location = (px, y, sz * (T / 2 - 0.002) + (0.0 if sz > 0 else -0.01))
            parts.append(dob)
    # a raised star on the big part, both faces, in the ink colour's lighter cousin
    for sz in (1, -1):
        st = obj('tstar', prism2d(star_pts(0.32, 0.135), T / 2 - 0.01 if sz > 0 else -T / 2 - 0.035, T / 2 + 0.035 if sz > 0 else -T / 2 + 0.01),
                 mat('tstar', tuple(0.5 * a + 0.5 * b for a, b in zip(TICKET, TICKET_INK)), rough=0.5), smooth=False, bevel=0.018, segs=2)
        st.location = (px + (hw - px) * 0.5 + 0.02, 0.0, 0.0)
        parts.append(st)
    root = bpy.data.objects.new('ticket_root', None)
    bpy.context.scene.collection.objects.link(root)
    for p in parts: p.parent = root
    root.location = at; root.rotation_euler = Euler(rot); root.scale = (s, s, s)
    return root


# ------------------------------------------------------------------------------------------------ props
def sack(at, s=1.0, lean=0.0, open_mouth=True):
    """a tied cloth sack: a soft round belly, a pinched neck tied with a rope band, a flared frill; coins in its mouth"""
    prof = [(0.0, 0.0), (0.7, 0.02), (1.02, 0.25), (1.12, 0.6), (1.08, 0.95), (0.9, 1.25), (0.55, 1.48), (0.33, 1.6),
            (0.32, 1.66), (0.5, 1.82), (0.62, 1.98), (0.55, 2.02), (0.36, 1.9), (0.0, 1.86)]
    bm = lathe(prof, 40)
    # soft lumps: push the belly in and out a little round the turn (cloth, not a pot)
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x)
        k = 1.0 + 0.05 * math.sin(3 * a + 0.7) + 0.03 * math.sin(5 * a)
        f = min(1.0, max(0.0, (v.co.z - 0.9) / 0.6))
        k += 0.07 * f * math.sin(9 * a + 0.3)
        if v.co.z < 1.56: v.co.x *= k; v.co.y *= k
    o = obj('sack', bm, mat('cloth', CLOTH, rough=0.85))
    band = obj('band', lathe([(0.3, 1.56), (0.42, 1.58), (0.43, 1.66), (0.3, 1.68)], 32), mat('rope', ROPE, rough=0.8))
    root = bpy.data.objects.new('sack_root', None)
    bpy.context.scene.collection.objects.link(root)
    for p in (o, band): p.parent = root
    if open_mouth:
        hm = lambda r: 1.84 + 0.3 * (1 - r ** 2)
        mm = mound(hm, 0.42, 0.42, 1.7); mm.parent = root
        for c in cover(hm, 0.42, 0.42, 0.19, 7, spacing=1.25, rmax=0.85): c.parent = root
    root.location = at; root.rotation_euler = (lean, 0, 0); root.scale = (s, s, s)
    return root


def chest(at, s=1.0, yaw=0.0, open_lid=True, full=True):
    """a small wooden chest: plank body with iron bands and corner caps, a domed lid hinged at the back (open: tipped
       back), heaped with coins"""
    W, D, H = 2.4, 1.6, 1.25
    parts = []
    def box(name, x0, x1, y0, y1, z0, z1, m, bev=0.04):
        bm = bmesh.new()
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r['verts']:
            v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0), (z0 + z1) / 2 + v.co.z * (z1 - z0)))
        return obj(name, bm, m, smooth=False, bevel=bev, segs=2)
    wood, wood_d, iron = mat('wood', WOOD, rough=0.75), mat('wood_d', WOOD_D, rough=0.8), mat('iron', IRON, metal=0.6, rough=0.45)
    t = 0.12
    parts += [box('floor', -W / 2, W / 2, -D / 2, D / 2, 0.0, t, wood_d),
              box('front', -W / 2, W / 2, -D / 2, -D / 2 + t, 0.0, H, wood), box('back', -W / 2, W / 2, D / 2 - t, D / 2, 0.0, H, wood),
              box('left', -W / 2, -W / 2 + t, -D / 2, D / 2, 0.0, H, wood), box('right', W / 2 - t, W / 2, -D / 2, D / 2, 0.0, H, wood)]
    for x in (-W / 2 + 0.35, W / 2 - 0.35):          # iron bands round the body
        parts.append(box('bandf', x - 0.08, x + 0.08, -D / 2 - 0.035, -D / 2 + 0.02, -0.01, H + 0.01, iron, 0.02))
        parts.append(box('bandb', x - 0.08, x + 0.08, D / 2 - 0.02, D / 2 + 0.035, -0.01, H + 0.01, iron, 0.02))
    parts.append(box('lock', -0.16, 0.16, -D / 2 - 0.06, -D / 2 + 0.01, H - 0.38, H - 0.06, mat('brass', GOLD_DEEP, metal=0.9, rough=0.35), 0.03))
    # the lid: a half-barrel, hinged on the back top edge
    lid_prof = []
    n = 14
    for k in range(n + 1):
        a = math.pi * k / n
        lid_prof.append((-D / 2 * math.cos(a), 0.42 * math.sin(a)))
    bm = bmesh.new()
    L = [[bm.verts.new((x, y, z)) for (y, z) in lid_prof] for x in (-W / 2, W / 2)]
    for i in range(n):
        bm.faces.new([L[0][i], L[0][i + 1], L[1][i + 1], L[1][i]])
    bm.faces.new(L[0][::-1]); bm.faces.new(L[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    lid = obj('lid', bm, wood, smooth=True, bevel=0.03, segs=2)
    lidparts = [lid]
    for x in (-W / 2 + 0.35, W / 2 - 0.35):
        bm2 = bmesh.new()
        L2 = [[bm2.verts.new((xx, y * 1.03, z * 1.06 + 0.005)) for (y, z) in lid_prof] for xx in (x - 0.08, x + 0.08)]
        for i in range(n): bm2.faces.new([L2[0][i], L2[0][i + 1], L2[1][i + 1], L2[1][i]])
        lidparts.append(obj('lidband', bm2, iron, smooth=True))
    lid_root = bpy.data.objects.new('lid_root', None)
    bpy.context.scene.collection.objects.link(lid_root)
    for p in lidparts: p.parent = lid_root
    if open_lid:
        # hinge at the back top: rotate about x through (0, D/2, H)
        lid_root.location = (0, D / 2, H)
        for p in lidparts: p.location = (0, -D / 2, 0)
        lid_root.rotation_euler = (-math.radians(105), 0, 0)
    else:
        lid_root.location = (0, 0, H)
    root = bpy.data.objects.new('chest_root', None)
    bpy.context.scene.collection.objects.link(root)
    for p in parts: p.parent = root
    lid_root.parent = root
    if open_lid and full:
        # the heap: a gold mound filling the box, coins lying over it at all angles
        hh = lambda r: 1.12 + 0.5 * (1 - r ** 2.2)
        ax, ay = W / 2 - t - 0.01, D / 2 - t - 0.01
        heap = mound(hh, ax, ay, 0.9)
        heap.parent = root
        for c in cover(hh, ax, ay, 0.27, int(at[0] * 100 + at[1] * 10 + 3), rmax=0.9):
            c.parent = root
    root.location = at; root.rotation_euler = (0, 0, yaw); root.scale = (s, s, s)
    return root


def heap_mat(): return mat('gold_heap', (0.5, 0.31, 0.08), metal=1.0, rough=0.6)


def mound(h, ax, ay, z0, n=24):
    """the mound under a heap: h(rho) for rho 0..1 over an ellipse ax x ay, closed underneath at z0"""
    prof = [(k / n, h(k / n)) for k in range(n + 1)] + [(1.0, z0), (0.0, z0)]
    bm = lathe(prof, 48)
    for v in bm.verts: v.co.x *= ax; v.co.y *= ay
    return obj('mound', bm, heap_mat())


def cover(h, ax, ay, s, seed, spacing=1.3, rmax=0.96, tries=4000):
    """coins laid on the mound's surface, each turned to the slope under it, a little tilt and spin"""
    rnd = random.Random(seed)
    def z(x, y): return h(min(1.0, math.sqrt((x / ax) ** 2 + (y / ay) ** 2)))
    placed, out = [], []
    for _ in range(tries):
        u, v = rnd.uniform(-1, 1), rnd.uniform(-1, 1)
        if u * u + v * v > rmax * rmax: continue
        x, y = u * ax, v * ay
        if any((x - px) ** 2 + (y - py) ** 2 < (s * spacing) ** 2 for px, py in placed): continue
        placed.append((x, y))
        e = 0.01
        nrm = Vector((-(z(x + e, y) - z(x - e, y)) / (2 * e), -(z(x, y + e) - z(x, y - e)) / (2 * e), 1.0)).normalized()
        q = Vector((0, 0, 1)).rotation_difference(nrm)
        tilt = Euler((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0, 6.28))).to_quaternion()
        c = coin((x, y, z(x, y) + 0.02 * s), (0, 0, 0), s)
        c.rotation_mode = 'QUATERNION'; c.rotation_quaternion = q @ tilt
        out.append(c)
    return out


def scatter(n, cx, cy, rx, ry, seed, s=0.32, z=0.0):
    rnd = random.Random(seed)
    out = []
    tries = 0
    while len(out) < n and tries < n * 30:
        tries += 1
        x, y = cx + rnd.uniform(-rx, rx), cy + rnd.uniform(-ry, ry)
        if any((Vector((x, y)) - Vector(p)).length < s * 2.05 for p in out): continue
        out.append((x, y))
        tilt = rnd.choice((0.0, 0.0, 0.25, -0.2))
        coin((x, y, z + s * 0.15 + abs(tilt) * s * 0.9), (tilt, rnd.uniform(-0.15, 0.15), rnd.uniform(0, 6)), s)
    return out


def stack(x, y, n, s=0.32, seed=1, z=0.0):
    rnd = random.Random(seed)
    for k in range(n):
        coin((x + rnd.uniform(-0.03, 0.03) * s, y + rnd.uniform(-0.03, 0.03) * s, z + s * (0.15 + 0.3 * k)), (0, 0, rnd.uniform(0, 6)), s)


def pile(cx, cy, R, Hh, seed, s=0.3, n=60):
    """a heap of coins: a gold mound with coins lying over it"""
    hh = lambda r: Hh * max(0.0, 1 - r ** 1.7) ** 1.25
    o = mound(hh, R, R, 0.0)
    o.location = (cx, cy, 0)
    for c in cover(hh, R, R, s, seed, rmax=0.97):
        c.location.x += cx; c.location.y += cy


# ------------------------------------------------------------------------------------------------ the stage
def stage(res, transparent=True, ground=True):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 96
    try: sc.cycles.use_denoising = True
    except Exception: pass
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.film_transparent = transparent
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.exposure = EXPOSURE
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.42, 0.4, 0.37, 1); bg.inputs[1].default_value = 0.55
    def light(name, kind, loc, energy, size, col=(1, 1, 1)):
        ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = col
        if kind == 'AREA': ld.size = size
        lo = bpy.data.objects.new(name, ld); sc.collection.objects.link(lo); lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return lo
    light('key', 'AREA', (-4.5, -5.0, 6.5), 1400, 4.0, (1.0, 0.93, 0.82))
    light('fill', 'AREA', (6.0, -3.5, 3.0), 420, 5.0, (0.85, 0.9, 1.0))
    light('rim', 'AREA', (1.5, 6.5, 5.5), 900, 3.0, (1.0, 0.85, 0.6))
    if ground:
        bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30)
        g = obj('ground', bm, mat('ground', (0.5, 0.5, 0.5)), smooth=False)
        g.is_shadow_catcher = True
    return sc


def camera(sc, target, dist, elev=26, azim=-38, lens=55):
    cam = bpy.data.cameras.new('cam'); cam.lens = lens
    co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
    e, a = math.radians(elev), math.radians(azim)
    t = Vector(target)
    co.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    co.rotation_euler = (t - co.location).to_track_quat('-Z', 'Y').to_euler()
    return co


def frame(sc, elev=26, azim=-30, lens=55, fill=0.8):
    """aim the camera at everything but the ground and back it off until the lot fills `fill` of the frame"""
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    pts = []
    for o in sc.objects:
        if o.type != 'MESH' or o.name.startswith('ground'): continue
        pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    t = sum(pts, Vector()) / len(pts)
    d = 10.0
    cam = camera(sc, t, d, elev, azim, lens)
    e, a = math.radians(elev), math.radians(azim)
    fwd = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    for _ in range(8):
        cam.location = t + fwd * d
        cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        right = cam.matrix_world.to_3x3() @ Vector((1, 0, 0)); up = cam.matrix_world.to_3x3() @ Vector((0, 1, 0))
        co = [world_to_camera_view(sc, cam, p) for p in pts]
        x0, x1 = min(c.x for c in co), max(c.x for c in co); y0, y1 = min(c.y for c in co), max(c.y for c in co)
        vw = d * 36.0 / lens
        t = t + right * ((x0 + x1) / 2 - 0.5) * vw + up * ((y0 + y1) / 2 - 0.5) * vw
        d *= max(x1 - x0, y1 - y0) / fill
    return cam


def fresh():
    global _COIN
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _COIN = None; _MATS.clear()


# ------------------------------------------------------------------------------------------------ the six shots
def shot_coin(out):
    fresh(); sc = stage(256, ground=False)
    coin((0, 0, 0), (math.radians(62), 0, math.radians(-14)), 1.0)
    camera(sc, (0, 0, 0), 5.0, elev=8, azim=-8, lens=60)
    sc.view_settings.exposure = EXPOSURE - 0.9
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)


def shot_ticket(out):
    fresh(); sc = stage(256, ground=False)
    ticket((0, 0, 0), (math.radians(58), math.radians(-8), math.radians(-12)), 1.0)
    camera(sc, (0, 0, 0), 5.1, elev=8, azim=-8, lens=60)
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)


def shot_99(out):
    fresh(); sc = stage(512)
    stack(0.0, 0.1, 7, 0.42, seed=4)
    stack(-0.78, 0.55, 3, 0.42, seed=5)
    for x, y, rot in ((0.92, -0.38, (0, 0, 1.0)), (-0.72, -0.5, (0.2, 0.1, 2.0)), (0.62, 0.82, (0, 0, 3.0)), (0.12, -0.95, (0, 0, 0.4))):
        coin((x, y, 0.42 * 0.15 + abs(rot[0]) * 0.3), rot, 0.42)
    frame(sc, 24, -32, 60, 0.74)
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)


def shot_499(out):
    fresh(); sc = stage(512)
    sack((0.0, 0.3, 0.0), 1.05, lean=0.0)
    for x, y, rot in ((0.35, -1.3, (0.0, 0.0, 0.4)), (-0.6, -1.1, (0.25, 0.0, 1.2)), (0.95, -0.7, (0.0, 0.0, 2.4)), (-1.15, -0.4, (0.0, 0.0, 0.9)),
                      (0.05, -1.75, (0.2, 0.1, 3.0))):
        coin((x, y, 0.36 * 0.15 + abs(rot[0]) * 0.28), rot, 0.36)
    stack(1.05, -1.45, 3, 0.36, seed=8)
    frame(sc, 22, -30, 55, 0.78)
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)


def shot_1999(out):
    fresh(); sc = stage(512)
    chest((0.0, 0.3, 0.0), 1.0, yaw=math.radians(-12), open_lid=True)
    scatter(9, 0.0, -1.55, 2.0, 0.45, seed=21, s=0.3)
    stack(1.75, -1.0, 4, 0.3, seed=9)
    frame(sc, 26, -28, 55, 0.82)
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)


def shot_4500(out):
    fresh(); sc = stage(512)
    pile(0.0, -0.25, 1.6, 1.2, seed=33, s=0.27)
    chest((-1.55, 1.15, 0.0), 1.0, yaw=math.radians(20), open_lid=True)
    chest((1.6, 1.25, 0.0), 0.9, yaw=math.radians(-24), open_lid=False, full=False)
    sack((-2.05, -0.85, 0.0), 0.8)
    sack((2.1, -0.6, 0.0), 0.74)
    scatter(9, 0.1, -1.95, 2.1, 0.35, seed=44, s=0.27)
    stack(-1.05, -1.95, 5, 0.27, seed=12); stack(1.2, -1.85, 3, 0.27, seed=13)
    frame(sc, 27, -24, 50, 0.9)
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)


def backdrop(n):
    """the VIP pass icon's backdrop: dark slate, bluer in the corners, a warm gold glow behind the subject"""
    import numpy as np
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / (n - 1)
    y = 1.0 - y                                                   # (Blender's pixel rows run bottom-up)
    r = np.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2) / 0.7071
    edge = np.array((35, 34, 36), np.float32) / 255; corner = np.array((24, 26, 34), np.float32) / 255
    t = np.clip((r - 0.55) / 0.45, 0, 1)[..., None]
    base = edge * (1 - t) + corner * t
    g = np.exp(-(((x - 0.5) ** 2 + (y - 0.47) ** 2) / (0.27 ** 2)))[..., None]
    glow = np.array((150, 116, 62), np.float32) / 255
    return base * (1 - 0.85 * g) + glow * 0.85 * g


def finish(raw, out):
    """lay the transparent render (shadows included, from the shadow catcher) over the backdrop; write the PNG"""
    import numpy as np
    im = bpy.data.images.load(raw)
    n = im.size[0]
    px = np.array(im.pixels[:], np.float32).reshape(n, n, 4)
    a = px[..., 3:4]
    rgb = px[..., :3] * a + backdrop(n) * (1 - a)
    o = bpy.data.images.new('final', n, n, alpha=False)
    o.pixels[:] = np.concatenate([rgb, np.ones_like(a)], axis=2).ravel()
    o.filepath_raw = out; o.file_format = 'PNG'; o.save()
    bpy.data.images.remove(im); bpy.data.images.remove(o)
    os.remove(raw)


SHOTS = {'coin': shot_coin, 'ticket': shot_ticket, 'pack_99': shot_99, 'pack_499': shot_499, 'pack_1999': shot_1999,
         'pack_4500': shot_4500}

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out_dir = argv[0]
    os.makedirs(out_dir, exist_ok=True)
    import tempfile
    for key in (argv[1:] or list(SHOTS)):
        out = os.path.join(out_dir, key + '.png')
        if key.startswith('pack_'):
            raw = os.path.join(tempfile.gettempdir(), 'currency_' + key + '_raw.png')
            SHOTS[key](raw)
            finish(raw, out)
        else:
            SHOTS[key](out)
        print('RENDERED', key, out)
