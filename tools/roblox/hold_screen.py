# Where each first-person weapon sits on a 16:9 screen at rest, computed the way the game places it (Viewmodel.luau):
# the gun's root at camera * (vm.p + shift * S) * Euler(vm.r + tilt), the file's metres times k = S * vm.s * size, and
# the camera at the game's default vertical FOV of 80 (or --fov). Every piece of the gun is its box from the kit's export report (8
# corners), which is close to its outline for these chunky models. Prints, per weapon: the muzzle's spot, the box the
# gun covers (left, right, top, bottom; bottom is cut at the screen's edge) and how wide and tall that is, in % of the
# screen from the top left (the crosshair is 50, 50). Used to put our guns where the Rivals-class measurements say
# (the vault's Research note "Rivals first-person holds").
#   py tools/roblox/hold_screen.py [--fov 70] [--holds other.json] [--look before|after|combined] [--ads] [id ...]   (--ads: the aimed view)
import json, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from holds_lib import angles, mvec, read_vm

S = 3


def read_muzzles():
    src = open(os.path.join(ROOT, 'roblox/src/shared/Weapons.luau'), encoding='utf-8').read()
    out = {}
    ids = [(m.start(), m.group(1)) for m in re.finditer(r'\bid = "(\w+)"', src)]
    for i, (at, wid) in enumerate(ids):
        end = ids[i + 1][0] if i + 1 < len(ids) else len(src)
        m = re.search(r'muzzle = Vector3\.new\(([^)]*)\)', src[at:end])
        if m: out[wid] = [float(x) for x in m.group(1).split(',')]
    return out


def boxes(wid):
    rep = json.load(open(os.path.join(ROOT, 'roblox/assets/weapons-kit/export_report.json'), encoding='utf-8'))
    r = rep.get('w_' + wid)
    if not r: return []
    return [(p['lo'], p['hi']) for p in r['pieces']]


def project(c, fov, aspect=16 / 9):
    """camera space (x right, y up, -z ahead) -> screen % from the top left, or None behind the near plane"""
    if c[2] > -0.1: return None
    t = math.tan(math.radians(fov) / 2)
    x = c[0] / (-c[2] * t * aspect)
    y = c[1] / (-c[2] * t)
    return (50 + 50 * x, 50 - 50 * y)


LOOK = None  # (--look before|after|combined: that look on every weapon; else each weapon's "use")


def row_of(holds, wid):
    """a weapon's row with its look's shift / scale / tilt / aimZ laid on top"""
    row = dict(holds.get(wid, {}))
    if row.get('looks'): row.update(row['looks'][LOOK or row['use']])
    return row


def place(wid, vm, holds, q):
    """a file point (metres) of this weapon -> camera space (studs) at rest"""
    p, r, s = vm[wid]
    row = row_of(holds, wid)
    size = holds.get('_size', 1) * row.get('scale', 1)
    k = S * s * size
    pos = [p[i] * S + (row.get('shift') or [0, 0, 0])[i] * S for i in range(3)]
    tilt = row.get('tilt') or [0, 0, 0]
    R = angles([r[i] + math.radians(tilt[i]) for i in range(3)])
    v = mvec(R, [c * k for c in q])
    return [pos[i] + v[i] for i in range(3)], k


def measure(wid, vm, holds, fov):
    mz = read_muzzles().get(wid)
    pts = []
    for lo, hi in boxes(wid):
        for cx in (lo[0], hi[0]):
            for cy in (lo[1], hi[1]):
                for cz in (lo[2], hi[2]):
                    c, k = place(wid, vm, holds, (cx, cy, cz))
                    pts.append(c)
    scr = [project(c, fov) for c in pts]
    vis = [s for s in scr if s]
    near = min(-c[2] for c in pts)
    out = {'near': near}
    if vis:
        L = max(0, min(s[0] for s in vis)); R = min(100, max(s[0] for s in vis))
        T = max(0, min(s[1] for s in vis)); B = min(100, max(s[1] for s in vis))
        if len(vis) < len(scr): B = 100  # something reaches behind the near plane: it runs off the bottom
        out.update(L=L, R=R, T=T, B=B, W=R - L, H=B - T)
    if mz:
        c, k = place(wid, vm, holds, mz)
        out['muzzle'] = project(c, fov)
        out['k'] = k
    for side in ('R', 'L'):
        h = holds.get(wid, {}).get(side)
        if h:
            c, _ = place(wid, vm, holds, h['at'])
            out['hand' + side] = project(c, fov)
    return out


