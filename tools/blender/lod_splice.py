# Gives a prop file that's already shipped the far LOD (`lod1`) of a fresh Blender build, without touching the shipped
# close-up: the file is rebuilt from OLD's scene (minus any lod1 it had) plus every lod1 subtree of NEW (a node named
# lod1 / lod1.001..., with its meshes), each hung under the node of the same name as its parent in NEW. Materials are
# matched by name (copied over, pictures and all, if OLD hasn't got one); OLD's roots take NEW's metadata (the lod
# distance). Every lod0 accessor keeps its exact bytes, so players see exactly the model they had up close.
# (why: Blender 4.0's exact booleans give a cut face a random material when the cutter has none, so round 1's props
# don't rebuild byte for byte: this adds their far LOD without re-rolling the close one.)
# run: python3 tools/blender/lod_splice.py <old.glb> <new.glb> <out.glb>   (out may be old; no Blender needed)
import json, re, struct, sys

FAR = re.compile(r'lod1(\.\d+)?$')


def read(path):
    b = open(path, 'rb').read()
    magic, ver, _ = struct.unpack_from('<III', b, 0)
    if magic != 0x46546C67 or ver != 2: raise ValueError(path + ': not a glb 2.0')
    jl, jt = struct.unpack_from('<II', b, 12)
    if jt != 0x4E4F534A: raise ValueError(path + ': no JSON chunk')
    j = json.loads(b[20:20 + jl])
    off, binb = 20 + jl, b''
    if off + 8 <= len(b):
        bl, bt = struct.unpack_from('<II', b, off)
        if bt == 0x004E4942: binb = b[off + 8:off + 8 + bl]
    return j, binb


def write(path, j, binb):
    js = json.dumps(j, separators=(',', ':')).encode()
    js += b' ' * (-len(js) % 4)
    binb = bytes(binb) + b'\0' * (-len(binb) % 4)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binb)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(binb), 0x004E4942)); f.write(binb)


def _deep(o): return json.loads(json.dumps(o))


class _Out:
    """a fresh glTF that things are copied into from either source (index maps per source)"""
    def __init__(s, asset):
        s.j = {'asset': asset, 'scene': 0, 'scenes': [], 'nodes': [], 'meshes': [], 'materials': [], 'textures': [],
               'images': [], 'samplers': [], 'accessors': [], 'bufferViews': [], 'buffers': [{'byteLength': 0}]}
        s.bin = bytearray(); s.maps = {}; s.mat_by_name = {}; s.ext = set()

    def _add(s, kind, src, i, make):
        key = (id(src[0]), kind, i)
        if key not in s.maps:
            s.maps[key] = None  # (no cycles in glTF, but keep the slot)
            o = make()
            s.j[kind].append(o); s.maps[key] = len(s.j[kind]) - 1
        return s.maps[key]

    def view(s, src, i):
        def make():
            v = dict(src[0]['bufferViews'][i]); o0 = v.get('byteOffset', 0)
            data = src[1][o0:o0 + v['byteLength']]
            s.bin.extend(b'\0' * (-len(s.bin) % 4))
            v['buffer'] = 0; v['byteOffset'] = len(s.bin); s.bin.extend(data)
            return v
        return s._add('bufferViews', src, i, make)

    def accessor(s, src, i):
        def make():
            a = dict(src[0]['accessors'][i])
            if 'sparse' in a: raise ValueError('sparse accessors are not handled')
            if 'bufferView' in a: a['bufferView'] = s.view(src, a['bufferView'])
            return a
        return s._add('accessors', src, i, make)

    def image(s, src, i):
        def make():
            im = _deep(src[0]['images'][i])
            if 'bufferView' in im: im['bufferView'] = s.view(src, im['bufferView'])
            return im
        return s._add('images', src, i, make)

    def texture(s, src, i):
        def make():
            t = _deep(src[0]['textures'][i])
            if 'sampler' in t: t['sampler'] = s._add('samplers', src, t['sampler'], lambda: _deep(src[0]['samplers'][t['sampler']]))
            if 'source' in t: t['source'] = s.image(src, t['source'])
            for k, e in (t.get('extensions') or {}).items():
                s.ext.add(k)
                if isinstance(e, dict) and 'source' in e: e['source'] = s.image(src, e['source'])
            return t
        return s._add('textures', src, i, make)

    def material(s, src, i):
        m = src[0]['materials'][i]; nm = m.get('name')
        if nm is not None and nm in s.mat_by_name: return s.mat_by_name[nm]  # (NEW's lod1 uses OLD's paint of that name)
        def make():
            mm = _deep(m)
            def fix(o):
                if isinstance(o, dict):
                    for k, v in o.items():
                        if k == 'extensions' and isinstance(v, dict): s.ext.update(v.keys())
                        if k.endswith('Texture') and isinstance(v, dict) and 'index' in v: v['index'] = s.texture(src, v['index'])
                        fix(v)
                elif isinstance(o, list):
                    for v in o: fix(v)
            fix(mm)
            return mm
        k = s._add('materials', src, i, make)
        if nm is not None: s.mat_by_name.setdefault(nm, k)
        return k

    def mesh(s, src, i):
        def make():
            me = _deep(src[0]['meshes'][i])
            for p in me['primitives']:
                if 'targets' in p: raise ValueError('morph targets are not handled')
                p['attributes'] = {k: s.accessor(src, v) for k, v in p['attributes'].items()}
                if 'indices' in p: p['indices'] = s.accessor(src, p['indices'])
                if 'material' in p: p['material'] = s.material(src, p['material'])
            return me
        return s._add('meshes', src, i, make)

    def node(s, src, i, skip=None):
        n = _deep(src[0]['nodes'][i])
        for k in ('skin', 'camera'):
            if k in n: raise ValueError(f'node {n.get("name")}: {k} is not handled')
        if 'mesh' in n: n['mesh'] = s.mesh(src, n['mesh'])
        kids = [c for c in n.pop('children', []) if not (skip and skip(src[0]['nodes'][c]))]
        s.j['nodes'].append(n); k = len(s.j['nodes']) - 1
        if kids: s.j['nodes'][k]['children'] = [s.node(src, c, skip) for c in kids]
        return k


