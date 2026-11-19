"""MotionBricks trial (19 Nov 2026): our own poses in, NVIDIA's in-betweens out, four takes per recipe.

run (from a MotionBricks checkout, in its uv environment; see tools/motionbricks/README.md):
    uv run --frozen python <repo>/tools/motionbricks/mb_gen.py <recipe.json> <clips dir> <out dir>

  * the poses come from our Mixamo clips (sampled by mixamo_rot_sample.py into <clips dir>/<clip>.json), NEVER from the
    sample clips bundled with MotionBricks: those are under NVIDIA's Sample Data Evaluation License (evaluation only).
    the model itself (NVIDIA Open Model Agreement) may be used commercially and NVIDIA claims no rights in its outputs.
  * retarget Mixamo -> SOMA (both rest in a T-pose): a bone's turn against its rest, D = R(t) R(rest)^-1, goes on the
    SOMA joint on top of a small rest alignment A (SOMA's bone direction turned onto Mixamo's): W = D A Rsoma(rest).
    the hips move by the hip-height ratio. SOMA's fingers, jaw, eyes and Neck2 keep their rest turn.
  * Blender axes (Z up, Mixamo faces -Y) -> SOMA model space (Y up, faces +Z): (x, y, z) -> (x, z, -y).
  * a recipe: a context (four poses at 30 Hz from a clip), then targets, each one generation from the last four
    poses before it. a target is 1-4 poses from a clip (or "same": the last context pose), placed by "move"
    (metres: forward, left) and "turn" (degrees, left) from where the character stands in the clip's facing frame (not
    the hips': a slash twists them 100 degrees), its poses moving on at "carry" m/s (a standstill target far away
    comes out as a flip), changed by "edit"s:
      { "joint": "Head", "yaw": 30, "pitch": 0, "roll": 0 }   turn a joint (and all below it) about the body's up /
                                                              left / forward axes, degrees (yaw + = to its left,
                                                              pitch + = down/forward, roll + = to its right)
      { "reach": "Right", "to": [l, u, f], "pole": [l, u, f] } put the hand at a spot (metres from the feet: left, up,
                                                              forward) with the elbow toward pole: two-bone IK
      { "point": "Right", "dir": [l, u, f] }                  the whole arm straight along dir (an aim)
    each take k (0-3) lets the model pick from "tokens"[k] (tokens of four frames; default 7-8, 9-10, 11-12, 13-14).
  * out: <out dir>/<recipe>_t<k>.json in mixamo_rot_sample.py's shape (rest + every frame's bone turns and joint
    heads, Blender axes, Mixamo's size), so mixamo_r15.py makes an R15 clip of it and mb_sheet.py draws it; plus "cuts"
    (the frame each generation starts at) and "tokens".
"""
import json, math, os, sys
import numpy as np
import warp as wp
from scipy.spatial.transform import Rotation as Rot

from motionbricks.io.usd import load_skeleton_from_usd
from motionbricks.io.utils import SOMA_SKELETON_PRIM_PATH, get_asset_file
from motionbricks.model.config import MotionBricksInferenceConfig
from motionbricks.model.soma.contract import SOMA_N1_FP32_ONNX_PATH
from motionbricks.model.soma.engine import MotionBricksSOMAEngine

FPS = 30.0
C = np.array([[1.0, 0, 0], [0, 0, 1.0], [0, -1.0, 0]])  # Blender -> SOMA
# SOMA joint <- Mixamo bone, and the child each one's direction is measured to (SOMA, Mixamo)
MAP = [('Hips', 'Hips', 'Spine1', 'Spine'), ('Spine1', 'Spine', 'Spine2', 'Spine1'), ('Spine2', 'Spine1', 'Chest', 'Spine2'),
       ('Chest', 'Spine2', 'Neck1', 'Neck'), ('Neck1', 'Neck', 'Head', 'Head'), ('Head', 'Head', 'HeadEnd', 'HeadTop_End')]
