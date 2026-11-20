"""Mixamo <-> SOMA retargeting and pose edits, numpy only (19 Nov 2026: MotionBricks and Kimodo share SOMA).

A SOMA body here is joint names, parents, rest world turns and rest joint places (SOMA model space: Y up, the body
faces +Z, its left on +X, metres). MotionBricks' USD skeleton rests with its own bone frames; Kimodo's somaskel77
rests in a T-pose with every turn the identity. Mixamo clips come from mixamo_rot_sample.py (Blender axes: Z up, the
body faces -Y): (x, y, z) -> SOMA (x, z, -y).

  retarget: a Mixamo bone's turn against its rest, D = R(t) R(rest)^-1, goes on its SOMA joint on top of a small rest
            alignment A (SOMA's bone direction turned onto Mixamo's): W = D A Wsoma(rest); the hips move by the
            hip-height ratio; unmapped joints (fingers, jaw, eyes, Neck2) keep their rest turn under their parent.
  back:     W -> D = W (A Wsoma(rest))^-1 -> the Mixamo bone's world turn D R(rest), and SOMA joint places as Mixamo
            heads (Blender axes, Mixamo's size), the shape mixamo_r15.py and mb_sheet.py read.
  edits:    turn a joint (and all below it) about the body's up / left / forward; reach a hand to a spot (two-bone IK
            with a pole); point a whole arm along a direction.
"""
import math
import numpy as np
from scipy.spatial.transform import Rotation as Rot

C = np.array([[1.0, 0, 0], [0, 0, 1.0], [0, -1.0, 0]])  # Blender -> SOMA
MAP = [('Hips', 'Hips', 'Spine1', 'Spine'), ('Spine1', 'Spine', 'Spine2', 'Spine1'), ('Spine2', 'Spine1', 'Chest', 'Spine2'),
       ('Chest', 'Spine2', 'Neck1', 'Neck'), ('Neck1', 'Neck', 'Head', 'Head'), ('Head', 'Head', 'HeadEnd', 'HeadTop_End')]
for _s in ('Left', 'Right'):
    MAP += [(_s + 'Shoulder', _s + 'Shoulder', _s + 'Arm', _s + 'Arm'), (_s + 'Arm', _s + 'Arm', _s + 'ForeArm', _s + 'ForeArm'),
            (_s + 'ForeArm', _s + 'ForeArm', _s + 'Hand', _s + 'Hand'), (_s + 'Hand', _s + 'Hand', _s + 'HandMiddle1', _s + 'HandMiddle1'),
            (_s + 'Leg', _s + 'UpLeg', _s + 'Shin', _s + 'Leg'), (_s + 'Shin', _s + 'Leg', _s + 'Foot', _s + 'Foot'),
            (_s + 'Foot', _s + 'Foot', _s + 'ToeBase', _s + 'ToeBase'), (_s + 'ToeBase', _s + 'ToeBase', _s + 'ToeEnd', _s + 'Toe_End')]
HEADS = {'Hips': 'Hips', 'Spine': 'Spine1', 'Spine1': 'Spine2', 'Spine2': 'Chest', 'Neck': 'Neck1', 'Head': 'Head',
         'HeadTop_End': 'HeadEnd'}
for _s in ('Left', 'Right'):
    HEADS.update({_s + 'Shoulder': _s + 'Shoulder', _s + 'Arm': _s + 'Arm', _s + 'ForeArm': _s + 'ForeArm', _s + 'Hand': _s + 'Hand',
                  _s + 'HandMiddle1': _s + 'HandMiddle1', _s + 'UpLeg': _s + 'Leg', _s + 'Leg': _s + 'Shin', _s + 'Foot': _s + 'Foot',
                  _s + 'ToeBase': _s + 'ToeBase', _s + 'Toe_End': _s + 'ToeEnd'})


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def arc(a, b):
    """The shortest turn taking direction a onto b (3x3)."""
    a, b = unit(np.asarray(a, float)), unit(np.asarray(b, float))
    v = np.cross(a, b); c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        if c > 0: return np.eye(3)
        p = unit(np.cross(a, [1, 0, 0] if abs(a[0]) < 0.9 else [0, 1, 0]))
        return Rot.from_rotvec(p * math.pi).as_matrix()
    return Rot.from_rotvec(unit(v) * math.atan2(np.linalg.norm(v), c)).as_matrix()


class Body:
    """A SOMA skeleton: names, parents (index, -1 = root), rest world turns W and places P, local rest offsets."""
    def __init__(self, names, parents, rest_W, rest_P):
        self.names = list(names)
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.par = list(parents)
        self.W = [np.asarray(w, float) for w in rest_W]
        self.P = [np.asarray(p, float) for p in rest_P]
        # local rest: turn under the parent and offset in the parent's frame
        self.lrot = [self.W[i] if self.par[i] < 0 else self.W[self.par[i]].T @ self.W[i] for i in range(len(self.names))]
        self.off = [self.P[i] if self.par[i] < 0 else self.W[self.par[i]].T @ (self.P[i] - self.P[self.par[i]]) for i in range(len(self.names))]
        # the hips over the floor (the lowest toe end at rest)
        feet = [self.P[self.idx[n]][1] for n in ('LeftToeEnd', 'RightToeEnd', 'LeftToeBase', 'RightToeBase') if n in self.idx]
        self.hip_height = self.P[self.idx['Hips']][1] - min(feet)

    def fk(self, W_or_local, root, local=False):
        """world turns (or local turns) + root place -> world turns, places"""
        n = len(self.names)
        W = [None] * n; P = [None] * n
        for i in range(n):
            p = self.par[i]
            if local:
                W[i] = W_or_local[i] if p < 0 else W[p] @ W_or_local[i]
            else:
                W[i] = W_or_local[i]
            P[i] = np.asarray(root, float) if p < 0 else P[p] + W[p] @ self.off[i]
        return W, P

    def locals(self, W):
        return [W[i] if self.par[i] < 0 else W[self.par[i]].T @ W[i] for i in range(len(self.names))]


