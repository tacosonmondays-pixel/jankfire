# The sums the hold table needs, in plain Python (no Blender, no numpy), so the Blender preview (hold_preview.py) and
# the Luau writer (holds.py) cannot disagree: the game's rotation order, a clip's pose (Viewmodel.luau VM.sample), and
# the katana's new rest and parry poses turned into "fixes" laid over the web game's clips.
import json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')


# ------------------------------------------------------------------ 3x3 matrices as tuples of rows
def mmul(A, B): return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def mvec(A, v): return tuple(sum(A[i][k] * v[k] for k in range(3)) for i in range(3))
def mT(A): return tuple(tuple(A[j][i] for j in range(3)) for i in range(3))
def rx(a): c, s = math.cos(a), math.sin(a); return ((1, 0, 0), (0, c, -s), (0, s, c))
def ry(a): c, s = math.cos(a), math.sin(a); return ((c, 0, s), (0, 1, 0), (-s, 0, c))
def rz(a): c, s = math.cos(a), math.sin(a); return ((c, -s, 0), (s, c, 0), (0, 0, 1))
def angles(r): return mmul(mmul(rx(r[0]), ry(r[1])), rz(r[2]))        # CFrame.Angles / fromEulerAnglesXYZ
def angles_deg(r): return angles([math.radians(a) for a in r])
def vadd(a, b): return tuple(a[i] + b[i] for i in range(3))
def vsub(a, b): return tuple(a[i] - b[i] for i in range(3))
def vmul(a, k): return tuple(c * k for c in a)
def dot(a, b): return sum(a[i] * b[i] for i in range(3))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def unit(a):
    n = math.sqrt(dot(a, a))
    return tuple(c / n for c in a)
def cols(x, y, z): return tuple((x[i], y[i], z[i]) for i in range(3))


def quat(M):
    t = M[0][0] + M[1][1] + M[2][2]
    if t > 0:
        s = math.sqrt(t + 1) * 2
        return (0.25 * s, (M[2][1] - M[1][2]) / s, (M[0][2] - M[2][0]) / s, (M[1][0] - M[0][1]) / s)
    if M[0][0] > M[1][1] and M[0][0] > M[2][2]:
        s = math.sqrt(1 + M[0][0] - M[1][1] - M[2][2]) * 2
        return ((M[2][1] - M[1][2]) / s, 0.25 * s, (M[0][1] + M[1][0]) / s, (M[0][2] + M[2][0]) / s)
    if M[1][1] > M[2][2]:
        s = math.sqrt(1 + M[1][1] - M[0][0] - M[2][2]) * 2
        return ((M[0][2] - M[2][0]) / s, (M[0][1] + M[1][0]) / s, 0.25 * s, (M[1][2] + M[2][1]) / s)
    s = math.sqrt(1 + M[2][2] - M[0][0] - M[1][1]) * 2
    return ((M[1][0] - M[0][1]) / s, (M[0][2] + M[2][0]) / s, (M[1][2] + M[2][1]) / s, 0.25 * s)


def qmat(q):
    w, x, y, z = q
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def slerp(A, B, t):
    a, b = quat(A), quat(B)
    d = sum(a[i] * b[i] for i in range(4))
    if d < 0: b = tuple(-c for c in b); d = -d
    if d > 0.9995: q = tuple(a[i] + (b[i] - a[i]) * t for i in range(4))
    else:
        th = math.acos(d)
        q = tuple((math.sin((1 - t) * th) * a[i] + math.sin(t * th) * b[i]) / math.sin(th) for i in range(4))
    n = math.sqrt(sum(c * c for c in q))
    return qmat(tuple(c / n for c in q))


I3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


# ------------------------------------------------------------------ the game's own numbers
def read_vm():
    """each weapon's rest pose in first person: { id: (p metres, r radians, s) } (Weapons.luau)"""
    src = open(os.path.join(ROOT, 'roblox/src/shared/Weapons.luau'), encoding='utf-8').read()
    out = {}
    for m in re.finditer(r'id = "(\w+)"(.*?)vm = \{ p = Vector3\.new\(([^)]*)\) \* S, r = Vector3\.new\(([^)]*)\), s = ([\d.]+) \}', src, re.S):
        if 'id = "' in m.group(2): continue
        out[m.group(1)] = ([float(x) for x in m.group(3).split(',')], [float(x) for x in m.group(4).split(',')], float(m.group(5)))
    return out


def read_anims():
    src = open(os.path.join(ROOT, 'roblox/src/shared/Anims.luau'), encoding='utf-8').read()
    out = {}
    for m in re.finditer(r'\n\t(\w+) = \{\n(.*?)\n\t\},', src, re.S):
        body = m.group(2)
        sl = re.search(r'slerp = \{([^}]*)\}', body)
        dur = re.search(r'dur = ([\d.]+)', body)
        keys = [dict(t=float(k.group(1)), p=[float(x) for x in k.group(2).split(',')], r=[float(x) for x in k.group(3).split(',')], e=k.group(4))
                for k in re.finditer(r'\{ t = ([\d.]+), p = \{([^}]*)\}, r = \{([^}]*)\}, e = "(\w+)" \}', body)]
        out[m.group(1)] = dict(slerp=[float(x) for x in sl.group(1).split(',')] if sl else None, keys=keys, dur=float(dur.group(1)) if dur else keys[-1]['t'])
    return out