for s in ('Left', 'Right'):
    MAP += [(s + 'Shoulder', s + 'Shoulder', s + 'Arm', s + 'Arm'), (s + 'Arm', s + 'Arm', s + 'ForeArm', s + 'ForeArm'),
            (s + 'ForeArm', s + 'ForeArm', s + 'Hand', s + 'Hand'), (s + 'Hand', s + 'Hand', s + 'HandMiddle1', s + 'HandMiddle1'),
            (s + 'Leg', s + 'UpLeg', s + 'Shin', s + 'Leg'), (s + 'Shin', s + 'Leg', s + 'Foot', s + 'Foot'),
            (s + 'Foot', s + 'Foot', s + 'ToeBase', s + 'ToeBase'), (s + 'ToeBase', s + 'ToeBase', s + 'ToeEnd', s + 'Toe_End')]
# where each Mixamo joint head is drawn from on the SOMA body (the sheets)
HEADS = {'Hips': 'Hips', 'Spine': 'Spine1', 'Spine1': 'Spine2', 'Spine2': 'Chest', 'Neck': 'Neck1', 'Head': 'Head',
         'HeadTop_End': 'HeadEnd'}
for s in ('Left', 'Right'):
    HEADS.update({s + 'Shoulder': s + 'Shoulder', s + 'Arm': s + 'Arm', s + 'ForeArm': s + 'ForeArm', s + 'Hand': s + 'Hand',
                  s + 'HandMiddle1': s + 'HandMiddle1', s + 'UpLeg': s + 'Leg', s + 'Leg': s + 'Shin', s + 'Foot': s + 'Foot',
                  s + 'ToeBase': s + 'ToeBase', s + 'Toe_End': s + 'ToeEnd'})
DEFAULT_TOKENS = [(7, 8), (9, 10), (11, 12), (13, 14)]


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def arc(a, b):
    """The shortest turn taking direction a onto b (3x3)."""
    a, b = unit(a), unit(b)
    v = np.cross(a, b); c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        if c > 0: return np.eye(3)
        p = unit(np.cross(a, [1, 0, 0] if abs(a[0]) < 0.9 else [0, 1, 0]))
        return Rot.from_rotvec(p * math.pi).as_matrix()
    return Rot.from_rotvec(unit(v) * math.atan2(np.linalg.norm(v), c)).as_matrix()


class Soma:
    def __init__(self):
        self.sk = load_skeleton_from_usd(get_asset_file('human', 'soma_base_skel_minimal_no_root.usd'), SOMA_SKELETON_PRIM_PATH)
        self.names = list(self.sk.joint_names)
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.par = [self.sk.joint_parent(i) for i in range(len(self.names))]
        self.loc = self.sk.reference_local_transforms.numpy().astype(np.float64)  # [J, 7]: t xyz, q xyzw
        self.lrot = [Rot.from_quat(self.loc[i][3:7]).as_matrix() for i in range(len(self.names))]
        self.W, self.P = self.fk([self.lrot[i] for i in range(len(self.names))], self.loc[0][:3])

    def fk(self, lrots, root_pos):
        W = [None] * len(self.names); P = [None] * len(self.names)
        for i in range(len(self.names)):
            p = self.par[i]
            if p < 0: W[i] = lrots[i]; P[i] = np.array(root_pos, dtype=np.float64)
            else: W[i] = W[p] @ lrots[i]; P[i] = P[p] + W[p] @ self.loc[i][:3]
        return W, P


