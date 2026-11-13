# A hero glb with one mesh per joint -> the same hero as ONE skinned mesh per LOD (the coordinator, 2026-11-13: a hero
# draws in 15-30 calls; every joint's mesh costs one call per material, a skinned mesh costs one per material in all).
# Every vertex is weighted 100 % to the joint its piece hung on (rigid parts, exactly as before); the joint nodes, their
# rest transforms, every clip, every marker and the meta stay byte for byte what they were, so code that turns joints
# keeps working. The <joint>_mesh / <joint>_lod1 nodes go; <prefix>_mesh (near) and <prefix>_lod1 (far) come in at
# the root, bound to a skin over the joints, and meta.skinned says so. Plain Python + numpy (no Blender).
#   python3 tools/blender/mechs/skin_glb.py <in.glb> <out.glb> [prefix]
import json, struct, sys
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
CT_OF = {np.dtype(v): k for k, v in CT.items()}


def load(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'glTF'
    jl = struct.unpack('<I', d[12:16])[0]; j = json.loads(d[20:20 + jl])
    o = 20 + jl; bl = struct.unpack('<I', d[o:o + 4])[0]; return j, d[o + 8:o + 8 + bl]


def read(j, b, a):
    acc = j['accessors'][a]; bv = j['bufferViews'][acc['bufferView']]
    dt = np.dtype(CT[acc['componentType']]); n = NC[acc['type']]
    off = bv.get('byteOffset', 0) + acc.get('byteOffset', 0); stride = bv.get('byteStride', 0)
    if stride and stride != dt.itemsize * n:
        rows = [np.frombuffer(b, dt, n, off + i * stride) for i in range(acc['count'])]; return np.array(rows), acc
    return np.frombuffer(b, dt, acc['count'] * n, off).reshape(acc['count'], n).copy(), acc


def trs(node):
    if 'matrix' in node: return np.array(node['matrix'], np.float64).reshape(4, 4).T
    t = node.get('translation', [0, 0, 0]); r = node.get('rotation', [0, 0, 0, 1]); s = node.get('scale', [1, 1, 1])
    x, y, z, w = r
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4); M[:3, :3] = R * np.array(s)[None, :]; M[:3, 3] = t; return M


