# The VFX pipeline (Roblox)

How JANKFIRE's effects are rebuilt for Roblox so that they match the web game's own effects (their timing, colours and
shapes) with a serious, polished finish. It is a loop with four parts, all scripted, and a cost guard:

1. **Reference capture**: the web game's own effect code, run on a fixed clock in headless Chrome, photographed at
   set times after the effect fires.
2. **Build**: the Luau effect in `roblox/src/client/Fx.luau` (pooled ParticleEmitters, Beams, PointLights), drawn
   with textures and flipbooks made in Blender (no image generators).
3. **Capture in Studio**: the same effect in a Play test, its clock frozen at the same times, photographed from the
   player's eye and from the side.
4. **Critic**: a fresh subagent compares the two, one time step at a time, scores out of 10 and lists fixes. The loop
   runs until about 9/10, or until rounds stop paying.

Our own pipeline; nothing in it comes from anyone else's recipes.

## Files

| what | where |
| --- | --- |
| reference page (runs `public/js/fx.js`, `flipbook.js`, the flash from `weapons.js`) | `tools/roblox/vfx/ref_harness.js` |
| reference capture (static server + headless Chrome over the DevTools protocol; no npm packages) | `tools/roblox/vfx/ref_capture.mjs` |
| what to capture (effects, views, times) | `tools/roblox/vfx/plans/*.json` |
| Blender sheets (flash star, flame, spark, glow, tracer core, shock ring, chips, dust puff) | `tools/roblox/vfx/vfx_sheets.py` |
| explosion flipbook (the web's own Blender bake, run again at 128 px) | `tools/sprites/blender/explosion_flipbook.py` (OUT changed) |
| smoke flipbook (the web's `puffsoft.png` as an 8x8 sheet, in-between frames cross-faded) | `tools/roblox/vfx/smoke_sheet.py` |
| the sheets and their asset ids | `roblox/assets/vfx/*.png`, `roblox/assets/vfx/assets.json` |
| the effects | `roblox/src/client/Fx.luau` (callers: `Arsenal.client.luau`, `Utility.client.luau`) |
| Studio capture helper (Client, Play test) | `tools/roblox/vfx/FxLab.luau` |
| packing modules for a capture test | `tools/roblox/vfx/lab_pack.mjs` |
| frame strips | `tools/roblox/vfx/strip.py` |
| the critic's brief | `tools/roblox/vfx/critic_brief.md` |
| proof (strips, scores) | `roblox/docs/vfx/` |

## 1. Reference capture

```bash
node tools/roblox/vfx/ref_capture.mjs tools/roblox/vfx/plans/ref_r1.json <out dir> --three <dir holding build/three.module.js>
```

- The page imports the web game's modules unchanged (`/js/fx.js`, `/js/flipbook.js`, `/js/ctx.js`) and copies only the
  muzzle flash, which `weapons.js` does not export (same star, gradient, sizes and times as `weapons.js:114-145`).
- `Math.random` is seeded and the effects are stepped in fixed 1/240 s steps (`REF.advance(t)`), so "0.05 s after the
  shot" is the same picture every run. `setTimeout` inside an effect (the explosion's after-smoke) runs on that clock too.
- Views: `eye` (the camera at the eye, the muzzle where Roblox's viewmodel puts it, in camera space), `side` (4 m
  to the right of the shot), `far` (any point from a distance).
- three.js is the web game's own dependency (0.170.0); point `--three` at any `node_modules/three`.
- Owner-supplied reference videos also work: Blender turns an .mp4 into stills (memory `blender-headless`).

## 2. Build

Rules for every texture: shapes, gradients, clouds and fire only. **No text, digits, codes, logos or links in any
image** (the account was warned once over an image that looked like a QR code). Look at each sheet at full size
before uploading.

```bash
blender -b --factory-startup -P tools/roblox/vfx/vfx_sheets.py -- <out dir> [flash spike spark glow tracer ring chips dust]
py tools/roblox/vfx/smoke_sheet.py <out dir>/vfx_smoke_8x8.png
```

Upload: Open Cloud `POST /assets/v1/assets`, `assetType: "Image"`, from the Studio-approved upload folder (the
Studio MCP's `open_cloud_invoke`); poll the operation for the id; record it in `roblox/assets/vfx/assets.json`; the ids
go into `TEX` at the top of `Fx.luau`.

Roblox limits that shaped the effects: flipbooks are 2x2 / 4x4 / 8x8 (plus a beta Custom grid), at most 1024 px; a
one-shot flipbook plays at its `FlipbookFramerate` (default 1 a second, at most 30), NOT over the particle's life, so
every one-shot emitter sets it to frames / lifetime (`oneshot()` in Fx.luau) and short-lived ones use 16-frame sheets; `FlipbookBlendFrames`
cross-fades frames (on for smoke and fire, off for flashes); a particle's `Size` is half its width; a particle's Size
and Color belong to its emitter (pools cycle through several emitters so a new shot does not recolour the last one).

## 3. Capture in Studio

Takes a Studio turn (`STUDIO-TURNS.md`: the queue, the lock, at most one Play test of at most 5 minutes). Nothing in
the place changes:

1. `node tools/roblox/vfx/lab_pack.mjs <approved folder>/fxlab.rbxm Fx=roblox/src/client/Fx.luau FxOld=<frozen old> FxLab=tools/roblox/vfx/FxLab.luau`,
   upload it as a Model.
2. Edit: compile check (load the pack unparented, wrap each source in `return function() ... end`, `require`).
3. Play. Server: `InsertService:LoadAsset(id)`, the folder into ReplicatedStorage; arm the player
   (`ServerStorage.JankTest:Invoke("arm", p, {...})`); stamp `TeleportT` and move them into the training range.
4. Client: clone `FxLab` and require it; `L.load("new", pack.Fx)`, `L.load("old", pack.FxOld)`.
5. Per frame: `L.frame(which, kind, opts, t, slow)` clears, fires, runs the effect clock (slow motion for short
   effects) and freezes it (`workspace` attribute `FxTimeScale = 0`; every copy of `Fx` listens in Studio), then
   `screen_capture`. Eye view: the game's own first-person camera and viewmodel; side view: `L.cam(cf)`.

The "before" frames come from `FxOld`: the previous `Fx.luau` with only the freeze added, plus the previous frag blast
and smoke cloud from `Utility.client.luau`.

## 4. Critic

A fresh-context subagent gets `tools/roblox/vfx/critic_brief.md` with the strips and the web's numbers, and nothing
else (not this session's opinions). It scores each effect out of 10, time step by time step, and lists concrete fixes.
Fixes go into `Fx.luau`, a new pack is uploaded, the next turn captures again.

## Cost guard

`L.cost("new", wid, secs, from, to)` fires a gun at its rate for `secs` (flash, tracer and impact, like a real shot) and
compares frame times with the same time idle; `Fx.stats` counts emits, particles, beams and lights per shot, and
`stepUs` is the effects' own Luau time per frame. Studio unfocused runs at about 15 fps, so frame times are only
compared against the idle window of the same test.

## What lives where in Fx.luau

| effect | Fx call | callers |
| --- | --- | --- |
| a gun shot (flash, flame planes, glow, light, smoke puff for others' guns, tracers) | `Fx.gunShot(w, muzzleCF, ends, path, fpv, noFlash)` | Arsenal (yours and others') |
| tracer | `Fx.tracer(from, to, colour, width, life)` | gunShot, the katana's parry return |
| impact by material (chips, dust, sparks, hole) | `Fx.impact(at, n, inst, mat, o)` | Arsenal, `Fx.shotEnds` |
| sparks + pop / melee hit flash | `Fx.sparks(at, dir, n, pop)` / `Fx.blast(at, r)` | Arsenal |
| frag blast | `Fx.explosion(at, R)` | Utility `boom()` |
| smoke bomb cloud | `Fx.smokeCloud(id, at, r, left)` / `Fx.smokeStop(id)` | Utility `addCloud()` |
| shield dome layers | `Fx.domeOpen(id, at, r, floor, fresh)` / `Fx.domeClose(id, popped)` | Utility `addDome` / `dropDome` |
| medkit heal | `Fx.heal(root)` | Utility `healFx` |
| duck black hole (the whole look; returns true) | `Fx.holeOpen(id, at, R, age)` / `Fx.holeMove` / `Fx.holePop(id, at?, r?)` | Utility hole functions |
| high-tier skin effects | `Fx.skinIdle(model, k, spec?)` / `Fx.skinOff(model)`; shots take the skin's colours | `WeaponModels.onBuilt` (one line in build) |
| capture controls | `Fx.setTimeScale(k)`, `Fx.clear()`, `Fx.stats`, `Fx.clock()` | FxLab |

**Sizes:** a ParticleEmitter's `Size` is half the particle's width (measured: Size 1 = 2 studs across), so every width
from the web game is multiplied by `H = 0.5`. The first-person flash uses `FPK = S x Holds.size` (the viewmodel is drawn
that much bigger than the web's metres).

**The flash's flame** is two thin crossed planes along the barrel with an unlit SurfaceGui showing the flame drawing on
both faces, the web's own construction. A camera-facing billboard (VelocityParallel particle) or Beam does not work
here: seen end-on from first person it becomes a big smear across the view.

## Hologram (`roblox/src/shared/Hologram.luau`)

The owner asked for "a cool hologram effect" for the hub's loadout and bundle holograms and training's mirror. One
client module, `Hologram.apply(model, opts)` -> handle, `H:remove(fade)`, `Hologram.of(model)`:

- the model's own shape in a calm tint, see-through, its drawn skin set aside and put back on remove; with `lines`
  (default) the body is Roblox's ForceField material, whose moving pattern the graphics card draws; `lines = false`
  plain Neon;
- a rim (Highlight fill + outline, depth-occluded), flickering faintly;
- a thin bright disc sweeping up through it every few seconds (the same disc flares as the odd glitch slice);
- optional projector (`projector = lensCFrame`): a soft cone of light up to the model, motes rising in it, a glowing lens;
- a scan-in build (a bright line rising, the pieces lighting up as it passes) and the reverse on remove;
- optional bob and turn round `pivot`.

**Cost** (16 Nov evening: the owner's lag report in training; the perf session found the mirror's 1.8x avatar with 288
scanline Textures, every part rewritten every frame): no Texture objects at all now; every part is set once when it is
dressed and written per frame only during the 1.5 s build-in and the 0.45 s scan-out, and then only when a value
changes by a visible step. A standing hologram's frame is the one Highlight (two writes, only on a visible step) and
the one sweep disc (skipped with `band = false, glitch = false`). One RenderStepped for all; nothing past 260 studs;
in Studio it obeys `FxTimeScale`. Highlights are capped at 31 on a client: a hologram uses one.

## High-tier skins (`SkinSets.FX`, the gun models session's spec)

Per skin: idle particles at points on the gun (metres in the gun frame, `both` mirrors), `afterFire` ones for 1.5 s
after each shot, a glow (a faint light), and the skin's own flash and tracer colours. Sprites: feather, petal, four-point
sparkle (Blender, `vfx_sheets.py`); ember = the glow, haze = the soft smoke sheet. Rule: nothing in front of the sights.

## Item looks after the owner's reference clips (16 Nov)

The owner sent five clips of layered ability effects and asked for new effects like them. Read as the kind of layering
(a core flash, a ring across the floor, swirling bands, rising sparkles, rolling smoke, debris), never their looks, and
with our quiet colours:

- **Frag:** shards flung out, slow cinders drifting up, a scorch that fades over 8 s, on top of the web's fireball.
- **Shield Bubble:** an opening flash and floor ring, two faint bands orbiting the dome, a ripple from its foot every
  1.4 s, droplets when it pops.
- **Medkit:** two green ribbons spiralling up the body (a Trail climbing a helix), a ring of light at the feet, sparkles.
- **Rubber Duck hole: a real black hole** (the owner, 16 Nov evening: "actual blackhole effect for duck pls"; Fx draws
  the whole hole, Utility keeps the gameplay, 3 s, the pull, the pop, and the little ducks): a pure black horizon (a
  black Neon ball: unlit, no shine) 2 m across like the web's core, growing in over 0.3 s; the accretion disk (a flat
  sprite in the disk's plane, tilted 14 degrees, turning, copies crossfading so the streaks keep moving; the horizon
  hides its far half); the lensing halo (a camera-facing sprite: the photon ring hugging the horizon, the disk's far
  side bent over the top and under the bottom, a faint warped glow); streaks falling in on a spiral and stretching
  (inward particles locked to a turning part, speeding up with negative drag); loose dark flakes pulled in from 6 m;
  grey floor dust drawn in; a faint violet light pulse. The pop: the horizon collapses in 0.12 s with the flash, a ring
  out across the floor. Sprites drawn from maths (`tools/roblox/vfx/bh_sheets.py`: `vfx_bhdisk`, `vfx_bhhalo`). The
  owner's reference clip for this was a glowing floor field; only its layering (a ground disc, streaks falling in) was
  taken.

## Results

### Batch 1-3: guns, impacts, frag, smoke, item layers, skins, hologram (16 Nov 2026, place version 430)

Live in place version 430: `Fx.luau` (all of the above), `Hologram.luau` (new, not yet applied by the hub or training),
the two `Fx.gunShot` call sites in Arsenal, the frag / smoke / dome / heal / hole hooks in Utility, the one-line
`WeaponModels.onBuilt` hook. Checked in Play: real SMG fire draws through `Fx.gunShot` (its tracers lit in the game's
own Fx folder), no script errors.

**Critic round 1** (fresh subagent, strips in `roblox/docs/vfx/round1/`, judged before the round-2 fixes):

| effect | score | the main faults it found |
| --- | --- | --- |
| gun shot, first person | 6 | spikes too orange; tracer a washed beige band; a hard blob at the tracer's end (the impact dust's first frame) |
| gun shot seen by others | 5 | a round glow, not the star; no grey smoke puff |
| bullet impact | 4 | chips read as rings, too light, too few, too close to the wall |
| frag | 3 | no fireball at 167 ms; at 0.8 s still orange, should be dark smoke; too small |
| smoke bomb | 6 | right idea; edges see-through; a slight blue cast |
| 14-gun lineup (previous tuning) | 3 | a huge glow ball near the camera; tracer colours washed to white |
| hologram | 4 | faint, no outline, a solid white disc, cone not meeting the gun |

**Found by that round** (now fixed, in 430):
- A one-shot flipbook plays at its **`FlipbookFramerate`, default 1 frame a second** (at most 30), not over the
  particle's life: the fireball sat on its first frame (a dot), the impact dust on its first frame (the critic's "hard
  blob"), the muzzle puff never opened. Found in round 2 (setting the rate live brought the fireball in at 0.22 s); fixed
  by `oneshot()` (frames / mean lifetime) on every one-shot emitter, 16-frame sheets for short lives (`vfx_boom_4x4`,
  `vfx_smoke_4x4`), `FlipbookBlendFrames` on.
- The flash: one star held per flash (no playing flipbook), orange only on the outer fifth of the spikes, no glow ball;
  third person uses a camera-facing star; lights dimmer and shorter.
- Tracers: less glow (LightEmission 0.5, Brightness 1.3) so each gun's colour survives; your own starts 3 studs out.
- Impact: solid flakes, the web's grey-green turning dark grey, faster (12-27 studs/s), the dust puff starts faint.
- Frag: opaque fireball (LightEmission 0), a dust-grey floor ring, a softer light.
- Hologram: pale ice blue, a firmer body and outline, light down 70 %, the cone ends under the model, gear cleaned
  up with the model, and the owner's sweep (from the lens up through the piece, 1.5 s).

**Cost guard** (SMG, 16 shots a second for 5 s, 82 shots, Studio unfocused at ~15 fps): frame time idle 66.65 ms avg /
71.8 p95, firing 66.66 / 72.5, no change. Per shot: 4 emits, 13 particles, 1 beam, 1 light; the effects' own Luau step
33 us a frame.

Next: round 2 captures at the web's own times (flash 8/20/40 ms, tracer 30/70 ms, impact 50/100/300/500 ms, frag
200/700/1000 ms, smoke 1/2 s) and a second critic pass; then the hit feedback batch, the smoke shell, the mesh kit.

### Rounds 2 and 3: critic fixes, the black hole, a cheap hologram (16 Nov 2026, place version 447)

**Critic round 2** (strips `roblox/docs/vfx/round2/`, the r14 tuning): first-person shot 7, others' shot 6, lineup 6,
smoke 5, impact 4, frag 4. Its fixes, all in 447:
- Flash: Brightness 2.5 -> 1.35 (it was a white blob, the star's #fff2a0 body and #ff9a1a tips lost); first person a
  quarter bigger and 0.1 m ahead of the muzzle (the handguard hid a quarter of it); others' 1.4x so the star reads at
  range.
- Tracers: LightEmission 0.3, Brightness 0.85 (they bloomed into a white smear where they overlap).
- Impact chips: the web's #999988 turning #444444 by a quarter second, sprayed wider (4-21 studs/s over 65 degrees), no
  drag; the dust puff a third smaller and half again more see-through, in neutral grey.
- Smoke bomb: our own thick lumpy puff (`tools/roblox/vfx/cotton_sheet.py`, `vfx_cotton_8x8`; the web's wispy
  puffsoft frames read as steam), drawn 1.3x, a few more of them: at 2 s it is now a solid white mass.
- Frag: fireball 25 % bigger, Brightness 1.0. The round-2 "dark square" at 0.7 s: the sheet's alpha is intact in
  Roblox (read back with an EditableImage), and the square did not show in round 3; the smoke stage still reads as a
  soft blur next to the web's crisp lumps (next round).

**Round 3 captures** (`roblox/docs/vfx/round3/`): the first-person flash is a pale star ahead of the muzzle; the smoke
bomb hides what is behind it; the black hole from the side and above (disk spiral, photon ring, floor dust, flakes);
the Seraph AR's effects in first person idle and aiming (7 emitters + 2 trails on the viewmodel, nothing over the
sights). Seen and fixed in the same turn: the hole's light washed the room violet (now 0.45 +- 0.2 over 8 m).

**Cost guard** (Seraph AR, full auto 5 s, Studio at 60 fps): idle 16.67 ms avg / 17.62 p95, firing 16.67 / 17.85.


### Round 4: the frag's smoke stage, black hole v2 (16 Nov 2026, place version 454)

**Critic round 3** (strips `roblox/docs/vfx/round3/`): first-person flash 7, frag 3, smoke bomb 6, duck black hole 6,
Seraph skin in first person 8. Its fixes, all in 454 (photos `roblox/docs/vfx/round4/`):
- Frag: the 0.5-1.2 s stage was a see-through maroon fog with no outline. Now the fireball (0.8 s) hands over at 0.3 s
  to a cluster of 11 opaque lumpy grey puffs (the cotton sheet, a box 0.55 r wide centred 0.4 r up, so nothing cuts
  into the floor) with 4 orange hot pockets glowing inside till about 1.1 s; small dark soot puffs from 0.65 s; the
  feathers use the feather drawing (they read as white dots).
- Black hole: the disk sprite crisper and more violet with a white-hot inner edge, twice as bright, tilted 20 degrees,
  about half a turn a second; the halo tighter (about 1.2x) with crisp arcs over the top and bottom; the streaks from
  5 m, 60 a second, twice as bright and stretched; the flakes stretch as they fall.
- Smoke bomb: lower and wider (boxes at 1.5 and 2.2 m, puffs 2.9 -> 5.7 m drawn), crisper lumpier puffs, more of them.
- Flash: LightEmission 0.45, Brightness 1.15 (the star's yellow body and orange tips show over a bright room); first
  person 0.16 m ahead of the muzzle, its barrel flames 1.5x wider.
- Skin particles in first person ride with the gun (LockedToPart): world-space ones were left floating when the view
  turned.

**Critic round 4** (strips `roblox/docs/vfx/round4/`): flash 7, frag 4, smoke bomb 7, black hole 6, Ducky LMG in first
person 7. Round 5's answers:
- Frag: the hot pockets burned down by about 0.5 s (gold -> #c0561a, LightEmission 0.3 so overlaps stop stacking into
  bright crescents), smaller uneven ragged lumps holding random frames, sorted behind the grey puffs (ZOffset -1.2 vs
  +0.5); the smoke body wider than tall (a box 0.75 r x 0.12 r, centred 0.3 r up on the blast), 9 puffs of 3.9-6 m.
- Black hole: a thin bright ring in the disk's plane at 2.25 m (the ring drawing) whose near arc crosses in front of
  the horizon from the side; the streaks only in a flat band round the disk's plane (a flat cylinder emitter, 5 m out,
  ending 1.2 m out, violet-white, shorter); the light halved and paler; the floor dust fainter; the flakes 2.5x bigger.
- Smoke bomb: a cool base colour (226, 229, 232), less room light (LightInfluence 0.55), more puffs at the rim.
- Flash: first person 0.72 of the viewmodel's scale (it was half the web's size on screen), LightEmission 0.3; your
  own tracer starts 3.5 studs out and comes to a point at the gun end (taper 0.15).
- Skins in first person go quiet while the gun is hidden (scope, a held camera) or while aiming (the view narrower
  than 0.95 of the widest seen lately): the bubbles drifted by the sight and hung in view when the gun was hidden.

**Critic round 5** (strips `roblox/docs/vfx/round5/`): flash 7, frag 3, smoke bomb 7, black hole 6, Ducky revolver and
katana 6. **Round 6** (place version 459):
- Frag rebuilt: the web's boom sheet (256 px cells drawn 30 m across) was a blur and its dark late frames the "fog".
  The fireball is now ~12 crisp lumpy puffs (`tools/roblox/vfx/lumps_sheet.py`, `vfx_lumps_4x4`: 16 different drawn
  lumps, each particle holds one) whose colour burns white -> gold -> orange -> dark brown over 1.1 s, plus a charcoal
  lumpy shell 15 % bigger from 0.35 s. Seen in Play: the crisp cauliflower outline is there; it ran near white at 0.2 s
  and still bright orange at 0.73 s, so the saved version burns down sooner (orange by 0.3 s, dark brown with orange
  inside by 0.7 s) and glows less (LightEmission 0.35, Brightness 1.2): not yet photographed.
- Black hole: the halo's arcs over the top and under the bottom wider, thicker and the brightest part (halo v3), the
  disk 35 % calmer, the band dimmer and lilac, white streaks (`vfx_streak`; the spark drawing is warm and read peach),
  the flakes from 4.5 m.
- Flash: tinted warm by default (255, 226, 150), so the star's body reads yellow and its tips orange.
- Skins: no trails in first person (they drew as stray straight lines after the draw).
- Smoke bomb: tried on the lumps (taller, see-through); back on the cotton puffs with less room light.

### Round 7: the frag that reads like the web's (16 Nov 2026, place version 464)

The round-6 frag (one burning colour on every lump) photographed as a flat lemon ball at 0.2 s and a flat rust blob at
0.7 s. Instead of one change per Studio turn, four variants side by side in one Play (`roblox/docs/vfx/round7/
lineup-*.jpg`; the two left ones partly behind a cabinet): A the round-6 glow, B a low glow, C the lumps unlit and dark
with a warm additive glow inside, D all additive. C read like the web's: a crisp dark lumpy mass with fire inside.
Live in 464: the fireball's 12 lumps unlit (LightInfluence 0.2, greys 120 -> 58), 7 smaller warm additive lumps inside
(cream -> orange by 0.5 s -> dim orange at 0.7 s, 0.9-1.1 s), the charcoal shell (7) from 0.35 s. Photos
`round7/frag.jpg`: at 0.72 s a dark charcoal cauliflower with orange glowing inside; at 0.2 s the inner glow still
blows out white (next: about a third less, cream not white). The katana keeps its trail in first person (checked: one
Trail on the viewmodel), guns' trails stay off in first person.

### Round 8: the frag from the reference itself; the angel flames (16 Nov 2026, place version 469)

- Frag (main, after seven rounds of layered round particles landing at "soft discs": take the shape from the
  reference): the web's own boom bake (`vfx_boom_4x4`) played as 7 smaller copies clustered, turned at random, in two
  waves 0.06 s apart. Round 1's blur was one 256 px cell stretched over 30 m; each copy now covers ~5 m, so the cells
  stay crisp and the cluster makes the cauliflower, with the web's own colours and timing. Photos `round8/frag.jpg`:
  at 0.72 s dark billowing smoke with orange inside, like the web's; at 0.2 s textured gold fire, a little softer
  and smaller than the web's crisp cream ball. The lump fireball (`vfx_lumps_4x4`) is no longer used by the frag.
- Angel weapons (the owner, 17 Nov: "glowing parts with cool vfx ... when you add a spray to it, it changes the color
  of the glow like flameish effect"): `tools/roblox/vfx/flame_sheet.py` (`vfx_flame_4x4`, a flame tongue licking up, 16
  frames). A skin's `SkinSets.FX[skin].flame = { segs = { polylines }, both, size, rate }` puts a small flame emitter
  every 7 cm along each lit edge (first person: locked to the gun, quiet while aiming); the gun's parts named
  `*__lit` and the flames take the equipped wrap's glow colour (`glow` on the wrap in Roster, else its neon slot,
  else its brightest saturated colour, else gold FFC94A), re-checked once a second from the "Wrap" attribute the
  wrap leaves on the painted pieces. A shot from a flaming skin throws flame tongues off the muzzle and draws a
  wider tracer in the glow colour. Tested in Play on a stand-in rifle with made-up edges (`round8/raw-flame-*.jpg`):
  gold flames along the top; a Galaxy wrap turned them violet (mid colour 176,125,255) but they barely showed on a
  light wall, so the defaults went up (0.12 m tall, 60 a metre, Brightness 2.4: not re-photographed). The six angel
  guns and their flame rows come from the gun models session after the slim-sights remodel.
- Katana flame arc (place version 471): a flaming skin's blade throws flame tongues off itself, mid to tip, every frame
  of the swing (your own: fed from Arsenal's first-person smear window, `Fx.bladeFlames`; someone else's: their swing
  event flares their blade for 0.25 s, `Fx.swingFlames`), left in the world so the blade's path draws the arc. Two
  one-line hooks in Arsenal. Tested on a stand-in katana at 3x scale (`round8/raw-katana-flame-arc.jpg`): a fan of
  gold tongues where the blade passed.
- Katana flame trail, reworked (place version 472; main: the round-9 tongues stood up across the crosshair, a fire wall
  not a swing; the owner asked for "a bit of a trail"): thin flame licks laid along the blade's path and stretched with
  its motion (VelocityParallel), from the blade's outer half, gone in ~0.2 s; your own in first person narrower and
  dimmer and never in the middle fifth of the screen; Arsenal's slash smear takes the glow colour (`Fx.bladeGlow`).
  Photos `round8/katana-trail.jpg`: first person right (thin gold licks along the arc, the crosshair clear); third
  person was too thin and faint, so it is now wider (0.09 m), brighter (3) and three licks a frame: not re-photographed.