class Retarget:
    """Mixamo bone turns (Blender axes) <-> SOMA world turns, through each bone's rest alignment."""
    def __init__(self, soma, mix_rest):
        self.s = soma
        self.RM = {b: C @ np.array(r['rot']) @ C.T for b, r in mix_rest.items()}  # Mixamo rest turns, SOMA axes
        hM = {b: C @ np.array(r['head']) for b, r in mix_rest.items()}
        self.A = {}
        for sj, mb, sc, mc in MAP:
            if mb not in hM or mc not in hM: continue
            dS = soma.P[soma.idx[sc]] - soma.P[soma.idx[sj]]
            dM = hM[mc] - hM[mb]
            self.A[sj] = arc(dS, dM)
        self.ratio = soma.P[soma.idx['Hips']][1] / hM['Hips'][1]
        self.mix_rest = mix_rest

    def to_soma(self, rots_b, hips_b):
        """one Mixamo frame -> SOMA world turns (all joints) and the hips' place (SOMA axes)."""
        s = self.s
        D = {}
        for sj, mb, _, _ in MAP:
            if sj in self.A and mb in rots_b:
                D[sj] = C @ np.array(rots_b[mb]) @ C.T @ self.RM[mb].T
        W = [None] * len(s.names)
        for i, n in enumerate(s.names):
            p = s.par[i]
            if n in D: W[i] = D[n] @ self.A[n] @ s.W[i]
            elif p < 0: W[i] = s.W[i]
            else: W[i] = W[p] @ s.lrot[i]  # (unmapped: its rest turn under its parent)
        return W, C @ np.array(hips_b) * self.ratio

    def to_mixamo(self, W, P):
        """SOMA world turns + joint places -> Mixamo bone turns and heads (Blender axes, Mixamo's size)."""
        s = self.s
        rots, heads = {}, {}
        for sj, mb, _, _ in MAP:
            if sj not in self.A: continue
            Ds = W[s.idx[sj]] @ (self.A[sj] @ s.W[s.idx[sj]]).T
            rots[mb] = (C.T @ Ds @ self.RM[mb] @ C).round(6).tolist()
        for mb, sj in HEADS.items():
            heads[mb] = (C.T @ (P[s.idx[sj]] / self.ratio)).round(6).tolist()
        return rots, heads


def locals_of(soma, W, root_pos):
    """world turns -> a pose of local transforms [J, 7] (warp: p xyz, q xyzw)."""
    out = np.array(soma.loc)
    for i in range(len(soma.names)):
        p = soma.par[i]
        R = W[i] if p < 0 else W[p].T @ W[i]
        out[i][3:7] = Rot.from_matrix(R).as_quat()
        if p < 0: out[i][:3] = root_pos
    return out


def worlds_of(soma, pose):
    lr = [Rot.from_quat(pose[i][3:7]).as_matrix() for i in range(len(soma.names))]
    return soma.fk(lr, pose[0][:3])


def yaw_of(soma, W):
    f = W[0] @ soma.W[0].T @ np.array([0, 0, 1.0])  # (the hips' turn against SOMA's rest, applied to its forward)
    return math.atan2(f[0], f[2])


def frame_axes(yaw):
    """the body's left, up and forward in SOMA space for a heading (yaw 0 = +Z, + turns to the left)."""
    fwd = np.array([math.sin(yaw), 0, math.cos(yaw)])
    up = np.array([0, 1.0, 0])
    left = np.cross(up, fwd)
    return left, up, fwd


def two_bone(S, T, l1, l2, pole):
    d = T - S; L = np.linalg.norm(d)
    L = min(max(L, abs(l1 - l2) + 1e-4), l1 + l2 - 1e-4)
    u = unit(d)
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    pv = pole - S; pv = unit(pv - np.dot(pv, u) * u)
    E = S + u * a + pv * h
    return E, S + u * L


