# The bought "Katana Combat Pack" (robloxanimations.com, BuiltByBit 117603) -> what the katana uses (20 Nov 2026).
# The pack's files live in the vault (Documents\JANKFIRE Vault\Tools\Packs-20nov\katana-combat\unzipped\...) and NEVER go
# in git; the licence lets us publish its KeyframeSequences to the owner's account and use them in our experience. This
# tool reads the pack's binary .rbxm offline (runs nothing in it) and writes, into a folder outside the repo:
#   py tools/roblox/katana_pack.py <pack.rbxm> list
#       every KeyframeSequence: name, length, keyframes, its markers (name @ time)
#   py tools/roblox/katana_pack.py <pack.rbxm> export <clip> <out.rbxm> [--upper] [--name N] [--from a --to b] [--speed k]
#       one clip as its own KeyframeSequence (.rbxmx, then .rbxm by Rojo: Open Cloud refuses XML for an Animation).
#       --upper: the legs dropped and the root / lower torso (R15) or torso (R6) left unweighted, so it plays over a run
#       --from/--to: a window (s); --speed: times divided by k (a clip retimed to the katana's own numbers)
#   py tools/roblox/katana_pack.py <pack.rbxm> hand <clip> <out.json> [--fps 60]
#       the R15 right hand through the clip (forward kinematics on the pack's own rig): its position and turn each frame
#       in the body's start frame (the hips at frame 0), for the first-person keys (katana_vm.py)
import sys, os, re, json, struct, math, subprocess

# ------------------------------------------------------------------ the binary reader (LZ4 / zstd chunks)
def lz4_block(src, outlen):
    dst = bytearray(); i = 0; n = len(src)
    while i < n:
        tok = src[i]; i += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                b = src[i]; i += 1; lit += b
                if b != 255: break
        dst += src[i:i + lit]; i += lit
        if i >= n: break
        off = src[i] | (src[i + 1] << 8); i += 2
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255: break
        ml += 4
        start = len(dst) - off
        for k in range(ml): dst.append(dst[start + k])
    return bytes(dst)

def unzstd(src, outlen):
    try:
        import zstandard
        return zstandard.ZstdDecompressor().decompress(src, max_output_size=outlen)
    except ImportError:
        raise SystemExit('this file is zstd-compressed: run with a Python that has zstandard')

class Rd:
    def __init__(s, b): s.b, s.i = b, 0
    def u8(s): v = s.b[s.i]; s.i += 1; return v
    def u32(s): v = struct.unpack_from('<I', s.b, s.i)[0]; s.i += 4; return v
    def f32le(s): v = struct.unpack_from('<f', s.b, s.i)[0]; s.i += 4; return v
    def string(s): n = s.u32(); v = s.b[s.i:s.i + n]; s.i += n; return v
    def raw32(s, n):
        raw = s.b[s.i:s.i + 4 * n]; s.i += 4 * n
        return [(raw[k] << 24) | (raw[n + k] << 16) | (raw[2 * n + k] << 8) | raw[3 * n + k] for k in range(n)]
    def ints(s, n): return [(x >> 1) ^ -(x & 1) for x in s.raw32(n)]
    def refs(s, n):
        acc, out = 0, []
        for d in s.ints(n): acc += d; out.append(acc)
        return out
    def floats(s, n):
        out = []
        for x in s.raw32(n):
            x = ((x >> 1) | ((x & 1) << 31)) & 0xFFFFFFFF
            out.append(struct.unpack('<f', struct.pack('<I', x))[0])
        return out

AXES = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (-1, 0, 0), (0, -1, 0), (0, 0, -1)]  # NormalId order: Right Top Back Left Bottom Front
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

