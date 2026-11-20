# OFFLINE reader for Roblox binary model/place files (.rbxm/.rbxl): reads them as data, runs nothing in them.
# chunks INST / PROP / PRNT / META / SSTR / END, LZ4 block (or zstd) compressed. reports: class counts, the object tree,
# every script's source scanned for backdoor patterns, the animations (inline KeyframeSequences: rig, keyframes, length;
# bare Animation objects: their ids), StringValues and any licence/readme text.
# usage: py -3 -I rbxread.py <file> <out.json> [--scripts-dir DIR]
import struct, sys, re, json, os
from collections import Counter, defaultdict

def lz4_block(src, outlen):
    dst = bytearray()
    i, n = 0, len(src)
    while i < n:
        token = src[i]; i += 1
        lit = token >> 4
        if lit == 15:
            while True:
                b = src[i]; i += 1; lit += b
                if b != 255: break
        dst += src[i:i + lit]; i += lit
        if i >= n: break
        off = src[i] | (src[i + 1] << 8); i += 2
        ml = token & 15
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255: break
        ml += 4
        start = len(dst) - off
        if off >= ml:
            dst += dst[start:start + ml]
        else:
            for k in range(ml): dst.append(dst[start + k])
    if len(dst) != outlen: raise ValueError('lz4 size %d != %d' % (len(dst), outlen))
    return bytes(dst)

def zstd(src, outlen):
    try:
        import zstandard
        return zstandard.ZstdDecompressor().decompress(src, max_output_size=outlen)
    except ImportError:
        pass
    try:
        from compression import zstd as z
        return z.decompress(src)
    except Exception:
        raise RuntimeError('zstd chunk and no zstd decoder')

class R:
    def __init__(s, b): s.b, s.i = b, 0
    def u8(s): v = s.b[s.i]; s.i += 1; return v
    def u32(s): v = struct.unpack_from('<I', s.b, s.i)[0]; s.i += 4; return v
    def string(s):
        n = s.u32(); v = s.b[s.i:s.i + n]; s.i += n; return v
    def ints(s, n):
        raw = s.b[s.i:s.i + 4 * n]; s.i += 4 * n
        out = []
        for k in range(n):
            x = (raw[k] << 24) | (raw[n + k] << 16) | (raw[2 * n + k] << 8) | raw[3 * n + k]
            out.append((x >> 1) ^ -(x & 1))
        return out
    def refs(s, n):
        v = s.ints(n); acc = 0; out = []
        for d in v: acc += d; out.append(acc)
        return out
    def floats(s, n):
        raw = s.b[s.i:s.i + 4 * n]; s.i += 4 * n
        out = []
        for k in range(n):
            x = (raw[k] << 24) | (raw[n + k] << 16) | (raw[2 * n + k] << 8) | raw[3 * n + k]
            x = ((x >> 1) | ((x & 1) << 31)) & 0xFFFFFFFF
            out.append(struct.unpack('<f', struct.pack('<I', x))[0])
        return out

