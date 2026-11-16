# How far each weapon hat cuts into each gun (and the gun into the hat), measured on the models themselves, every hat
# on every gun, at the first-person size and at the third-person size (GunHats.THIRD). Headless Blender:
#
#   blender -b --factory-startup -P tools/roblox/hat_clip.py -- [--set kit] [--third 1.5] [gun ...]
#
# Placement is the game's own (GunHats.attach): the foot on the gun's top under the spot, `sink` into it, lifted by the
# spot's saddle, turned by yaw / pitch, sized by s (x THIRD in third person). The moving bits are swept: the propeller
# round its axis, the halo through its bob. A point counts as inside a solid when it is behind the nearest face of that
# solid (each gun and hat piece is split into its closed solids first, since solids overlap inside a piece).
# Reported per pair: FOOT = how deep the hat's foot goes in (it is meant to sit `sink` = 2 mm in), BODY = how deep the
# rest of the hat goes in, GUN = how deep any part of the gun goes into the hat. mm in the gun's own metres; the worst
# solid of the gun is named. Nothing is changed: it only reports.
import bpy, bmesh, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
import hat_models

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--set' in argv and argv[argv.index('--set') + 1] == 'kit':
    import gun_models as GUNS
else:
    import gun_set as GUNS
THIRD = 1.5
if '--third' in argv: THIRD = float(argv[argv.index('--third') + 1])
argv = [a for i, a in enumerate(argv) if a not in ('--set', '--third', '--spots') and (i == 0 or argv[i - 1] not in ('--set', '--third', '--spots'))]
HERE = os.path.dirname(os.path.abspath(__file__))
SPOT_FILE = os.path.join(HERE, 'hat_spots.json')
if '--spots' in sys.argv: SPOT_FILE = sys.argv[sys.argv.index('--spots') + 1]  # (try other seats)
SPOTS = json.load(open(SPOT_FILE))
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # weapon frame -> Blender


def to_blender(mf): return C @ mf @ C.inverted()


def build(wid):
    if '@' in wid: return GUNS.SKINS[wid]()
    return GUNS.BUILD[wid]()


def islands(pieces):
    """every closed solid of every piece: [(name, bvh, lo, hi)]"""
    out = []
    for name, bm in pieces:
        bm.faces.ensure_lookup_table()
        seen = set()
        for f0 in bm.faces:
            if f0.index in seen: continue
            stack, comp = [f0], []
            seen.add(f0.index)
            while stack:
                f = stack.pop()
                comp.append(f)
                for e in f.edges:
                    for g in e.link_faces:
                        if g.index not in seen:
                            seen.add(g.index); stack.append(g)
            vidx = {}
            verts, polys = [], []
            for f in comp:
                poly = []
                for v in f.verts:
                    if v.index not in vidx:
                        vidx[v.index] = len(verts); verts.append(v.co.copy())
                    poly.append(vidx[v.index])
                polys.append(poly)
            lo = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
            hi = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
            out.append((name, BVHTree.FromPolygons(verts, polys), lo, hi))
    return out


RAYS = (Vector((0.5774, 0.5774, 0.5774)), Vector((-0.6, 0.3, 0.7416)).normalized(), Vector((0.2, -0.9, 0.3873)).normalized())


def crossings(bvh, p, d):
    n, o = 0, p.copy()
    for _ in range(64):
        hit = bvh.ray_cast(o, d)
        if hit[0] is None: break
        n += 1
        o = hit[0] + d * 1e-6
    return n


def depth_inside(points, isl, pad=0.0005):
    """the deepest any point goes inside any solid: (depth, solid name). inside = an odd number of crossings along at
       least two of three rays (each solid is closed), depth = the distance to its nearest face"""
    best, who = 0.0, '-'
    for name, bvh, lo, hi in isl:
        for p in points:
            if not (lo.x - pad <= p.x <= hi.x + pad and lo.y - pad <= p.y <= hi.y + pad and lo.z - pad <= p.z <= hi.z + pad):
                continue
            loc, nrm, _, dist = bvh.find_nearest(p)
            if loc is None or dist <= best: continue
            if sum(crossings(bvh, p, d) % 2 for d in RAYS) >= 2:
                best, who = dist, name
    return best, who


