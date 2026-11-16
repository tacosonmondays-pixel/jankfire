# Where each first-person weapon sits on a 16:9 screen at rest, computed the way the game places it (Viewmodel.luau):
# the gun's root at camera * (vm.p + shift * S) * Euler(vm.r + tilt), the file's metres times k = S * vm.s * size, and
# the camera at the game's default vertical FOV of 80 (or --fov). Every piece of the gun is its box from the kit's export report (8
# corners), which is close to its outline for these chunky models. Prints, per weapon: the muzzle's spot, the box the
# gun covers (left, right, top, bottom; bottom is cut at the screen's edge) and how wide and tall that is, in % of the
# screen from the top left (the crosshair is 50, 50). Used to put our guns where the Rivals-class measurements say
# (the vault's Research note "Rivals first-person holds").
#   py tools/roblox/hold_screen.py [--fov 70] [--holds other.json] [--look before|after|combined] [--ads] [id ...]
#   --ads: the aimed view, measured on the guns' real triangles (an id may be id@skin): how much of the screen it
#   covers, the top of its body, where it leaves the bottom edge, the sight's box (Rivals' rifles: about 8 % covered,
#   the body's top at 52, leaving the bottom at 40 to 60)
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


GX, GY = 192, 108  # the raster the aimed view is measured on (16:9)
NEAR = 0.1  # the camera's near plane (studs)


def tris(key):
    """{piece name: (n, 3, 3) triangles} of w_<key>.glb (key = id or id@skin) in the file's frame (x right, y up,
       z back, metres): the glb is the file turned half round about y"""
    import struct
    import numpy as np
    b = open(os.path.join(ROOT, 'roblox/assets/weapons-kit/w_%s.glb' % key), 'rb').read()
    L = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + L])
    off = 20 + L; L2 = struct.unpack('<I', b[off:off + 4])[0]; bn = b[off + 8:off + 8 + L2]
    out = {}
    for n in j['nodes']:
        if 'mesh' not in n: continue
        for pr in j['meshes'][n['mesh']]['primitives']:
            a = j['accessors'][pr['attributes']['POSITION']]; bv = j['bufferViews'][a['bufferView']]
            pos = np.frombuffer(bn, dtype='<f4', count=a['count'] * 3, offset=bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, 3) * np.array([-1, 1, -1])
            ia = j['accessors'][pr['indices']]; ibv = j['bufferViews'][ia['bufferView']]
            idx = np.frombuffer(bn, dtype={5121: 'u1', 5123: '<u2', 5125: '<u4'}[ia['componentType']], count=ia['count'], offset=ibv.get('byteOffset', 0) + ia.get('byteOffset', 0)).reshape(-1, 3)
            out.setdefault('__'.join(n['name'].split('__')[:2]), []).append(pos[idx])
    return {k: np.concatenate(v) for k, v in out.items()}


def raster(tri_list, pos, k, fov, aspect=16 / 9):
    """the screen cells (GY x GX) these triangles cover, the gun unturned at pos (camera space, studs), clipped at the
       near plane"""
    import numpy as np
    m = np.zeros((GY, GX), bool)
    t = math.tan(math.radians(fov) / 2)
    xs = (np.arange(GX) + 0.5) * 100 / GX; ys = (np.arange(GY) + 0.5) * 100 / GY
    for T in tri_list:
        for tri in T * k + np.array(pos):
            poly = []
            for i in range(3):
                A, B = tri[i], tri[(i + 1) % 3]
                if A[2] <= -NEAR: poly.append(A)
                if (A[2] <= -NEAR) != (B[2] <= -NEAR): poly.append(A + (B - A) * ((-NEAR - A[2]) / (B[2] - A[2])))
            P = [(50 + 50 * q[0] / (-q[2] * t * aspect), 50 - 50 * q[1] / (-q[2] * t)) for q in poly]
            for i in range(1, len(P) - 1):
                a, b, c = P[0], P[i], P[i + 1]
                d = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
                if abs(d) < 1e-12: continue
                gx0, gx1 = max(0, int(min(a[0], b[0], c[0]) * GX / 100)), min(GX, int(max(a[0], b[0], c[0]) * GX / 100) + 1)
                gy0, gy1 = max(0, int(min(a[1], b[1], c[1]) * GY / 100)), min(GY, int(max(a[1], b[1], c[1]) * GY / 100) + 1)
                if gx1 <= gx0 or gy1 <= gy0: continue
                X, Y = np.meshgrid(xs[gx0:gx1], ys[gy0:gy1])
                w0 = ((b[0] - X) * (c[1] - Y) - (b[1] - Y) * (c[0] - X)) / d
                w1 = ((c[0] - X) * (a[1] - Y) - (c[1] - Y) * (a[0] - X)) / d
                m[gy0:gy1, gx0:gx1] |= (w0 >= 0) & (w1 >= 0) & (1 - w0 - w1 >= 0)
    return m


