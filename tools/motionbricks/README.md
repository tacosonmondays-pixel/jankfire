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

# Kimodo (19 Nov 2026)

The owner: "yes but can you put kimodo on my d drive anywhere". NVIDIA's Kimodo (github.com/nv-tlabs/kimodo) does text to
motion. It can be pinned with constraints: full-body keyframes, hand or foot places and turns, root paths. It uses the
same SOMA body as MotionBricks, so `soma_retarget.py` serves both.

## Licence

- **Code:** Apache 2.0.
- **Model:** use only **Kimodo-SOMA-RP-v1.2**, under the NVIDIA Open Model License: commercial use is OK and NVIDIA
  claims no outputs. Never use **Kimodo-SMPLX-RP-v1**: it is under an R&D-only licence. The BONES-SEED data and the
  benchmark aren't needed and were not downloaded.
- **Text encoder:** Meta's **gated** `meta-llama/Meta-Llama-3-8B-Instruct`, under the Llama 3 licence. The owner
  requests access and logs in themselves. It is read through McGill's LLM2Vec adapters
  (`McGill-NLP/LLM2Vec-Meta-Llama-3-8B-Instruct-mntp` and `...-supervised`).
- Kimodo output is still generated. The owner judges it against mocap before anything ships.

## Setup on this PC (everything big on D:)

- Clone and venv: `D:\SteamLibrary\AI\kimodo`. The repo is cloned with `GIT_LFS_SKIP_SMUDGE=1`; `.venv` holds torch
  2.11+cu128 and Kimodo's dependencies.
- Caches, all set in `D:\SteamLibrary\AI\kimodo-env.sh` (source it first):
  - `UV_CACHE_DIR=D:\SteamLibrary\AI\uv-cache`
  - `HF_HUB_CACHE` and `HUGGINGFACE_CACHE_DIR=D:\SteamLibrary\AI\hf-hub`
  - `TORCH_HOME=D:\SteamLibrary\AI\torch`
  - `TMP=D:\SteamLibrary\AI\tmp`
  - `TEXT_ENCODER_DEVICE=cpu`, because the 8B encoder doesn't fit the RTX 4080's 16 GB alongside the model.
- `HF_HOME` stays at its default, so the owner's token lives where `hf auth login` puts it
  (`C:\Users\soup2\.cache\huggingface\token`). Never read it, type it or store it elsewhere.
- Owner's login, in their own PowerShell: `& "D:\SteamLibrary\AI\kimodo\.venv\Scripts\hf.exe" auth login`
- **No post-processing.** Kimodo's MotionCorrection (foot-skate cleanup and exact constraint hits) is a C++
  extension. This PC has Visual Studio 2026's compiler but no Windows SDK (`kernel32.lib` is missing), and installing
  the SDK is a multi-GB system install on C:. So Kimodo isn't pip-installed: it runs from source (`PYTHONPATH` = the
  repo) with `post_processing=False`. Pins are followed closely, not exactly, and the take JSON records each pin's
  miss in metres. To get exact pins, add "Windows 11 SDK" in the Visual Studio Installer, then run `pip install -e .`
  in the repo with `cmake` and `pybind11` installed in the venv, `--no-build-isolation`, and the venv's Scripts folder
  on PATH.

## Pipeline

1. `kimodo_gen.py <recipes.json> <clips dir> <out dir> [recipe]`, run in the Kimodo venv. Each recipe gets four takes
   (one call with 4 samples). A `loop` recipe is then generated again, each take pinned to its own first pose at both
   ends. Pins are our Mixamo poses on Kimodo's somaskel77, which rests in a T-pose with every turn the identity. They
   were checked: our FK matches Kimodo's to 1e-6 m, and the Mixamo round trip matches to 1e-6.
2. `mixamo_r15.py take.json take.rbxm --no-loop --keep-drift --priority action` turns a take into an R15 clip.
3. `r15_sheet.py out.png --frames 8 clip.rbxmx@label ... '#title'` renders a contact sheet in Blender on the place's
   real R15 rig (the part sizes and joint offsets of tools/roblox/finisher_r15.py). The rig's right side is orange and
   shows on the image's left; travel in studs is printed per cell.
