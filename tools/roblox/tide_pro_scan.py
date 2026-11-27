# The pro animator's Tidecrest take on the katana package's own R15 rig, by forward kinematics in plain Python (26 Nov
# 2026): the rig he framed his camera on. Per frame: the body points the game's lens follows on the real avatars (head,
# torsos, hands, the blade's tip and guard, the sheath's mouth), the feet against the floor, and when the blade sits home
# in its sheath with its place against the sheath (the game holds a sheathed blade to the real sheath on any body).
# Writes the scan JSON tide_pro_data.py folds into FinisherProData_inkfall.
#   py -I tools/roblox/tide_pro_scan.py <take.rbxm> <package.rbxm> <out.json>
import sys, os, re, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxm_read as R

GZ = -0.62


def M(cf):
    (x, y, z), r = cf
    return [[r[0], r[1], r[2], x], [r[3], r[4], r[5], y], [r[6], r[7], r[8], z], [0, 0, 0, 1]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def inv(a):
    """a rigid transform's inverse"""
    Rt = [[a[j][i] for j in range(3)] for i in range(3)]
    t = [a[0][3], a[1][3], a[2][3]]
    nt = [-sum(Rt[i][k] * t[k] for k in range(3)) for i in range(3)]
    return [Rt[0] + [nt[0]], Rt[1] + [nt[1]], Rt[2] + [nt[2]], [0, 0, 0, 1]]


def pt(a, v):
    return [a[i][0] * v[0] + a[i][1] * v[1] + a[i][2] * v[2] + a[i][3] for i in range(3)]


def vec(a, v):
    return [a[i][0] * v[0] + a[i][1] * v[1] + a[i][2] * v[2] for i in range(3)]


I4 = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def main(take_p, pkg_p, out_p):
    take = R.load(take_p)
    seqs = {}
    for k in take:
        if k.cls != 'KeyframeSequence':
            continue
        frames = []
        for kf in sorted((c for c in k.children if c.cls == 'Keyframe'), key=lambda c: c.props.get('Time', 0)):
            tr = {}
            stack = [p for p in kf.children if p.cls == 'Pose']
            while stack:
                p = stack.pop()
                tr[p.name] = M(p.props.get('CFrame', ((0, 0, 0), [1, 0, 0, 0, 1, 0, 0, 0, 1])))
                stack += [c for c in p.children if c.cls == 'Pose']
            frames.append(tr)
        seqs[k.name] = frames
    src = {i.name: i.props.get('Source', '') for i in take if i.cls == 'ModuleScript'}
    blade = {int(m.group(1)): float(m.group(2)) for m in re.finditer(r'\[(\d+)\]\s*=\s*(-?[\d.]+)', src['BladeStretch'])}

    pkg = R.load(pkg_p)
    byref = {i.ref: i for i in pkg}
    fold = [i for i in pkg if i.cls == 'Folder' and i.name == 'Tidecrest'][0]
    rig = [c for c in fold.children if c.name == 'R15_Katana_Rig'][0]
    rest, size = {}, {}
    for c in rig.children:
        if c.cls in ('Part', 'MeshPart'):
            rest[c.name] = M(c.props['CFrame']); size[c.name] = c.props.get('size', (1, 1, 1))
    joints = {}
    for d in pkg:
        if d.cls == 'Motor6D':
            p0, p1 = byref.get(d.props.get('Part0')), byref.get(d.props.get('Part1'))
            if p0 and p1 and p0.parent == rig.ref:
                joints[p1.name] = (p0.name, M(d.props['C0']), M(d.props['C1']))
    sm = [c for c in rig.children if c.name == 'SheathModel'][0]
    sroot = [c for c in sm.children if c.name == 'Sheath'][0]
    srest = M(sroot.props['CFrame'])
    att = {a.name: M(a.props['CFrame']) for a in sroot.children if a.cls == 'Attachment'}
    cap = [c for c in sm.children if c.name == 'saya_cap'][0]
    cap_rel = mul(inv(srest), M(cap.props['CFrame']))
    mouth_rel = att.get('SheathMouth', I4)

    def pose(tr, root):
        out = {'HumanoidRootPart': root}
        todo = True
        while todo:
            todo = False
            for p1, (p0, C0, C1) in joints.items():
                if p1 not in out and p0 in out:
                    out[p1] = mul(mul(mul(out[p0], C0), tr.get(p1, I4)), inv(C1))
                    todo = True
        return out

    ROOT_V = mul([[1, 0, 0, 0], [0, 1, 0, 0.22], [0, 0, 1, -36], [0, 0, 0, 1]], [[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
    r2 = lambda x: round(x, 2)
    S = {'pts': {k: [] for k in ('kH', 'kUT', 'kLT', 'kRH', 'kLH', 'kLF', 'kRF', 'vH', 'vUT', 'vLT', 'tip', 'guard', 'mouth')},
         'kFoot': [], 'vFoot': [], 'vLow': [], 'inSheath': [], 'relS': [], 'dm': [], 'al': []}
    floor = -3.0

    def lowest(W, names):
        y = 1e9
        for n in names:
            if n not in W: continue
            sx, sy, sz = size[n]
            for a in (-1, 1):
                for b in (-1, 1):
                    for c in (-1, 1):
                        y = min(y, pt(W[n], [a * sx / 2, b * sy / 2, c * sz / 2])[1])
        return y - floor

    BODY = [n for n in size if n not in ('HumanoidRootPart',)]
    n = len(seqs['Tidecrest_Samurai'])
    for f in range(n):
        K = pose(seqs['Tidecrest_Samurai'][f], I4)
        V = pose(seqs['Tidecrest_Enemy'][f], ROOT_V)
        L = blade.get(f, 1.0)
        kat = K['Katana']
        tip = pt(kat, [0, 0.181 * L, GZ + (-3.84 - GZ) * L])
        guard = pt(kat, [0, 0, GZ])
        sh = K['Sheath']
        mouth = pt(mul(sh, mouth_rel), [0, 0, 0])
        capp = pt(mul(sh, cap_rel), [0, 0, 0])
        for key, W, part in (('kH', K, 'Head'), ('kUT', K, 'UpperTorso'), ('kLT', K, 'LowerTorso'), ('kRH', K, 'RightHand'), ('kLH', K, 'LeftHand'),
                             ('kLF', K, 'LeftFoot'), ('kRF', K, 'RightFoot'),
                             ('vH', V, 'Head'), ('vUT', V, 'UpperTorso'), ('vLT', V, 'LowerTorso')):
            S['pts'][key].append([r2(c) for c in pt(W[part], [0, 0, 0])])
        S['pts']['tip'].append([r2(c) for c in tip]); S['pts']['guard'].append([r2(c) for c in guard]); S['pts']['mouth'].append([r2(c) for c in mouth])
        S['kFoot'].append(r2(lowest(K, ['LeftFoot', 'RightFoot'])))
        S['vFoot'].append(r2(lowest(V, ['LeftFoot', 'RightFoot'])))
        S['vLow'].append(r2(lowest(V, BODY)))
        dm = math.dist(guard, mouth)
        ax = [capp[i] - mouth[i] for i in range(3)]
        la = math.sqrt(sum(c * c for c in ax)) or 1
        bl = vec(kat, [0, 0, -1])   # the blade's way: the katana's -z
        al = sum(bl[i] * ax[i] for i in range(3)) / la
        home = max(0.0, min(1.0, (0.6 - dm) / 0.35)) * max(0.0, min(1.0, (al - 0.8) / 0.15))
        S['dm'].append(r2(dm)); S['al'].append(r2(al)); S['inSheath'].append(r2(home))
        if home > 0:
            rel = mul(inv(sh), kat)
            S['relS'].append([round(rel[0][3], 4), round(rel[1][3], 4), round(rel[2][3], 4)] + [round(rel[i][j], 4) for i in range(3) for j in range(3)])
        else:
            S['relS'].append(None)
    json.dump(S, open(out_p, 'w'))
    print('frames', n, 'sheathed', sum(1 for x in S['inSheath'] if x > 0.5), 'kFoot', min(S['kFoot']), max(S['kFoot']), 'vLow', min(S['vLow']), max(S['vLow']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