class Retarget:
    def __init__(self, body, mix_rest, floor_hips=None):
        self.b = body
        self.RM = {k: C @ np.array(r['rot']) @ C.T for k, r in mix_rest.items()}
        hM = {k: C @ np.array(r['head']) for k, r in mix_rest.items()}
        self.A = {}
        for sj, mb, sc, mc in MAP:
            if sj in body.idx and sc in body.idx and mb in hM and mc in hM:
                self.A[sj] = arc(body.P[body.idx[sc]] - body.P[body.idx[sj]], hM[mc] - hM[mb])
        self.ratio = body.hip_height / hM['Hips'][1]
        self.mix_hips_y = hM['Hips'][1]

    def to_soma(self, rots_b, hips_b):
        """one Mixamo frame (bone world turns, hips head; Blender axes) -> SOMA world turns + hips place (floor y = 0)"""
        b = self.b
        D = {sj: C @ np.array(rots_b[mb]) @ C.T @ self.RM[mb].T for sj, mb, _, _ in MAP if sj in self.A and mb in rots_b}
        W = [None] * len(b.names)
        for i, n in enumerate(b.names):
            p = b.par[i]
            if n in D: W[i] = D[n] @ self.A[n] @ b.W[i]
            elif p < 0: W[i] = b.W[i]
            else: W[i] = W[p] @ b.lrot[i]
        return W, C @ np.array(hips_b) * self.ratio

    def to_mixamo(self, W, P):
        """SOMA world turns + joint places (floor y = 0) -> Mixamo bone turns and heads (Blender axes, Mixamo's size)"""
        b = self.b
        rots, heads = {}, {}
        for sj, mb, _, _ in MAP:
            if sj not in self.A: continue
            Ds = W[b.idx[sj]] @ (self.A[sj] @ b.W[b.idx[sj]]).T
            rots[mb] = (C.T @ Ds @ self.RM[mb] @ C).round(6).tolist()
        for mb, sj in HEADS.items():
            if sj in b.idx:
                heads[mb] = (C.T @ (np.asarray(P[b.idx[sj]]) / self.ratio)).round(6).tolist()
        return rots, heads


def yaw_of(body, W):
    f = W[body.idx['Hips']] @ body.W[body.idx['Hips']].T @ np.array([0, 0, 1.0])
    return math.atan2(f[0], f[2])


def frame_axes(yaw):
    """the body's left, up and forward for a heading (yaw 0 = +Z, + turns to the left)"""
    fwd = np.array([math.sin(yaw), 0, math.cos(yaw)])
    up = np.array([0, 1.0, 0])
    return np.cross(up, fwd), up, fwd


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
    """one pose: SOMA world turns + hips place, editable; frame_yaw = the facing the edits use (else the hips')"""
    def __init__(self, body, W, hips, frame_yaw=None):
        self.b, self.W, self.hips, self.frame_yaw = body, [w.copy() for w in W], np.array(hips, float), frame_yaw

    def copy(self): return Pose(self.b, self.W, self.hips, self.frame_yaw)

    def subtree(self, j):
        out = [j]
        for i in range(len(self.b.names)):
            if i not in out and self.b.par[i] in out: out.append(i)
        return out

    def places(self):
        return self.b.fk(self.W, self.hips)[1]

    def rotate(self, joint, R):
        for i in self.subtree(self.b.idx[joint]):
            self.W[i] = R @ self.W[i]

    def set_bone_dir(self, joint, child, d):
        b = self.b
        P = self.places()
        R = arc(P[b.idx[child]] - P[b.idx[joint]], d)
        for k in self.subtree(b.idx[joint]):
            self.W[k] = R @ self.W[k]

    def place(self, ground, yaw):
        cur = self.frame_yaw if self.frame_yaw is not None else yaw_of(self.b, self.W)
        R = Rot.from_rotvec([0, yaw - cur, 0]).as_matrix()
        g = np.array([self.hips[0], 0, self.hips[2]])
        self.hips = np.array([ground[0], 0, ground[2]]) + R @ (self.hips - g)
        self.W = [R @ w for w in self.W]
        self.frame_yaw = yaw

    def edit(self, e):
        b = self.b
        yaw = self.frame_yaw if self.frame_yaw is not None else yaw_of(b, self.W)
        left, up, fwd = frame_axes(yaw)
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
            S, El, H = P[b.idx[side + 'Arm']], P[b.idx[side + 'ForeArm']], P[b.idx[side + 'Hand']]
            E, T = two_bone(S, body(e['to']), np.linalg.norm(El - S), np.linalg.norm(H - El), body(e.get('pole', [0, 0.9, -0.5])))
            self.set_bone_dir(side + 'Arm', side + 'ForeArm', E - S)
            self.set_bone_dir(side + 'ForeArm', side + 'Hand', T - E)
        elif 'point' in e:
            side = e['point']
            d = bdir(e['dir'])
            self.set_bone_dir(side + 'Arm', side + 'ForeArm', d)
            self.set_bone_dir(side + 'ForeArm', side + 'Hand', d)


def clip_pose(rt, clip, t, frame_yaw=0.0):
    """a Mixamo clip's pose at t seconds (its facing frame is +Z: Mixamo's clips face -Y in Blender)"""
    fr = clip['frames'][min(len(clip['frames']) - 1, max(0, int(round(t * clip['fps']))))]
    W, hips = rt.to_soma(fr['rot'], fr['head']['Hips'])
    return Pose(rt.b, W, hips, frame_yaw)
