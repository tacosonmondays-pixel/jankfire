# The zombies lobby's people (DEB, GUS, MARGE: public/js/lobbyscenes/warehouse.js), the kit. Each one is ONE skinned
# mesh on its own little skeleton with its clips baked in (idle, talk, gesture), three materials (gloss: the mannequin
# plastic, hair, shoes and hard props; cloth: the clothes + the stickers; metal: chrome and brass), each part's colour in
# the vertex colours over a small crusty atlas. Draws = 3 + the game's ink hull.
# Built in game axes (x right, y up, -z forward) in mannequin units (the code mannequin's numbers, models.js
# buildCharacter), then scaled to the game's people size (x1.2, the lobby draws everyone at 1.2).
# Every bone's rest frame is the game's axes, so a clip's turns are plain game-axis angles (three.js order YXZ: yaw,
# then pitch, then roll) and the game can add a head turn on top. Conventions (same as the code mannequin / actors.js):
#   arm.x + = raise forward   arm.z + (right) / - (left) = out to the side   fore.x + = bend the elbow   hand.y = twist
#   thigh.x + = thigh forward   shin.x - = knee bends the right way (+ is the WRONG way: the house jank)
#   head.x + = look up   head.y + = look to their left   head.z + = tilt to their left   jaw.x - = mouth opens
#   lid.x - = lid comes down (about -1.4 shut)   brow.py + = raise
import os, sys, math, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
for p in (BL, os.path.join(BL, 'cast')):
    if p not in sys.path: sys.path.insert(0, p)
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, Quaternion
import numpy as np
import lib
from lib import gv, srgb, hexrgb, text_px, box, cyl, ball, lathe, tube, rod, sweep, loft, apply_mods, reset, stats, SHEETS, MODELS, ROOT
from castlib import blob, limb, subsurf

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
S = 1.2      # mannequin units -> game metres (the lobby's people are 1.2 x the mannequin)
FPS = 30
ATLAS = 256  # each material's texture: 4 crusty pattern fields on top, the stickers along the bottom 64 px


# ------------------------------------------------------------------ the skeleton
def skeleton(sh=0.25, hip=0.1, extra=None):
    """bone -> (parent, head position in mannequin units). sh = shoulder half-width, hip = hip half-width"""
    J = {'root': (None, (0, 0, 0)), 'hips': ('root', (0, 0.95, 0)), 'spine': ('hips', (0, 1.08, 0)), 'chest': ('spine', (0, 1.27, 0)),
         'neck': ('chest', (0, 1.54, 0)), 'head': ('neck', (0, 1.63, 0)), 'jaw': ('head', (0, 1.715, 0.02))}
    for s, sx in (('L', -1), ('R', 1)):
        J['lid' + s] = ('head', (sx * EYE_X, EYE_Y, ez(sx * EYE_X, EYE_Y) + 0.012))
        J['brow' + s] = ('head', (sx * 0.046, 1.83, ez(sx * 0.046, 1.83)))
        J['shoulder' + s] = ('chest', (sx * 0.11, 1.46, 0))
        J['arm' + s] = ('shoulder' + s, (sx * sh, 1.45, 0))
        J['fore' + s] = ('arm' + s, (sx * sh, 1.17, 0))
        J['hand' + s] = ('fore' + s, (sx * sh, 0.925, 0))
        J['thigh' + s] = ('hips', (sx * hip, 0.92, 0))
        J['shin' + s] = ('thigh' + s, (sx * hip, 0.49, 0))
        J['foot' + s] = ('shin' + s, (sx * hip, 0.085, 0))
    for k, v in (extra or {}).items(): J[k] = v
    return J


# the egg head (models.js: head at 1.62, an egg of r 0.14 scaled 0.85 / 1.22 / 0.95, centred 0.14 up)
HEAD_C = (0.0, 1.76, 0.0); HEAD_R = (0.119, 0.171, 0.133)
EYE_X, EYE_Y = 0.043, 1.787


def ez(x, y, c=HEAD_C, r=HEAD_R):
    """the egg's front surface (game z, negative) at x, y"""
    k = 1 - ((x - c[0]) / r[0]) ** 2 - ((y - c[1]) / r[1]) ** 2
    return c[2] - r[2] * math.sqrt(max(0.0, k))


# ------------------------------------------------------------------ the parts list
class Char:
    """everything one character is made of: pieces (mesh, weights, material kind, colour, pattern) + its stickers"""
    def __init__(self, cid, joints):
        self.cid = cid; self.J = joints; self.pieces = []; self.decals = {}; self.ink_skip = []
        self.M = {k: bpy.data.materials.new(f'npc_{cid}_{k}') for k in ('gloss', 'cloth', 'metal')}

    def add(self, o, bone, kind, color, pat=None, decal=None, span=0.5):
        """bone: a bone name (rigid), a {bone: w} dict, or fn(game point) -> {bone: w}. kind: gloss / cloth / metal.
        pat: the crusty field the UVs land in (PATS[kind]); decal: a sticker cell name (front-projected UVs)"""
        if o is None: return None
        apply_mods(o)
        o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)
        self.pieces.append(dict(o=o, bone=bone, kind=kind, color=color, pat=pat or PATS[kind][0], decal=decal, span=span))
        return o

    def many(self, objs, bone, kind, color, pat=None, span=0.5):
        for o in objs: self.add(o, bone, kind, color, pat, span=span)