def read(path):
    b = open(path, 'rb').read()
    if not b.startswith(b'<roblox!'):
        raise ValueError('not a binary Roblox file (XML?)')
    nclass, ninst = struct.unpack_from('<ii', b, 16)
    i = 32
    classes = {}      # id -> (name, refs)
    inst = {}         # ref -> {'class', 'props'}
    parent = {}
    types_seen = Counter()
    raw_strings = []  # (class, prop, bytes) for odd types worth a look
    while i < len(b):
        name = b[i:i + 4]; clen, ulen = struct.unpack_from('<II', b, i + 4); i += 16
        if clen == 0:
            data = b[i:i + ulen]; i += ulen
        else:
            comp = b[i:i + clen]; i += clen
            data = zstd(comp, ulen) if comp[:4] == b'\x28\xb5\x2f\xfd' else lz4_block(comp, ulen)
        if name == b'END\x00': break
        r = R(data)
        if name == b'INST':
            cid = r.u32(); cname = r.string().decode('utf-8', 'replace'); fmt = r.u8(); n = r.u32()
            refs = r.refs(n)
            classes[cid] = (cname, refs)
            for ref in refs: inst[ref] = {'class': cname, 'props': {}}
        elif name == b'PROP':
            cid = r.u32(); pname = r.string().decode('utf-8', 'replace'); t = r.u8()
            cname, refs = classes[cid]
            n = len(refs)
            types_seen[(pname, t)] += 1
            try:
                if t == 0x01:
                    for ref in refs: inst[ref]['props'][pname] = r.string()
                elif t == 0x02:
                    for ref in refs: inst[ref]['props'][pname] = bool(r.u8())
                elif t == 0x03:
                    for ref, v in zip(refs, r.ints(n)): inst[ref]['props'][pname] = v
                elif t == 0x04:
                    for ref, v in zip(refs, r.floats(n)): inst[ref]['props'][pname] = v
                elif t == 0x12:
                    raw = r.b[r.i:r.i + 4 * n]
                    for k, ref in enumerate(refs):
                        inst[ref]['props'][pname] = (raw[k] << 24) | (raw[n + k] << 16) | (raw[2 * n + k] << 8) | raw[3 * n + k]
                else:
                    # anything else (Content, SharedString...): keep any id-like text it holds
                    txt = re.findall(rb'(?:rbxassetid://|roblox\.com/asset/\?id=|rbxasset://)[\w./=?-]+', data)
                    if txt: raw_strings.append((cname, pname, t, [x.decode() for x in txt[:400]]))
            except Exception as e:
                raw_strings.append((cname, pname, t, ['parse error %s' % e]))
        elif name == b'PRNT':
            r.u8(); n = r.u32()
            ch = r.refs(n); pa = r.refs(n)
            for c, p in zip(ch, pa): parent[c] = p
    return inst, parent, types_seen, raw_strings, (nclass, ninst)

PATTERNS = [('require(<number>)', rb'require\s*\(\s*\d{5,}'), ('getfenv/setfenv', rb'[gs]etfenv'), ('loadstring', rb'loadstring'),
            ('HttpService', rb'HttpService'), ('InsertService', rb'InsertService'), ('TeleportService', rb'TeleportService'),
            ('MarketplaceService', rb'MarketplaceService'), ('Prompt*Purchase', rb'Prompt\w*Purchase'),
            ('string.char', rb'string\.char'), ('\\ddd escapes', rb'(?:\\\d{2,3}){8,}'), ('long encoded string', rb'[A-Za-z0-9+/=]{400,}'),
            ('ServerScriptService', rb'ServerScriptService'), ('Players kick/ban', rb':Kick\(|BanAsync'), ('webhook/url', rb'https?://'),
            ('fenv/_G tricks', rb'_G\[|shared\['), ('MessagingService', rb'MessagingService'), ('DataStore', rb'DataStore')]