class Pose:
    """one pose as SOMA world turns + hips place, editable."""
    def __init__(self, soma, W, hips):
        self.s, self.W, self.hips = soma, [w.copy() for w in W], np.array(hips, dtype=np.float64)

    def copy(self): return Pose(self.s, self.W, self.hips)

    def subtree(self, j):
        out = [j]
        for i in range(len(self.s.names)):
            if i not in out and self.s.par[i] in out: out.append(i)
        return out

    def rotate(self, joint, R):
        """turn a joint and everything below it by world turn R about the joint."""
        s = self.s
        for i in self.subtree(s.idx[joint]):
            self.W[i] = R @ self.W[i]

    def places(self):
        s = self.s
        return s.fk([self.W[i] if s.par[i] < 0 else self.W[s.par[i]].T @ self.W[i] for i in range(len(s.names))], self.hips)[1]

    def set_bone_dir(self, joint, child, d):
        """turn one joint (its children keep their world turns) so its bone points along d."""
        s = self.s
        P = self.places()
        cur = P[s.idx[child]] - P[s.idx[joint]]
        R = arc(cur, d)
        i = s.idx[joint]
        keep = {k: self.W[k].copy() for k in self.subtree(i) if k != i}
        self.W[i] = R @ self.W[i]
        for k in self.subtree(s.idx[child]):
            self.W[k] = R @ keep[k] if k in keep else self.W[k]

    def place(self, ground, yaw):
        """move the pose so its feet's ground point is at ground and it heads yaw."""
        cur = yaw_of(self.s, self.W)
        R = Rot.from_rotvec([0, yaw - cur, 0]).as_matrix()
        g = np.array([self.hips[0], 0, self.hips[2]])
        self.hips = np.array([ground[0], 0, ground[2]]) + R @ (self.hips - g)
        self.W = [R @ w for w in self.W]

    def edit(self, e):
        s = self.s
        left, up, fwd = frame_axes(getattr(self, 'frame_yaw', None) if getattr(self, 'frame_yaw', None) is not None else yaw_of(s, self.W))
        ground = np.array([self.hips[0], 0, self.hips[2]])
        body = lambda v: ground + left * v[0] + up * v[1] + fwd * v[2]
        bdir = lambda v: unit(left * v[0] + up * v[1] + fwd * v[2])
        if 'joint' in e:
            R = (Rot.from_rotvec(up * math.radians(e.get('yaw', 0))) * Rot.from_rotvec(left * math.radians(e.get('pitch', 0)))
                 * Rot.from_rotvec(fwd * math.radians(e.get('roll', 0)))).as_matrix()
            self.rotate(e['joint'], R)
        elif 'reach' in e:
            side = e['reach']
            P = self.places()
            S, El, H = P[s.idx[side + 'Arm']], P[s.idx[side + 'ForeArm']], P[s.idx[side + 'Hand']]
            l1, l2 = np.linalg.norm(El - S), np.linalg.norm(H - El)
            E, T = two_bone(S, body(e['to']), l1, l2, body(e.get('pole', [0, 0.9, -0.5])))
            self.set_bone_dir(side + 'Arm', side + 'ForeArm', E - S)
            self.set_bone_dir(side + 'ForeArm', side + 'Hand', T - E)
        elif 'point' in e:
            side = e['point']
            d = bdir(e['dir'])
            self.set_bone_dir(side + 'Arm', side + 'ForeArm', d)
            self.set_bone_dir(side + 'ForeArm', side + 'Hand', d)


def load_clip(clips, name):
    return json.load(open(os.path.join(clips, name + '.json')))


def clip_pose(rt, clip, t):
    fr = clip['frames'][min(len(clip['frames']) - 1, max(0, int(round(t * clip['fps']))))]
    W, hips = rt.to_soma(fr['rot'], fr['head']['Hips'])
    return Pose(rt.s, W, hips)