PATS = {'gloss': ('plastic', 'skin', 'hair', 'vinyl'), 'cloth': ('knit', 'weave', 'fuzz', 'canvas'), 'metal': ('chrome', 'brushed', 'cast', 'chain')}


def field(kind, pat):
    """the atlas rectangle (u0, v0, u1, v1) of a pattern field: 2 x 2 fields of 128 x 96 px over the top 192 px"""
    i = PATS[kind].index(pat); cx, cy = i % 2, i // 2
    x0, y0 = cx * 128, cy * 96
    return (x0 / ATLAS, 1 - (y0 + 96) / ATLAS, (x0 + 128) / ATLAS, 1 - y0 / ATLAS)


# ------------------------------------------------------------------ the atlases (srgb, multiplied by the vertex colour)
def _rng(seed): return np.random.default_rng(seed)


def pat_px(kind, pat, w=128, h=96, seed=1):
    r = _rng(seed); y, x = np.mgrid[0:h, 0:w]
    if pat == 'plastic':   # near white with a few crusty specks (the house crunch)
        v = 0.95 + r.random((h, w)) * 0.05; v[r.random((h, w)) < 0.02] *= 0.86
    elif pat == 'skin':    # soft pores and a few freckle specks
        v = 0.975 + r.random((h, w)) * 0.025; v[r.random((h, w)) < 0.012] *= 0.93
        v = (v + np.roll(v, 1, 0) + np.roll(v, 1, 1)) / 3
    elif pat == 'hair':    # streaks along v
        col = r.random(w) * 0.16 + 0.84; v = np.tile(col, (h, 1)) * (0.97 + r.random((h, w)) * 0.03)
        v = (v + np.roll(v, 1, 1)) / 2
    elif pat == 'vinyl':   # seat vinyl / leather: blotchy
        v = 0.9 + r.random((h // 4 + 1, w // 4 + 1)).repeat(4, 0).repeat(4, 1)[:h, :w] * 0.1
    elif pat == 'knit':    # rows of V stitches
        u = (x % 4); row = (y % 4)
        v = 0.88 + 0.12 * np.clip(1 - np.abs((u - 1.5) - (row - 1.5) * np.where(u < 2, -1, 1)) / 2.0, 0, 1)
        v *= 0.96 + r.random((h, w)) * 0.04; v[(y % 4) == 0] *= 0.94
    elif pat == 'weave':   # fine cloth
        v = 0.9 + 0.06 * ((x + y) % 2) + r.random((h, w)) * 0.04
    elif pat == 'fuzz':    # fluffy (slippers, felt)
        v = 0.78 + r.random((h, w)) * 0.22; v = (v + np.roll(v, 1, 0) + np.roll(v, -1, 1)) / 3
    elif pat == 'canvas':  # canvas duck: a weave + grime
        v = 0.86 + 0.07 * (((x // 2) + (y // 2)) % 2) + r.random((h, w)) * 0.07
        v[r.random((h, w)) < 0.02] *= 0.8
    elif pat == 'chrome':
        v = 0.93 + 0.07 * np.tile(r.random(h)[:, None], (1, w)); v[r.random((h, w)) < 0.01] *= 0.75
    elif pat == 'brushed':
        v = 0.84 + 0.16 * np.tile(r.random(w)[None, :], (h, 1)) * (0.9 + r.random((h, w)) * 0.1)
    elif pat == 'cast':
        v = 0.8 + r.random((h, w)) * 0.2
    else:  # chain
        v = 0.85 + 0.15 * ((x // 3 + y // 3) % 2)
    return np.repeat(np.clip(v, 0, 1)[..., None], 3, 2).astype(np.float32)


def build_atlas(C, kind, seed):
    px = np.ones((ATLAS, ATLAS, 3), np.float32) * 0.92
    for i, pat in enumerate(PATS[kind]):
        cx, cy = i % 2, i // 2
        px[cy * 96:(cy + 1) * 96, cx * 128:(cx + 1) * 128] = pat_px(kind, pat, seed=seed + i)
    # stickers: cells along the bottom strip (x0, w, h, draw(px_cell))
    x = 0
    for name, val in list(C.decals.items()):
        if not name.startswith(kind + ':'): continue
        w, h, draw = val[:3]
        cell = np.ones((h, w, 3), np.float32); draw(cell)
        px[ATLAS - h:ATLAS, x:x + w] = cell
        C.decals[name] = (w, h, draw, (x / ATLAS, 0.0, (x + w) / ATLAS, h / ATLAS))
        x += w
    return lib._image(f'npc_{C.cid}_{kind}_t', np.clip(px, 0, 1))


def decal(C, kind, name, w, h, draw):
    """register a sticker cell (w x h px, w + h <= 64 tall) painted by draw(px)"""
    C.decals[kind + ':' + name] = (w, h, draw)


def setup_mats(C):
    spec = {'gloss': (0.34, 0.0, 0.75), 'cloth': (0.88, 0.0, 0.0), 'metal': (0.24, 1.0, 0.0)}
    for i, (kind, (rough, metal, coat)) in enumerate(spec.items()):
        m = C.M[kind]; m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
        b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
        if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.12
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = build_atlas(C, kind, 40 + i * 9); t.interpolation = 'Closest'
        vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1.0
        nt.links.new(t.outputs['Color'], mix.inputs[6]); nt.links.new(vc.outputs['Color'], mix.inputs[7])
        nt.links.new(mix.outputs[2], b.inputs['Base Color'])
        if kind == 'cloth': m.use_backface_culling = False


# ------------------------------------------------------------------ UVs + colours per piece
def _game(v): return (v.x, v.z, -v.y)


def uv_field(o, rect, span, seed):
    """box-projected UVs (metres / span across the field), squeezed into the field so nothing wraps"""
    me = o.data; uvl = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    raw = []
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index]; n = v.normal; ax = max(range(3), key=lambda k: abs(n[k]))
            g = _game(v.co)  # (per vertex, not per face: no UV seams, so no split vertices)
            a, b = {0: (g[2], g[1]), 1: (g[0], g[1]), 2: (g[0], g[2])}[ax]  # (blender x / y / z dominant)
            raw.append((li, a, b))
    if not raw: return
    A = np.array([[a, b] for _, a, b in raw]); A -= A.min(0); ext = A.max(0)
    A /= max(span, ext.max(), 1e-6)
    rr = random.Random(seed); room = 1 - A.max(0)
    A += np.array([rr.random() * room[0], rr.random() * room[1]])
    u0, v0, u1, v1 = rect; m = 1.5 / ATLAS
    for (li, _, _), (a, b) in zip(raw, A):
        uvl.data[li].uv = (u0 + m + a * (u1 - u0 - 2 * m), v0 + m + b * (v1 - v0 - 2 * m))
    # (a face whose corners all landed on one line gets its own flat projection: no zero-area UV faces)
    k = (u1 - u0 - 2 * m) / max(span, ext.max(), 1e-6)
    for poly in me.polygons:
        L = list(poly.loop_indices); q = [uvl.data[i].uv for i in L]
        area = 0.5 * abs(sum(q[i][0] * q[(i + 1) % len(q)][1] - q[(i + 1) % len(q)][0] * q[i][1] for i in range(len(q))))
        if area > 1e-9: continue
        n = poly.normal; ax = max(range(3), key=lambda j: abs(n[j]))
        pts = [_game(me.vertices[me.loops[i].vertex_index].co) for i in L]
        ab = [{0: (g[2], g[1]), 1: (g[0], g[1]), 2: (g[0], g[2])}[ax] for g in pts]
        c0 = (sum(x for x, _ in ab) / len(ab), sum(y for _, y in ab) / len(ab)); cu, cv = q[0]
        for i, (x, y) in zip(L, ab): uvl.data[i].uv = (min(u1 - m, max(u0 + m, cu + (x - c0[0]) * k)), min(v1 - m, max(v0 + m, cv + (y - c0[1]) * k)))


def uv_front(o, rect, face='-z'):
    """a sticker seen from its face direction: the image's right on the viewer's right"""
    me = o.data; uvl = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    pts = [_game(v.co) for v in me.vertices]
    if face in ('-z', '+z', '+y', '-y'): us = [p[0] for p in pts]; flip = face in ('-z', '-y')
    else: us = [p[2] for p in pts]; flip = face == '+x'
    vs = [-p[2] for p in pts] if face == '+y' else [p[2] for p in pts] if face == '-y' else [p[1] for p in pts]  # (+y: a sheet lying face up, its top toward -z; -y: face down, its top toward +z)
    ul, uh, vl, vh = min(us), max(us), min(vs), max(vs)
    u0, v0, u1, v1 = rect
    fd = {'-z': (0, 0, -1), '+z': (0, 0, 1), '+x': (1, 0, 0), '-x': (-1, 0, 0), '+y': (0, 1, 0), '-y': (0, -1, 0)}[face]
    for poly in me.polygons:
        g = _game(poly.normal)
        if abs(g[0] * fd[0] + g[1] * fd[1] + g[2] * fd[2]) < 0.5:  # (an edge of the sticker: a sliver of the cell's border, not a line)
            e = 1.0 / ATLAS
            for k, li in enumerate(poly.loop_indices): uvl.data[li].uv = (u0 + e * (0, 1, 1, 0)[k % 4], v0 + e * (0, 0, 1, 1)[k % 4])
            continue
        for li in poly.loop_indices:
            p = pts[me.loops[li].vertex_index]
            uu = ((p[0] if face in ('-z', '+z', '+y', '-y') else p[2]) - ul) / max(uh - ul, 1e-6); vv = ((-p[2] if face == '+y' else p[2] if face == '-y' else p[1]) - vl) / max(vh - vl, 1e-6)
            if flip: uu = 1 - uu
            uvl.data[li].uv = (u0 + uu * (u1 - u0), v0 + vv * (v1 - v0))


def paint(o, color):
    me = o.data
    for c in list(me.color_attributes): me.color_attributes.remove(c)
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    if callable(color):  # per-vertex: fn(game point) -> 0xRRGGBB
        for poly in me.polygons:
            for li in poly.loop_indices: ca.data[li].color = srgb(color(_game(me.vertices[me.loops[li].vertex_index].co)))
    else:
        c = srgb(color)
        for d in ca.data: d.color = c


def weigh(o, bone):
    me = o.data
    for v in me.vertices:
        w = bone if isinstance(bone, dict) else ({bone: 1.0} if isinstance(bone, str) else bone(_game(v.co)))
        t = sum(w.values()) or 1.0
        for b, x in w.items():
            if x <= 0: continue
            g = o.vertex_groups.get(b) or o.vertex_groups.new(name=b)
            g.add([v.index], x / t, 'REPLACE')


def blend(b0, b1, y0, y1, axis=1):
    """weights that slide from b0 to b1 between game coordinate y0 and y1 along axis (soft cloth over a joint)"""
    def f(p):
        t = min(1.0, max(0.0, (p[axis] - y0) / (y1 - y0)))
        t = t * t * (3 - 2 * t)
        return {b0: 1 - t, b1: t}
    return f


# ------------------------------------------------------------------ assemble: one mesh + one armature
def assemble(C, meta):
    setup_mats(C)
    objs = []
    for i, P in enumerate(C.pieces):
        o = P['o']; o.data.materials.clear(); o.data.materials.append(C.M[P['kind']])
        if P['decal']:
            w, h, draw, rect = C.decals[P['kind'] + ':' + P['decal'][0]]
            uv_front(o, rect, P['decal'][1] if len(P['decal']) > 1 else '-z')
        else:
            uv_field(o, field(P['kind'], P['pat']), P['span'], i * 7 + 3)
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-8)
        bm.to_mesh(o.data); bm.free()
        paint(o, P['color'])
        weigh(o, P['bone'])
        if '--uvdbg' in ARGV:
            uvl = o.data.uv_layers.active.data; z = 0
            for poly in o.data.polygons:
                q = [uvl[i].uv for i in poly.loop_indices]
                if abs(sum(q[i][0] * q[(i + 1) % len(q)][1] - q[(i + 1) % len(q)][0] * q[i][1] for i in range(len(q)))) < 1e-12: z += 1
            if z: print('UVZERO', C.cid, o.name, z, P['decal'] is not None)
        for poly in o.data.polygons: poly.material_index = 0
        objs.append(o)
    if '--qa-parts' in ARGV:  # (the gate on every piece apart: clashes come back with names)
        sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
        import qa_check
        for i, o in enumerate(objs): o.name = f'{i}_{o.name}'
        res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=0.0006 / S, tol=0.004 / S, uv=False)
        for k in ('errors', 'warnings'):
            for e in res.get(k, []): print('QAP_' + k.upper()[:-1], C.cid, str(e)[:600])
    if '--tris' in ARGV:
        tl = sorted(((sum(len(p.vertices) - 2 for p in o.data.polygons), o.name) for o in objs), reverse=True)
        print('JF_TRIS', sum(t for t, _ in tl), tl[:25])
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    me_o = bpy.context.view_layer.objects.active; me_o.name = f'npc_{C.cid}_mesh'; me_o.data.name = me_o.name
    me_o.data.transform(Matrix.Scale(S, 4))
    me_o.data.color_attributes.active_color = me_o.data.color_attributes['Col']

    # the armature
    ad = bpy.data.armatures.new(f'npc_{C.cid}_rig'); arm = bpy.data.objects.new(f'npc_{C.cid}', ad)
    bpy.context.scene.collection.objects.link(arm)
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = {}
    for name in order(C.J):
        par, h = C.J[name]
        b = ad.edit_bones.new(name); hv = gv(*(k * S for k in h)); b.head = hv; b.tail = hv + Vector((0, 0, 0.04)); b.roll = 0
        if par: b.parent = eb[par]; b.use_connect = False
        eb[name] = b
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    me_o.parent = arm
    md = me_o.modifiers.new('rig', 'ARMATURE'); md.object = arm
    arm['jf'] = json.dumps(meta)
    C.arm, C.mesh = arm, me_o
    return arm, me_o


def order(J):
    out, seen = [], set()
    def go(n):
        if n in seen: return
        p = J[n][0]
        if p: go(p)
        seen.add(n); out.append(n)
    for n in J: go(n)
    return out


# ------------------------------------------------------------------ forward kinematics + a small IK (authoring only)
def _R(x, y, z):
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]); Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


def fk(C, pose, want=None):
    """world 4x4 per bone (game metres, the character's own space) for a pose {'bone.x': rad, 'bone.px': m, 'bone.s': k}"""
    W = {}
    for n in C.order:
        par, h = C.J[n]
        off = np.array(h, float) * S - (np.array(C.J[par][1], float) * S if par else 0)
        g = lambda k, d=0.0: pose.get(n + '.' + k, d)
        M = np.eye(4); M[:3, :3] = _R(g('x'), g('y'), g('z')) * g('s', 1.0); M[:3, 3] = off + np.array([g('px'), g('py'), g('pz')])
        W[n] = (W[par] @ M) if par else M
    return W


def at(C, pose, bone, local=(0, 0, 0)):
    """where a point given in a bone's rest space (game metres, relative to its head) is in this pose"""
    return (fk(C, pose)[bone] @ np.array([*local, 1.0]))[:3]


def ik(C, pose, terms, chans, reg=0.02, steps=(0.4, 0.2, 0.1, 0.05, 0.025, 0.012, 0.006, 0.003)):
    """move `chans` so the terms hold: ('pos', bone, local point, target, w) / ('dir', bone, local axis, target dir, w).
    a little pull back to where they started (reg) keeps the answer near the old pose. returns a new pose"""
    p = dict(pose); p0 = {c: p.get(c, 0.0) for c in chans}
    def cost(q):
        W = fk(C, q); e = 0.0
        for t in terms:
            if t[0] == 'pos':
                _, b, lp, tg, w = t; P = (W[b] @ np.array([*lp, 1.0]))[:3]; e += w * float(np.sum((P - np.array(tg)) ** 2))
            else:
                _, b, ax, d, w = t; v = W[b][:3, :3] @ np.array(ax, float); v /= np.linalg.norm(v) + 1e-9
                dd = np.array(d, float); dd /= np.linalg.norm(dd); e += w * (1 - float(v @ dd))
        return e + reg * sum((q.get(c, 0.0) - p0[c]) ** 2 for c in chans) * 0.01
    best = cost(p)
    for st in steps:
        for _ in range(40):
            moved = False
            for c in chans:
                for s in (st, -st):
                    q = dict(p); q[c] = p.get(c, 0.0) + s; e = cost(q)
                    if e < best - 1e-12: best, p, moved = e, q, True; break
            if not moved: break
    return p


# ------------------------------------------------------------------ clips: key poses -> sampled curves -> baked actions
class Clip:
    """keys: (t, {channel: value}) each inheriting the key before it. osc: (channel, amp, period, phase) on top.
    pulses: (channel, t, amp, in, hold, out) quick bumps on top (blinks, stamps, toothpick flicks)"""
    def __init__(self, name, length, loop, base):
        self.name, self.length, self.loop = name, length, loop
        self.keys = [(0.0, dict(base))]; self.osc = []; self.pulses = []; self.marks = []

    def key(self, t, ch=None, **kw):
        prev = dict(self.keys[-1][1]) if self.keys else {}
        if ch: prev.update(ch)
        for k, v in kw.items(): prev[k.replace('__', '.')] = v
        self.keys = [k for k in self.keys if abs(k[0] - t) > 1e-6] + [(t, prev)]
        self.keys.sort(key=lambda k: k[0])
        return prev

    def last(self): return dict(self.keys[-1][1])

    def blink(self, t, lids=('lidL', 'lidR'), depth=1.0, d=0.2):
        for l in lids: self.pulses.append((l + '.x', t, -depth, d * 0.35, 0.03, d * 0.65))

    def sample(self, t):
        chans = set()
        keys = [k for k in self.keys if not (self.loop and k[0] >= self.length - 1e-6)]  # (a loop's end is its start)
        for _, p in keys: chans |= set(p)
        out = {}
        T = [k[0] for k in keys]
        for c in chans:
            V = [k[1].get(c, 0.0 if not c.endswith('.s') else 1.0) for k in keys]
            out[c] = interp(T, V, t, self.length if self.loop else None)
        for c, a, per, ph in self.osc: out[c] = out.get(c, 0.0) + a * math.sin(2 * math.pi * t / per + ph)
        for c, t0, a, ti, th, to in self.pulses:
            dt = t - t0
            if self.loop:  # (a pulse near the seam wraps round)
                if dt < -self.length / 2: dt += self.length
                elif dt > self.length / 2: dt -= self.length
            if 0 <= dt < ti: k = sm(dt / ti)
            elif ti <= dt < ti + th: k = 1.0
            elif ti + th <= dt < ti + th + to: k = 1 - sm((dt - ti - th) / to)
            else: k = 0.0
            out[c] = out.get(c, 0.0) + a * k
        return out


def sm(u): return u * u * (3 - 2 * u)


def interp(T, V, t, loop):
    """monotone cubic (Fritsch-Carlson) through the keys: no overshoot, no flat stop unless the motion turns there.
    a loop wraps round (the first key comes back at t = loop)"""
    if loop:
        T = [T[-1] - loop] + T + [T[0] + loop, T[1] + loop if len(T) > 1 else T[0] + loop * 2]
        V = [V[-1]] + V + [V[0], V[1] if len(V) > 1 else V[0]]
        t = t % loop
    if len(T) == 1: return V[0]
    if t <= T[0]: return V[0]
    if t >= T[-1]: return V[-1]
    n = len(T); d = [(V[i + 1] - V[i]) / max(T[i + 1] - T[i], 1e-9) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2 for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if d[i] == 0: m[i] = m[i + 1] = 0.0
        else:
            a, b = m[i] / d[i], m[i + 1] / d[i]; s = a * a + b * b
            if s > 9: tau = 3 / math.sqrt(s); m[i] = tau * a * d[i]; m[i + 1] = tau * b * d[i]
    i = max(k for k in range(n - 1) if T[k] <= t)
    h = T[i + 1] - T[i]; u = (t - T[i]) / h
    h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
    return h00 * V[i] + h10 * h * m[i] + h01 * V[i + 1] + h11 * h * m[i + 1]


def bake(C, clip):
    arm = C.arm
    act = bpy.data.actions.new(clip.name); act.use_fake_user = True
    arm.animation_data_create(); arm.animation_data.action = act
    n = int(round(clip.length * FPS)); prevq = {}
    moves = {b for b in C.J if any(any(c.startswith(b + '.p') for c in k[1]) for k in clip.keys)}
    scales = {b for b in C.J if any(c == b + '.s' for k in clip.keys for c in k[1])}
    for f in range(n + 1):
        t = f / FPS if not (clip.loop and f == n) else 0.0  # (a loop's last frame IS its first)
        P = clip.sample(t)
        for b in C.J:
            pb = arm.pose.bones[b]
            q = Euler((P.get(b + '.x', 0.0), P.get(b + '.y', 0.0), P.get(b + '.z', 0.0)), 'ZXY').to_quaternion()
            if b in prevq and prevq[b].dot(q) < 0: q.negate()
            prevq[b] = q; pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=f, group=b)
            if b in moves:
                pb.location = Vector((P.get(b + '.px', 0.0), P.get(b + '.py', 0.0), P.get(b + '.pz', 0.0)))
                pb.keyframe_insert('location', frame=f, group=b)
            if b in scales:
                s = max(1e-3, P.get(b + '.s', 1.0)); pb.scale = Vector((s, s, s)); pb.keyframe_insert('scale', frame=f, group=b)
    arm.animation_data.action = None
    return act


def pose_at(C, clip, t):
    """put the armature in a clip's pose at time t (for the sheets)"""
    P = clip.sample(t)
    for b in C.J:
        pb = C.arm.pose.bones[b]
        pb.rotation_quaternion = Euler((P.get(b + '.x', 0.0), P.get(b + '.y', 0.0), P.get(b + '.z', 0.0)), 'ZXY').to_quaternion()
        pb.location = Vector((P.get(b + '.px', 0.0), P.get(b + '.py', 0.0), P.get(b + '.pz', 0.0)))
        s = max(1e-3, P.get(b + '.s', 1.0)); pb.scale = Vector((s, s, s))
    bpy.context.view_layer.update()


# ------------------------------------------------------------------ export
def export(C, file_id):
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    C.arm.select_set(True); C.mesh.select_set(True)
    for o in (C.arm, C.mesh): o.hide_render = False
    path = os.path.join(MODELS, file_id + '.glb')
    for pb in C.arm.pose.bones: pb.rotation_quaternion = Quaternion(); pb.location = Vector(); pb.scale = Vector((1, 1, 1))
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=False, export_extras=True, export_yup=True,
              export_texcoords=True, export_normals=True, export_materials='EXPORT', export_image_format='AUTO', export_lights=False,
              export_cameras=False, export_skins=True, export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
              export_frame_step=1, export_vertex_color='ACTIVE', export_all_influences=False, export_def_bones=False,
              export_optimize_animation_size=True, export_anim_slide_to_zero=True, export_reset_pose_bones=True)
    props = bpy.ops.export_scene.gltf.get_rna_type().properties
    kw = {k: v for k, v in kw.items() if k in props}
    bpy.ops.export_scene.gltf(**kw)
    me = C.mesh.data; me.calc_loop_triangles()
    print(f'JF_EXPORT {file_id}: {os.path.getsize(path) // 1024} KB, {len(me.loop_triangles)} tris, {len(C.J)} bones, mats {[m.name for m in me.materials]}')
    return path


# ------------------------------------------------------------------ the ink hull for the sheets (the game draws its own)
def ink_on(C, k=0.007):
    m = bpy.data.materials.get('npc_ink') or bpy.data.materials.new('npc_ink')
    m.use_nodes = True; m.use_backface_culling = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = srgb(0x120818); b.inputs['Roughness'].default_value = 1.0
    b.inputs['Specular IOR Level'].default_value = 0.0
    if 'npc_ink' not in [x.name for x in C.mesh.data.materials]: C.mesh.data.materials.append(m)
    md = C.mesh.modifiers.new('ink', 'SOLIDIFY'); md.thickness = k; md.offset = 1.0; md.use_flip_normals = True
    md.material_offset = len(C.mesh.data.materials) - 1; md.use_rim = False
    return md


def ink_off(C):
    md = C.mesh.modifiers.get('ink')
    if md: C.mesh.modifiers.remove(md)
    i = C.mesh.data.materials.find('npc_ink')
    if i >= 0: C.mesh.data.materials.pop(index=i)


# ------------------------------------------------------------------ sheets
def _studio(H, c):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 24
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.get('npcw') or bpy.data.worlds.new('npcw'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(0x2a2236); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.7
    made = []
    def light(e, loc, sz, col=(1, 1, 1)):
        L = bpy.data.lights.new('l', 'AREA'); L.energy = e * H * H; L.size = sz * H; L.color = col
        o = bpy.data.objects.new('l', L); bpy.context.scene.collection.objects.link(o); o.location = c + Vector(loc) * H
        d = c - o.location; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); made.append(o)
    light(80, (0.9, 1.6, 1.0), 0.8); light(30, (-1.4, 0.8, 0.4), 1.0, (0.85, 0.9, 1.0)); light(70, (-0.5, -1.6, 0.9), 0.5, (1.0, 0.6, 0.85))
    fl = bpy.data.objects.get('npc_floor')
    if not fl:
        bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=1.3)
        me = bpy.data.meshes.new('npc_floor'); bm.to_mesh(me); bm.free(); fl = bpy.data.objects.new('npc_floor', me)
        bpy.context.scene.collection.objects.link(fl)
        fm = bpy.data.materials.new('npc_floor_m'); fm.use_nodes = True
        fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = srgb(0x4a3f58); fm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.8
        me.materials.append(fm)
    return made


