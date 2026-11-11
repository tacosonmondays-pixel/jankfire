# MADAM CHAIR's skin weights and posing for rebuild_hat_lord_tripo.py. Weights are worked out from the bones the Tripo
# model came with (its Mixamo rig, for where each finger and limb runs) mapped onto OUR joints (hatlook.js), then
# blended across every joint over a width that suits it, smoothed over the mesh, cut to 4 bones a vertex.
# The poser is the game's own sum (the same as hatlord.js + three's SkinnedMesh): every vertex goes by
#   v' = sum_j w_j * Pose_j * Rest_j^-1 * v,  Rest = the joints' rest (joints.json mats), Pose = hl_clips.fk(pose)
# so the Blender clip strips show what the game draws.
import math, json
import numpy as np
from mathutils import Vector

STD = ('body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR')


def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if b != a else (1.0 if x >= b else 0.0)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------------------------------------ segments
def segments(B, J, gv):
    """bone segments (blender axes) labelled with our joints. B: Mixamo bone name -> (head, tail) in game coords,
    J: our joint -> rest position (blender axes). each: label, parent label, a (start), b (end), h (blend half width),
    first (this segment starts the label's joint: it blends back into the parent there)"""
    g = lambda p: gv(*p)
    S = []
    def seg(label, par, a, b, h, first=True): S.append(dict(label=label, par=par, a=Vector(a), b=Vector(b), h=h, first=first))
    seg('body', None, J['spine'] - Vector((0, 0, 0.16)), J['spine'], 0.0)
    seg('spine', 'body', J['spine'], J['neck'], 0.09)
    seg('neck', 'spine', J['neck'], J['head'], 0.045)
    seg('head', 'neck', J['head'], J['head'] + Vector((0, 0, 0.32)), 0.04)
    for s, side, arm, fore, hand in (('Left', 'L', 'armL', 'foreL', 'handL'), ('Right', 'R', 'arm', 'foreR', 'handR')):
        seg('spine', None, g(B[s + 'Shoulder'][0]), J[arm], 0.0, first=False)
        seg(arm, 'spine', J[arm], J[fore], 0.075)
        seg(fore, arm, J[fore], J[hand], 0.055)
        seg(hand, fore, J[hand], g(B[s + 'HandMiddle1'][0]), 0.035)
        for f, lab in (('Index', 'idx'), ('Middle', 'fin'), ('Ring', 'fin'), ('Pinky', 'fin')):
            p1, p2, p3, p4, tip = [g(B[s + 'Hand' + f + str(k)][0]) for k in (1, 2, 3, 4)] + [g(B[s + 'Hand' + f + '4'][1])]
            # (the hand reaches its knuckles: a finger's root is part of the palm)
            seg(lab + side, hand, p1, p2, 0.026); seg(lab + side, hand, p2, p3, 0.0, first=False)
            seg(lab + side + 'b', lab + side, p3, p4, 0.02); seg(lab + side + 'b', lab + side, p4, tip, 0.0, first=False)
        t = [g(B[s + 'HandThumb' + str(k)][0]) for k in (1, 2, 3, 4)] + [g(B[s + 'HandThumb4'][1])]
        seg('thumb' + side, hand, t[0], t[1], 0.025)
        for a, b in zip(t[1:], t[2:]): seg('thumb' + side, hand, a, b, 0.0, first=False)
        leg, knee = 'leg' + side, 'knee' + side
        seg(leg, 'body', J[leg], J[knee], 0.12)
        seg(knee, leg, J[knee], g(B[s + 'Foot'][0]), 0.095)
        seg(knee, leg, g(B[s + 'Foot'][0]), g(B[s + 'ToeBase'][0]), 0.0, first=False)
        seg(knee, leg, g(B[s + 'ToeBase'][0]), g(B[s + 'Toe_End'][1]), 0.0, first=False)
    return S


