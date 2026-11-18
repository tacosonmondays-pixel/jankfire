# shared maths for the scythe's mocap attacks (18 Nov 2026): the JSON from tools/blender/mocap_sample.py (Roblox axes,
# metres, the body facing -Z), the scythe held rigidly in the right fist, the strike's fastest moment, a time warp
import json, math
import numpy as np

def load(path):
    d = json.load(open(path))
    fr = d['frames']
    pos = {b: np.array([f['pos'][b] for f in fr]) for b in fr[0]['pos']}
    rot = {b: np.array([f['rot'][b] for f in fr]) for b in fr[0]['rot']}
    return d, pos, rot

HAFT = 1.22   # grip -> the blade's root along the haft (the kit scythe, file metres)
HEEL = 0.2    # grip -> the heel
BLADE = 0.63  # the blade's reach out from the haft

def grip_frames(pos, rot, contact=None):
    """per frame: the grip point g, the haft's direction d (grip -> blade) and the blade's direction b (out from the
    haft), all world. the haft runs through the right fist along the hand's knuckle line (its -x axis); the blade's
    turn about the haft is fixed in the hand, chosen so the blade leads the cut at the hit (contact: the fastest
    moment with the blade out in front at about chest height)"""
    n = len(pos['RightHand'])
    R = rot['RightHand']                      # (n, 3, 3), columns = the hand's axes
    hx, hy = R[:, :, 0], R[:, :, 1]
    g = pos['RightHand'] + 0.085 * hy          # the fist's middle: a little along toward the fingers
    # the haft runs along the fist's -x: in all seven two-handed Mixamo clips measured (18 Nov) the left hand sits on
    # the right hand's +x, so the blade is beyond the right fist that way; one-handed clips use the same rig convention
    d = -hx
    tip = g + d * HAFT
    v = np.gradient(tip, axis=0)
    speed = np.linalg.norm(v, axis=1)
    if contact is None:
        # the hit: the fastest moment while the blade is out in front of the body (the body faces -Z), not the top of
        # the wind-up behind the head
        ahead = pos['Hips'][:, 2] - tip[:, 2]
        chest = (pos['Spine2'][:, 1] + pos['Hips'][:, 1]) / 2
        level = np.exp(-((tip[:, 1] - chest) / 0.45) ** 2)  # (and at about chest height: where a body is hit)
        contact = int(np.argmax(speed * np.clip(ahead / 0.6, 0, 1) * (0.25 + level)))
    vc = v[contact] - d[contact] * np.dot(v[contact], d[contact])
    if np.linalg.norm(vc) < 1e-6: vc = R[contact][:, 2]
    vc /= np.linalg.norm(vc)
    local = R[contact].T @ vc                  # the blade's way in the hand's own axes
    b = np.einsum('nij,j->ni', R, local)
    b -= d * np.sum(b * d, axis=1)[:, None]
    b /= np.linalg.norm(b, axis=1)[:, None]
    return g, d, b, speed, contact

def scythe_cf(g, d, b):
    """the kit scythe's frame (columns x, y, z; model -z = the haft toward the blade, model -x = the blade's way)"""
    x = -b; z = -d; y = np.cross(z, x)
    return np.stack([x, y, z], axis=-1), g

def warp(times, keys):
    """piecewise-linear time map: keys = [(src, dst), ...] sorted by src"""
    s = np.array([k[0] for k in keys]); t = np.array([k[1] for k in keys])
    return np.interp(times, s, t)