def _cam():
    cam = bpy.data.objects.get('npc_cam')
    if not cam:
        cam = bpy.data.objects.new('npc_cam', bpy.data.cameras.new('npc_cam')); bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def bounds(C):
    dg = bpy.context.evaluated_depsgraph_get(); ev = C.mesh.evaluated_get(dg); me = ev.to_mesh()
    pts = np.array([tuple(C.mesh.matrix_world @ v.co) for v in me.vertices]); ev.to_mesh_clear()
    return pts.min(0), pts.max(0)


def render_views(C, views, res, tag, look_at=None, dist=2.6, lens=60):
    """views: [(label, yaw degrees round the model, height k)] -> png paths. 0 = from the front (game -z)"""
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = res
    lo, hi = bounds(C); H = hi[2] - lo[2]; c = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2] + H * 0.52)) if look_at is None else Vector(look_at)
    made = _studio(H, c); cam = _cam(); cam.data.lens = lens; cam.data.clip_start = 0.01; cam.data.clip_end = 100
    fl = bpy.data.objects['npc_floor']; fl.location = Vector((c.x, c.y, lo[2] - 0.002)); fl.scale = Vector((H, H, 1))
    tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True); out = []
    for i, (lab, deg, hk, *rest) in enumerate(views):
        a = math.radians(deg); d = Vector((math.sin(a), math.cos(a), hk))  # (the model faces game -z = blender +y)
        dd = rest[0] if rest else dist
        tgt = Vector(rest[1]) if len(rest) > 1 else c
        cam.location = tgt + d.normalized() * H * dd
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        p = os.path.join(tmp, f'{tag}_{i}.png'); sc.render.filepath = p
        bpy.ops.render.render(write_still=True); out.append((lab, p))
    for o in made: bpy.data.objects.remove(o, do_unlink=True)
    return out