def splice(old_path, new_path, out_path):
    """returns (lod1 subtrees added, names of the nodes they hang under)"""
    J, JB = read(old_path); N, NB = read(new_path)
    for src in (J, N):
        if src.get('animations') or src.get('skins'): raise ValueError('animations / skins are not handled')
    old, new = (J, JB), (N, NB)
    out = _Out(J.get('asset', {'version': '2.0'}))
    for k in ('materials',):  # OLD's materials first, all of them, in order: lod0 keeps its own
        for i in range(len(J.get(k, []))): out.material(old, i)
    is_far = lambda n: bool(FAR.match(n.get('name') or ''))
    sc = J['scenes'][J.get('scene', 0)]
    roots = [out.node(old, i, skip=is_far) for i in sc.get('nodes', []) if not is_far(J['nodes'][i])]
    out.j['scenes'].append({k: v for k, v in _deep(sc).items() if k != 'nodes'} | {'nodes': roots})
    by_name = {}
    for k, n in enumerate(out.j['nodes']): by_name.setdefault(n.get('name'), []).append(k)
    parent = {c: i for i, n in enumerate(N['nodes']) for c in n.get('children', [])}
    def far_above(i):
        while i in parent:
            i = parent[i]
            if is_far(N['nodes'][i]): return True
        return False
    added, under = 0, []
    for i, n in enumerate(N['nodes']):
        if not is_far(n) or far_above(i): continue
        pn = N['nodes'][parent[i]].get('name') if i in parent else None
        t = by_name.get(pn, [])
        if len(t) != 1: raise ValueError(f'{n.get("name")}: its parent {pn!r} is {len(t)} nodes in {old_path}, not 1')
        out.j['nodes'][t[0]].setdefault('children', []).append(out.node(new, i)); added += 1; under.append(pn)
    for i in N['scenes'][N.get('scene', 0)].get('nodes', []):  # the roots' metadata (jf: lod distance...) from NEW
        nn = N['nodes'][i]; t = by_name.get(nn.get('name'), [])
        if len(t) == 1 and 'extras' in nn: out.j['nodes'][t[0]]['extras'] = _deep(nn['extras'])
    ext = set(J.get('extensionsUsed', [])) | out.ext
    if ext: out.j['extensionsUsed'] = sorted(ext)
    if J.get('extensionsRequired'): out.j['extensionsRequired'] = J['extensionsRequired']
    for k in ('textures', 'images', 'samplers', 'materials'):
        if not out.j[k]: del out.j[k]
    out.bin.extend(b'\0' * (-len(out.bin) % 4)); out.j['buffers'][0]['byteLength'] = len(out.bin)
    write(out_path, out.j, out.bin)
    return added, under


if __name__ == '__main__':
    if len(sys.argv) != 4: sys.exit(__doc__ or 'usage: lod_splice.py <old.glb> <new.glb> <out.glb>')
    n, under = splice(*sys.argv[1:])
    print(f'JF_SPLICE {sys.argv[3]}: {n} lod1 subtree(s) under {", ".join(map(str, under))}')
