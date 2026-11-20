"""Kimodo trial (19 Nov 2026): NVIDIA's text-to-motion with our own pose pins, four takes per recipe, out as Mixamo-shape
JSON for tools/blender/mixamo_r15.py (R15 clips) and the sheets.

run (Kimodo's venv on D:, the repo on PYTHONPATH; source D:/SteamLibrary/AI/kimodo-env.sh first; README.md):
    python <repo>/tools/motionbricks/kimodo_gen.py <recipes.json> <clips dir> <out dir> [recipe] [--steps 100]

  * model: Kimodo-SOMA-RP-v1.2 only (NVIDIA Open Model License, commercial use OK). Never the SMPL-X one (R&D only).
    Its text encoder is Meta's gated Llama-3-8B-Instruct through McGill's LLM2Vec adapters; it runs on the CPU here
    (TEXT_ENCODER_DEVICE=cpu: the RTX 4080 has 16 GB).
  * post-processing (MotionCorrection, a C++ extension) needs the Windows SDK, which this PC doesn't have, so takes are
    raw model output: pins are followed closely, not exactly, and feet may slide a little.
  * Kimodo's somaskel77 rests in a T-pose with every turn the identity (Y up, faces +Z), so soma_retarget.py's Mixamo
    <-> SOMA mapping works on it as on MotionBricks' skeleton. Pins come from our vault Mixamo clips (sampled by
    mixamo_rot_sample.py into <clips dir>) or edits of them, placed at the canonical start (root XZ = 0, facing +Z).
  * a recipe:
      { "prompt": "A person ...", "duration": 3.5,
        "pins": [ { "type": "right-hand" | "left-hand" | "fullbody" | ..., "at": 2.4 (s),
                    "pose": { "clip": "06_sheathing_sword", "t": 1.27, "edit": [...], "move": [fwd, left] } } ],
        "loop": true }   (loop: a free pass, then each take again pinned to its own first pose at both ends)
  * out: <out>/<recipe>_t<k>.json (mixamo_rot_sample.py's shape) and <recipe>_t<k>.npz (Kimodo's own output).
"""
import json, math, os, sys
import numpy as np
import torch
from scipy.spatial.transform import Rotation as Rot

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soma_retarget as SR  # noqa: E402

from kimodo import load_model  # noqa: E402
from kimodo.constraints import load_constraints_lst  # noqa: E402
from kimodo.skeleton.definitions import SOMASkeleton77  # noqa: E402
from kimodo.tools import seed_everything  # noqa: E402

MODEL = 'Kimodo-SOMA-RP-v1.2'
SEEDS = [11, 23, 37, 51]


def kimodo_body():
    sk = SOMASkeleton77()
    names = list(sk.bone_order_names)
    parents = [names.index(sk.bone_parents[n]) if sk.bone_parents[n] else -1 for n in names]
    P = sk.neutral_joints.detach().cpu().numpy().astype(float)
    return SR.Body(names, parents, [np.eye(3)] * len(names), P)


def pin_dict(body, pose, kind, frame):
    """a Pose -> one Kimodo constraint dict (77-joint local axis-angle + root place)"""
    loc = body.locals(pose.W)
    aa = [Rot.from_matrix(m).as_rotvec().round(6).tolist() for m in loc]
    d = {'type': kind, 'frame_indices': [int(frame)], 'local_joints_rot': [aa],
         'root_positions': [np.asarray(pose.hips).round(5).tolist()]}
    return d


def build_pose(body, clips, rts, spec):
    c = spec['clip']
    if c not in clips:
        clips[c] = json.load(open(os.path.join(CLIPDIR, c + '.json')))
        rts[c] = SR.Retarget(body, clips[c]['rest'])
    p = SR.clip_pose(rts[c], clips[c], spec.get('t', 0.0), 0.0)
    # (the canonical start: hips over XZ = 0, the clip's own facing = +Z), then moved and edited
    mv = spec.get('move', [0, 0])
    p.hips = np.array([mv[1], p.hips[1], mv[0]])
    for e in spec.get('edit', []):
        p.edit(e)
    return p


def to_doc(body, rt, rest, name, k, out, i):
    W_all = out['global_rot_mats'][i]
    P_all = out['posed_joints'][i]
    frames = []
    for f in range(W_all.shape[0]):
        rots, heads = rt.to_mixamo([np.asarray(W_all[f][j], float) for j in range(len(body.names))],
                                   [np.asarray(P_all[f][j], float) for j in range(len(body.names))])
        frames.append({'f': f, 'rot': rots, 'head': heads})
    return {'src': '%s take %d (Kimodo)' % (name, k + 1), 'fps': FPS, 'f0': 0, 'f1': len(frames) - 1,
            'bones': list(frames[0]['rot'].keys()), 'rest': rest, 'frames': frames}


