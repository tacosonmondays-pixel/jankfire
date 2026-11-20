# full-ish OFFLINE decoder for Roblox binary models (reads data only; runs nothing): every property type the VFX packs
# use, into plain Python values. Builds on the kill-effects session's rbxread (LZ4/zstd chunks, interleaved ints/floats).
import struct, sys
sys.path.insert(0, r"C:/Users/soup2/AppData/Local/Temp/claude/b01c297bd4d79264/ea2316be-4668-4831-9067-f9ac2715236d/scratchpad/setfx")
import rbxlib
from rbxlib import R, lz4_block, zstd

ROT = {}  # the special CFrame rotation ids (only identity-ish ones matter for effects; others -> identity + flag)


def read(path):
    b = open(path, 'rb').read()
    assert b.startswith(b'<roblox!')
    i = 32
    classes, inst, parent = {}, {}, {}
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
            for ref in refs: inst[ref] = {'class': cname, 'props': {}, 'ref': ref}
        elif name == b'PROP':
            cid = r.u32(); pname = r.string().decode('utf-8', 'replace'); t = r.u8()
            cname, refs = classes[cid]; n = len(refs)
            P = lambda ref, v: inst[ref]['props'].__setitem__(pname, v)
            try:
                if t == 0x01:
                    for ref in refs: P(ref, r.string())
                elif t == 0x02:
                    for ref in refs: P(ref, bool(r.u8()))
                elif t == 0x03:
                    for ref, v in zip(refs, r.ints(n)): P(ref, v)
                elif t == 0x04:
                    for ref, v in zip(refs, r.floats(n)): P(ref, v)
                elif t == 0x05:
                    for ref in refs: P(ref, struct.unpack_from('<d', data, r.i)[0]); r.i += 8
                elif t == 0x0C:
                    R_, G_, B_ = r.floats(n), r.floats(n), r.floats(n)
                    for k, ref in enumerate(refs): P(ref, ('Color3', R_[k], G_[k], B_[k]))
                elif t == 0x0D:
                    X, Y = r.floats(n), r.floats(n)
                    for k, ref in enumerate(refs): P(ref, ('Vector2', X[k], Y[k]))
                elif t == 0x0E:
                    X, Y, Z = r.floats(n), r.floats(n), r.floats(n)
                    for k, ref in enumerate(refs): P(ref, ('Vector3', X[k], Y[k], Z[k]))
                elif t == 0x10:
                    rots = []
                    for _ in refs:
                        rid = r.u8()
                        if rid == 0:
                            m = struct.unpack_from('<9f', data, r.i); r.i += 36; rots.append(m)
                        else:
                            rots.append(('id', rid))
                    X, Y, Z = r.floats(n), r.floats(n), r.floats(n)
                    for k, ref in enumerate(refs): P(ref, ('CFrame', X[k], Y[k], Z[k], rots[k]))
                elif t == 0x12:
                    raw = r.b[r.i:r.i + 4 * n]; r.i += 4 * n
                    for k, ref in enumerate(refs):
                        P(ref, ('Enum', (raw[k] << 24) | (raw[n + k] << 16) | (raw[2 * n + k] << 8) | raw[3 * n + k]))
                elif t == 0x15:
                    for ref in refs:
                        c = r.u32(); kp = []
                        for _ in range(c):
                            kp.append(struct.unpack_from('<3f', data, r.i)); r.i += 12
                        P(ref, ('NumberSequence', kp))
                elif t == 0x16:
                    for ref in refs:
                        c = r.u32(); kp = []
                        for _ in range(c):
                            kp.append(struct.unpack_from('<5f', data, r.i)); r.i += 20
                        P(ref, ('ColorSequence', kp))
                elif t == 0x17:
                    for ref in refs:
                        P(ref, ('NumberRange',) + struct.unpack_from('<2f', data, r.i)); r.i += 8
                elif t == 0x1A:
                    R_ = list(r.b[r.i:r.i + n]); r.i += n
                    G_ = list(r.b[r.i:r.i + n]); r.i += n
                    B_ = list(r.b[r.i:r.i + n]); r.i += n
                    for k, ref in enumerate(refs): P(ref, ('Color3', R_[k] / 255, G_[k] / 255, B_[k] / 255))
                else:
                    pass
            except Exception as e:
                print('prop', cname, pname, t, 'error', e, file=sys.stderr)
        elif name == b'PRNT':
            r.u8(); n = r.u32()
            ch = r.refs(n); pa = r.refs(n)
            for c, p in zip(ch, pa): parent[c] = p
    return inst, parent


def attrs(b):
    out = {}
    if not b: return out
    i = 0; n = struct.unpack_from('<I', b, 0)[0]; i = 4
    for _ in range(n):
        kl = struct.unpack_from('<I', b, i)[0]; i += 4; k = b[i:i + kl].decode(); i += kl
        t = b[i]; i += 1
        if t == 0x06: v = struct.unpack_from('<d', b, i)[0]; i += 8
        elif t == 0x03: v = bool(b[i]); i += 1
        elif t == 0x02:
            sl = struct.unpack_from('<I', b, i)[0]; i += 4; v = b[i:i + sl].decode('utf-8', 'replace'); i += sl
        elif t == 0x05: v = struct.unpack_from('<f', b, i)[0]; i += 4
        elif t == 0x04: v = struct.unpack_from('<i', b, i)[0]; i += 4
        else: out[k] = 'type%d' % t; break
        out[k] = v
    return out