SPECIAL = [0, 0]  # (axis-aligned turns read, of them non-identity Pose turns)
def read(path):
    b = open(path, 'rb').read()
    if not b.startswith(b'<roblox!'): raise SystemExit('not a binary Roblox file')
    i = 32
    classes, inst, parent, order = {}, {}, {}, []
    while i < len(b):
        name = b[i:i + 4]; clen, ulen = struct.unpack_from('<II', b, i + 4); i += 16
        if clen == 0: data = b[i:i + ulen]; i += ulen
        else:
            comp = b[i:i + clen]; i += clen
            data = unzstd(comp, ulen) if comp[:4] == b'\x28\xb5\x2f\xfd' else lz4_block(comp, ulen)
        if name == b'END\x00': break
        r = Rd(data)
        if name == b'INST':
            cid = r.u32(); cname = r.string().decode('utf-8', 'replace'); r.u8(); n = r.u32()
            refs = r.refs(n); classes[cid] = (cname, refs)
            for ref in refs: inst[ref] = {'class': cname, 'props': {}, 'kids': []}
        elif name == b'PROP':
            cid = r.u32(); pname = r.string().decode('utf-8', 'replace'); t = r.u8()
            cname, refs = classes[cid]; n = len(refs)
            P = lambda vals: [inst[ref]['props'].__setitem__(pname, v) for ref, v in zip(refs, vals)]
            if t == 0x01: P([r.string() for _ in range(n)])
            elif t == 0x02: P([bool(r.u8()) for _ in range(n)])
            elif t == 0x03: P(r.ints(n))
            elif t == 0x04: P(r.floats(n))
            elif t == 0x0E:
                xs, ys, zs = r.floats(n), r.floats(n), r.floats(n); P(list(zip(xs, ys, zs)))
            elif t == 0x10:
                rots = []
                for _ in range(n):
                    rid = r.u8()
                    if rid == 0: rots.append([r.f32le() for _ in range(9)])
                    else:  # an axis-aligned turn by id: its x and y axes are the matrix's COLUMNS (R15 grips: -90 about X)
                        x = AXES[(rid - 1) // 6]; y = AXES[(rid - 1) % 6]; z = cross(x, y)
                        rots.append([x[0], y[0], z[0], x[1], y[1], z[1], x[2], y[2], z[2]])
                        SPECIAL[0] += 1
                        if rid != 2 and cname == 'Pose': SPECIAL[1] += 1
                xs, ys, zs = r.floats(n), r.floats(n), r.floats(n)
                P([(p[0], p[1], p[2], *R) for p, R in zip(zip(xs, ys, zs), rots)])
            elif t == 0x12: P(r.raw32(n))
            elif t == 0x13: P(r.refs(n))
        elif name == b'PRNT':
            r.u8(); n = r.u32(); ch = r.refs(n); pa = r.refs(n)
            for c, p in zip(ch, pa):
                parent[c] = p
                if p in inst: inst[p]['kids'].append(c)
                else: order.append(c)
    return inst, parent, order

def nm(o): v = o['props'].get('Name', b''); return v.decode('utf-8', 'replace') if isinstance(v, bytes) else str(v)
def kids(inst, ref, cls=None): return [c for c in inst[ref]['kids'] if cls is None or inst[c]['class'] == cls]

def sequences(inst, parent):
    out = {}
    for ref, o in inst.items():
        if o['class'] != 'KeyframeSequence': continue
        p = parent.get(ref)
        # the pack keeps each clip twice: in the Katana KeyframeSequences folders and in the rig's AnimSaves (same data)
        if p is not None and inst.get(p, {}).get('class') == 'ObjectValue': continue
        out.setdefault(nm(o), ref)
    return out

def keyframes(inst, seq):
    kf = sorted(kids(inst, seq, 'Keyframe'), key=lambda k: inst[k]['props'].get('Time', 0))
    return kf

def markers(inst, seq):
    out = []
    for k in keyframes(inst, seq):
        t = inst[k]['props'].get('Time', 0)
        for m in kids(inst, k, 'KeyframeMarker'):
            v = inst[m]['props'].get('Value', b'')
            out.append((round(t, 4), nm(inst[m]), v.decode('utf-8', 'replace') if isinstance(v, bytes) else str(v)))
    return out

# ------------------------------------------------------------------ CFrame maths (tuples: x y z r00..r22, row-major)
def cf_mul(a, b):
    ar, br = a[3:], b[3:]
    R = [sum(ar[i * 3 + k] * br[k * 3 + j] for k in range(3)) for i in range(3) for j in range(3)]
    p = [a[i] + sum(ar[i * 3 + k] * b[k] for k in range(3)) for i in range(3)]
    return tuple(p + R)
def cf_inv(a):
    R = a[3:]; Rt = [R[j * 3 + i] for i in range(3) for j in range(3)]
    p = [-sum(Rt[i * 3 + k] * a[k] for k in range(3)) for i in range(3)]
    return tuple(p + Rt)
IDENT = (0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1)

# ------------------------------------------------------------------ export: one clip as its own .rbxm
R15_LEGS = {'LeftUpperLeg', 'LeftLowerLeg', 'LeftFoot', 'RightUpperLeg', 'RightLowerLeg', 'RightFoot'}
R6_LEGS = {'Left Leg', 'Right Leg'}
UNWEIGHT = {'HumanoidRootPart', 'LowerTorso', 'Torso'}
ROJO = os.environ.get('ROJO') or os.path.join(os.path.expanduser('~'), '.aftman', 'tool-storage', 'rojo-rbx', 'rojo', '7.7.1', 'rojo.exe')

def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
def cf_xml(name, c):
    tags = ['X', 'Y', 'Z', 'R00', 'R01', 'R02', 'R10', 'R11', 'R12', 'R20', 'R21', 'R22']
    return '<CoordinateFrame name="%s">%s</CoordinateFrame>' % (name, ''.join('<%s>%.6f</%s>' % (t, x, t) for t, x in zip(tags, c)))

def export(inst, seq, out, upper, name, t0, t1, speed):
    ref = [0]
    def nref(): ref[0] += 1; return 'RBX%08X' % ref[0]
    def pose_xml(p):
        o = inst[p]; pn = nm(o)
        if upper and (pn in R15_LEGS or pn in R6_LEGS): return ''
        w = o['props'].get('Weight', 1)
        c = o['props'].get('CFrame', IDENT)
        if upper and pn in UNWEIGHT: w, c = 0, IDENT
        sub = ''.join(pose_xml(k) for k in kids(inst, p, 'Pose'))
        return ('<Item class="Pose" referent="%s"><Properties><string name="Name">%s</string>%s<float name="Weight">%g</float>'
                '<token name="EasingStyle">%d</token><token name="EasingDirection">%d</token></Properties>%s</Item>'
                % (nref(), esc(pn), cf_xml('CFrame', c), w, o['props'].get('EasingStyle', 0), o['props'].get('EasingDirection', 0), sub))
    items = []
    kfs = [k for k in keyframes(inst, seq) if t0 - 1e-4 <= inst[k]['props'].get('Time', 0) <= t1 + 1e-4]
    base = inst[kfs[0]]['props'].get('Time', 0) if kfs else 0
    for k in kfs:
        t = (inst[k]['props'].get('Time', 0) - base) / speed
        poses = ''.join(pose_xml(p) for p in kids(inst, k, 'Pose'))
        mk = ''.join('<Item class="KeyframeMarker" referent="%s"><Properties><string name="Name">%s</string><string name="Value">%s</string></Properties></Item>'
                     % (nref(), esc(nm(inst[m])), esc((inst[m]['props'].get('Value', b'') or b'').decode('utf-8', 'replace')))
                     for m in kids(inst, k, 'KeyframeMarker'))
        items.append('<Item class="Keyframe" referent="%s"><Properties><string name="Name">%s</string><float name="Time">%.5f</float></Properties>%s%s</Item>'
                     % (nref(), esc(nm(inst[k]) or 'Keyframe'), t, poses, mk))
    s = inst[seq]['props']
    xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" version="4"><Item class="KeyframeSequence" referent="%s"><Properties>'
           '<string name="Name">%s</string><bool name="Loop">false</bool><token name="Priority">%d</token></Properties>%s</Item></roblox>'
           % (nref(), esc(name), s.get('Priority', 2), ''.join(items)))
    xml_path = out + 'x'
    open(xml_path, 'w', encoding='utf-8').write(xml)
    proj = out + '.project.json'
    open(proj, 'w', encoding='utf-8').write(json.dumps({'name': name, 'tree': {'$path': os.path.basename(xml_path)}}))
    subprocess.run([ROJO, 'build', proj, '-o', out], check=True, capture_output=True)
    os.remove(proj)
    last = (inst[kfs[-1]]['props'].get('Time', 0) - base) / speed if kfs else 0
    print('%s: %d keyframes, %.3f s%s -> %s' % (name, len(kfs), last, ' (upper body)' if upper else '', out))

