# MotionBricks trial (19 Nov 2026)

The owner: "let's try using Nvidia motion bricks!!" These tools feed NVIDIA's MotionBricks our own poses and bring its
in-betweens back as R15 clips.

## Licence (read before using any output)

- **Code:** Apache 2.0. **Models** (the SOMA and G1 ONNX files and checkpoints): NVIDIA Open Model Agreement. It allows
  commercial use. NVIDIA claims no ownership of outputs, and an output is not a Derivative Model. The agreement's
  Trustworthy AI terms apply, and bypassing its guardrails ends the licence. Redistributing the model needs
  attribution. We don't redistribute it.
- **Sample motions** (the BVH and CSV clips under `assets/motions/` in NVIDIA's repo): NVIDIA Sample Data Evaluation
  License, for internal evaluation only. **Never use them as context or targets for anything that ships.** We only
  ran NVIDIA's own `generate_once.py` smoke test on one of them, and threw that output away.
- Our context and target poses come only from our Mixamo clips in the vault (`Documents\JANKFIRE Vault\Assets\mixamo-*`),
  or from edits of them. So every take here is ours to use.
- Neither the clips nor the takes go in git. The takes live in the shared notes folder (see below).

## Setup (official repo only)

- Repo: https://github.com/NVlabs/motionbricks (v0.2.0, commit 54fc563). Clone it with `GIT_LFS_SKIP_SMUDGE=1`, then pull
  only what's needed:
  `git lfs pull --include="motionbricks/assets/onnx/soma/mmm_v6_soma_fp32.onnx,motionbricks/assets/human/soma_base_skel_minimal_no_root.usd"`
  That is about 760 MB. Skip the G1 model and the media.
- `py -m pip install --user uv`, then `uv sync` in the clone. Set `UV_PYTHON_DOWNLOADS=never`, which makes it use the
  installed Python 3.12, and point `UV_CACHE_DIR` at a folder you can delete afterwards. This installs 17 packages,
  including TensorRT 10.8 (cu12), Warp, Newton and usd-core. The whole thing takes about 7 GB on C:.
- Hardware: it runs on this PC's RTX 4080 (16 GB) under Windows. NVIDIA only tested an RTX 4090, but no UE5 is needed.
  The first run builds a TensorRT plan (about 2 min, cached in `.trt-cache/`). After that, one generation takes well
  under a second.
- In the 19 Nov trial the clone lived in a session scratchpad: `...\scratchpad\mb`. Re-clone it if that has been cleaned.

## Pipeline

1. `blender -b --factory-startup -P tools/motionbricks/mixamo_rot_sample.py -- clip.fbx clip.json` writes every bone's
   world turn and head per frame (Blender axes).
2. `uv run --frozen python tools/motionbricks/mb_gen.py recipes_19nov.json <clips dir> <out dir>`, run from the
   MotionBricks clone, does three things:
   - Retargets Mixamo onto SOMA (both rest in a T-pose, with a per-bone rest alignment).
   - Runs one generation per target and chains them on the last four poses.
   - Writes four takes per recipe (token windows) in step 1's JSON shape.
3. `blender ... tools/blender/mixamo_r15.py -- take.json take.rbxm --no-loop --keep-drift --priority action
   [--warp ...]` turns a take into an R15 KeyframeSequence. For a Mixamo clip, the JSON path matches the FBX path to
   2e-6. Upload it as before (Open Cloud, assetType Animation).
4. `py tools/motionbricks/mb_sheet.py out.png --frames 10 take.json@label ... '#title'` draws contact sheets of takes
   and Mixamo clips side by side. Gold frames mark the poses we gave it; the gold tick shows where the face points.

## What it is and isn't

- MotionBricks is pose-conditioned in-betweening: four recent poses plus 1-4 target poses in, 0.6-1.9 s of motion out
  (6-16 tokens of 4 frames at 30 Hz). It is **not** text-to-motion; NVIDIA's Kimodo is the text one. It is good at
  bridging and locomotion, and keeps the poses you give it exactly.
- **Standstill targets far away get acrobatics.** We asked for "be 7 m ahead in the slash wind-up in ~1 s" and got a
  forward flip, with feet over the head. The model's training data (Bones RigPlay 1) has parkour in it. To get a run,
  give the targets speed: a recipe's `carry` moves the 4 target poses on at m/s. Our idle pose as two moving targets
  (3.5 then 5.5 m/s) gave a clean run at 5-6.7 m/s, with the spine leaning at most 20°.
- **The shortest move is 18 frames (0.6 s).** A faster action (a quick draw) needs a time warp in mixamo_r15.py
  (`--warp`).
- **Twist:** a slash turns the hips by over 100°. Recipes work in the clip's facing frame, not the hips' facing, or
  the given poses get spun.