def tile(paths, cols, dst, title, res):
    """tile labelled pngs into one jpg (ffmpeg drawtext with the house font)"""
    font = os.path.join(BL, 'fonts', 'comic-neue-700.ttf')
    fnt = f":fontfile='{font}'" if os.path.exists(font) else ''
    ins = ' '.join(f'-i "{p}"' for _, p in paths)
    n = len(paths); rows = (n + cols - 1) // cols; w, h = res
    lay = '|'.join(f'{(i % cols) * w}_{(i // cols) * h}' for i in range(n))
    lab = ';'.join(f'[{i}:v]drawtext=text=\'{t}\'{fnt}:x=10:y=8:fontsize=22:fontcolor=0xffe14d:box=1:boxcolor=0x120818@0.7:boxborderw=4[v{i}]' for i, (t, _) in enumerate(paths))
    stack = ''.join(f'[v{i}]' for i in range(n))
    flt = f'{lab};{stack}xstack=inputs={n}:layout={lay}:fill=0x120818[s];[s]pad=iw:ih+44:0:44:0x120818,drawtext=text=\'{title}\'{fnt}:x=12:y=8:fontsize=28:fontcolor=0xff4fd8[o]' if n > 1 else \
        f'{lab};[v0]pad=iw:ih+44:0:44:0x120818,drawtext=text=\'{title}\'{fnt}:x=12:y=8:fontsize=28:fontcolor=0xff4fd8[o]'
    os.system(f'ffmpeg -loglevel error -y {ins} -filter_complex "{flt}" -map "[o]" -q:v 3 "{dst}"')
    for _, p in paths:
        if os.path.exists(p): os.remove(p)
    print('JF_SHEET', dst)
    return dst