# ------------------------------------------------------------------ hand: R15 forward kinematics on the pack's rig
R15_JOINTS = {  # Part1: (Part0, the rig attachment both carry) - the standard R15 joints (C0 / C1 = the two attachments)
    'LowerTorso': ('HumanoidRootPart', 'RootRigAttachment'), 'UpperTorso': ('LowerTorso', 'WaistRigAttachment'),
    'Head': ('UpperTorso', 'NeckRigAttachment'),
    'RightUpperArm': ('UpperTorso', 'RightShoulderRigAttachment'), 'RightLowerArm': ('RightUpperArm', 'RightElbowRigAttachment'),
    'RightHand': ('RightLowerArm', 'RightWristRigAttachment'),
    'LeftUpperArm': ('UpperTorso', 'LeftShoulderRigAttachment'), 'LeftLowerArm': ('LeftUpperArm', 'LeftElbowRigAttachment'),
    'LeftHand': ('LeftLowerArm', 'LeftWristRigAttachment'),
}
def rig_joints(inst):
    # the pack's "Katana Rig" (AnimationConstraints on rig attachments): C0 = Part0's attachment, C1 = Part1's
    rig = next(r for r, o in inst.items() if o['class'] == 'Model' and nm(o) == 'Katana Rig')
    parts = {nm(inst[c]): c for c in inst[rig]['kids'] if inst[c]['class'] in ('MeshPart', 'Part')}
    def att(part, name):
        for c in inst[parts[part]]['kids']:
            if inst[c]['class'] == 'Attachment' and nm(inst[c]) == name: return inst[c]['props'].get('CFrame', IDENT)
        raise SystemExit('no %s on %s' % (name, part))
    joints = {}
    for p1, (p0, a) in R15_JOINTS.items():
        if p1 in parts and p0 in parts: joints[p1] = (p0, att(p0, a), att(p1, a))
    grip = att('RightHand', 'RightGripAttachment')
    # the sword's own joint: a Motor6D RightHand -> RightHandle, which the clips turn too (up to 70 deg in Light02)
    h0 = IDENT
    for r, o in inst.items():
        if o['class'] == 'Motor6D' and isinstance(o['props'].get('Part1'), int) and nm(inst.get(o['props']['Part1'], {'props': {}})) == 'RightHandle':
            h0 = o['props'].get('C0', IDENT)
    return joints, {'grip': grip, 'handle': h0}