def measure_ads(key, vm, holds, fov):
    """a gun (or id@skin) fully aimed, the way Viewmodel.adsPos places it: the aim line on the screen's centre, no
       turn, 0.17 m + aimZ from the eye, pushed back by the zoom (so the zoom never enlarges it), the camera at
       fov / zoom; a skin's hidden pieces left out. Returns % of the screen covered, the body's top, where it leaves
       the bottom edge and the sight pieces' box"""
    import numpy as np
    wid, skin = (key.split('@') + [None])[:2]
    ads = read_ads().get(wid)
    if not ads: return None
    sight, zoom, scoped = ads
    p, r, s = vm[wid]
    row = row_of(holds, wid)
    a = holds.get(wid, {}).get('ads', {})
    sk = a.get('skins', {}).get(skin, {}) if skin else {}
    size = holds.get('_size', 1) * row.get('scale', 1)
    k = S * s * size
    f = fov / zoom
    back = (0.17 + sk.get('aimZ', a.get('aimZ', 0))) * math.tan(math.radians(fov) / 2) / math.tan(math.radians(f) / 2)
    sight = sk.get('sight') or a.get('sight') or sight
    if sight: pos = [0, -sight[1] * s * size * S, (-back - sight[2] * s * size) * S]
    else: pos = [0.06 * S, min(-0.1, -0.03 - 0.1479 * s * size) * S, (-back - 0.13) * S]
    hide = [h.lower() for h in sk.get('hide', [])]
    T = {n: v for n, v in tris(key).items() if n.lower() not in hide}
    body = raster([v for n, v in T.items() if not n.startswith('sight')], pos, k, f)
    sig = raster([v for n, v in T.items() if n.startswith('sight')], pos, k, f)
    out = {'zoom': zoom, 'scoped': scoped, 'cover': 100 * (body | sig).mean()}
    rows = np.where(body.any(1))[0]
    out['top'] = (rows[0] + 0.5) * 100 / GY if len(rows) else 100
    last = np.where(body[-1])[0]
    out['bottom'] = (last[0] * 100 / GX, (last[-1] + 1) * 100 / GX) if len(last) else None
    if sig.any():
        r2 = np.where(sig.any(1))[0]; c2 = np.where(sig.any(0))[0]
        out['sight'] = (c2[0] * 100 / GX, (c2[-1] + 1) * 100 / GX, r2[0] * 100 / GY, (r2[-1] + 1) * 100 / GY)
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
        print('weapon                  zoom  covers  body top  bottom edge   sight box (x, y)   (aimed, % of a 16:9 screen)')
        for key in (args or list(read_ads())):
            m = measure_ads(key, vm, holds, fov)
            if not m: continue
            bt = ('%4.0f to %3.0f' % m['bottom']) if m['bottom'] else '   clear   '
            sg = ('%3.0f-%3.0f, %3.0f-%3.0f' % m['sight']) if m.get('sight') else '        -       '
            print('%-22s %5.2f  %5.1f   %5.1f    %s   %s%s' % (key, m['zoom'], m['cover'], m['top'], bt, sg, '  (behind the scope)' if m['scoped'] else ''))
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