def read_ads():
    """{ id: (sight file point or None, zoom) } from Weapons.luau"""
    src = open(os.path.join(ROOT, 'roblox/src/shared/Weapons.luau'), encoding='utf-8').read()
    out = {}
    ids = [(m.start(), m.group(1)) for m in re.finditer(r'\bid = "(\w+)"', src)]
    for i, (at, wid) in enumerate(ids):
        end = ids[i + 1][0] if i + 1 < len(ids) else len(src)
        body = src[at:end]
        z = re.search(r'ads = \{ zoom = ([\d.]+)', body)
        sg = re.search(r'sight = Vector3\.new\(([^)]*)\)', body)
        if z: out[wid] = ([float(x) for x in sg.group(1).split(',')] if sg else None, float(z.group(1)), 'scope = true' in body)
    return out


def measure_ads(wid, vm, holds, fov):
    """the gun's screen box while aiming (Viewmodel.adsPos: the sight on the screen's centre line, no turn), at the
       aimed FOV (fov / zoom)"""
    ads = read_ads().get(wid)
    if not ads: return None
    sight, zoom, scoped = ads
    p, r, s = vm[wid]
    row = row_of(holds, wid)
    size = holds.get('_size', 1) * row.get('scale', 1)
    k = S * s * size
    back = row.get('aimZ', 0)
    if wid == 'redline': sight = [0, 0.0737, 0.1058]
    if sight: pos = [0, -sight[1] * s * size * S, (-0.17 - back - sight[2] * s * size) * S]
    else: pos = [0.06 * S, min(-0.1, -0.03 - 0.1479 * s * size) * S, (-0.3 - back) * S]
    f = fov / zoom
    pts = []
    for lo, hi in boxes(wid):
        for cx in (lo[0], hi[0]):
            for cy in (lo[1], hi[1]):
                for cz in (lo[2], hi[2]):
                    pts.append([pos[0] + cx * k, pos[1] + cy * k, pos[2] + cz * k])
    scr = [project(c, f) for c in pts]
    vis = [q for q in scr if q]
    out = {'zoom': zoom, 'scoped': scoped, 'near': min(-c[2] for c in pts)}
    if vis:
        out.update(L=max(0, min(q[0] for q in vis)), R=min(100, max(q[0] for q in vis)), T=max(0, min(q[1] for q in vis)),
                   B=100 if len(vis) < len(scr) else min(100, max(q[1] for q in vis)))
        out['W'] = out['R'] - out['L']
    return out


def main():
    args = sys.argv[1:]
    fov = 80  # the game's default (JankSettings: S.fov = 80; the P menu changes it)
    hp = os.path.join(HERE, 'holds.json')
    if '--fov' in args:
        i = args.index('--fov'); fov = float(args[i + 1]); del args[i:i + 2]
    global LOOK
    if '--look' in args:
        i = args.index('--look'); LOOK = args[i + 1]; del args[i:i + 2]
    if '--holds' in args:
        i = args.index('--holds'); hp = args[i + 1]; del args[i:i + 2]
    holds = json.load(open(hp, encoding='utf-8'))
    vm = read_vm()
    if '--ads' in args:
        args.remove('--ads')
        print('weapon     zoom  left  right   top  bottom  wide  nearest   (aiming: the gun on the screen at fov / zoom)')
        for wid in (args or list(read_ads())):
            m = measure_ads(wid, vm, holds, fov)
            if m and 'L' in m:
                print('%-9s %5.2f %5.1f %5.1f %5.1f %5.1f %5.1f   %.2f%s' % (wid, m['zoom'], m['L'], m['R'], m['T'], m['B'], m['W'], m['near'], '  (scope overlay)' if m['scoped'] else ''))
        return
    ids = args or [w for w in vm if os.path.exists(os.path.join(ROOT, 'roblox/assets/weapons-kit/w_%s.glb' % w))]
    f = lambda v: '%5.1f' % v
    print('weapon     muzzle x,y     left  right   top  bottom | wide  tall | hand R x,y   hand L x,y   nearest(studs)')
    for wid in ids:
        m = measure(wid, vm, holds, fov)
        mz = m.get('muzzle'); hr = m.get('handR'); hl = m.get('handL')
        print('%-9s %s %s   %s %s %s %s | %s %s | %s %s %s' % (
            wid, f(mz[0]) if mz else '  -  ', f(mz[1]) if mz else '  -  ',
            f(m.get('L', 0)), f(m.get('R', 0)), f(m.get('T', 0)), f(m.get('B', 0)), f(m.get('W', 0)), f(m.get('H', 0)),
            ('%5.1f,%5.1f' % hr) if hr else '     -     ', ('%5.1f,%5.1f' % hl) if hl else '     -     ', '%.2f' % m['near']))


if __name__ == '__main__':
    main()