def main():
    global CLIPDIR, FPS
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    steps = int(sys.argv[sys.argv.index('--steps') + 1]) if '--steps' in sys.argv else 100
    if '--steps' in sys.argv: args.remove(str(steps))
    recipes_path, CLIPDIR, out_dir = args[0], args[1], args[2]
    only = args[3] if len(args) > 3 else None
    book = json.load(open(recipes_path))
    os.makedirs(out_dir, exist_ok=True)
    body = kimodo_body()
    clips, rts = {}, {}
    ref_name = book.get('_rest_clip', '06_sheathing_sword')
    clips[ref_name] = json.load(open(os.path.join(CLIPDIR, ref_name + '.json')))
    rts[ref_name] = rt_out = SR.Retarget(body, clips[ref_name]['rest'])
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    model = load_model(MODEL, device=device, default_family='Kimodo')
    FPS = float(model.fps)
    report = {}
    for name, rc in book.items():
        if name.startswith('_') or (only and name != only):
            continue
        n_frames = int(round(rc['duration'] * FPS))
        pins = []
        for pn in rc.get('pins', []):
            p = build_pose(body, clips, rts, pn['pose'])
            pins.append(pin_dict(body, p, pn['type'], min(n_frames - 1, int(round(pn['at'] * FPS)))))
        cons = load_constraints_lst(pins, model.skeleton) if pins else []
        seed_everything(SEEDS[0])
        out = model(rc['prompt'], n_frames, num_denoising_steps=steps, constraint_lst=cons, num_samples=4,
                    return_numpy=True, post_processing=False)
        takes = [{k: v[i] for k, v in out.items() if hasattr(v, 'shape') and v.shape[0] == 4} for i in range(4)]
        if rc.get('loop'):
            # each take again, pinned to its own first pose at both ends (same place, same facing): a loop
            looped = []
            for k, tk in enumerate(takes):
                loc = tk['local_rot_mats'][0]
                aa = [Rot.from_matrix(np.asarray(m, float)).as_rotvec().round(6).tolist() for m in loc]
                root = np.asarray(tk['posed_joints'][0][body.idx['Hips']], float).round(5).tolist()
                d = {'type': 'fullbody', 'frame_indices': [0, n_frames - 1], 'local_joints_rot': [aa, aa], 'root_positions': [root, root]}
                seed_everything(SEEDS[k])
                o2 = model(rc['prompt'], n_frames, num_denoising_steps=steps, constraint_lst=load_constraints_lst([d], model.skeleton),
                           num_samples=1, return_numpy=True, post_processing=False)
                looped.append({kk: v[0] for kk, v in o2.items() if hasattr(v, 'shape') and v.shape[0] == 1})
            takes = looped
        report[name] = []
        for k, tk in enumerate(takes):
            np.savez_compressed(os.path.join(out_dir, '%s_t%d.npz' % (name, k + 1)), **tk)
            one = {kk: v[None] for kk, v in tk.items()}
            doc = to_doc(body, rt_out, clips[ref_name]['rest'], name, k, one, 0)
            doc['recipe'] = rc
            # how close the pins came (no post-processing): the pinned joint's place against the pin's
            errs = []
            for pn, pd in zip(rc.get('pins', []), pins):
                f = pd['frame_indices'][0]
                p = build_pose(body, clips, rts, pn['pose'])
                _, Pp = body.fk(p.W, p.hips)
                j = {'right-hand': 'RightHand', 'left-hand': 'LeftHand', 'right-foot': 'RightFoot', 'left-foot': 'LeftFoot'}.get(pn['type'], 'Hips')
                errs.append(round(float(np.linalg.norm(np.asarray(tk['posed_joints'][f][body.idx[j]]) - Pp[body.idx[j]])), 3))
            doc['pin_miss_m'] = errs
            json.dump(doc, open(os.path.join(out_dir, '%s_t%d.json' % (name, k + 1)), 'w'))
            report[name].append({'take': k + 1, 'frames': len(doc['frames']), 'pin_miss_m': errs})
            print('%s take %d: %d frames, pin miss %s m' % (name, k + 1, len(doc['frames']), errs))
    json.dump(report, open(os.path.join(out_dir, 'report.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
