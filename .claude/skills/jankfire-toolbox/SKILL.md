---
name: jankfire-toolbox
description: Which tools and skills to use for JANKFIRE models, maps, textures, sound and UI work, and how they fit the game's rules. Read before any Blender, map, art or sound task in this repo.
---

# JANKFIRE toolbox

`CLAUDE.md` always wins. The skills below are third-party helpers (MIT, vendored in `.claude/skills`, licenses in
`_licenses/`); when one disagrees with CLAUDE.md's style or code rules, follow CLAUDE.md.

## Blender (two installs on the jankfire cloud environment)
- `blender52`: Blender 5.2.3 LTS headless (pip `bpy` in `/opt/bpy52`). **Use this one.** The `blender-*` skills target 5.2.
  It takes the same flags as the real binary (`blender52 -b file.blend -P script.py -- args`, `--python-expr`, `--version`).
  For the skills' runner: `BLENDER_EXE=blender52 python3 .claude/skills/blender-core/scripts/run_in_blender.py <script.py> -- ...`
- `blender`: Blender 4.0.2 from apt, a fallback. No Draco/meshopt in either: optimise glb with `npx @gltf-transform/cli`.
- EEVEE renders work through software GL (slow). Keep previews small (e.g. 640x480, a few samples).
- If `blender52` is missing (old environment): `python3 -m venv /opt/bpy52 && /opt/bpy52/bin/pip install bpy==5.2.3`,
  then recreate the wrapper from `tools/blender52`.

## Which skill for what
- Weapons and props: `blender-hardsurface-modeling`, `blender-pbr-materials` / `blender-texturing`, `blender-stylized-npr`
  (toon/outline looks), `blender-game-optimization` (poly budgets), `blender-export-pipelines` (glTF for the web),
  `blender-asset-qa` (always, before shipping a model), `blender-workflow-recipes` (end-to-end prop playbook).
- Map art and props: `blender-environment-kits` (modular kit metrics, scatter), `blender-time-of-day`, `blender-weather-fx`
  (wet neon streets), `blender-geometry-nodes`. Gameplay geometry stays boxes in `shared/map.js` (server physics + bots).
- Look development: `lowpoly-style` (poly budgets), `neon-retrofuturism` (cyberpunk), `comic-book-style` (the UI's zine
  look), `frutiger-aero-style` (glossy Y2K CG, the Nubby's Number Factory side), `liminal-space-style` (Backrooms map).
  These are art direction only: CLAUDE.md's palette and "chunky low-poly" rule come first.
- Design: `level-design`, `game-feel-design`, `procgen-design` (the city), `ai-behavior-patterns` (bots).
- Sound: `game-sfx` (renders layered WAVs from synth + real recordings and checks them with a spectrogram). Write the
  project's `sfx/SOUND_STYLE.md` first, as the skill asks. Today's sounds are synthesized in `public/js/audio.js`; real
  samples are welcome where they sound better (the owner wants less chiptune), loaded with Web Audio.

## Sound sources (check the license of every file you add, and list it in `public/sfx/CREDITS.md`)
- Freesound CC0 via `game-sfx`'s `freesound.py`: needs `FREESOUND_API_KEY` and freesound.org allowed on the environment
  (ask the owner; never put the key in the repo).
- Meta Open Sound (github.com/facebookincubator/Meta-open-sound): Oculus Audio Pack = CC BY 4.0 (credit line required):
  footsteps on six surfaces, UI sets, doors, ambience loops. Instruments are CC0.
- Stable Audio 3 Small SFX (open weights, Stability AI Community License) can generate effects; needs huggingface.co.

## Other GitHub tools worth using
- isaac-mason/recast-navigation-js (MIT): navmeshes from the map boxes for bot pathfinding (BR city, Plant & Defuse).
- donmccurdy/glTF-Transform (MIT): optimise glb. gkjohnson/three-mesh-bvh (MIT): fast raycasts on meshes if ever needed.
- bytecauldron/awesome-level-design (CC0): level design reading list.
