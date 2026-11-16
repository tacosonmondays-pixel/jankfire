# The loot containers for the Roblox game: the CRATE (weapon skins), the DUFFEL BAG (hats, effects, kill effects,
# grapples) and the SPRAY CAN (wraps, sprays). Headless Blender, built on the gun kit (gunkit.py, style C: boxes and
# slabs with one crisp chamfer, round tubes with faceted outlines, flat colours, SmoothPlastic) so they sit with the
# guns. Each has a part that opens: the crate's lid on a back hinge, the bag's zip pull and two top flaps, the can's cap.
#   blender -b --factory-startup -P tools/roblox/loot_models.py -- <out_dir>            # loot_upload.glb + loot.json
#   blender -b --factory-startup -P tools/roblox/loot_models.py -- <out_dir> --preview  # + preview renders (Cycles)
#
# THE LOOK (owner's rules: memories chunky-model-style, less-colourful-look, roblox-port-direction; vault
# Research/Rivals crates and opening.md): a few big chunky masses, every edge chamfered once, a charcoal and steel
# family, ONE muted colour per container so the three are told apart at a glance (the crate's slate panels, the bag's
# olive canvas, the can's pale body) and the house amber on the one thing your eye should go to (the crate's latch, the
# bag's zip pull, the can's cap). No text, no logos, no stickers. Inspired by the polish of Rivals' cases, never a copy.
#
# THE FRAME. studs, Roblox's own frame: x = right, y = up, z = BACK; the FRONT faces -z; the origin is the middle of the
# bottom face. (gunkit.P turns that into Blender's frame and rbxglb.turn_for_roblox makes the upload land as written.)
# PIECES arrive in Studio as MeshParts named "<kind>_<node>__<look>"; a node "<Group>-<name>" belongs to the moving
# group <Group> (Lid, Zip, FlapL, FlapR, Cap). look = p<hex> (SmoothPlastic) / n<hex> (Neon). "glow" pieces are the
# light inside: hidden until the opening pops them. PolishBackup.LootImport builds ReplicatedStorage.JankfireLoot.
import bpy, bmesh, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gunkit
from gunkit import Gun, rect
from mathutils import Vector, Matrix, Euler

gunkit.use_style('C')
gunkit.BEV_SEG = 2  # (big containers: a two-step chamfer reads as a soft, cast edge instead of a sharp facet)

# ---- the palette (a step greyer than it looks in Blender: the hub's lamps warm and lift colour)
DARK = '2b2e35'    # near-charcoal: skids, handles, straps, the can's band
FRAME = '3d424c'   # charcoal: the crate's frame and lid
STEEL = '8c929c'   # light steel: guards, rims, the zip track
PALE = 'c8ccd2'    # pale grey: trims
AMBER = 'd9a23c'   # the house accent (Theme's amber, greyed for the lamps)
SLATE = '4c5a6e'   # the crate's colour: slate-blue panels
OLIVE = '5d624e'   # the bag's colour: olive canvas
OLIVE_D = '41453a' # the bag's ends
CAN = 'd4d7dc'     # the can's pale body
GLOW = 'fff4e2'    # the light inside (neon)


def palette(g):
    for name, col, kind in (('dark', DARK, 'p'), ('frame', FRAME, 'p'), ('steel', STEEL, 'p'), ('pale', PALE, 'p'),
                            ('amber', AMBER, 'p'), ('slate', SLATE, 'p'), ('olive', OLIVE, 'p'), ('olived', OLIVE_D, 'p'),
                            ('can', CAN, 'p'), ('glow', GLOW, 'n')):
        g.slot(name, col, kind)


def box(g, piece, x, y, z, bev=0.06):
    g.box(piece, x, y, z, bev=bev)


# ------------------------------------------------------------------------------------------------- the crate
CRATE = dict(w=3.6, h=1.78, d=2.4, lid=0.55)


