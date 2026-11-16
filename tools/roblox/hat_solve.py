# Find a hat seat on a gun (or a gun skin) where no hat clips: searches along the gun's top round its spot in
# hat_spots.json (the base gun's spot for a skin), with a saddle and a smaller size as the last resorts, and scores
# each seat by the worst clip of every hat at the third-person size (GunHats.THIRD, the biggest), measured like
# hat_clip.py. Headless Blender:
#
#   blender -b --factory-startup -P tools/roblox/hat_solve.py -- [--write] <gun or gun@skin> ...
#
# prints the best seat per gun; --write puts it into hat_spots.json (with a note saying it was solved). Then run
# hat_spots.py and check the result from the side and from the eye (hat_preview.py).
import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Matrix, Vector
import hat_clip as HC
import hat_models

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
WRITE = '--write' in argv
ids = [a for a in argv if not a.startswith('--')]
OK_MM = 1.0       # a seat passes when every hat's clip score is at most this (mm)
FOOT_MM = 3.0     # a foot may sit this far in (its design sink is 2 mm)
DZ = [d / 100 for d in (0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6, -8, 8, -10, 10, -12, 12)]
SADDLES = (0.0, 0.003, 0.006, 0.01, 0.015)
SIZES = (1.0, 0.9, 0.8)


def score(gisl, gverts, x, y, z, sp, s, saddle, boost, hats):
    worst = 0.0
    for hid, h in hats:
        mw = (Matrix.Translation(Vector((x, y + saddle * boost, z)))
              @ Matrix.Rotation(math.radians(sp.get('yaw', 0)), 4, 'Y')
              @ Matrix.Rotation(math.radians(sp.get('pitch', 0)), 4, 'X')
              @ Matrix.Scale(s * boost, 4))
        M = HC.to_blender(mw)
        foot, body, bpieces = HC.hat_points(h, M, hat_models.MOVES.get(hid, {}))
        foot, body = foot[::2], body[::2]
        fd, _ = HC.depth_inside(foot, gisl)
        bd, _ = HC.depth_inside(body, gisl)
        hisl = HC.islands(bpieces)
        pts = foot + body
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        near = [v for v in gverts if lo.x <= v.x <= hi.x and lo.y <= v.y <= hi.y and lo.z <= v.z <= hi.z]
        gd, _ = HC.depth_inside(near, [i for i in hisl if i[0] != 'foot'])
        for _, b2 in bpieces: b2.free()
        sc = max(0.0, fd * 1000 - FOOT_MM) + bd * 1000 + gd * 1000
        worst = max(worst, sc)
        if worst > 30: break
    return worst


def gun_back(gisl, x, y):
    """the back end of the gun along +z at (x, y) (weapon frame): where a hat stood on the pommel sits"""
    best = None
    for name, bvh, lo, hi in gisl:
        hit = bvh.ray_cast(Vector((x, -1.0, y)), Vector((0, 1, 0)))  # (Blender: from far behind toward the muzzle)
        if hit[0] is not None:
            zz = -hit[0].y
            if best is None or zz > best: best = zz
    return best


def solve(wid):
    spots = HC.SPOTS
    base = spots.get(wid) or spots.get(wid.split('@')[0])
    g = HC.build(wid)
    gisl = HC.islands([('%s__%s' % k, bm) for k, bm in g.pieces.items()])
    gverts = [v.co.copy() for bm in g.pieces.values() for v in bm.verts]
    hats = [(hid, hat_models.make(hid)) for hid in hat_models.HATS]
    x, z0, s0 = base.get('x', 0.0), base['z'], base.get('s', 1.0)
    if base.get('pitch') == 90:  # (a hat stood on the back end: its seat is that end, its height the spot's)
        back = gun_back(gisl, x, base.get('y', 0.0))
        z0 = back - base.get('sink', 0.002) if back is not None else z0
    best = None
    tried = 0
    for size in SIZES:
        for saddle in SADDLES:
            for dz in DZ:
                z = z0 + dz
                if base.get('pitch') == 90:
                    if dz != 0: continue
                    y = base.get('y', 0.0)
                elif 'y' in base and dz == 0: y = base['y'] - base.get('sink', 0.0)
                else:
                    top = HC.gun_top(gisl, x, z)
                    if top is None: continue
                    y = top - base.get('sink', 0.002)
                tried += 1
                sc = score(gisl, gverts, x, y, z, base, s0 * size, saddle, HC.THIRD, hats)
                if sc <= OK_MM: sc = max(sc, score(gisl, gverts, x, y, z, base, s0 * size, saddle, 1.0, hats))
                cost = abs(dz) * 100 + saddle * 1000 * 0.5 + (1 - size) * 30
                if best is None or (sc <= OK_MM and (best[0] > OK_MM or cost < best[1])) or (best[0] > OK_MM and sc < best[0]):
                    best = (sc, cost, z, saddle, s0 * size)
                if sc <= OK_MM and dz == 0 and saddle == 0.0: break
            if best and best[0] <= OK_MM: break
        if best and best[0] <= OK_MM: break
    # (the same seat at the first-person size must pass too)
    yb = base.get('y', 0.0) if base.get('pitch') == 90 else HC.gun_top(gisl, x, best[2]) - base.get('sink', 0.002)
    fp = score(gisl, gverts, x, yb, best[2], base, best[4], best[3], 1.0, hats)
    for bm in g.pieces.values(): bm.free()
    return {'score_tp': round(best[0], 2), 'score_fp': round(fp, 2), 'z': round(best[2], 4), 'saddle': best[3], 's': round(best[4], 3), 'tried': tried,
            'base_z': z0, 'base_s': s0}


def main():
    out = {}
    for wid in ids:
        r = solve(wid)
        out[wid] = r
        print('SOLVE %-28s tp %5.2f fp %5.2f  z %7.3f (base %7.3f)  saddle %.3f  s %.2f (base %.2f)  [%d tried]' % (
            wid, r['score_tp'], r['score_fp'], r['z'], r['base_z'], r['saddle'], r['s'], r['base_s'], r['tried']))
    if WRITE:
        p = os.path.join(HC.HERE, 'hat_spots.json')
        d = json.load(open(p, encoding='utf8'))
        for wid, r in out.items():
            base = d.get(wid) or d.get(wid.split('@')[0])
            e = {k: v for k, v in base.items() if k not in ('z', 's', 'saddle', 'note', 'y')}
            e['z'] = r['z']; e['s'] = r['s']
            if r['saddle']: e['saddle'] = r['saddle']
            e['note'] = 'solved by hat_solve.py: worst clip %.1f mm (third person), %.1f mm (first)' % (r['score_tp'], r['score_fp'])
            d[wid] = e
        lines = ['{', '  "_": %s,' % json.dumps(d['_'])]
        keys = [k for k in d if k != '_']
        for n, k in enumerate(keys):
            lines.append('  "%s": %s%s' % (k, json.dumps(d[k]), ',' if n < len(keys) - 1 else ''))
        lines.append('}')
        open(p, 'w', encoding='utf8', newline='\n').write('\n'.join(lines) + '\n')
        print('WROTE', p)


main()
