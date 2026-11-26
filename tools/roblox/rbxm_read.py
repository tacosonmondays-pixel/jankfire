# A small reader for Roblox binary model files (.rbxm / .rbxl, LZ4 chunks): instances, their classes, names, parents and
# the common property types, as plain Python - so a file someone sent can be looked at (and its scripts read) without
# loading it into Studio first. 26 Nov 2026 (the pro animator's Tidecrest cutscene).
#   py -I rbxm_read.py <file.rbxm> [--tree] [--scripts <out dir>]
#   (as a module) load(path) -> list of Inst(ref, cls, name, props, parent, children)
# Types read: String/ProtectedString, Bool, Int32, Float32, Float64, Vector3, CFrame, Enum, Referent, SharedString,
# Color3uint8;
# a property of any other type is left out (its chunk is skipped whole).
import struct, sys, os, math

def lz4_block(src: bytes, n: int) -> bytes:
    out = bytearray()
    i = 0
    while i < len(src):
        tok = src[i]; i += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                b = src[i]; i += 1; lit += b
                if b != 255: break
        out += src[i:i + lit]; i += lit
        if i >= len(src): break
        off = src[i] | (src[i + 1] << 8); i += 2
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255: break
        ml += 4
        st = len(out) - off
        for k in range(ml): out.append(out[st + k])
    assert len(out) == n, (len(out), n)
    return bytes(out)

def deint(buf: bytes, o: int, count: int, width: int):
    # interleaved: all first bytes, then all second bytes... -> big-endian words
    out = []
    for k in range(count):
        v = 0
        for b in range(width): v = (v << 8) | buf[o + b * count + k]
        out.append(v)
    return out, o + width * count

def zz(u): return (u >> 1) ^ -(u & 1)
def rfloat(u):
    u = ((u >> 1) | (u << 31)) & 0xFFFFFFFF
    return struct.unpack('>f', u.to_bytes(4, 'big'))[0]