def crate():
    """a flight case: a charcoal shell with slate panels, steel corner posts the full height, a skid, side handles, a
       thick lid on a back hinge with an amber latch. hollow: open, you see a lit floor inside"""
    g = Gun('crate'); palette(g)
    W, H, D, LH = CRATE['w'] / 2, CRATE['h'], CRATE['d'] / 2, CRATE['lid']
    T_ = 0.2  # wall
    # the shell: a floor and four walls (the ends sit between the long walls; the corner posts cover the joins)
    box(g, 'body__frame', (-W, W), (0.16, 0.62), (-D, D), bev=0.08)
    box(g, 'body__frame', (-W, W), (0.16, H), (-D, -D + T_), bev=0.08)
    box(g, 'body__frame', (-W, W), (0.16, H), (D - T_, D), bev=0.08)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * W, sx * (W - T_)))
        box(g, 'body__frame', (x0, x1), (0.16, H), (-D + T_ - 0.01, D - T_ + 0.01), bev=0.06)
    box(g, 'skid__dark', (-W - 0.05, W + 0.05), (0, 0.24), (-D - 0.05, D + 0.05), bev=0.07)
    # slate panels set into each face, two pressed ribs across the long ones
    for z0, z1 in ((-D - 0.03, -D), (D, D + 0.03)):
        box(g, 'panel__slate', (-W + 0.38, W - 0.38), (0.42, H - 0.26), (z0, z1), bev=0.04)
    for x0, x1 in ((-W - 0.03, -W), (W, W + 0.03)):
        box(g, 'panel__slate', (x0, x1), (0.42, H - 0.26), (-D + 0.36, D - 0.36), bev=0.04)
    for z0, z1 in ((-D - 0.07, -D), (D, D + 0.07)):
        for y in (0.84, 1.18):
            box(g, 'rib__frame', (-W + 0.52, W - 0.52), (y, y + 0.1), (z0, z1), bev=0.03)
    # steel corner posts, the full height (a flight case's extrusions)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, x1 = sorted((sx * (W - 0.26), sx * (W + 0.08)))
            z0, z1 = sorted((sz * (D - 0.26), sz * (D + 0.08)))
            box(g, 'guard__steel', (x0, x1), (0.02, H - 0.02), (z0, z1), bev=0.07)
    # side handles: a fat bar on two posts
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (W + 0.02), sx * (W + 0.22)))
        box(g, 'handle__dark', (x0, x1), (1.0, 1.14), (-0.5, 0.5), bev=0.04)
        for z in (-0.46, 0.34):
            box(g, 'handle__dark', (x0, x1), (0.86, 1.14), (z, z + 0.12), bev=0.03)
    # the catch the latch closes on
    box(g, 'catch__steel', (-0.26, 0.26), (H - 0.26, H - 0.08), (-D - 0.1, -D + 0.02), bev=0.03)
    # the light inside (on at the pop): the floor of the case
    box(g, 'glow__glow', (-W + 0.3, W - 0.3), (0.62, 0.66), (-D + 0.3, D - 0.3), bev=0.0)
    # THE LID (hinged at the back top edge): a thick charcoal slab, a slate top panel and lining, steel corner caps,
    # the amber latch
    y0, y1 = H, H + LH
    box(g, 'Lid-shell__frame', (-W - 0.04, W + 0.04), (y0, y1), (-D - 0.04, D + 0.04), bev=0.12)
    box(g, 'Lid-top__slate', (-W + 0.42, W - 0.42), (y1 - 0.02, y1 + 0.04), (-D + 0.38, D - 0.38), bev=0.03)
    box(g, 'Lid-lining__slate', (-W + 0.3, W - 0.3), (y0 - 0.03, y0 + 0.01), (-D + 0.3, D - 0.3), bev=0.02)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, x1 = sorted((sx * (W - 0.3), sx * (W + 0.12)))
            z0, z1 = sorted((sz * (D - 0.3), sz * (D + 0.12)))
            box(g, 'Lid-guard__steel', (x0, x1), (y0 + 0.06, y1 + 0.06), (z0, z1), bev=0.07)
    box(g, 'Lid-latch__amber', (-0.34, 0.34), (H - 0.2, y0 + 0.42), (-D - 0.2, -D - 0.04), bev=0.05)
    box(g, 'Lid-latchbar__dark', (-0.18, 0.18), (H - 0.12, H + 0.02), (-D - 0.24, -D - 0.18), bev=0.02)
    for x in (-W + 0.75, W - 0.75):
        g.cyl('hinge__steel', 0.1, (x - 0.3, H, D + 0.06), (x + 0.3, H, D + 0.06), sides=8, bev=0.02)
    info = {'open': 'hinge', 'height': H + LH,
            'groups': {'Lid': {'hinge': [0, H, D + 0.06], 'angle': 108}}}
    return g, info


# ------------------------------------------------------------------------------------------------- the duffel bag
def loaf(zh, h, r_top, r_bot, n=9):
    """the bag's cross-section [(z, y)]: a flat bottom, round shoulders, a round top (z = depth, y = height)"""
    pts = []
    def arc(cz, cy, r, a0, a1):
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cz + r * math.cos(a), cy + r * math.sin(a)))
    arc(zh - r_bot, r_bot, r_bot, -90, 0)
    arc(zh - r_top, h - r_top, r_top, 0, 90)
    arc(-zh + r_top, h - r_top, r_top, 90, 180)
    arc(-zh + r_bot, r_bot, r_bot, 180, 270)
    out = []
    for p in pts:
        if not out or (abs(out[-1][0] - p[0]) > 1e-6 or abs(out[-1][1] - p[1]) > 1e-6): out.append(p)
    return out