# ------------------------------------------------------------------ shared body pieces (mannequin units, game axes)
def egg(name, m=None, fn=None, seg=28, rings=20):
    return blob(name, HEAD_C, HEAD_R, m, fn=fn, seg=seg, rings=rings)


def hand_r(curl, thumb, k=1.0, wrist=True):
    """a chunky mannequin right hand hanging down (wrist at the origin, fingers to -y, palm facing -x, thumb in front
    at -z). curl: 4 x (base, tip) bend in radians (- = toward the palm), thumb: (out, bend). returns (palm parts,
    finger parts [4 lists], thumb parts)"""
    R = 0.0105 * k
    palm = [blob('palm', (0.0, -0.042 * k, 0.0), (0.017 * k, 0.042 * k, 0.037 * k), None, seg=14, rings=10),
            blob('heel', (-0.006 * k, -0.02 * k, -0.018 * k), (0.016 * k, 0.022 * k, 0.018 * k), None, seg=10, rings=8)]
    if wrist: palm.append(ball(0.026 * k, (0, 0.004 * k, 0), None, seg=12, rings=8, name='wrist'))
    fing = []
    FZ = ((-0.03, 0.05), (-0.013, 0.056), (0.014, 0.052), (0.031, 0.042))  # (a bit more gap side to side: curled, neighbours don't share a plane)
    for i, (zf, ln) in enumerate(FZ):
        a0, a1 = curl[i]; p0 = Vector((-0.004 * k, (-0.078, -0.0805, -0.0792, -0.0755)[i] * k, zf * k)); L0, L1 = ln * 0.55 * k, ln * 0.45 * k  # (the knuckles on an arc)
        d0 = Vector((math.sin(a0), -math.cos(a0), 0)); p1 = p0 + d0 * L0
        d1 = Vector((math.sin(a0 + a1), -math.cos(a0 + a1), 0)); p2 = p1 + d1 * L1
        pts = [tuple(p0 - d0 * 0.004), tuple(p0 + d0 * L0 * 0.5), tuple(p1), tuple(p1 + d1 * L1 * 0.55), tuple(p2)]
        r = R * (1.0, 1.1, 1.02, 0.92)[i]  # (neighbours a touch different: side by side they never share a plane)
        fing.append([limb('f%d' % i, pts, [r * 1.05, r, r * 0.95, r * 0.9, r * 0.75], None, seg=8)])
    to, tb = thumb
    t0 = Vector((-0.012 * k, -0.03 * k, -0.034 * k)); dt0 = Vector((-math.sin(to) * 0.6, -math.cos(to), -0.45)).normalized()
    t1 = t0 + dt0 * 0.03 * k; dt1 = Vector((-math.sin(to + tb) * 0.8, -math.cos(to + tb) * 0.7, -0.1)).normalized(); t2 = t1 + dt1 * 0.026 * k
    th = [limb('thumb', [tuple(t0 - dt0 * 0.01), tuple(t1), tuple(t2)], [R * 1.25, R * 1.1, R * 0.85], None, seg=8)]
    return palm, fing, th