def _segdist(P, a, b):
    ab = b - a; L2 = max(1e-12, ab.dot(ab))
    t = np.clip(((P - a) @ ab) / L2, 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


REACH = (('arm', 0.1), ('fore', 0.075), ('hand', 0.07), ('thumb', 0.035), ('idx', 0.028), ('fin', 0.05), ('leg', 0.13), ('knee', 0.1), ('neck', 0.09), ('head', 0.16), ('spine', 0.3))


def reach(label):
    """how far from a limb's axis its own skin can be (the forward blend into a child is only for these)"""
    for k, r in REACH:
        if label.startswith(k): return r
    return 0.1


def body_weights(bm, S):
    """-> list of {joint: w} per vertex (bm.verts order)"""
    P = np.array([v.co[:] for v in bm.verts])
    A = [np.array(s['a'][:]) for s in S]; Bb = [np.array(s['b'][:]) for s in S]
    D = np.stack([_segdist(P, a, b) for a, b in zip(A, Bb)], 1)
    near = D.argmin(1)
    first = {s['label']: s for s in S if s['first'] and s['par']}
    kids = {}
    for s in S:
        if s['first'] and s['par']: kids.setdefault(s['par'], []).append(s)
    W = []
    for vi, k in enumerate(near):
        s = S[k]; L = s['label']; v = Vector(P[vi]); w = {L: 1.0}
        f = first.get(L)
        if f and f['h'] > 0:
            u = (f['b'] - f['a']).normalized(); t = (v - f['a']).dot(u)
            if t < f['h']:
                c = ss(-f['h'], f['h'], t); w = {L: c, f['par']: 1 - c}
        for c_ in kids.get(L, []):
            if (v - c_['a']).length > c_['h'] * 3 + 0.04: continue
            u = (c_['b'] - c_['a']).normalized(); t = (v - c_['a']).dot(u)
            if ((v - c_['a']) - u * t).length > reach(c_['label']): continue    # (only the limb itself, not the chest beside a shoulder)
            if t > -c_['h']:
                c = ss(-c_['h'], c_['h'], t)
                w = {kk: ww * (1 - c) for kk, ww in w.items()}; w[c_['label']] = w.get(c_['label'], 0) + c
        W.append(w)
    return W


def smooth(bm, W, iters=2, keep=0.5):
    nb = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
    for _ in range(iters):
        N = []
        for i, w in enumerate(W):
            if not nb[i]: N.append(w); continue
            acc = {}
            for j in nb[i]:
                for k, x in W[j].items(): acc[k] = acc.get(k, 0) + x / len(nb[i])
            out = {k: x * keep for k, x in w.items()}
            for k, x in acc.items(): out[k] = out.get(k, 0) + x * (1 - keep)
            N.append(out)
        W = N
    return W


def limit(W, n=4):
    out = []
    for w in W:
        top = sorted(((x, k) for k, x in w.items() if x > 1e-4), reverse=True)[:n]
        s = sum(x for x, _ in top) or 1.0
        out.append({k: x / s for x, k in top})
    return out


# ------------------------------------------------------------------------------------------------ poser
def mat4(e):
    """three.js column-major 16 -> numpy 4x4"""
    return np.array(e, float).reshape(4, 4).T


def fk_mats(fk_out):
    out = {}
    for n, (R, p, s) in fk_out.items():
        M = np.eye(4); M[:3, :3] = np.array(R) * s; M[:3, 3] = p; out[n] = M
    return out


def skin_mats(JD, fk_out):
    """joint -> Pose * Rest^-1 (game coords)"""
    PM = fk_mats(fk_out)
    return {n: PM[n] @ np.linalg.inv(mat4(JD['mats'][n])) for n in JD['order']}


def pose_points(Pg, W, SM):
    """Pg: N x 3 game coords at rest, W: list of {joint: w} -> N x 3 posed"""
    out = np.zeros_like(Pg); H4 = np.c_[Pg, np.ones(len(Pg))]
    joints = sorted({k for w in W for k in w})
    for j in joints:
        wj = np.array([w.get(j, 0.0) for w in W])
        m = wj > 0
        if m.any(): out[m] += wj[m, None] * (H4[m] @ SM[j].T)[:, :3]
    return out