def clip(poly, keep):
    """Sutherland-Hodgman: the part of a closed outline where keep(p) >= 0 (keep is linear)"""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ka, kb = keep(a), keep(b)
        if ka >= 0: out.append(a)
        if (ka >= 0) != (kb >= 0):
            t = ka / (ka - kb)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def ccw(poly):
    s = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return poly if s > 0 else poly[::-1]


def bag():
    """a barrel duffel: olive canvas round on top, flat underneath, darker round end panels, two dark straps under
       it, a handle on each top flap, a steel zip track along the top with the amber pull. it opens down the zip:
       the pull runs end to end, then the two top flaps fall open to either side; hollow, lit inside"""
    g = Gun('bag'); palette(g)
    L, ZH, H = 1.85, 0.95, 1.8    # half length (x), half depth (z), height
    CUT = 1.22                    # where the flaps hinge (the top opens above this)
    WALL = 0.2
    sec = loaf(ZH, H, 0.92, 0.36)
    top = clip(sec, lambda p: p[1] - CUT)
    front = ccw(clip(top, lambda p: -p[0] - 0.02))    # z < 0: the front flap (FlapL)
    back = ccw(clip(top, lambda p: p[0] - 0.02))      # z > 0: the back flap (FlapR)
    floor = ccw(clip(sec, lambda p: (CUT - 0.36) - p[1]))
    band = clip(clip(sec, lambda p: p[1] - (CUT - 0.38)), lambda p: (CUT - 0.005) - p[1])
    wallF = ccw(clip(band, lambda p: -(ZH - WALL) - p[0]))
    wallB = ccw(clip(band, lambda p: p[0] - (ZH - WALL)))
    LEN = 2 * L - 0.3
    g.prism('body__olive', floor, LEN, bev=0.06)
    g.prism('body__olive', wallF, LEN, bev=0.03)
    g.prism('body__olive', wallB, LEN, bev=0.03)
    g.prism('FlapL-canvas__olive', front, LEN, bev=0.05)
    g.prism('FlapR-canvas__olive', back, LEN, bev=0.05)
    # piping along the seam where each flap meets the body (a darker welt)
    for sz in (-1, 1):
        zz = min(p[0] for p in top) if sz < 0 else max(p[0] for p in top)
        z0, z1 = sorted((zz - sz * 0.05, zz + sz * 0.06))
        g.box('piping__olived', (-L + 0.2, L - 0.2), (CUT - 0.07, CUT + 0.02), (z0, z1), bev=0.025)
    # the round end panels, a touch bigger than the section, full height: they stay put when it opens
    big = [(z * 1.04, y * 1.025 - 0.02) for z, y in sec]
    for sx in (-1, 1):
        g.prism('end__olived', big, 0.18, x=sx * (L - 0.06), bev=0.06)
        g.cyl('ring__steel', 0.16, (sx * (L + 0.02), 0.98, 0), (sx * (L + 0.14), 0.98, 0), sides=8, bev=0.025)
    # two dark straps round the underside, up to the seam
    strap = ccw([(z * 1.045, y * 1.02 - 0.015) for z, y in clip(sec, lambda p: (CUT - 0.04) - p[1])])
    for x in (-0.98, 0.98):
        g.prism('strap__dark', strap, 0.26, x=x, bev=0.03)
    # a pale scuff band round the bottom
    base = ccw([(z * 1.03, y - 0.005) for z, y in clip(sec, lambda p: 0.3 - p[1])])
    g.prism('band__pale', base, LEN - 0.04, bev=0.03)
    # the zip: a steel track along the top where the flaps meet, and the amber pull that runs along it
    g.box('track__steel', (-L + 0.25, L - 0.25), (H - 0.07, H + 0.02), (-0.06, 0.06), bev=0.02)
    g.box('Zip-pull__amber', (-L + 0.24, -L + 0.52), (H - 0.03, H + 0.11), (-0.13, 0.13), bev=0.035)
    g.box('Zip-tab__amber', (-L + 0.3, -L + 0.46), (H + 0.03, H + 0.08), (-0.5, -0.12), bev=0.02)
    # a handle on each flap: a fat loop standing off the canvas near the top
    for flap, sz in (('FlapL', -1), ('FlapR', 1)):
        z0, z1 = sorted((sz * 0.3, sz * 0.44))
        for x in (-0.66, 0.52):
            g.box(flap + '-handle__dark', (x, x + 0.14), (H - 0.22, H + 0.16), (z0, z1), bev=0.03)
        g.box(flap + '-handle__dark', (-0.66, 0.66), (H + 0.06, H + 0.2), (z0, z1), bev=0.04)
    # the light inside
    g.box('glow__glow', (-L + 0.4, L - 0.4), (CUT - 0.37, CUT - 0.33), (-ZH + 0.3, ZH - 0.3), bev=0.0)
    # the canvas shades round (soft cloth), its flat ends stay crisp
    for (node, slot), bm in g.pieces.items():
        if slot in ('olive', 'olived', 'dark', 'pale') and node.split('-')[-1] in ('body', 'canvas', 'end', 'strap', 'band'):
            bm.normal_update()
            for f in bm.faces:
                f.smooth = abs(f.normal.x) < 0.5
            for e in bm.edges:
                fs = e.link_faces
                e.smooth = len(fs) == 2 and fs[0].smooth and fs[1].smooth
    zl = min(p[0] for p in top if abs(p[1] - CUT) < 1e-6)
    zr = max(p[0] for p in top if abs(p[1] - CUT) < 1e-6)
    info = {'open': 'flap', 'height': H + 0.2, 'run': 2 * L - 0.76,
            'groups': {'FlapL': {'hinge': [0, CUT, zl], 'angle': -80}, 'FlapR': {'hinge': [0, CUT, zr], 'angle': 80},
                       'Zip': {}}}
    return g, info


