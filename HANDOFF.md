# JANKFIRE handoff (2026-11-07, coordinator session)

Live: https://jankfire.onrender.com (Render auto-deploys `main`). Latest shipped patch notes: **v6.8**. Read CLAUDE.md first.

## How the coordinator works
- Lane sessions build on their own branch and open draft PRs. The coordinator re-tests each one on latest `main` and merges it (owner's standing OK).
  - Merge with `git checkout -B ship-check origin/main && git merge <branch>`, then `node --check` on the changed files.
  - Boot with `node --max-old-space-size=256 server.js`. It must print no "share bit" warnings.
  - Smoke scripts: handoff/tests (t_all404, t_melee, t_mm, t_zm3, t_story0, t_lobby with `JF_LOBBY_WAIT=9000`, t_lb). They pre-set `jf_giftseen_all` so the gift popup doesn't cover the menu.
  - Story tests: `node --test tests/story/*.test.mjs tests/browsable.test.mjs`.
- Add a line to `public/js/patchnotes.js` for anything players notice, push it to the PR branch, then merge with the full 40-char `expectedHeadSha`. Wait until the new version string shows up in /js/patchnotes.js on the live site.
- Look choices, `supabase.sql` re-runs and exe builds wait for the owner. Original designs only. Secrets never leave the server.
- Server code: `class Room` now lives in **server/room.js** (#111). New installers go there, and `installModeStats` must stay the LAST installer.

## Shipped this run (all on main)
- Minimap + bot outfits + bot chatter (#82, #92)
- Fast model loading + 3D icons + streak looks (#86, #87, #95)
- Side-menu polish (#80, #85, #88)
- Royale backpack/grapple charges + S&D tactical shop (#89)
- Zombies:
  - boards, drops, Cheat Machine, loadouts (#90)
  - squad bots, cap of 4 (#113, #118)
- Per-mode leaderboards (#106)
- Liquids (#103)
- Gift + bulk container opening (#108, #114)
- S&D 5v5, 15 rounds, Valorant-style gunplay, learnable sprays, first-person spectate + corner box, Training SPRAY RANGE (#109, #117, #121, #123)
- Room move (#111)
- OVERDUE (story, hidden behind `?story=1`):
  - script (#75, #76, #84, #100 mechanics/bosses)
  - systems WP3/4/5/7 (#78, #81, #98, #105, #112)
  - world WP1/2, grapple, GTA data, Gate arena, shops (#79, #91, #99, #101, #107, #110, #116)
  - WP8 engine + Act I + cast (#77, #102, #104)
  - solo combat referee v1 (#120)

## Open PRs / in flight
- **#122 Overtime model/anims/cutscenes** (session_01Ayo4emQj6kDyzTHXfVXb6p). BLOCKED: `tests/story/ref.test.mjs` hardcodes the old enemy name/tags ('Corp Temp', ['corp']), but its enemies.js now says "☺ CORP TEMP" / ['corp','ranged']. The test should read from ENEMIES. The lane was told to fix this.
- **#71 Blender round 4 props**, glossy (session_01Ayo4eoPw2pkw8sSnE3MaPX). Finishing the vehicles. After it: a game-wide `docs/blender/INVENTORY.md` of everything still code-built, then a PS1/Cruelty Squad look test (car, palm, TV, pool ladder).
- **#115 Architecture look test**, PS1/Cruelty Squad buildings + real stairs on Suburb/Skyline (session_01Ayo4en8Pcv3HrjSrvgFhEV). **Waiting for the owner's OK** before converting every map.
- **#119 Grudge Ledger design** (OVERDUE "nemesis"-style system, kept distinct from WB's patent). **Waiting for the owner's OK** plus 3 questions:
  - is a 35% file chance right?
  - do they steal a cosmetic every time or only the first?
  - OVERDUE only, or multiplayer bots too?
- **#83 PS1 texture test**: parked by the owner (back burner). The pipeline at tools/blender/ps1.py is reused by the art lanes.
- **#6**: an old CSS reskin, stale; ignore it.
- Systems lane (session_01Ayo4epRiUAHmUrMzDPYwVi), next steps:
  - bosses PR (Overtime 1 at the Gut Border Gate, using #122's parts.json)
  - the slice world in the worker
  - civilians (killable, respawning), Late Fees wanted level, shops
  - grudge hooks
- World lane (session_01Ayo4enhVSVnYw2M1PfCmzD): standing by for boss-arena needs; swaps stand-ins to the PS1 kit after the look test is approved.

## Owner decisions still open
1. Approve the PS1/Cruelty Squad look (#115). Then: convert all maps, and should the existing glossy models be re-baked?
2. Grudge Ledger design + its 3 questions (#119).
3. S&D: is the moving inaccuracy harsh enough? Keep bots at 0.7x damage?
4. Streak-skin rarities in crates OK? (Disco Ball epic, Golden Duck legendary.)

## Goals the owner set
- **Everything Blender-made** in the PS1 + Cruelty Squad style: props, buildings, real staircases, vehicles, planes, TVs, pools, trees, terrain, characters. Gameplay and collision stay identical; check with a hash per map.
- OVERDUE demo: the slice is Act I solo through the first Overtime fight.
  - Missing: bosses, the slice world in the referee, and polish.
  - Optional for the first demo: co-op, Late Fees.
- OVERDUE features: GTA-style driving (done), killable respawning civilians, wanted level, shops, grapple-heavy traversal, Borderlands-style bosses.

## Known gotchas
- The guest gift memo (g20261107, open until 2026-12-07) shows once per browser. Tests must set `jf_giftseen_all`.
- A merged PR can't take new commits. If a lane pushes after a merge, open a new PR from that branch.
- Stacked PRs auto-close when their base branch is merged. Reopen them as new PRs against main.
- Headless runs are slow (SwiftShader). Perf numbers are noisy; use the bench method from #103.

## STOPPED 2026-11-08 (owner out of credit)
All lane sessions were interrupted. Nothing is merging. The open PRs above are drafts and safe to leave. Restart by reading this file.

## How to recreate the setup (so the models look as good)
**Cloud environment "jankfire"** (claude.ai > Claude Code > Environments, id env_01PZ5kcs8UzPeASfhX2RCLix):
- **Network:** limited.
  - Package managers and MCP servers are allowed.
  - Hosts: jankfire.onrender.com, plus the huggingface hosts (huggingface.co, cdn-lfs.huggingface.co, cdn-lfs.hf.co, cdn-lfs-us-1.hf.co, cas-bridge/cas-server/transfer.xethub.hf.co).
  - Network secret: a Freesound API key for freesound.org (CC0 sound effects). Re-add it in the environment's settings; the value never goes in the repo.
- **Setup script** (runs as root at session start):
  ```bash
  retry() { for i in 1 2 3; do "$@" && return 0; sleep $((i * 5)); done; return 1; }
  retry apt-get update -qq || true
  DEBIAN_FRONTEND=noninteractive retry apt-get install -y -qq blender python3-numpy python3-venv libegl1 libgl1-mesa-dri libegl-mesa0
  [ -x /opt/bpy52/bin/python ] || python3 -m venv /opt/bpy52
  retry /opt/bpy52/bin/pip install -q bpy==5.2.3        # Blender 5.2 LTS as a python module
  # + a /usr/local/bin/blender52 wrapper that runs scripts like `blender -b -P x.py -- args` through /opt/bpy52/bin/python
  if [ -d jankfire ]; then (cd jankfire && retry npm ci --silent); fi
  ```
  The full script, including the blender52 wrapper, is stored on the environment. Ask the new Claude to read it with the get_environment tool, or recreate the wrapper from the comment above.
- **Already in the image:** Node 22, Playwright + Chromium (use `--use-gl=swiftshader --enable-unsafe-swiftshader` for headless WebGL), ffmpeg.

**GitHub:** repo tacosonmondays-pixel/jankfire. The Claude GitHub app must be installed on it. Branches:
- `main`: live.
- `claude/handoff`: this file + the regression scripts in handoff/tests.

**Skills (vendored in the repo, load automatically):** `.claude/skills/`:
- `jankfire-toolbox`: start here. It says which skill fits which job and the game's art rules.
- The `blender-*` set targets Blender 5.2: core, hardsurface-modeling, pbr-materials, texturing, stylized-npr, asset-qa (the mandatory QA gate), retopology-uv, game-optimization, export-pipelines, rendering, lighting-lookdev, animation, environment-kits, geometry-nodes, scene-setup, pipeline-automation, workflow-recipes, time-of-day, weather-fx.
- Style/design skills: lowpoly-style (PS1), comic-book-style, liminal-space-style, neon-retrofuturism, frutiger-aero-style, game-feel-design, game-sfx, level-design, procgen-design, ai-behavior-patterns.
- Licenses are in `.claude/skills/_licenses`.

**The model pipeline itself (all in the repo, read `tools/blender/README.md`):**
- Models are built FROM CODE in headless Blender:
  - `blender -b --python tools/blender/make_<thing>.py` writes `public/models/<id>.glb` plus a turnaround sheet in `tools/blender/sheets/`.
  - `tools/blender/lib.py` is the shared kit: game-space primitives, sweeps, lofts, bevels, materials.
  - There are about 100 `make_*.py` scripts for weapons, skins, props, vehicles and gear. `make_all.sh` runs them all.
- Story models live in `tools/blender/cast/` (characters), `bottom_kit.py`, `gutkit.py` and `corp.py`. They export into `public/models/story|cast`.
- The look rules that make them good:
  - real-reference proportions;
  - glossy candy/clear-coat paint with chrome and brass (the current look);
  - the code model's muzzle/grip/sight spots, and wrap zones tagged in part names (`_wzA/_wzB/_wzN`);
  - a far `lod1`, baked AO, and a code fallback if the file is missing;
  - every model passes the blender-asset-qa gate and gets compared in game with `tools/blender/shots*.cjs`.
- **NEW PS1 + Cruelty Squad look** (owner direction; awaiting look-test approval):
  - `tools/blender/ps1.py` (PR #83, branch claude/map-pass) bakes one tiny dithered 15-bit texture per model.
  - `texkit.py` + the tiling kit in `public/models/arch/kit` (PR #115, branch claude/blender-buildings) is shared by the props and buildings lanes. The kit fixes a 16-colour palette, dither, and glb material extras (tex/tile/col/paint/alpha/glow/nocast).
- In-game check: start `PORT=3100 node server.js`, then run the shots scripts (Too HD = `jank: 3`, Potato = `jank: 0`).
- **Quality bar from the owner: "Models and animation max!!"** Run model/animation work at max effort, with sheets, screenshots and iteration.