def main():
    recipe_path, clips, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    only = sys.argv[4] if len(sys.argv) > 4 else None
    book = json.load(open(recipe_path))
    os.makedirs(out_dir, exist_ok=True)
    wp.init(); wp.set_device('cuda:0')
    soma = Soma()
    # (each clip retargets from its own rest: Mixamo's downloads may come on different characters; the clip out uses the
    # first recipe's context clip's rest)
    rts = {}
    def rt_of(name, d):
        if name not in rts: rts[name] = Retarget(soma, d['rest'])
        return rts[name]
    any_name = next(iter(book.values()))['context']['clip']
    any_clip = load_clip(clips, any_name)
    rt = rt_of(any_name, any_clip)
    report = {}
    with MotionBricksSOMAEngine(SOMA_N1_FP32_ONNX_PATH) as engine, wp.ScopedStream(engine.stream):
        context = engine.create_input(soma.sk); target = engine.create_input(soma.sk); output = engine.create_output(soma.sk)
        for name, rc in book.items():
            if only and name != only: continue
            cl = load_clip(clips, rc['context']['clip'])
            t_end = rc['context']['at']
            ctx = []
            for k in range(4):
                p = clip_pose(rt_of(rc['context']['clip'], cl), cl, t_end - (3 - k) / FPS)
                ctx.append(p)
            # (the context's last pose's ground point at the origin; its clip faces +Z as Mixamo's in-place clips do. the
            # heading the recipe works in is the CLIP's facing, not the hips': a slash twists the hips 100 degrees and more)
            g0 = ctx[-1].hips.copy()
            for p in ctx:
                p.hips = p.hips - np.array([g0[0], 0, g0[2]])
            for take in range(4):
                frames_W, cuts, toks = [], [], []
                cposes = [locals_of(soma, p.W, p.hips) for p in ctx]
                for k, p in enumerate(ctx[:-1]):  # (the context's own first frames lead the clip)
                    frames_W.append(cposes[k])
                heading = 0.0  # (the clip frame's facing, + to the left)
                for step in rc['targets']:
                    last = cposes[-1]
                    Wl, Pl = worlds_of(soma, last)
                    here, yaw = np.array([Pl[0][0], 0, Pl[0][2]]), heading
                    left, up, fwd = frame_axes(yaw)
                    mv = step.get('move', [0, 0]); turn = math.radians(step.get('turn', 0))
                    spot = here + fwd * mv[0] + left * mv[1]
                    heading = yaw + turn
                    tp = []
                    if step.get('clip') == 'same':
                        tp = [Pose(soma, Wl, Pl[0])]
                    else:
                        tc = load_clip(clips, step['clip'])
                        n = step.get('poses', 1)
                        tp = [clip_pose(rt_of(step['clip'], tc), tc, step['at'] + k / FPS) for k in range(n)]
                    first_yaw = 0.0 if step.get('clip') != 'same' else yaw + turn  # (a clip's poses keep their own twist)
                    out_t = []
                    carry = step.get('carry', 0.0)  # (m/s: the target poses move on at this speed, so it arrives running)
                    hfwd = frame_axes(yaw + turn)[2]
                    for k, p in enumerate(tp):
                        # (every target pose keeps its place against the first: the clip's own small steps)
                        q = p.copy()
                        rel = Rot.from_rotvec([0, (yaw + turn) - first_yaw, 0]).as_matrix()
                        g = np.array([tp[0].hips[0], 0, tp[0].hips[2]])
                        q.hips = spot + rel @ (p.hips - g) + hfwd * (carry * k / FPS); q.hips[1] = p.hips[1]
                        q.W = [rel @ w for w in p.W]
                        q.frame_yaw = yaw + turn
                        for e in step.get('edit', []): q.edit(e)
                        out_t.append(locals_of(soma, q.W, q.hips))
                    tk = tuple(step.get('tokens', DEFAULT_TOKENS)[take])
                    context.update_from_poses(wp.array(np.array(cposes, dtype=np.float32), dtype=wp.transform), stream=engine.stream)
                    target.update_from_poses(wp.array(np.array(out_t, dtype=np.float32), dtype=wp.transform), stream=engine.stream)
                    engine.generate_animation(context, target, output, config=MotionBricksInferenceConfig(allowed_token_counts=tk))
                    engine.synchronize()
                    nf = output.num_frames
                    gen = output.poses[:nf].numpy().astype(np.float64)
                    cuts.append(len(frames_W)); toks.append(int((nf + 6) // 4))
                    hold = step.get('hold', 0)
                    for f in gen: frames_W.append(f)
                    for _ in range(int(hold * FPS)): frames_W.append(gen[-1])
                    cposes = [gen[i] for i in range(nf - 4, nf)] if hold == 0 else [gen[-1]] * 4
                # out, in mixamo_rot_sample.py's shape
                fr_out = []
                for i, pose in enumerate(frames_W):
                    W, P = worlds_of(soma, pose)
                    rots, heads = rt.to_mixamo(W, P)
                    fr_out.append({'f': i, 'rot': rots, 'head': heads})
                doc = {'src': '%s take %d (MotionBricks)' % (name, take + 1), 'fps': FPS, 'f0': 0, 'f1': len(fr_out) - 1,
                       'bones': [b for b in any_clip['bones'] if b in fr_out[0]['rot'] or b in fr_out[0]['head']],
                       'rest': any_clip['rest'], 'frames': fr_out, 'cuts': cuts, 'tokens': toks, 'recipe': rc}
                path = os.path.join(out_dir, '%s_t%d.json' % (name, take + 1))
                json.dump(doc, open(path, 'w'))
                report.setdefault(name, []).append({'take': take + 1, 'frames': len(fr_out), 'seconds': round(len(fr_out) / FPS, 2),
                                                    'cuts': cuts, 'tokens': toks})
                print('%s take %d: %d frames (%.2f s), cuts %s, tokens %s' % (name, take + 1, len(fr_out), len(fr_out) / FPS, cuts, toks))
    json.dump(report, open(os.path.join(out_dir, 'report.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
