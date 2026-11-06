# Lighting and shadows

Code: `public/js/lighting.js`. world.js calls it when the map loads, when the quality preset changes, and once a frame
right before drawing.

## What's in it
- **Sun shadows.** The first DirectionalLight in the scene (the one goggles.js and zombies.js already treat as "the sun")
  casts real shadows. The shadow box follows you and sits a bit ahead of where you look. It snaps to a coarse grid in
  light space (in whole texels, so edges don't swim) and only re-renders when it moves (every ~7 m), when the map, props
  or settings change, or when a player or something spawned since the map loaded is inside it (throttled per preset).
  Standing still in an empty area costs **0 shadow passes**.
- **Casters:** the world boxes, Blender props, remote players (mannequin, held glb gun, rig, wrecking ball, anything
  parented to them), loot, carts, traffic, debris: everything solid. Not cast: transparent/additive stuff (beams, the
  laser, smoke, water), back-face outline shells, the sky/sun/clouds/void, mesh crumbs under ~18 cm (players keep every
  part), and ceiling slabs on indoor maps (sealed maps and the mall), so the "sun" reads as the overhead lights there.
- **Receivers:** every lit material (Lambert / Phong / Standard, including the wrap pack's triplanar MeshStandardMaterial,
  which already has the shadow chunks). Unlit neon, screens and signs stay unlit.
- **Blob shadows** stay for anyone outside the shadow box, and for everyone on Potato or with shadows off.
- **Map moods** (`MOOD` in lighting.js): sun elevation (its compass direction comes from the sun/moon cube in the sky),
  shadow darkness, and a coloured bounce light from the other side (sky blue, sunset pink, moon blue, warm mall light...).
  The sky light is turned down a little and the sun up a little so the two sides read apart. `map.light` (backrooms,
  forest, crate) is still the base.
- **Neon and lamps** (`GLOW` table): every lamp, neon tube, glowing sign and ad box becomes a light source. A soft
  coloured pool of light on the floor under each one (one instanced draw for the whole map, on every preset), plus a
  few real point lights that move to the nearest sources and fade in and out (Mid: 2, Too HD: 4).
- **Baked corner AO** in the box vertex colours: corners, wall bottoms, under shelves and overhangs get darker. Built
  once at map load, free at runtime, so Potato gets the depth too.
- **Viewmodel:** your hands and gun dim when you stand in shade (a cheap walk towards the sun through the boxes every
  few frames), take the map's sky colours, and follow how bright the map is now (night, the mall power, flicker).
- **Forest flashlight** casts shadows on Too HD (512 map, yours only).

## Settings
Settings > video > **shadows**: `auto (by quality)` / `off (blobs)` / `low` / `medium` / `high (soft)`.

| level | used by (auto) | map | filter | shadow box | refresh while people move | remotes with real shadows | point lights |
|---|---|---|---|---|---|---|---|
| off | Potato | - | - | - | - | none (blobs) | 0 |
| low | Crusty | 1024 | hard, 1 sample (crunchy, matches the pixels) | 72 m | every 3rd frame | < 26 m | 0 |
| med | Mid | 2048 | PCF | 100 m | every 2nd frame | < 40 m | 2 |
| high | Too HD | 3072 | soft PCF | 120 m | every frame | < 56 m | 4 |

Light counts only change when you change a setting (that recompiles shaders once). Nothing allocates per frame.

## Pictures
- `before_after_*.png`: main vs this branch at Too HD, every map
- `presets_*.png`: Potato / Crusty / Mid / Too HD on this branch
- `clip_desert.mp4`: bots running around with real shadows (Too HD)

## Performance
Headless Chromium on swiftshader (software GL: no GPU in the sandbox), 1280x720, Training, the camera circling slowly
6 m round spawn 0, 6 s after 7 s of warm-up (so shader compiles stay out of the numbers). Draw calls and triangles are
per frame, both scenes plus shadow passes (renderer.info with autoReset off). "Worst case" forces a shadow re-render
every frame. Scripts: `docs/lighting/tests/` (perf.cjs, shots.cjs, t_light.cjs, t_bots.cjs; set PWLOCK to the handoff pwlock.cjs).

| map | preset | main: draw calls / tris | lighting: draw calls / tris | shadow passes per frame (calls per pass) | worst case, shadows every frame: calls / tris (calls per pass) | fps main → lighting (swiftshader) | render() CPU ms main → lighting |
|---|---|---|---|---|---|---|---|
| jankburg | Potato | 1371 / 411k | 1346 / 412k | 0 (0) | - | 5.3 → 4.6 | 12.96 → 11.08 |
| jankburg | Crusty | 1370 / 410k | 1348 / 413k | 0 (0) | 1593 / 622k (245) | 4.1 → 3.1 | 14.5 → 16.34 |
| jankburg | Mid | 1343 / 412k | 1334 / 412k | 0 (0) | 1730 / 645k (392) | 2.7 → 2.1 | 15.08 → 11.16 |
| jankburg | TooHD | 1336 / 412k | 1332 / 412k | 0 (0) | 1869 / 683k (529) | 1.7 → 1.1 | 14.77 → 10.29 |
| skyline | Potato | 119 / 264k | 125 / 265k | 0 (0) | - | 8.3 → 6.2 | 5.5 → 5.86 |
| skyline | Crusty | 106 / 262k | 168 / 307k | 0.14 (95) | 211 / 524k (71) | 6.5 → 4.7 | 5.17 → 7.98 |
| skyline | Mid | 131 / 265k | 161 / 320k | 0.2 (106) | 180 / 519k (69) | 4.4 → 3.2 | 5.51 → 6.4 |
| skyline | TooHD | 141 / 266k | 198 / 322k | 0.18 (167) | 275 / 535k (91) | 3.1 → 1.8 | 5.37 → 10.78 |
| suburb | Potato | 472 / 300k | 486 / 302k | 0 (0) | - | 6.3 → 6 | 9.21 → 10.08 |
| suburb | Crusty | 474 / 301k | 590 / 415k | 0.35 (285) | 785 / 626k (285) | 5.2 → 3.7 | 9.79 → 10.64 |
| suburb | Mid | 488 / 303k | 670 / 486k | 0.54 (320) | 822 / 641k (319) | 3.8 → 2 | 8.74 → 13.85 |
| suburb | TooHD | 497 / 304k | 977 / 700k | 1 (479) | 993 / 701k (490) | 2.2 → 0.8 | 9.76 → 13.24 |


How to read it:
- **Shadow passes are mostly cached.** On Jankburg and Skyline almost nothing near you moves, so the map re-renders
  0-0.2 times a frame. Suburb has dummies in range, so it refreshes at the preset's rate (Too HD: every frame).
- **Main-pass draw calls don't change.** The extra calls are the shadow pass. Its cost is capped by the shadow box size
  and the "no crumbs" rule: about 70-530 depth-only draws per pass.
- **fps on swiftshader drops a lot** (Suburb Too HD 2.2 → 0.8), because every shadow lookup and light runs on the CPU
  here. On a real GPU these are standard costs (one 1024-3072 depth map, PCF), but this sandbox couldn't measure that.
  Weak laptops can pick shadows **low** (hard 1-sample, 1024) or **off**, which goes back to blobs and costs the same as
  before, while still getting the AO and the light pools.