def mirror(objs):
    """flip pieces from the right side to the left (x -> -x), normals kept outward"""
    for o in objs:
        apply_mods(o)
        o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)
        o.data.transform(Matrix.Scale(-1, 4, Vector((1, 0, 0))))
        o.data.flip_normals()
    return objs


def move(objs, off=(0, 0, 0), R=None, pivot=(0, 0, 0)):
    """carry pieces made round the origin: rotate by R (game-axis euler YXZ or a 3x3) about pivot, then offset"""
    Rm = None
    if R is not None:
        Rm = _R(*R) if len(R) == 3 and not hasattr(R[0], '__len__') else np.array(R)
    for o in objs:
        apply_mods(o)
        o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)
        for v in o.data.vertices:
            g = np.array(_game(v.co)) - np.array(pivot)
            if Rm is not None: g = Rm @ g
            g = g + np.array(pivot) + np.array(off)
            v.co = gv(*g)
        o.data.update()
    return objs


def qa(C):
    """the blender-asset-qa gate on the joined, skinned mesh (rest pose)"""
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[C.mesh.name], profile='game', eps=0.0006, tol=0.004)
    print('QA_PASS', C.cid, res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], C.cid, str(e)[:400])
    for n, m in res.get('objects', {}).items():
        print('QA_OBJ', n, {k: v for k, v in m.items() if not isinstance(v, (list, dict))})
    return res
