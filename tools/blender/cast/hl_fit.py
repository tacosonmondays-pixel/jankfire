# MADAM CHAIR's skeleton fitted to the owner's Tripo model: reads the Mixamo bones that came with the Tripo glb (its
# rest pose is an A-pose), scales and turns them like rebuild_hat_lord_tripo.py does, and prints the numbers that go
# into public/js/story/hatlook.js (HATLORD, FIT) and tools/blender/cast/hl_clips.py (the stance). Run it once when the
# source changes:  blender52 -b --python tools/blender/cast/hl_fit.py
# Joint frames follow the game's conventions (three.js XYZ euler): a limb hangs along its joint's -y, x = across (the
# elbow / knee / knuckle hinge), +z = back (for a hand: the palm side).
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
import hltripo as H

HIP = 0.92


def game(p):
    b = H.t2b(p); return np.array([b.x, b.z, -b.y])


def bones():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=H.SRC)
    A = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    out = {}
    for b in A.data.bones:
        out[b.name.split(':')[-1]] = (game(A.matrix_world @ b.head_local), game(A.matrix_world @ b.tail_local))
    return out


def unit(v): v = np.asarray(v, float); return v / np.linalg.norm(v)


def euler_xyz(R):
    """three.js Euler.setFromRotationMatrix, order XYZ"""
    m13 = R[0, 2]; b = math.asin(max(-1, min(1, m13)))
    if abs(m13) < 0.9999999: a = math.atan2(-R[1, 2], R[2, 2]); c = math.atan2(-R[0, 1], R[0, 0])
    else: a = math.atan2(R[2, 1], R[1, 1]); c = 0.0
    return np.array([a, b, c])


def rot_xyz(e):
    a, b, c = e
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rx @ Ry @ Rz


def frame(down, zref):
    """a rotation whose -y is `down` and whose z is as close to zref as it can be"""
    y = -unit(down); z = np.asarray(zref, float); z = unit(z - y * z.dot(y)); x = np.cross(y, z)
    return np.stack([x, y, z], axis=1)


def fit():
    B = bones(); r = lambda v: [round(float(x), 4) for x in v]
    out = {}
    hipL, hipR = B['LeftUpLeg'][0], B['RightUpLeg'][0]
    hipY = (hipL[1] + hipR[1]) / 2; legS = hipY / HIP; hipW = (abs(hipL[0]) + abs(hipR[0])) / 2
    out['legS'] = round(legS, 4); out['hipW'] = round(hipW, 4)
    spineY = hipY + 0.06
    for side, s, sx in (('L', 'Left', -1), ('R', 'Right', 1)):
        hip = np.array([sx * hipW, hipY, 0.0]); knee = B[s + 'Leg'][0]; ankle = B[s + 'Foot'][0]
        R = frame(knee - hip, [0, 0, 1]); out['leg' + side] = r(euler_xyz(R))
        out['thigh' + side] = round(float(np.linalg.norm(knee - hip)), 4)
        out['shin' + side] = round(float(np.linalg.norm(ankle - knee)), 4)
        # the arm: shoulder, elbow, wrist, the hand to the middle knuckle, the palm side from the way the fingers curl
        sh, el, wr = B[s + 'Arm'][0], B[s + 'ForeArm'][0], B[s + 'Hand'][0]
        mid1, mid2 = B[s + 'HandMiddle1'][0], B[s + 'HandMiddle2'][0]; tip = B[s + 'HandMiddle4'][1]
        Ra = frame(el - sh, [0, 0, 1]); ea = euler_xyz(Ra)
        Rf_w = frame(wr - el, Ra[:, 2]); ef = euler_xyz(Ra.T @ Rf_w)
        d1 = unit(mid2 - mid1); d2 = tip - mid2; palm = unit(d2 - d1 * d2.dot(d1))
        Rh_w = frame(mid1 - wr, Rf_w[:, 2]); eh = euler_xyz(Rf_w.T @ Rh_w)   # (z kept near the forearm's: no twist at the wrist)
        arm = 'arm' if side == 'R' else 'armL'
        out[arm] = dict(at=r(sh), rest=r(ea), upper=round(float(np.linalg.norm(el - sh)), 4))
        out['fore' + side] = dict(at=r(el), rest=r(ef), fore=round(float(np.linalg.norm(wr - el)), 4))
        out['hand' + side] = dict(at=r(wr), rest=r(eh), toKnuckle=round(float(np.linalg.norm(mid1 - wr)), 4), palm=r(Rh_w.T @ palm))
        # fingers in the hand's frame: idx = the index finger, fin = the other three together, thumb. b = the second joint
        def local(p, Rw=Rh_w, o=wr): return Rw.T @ (p - o)
        fing = {}
        for k, nm in (('idx', 'Index'), ('fin', 'Middle')):
            j1, j3, j4e = B[s + 'Hand' + nm + '1'][0], B[s + 'Hand' + nm + '3'][0], B[s + 'Hand' + nm + '4'][1]
            R1w = frame(j3 - j1, palm); e1 = euler_xyz(Rh_w.T @ R1w)
            R2w = frame(j4e - j3, R1w[:, 2]); e2 = euler_xyz(R1w.T @ R2w)
            fing[k] = dict(p=r(local(j1)), rest=r(e1), len=round(float(np.linalg.norm(j3 - j1)), 4))
            fing[k + 'b'] = dict(p=r(R1w.T @ (j3 - j1)), rest=r(e2), len=round(float(np.linalg.norm(j4e - j3)), 4))
        t1, t4 = B[s + 'HandThumb1'][0], B[s + 'HandThumb4'][1]
        Rt = frame(t4 - t1, palm); fing['thumb'] = dict(p=r(local(t1)), rest=r(euler_xyz(Rh_w.T @ Rt)), len=round(float(np.linalg.norm(t4 - t1)), 4))
        out['fingers' + side] = fing
    shL, shR = out['armL']['at'], out['arm']['at']
    out['shW'] = round((abs(shL[0]) + abs(shR[0])) / 2, 4); shY = (shL[1] + shR[1]) / 2; out['shZ'] = round((shL[2] + shR[2]) / 2, 4)
    out['torsoH'] = round((shY - spineY) / 0.85, 4)
    neck = B['Neck'][0]; out['neckAt'] = r(neck); out['neck'] = round(float(neck[1] - spineY - out['torsoH']), 4)
    out['upper'] = round((out['arm']['upper'] + out['armL']['upper']) / 2, 4)
    out['fore'] = round((out['foreR']['fore'] + out['foreL']['fore']) / 2 - 0.02, 4)
    out['spineY'] = round(spineY, 4)
    return out


if __name__ == '__main__':
    F = fit()
    print('JF_FIT ' + json.dumps(F))