EASE = {'linear': lambda u: u, 'smooth': lambda u: u * u * (3 - 2 * u), 'snap': lambda u: 1 - (1 - u) ** 3, 'in': lambda u: u ** 3,
        'back': lambda u: 1 + 2.9 * (u - 1) ** 3 + 1.9 * (u - 1) ** 2}


def sample(a, t, base):
    """a clip's pose at t: (offset metres, rotation matrix). Viewmodel.luau VM.sample"""
    keys = a['keys']
    k0, k1 = keys[0], keys[-1]
    if t <= keys[0]['t']: k1 = keys[0]
    for i in range(len(keys) - 1):
        if keys[i]['t'] <= t < keys[i + 1]['t']: k0, k1 = keys[i], keys[i + 1]; break
    span = k1['t'] - k0['t']
    u = min(1, max(0, (t - k0['t']) / span)) if span > 0 else 1
    e = EASE[k1['e']](u)
    p = [k0['p'][i] + (k1['p'][i] - k0['p'][i]) * e for i in range(3)]
    if a['slerp']:
        sb = a['slerp']
        return p, slerp(angles([sb[i] + k0['r'][i] for i in range(3)]), angles([sb[i] + k1['r'][i] for i in range(3)]), e)
    return p, angles([base[i] + k0['r'][i] + (k1['r'][i] - k0['r'][i]) * e for i in range(3)])


# ------------------------------------------------------------------ the katana's poses
GUARD_Z = -0.134   # the guard's place along the katana, file metres


def aimed(spec, s):
    """a pose given as where the guard is (camera space, metres), which way the blade points and how far it is turned
       about itself (0 = the back of the blade up the screen, edge down): the weapon's rotation and its origin"""
    b = unit(spec['dir'])
    up = (0.0, 1.0, 0.0)
    ref = unit(vsub(up, vmul(b, dot(up, b))))
    a = math.radians(spec.get('roll', 0))
    # turn ref about b by a (Rodrigues; ref is square to b)
    y = vadd(vmul(ref, math.cos(a)), vmul(cross(b, ref), math.sin(a)))
    z = vmul(b, -1)
    x = cross(y, z)
    Rm = cols(x, y, z)
    origin = vsub(spec['guard'], mvec(Rm, (0, 0, GUARD_Z * s)))
    return Rm, origin


def katana_fixes(holds, vm=None, anims=None, look=None):
    """{ name: (rotation laid after the clip's own, offset in camera space) } for 'rest' and 'parry': what turns the
       web game's pose into the one asked for in holds.json. 'none' is no change (the swing itself)."""
    vm = vm or read_vm(); anims = anims or read_anims()
    p0, r0, s = vm['katana']
    s = s * holds.get('_size', 1)  # (the katana is drawn at the viewmodel's size too)
    k = dict(holds.get('katana', {}).get('vm') or {})
    kl = holds.get('katana', {})
    if kl.get('looks') and 'rest' not in k:
        k['rest'] = kl['looks'][look or kl.get('use', 'combined')]['rest']
    out = {'none': (I3, (0.0, 0.0, 0.0))}
    old = {'rest': (p0, angles(r0))}
    pp, pr = sample(anims['parry_katana'], 0.2, r0)
    old['parry'] = (vadd(p0, pp), pr)
    for name in ('rest', 'parry'):
        spec = k.get(name)
        if not spec: out[name] = out['none'] if name == 'rest' else out['rest']; continue
        Rd, Pd = aimed(spec, s)
        P0, R0 = old[name]
        out[name] = (mmul(mT(R0), Rd), vsub(Pd, P0))
    return out


# when each fix is on, per clip: (time, fix name). between keys it blends (smoothstep). a clip not listed keeps 'rest'
KATANA_CLIPS = {
    'swing_katana':  [(0.0, 'rest'), (0.05, 'none'), (0.28, 'none'), (0.5, 'rest')],
    'swing_katana2': [(0.0, 'rest'), (0.05, 'none'), (0.28, 'none'), (0.5, 'rest')],
    'parry_katana':  [(0.0, 'rest'), (0.07, 'parry'), (0.36, 'parry'), (0.56, 'rest')],
    'draw_katana':   [(0.0, 'none'), (0.40, 'none'), (0.66, 'rest'), (0.72, 'rest')],
}


def katana_fix_at(fixes, clip, t):
    keys = KATANA_CLIPS.get(clip) if clip else None
    if not keys: return fixes['rest']
    a, b = keys[0], keys[-1]
    if t <= keys[0][0]: b = keys[0]
    for i in range(len(keys) - 1):
        if keys[i][0] <= t < keys[i + 1][0]: a, b = keys[i], keys[i + 1]; break
    span = b[0] - a[0]
    u = min(1, max(0, (t - a[0]) / span)) if span > 0 else 1
    u = u * u * (3 - 2 * u)
    (Ra, Pa), (Rb, Pb) = fixes[a[1]], fixes[b[1]]
    return slerp(Ra, Rb, u), tuple(Pa[i] + (Pb[i] - Pa[i]) * u for i in range(3))


def load_holds(path=None):
    return json.load(open(path or os.path.join(HERE, 'holds.json'), encoding='utf-8'))
