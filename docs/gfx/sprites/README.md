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

## Blender smoke sim: not done
Blender is not installed on the machine this was built on (and it could not be downloaded there), so the soft smoke is a
noise volume marched by the script instead of a real simulation. On the jankfire environment with `blender52` a Mantaflow
sim baked to the same 6x6 sheet would drop straight into `flipbook.js`.

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