def pose_at(inst, seq, t):
    # each joint's Transform at time t: linear between the keyframes that pose it (good enough for a hand's path)
    kfs = keyframes(inst, seq)
    tracks = {}
    for k in kfs:
        kt = inst[k]['props'].get('Time', 0)
        stack = list(kids(inst, k, 'Pose'))
        while stack:
            p = stack.pop(); o = inst[p]
            stack += kids(inst, p, 'Pose')
            if o['props'].get('Weight', 1) == 0: continue
            tracks.setdefault(nm(o), []).append((kt, o['props'].get('CFrame', IDENT)))
    out = {}
    for j, tr in tracks.items():
        if t <= tr[0][0]: out[j] = tr[0][1]; continue
        if t >= tr[-1][0]: out[j] = tr[-1][1]; continue
        for (ta, ca), (tb, cb) in zip(tr, tr[1:]):
            if ta <= t <= tb:
                u = (t - ta) / (tb - ta) if tb > ta else 0
                out[j] = lerp_cf(ca, cb, u); break
    return out

def quat(R):
    m = R; tr = m[0] + m[4] + m[8]
    if tr > 0:
        s = math.sqrt(tr + 1) * 2; return ((m[7] - m[5]) / s, (m[2] - m[6]) / s, (m[3] - m[1]) / s, s / 4)
    if m[0] > m[4] and m[0] > m[8]:
        s = math.sqrt(1 + m[0] - m[4] - m[8]) * 2; return (s / 4, (m[1] + m[3]) / s, (m[2] + m[6]) / s, (m[7] - m[5]) / s)
    if m[4] > m[8]:
        s = math.sqrt(1 + m[4] - m[0] - m[8]) * 2; return ((m[1] + m[3]) / s, s / 4, (m[5] + m[7]) / s, (m[2] - m[6]) / s)
    s = math.sqrt(1 + m[8] - m[0] - m[4]) * 2; return ((m[2] + m[6]) / s, (m[5] + m[7]) / s, s / 4, (m[3] - m[1]) / s)