def gun_top(isl, x, z):
    best = None
    for name, bvh, lo, hi in isl:
        hit = bvh.ray_cast(Vector((x, -z, 1.0)), Vector((0, 0, -1)))
        if hit[0] is not None and (best is None or hit[0].z > best): best = hit[0].z
    return best


def hat_points(h, M, moves):
    """(foot points, body points, [body islands]) in Blender world, the moving bits swept"""
    foot, body, bpieces = [], [], []
    for (node, slot), bm in h.pieces.items():
        mv = moves.get(node)
        frames = [Matrix.Identity(4)]
        if mv and mv['kind'] == 'spin':
            frames = [Matrix.Rotation(math.radians(a), 4, 'Z') for a in range(0, 360, 15)]
        elif mv and mv['kind'] == 'bob':
            frames = [Matrix.Translation(Vector((0, 0, d * mv['amp']))) for d in (-1, 0, 1)]
        pts = [M @ (fr @ v.co) for fr in frames for v in bm.verts]
        (foot if node == 'foot' else body).extend(pts)
        # (the hat's own solids, placed, for the gun-into-hat test: only the rest pose)
        b2 = bm.copy(); b2.transform(M); bpieces.append((node, b2))
    return foot, body, bpieces


def main():
    guns = argv or [k for k in SPOTS if not k.startswith('_')]
    rows = []
    for wid in guns:
        sp = SPOTS.get(wid) or SPOTS.get(wid.split('@')[0])
        g = build(wid)
        gisl = islands([('%s__%s' % k, bm) for k, bm in g.pieces.items()])
        gverts = [v.co.copy() for bm in g.pieces.values() for v in bm.verts]
        x, z = sp.get('x', 0.0), sp['z']
        if 'y' in sp: y = sp['y'] - sp.get('sink', 0.0)
        else: y = gun_top(gisl, x, z) - sp.get('sink', 0.002)
        for scale_name, boost in (('fp', 1.0), ('tp', THIRD)):
            for hid in hat_models.HATS:
                h = hat_models.make(hid)
                mw = (Matrix.Translation(Vector((x, y + sp.get('saddle', 0.0) * boost, z)))
                      @ Matrix.Rotation(math.radians(sp.get('yaw', 0)), 4, 'Y')
                      @ Matrix.Rotation(math.radians(sp.get('pitch', 0)), 4, 'X')
                      @ Matrix.Scale(sp.get('s', 1.0) * boost, 4))
                M = to_blender(mw)
                foot, body, bpieces = hat_points(h, M, hat_models.MOVES.get(hid, {}))
                fd, fw = depth_inside(foot, gisl)
                bd, bw = depth_inside(body, gisl)
                hisl = islands(bpieces)
                lo = Vector((min(p.x for p in foot + body), min(p.y for p in foot + body), min(p.z for p in foot + body)))
                hi = Vector((max(p.x for p in foot + body), max(p.y for p in foot + body), max(p.z for p in foot + body)))
                near = [v for v in gverts if lo.x <= v.x <= hi.x and lo.y <= v.y <= hi.y and lo.z <= v.z <= hi.z]
                gd, gw = depth_inside(near, [i for i in hisl if i[0] != 'foot'])
                for _, b2 in bpieces: b2.free()
                rows.append((wid, scale_name, hid, fd * 1000, bd * 1000, gd * 1000, fw, bw, gw))
                print('CLIP %-14s %s %-9s foot %5.1f body %5.1f gun %5.1f   %s | %s | %s' % (wid, scale_name, hid, fd * 1000, bd * 1000, gd * 1000, fw, bw, gw))
        for bm in g.pieces.values(): bm.free()
    out = os.path.join(HERE, '..', '..', 'roblox', 'assets', 'hats', 'clip_report.json')
    json.dump([dict(zip(('gun', 'view', 'hat', 'foot_mm', 'body_mm', 'gun_mm', 'foot_on', 'body_on', 'gun_piece'), r)) for r in rows],
              open(out, 'w'), indent=0)
    print('WROTE', out)


if __name__ == '__main__':
    main()
