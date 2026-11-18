# How far each weapon hat cuts into each gun (and the gun into the hat), measured on the models themselves, every hat
# on every gun, at the first-person size and at the third-person size (GunHats.THIRD). Headless Blender:
#
#   blender -b --factory-startup -P tools/roblox/hat_clip.py -- [--set kit] [--third 1.5] [--hat <id> ...] [gun ...]
#
# Writes roblox/assets/hats/clip_report.json. Named guns only update their own rows in it; no guns = every gun, the
# report written afresh; --hat = nothing written.
#
# Placement is the game's own (GunHats.attach): the foot on the gun's top under the spot, `sink` into it, lifted by the
# spot's saddle, turned by yaw / pitch, sized by s (x THIRD in third person); the googly eyes (round 13) at their own
# height, upright and with no saddle (hat_models.eyes_seat, GunHats' seatOf). The moving bits are swept: the
# propeller round its axis, the halo through its bob, the pupils through their rattle. A point counts as inside a solid when it is behind the nearest face of that
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
ONLY = [argv[i + 1] for i, a in enumerate(argv) if a == '--hat']  # (--hat <id>: that hat only; the report is then not written)
argv = [a for i, a in enumerate(argv) if a not in ('--set', '--third', '--spots', '--hat') and (i == 0 or argv[i - 1] not in ('--set', '--third', '--spots', '--hat'))]
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


def hat_points(h, M, moves, seated=()):
    """(foot points, body points, [body islands]) in Blender world, the moving bits swept. seated = nodes that stand on
       the gun themselves (hat_models.SEATED: the googly eyes' balls): they count as the foot"""
    foot, body, bpieces = [], [], []
    for (node, slot), bm in h.pieces.items():
        mv = moves.get(node)
        frames = [Matrix.Identity(4)]
        if mv and mv['kind'] == 'spin':
            frames = [Matrix.Rotation(math.radians(a), 4, 'Z') for a in range(0, 360, 15)]
        elif mv and mv['kind'] == 'bob':
            frames = [Matrix.Translation(Vector((0, 0, d * mv['amp']))) for d in (-1, 0, 1)]
        elif mv and mv['kind'] == 'rattle':  # (u, v in the hat frame: x right, y up, z back -> Blender x, -z, y)
            u = Vector((mv['u'][0], -mv['u'][2], mv['u'][1])) * mv['amp']
            v = Vector((mv['v'][0], -mv['v'][2], mv['v'][1])) * mv['amp']
            frames = [Matrix.Translation(u * a + v * b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
        pts = [M @ (fr @ v.co) for fr in frames for v in bm.verts]
        (foot if node == 'foot' or node in seated else body).extend(pts)
        # (the hat's own solids, placed, for the gun-into-hat test: only the rest pose)
        b2 = bm.copy(); b2.transform(M); bpieces.append(('foot' if node in seated else node, b2))
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
        topf = lambda a, b: gun_top(gisl, a, b)
        for scale_name, boost in (('fp', 1.0), ('tp', THIRD)):
            for hid in (ONLY or hat_models.HATS):
                h = hat_models.make(hid)
                # (the saddle lifts the hat along its own up, after the turn, as GunHats.make does: off the end of a
                # pitch-90 seat, not straight up)
                mw = (Matrix.Translation(Vector((x, y, z)))
                      @ Matrix.Rotation(math.radians(sp.get('yaw', 0)), 4, 'Y')
                      @ Matrix.Rotation(math.radians(sp.get('pitch', 0)), 4, 'X')
                      @ Matrix.Translation(Vector((0, sp.get('saddle', 0.0) * boost, 0)))
                      @ Matrix.Scale(sp.get('s', 1.0) * boost, 4))
                if hid in hat_models.SEATED:
                    # (the googly eyes stand on the gun themselves: their own height at this size, upright, no saddle)
                    # (at their own size: EYES_GROW times the seat's, as GunHats draws them since 18 Nov 2026)
                    g_ = hat_models.SIZE.get(hid, 1.0)
                    ex, _, _, ez = hat_models.eyes_seat(topf, sp)
                    ey = hat_models.eyes_rest(topf, ex, ez, sp.get('yaw', 0), sp.get('s', 1.0) * boost * g_)
                    mw = (Matrix.Translation(Vector((ex, ey, ez))) @ Matrix.Rotation(math.radians(sp.get('yaw', 0)), 4, 'Y')
                          @ Matrix.Scale(sp.get('s', 1.0) * boost * g_, 4))
                M = to_blender(mw)
                foot, body, bpieces = hat_points(h, M, hat_models.MOVES.get(hid, {}), hat_models.SEATED.get(hid, ()))
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
    if ONLY: return
    out = os.path.join(HERE, '..', '..', 'roblox', 'assets', 'hats', 'clip_report.json')
    new = [dict(zip(('gun', 'view', 'hat', 'foot_mm', 'body_mm', 'gun_mm', 'foot_on', 'body_on', 'gun_piece'), r)) for r in rows]
    if argv and os.path.exists(out):
        # (a gun list: those guns' rows replace theirs in the full report, in place, and new ones go on the end; the rest
        # of the report stays. Only a run over every gun writes the report from scratch)
        key = lambda r: (r['gun'], r['view'], r['hat'])
        fresh = {key(r): r for r in new}
        old = json.load(open(out))
        merged = [fresh.pop(key(r), r) for r in old]
        new = merged + [r for r in new if key(r) in fresh]
        print('MERGED %d rows into the report (%d new)' % (len(rows), len(new) - len(old)))
    json.dump(new, open(out, 'w'), indent=0)
    print('WROTE', out, len(new), 'rows')


if __name__ == '__main__':
    main()