# ------------------------------------------------------------------------------------------------- the spray can
def spray():
    """a big aerosol can: a charcoal label round most of it with one amber and one pale stripe, a steel foot and a
       steel domed shoulder with a rolled bead, and an amber cap the can's full width that pops off to show the nozzle
       and a light"""
    g = Gun('spray'); palette(g)
    R = 0.62
    up = lambda y0, y1: ((0, y0, 0), (0, y1, 0))
    g.cyl('rim__steel', R - 0.02, *up(0.0, 0.22), sides=16, bev=0.05)
    g.cyl('body__dark', R, *up(0.2, 2.56), sides=16, bev=0.03)
    g.cyl('stripe__amber', R + 0.018, *up(1.86, 2.02), sides=16, bev=0.015)
    g.cyl('stripe2__pale', R + 0.018, *up(0.44, 0.5), sides=16, bev=0.01)
    g.cyl('stripe2__pale', R + 0.018, *up(2.12, 2.18), sides=16, bev=0.01)
    g.cyl('shoulder__steel', R, *up(2.54, 2.8), sides=16, bev=0.04, r2=0.46)
    g.ring('bead__steel', 0.5, 0.36, *up(2.76, 2.86), sides=16, bev=0.02)
    g.cyl('top__dark', 0.4, *up(2.76, 2.84), sides=16, bev=0.02)
    g.cyl('stem__dark', 0.09, *up(2.82, 2.98), sides=8, bev=0.02)
    g.box('nozzle__pale', (-0.14, 0.14), (2.94, 3.16), (-0.16, 0.12), bev=0.04)
    g.box('nozzle__dark', (-0.05, 0.05), (3.01, 3.09), (-0.19, -0.15), bev=0.01)
    g.cyl('glow__glow', 0.34, *up(2.84, 2.87), sides=16, bev=0.0)
    # THE CAP: the can's full width, a soft-edged flat top; it pops straight up and tumbles off
    g.cyl('Cap-body__amber', R + 0.012, *up(2.7, 3.46), sides=16, bev=0.05, r2=R - 0.01)
    g.cyl('Cap-top__amber', R - 0.01, *up(3.44, 3.56), sides=16, bev=0.07, r2=R - 0.1)
    g.ring('Cap-rib__dark', R + 0.03, R - 0.08, *up(2.72, 2.84), sides=16, bev=0.02)
    info = {'open': 'pop', 'height': 3.56, 'groups': {'Cap': {'hinge': [0, 3.13, 0]}}}
    return g, info


BUILD = {'crate': crate, 'bag': bag, 'spray': spray}


# ------------------------------------------------------------------------------------------------- out
def look(slot):
    return ('n' if slot['kind'] == 'n' else 'p') + slot['color']