AX = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (-1, 0, 0), (0, -1, 0), (0, 0, -1)]
def rot_of_id(i):
    k = i - 1
    r, u = AX[k // 6], AX[k % 6]
    b = (r[1] * u[2] - r[2] * u[1], r[2] * u[0] - r[0] * u[2], r[0] * u[1] - r[1] * u[0])
    # rows of the matrix: columns are right, up, back
    return [r[0], u[0], b[0], r[1], u[1], b[1], r[2], u[2], b[2]]

class Inst:
    __slots__ = ('ref', 'cls', 'name', 'props', 'parent', 'children')
    def __init__(self, ref, cls):
        self.ref, self.cls, self.name, self.props, self.parent, self.children = ref, cls, '', {}, None, []

def load(path):
    b = open(path, 'rb').read()
    assert b[:8] == b'<roblox!'
    o = 32
    classes = {}   # id -> (name, [refs])
    insts = {}
    sstr = []
    chunks = []
    while o < len(b):
        name = b[o:o + 4]; clen, ulen = struct.unpack_from('<II', b, o + 4)
        raw = b[o + 16:o + 16 + (clen if clen else ulen)]
        data = lz4_block(raw, ulen) if clen else raw
        o += 16 + (clen if clen else ulen)
        chunks.append((name, data))
        if name == b'END\x00': break
    for name, d in chunks:
        if name == b'INST':
            cid, = struct.unpack_from('<I', d, 0)
            ln, = struct.unpack_from('<I', d, 4); cname = d[8:8 + ln].decode()
            p = 8 + ln + 1
            cnt, = struct.unpack_from('<I', d, p); p += 4
            refs, p = deint(d, p, cnt, 4)
            acc, rs = 0, []
            for r in refs: acc += zz(r); rs.append(acc)
            classes[cid] = (cname, rs)
            for r in rs: insts[r] = Inst(r, cname)
        elif name == b'SSTR':
            p = 4
            cnt, = struct.unpack_from('<I', d, p); p += 4
            for _ in range(cnt):
                p += 16
                ln, = struct.unpack_from('<I', d, p); p += 4
                sstr.append(d[p:p + ln]); p += ln
    for name, d in chunks:
        if name != b'PROP': continue
        cid, = struct.unpack_from('<I', d, 0)
        ln, = struct.unpack_from('<I', d, 4); pname = d[8:8 + ln].decode()
        p = 8 + ln
        t = d[p]; p += 1
        cname, rs = classes[cid]
        n = len(rs)
        vals = None
        try:
            if t == 0x01:
                vals = []
                for _ in range(n):
                    l2, = struct.unpack_from('<I', d, p); p += 4
                    vals.append(d[p:p + l2]); p += l2
                vals = [v.decode('utf-8', 'replace') for v in vals]
            elif t == 0x02:
                vals = [bool(x) for x in d[p:p + n]]
            elif t == 0x03:
                u, p = deint(d, p, n, 4); vals = [zz(x) for x in u]
            elif t == 0x04:
                u, p = deint(d, p, n, 4); vals = [rfloat(x) for x in u]
            elif t == 0x05:
                vals = list(struct.unpack_from('<%dd' % n, d, p))
            elif t == 0x0E:
                xs, p = deint(d, p, n, 4); ys, p = deint(d, p, n, 4); zs, p = deint(d, p, n, 4)
                vals = [(rfloat(a), rfloat(c), rfloat(e)) for a, c, e in zip(xs, ys, zs)]
            elif t == 0x10:
                rots = []
                for _ in range(n):
                    i = d[p]; p += 1
                    if i == 0:
                        rots.append(list(struct.unpack_from('<9f', d, p))); p += 36
                    else:
                        rots.append(rot_of_id(i))
                xs, p = deint(d, p, n, 4); ys, p = deint(d, p, n, 4); zs, p = deint(d, p, n, 4)
                vals = [((rfloat(a), rfloat(c), rfloat(e)), r) for a, c, e, r in zip(xs, ys, zs, rots)]
            elif t == 0x12:
                vals, p = deint(d, p, n, 4)
            elif t == 0x13:
                u, p = deint(d, p, n, 4)
                acc, vals = 0, []
                for x in u: acc += zz(x); vals.append(acc)
            elif t == 0x1A:
                rr, gg, bb = d[p:p + n], d[p + n:p + 2 * n], d[p + 2 * n:p + 3 * n]
                vals = [(rr[k], gg[k], bb[k]) for k in range(n)]
            elif t == 0x1B:
                u, p = deint(d, p, n, 4)
                vals = [sstr[x].decode('utf-8', 'replace') if x < len(sstr) else '' for x in u]
        except Exception:
            vals = None
        if vals is None: continue
        for r, v in zip(rs, vals):
            if pname == 'Name': insts[r].name = v
            insts[r].props[pname] = v
    for name, d in chunks:
        if name != b'PRNT': continue
        cnt, = struct.unpack_from('<I', d, 1)
        ch, p = deint(d, 5, cnt, 4)
        pa, p = deint(d, p, cnt, 4)
        acc, cs = 0, []
        for x in ch: acc += zz(x); cs.append(acc)
        acc, ps = 0, []
        for x in pa: acc += zz(x); ps.append(acc)
        for c, q in zip(cs, ps):
            if c in insts:
                insts[c].parent = q if q in insts else None
                if q in insts: insts[q].children.append(insts[c])
    return [i for i in insts.values()]

def tree(insts, depth_max=3):
    roots = [i for i in insts if i.parent is None]
    out = []
    def walk(i, d):
        if d > depth_max: return
        kids = len(i.children)
        out.append('  ' * d + '%s "%s"%s' % (i.cls, i.name, (' (%d children)' % kids) if kids else ''))
        if i.cls not in ('Pose',):
            for c in i.children: walk(c, d + 1)
    for r in roots: walk(r, 0)
    return '\n'.join(out)

if __name__ == '__main__':
    path = sys.argv[1]
    ins = load(path)
    from collections import Counter
    print(len(ins), 'instances', dict(Counter(i.cls for i in ins)))
    if '--tree' in sys.argv: print(tree(ins))
    if '--scripts' in sys.argv:
        od = sys.argv[sys.argv.index('--scripts') + 1]
        os.makedirs(od, exist_ok=True)
        for i in ins:
            if i.cls in ('Script', 'LocalScript', 'ModuleScript'):
                fn = os.path.join(od, '%s.%s.lua' % (i.name, i.cls))
                open(fn, 'w', encoding='utf-8').write(i.props.get('Source', ''))
                print('wrote', fn, len(i.props.get('Source', '')))
