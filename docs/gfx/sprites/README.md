# Drawn effects test (smoke + water)

Owner: "is there a way to get like actual water ripples, smoke etc that arent like code ? like can you draw your own
sprites like the standard 3 layer ones or find a skillset or something off github reddit x internet?"

## What's in the test
- `old_vs_new.jpg` / `old_vs_new.mp4`: the old code squares (left) against option A (right). Top: Smoke Bomb. Bottom: water splashes.
- `option_b_soft_smoke_painted_ripples.jpg`: option A (left) against option B (right). Top: comic puffs vs soft smoke.
  Bottom: the water as it is vs painted ripples (a ripple normal map sliding over it).

| | option A | option B |
|---|---|---|
| smoke | comic puffs with ink outlines (`puff.png`) | soft see-through billows (`puffsoft.png`) |
| water | splash crown + foam rings (`splash.png`, `ripple.png`) | the same, plus painted ripples on the surface (`ripplenormal.png`) |

Switches (Settings > video): "drawn smoke + splashes", "smoke style", "painted water ripples". Potato keeps the code effects.

All five images are drawn by `tools/sprites/make.cjs` (noise + a little maths). Nothing was downloaded.

## Blender smoke sim: script written, bake fails here
`tools/sprites/smoke_sim.py` sets up a real Mantaflow smoke burst (gas domain, a puffing ball, turbulence, dissolve),
renders 36 frames side-on with Cycles on a see-through background and packs them into `public/sprites/puffsoft.png`
(same 6x6 layout the game already plays). Run: `blender52 -b -P tools/sprites/smoke_sim.py`.

It does not bake in the headless `bpy` 5.2.3 pip module (2026-11-10): Mantaflow's own start-up script dies with
`AttributeError: 'LevelsetGrid' object has no attribute 'setConst'`, then `NameError: name 'bake_fluid_data_1' is not
defined`, then Blender aborts with `Manta::Error ... can't clean grid cache`. Same with default domain borders. It
needs a full Blender build. Until someone bakes it there, `puffsoft.png` is the script-made cloud from `make.cjs`.

## Kenney and Unity packs: blocked by this environment's network
Not downloaded and their licence pages not opened: the session's network policy refuses these hosts (proxy 403):
`kenney.nl`, `opengameart.org`, `unity.com`, `blogs.unity3d.com`. So no licence line is quoted here and no files were
added. Once the hosts are allowed (or the files are put in the repo by someone who has read the licence), each pack
becomes one more "smoke style" in `flipbook.js`: a sheet, its grid size and a spawn recipe.

## What I found on the internet, and why none of it is in the repo
Looked up on 2026-11-10; licences as the pages state them, not downloaded or checked file by file.
- **Kenney smoke particles** (opengameart.org/content/smoke-particle-assets): CC0, 77 single sprites (smoke, explosion,
  flash, puff). Clean licence, but single frames, not animations, and a soft style that isn't ours.
- **Unity Labs "Free VFX image sequences & flipbooks"** (unity.com blog, 2016): smoke, fire and explosion flipbooks from
  Houdini sims, stated CC0. The best ready-made realistic set. Not used: realistic look, big files, and the licence
  should be re-read on the page before anything ships.
- **CGHeven flipbooks**: says CC0 on its own blog only. Not used: self-reported licence.
- **itch.io packs** (explosion minipack, stylized sprite VFX, Fellor's smoke pack): licence unclear, confirmed only in a
  comment, or paid with no redistribution. Rejected.
- **three.quarks** (MIT particle library for three.js): rejected for now. Our own particle code plus the ~170-line
  flipbook player covers this, and a library would be a new dependency to keep in step with three 0.170.
- Reddit and X: not searched (no tool for them here beyond a web search, which turned up nothing useful from either).