def main():
    path, outp = sys.argv[1], sys.argv[2]
    sdir = sys.argv[sys.argv.index('--scripts-dir') + 1] if '--scripts-dir' in sys.argv else None
    inst, parent, types_seen, raw_strings, hdr = read(path)
    def nm(ref):
        v = inst[ref]['props'].get('Name', b'')
        return v.decode('utf-8', 'replace') if isinstance(v, bytes) else str(v)
    def pathof(ref):
        parts = []
        k = ref
        while k in inst and len(parts) < 30:
            parts.append('%s:%s' % (inst[k]['class'], nm(k)))
            k = parent.get(k, -1)
        return '/'.join(reversed(parts))
    kids = defaultdict(list)
    for c, p in parent.items(): kids[p].append(c)
    rep = {'file': os.path.basename(path), 'header_classes_instances': hdr, 'class_counts': Counter(v['class'] for v in inst.values()).most_common()}
    # the tree: containers down to depth 4, with what each holds
    def summary(ref, depth):
        cc = Counter(inst[c]['class'] for c in kids[ref])
        line = '  ' * depth + '%s "%s"  [%s]' % (inst[ref]['class'], nm(ref), ', '.join('%s x%d' % kv for kv in cc.most_common(5)))
        out = [line]
        if depth < 4:
            for c in kids[ref]:
                if inst[c]['class'] in ('Folder', 'Model', 'Configuration', 'Workspace', 'ReplicatedStorage', 'ServerStorage', 'StarterPack',
                                        'ServerScriptService', 'StarterPlayer', 'StarterPlayerScripts', 'StarterCharacterScripts', 'StarterGui', 'Lighting'):
                    out += summary(c, depth + 1)
        return out
    roots = [r for r in inst if parent.get(r, -1) not in inst]
    tree = []
    for r0 in roots: tree += summary(r0, 0)
    rep['tree'] = tree[:400]
    # scripts
    scripts = []
    for ref, v in inst.items():
        if v['class'] in ('Script', 'LocalScript', 'ModuleScript'):
            src = v['props'].get('Source', b'')
            if not isinstance(src, bytes): src = b''
            hits = [n for n, rx in PATTERNS if re.search(rx, src)]
            scripts.append({'path': pathof(ref), 'class': v['class'], 'bytes': len(src), 'hits': hits,
                            'disabled': v['props'].get('Disabled'), 'head': src[:300].decode('utf-8', 'replace')})
            if sdir:
                os.makedirs(sdir, exist_ok=True)
                fn = re.sub(r'[^\w.-]+', '_', pathof(ref))[-150:] + '.lua.txt'
                open(os.path.join(sdir, fn), 'wb').write(src)
    rep['scripts'] = scripts
    # animations: inline KeyframeSequences (rig from pose names, keyframes, length)
    seqs = []
    for ref, v in inst.items():
        if v['class'] == 'KeyframeSequence':
            kfs = [c for c in kids[ref] if inst[c]['class'] == 'Keyframe']
            times = [inst[c]['props'].get('Time', 0.0) for c in kfs]
            poses = set()
            stack = list(kfs)
            while stack:
                x = stack.pop()
                for c in kids[x]:
                    if inst[c]['class'] == 'Pose':
                        poses.add(nm(c)); stack.append(c)
            rig = 'R15' if ({'UpperTorso', 'LowerTorso'} & poses) else ('R6' if ({'Torso', 'Left Arm', 'Right Arm', 'Left Leg', 'Right Leg'} & poses) else '?')
            seqs.append({'path': pathof(ref), 'name': nm(ref), 'rig': rig, 'keyframes': len(kfs), 'length': round(max(times) if times else 0.0, 3),
                         'loop': v['props'].get('Loop'), 'priority': v['props'].get('Priority')})
    rep['keyframe_sequences'] = seqs
    anims = []
    for ref, v in inst.items():
        if v['class'] == 'Animation':
            aid = v['props'].get('AnimationId')
            anims.append({'path': pathof(ref), 'id': aid.decode('utf-8', 'replace') if isinstance(aid, bytes) else aid})
    rep['animation_objects'] = anims
    rep['odd_property_ids'] = [{'class': c, 'prop': p, 'type': t, 'ids': ids[:30], 'n': len(ids)} for c, p, t, ids in raw_strings]
    sv = []
    for ref, v in inst.items():
        if v['class'] in ('StringValue',):
            val = v['props'].get('Value', b'')
            sv.append({'path': pathof(ref), 'value': (val.decode('utf-8', 'replace') if isinstance(val, bytes) else str(val))[:2000]})
    rep['string_values'] = sv
    # every asset id any property points at (textures, meshes, sounds, animations): whose they are matters
    ids = Counter()
    for v in inst.values():
        for pn, val in v['props'].items():
            if isinstance(val, bytes):
                for m in re.findall(rb'(?:rbxassetid://|roblox\.com/asset/\?id=)(\d+)', val): ids['%s.%s %s' % (v['class'], pn, m.decode())] += 1
    for c, pn, t, lst in raw_strings:
        for x in lst:
            m = re.search(r'(\d{5,})', x)
            if m: ids['%s.%s %s' % (c, pn, m.group(1))] += 1
    rep['asset_ids'] = ids.most_common()
    rep['types_seen'] = sorted(['%s:0x%02x x%d' % (p, t, n) for (p, t), n in types_seen.items()])
    json.dump(rep, open(outp, 'w', encoding='utf-8'), indent=1, default=str)
    print('instances', len(inst), 'scripts', len(scripts), 'kfs', len(seqs), 'animations', len(anims), 'stringvalues', len(sv))

pass