def mat(q):
    x, y, z, w = q
    return [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
            2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
            2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]
def lerp_cf(a, b, u):
    qa, qb = quat(a[3:]), quat(b[3:])
    d = sum(x * y for x, y in zip(qa, qb))
    if d < 0: qb = tuple(-x for x in qb); d = -d
    if d > 0.9995: q = tuple(x + (y - x) * u for x, y in zip(qa, qb))
    else:
        th = math.acos(d); s = math.sin(th)
        q = tuple((math.sin((1 - u) * th) * x + math.sin(u * th) * y) / s for x, y in zip(qa, qb))
    n = math.sqrt(sum(x * x for x in q)); q = tuple(x / n for x in q)
    return tuple([a[i] + (b[i] - a[i]) * u for i in range(3)] + mat(q))

def world(joints, tf, part):
    if part == 'HumanoidRootPart' or part not in joints: return IDENT
    p0, c0, c1 = joints[part]
    return cf_mul(cf_mul(cf_mul(world(joints, tf, p0), c0), tf.get(part, IDENT)), cf_inv(c1))

def hand(inst, seq, fps, no_handle=False):
    joints, parts = rig_joints(inst)
    kfs = keyframes(inst, seq)
    length = inst[kfs[-1]]['props'].get('Time', 0)
    frames = []
    n = int(round(length * fps)) + 1
    for i in range(n):
        t = min(length, i / fps)
        tf = pose_at(inst, seq, t)
        # the fist's grip (where a held weapon sits), turned as the sword's own joint has it: the handle's C0 turn and its
        # pose's turn (the blade along the result's +Y, as along the grip's when the handle is still). --no-handle: the
        # grip alone (the first take)
        if no_handle: H = cf_mul(world(joints, tf, 'RightHand'), parts['grip'])
        else:
            th = tf.get('RightHandle', IDENT)
            turn = tuple([0, 0, 0] + list(cf_mul(parts['handle'], th)[3:]))
            H = cf_mul(cf_mul(world(joints, tf, 'RightHand'), tuple(list(parts['grip'][:3]) + [1, 0, 0, 0, 1, 0, 0, 0, 1])), turn)
        Hd = world(joints, tf, 'Head')
        L = world(joints, tf, 'LeftHand')
        frames.append({'t': round(t, 4), 'hand': [round(x, 5) for x in H], 'head': [round(x, 5) for x in Hd], 'left': [round(x, 4) for x in L[:3]]})
    return {'fps': fps, 'length': length, 'frames': frames, 'markers': markers(inst, seq), 'joints': sorted(joints)}

# ------------------------------------------------------------------ cli
if __name__ == '__main__':
    a = sys.argv[1:]
    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    inst, parent, order = read(a[0])
    seqs = sequences(inst, parent)
    cmd = a[1]
    if cmd == 'list':
        for n, ref in sorted(seqs.items()):
            kf = keyframes(inst, ref)
            ln = inst[kf[-1]]['props'].get('Time', 0) if kf else 0
            mk = markers(inst, ref)
            print('%-58s %6.3f s %3d kf  pri %s  %s' % (n, ln, len(kf), inst[ref]['props'].get('Priority'), ' '.join('%s@%g' % (m[1], m[0]) for m in mk)))
    elif cmd == 'export':
        clip = a[2]; out = a[3]
        ref = seqs.get(clip) or next((r for n, r in seqs.items() if clip.lower() in n.lower()), None)
        if ref is None: raise SystemExit('no clip ' + clip)
        export(inst, ref, out, '--upper' in a, opt('--name', clip), float(opt('--from', '0')), float(opt('--to', '999')), float(opt('--speed', '1')))
    elif cmd == 'hand':
        clip = a[2]; out = a[3]
        ref = seqs.get(clip) or next((r for n, r in seqs.items() if clip.lower() in n.lower()), None)
        if ref is None: raise SystemExit('no clip ' + clip)
        d = hand(inst, ref, int(opt("--fps", "60")), "--no-handle" in a)
        json.dump(d, open(out, 'w'), indent=0)
        print('%s: %d frames, %.3f s, joints %s' % (clip, len(d['frames']), d['length'], ', '.join(d['joints'])))