def main(src, dst, prefix=None):
    j, b = load(src)
    N = j['nodes']; parent = {c: i for i, n in enumerate(N) for c in n.get('children', [])}
    world = {}
    def W(i):
        if i not in world: world[i] = (W(parent[i]) if i in parent else np.eye(4)) @ trs(N[i])
        return world[i]
    ri = next(i for i, n in enumerate(N) if isinstance(n.get('extras', {}).get('jf'), str))
    meta = json.loads(N[ri]['extras']['jf'])
    byname = {n.get('name'): i for i, n in enumerate(N)}
    joints = [byname[k] for k in meta['joints']]; jidx = {ni: k for k, ni in enumerate(joints)}
    assert len(joints) < 256
    pieces = [i for i, n in enumerate(N) if 'mesh' in n and i in parent and parent[i] in jidx and (n['name'].endswith('_mesh') or n['name'].endswith('_lod1'))]
    assert pieces and not any(N[i].get('children') for i in pieces), 'a piece with children'
    if prefix is None:
        mats = [j['materials'][p['material']]['name'] for i in pieces for p in j['meshes'][N[i]['mesh']]['primitives']]
        prefix = next(m[:-6] for m in mats if m.endswith('_paint'))
    # gather: (lod, material) -> lists of per-piece attribute arrays (in bind space = the rest pose, world)
    groups, attrs_all, kinds = {}, set(), {}
    for i in pieces:
        lod = 'far' if N[i]['name'].endswith('_lod1') else 'near'; M = W(i); R3 = M[:3, :3]; ji = jidx[parent[i]]
        for p in j['meshes'][N[i]['mesh']]['primitives']:
            assert p.get('mode', 4) == 4
            A = {}
            for k, a in p['attributes'].items():
                arr, acc = read(j, b, a); A[k] = arr; attrs_all.add(k); kinds.setdefault(k, (acc['componentType'], acc['type'], acc.get('normalized', False)))
            pos = A['POSITION'].astype(np.float64); A['POSITION'] = (pos @ R3.T + M[:3, 3]).astype(np.float32)
            if 'NORMAL' in A:
                nn = A['NORMAL'].astype(np.float64) @ R3.T; nn /= np.maximum(1e-9, np.linalg.norm(nn, axis=1, keepdims=True)); A['NORMAL'] = nn.astype(np.float32)
            idx = read(j, b, p['indices'])[0].ravel().astype(np.uint32) if 'indices' in p else np.arange(len(pos), dtype=np.uint32)
            groups.setdefault((lod, p['material']), []).append((A, idx, ji))
    # the new file: kept data copied, new meshes, a skin
    out_views, out_acc, blob = [], [], bytearray()
    def view(data, target=None):
        while len(blob) % 4: blob.append(0)
        v = {'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)}
        if target: v['target'] = target
        blob.extend(data); out_views.append(v); return len(out_views) - 1
    def accessor(arr, ct, typ, norm=False, target=None, minmax=False):
        arr = np.ascontiguousarray(arr.astype(CT[ct])); a = {'bufferView': view(arr.tobytes(), target), 'componentType': ct, 'count': int(arr.shape[0]), 'type': typ}
        if norm: a['normalized'] = True
        if minmax: a['min'] = [float(x) for x in arr.reshape(arr.shape[0], -1).min(0)]; a['max'] = [float(x) for x in arr.reshape(arr.shape[0], -1).max(0)]
        out_acc.append(a); return len(out_acc) - 1
    def keep(a):  # copy an old accessor (animation keys) as it is
        arr, acc = read(j, b, a); na = {k: v for k, v in acc.items() if k not in ('bufferView', 'byteOffset')}
        na['bufferView'] = view(np.ascontiguousarray(arr).tobytes()); out_acc.append(na); return len(out_acc) - 1
    for im in j.get('images', []):
        if 'bufferView' in im:
            bv = j['bufferViews'][im['bufferView']]; o = bv.get('byteOffset', 0); im['bufferView'] = view(b[o:o + bv['byteLength']])
    for an in j.get('animations', []):
        for s in an['samplers']: s['input'] = keep(s['input']); s['output'] = keep(s['output'])
    meshes = {'near': {'name': prefix + '_mesh', 'primitives': []}, 'far': {'name': prefix + '_lod1', 'primitives': []}}
    report = {}
    for (lod, mat), parts in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        keys = sorted(attrs_all & set().union(*[set(A) for A, _, _ in parts]))
        cat = {k: [] for k in keys}; idx, js, base = [], [], 0
        for A, ix, ji in parts:
            n = len(A['POSITION'])
            for k in keys:
                if k in A: cat[k].append(A[k].astype(np.float32) if CT[kinds[k][0]] == np.float32 else A[k])
                else: cat[k].append(np.zeros((n, NC[kinds[k][1]]), CT[kinds[k][0]]))
            idx.append(ix + base); js.append(np.full(n, ji, np.uint8)); base += n
        prim = {'attributes': {}, 'material': mat}
        for k in keys:
            ct, typ, norm = kinds[k]
            prim['attributes'][k] = accessor(np.concatenate(cat[k]), ct, typ, norm, 34962, minmax=(k == 'POSITION'))
        jj = np.zeros((base, 4), np.uint8); jj[:, 0] = np.concatenate(js); ww = np.zeros((base, 4), np.uint8); ww[:, 0] = 255
        prim['attributes']['JOINTS_0'] = accessor(jj, 5121, 'VEC4', False, 34962)
        prim['attributes']['WEIGHTS_0'] = accessor(ww, 5121, 'VEC4', True, 34962)
        I = np.concatenate(idx); prim['indices'] = accessor(I.reshape(-1, 1), 5123 if base < 65536 else 5125, 'SCALAR', False, 34963)
        meshes[lod]['primitives'].append(prim); report.setdefault(lod, []).append((j['materials'][mat]['name'], int(len(I) // 3)))
    ibm = np.stack([np.linalg.inv(W(ni)).T.astype(np.float32).ravel() for ni in joints])  # (column-major, like glTF wants)
    skin = {'name': prefix + '_skin', 'joints': joints, 'inverseBindMatrices': accessor(ibm, 5126, 'MAT4'), 'skeleton': joints[0]}
    # nodes: the pieces go (everything re-indexed), the two skinned meshes hang on the root
    gone = set(pieces); keepn = [i for i in range(len(N)) if i not in gone]; remap = {o: n for n, o in enumerate(keepn)}
    assert not any('mesh' in N[i] for i in keepn), 'a mesh that is not a joint piece'
    newN = []
    for i in keepn:
        n = dict(N[i])
        if 'children' in n:
            n['children'] = [remap[c] for c in n['children'] if c not in gone]
            if not n['children']: n.pop('children')
        newN.append(n)
    mesh_list = [m for m in (meshes['near'], meshes['far']) if m['primitives']]
    for k, m in enumerate(mesh_list):
        newN.append({'name': m['name'], 'mesh': k, 'skin': 0}); newN[remap[ri]].setdefault('children', []).append(len(newN) - 1)
    skin['joints'] = [remap[x] for x in joints]; skin['skeleton'] = remap[joints[0]]
    for sc in j.get('scenes', []): sc['nodes'] = [remap[x] for x in sc['nodes'] if x not in gone]
    for an in j.get('animations', []):
        for c in an['channels']: c['target']['node'] = remap[c['target']['node']]
    meta['skinned'] = {'near': meshes['near']['name'], 'far': meshes['far']['name'] if meshes['far']['primitives'] else None, 'rigid': True}
    newN[remap[ri]]['extras']['jf'] = json.dumps(meta)
    j['nodes'] = newN; j['meshes'] = mesh_list; j['skins'] = [skin]; j['accessors'] = out_acc; j['bufferViews'] = out_views
    j['buffers'] = [{'byteLength': len(blob)}]
    while len(blob) % 4: blob.append(0)
    js_ = json.dumps(j, separators=(',', ':')).encode()
    while len(js_) % 4: js_ += b' '
    out = b'glTF' + struct.pack('<II', 2, 12 + 8 + len(js_) + 8 + len(blob)) + struct.pack('<I', len(js_)) + b'JSON' + js_ + struct.pack('<I', len(blob)) + b'BIN\x00' + bytes(blob)
    open(dst, 'wb').write(out)
    for lod in ('near', 'far'):
        r = report.get(lod, []); print(f'JF_SKIN {lod}: {len(r)} draws, {sum(t for _, t in r)} tris:', ', '.join(f'{m} {t}' for m, t in r))
    print(f'JF_SKIN {len(pieces)} joint meshes -> {len(mesh_list)} skinned meshes over {len(joints)} joints; {len(out) // 1024} KB')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