def to_scene(kind, at=Matrix.Identity(4), opened=0.0):
    """the container's pieces as objects (opened 0..1 poses its moving groups: previews only)"""
    g, info = BUILD[kind]()
    made = g.to_scene(at=at)
    keys = list(g.pieces.keys())
    for o, (node, slot) in zip(made, keys):
        o.name = '%s_%s__%s' % (kind, node, look(g.slots[slot]))
        grp = node.split('-')[0] if '-' in node else None
        if opened and grp:
            gi = info['groups'].get(grp, {})
            hx, hy, hz = gi.get('hinge', [0, 0, 0])
            hb = gunkit.P(hx, hy, hz)
            if grp == 'Zip':
                M = Matrix.Translation(Vector((info.get('run', 2.4) * opened, 0, 0)))
            elif info['open'] == 'pop':
                M = Matrix.Translation(Vector((0.5, 0, 1.6)) * opened) @ Matrix.Translation(hb) @ Matrix.Rotation(-0.9 * opened, 4, 'Y') @ Matrix.Translation(-hb)
            else:
                # (game: Angles(+a) about x in the Roblox frame = about Blender's x as well, with z-back -> -y)
                M = Matrix.Translation(hb) @ Matrix.Rotation(math.radians(gi.get('angle', 100)) * opened, 4, 'X') @ Matrix.Translation(-hb)
            o.matrix_world = at @ M
    return made, info, g


def export_all(out_dir):
    import rbxglb
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs, infos = [], {}
    for kind in BUILD:
        made, info, g = to_scene(kind)
        lo, hi = g.bounds()
        info['lo'], info['hi'], info['tris'], info['pieces'] = lo, hi, g.tris(), len(g.pieces)
        infos[kind] = info
        objs += made
    rbxglb.turn_for_roblox(objs)
    path = os.path.join(out_dir, 'loot_upload.glb')
    size = rbxglb.export_glb(path)
    json.dump(infos, open(os.path.join(out_dir, 'loot.json'), 'w'), indent=1)
    return path, size, infos


# ------------------------------------------------------------------------------------------------- previews
def preview(out_dir):
    W_, H_ = 1600, 900
    def reset():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 28; sc.cycles.use_denoising = True
        sc.render.resolution_x, sc.render.resolution_y = W_, H_
        sc.view_settings.view_transform = 'Standard'
        w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
        w.node_tree.nodes['Background'].inputs[0].default_value = (0.62, 0.64, 0.68, 1)
        w.node_tree.nodes['Background'].inputs[1].default_value = 0.55
        d = bpy.data.lights.new('sun', 'SUN'); d.energy = 3.2; d.angle = 0.25
        o = bpy.data.objects.new('sun', d); o.rotation_euler = Euler((math.radians(48), 0, math.radians(-35))); sc.collection.objects.link(o)
        # a floor
        bpy.ops.mesh.primitive_plane_add(size=60)
        fl = bpy.context.active_object
        m = bpy.data.materials.new('floor'); m.use_nodes = True
        m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.32, 0.33, 0.35, 1)
        m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.8
        fl.data.materials.append(m)
        return sc
    def camera(sc, loc, look, fov=32):
        cd = bpy.data.cameras.new('c'); o = bpy.data.objects.new('c', cd); sc.collection.objects.link(o)
        o.location = loc
        f = (Vector(look) - Vector(loc)).normalized()
        r = f.cross(Vector((0, 0, 1))).normalized(); u = r.cross(f)
        o.rotation_euler = Matrix((r, u, -f)).transposed().to_euler()
        cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(fov); cd.clip_end = 200
        sc.camera = o
    def shot(name, opened):
        sc = reset()
        xs = {'bag': -4.6, 'crate': 0.0, 'spray': 4.0}
        for kind, x in xs.items():
            # (each faces the camera a little turned: front = Roblox -z = Blender +y)
            at = Matrix.Translation(Vector((x, 0, 0))) @ Matrix.Rotation(math.radians(200), 4, 'Z')
            to_scene(kind, at=at, opened=opened)
        camera(sc, (1.2, -15.5, 6.2), (0, 0, 1.25), fov=30)
        sc.render.filepath = os.path.join(out_dir, name)
        bpy.ops.render.render(write_still=True)
        print('RENDER', sc.render.filepath)
    shot('loot_shut.png', 0.0)
    shot('loot_open.png', 1.0)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out_dir = argv[0]
    os.makedirs(out_dir, exist_ok=True)
    if '--preview' in argv:
        preview(out_dir)
    path, size, infos = export_all(out_dir)
    for k, v in infos.items():
        print('LOOT', k, v['tris'], 'tris', v['pieces'], 'pieces', 'lo', v['lo'], 'hi', v['hi'], 'groups', json.dumps(v['groups']))
    print('WROTE', path, size, 'bytes')
