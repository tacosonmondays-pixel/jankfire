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
| technique notes from three open-source Roblox VFX references, and the claims to test | `roblox/docs/VFX-STUDY.md` |

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
every one-shot emitter sets it to frames / lifetime (`oneshot()` in Fx.luau) and short-lived ones use 16-frame sheets
(**26 Nov 2026, measured again in place v1372: a OneShot flipbook now plays over the particle's LIFETIME and
FlipbookFramerate is ignored** (the same sheet at life 0.533 showed the same frame at 30 fps and at 15 fps; at life 0.267 it
was twice as far). `oneshot()` still works, since it sets both; new effects just set Lifetime); `FlipbookBlendFrames`
cross-fades frames (on for smoke and fire, off for flashes); a particle's `Size` is half its width; a particle's Size
and Color belong to its emitter (pools cycle through several emitters so a new shot does not recolour the last one).

Outside art (decided 17 Nov): sheets come from our own references, Blender or maths. The one exception so far is the
muzzle flash's flame shapes (Kenney's Particle Pack, CC0; round 13). **Fallback for an effect that stalls** (as the
frag did for seven rounds): Unity Labs' 2016 flipbooks, which Unity released under CC0 (public domain), not its usual
Unity-only sample licence: 28 Houdini-simulated sheets of smoke, clouds, fire, fireballs and explosions, with links
alive on 17 Nov ([the post](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks)). They are not
downloaded. A download is the owner's call: tell the main session which effect stalled, and it asks for that one
download (name, source, size).

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
in Studio it obeys `FxTimeScale`. Highlights are capped at 255 on a client, and disabled ones still count (the docs, checked 16 Nov; this line said 31 before): a hologram uses one.

## High-tier skins (`SkinSets.FX`, the gun models session's spec)

Per skin: idle particles at points on the gun (metres in the gun frame, `both` mirrors), `afterFire` ones for 1.5 s
after each shot, a glow (a faint light), and the skin's own flash and tracer colours. Sprites: feather, petal, four-point
sparkle (Blender, `vfx_sheets.py`); ember = the glow, haze = the soft smoke sheet. Rule: nothing in front of the sights.

**Bullet trails and swing bits (17 Nov, the owner: "make sure special weapons have custom bullet trails and sfx that
match the style of the gun"; the gun models session's sheet `special-skins-trails-sfx.md` in main's notes).** A gun
skin's row may carry `bullet = { kind = ... }` (optional `colour`): `Fx.bulletTrail` draws that kind's line, a few
particles along it and a flourish where it ends, in place of the plain tracer (Fx.gunShot: muzzle bits on the first
leg of a bent path, the flourish on the last). Kinds: `feathers` (Seraph), `ember` (Infernal), `wisp` (Pumpkin Patch,
a curved Beam), `bubbles` (Bubble Bath), `hearts` (Wish Duck, `vfx_heart`), `dust` (Dust Drover), `powder` (Iron
Horse), `hardlight` (Star Drover), `rail` (Streamliner, `vfx_dash` wrapped and scrolling), `stars` (Triangulum). A
katana's row may carry `swing = { kind = "petal" | "sparkle", colour? }`: shed along each swing (Fx.bladeFlames,
yours frame by frame, others' for 0.25 s) and a burst on your melee hit (`Fx.skinHit`, Arsenal next to Sfx.skinHit).
Your own shot: nothing within 6 studs of the eye or in the first quarter of the path, half the bits, no muzzle ring or
puff, lighter smoke. Sounds are the sound session's (`SkinSounds.luau`). A new special skin: add its `bullet` (or
`swing`) line; new kinds go in `Fx.bulletTrail`.

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
  **v3 since 17 Nov (place versions 540, 552)**, after the owner's second reference clip (a black-hole effect video: a hot pink
  spark, a white-gold lens flare, then a black shadow with a warm photon ring, lensed arcs and a wide purple-magenta disk
  with an orange inner edge; the sequence and colours taken, nothing traced). The hole now opens with the spark (0 s)
  and the flare (0.07 s, biggest about 0.17 s), then grows in over 0.2-0.53 s; it collapses to a point over the last
  0.16 s before the server's pop (the client knows the hole's age, `Items.DUCK.holeTime`), and the pop adds a smaller
  flare. New sprites from `tools/roblox/vfx/bh3_sheets.py`: `vfx_bhdisk3` (nebula clouds on a spiral, white-hot and
  orange inner edge, flecks), `vfx_bhhalo3` (warm photon ring, lensed arcs), `vfx_bhshade` (a soft round shade tinted
  dark: the dark twins behind the halo and under the disk, so the colours hold on our light maps) and `vfx_bhflare`.
  The shades, the band and the halo are one long particle each; only the disk crossfades. First person stays clear:
  the sprites fade within 3.2 horizon radii of the camera (gone by 1.4), and the spark is skipped for the one the duck
  is stuck to. Timing of the pull and the pop unchanged.

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

### Round 11: the space-western pair's shot and lever-cycle effects; first-person skin effects back on (17 Nov 2026, place version 482)

- **Shot and lever bursts** (the gun models session's `EFFECTS` in `tools/roblox/gun_sets_west.py`, which the idle rows
  could not express). `SkinSets.FX[skin]` now takes `shot` and `lever` lists of bursts: `kind` spark (a hot streak
  thrown off and falling), puff (a soft curl of gunsmoke) or steam (a round white chuff, the lumpy cotton puff); `n`
  (or `{ min, max }`) per point, `size`, `life`, `speed`, `spread`, `delay`, `at`, `dir` (where they fly, in the gun's
  frame) and `both`. `Fx.skinIdle` hangs the emitters at the points (riding the view in first person) and
  `Fx.gunShot` fires them: shot bursts at the shot, lever bursts at the lever's clack (0.23 s after the shot, the
  same for you and for everyone watching). `pulse = { parts = { name starts }, t }` flares the pieces named
  `<start>...__glow` toward white, and lifts the skin's glow light, for `t` seconds on each shot.
- What each gun does: Dust Drover: a spark off the falling hammer, then gunsmoke curling off the muzzle and the
  cylinder gap 0.3 s later. Star Drover: teal sparks off the rotor's sides, and the rotor's hub flares. Iron Horse
  (its wheels never turn, so the lever cycle is its moving moment): a steam chuff out of the stack on the shot, then at
  the clack another chuff, steam out of both cylinder cocks and sparks off the drive wheels' rims. Streamliner: teal
  sparks drop from under the hover rings at the clack, and the nose ring and the light line flare on each shot.
- Your own in first person: none while aiming or hidden, and no puff across the middle fifth of the screen.
- **Fixed: first-person skin effects were always off.** The check for whether your own gun is showing (round 4) read
  the model's Root, which is always invisible, so every skin's first-person idle effects (bubbles, feathers, sparkles,
  the angel flames) stayed off. It now watches the gun's biggest visible piece.
- In Play (`round11/`; stand-ins at twice third-person scale, frozen with `FxTimeScale`): the Iron Horse's wheel
  sparks and the Streamliner's falling teal sparks read well at 0.3 s; the Star Drover's hub flare shows at 0.05 s.
  The revolvers' sparks did not show at all at first (the spark drawing needs the frag's x3.4); fixed and checked
  live on the levers. The steam chuffs read too small, so they are about 1.7x bigger now. Not re-photographed after
  those two fixes, and nothing photographed in first person yet.

### Round 12: the first-person pass with effects really on (17 Nov 2026, place version 486)

Main asked for it after round 11's finding (first-person skin effects had been off since round 4, so no earlier
first-person check saw them). Real viewmodel, real input, the test hook arming the skins: the Ducky LMG (Bubble Bath
v3), the Seraph rifle, the Dust Drover revolver and an SMG in the Lava wrap, each idle, strafing, firing and aimed.
Sheet: `round12/first-person-sheet.jpg`.

- Passed: nothing sits on the sights; every skin's effects go quiet while aiming (0 of 8, 0 of 7, 0 of 5, Lava 0 of
  4) and come back after; strafing at 9-10 m/s floods nothing (first-person particles ride with the gun).
- Fixed: a shot's bursts went to the first skinned gun within 2.5 studs of the muzzle, and in first person that was
  often the copy hidden in your character's hand, so your own shots' sparks went off on a gun you can't see. Now the
  nearest muzzle wins. And any gun that isn't showing goes quiet (that hidden copy's idle effects drew round your
  hand before).
- Fixed: Lava's embers (WrapAnim, not Fx) rose into the upper middle of the view, one inside the middle fifth. In first
  person, wrap particles now live 0.55 as long (a third of the climb). Pushed after the Play, not re-photographed.
- Re-photographed from round 11: the Dust Drover's hammer spark (a warm streak pair off the back of the gun, riding
  it through the twirl) and its gunsmoke (a faint warm curl at the muzzle at 0.5 s).
- Capture trap: freeze on the mouse press, not on the ammo count. The count waits for the server, and a 0.14 s spark is
  gone by then.
- Open: firing right next to a wall, the muzzle light blows out half the screen (Lava SMG frames). That is Fx's own
  light at a stud from the wall; next turn.

### Round 13: a new muzzle flash (17 Nov 2026, place version 499)

The owner: the flash "looks kinda ugly" and asked for one found online. The web's 16-point star read as a flat sun
sticker. Looked at: free Creator Store flash images (most have the colour baked in, several are rips from other
games, and other people's images can be taken down under us) and CC0 packs (mostly pixel art). Picked Kenney's
Particle Pack (CC0, kenney.nl/assets/particle-pack; credit is welcome, not required): its five side-view muzzle flame
tongues, white with soft alpha, made for tinting.

- `tools/roblox/vfx/mflash_sheet.py` lays them out (the pack itself is not in the repo; point the tool at its
  `PNG (Transparent)` folder). Front sheet: 5-7 tongues of uneven length round a small hot core, long and short in
  turn, four variants. Side sheet: one tongue lying along +X with a thinner one inside it for a hot root. Colour is
  baked from a "heat" map (white core, pale gold, orange tips); the `_n` copies are white and pale grey, so a skin's
  flash colour tints them (the Star Drover's flash is now pale cyan, not gold). Alpha-bled, 2x2 cells of 512 px.
- Fx: the particle star uses `TEX.mflash` (or `mflashN` with a skin colour), 1.8x the old size because the tongues
  fill about half a cell; the barrel's two crossed flame planes show one random cell of `TEX.mside` through
  `ImageRectOffset`, sized from where the drawing actually shows (`SIDE_X0`, `SIDE_X1`, `SIDE_TH`, measured as alpha
  over 0.2).
- The light by a wall (round 12's open item): three 5-stud rays from the muzzle (ahead and to both sides, missing
  the effects, the camera and characters) dim it, squared. The first try (3 studs, a 1.5 power) still lit the wall
  bright at 2 studs; the squared one, photographed in a second Play 1.6 studs from the hall's wall, leaves the wall
  its own colour (`round13/wall-glare-before-after.jpg`).
- Sheet: `round13/muzzle-flash-before-after.jpg` (round 12's frames above, this round's below).

### Round 14: the sakura katana's petals on the new model (17 Nov 2026, place version 501)

The gun models session rebuilt `katana_sakura` as the J-A Maki-e katana (v498) and asked for a re-check: its petal
points sat on the old blossom guard and sprig. Measured on the new model's file (`w_katana@katana_sakura.glb`, gun
frame): the guard's first point was 1 cm above the new, smaller guard, and the first blade point 4 cm above the
blade's back (0.07 where the back is at 0.033). The petals now come off the guard's gold rim, the hilt's two blossom
ornaments (mirrored) and three points on the blade's back; the swing trail follows the back. First-person photo:
`round14/sakura-katana-petals-fp.jpg` (petals on the blade, the rim and the hilt, none floating). Third person not
photographed: the shoulder camera sits behind the avatar's hat.

### Round 15: black hole v3 (17 Nov 2026, place version 540)

Main passed on the owner's reference clip for the Rubber Duck (spark, flare, then a Gargantua-style hole). Built as in
"Item looks" above. One Play in the training hall with the effect clock frozen (Fx called directly, so Utility's little
orbiting duck is not in the frames): `round15/blackhole-v3-first-look.jpg`.
- Holding (1.4 s): from the side the black shadow, the thin warm ring, the bright arc over the top, the disk's near
  side crossing in front of the shadow, magenta and purple clouds with flecks on the dark backing; from above a
  swirling nebula with an orange inner edge. Reads on the hall's light walls.
- Opening: the spark's pink light and the flare's warm light flood the near wall (frozen at full strength), and the
  flare itself is faint against the lit wall.

**Second turn (place version 552)**, sheet `round15/blackhole-v3.jpg`: the spark's light 3 -> 1.1 over 3.5 m (was 5 m),
the flare's 4 -> 1.6 over 6 m (was 9 m); the flare 3.4 m wide at its biggest (was 2.8) at Brightness 4 (was 2.6); the
warm band moved from 2.25 m (a pale ring round the middle of the disk, a Saturn look) to the disk's hot inner edge
(1.17 m), where its near arc crosses the shadow's lower part. Seen:
- 0.17 s: a bright white-gold star with a long level streak and thin rays, the wall no longer flooded; 0.32 s: the
  hole opening inside it with the hot band across its lower edge.
- 1.4 s from the side: no outer ring; the nebula disk round the shadow, the warm ring and the arc over the top.
- 2.93 s: shrunk to about a third, streaks still falling in; 3.05 s: the pop's flash (its light frozen at full, so the
  hall reads pink-white; in play it fades in 0.3 s, and Utility's own violet flash and fire bits are not in the frame).
- First person with the hole on you (camera 1.25 studs from its middle): the view stays clear, only a few streaks
  and a flake cross it.
- Not checked: a real thrown duck end to end (the frames call Fx directly); the spark at its new light strength.

**Third turn (place version 570)**, main's last asks and the classic modes session's Duck Rain photo (the whole arena
lavender with many holes; `roblox/docs/modes/duck-rain-hud.jpg`), sheet `round15/blackhole-v3-real-and-rain.jpg`:
- The pop is a snap: its light 1.6 over 0.55 of the blast radius for 0.12 s (was 5 over 1.4 radius for 0.3 s), the
  glow 0.16 s and about two thirds the size, the hole's own light 1.2 for 0.12 s.
- The lavender room was Utility's screen tint (`JankHoleSqueeze`, a ColorCorrection up to 90 % violet whenever any
  hole pulled on you; Duck Rain's holes reach 12 m and are everywhere), not the holes' lights. It now starts only in
  the inner 60 % of a hole's reach and goes at most half way to a paler lilac. Lights budgeted too: only the two open
  holes nearest the camera carry their PointLight, now 6 m (was 8 m).
- Duck Rain holes live 2.6 s, not the duck's 3: the hole's message carries `life` and Utility passes it to
  `Fx.holeOpen(id, at, R, age, life)`, so their collapse lands on their pop too.
- A real duck thrown with G at a dummy (logged on the client from the G press): the hole's message at 0.41 s (age -0.3,
  stuck), the horizon from 0.63 s, full at 0.83 s (the pull starts at 0.71 s), the collapse from 3.56 s, gone at 3.70 s,
  the server's pop at 3.73 s: it closes 0.03 s before the pop.
- Six sky holes at once (their real client path: the server's hole messages with life 2.6, R 12 m): 6 open, 2 lit, no
  screen tint 7 m from the nearest; the hall keeps its own colours.
- Not clean: the throw at the floor. The first hole had pulled the player up to the dummy and the second duck stuck to
  it. A floor duck's hole sends age 0, the same message the sky-hole test sent, so its opening is that path.

### Kill effect previews for the shop's cards (17 Nov 2026, place version 625)

The owner: "for kill effects in shop can they be small previews? same with in inv?". The shop session's `FlairAnim`
plays a sheet per effect from `Shared.FlairSheets.kill`; the sheets are ours: 4x4 frames of 256 px (1024 px images),
0.1 s apart, on the flair tile's dark (22, 24, 30), no text in any image (`roblox/assets/kill-previews/`, ids in its
`assets.json`).
- Captured in Play (`tools/roblox/vfx/kill_capture.luau`, Client): a box far above the maps (Neon walls in the card's
  dark, which Studio draws black), its own Camera (a game script forces the main camera to FOV 80 every frame; ours FOV 10
  from 178 studs, nearly flat), two SurfaceLights, six training-dummy copies 12 studs apart cropped to 8 studs (so
  no effect spills into a neighbour's square), each playing `KillFx.play(copy, id, { preview = true })` from the client's
  own KillFx copy on the frozen `FlairTimeScale` clock; `C.runTo(t)` runs to each frame time then freezes. Gibs ("none")
  is moved by hand (flung, falling, a short skid where each piece lands). Blue Screen's TextLabels are hidden for the
  shot; its words come back as live text (`words`, over frames 2-9 on the panel's top line).
- `tools/roblox/vfx/kill_sheets.py <job.json> <out>` cuts each square out of 16 captures, shifts the frame so the
  wall reads exactly (22, 24, 30), and lays out the sheet. Ember's last four frames had the next square's chickens
  walking in: painted out by hand.
- `n` per sheet stops a loop before its empty tail (Yeet 8, Blast Zone 6, Shatter 9, Static 10, Gibs 10: the body
  is out of sight, or lies still), so each comes round after a short beat.
- Checked in Play: the shop's inspect card for Blue Screen steps its frames and shows the words on frames 2-9 (a
  property check; Studio's window was hidden, so no photo).
- Ink (place version 630): its black blots fell on the box's black and the first capture clipped them to nothing.
  Retaken on a lighter Neon wall (72, 74, 80), which Studio draws about (50, 54, 72); `"remap": true` in the job maps
  that wall to the card's dark and anything darker in proportion, so the ink stays black on the card. n 10. (A first
  retake came back blank white, even the card-dark wall: Studio's window was hidden, not the wall.)

**Bullet-trail retake (place version 630):** the ten special-skin trails with v596's doubled bits, drawn by
`Fx.bulletTrail` across the training hall with the Fx clock frozen: `round16/v630-ten-trails-008.jpg` (0.08 s: the
hearts, bubbles, stars, rings and feathers now read at this distance) and `-018.jpg` (0.18 s: the trails fading, the
Star Drover's ring bloom, sparks and feathers settling). Real first-person shots (a fresh Play, real
mouse clicks, the Fx clock frozen from the press): `round16/v630-fp-seraph-shot.jpg` (0.067 s after the press: the
muzzle star, the hit mark on the dummy 24 studs off, a shell; your own line is meant to stay faint up close, first 25 %
and 6 studs skipped, half the bits) and `round16/v630-fp-sakura-swing.jpg` (0.166 s: the pale swing trail with pink
petals shed along the arc and round the guard). Scripted cameras first and a real first-person shot after don't mix in
one Play: the game camera came back facing a pillar, with no gun in view.

### Speed lines, wind and the FOV kick; the RANKED fire's base; the Tripo rifle's glow (17 Nov 2026, place version 644)

**Speed lines** (the owner: "when you pick up speed with the grapple can you add those speed lines and wind effects from
jank fire"): `SpeedLines.client.luau` ports the web's `speedlines.js`. White wedge streaks (`ui_speedline`) run in
from the screen's edges toward where your velocity points on the screen, from 22 m/s, at full strength by 82 m/s
(14 + 70k of them, redrawn at 30 fps), hot pink and yellow past mach 1. It reads the body's real speed (1 m = 3 studs),
so grapple swings, pads and slides all count. A little wider and more opaque than the web's (0.25-0.75 x k): at the web's
0.12-0.52 they vanished on the hub's light walls. Under every other screen (DisplayOrder -2), so the HUD and the touch
buttons draw over them. The wind: a recorded loop (Pro Sound Effects "Barstow Wind Light Blustery Low Howl 1",
9113286782) from 15 m/s, louder and a little faster with speed, on the EFFECTS volume; thin wind streaks in a ring at
the edges of the view. The FOV kick is the web's (+ min(35, horizontal m/s x 0.3), + 6 sprinting, + the rope's swell),
eased, as the player's `SpeedFov` attribute that Arsenal adds to the base FOV (`Move` now sets `Sprinting`). Settings
`gfx.speedLines` and `fov.kick` (the settings session's rows), on unless set off. Off in menus, replays, finishers and
while dead. Studio hook: the player attribute `SpeedLinesTest` = m/s. Strip `round17/v644-speedlines-40-75-360.jpg`
(40, 75 and 360 m/s through the hook, so the focus is dead ahead; a real pad or swing not photographed).

**The RANKED fire's base** (the owner: "the base of the flame jumps up too!"): the layer never moved, but each flame was
stretched whole, so its solid hot base band grew to a third of the panel in the sweep. The flames are nine-sliced now
(`ScaleType.Slice`, the cell's bottom 44 rows at the settled flame's scale), so the base stays a low band on the
panel's edge and only the tongues climb; the glow is a fixed base glow plus a faint even one that rises with the
sweep. `round17/v644-ranked-fire-hold-01-03-06-10.jpg` (FlameStripHold 0.1, 0.3, 0.6, 1.0 on the real panel).

**The Tripo angel rifle** (`ar_seraph_tripo`, the owner: "Can it have some like cool glowing gold effects around the
barrel or somethin?"): a breathing gold aura round the halo ring (new idle kind `aura`), sparkles round the ring, slow
gold motes off the halo and the brake (new kind `mote`), a gold light on the barrel (`glow.at`). Idle rows may now carry
`fp` (their rate's share in first person; 0 = none there) and `tint` (they take the wrap's glow colour, gold with none).
Photos `round17/v644-tripo-halo-closeup-and-fp.jpg`: up close in the training hall (gold motes drifting up off the
barrel, the halo's lit ring and the brake's star bright, the light warming the barrel) and in first person (the halo far
down the barrel by the crosshair, its bits small and calm, the sights clear). The breathing aura is faint in the lit hall:
stronger if wanted (`aura` rate or size in the row).

### Jump pads light up (17 Nov 2026, place version 667)

The owner: "pads should glow when you step on them!". `PadFlare.client.luau` lights any part with a `Pad` attribute
(Move throws you off it), in every map: on a throw its kit's coloured pieces (the `JumpPad` model laid over the
see-through `JumpPadTop`, found by name: its meshes don't answer spatial queries) turn Neon in the pad's colour, a light
pulses, a glow lies on the face and a ring of light spreads off it, motes shoot up; about 0.6 s. While someone stands on
it, a steady fainter glow and light. The throws come from `PadSignal.luau`, one client-side signal that Steps.client
(the sound session's) fires with its launch sound for every character, so everyone sees everyone's; the standing is a
look at each character's floor ten times a second. Nothing runs for an idle pad. It never touches the hub's queue pads
(PadGlow.client's `Glow` parts: Team attribute, under QueuePads). Studio hook: the player attribute `PadFlareTest` =
"launch" / "stand" / "both" (the nearest pad). Strips `round17/v667-padglow-hub-idle-stand-launch.jpg` and
`-training-rooftop-launch.jpg`; a real step-on throw off a hub pad was checked by its light (peak 4.7 of a flare's 5).
Rooftop pads only throw in a match, so they were flared through the hook.

**The angel rifle v6's new glowing lines** (the owner: "can there be more glowing parts with cool vfx?"; the gun models
session's v6, place version 669): small gold flame licks along each rear wing's top edge to its tip (`flame`, with the
new `lift` 0.25: at the Seraph's lift, flames this small floated well above the edge), feathers shed off the wings'
outer edges, twinkles along the handguard's lines and on the brake's stars, a short trail off each wing tip; the brake's
motes moved clear of v6's wider ported brake. `flame` rows may now carry `fp` (first-person share; the wings sit close
to the eye there, 0.35), `step` and `lift`. Photos `round17/angel-v6-effects-wings-barrel-fp.jpg`.

**The angel rifle, second pass** (the owner: "those flames look so buns", then a reference clip of weapons wrapped in
coiling ribbons of golden light): the wing flames are out. New `Fx` option `coil` (spec.coil: strands running round a
helix along an axis, each a glow emitter that leaves a fading ribbon in the world; skinStep moves them): two round the
barrel, one up each wing, with a gold core under each glow (additive gold alone vanished on the white gun). In the
world, not locked to the gun (locked, they rode along as one ball), so off in first person (fp 0: they would smear as
you turn). Also twinkles along the wings' lit loops and a big star glint now and then at the wing tips and the muzzle.
First look `round17/angel-v6-coils-first-look.jpg`: the coils read as thin gold arcs round the barrel, not yet the
thick glowing vines of the reference. Next, from the research (`docs/vfx/research/stylized-weapon-vfx-2026-11-17.md`):
the coils as Beams on a spinning holder (a real ribbon), the glint with a halo, white-hot cores.

**The angel rifle, vines of light** (place version 701; the research's recipe 3): `coil` rebuilt from particles into
Beams. Each strand is a chain of Beams, one a quarter turn or less, between attachments on the helix whose X axes lie
along it, so each beam bends into its arc (CurveSize = 4/3 tan(dθ/4) |dp/dθ|, the circle-arc rule with the helix's
speed). Four layers an arc: a wide soft halo (additive, 0.55 clear), a deep-gold body (LightEmission 0.15, so it holds
on the white gun and light walls), a white-hot core (Brightness 3.5) and beads of light (`TEX.pulse`, new:
`tools/roblox/vfx/vine_sprite.py`, one soft bead a strip; Wrap with TextureLength a whole fraction of the arc, so the
beads run on across the joins; TextureSpeed = `pulse`). The vine tapers to nothing at both ends; skinStep turns the
helix at `spin` rad/s, so it winds along the gun like a barber's pole; the mirrored side turns the other way. Beams ride
the gun, so first person has them now (`fp` = their width share there; off while aiming, with the rest). A wrap's glow
colour reaches every layer (`coilShade`). The row: two vines round the barrel (r 6.5 cm, 1.5 turns), one up each wing.
88 beams a gun. Photos `round17/angel-vines-v701-close-side-fp.jpg` (taken before the bead texture had processed: halo,
body and core only) and `round17/angel-vines-v701-beads.jpg` (with the beads, over the training hall's dark floor).

**The legendary gadget skins' trails** (18 Nov 2026, place version 840; main's ask, rows in the notes folder's
`special-skins-trails-sfx.md`). New `Fx.itemFlight(model)`, `Fx.itemLand(model, at)` and `Fx.itemUse(model)`, keyed by
the skin model's name (Utility.client's itemModel clones `ReplicatedStorage.JankfireSkins.<id>`). The utility session
calls them (v836): flight in addFlying, landing only when the server's "pd" says it really went off (`x = true`: the
fuse, or the duck sticking), use as your own bento opens (first person only; nobody else sees the lid). Rows in
`Fx.ITEM_FX`; a plain gadget or a skin without a row does nothing.
- Paper Lantern (frag): a thin warm glow trail (Trail on a host part that follows the gadget, camera-facing, 10 cm) and
  a few tiny embers. At the blast, 20 red and gold paper scraps flung out and fluttering down for 2.4-3.4 s (the first
  look's 7.5 cm scraps living 2 s vanished in the soot), 9 embers rising, all under Fx.explosion.
- Incense Burner (smoke bomb): a faint pale smoke thread (3.5 cm, 0.7 s) with small curling wisps. As the cloud starts,
  7 slow incense curls and one soft bronze glint (under the cloud, by design).
- Origami Duck: cream and blue paper flecks (8 cm) shed as it flies, a very faint pale trail; a pop of 12 flecks
  where it lands.
- Bento Box (medkit): 4 faint steam wisps off the top as the lid lifts.
- The paper sheet `TEX.paper` (new, `tools/roblox/vfx/paper_sheet.py`): four folded scraps (2x2), grey-shaded faces and
  a darker rim so a Color tint keeps the fold; each particle holds one random scrap (FlipbookFramerate 0 +
  FlipbookStartRandom). When a gadget lands, its host stops moving rather than turning the Trail off (a disabled Trail
  vanishes at once), so the trail fades over its own life.
- Photos `round18/v840-gadget-skins-trails.jpg` (a test rig flying the skins' own models in loops at 14 m/s in the hub;
  the duck's larger flecks and the bento's steam are not in the photos).

## The RANKED fire, second drawing (18 Nov 2026, place version 913)

The owner on the Play menu's mode panel: "whya re the falmes like cut off or is ther blocky flames in the backl?". The
utility session traced it: each cell of `vfx_fire_8x8` was a full-width wall of fire (a solid hot base across the cell,
straight sides faded over only ~8 px, a fairly even top), so FlameStrip's eight labels at independent heights (56-96)
read as rectangular blocks at stepped heights with flat tops.

- New sheet `vfx_fire_tongues_8x8` (asset 76464949862705, `tools/roblox/vfx/fire_tongues.py`): every cell is a group
  of separate tongues, each widest low down and tapering to a point, eaten by the first sheet's scrolling turbulence;
  clear between them; only a soft broken ember band where they root; alpha fading over 28 % of the cell each side.
  Loops on whole cycles like the first.
- `FlameStrip.luau`: labels overlap 0.7 (was 0.4) so the groups blend into one row; the heights follow one smooth
  noise along the row (neighbours close, 64-88 settled) instead of each label's own; the 9-slice base is 20 rows (the
  tongues' roots) instead of the old wall's 44.
- Photos: `docs/vfx/round18/ranked-flames-v913.jpg` (settled; mid-sweep held with `FlameStripHold`). Getting the panel up
  in a solo Play: `PlayTest = "play"`, `PlayTest = "open"`, then `JankfireRemotes.Play:InvokeServer("mode", "1v1", true)`.
  The Play menu's lobby camera binds after a Last+50 step: close it (`PlayTest = "close"`) before staging other shots.

## The Blood Cross, rebuilt as light (18 Nov 2026, place version 944)

The owner: "blood cross looks bad compared to the web version, the cross is too rectangular, I wanted it to be like cool
and vfx-ish". The old Roblox cross was two flat Neon bars (ProjClient `cross()`), the pop was Fx.blast. Everything you
see of it is now `client/BloodCrossFx.luau`, ported from the web's own `public/js/bloodcross.js` as energy and light:
- **Bolt:** a glowing dart turned nose-first (tapered FaceCamera Beams in three layers: red haze, the bolt colour, a
  white-hot core; the long tail is its trail), red haze and hot specks shed behind, a red light.
- **Stick:** an X of tapered blades (`vfx_xblade`) with a white-hot core (`vfx_xcore`), both drawn by
  `tools/roblox/vfx/xblade_sheet.py`; locked to the body, throbbing faster as the fuse runs; a spray of light where it
  went in.
- **Erupt:** spikes burst out through them along the X's diagonals (overshoot, settle, throb; three thorns each),
  light streaks off all four ends.
- **Pop:** a red glow growing to 6 m, a white-hot blink, light sparks, a hanging red haze, the blast ring on the floor,
  a short red light (1.6 over 14 studs: at 4 over 22 a frozen photo was a red room).
- **Walls:** a lit SurfaceGui X flat on the wall that pops in, throbs, sizzles and fizzles into a puff of haze.
- **You:** the X on your screen (pulse, burst, red flash), as the web's overlay.
- **Shadow Cross** (`bloodcross_shadow`) is purple throughout (web `PAL.shadow`), picked per bolt from the shooter's
  `Skins` attribute.
- **Content line:** no blood or gore (the web's splats, drips and stains are light, haze and sparks here), and the cross
  is always a saltire X or spikes on its diagonals, never the web's upright cross (the protected Red Cross emblem).
- Web reference frames: `ref_harness.js` effect `bc` loads bloodcross.js with blood off (sounds and HUD stubbed).
- Sheet: `docs/vfx/round19/blood-cross-v944.jpg`.

### The Blood Cross, upright and only light (place version 955)

The owner, on v944 (via main): "Web's upright cross", then "vfx looks good just make upright", and of the web's flat red
cross sign: "it would look better without it". So the shape changed and the look stayed: no sprite of a cross anywhere
(vfx_xblade / vfx_xcore are parked, and the dagger-cross sprites drawn in between were never used). The upright cross
is drawn only by tapered Beams of light (`crossArms` / `placeArms` in BloodCrossFx): the stuck mark is four small
blades round a hot point (up and sides 0.62 studs, down 1.45: never equal-armed), and the erupt is the same cross as
spikes with its crossing raised half the chest's height above the chest, so the long blade runs down through them to just
over the floor (thorns on each arm). Walls and floors get a soft scorch glow, a spray and a sizzle of light streaks, then
a puff. When you're the one crossed, your screen pulses red and flashes, with no symbol. The pop and the bolt kept v944's
look, with the critic's round 2 kept small: five thin streaks, sparks a little bigger, a slightly longer tapered trail.
Sheet: `docs/vfx/round19/blood-cross-v955.jpg`.

## The Seraph sniper's scope rim (18 Nov 2026, place version 988)

Scoped, a sniper hides itself behind FightHud's scope (black round a lens), so the Seraph skin's own effects can't
show there. `ScopeRim.client` (a new LocalScript) gives the scope the skin's touch instead, from a `scope` row on the
skin's `SkinSets.FX` entry: six soft gold rings round the lens edge (a little inside it, then out over the black,
breathing slowly), white feathers drifting in the black beside the lens (left and right, where there is most black),
and sparkles twinkling on the rim. Nothing goes further into the lens than the rim, so the crosshair and the view stay
clear. It only adds its own frames (`SkinRim`) under `PlayerGui.JankfireFight.Scope` and removes them when the scope
closes or the held skin has no row; FightHud itself is unchanged. It reads the held skin off Viewmodel (`VM.skin`).
Any skin can have one: `scope = { colour, glow = 0..1, bits = { texture = "feather" | "sparkle", colour, n, size },
shimmer = { colour, n } }` (size is a share of the screen's height). Only `sniper_seraph` has one so far.
Before and after: `docs/vfx/round19/seraph-scope-v988.jpg`.

### The Seraph effects on the aim tucks (checked on place version 989)

With hold-hands' tuck rows live (the rifle's `rwing_*` and the pistol's `slide_*` wing pieces shrink to 0.85 toward a
pivot as you aim, `TuckScale` on each piece), the effects ride them as built in v978. Aimed in Studio: the rifle has 20 of
49 emitters on (the rest are in the sight picture), and all 24 on its tucked wings stay on them, scaled with them. The
pistol has 0 of 24 on, because its wings sit behind the slide in the middle of the view. The burst has 24 of 24 on, with
its wings below the view. No change was needed. Photos (rifle, pistol, burst, aimed):
`docs/vfx/round19/seraph-aim-tuck-v989.jpg`.

## Every skin set's own shots (19 Nov 2026; pushed 22:18 UTC, the place save failed on Roblox's side)

The owner: "guns will have different vfx based off their skin!" Every gun in a skin set now flashes, traces and lands in
its set's theme, not only the twelve legendary skins. `SkinSets.SETFX` holds one row per set (`flash` and `tracer`
colours, `muzzle`, `bullet` and `impact` kinds); `SkinSets.fxOf(id)` returns a skin's own `FX` row with its set's
fields filled in where the row has none (cached), and Fx's `skinSpec` reads it, so a set gun with no row of its own is
now a registered skinned gun too. The legendary skins keep their own trails (their `bullet` wins); they gain the set's
flash drawing and impact.

| Set | Muzzle (`muzzle.kind`, drawing) | Tracer (`bullet.kind`) | Impact (`impact.kind`) |
|---|---|---|---|
| Seraph | `wings`: angel wings of light round a white-hot core, a feather flung off each side, a thin gold halo thrown forward | `feathers` | `halo`: gold flare, a halo ring flat on the wall, sparkles, a feather drifting down |
| Infernal | `inferno`: the flame tongues tinted, a burst of flame and embers flung up | `ember` | `embers`: a flame licking up the wall, an ember spray, a hot glow |
| Witching Hour | `hex`: five or six curling ghost-green wisps round a candle core, a violet smoke curl | `hex` (new): a pale green S-curved wisp, a violet smoke thread, motes | `hex`: a ghost-green flame lick, a violet puff, motes rising |
| Tidecrest | `splash`: a water splash crown, ink and water flung forward | `ink` (new): a dark dry-brush stroke (`vfx_ink`) with a thin gold line, ink dripping off | `ink`: the splash crown flat on the wall, ink drops, gold flecks, a gold ripple |
| Ducky (VIP) | `bubbles`: a warm core ringed with bubbles, a puff of bubbles | `bubbles` in gold (`bits`) | `pop`: the bubble ring flat on the wall, bubbles, drops |
| Ducky Classic | `hearts`: the flame tongues tinted pink, little hearts | `hearts` (each skin keeps its own) | `hearts`: hearts and sparkles bursting |
| Dust Drover | `powder`: a ragged black-powder flare, a powder puff (others' guns), sparks | `dust` | `dust`: a dust kick and a ricochet |
| Star Drover | `ring`: a hard-light ring and level streak, a ring thrown forward | `hardlight` | `ring`: a ring burst flat on the wall, a teal glow, thin sparks |

- **Drawings:** `tools/roblox/vfx/set_flash_sheets.py` (numpy + Pillow, nothing downloaded): six 2x2 flash sheets
  coloured as drawn (`vfx_mf_wings / hex / splash / bubbles / powder / ring`) and the ink strip. Fx holds one random
  variant per flash, as the tongues; wings and ring stay level (rotation within 6 degrees). The hex flash always has
  five or six wisps: a four-armed pinwheel could read as a symbol.
- **Impacts** play only where a shot meets the map (a short ray at its end, as the nails find the wall); a shot that
  ends on someone or in the sky keeps its trail kind's own small flourish. Shotguns: the set's impact on two pellets
  at most, and the pellets past the second draw their line with one bit at most (`cheap`).
- **Your own gun:** the muzzle's bits halve and nothing lingers in your face (no smoke puffs in first person).
- **Pools:** the sets' bits use their own emitter pools (`SETP`), coloured on every use, so they never recolour the
  older trails' pools.
- **Photo hook (Studio only):** `Fx.JankSetFx:Invoke(setId, at: CFrame, to: Vector3, only?)` fires a set's whole shot
  from anywhere (only = "muzzle" | "trail" | "impact" for each part at its best age). The photos fire all eight sets
  side by side at a client-only grey wall and freeze (`FxTimeScale = 0`).
- Sheets: `docs/vfx/round20/set-fx-design-sheet.jpg` (mocked from the sprites before building, for the owner) and
  `docs/vfx/round20/set-fx-ingame.jpg` (in Play, frozen: all eight sets side by side from above and behind; the muzzles
  from the front; the Witching Hour, Tidecrest and Ducky trails and impacts close up).
- Checked: the hook drew every muzzle, trail and impact kind with no errors; `SkinSets.fxOf` in Edit gave ar_lacquer
  splash/ink/ink, burst_infernal inferno/ember/embers, smg_pumpkin hex/wisp/hex (its own wisp kept), revolver_star
  ring/hardlight/ring, sniper_triangulum its own stars only, a skin in no set nothing. Not yet seen: a real set gun
  fired in first person (`JankTest arm` returned false in that test; to check on the next turn).
- The place save timed out twice (the console: "Server Save Failure: PublishService AssetUpload failed ... Internal
  server error", already failing before this turn); the change is in the Team Create session and the next good save
  carries it.

## Screen particles and the legendary reveal fire (20 Nov 2026, place version 1113)

Main for the owner, from a "particle 2D test" reference (thick fire, smoke and embers rising along the bottom of a
screen; the kind of look, not that artist's effect). Roblox has no GUI particles, so `client/UiParticles.luau` is our
own: emitters inside a Frame spawn recycled ImageLabels (flipbook cells by `ImageRectOffset`, size, colour and
transparency curves over life, speed in frame heights, direction and spread, acceleration, drag, sway, spin). One shared
RenderStepped connection exists only while something is alive; at most 360 particles on screen and 40 born a frame;
rates and bursts follow the settings' particle slider (`Fx.density`). `UiParticles.fromEmitter` / `play` read a pack's
world-space emitter (and its EmitCount / EmitDelay / EmitDuration) as a screen spec.
- **Legendary reveals (removed, place version 1127):** the owner, on seeing it: "No liked flame there just wanted it as ref", then "No fire for crates"; the picture was only a reference for screen particles. `LootOpening` no longer calls it. What it was: `UiParticles.fireStrip(frame, colour)` in the rarity colour, in a "RevealFire" frame along the
  bottom third of the opening's screen, under the reveal text. A hot glowing base, flame tongues (`vfx_flame_4x4`) about
  half the strip tall, dark smoke above, embers rising well over it. Lit in `LootOpening` when the prize is legendary
  (both the container opening and the VIP daily reward), out as the reveal goes away. Round 1 (v1109) was a row of small
  tips along the edge; round 2 (v1113) is the wall. Sheet: `docs/vfx/round20/legendary-reveal-fire.jpg`.
- Next places (main's list): finisher overlays (impact embers, speed sparks over the letterbox, with the
  cinematic-finishers session) and the rank-up and mastery-camo unlock screens.

## The bought VFX packs in the game (20 Nov 2026, place versions 1134 and 1136)

The owner: "we purchased the vfx lets use them when we can!!". The packs (BuiltByBit: coldd Development's Combat VFX and
Crimson Slash, skaterstudios' 100+ Combat VFX, artchive's Heart & Butterfly; Standard EULA, credited in
`shared/Credits.luau` and the settings' CREDITS tab; the raw files never go in git) are read offline and rebuilt as
templates in `ReplicatedStorage.JankfireVfx` (one Part per effect, no Blood folder). `client/VfxEmit.luau` plays them:
`VfxEmit.play(name, cframe, { scale, tint, parent })` clones from a pool, fires each emitter by the pack's own
EmitCount / EmitDelay / EmitDuration / TimeScale_* attributes (what the VFX Editor and Emit(n) plugins read), follows
the particle slider and emits at most 260 particles a frame. Which effect is used where: the shared table
`pack-effects-usage.md` in main's notes folder.
- **Hits (v1134, bigger v1136):** `Fx.blood` plays HitPunch1 facing the viewer, scale 0.5 to 1 by damage (x1 to x1.8
  past 25 studs so a far hit still shows), with a few pale sparks.
- **Parry and guard break (v1136; called since v1138):** `Fx.parry(at, dir, perfect)` plays GuardBlock (recoloured in
  the template from lime green to warm white, a pale gold glow and a cool white shield), 0.55 or 0.75 for a perfect
  parry, smaller up close (the defender's own blade), with the old sparks (40 / 26); `Fx.guardBreak(at, dir)` plays
  GuardBreak1's ring and GuardBreak2's burst with sparks. Arsenal.client's Fx "parry" handler calls them (the katana
  session's pointer): a guard's first hit or a perfect one gets Fx.parry, a sword swing parried Fx.guardBreak, a
  spray's later bullets only the small sparks (an 18-round spray would be 18 flashes). Everyone sees them.
- **Hard landings and slides (v1136; called from Steps.client since v1137, the sounds session's 13537f5):** `Fx.land(feet, fallSpeed, mine)` plays
  HitSlam at 0.12 to 0.28 as a ring of dust puffs, only past 42 studs/s (a plain jump lands at 27.6);
  `Fx.slide(feet, look, mine)` plays DashPuff at 0.4 (a soft glow and streaks thrown behind; tinted grey it all but
  vanished, so it stays white). Your own are only shown in third person; none past 160 studs. Jump pads keep their own
  `PadFlare`.
- **Black-backed textures (v1138; main, after kill-effects hit it on Static in v1133):** a texture with a black (or
  dark, low-alpha) background shows that square whenever its emitter's LightEmission is under 1, a dark fringe or slab
  on a light floor or wall. Such an emitter gets LightEmission 1 (black adds nothing) and is kept quiet through
  Brightness (at most 2) and 30% more transparency; the pack's negative-LightEmission dark layers are left alone unless
  their texture is listed as `dark_too` (HitPunch2's black fringe); `dim` textures (already at 1, a faint background
  that shows as a pale quad under a big Brightness: GuardBreak1's hexagon) only get the Brightness cap. Which textures:
  checked on a mid-grey screen in Play (every template texture as an ImageLabel), listed in
  `tools/roblox/vfx/packs/black_backed.json`. The rule is `black_fix.luau` there, and the template builder
  (`pack_templates.py`, which reads a pack offline) applies it to every template it builds; 10 emitters in the Combat
  templates got it (HitPunch2, GuardBreak1, HitSlam x4, Slash4 x4; each keeps a BlackFix attribute with what it had).
  Every sheet is shot on mid-grey as well as dark now (black halos hide on dark). Sheet:
  `docs/vfx/round20/pack-black-fix.jpg`.
- **Explosions (v1184):** `Fx.explosion` plays the 100+ pack's burst #40 (template `BlastBurst`) facing the viewer:
  a white star of spikes inside a shock ring for the first 0.15 s, over our fireball (its middle is open, so the fire
  shows). It is scaled to `clamp(0.11 R, 0.4, 3.5)`, about 0.43 R across the ring, and shows on the frag, the Chicken
  Rocket and Overdrive. It was picked from the photographed pack (`docs/vfx/catalogue100/`, 96 effects numbered as the
  builder's `#n`).
- **Ducky Classic hearts (v1184):** the set's muzzle, bullet and impact hearts use the Heart & Butterfly pack's heart:
  a 4x4 one-shot flipbook of a glowing outline heart (`TEX.packheart`, always LightEmission 1). Fx has a new skin
  particle kind `heart`. The Ribbon Duck katana (`katana_ducky`) gets a heart rising off its pommel now and then, and
  sheds hearts on its swings and hits; it shed gold sparkles before.
- Sheet: `docs/vfx/round20/pack-blast-hearts.jpg`.
- **The Infernal katana's wave (v1189):** the wave opens with the Crimson Slash pack's slash (template
  `CrimsonSlash`): a crimson crescent ring with dark edges and a dark streak along its top, gone by 0.3 s. Others see it
  3 studs out at 0.75 scale (the wave's 6 m); your own sits 10 studs out at 0.45, or it fills your screen.
  - **Calls:** Katana.client calls `Fx.skinWave(thrower, from, dir, startIn)` in two places, as your own wave is drawn
    and as anyone's wave event arrives. Fx checks the thrower's katana skin (`GunSkins.skinFor`; the table `WAVE_SKIN`)
    and plays `Fx.crimsonSlash`.
  - **Facing:** the pack's crescents lie across the emit direction, so the part's top points at the viewer and everyone
    sees it face on. Seen from the side, as in the first catalogue shot, only its red dots show.
  - **Sheet:** `docs/vfx/round20/crimson-slash.jpg`.
- Photos: Play stage, clones fired by their attributes and frozen with TimeScale 0 (VfxEmit parks an effect after
  its life, too soon for a capture). Sheets: `docs/vfx/round20/pack-templates-1.jpg`, `docs/vfx/round20/pack-batch2.jpg`.

## World finishers (20 Nov 2026, place versions 1244 to 1289)

The owner (relayed by main): finishers should be "more like kill effects", using the VFX we bought, and "finisher
cutscene should only play when you get the final hit on the game winning round and otherwise it can be like a
valorant weapon finisher instead". So each finisher skin got a **world finisher**: about 2 s on the victim's real
body, seen by everyone from their own view, with no camera, screen or HUD effects. The cinematic stays for the
match-winning kill only (routing: the finishers session, v1242; `FINISHERS.md`).

- **Study:** the vault's `Research\Valorant finishers.md`: what Valorant's in-world finishers do (a themed effect at
  the body, 1.5 to 3 s, readable from any distance, no camera), the rules we took from it, and our eight. Inspired by,
  never copied: no names, shapes, art or sounds of theirs. No frames were saved.
- **Module:** `src/client/FinisherWorld.luau` (interface in the notes folder's `world-finishers.md`). `FW.play(id,
  victim, opts)`; one STEP function per finisher, run every frame on the body's own parts (moved, faded, shelled) plus
  our own parts, beams and emitters in `workspace.JankWorldFinisher`, all destroyed at the finisher's length. Past
  600 studs from the camera it only hides the body. `WorldFinisherTimeScale` (0 to 1) freezes or slows every running
  finisher for photos.
- **The eight:** Ascension (Seraph AR: lit white, rises into a shaft with feather wings, bursts into feathers under a
  gold halo), Hellgate (Infernal AR: cracks, a fire ring, chars and sinks into a black hole, then a dark-red streak
  plume as the hole shuts), Splashdown (Ducky sniper: whirlpool, spins down the drain, a splash crown, a rubber duck
  bobs up), High Noon (Dust revolver: a sand twister erodes the body top-down, a tumbleweed rolls through), Inkfall
  (Sakura katana: one ink stroke, the top half slides off, both halves go to petals), Warp Out (Star revolver: a teal
  ring opens behind it and yanks it in, snapping shut in a crackle), Lantern Light (Pumpkin SMG: a pumpkin closes over
  it, its carved face lights, it pops in a warm cloud), Starchart (Triangulum sniper: night-blue, stars on the joints,
  lines between them, the constellation rises).
- **Photos:** a Play stage 900 studs up, five copies of your own character at five ages (each finisher started that
  long before a freeze), plus all eight from about 100 studs. `tools/roblox/vfx/world_sheet.py` stacks the strips.
  Rounds 1 to 8 are in `docs/vfx/world/` (round 8 = the final check, v1289); a separate critic agent scored every round. Before/after sheet: main's notes
  folder, `world_finishers.jpg`.
- **Scores (critic, out of 10), round 1 to round 7:**

  | Finisher | R1 | R2 | R3 | R4 | R5 | R6 | R7 | final |
  |---|---|---|---|---|---|---|---|---|
  | Ascension | 5 | 6 | 7 | 8 | 8 | 8 | 8 | 8 |
  | Hellgate | 4 | 7 | 7 | 6 | 5 (errored) | 7 | 8 | 8 |
  | Splashdown | 6 | 6 | 6 | 7 | 7 | 8 | 8 | 8 |
  | High Noon | 4 | 4 | 5 | 7 | 8 | 8 | 8 | 8 |
  | Inkfall | 3 | 5 | 5 | 6 | 7 | 8 | 7 | 8 (round 6's cut restored) |
  | Warp Out | 5 | 6 | 6 | 7 | 8 | 8 | 8 | 8 |
  | Lantern Light | 6 | 7 | 6 | 8 | 8 | 8 | 8 | 8 |
  | Starchart | 5 | 7 | 8 | 8 | 8 | 8 | 8 | 8 |

- **Polish the critic would still do:** Ascension's feather burst wider (about 1.3 body heights); Starchart's lines
  drawn visibly head to feet; High Noon's tumbleweed rounder with a visible spin; Splashdown's crown with 8 to 10 crisp
  droplets and a faint blue; Inkfall's ink on the cut as a tapered brush line with a soft pink (round 7's solid bars
  read as a censor bar and were taken out).

### Lessons
- **A VelocityParallel streak flies along its texture's u axis.** Our streak and spark textures are drawn along v:
  give them Rotation 90, or a crown or plume flies sideways (the PLAYBOOK rule; broken and fixed again in round 6).
  Squash on such a streak turned it across its flight too.
- **A soft streak texture at a large size is a blob.** For a plume, use the hard thin spark streak, end its colour
  dark and transparent, and paint (LightEmission 0.1, Brightness 1) rather than add. A bright additive red ball is the loudest
  thing on screen.
- **A Highlight's fill draws over beams and particles on the body.** Ink across a highlighted body has to be
  geometry in front of the body's measured front, or it only shows where it sticks out. And a solid bar there reads as
  a censor bar: taper it, or leave it out.
- **Split a body by limb, not by height.** Arms hang past the waist; a part left behind stretches across the gap (the
  "white connecting line" in Inkfall's round 5).
- **Beam rings: segments two chords long, overlapping by half.** A tracer texture fades at its ends, so short
  segments read as beads.
- **Two values must not share a key.** `pour(r, key, ...)` keeps its running count in `r.s[key]`. A pour key equal to
  a part's name (`s.cone`) added a number to a Part and stopped the finisher mid-way (round 5's Hellgate).
- **A flipbook flame fills only part of its frame.** To get a flame a given height, size the particle about 2.5x that.

## Anime weapon effects (26 Nov 2026; installed in place v1372 with AnimeFx.ON = false until a real swing is tested)

The owner (25 Nov): "learning from the given references can you try to make better vfx? I heard you can do it in
blender?.. Don use too many meshes you usally end up making things looking to gemoertical otherwise use the roblox
plugins to make vfx ... watch tutortials for making anime style vfx, especially applioed to weapons!" The study of his
references is in main's notes folder (`vfx-refs-study.md`, `vfx-refs-study-web.md`).

**The method.** Shapes are Blender-rendered FLIPBOOKS played on camera-facing particles (no meshes in the game: a mesh
ribbon like the old katana WedgePart smear is what "geometric" means). Sparks, the twinkle and the impact frame are
code. Every effect is planned as a timeline in which each frame has a job, rendered offline, composited the way Roblox
will draw it, and scored by a fresh critic agent until it reaches 8; only then does it go to Studio.

- **Tools** (`tools/roblox/vfx/anime/`):
  - `slash_bl.py`: the slash. Ribbons on a plane under an orthographic camera; ALL the animation is in their shaders,
    set frame by frame from Python (head, tail, band width, core, teeth, strands, ink). A spec picks the take: arc,
    width, tilt, mirror, spiral, teeth depth, where the blade-light line is thickest.
  - `burst_bl.py`: the hit burst. Flat geometry rebuilt every frame (star, crescents, shards, needles).
  - `sheet.py`: `pack` (16 frames into a 4x4 sheet of 256 px cells, 2x renders box-downsampled premultiplied, every
    cell alpha-bled) and `preview` (the frames composited as Roblox draws them, tinted, on mid-grey and near-black).
  - `repack.py`: any flipbook into a Roblox grid, game-vfx's steps without ffmpeg: keep the live frames, skip a
    burst's first white frames (`--from`), pick frames on an eased clock (`--ease`), one crop round everything the
    effect touches, black to alpha (`--black`), soft cell edges, 4x4 of 256 px or 8x8 of 128 px.
  - `mad.py`: the error number (after AnyVFX): mean absolute difference per channel, 0-255, between a reference frame
    and our capture, aligned on their bounding boxes, at full size and after an 8x downsample.
- **Layers.** Every flipbook renders three layers from the same timing, played together from one part (AnimeFx
  `flipbook`):
  - body: greyscale 0.55-0.7, tinted per weapon. It is drawn twice: painted underneath (LightEmission 0, so the colour
    survives on bright floors) and added on top (warm tints at 0.45, because red clips first).
  - core: white-hot, added, untinted.
  - ink: black accents, painted over (the two-tone anime look).
- **The slash** (6 sheets x 3 layers): takes A (165° arc, flat), B (135°, tilted 55°, teeth 16 %), C (200°, a tighter
  spiral 0.65), each with a MIRRORED copy (a particle can't flip its texture; the mirror makes a right-to-left swing
  bulge the right way). 16 frames: f0 a fat lead-in with a pointed head; f1 the flash (mostly white); f2-4 the hold
  (the white pulls back along one diagonal to the rim; code pushes it from 92 % to full size); f5-7 the tail wipes to
  the head while the band thins and the back teeth deepen; f8-12 one tapered blade-light line that overshoots the head;
  f13-15 empty. Critic: 4 → 7 → 8 (A), 8 (B, C) over four rounds.
- **The hit burst** (1 sheet x 3 layers, drawn at 80 % of its cell for margins): f0 a four-point star of concave needle
  arms (its long axis level: the game can turn it along the slash), held on f1 at 65 %; f1-2 three tapered shockwave
  crescents (uneven angles, lengths and radii: never a ring, never a logo); f1-3 three long black needles; f2-6 blade
  slivers (one straight dark side, one curved coloured side, white on the leading tip behind a slanted edge) fly out;
  f7-11 they keep flying, thin, and go; f12-15 empty. Critic: 6 → 7 → 7 → 7.5 → 8 over five rounds.
- **In the game** (`client/AnimeFx.luau`, switch `AnimeFx.ON`):
  - your own swing in first person: the blade tip's path in camera space (Arsenal's smear window) gives the swing's
    direction on screen and which way it curves; after the 4th sample one slash rides with the camera
    (`AnimeFx.ownSlash`); the old WedgePart smear stands down;
  - anyone's swing seen from outside, and yours in third person: `AnimeFx.bodySlash` in front of the body at the clip's
    smear time, the chain's link picking the direction;
  - your own hit: `AnimeFx.hit` = the burst, sparks (velocity-stretched streaks, white into the tint, gravity), and on
    a heavy hit the twinkle and a 0.07 s black-and-white impact frame (off with SCREEN SHAKE).
  - weapon tints and sizes: `TINT`, `FP_SIZE`, `REACH` in AnimeFx.
- **The VFX LAB** (`client/VfxLab.client.luau`): Studio or the place's creator, F6 or "/vfx": every effect with PLAY and
  LOOP, speed 1x / 0.5x / 0.25x / 0.1x / FREEZE, the melee tints, a still dummy, and first-person swings both ways.
  The workspace attribute `AnimeFxTimeScale` freezes the game's own copy for photos.
- **game-vfx's library** (Patch's skill, MIT code, CC0 art; the clone is in the vault, never in git): its 12 flipbooks
  repack to Roblox 4x4 sheets with `repack.py --from 3 --ease 0.6`; they are realistic fire, smoke, lightning and magic,
  for the gun and ability effects, not the anime slashes.

### In game (Studio, 26 Nov evening): what changed after the first real swing
- **Judge in game, not just offline.** The Blender slash passed the offline critic at 8 but read 4/10 in first person on
  the bright training range ("four stacked, see-through pale arcs ... a ghostly wind smear"): its white core covered most
  of it and its additive layers washed out. The bullet pop, PAINTED and coloured as drawn, held up. So:
  - `ingame_sim.py` composites a sheet's frame onto a clean Studio capture of the same view with the game's own blend
    (painted / added), at the in-game size; the critic judges that, and only then does it go to Studio.
  - **The slash is now 2D** (`slash2d.py`, sheets `slashp_a/b/c` + mirrors, `painted = true` in AnimeFx.SHEET): one
    opaque crescent with a spiral outer edge, a white band on the outer leading edge (30 %), a saturated tint behind
    (katana 70, 160, 255), a tapered ink line on the inner trailing edge, one echo peeling off the inner edge
    tangentially; f0 a white sliver, f1 white, f2-4 hold, f5-6 tail wipe, f7-10 a shrinking curved sliver off the head.
    Critic in the in-game simulation 7 → 7 → 8 (the echo first read as a second blade, then as a hook / bird's wing).
    The Blender sheets stay in SHEET (the lab's "OLD BLENDER SLASH").
  - **Sparks** were soft stadiums flying 8 studs, past the camera ("white leaves, rice grains or feathers"): now a hard
    comet (`spark2d.py`, head up), 5-7, a 35° cone away from the camera, under 3 studs of travel.
  - **Bullet dust**: the old soft tan DUST next to the cel pop clashed ("blurry, muddy"): `Fx.impact` plays the cel puff
    (`IMPF`, MPUFF's sheet) at half the pop's width, behind it, 0.04 s late. DUST stays for landings and slides.
- **A particle's positive Rotation turns it ANTICLOCKWISE on screen.** AnimeFx assumed clockwise (`ROT_SIGN = -1`), so
  slashes swept and bulged the mirror way; seen in the v1372 stage slashes (bulging up, not down) and a side-wall pop
  that opened the wrong way. `ROT_SIGN = 1` and the pop's roll flipped (`math.atan2(v.Y, v.X) - 90`).
- **Command-bar `require` makes a second module copy:** setting `AnimeFx.ON` from execute_luau changed nothing in the
  game's swings. Tests flip the game's copy with the workspace attribute `AnimeFxOn` (and `AnimeFxSparkRot`).
- **The first-person slash's centre** came from the blade tip's projection, which starts near the lens and landed it
  off screen: it is clamped near the middle of the view now. **The hit burst** was drawn at the body's centre and hidden
  by it: it is pulled 1.4 studs towards the camera.
- **Freezing a gun test with FxTimeScale = 0 stacks flashes:** shots fired after the freeze never age, so 4-6 flashes
  pile up into a blurry many-spiked sunburst. Freeze on one tap and let go.

### In game, turn 3 (Studio, 27 Nov 01:27-01:35 UTC, place version 1409)
- **The rotation sign is confirmed:** three bullet pops on a grey wall in Edit at Rotation 0 / +90 / -90 opened up / left
  / right. `ref_frame.py` now turns cells the same way. The clean error number for the pop on that stage (design f0 vs
  Studio, `mad.py`): 8.4-9.5 full, 6.2-7.3 after an 8x downsample, the same at all three rotations; with the old sign
  the +90 one measured 36.6.
- **The painted slash plays** (take A seen frozen): one opaque blue crescent with its ink line, riding with the camera
  beside the blade. Its white core layer did not load in that frame ("Asset content representation is being
  generated" in the console, hours after upload, though PreloadAsync said Success): the next capture checks it.
- **The slash fired on 1 swing in 3 at Studio's 15 fps:** Arsenal fired `ownSlash` after 4 blade-tip samples inside
  the clip's trail window, and kat_light1's window is 0.096 s (1-2 frames at 15 fps, ~3 at 30). Now an unfired swing
  adds the tip on the first frame past the window (and the frame before it, when it has only one sample) and fires
  with those.
- **The cel dust** shows 0.13 s after a shot as a few small tan puffs; the pop at 35 ms reads as a hot star.
- **The muzzle flash cannot be frozen at 15 fps:** its life is under one frame there (the v1391 capture stands).
- **The critic on those captures:** slash 6 (about 8 expected with its core), burst 4, sparks 6, pop 5, "cel dust" 3.
  What followed:
  - **A slash layer's ink sat 10 px off its body:** every layer was its own emitter on a 0.2-stud part, and a part's
    emitter spawns each particle at a random spot inside the part. AnimeFx's layers now emit from one Attachment
    (a point), so body, core and ink register.
  - **The burst is a painted 2D drawing** (`burst2d.py`, `burstp_a`): a white flash star, then five concave needles
    with white streaks, a jagged white core, three ink wedges and two broken shock arcs, breaking into flying shards.
    The Blender `burst_a` stays in the lab as "OLD BLENDER BURST".
  - **Sparks are two painted emitters** (`spark2d.py` rim + core): a tinted shard with a white core at half its width.
    AnimeFx feeds them one spark at a time, turning their Attachment and setting the same Speed and Lifetime on both
    before each `Emit(1)`, so each core rides inside its rim. They shrink out, never fade.
  - **The "dust smudges" were the web's 10 soft chip flakes,** not the cel puff: 4 while the pop is on. The pop's
    "yellow glow" was the revolver tracer's end; the pop itself measured 9.5 on the clean stage.

### In game, turn 4 (Studio, 27 Nov 02:40-02:47 UTC, place version 1423)
- **Flipbook frame blending was the "soft, see-through" look.** `ParticleEmitter.FlipbookBlendFrames` is on by default
  and cross-fades each frame into the next, so at any moment a cel effect showed two drawings half see-through: the
  slash's "translucent" body, its "feathered" inner edge and its doubled ink. AnimeFx's layers turn it off (Fx's pools
  already did). Seen by switching it off on a frozen frame: `studio_slash_blended_v1409code.jpg` vs
  `studio_slash_crisp_v1423.jpg`.
- **A hit's effects faded into the body they sat in** (pale and see-through on the dummy, solid against the sky):
  the burst and sparks render up to 2 studs nearer the camera (`ZOffset`, which keeps their size on screen;
  `AnimeFx.nearZ`, never past 0.6 studs from the lens). `studio_hit_near_v1423.jpg`, `studio_hit_v1423.jpg`.
- **The low-frame-rate slash, second half:** a new swing of the same clip was noticed only when its first sample in the
  trail window came earlier in the clip than the last swing's last sample; at 14 fps half the swings looked like the
  old, already fired one. Arsenal now tracks the clip's time on every frame and starts a new swing when it goes back.
  Measured with the client forced to 14.7 fps (a busy-wait in RenderStepped): 5 of 5 swings fired (2 of 5 before).
- **Testing at a low frame rate:** Studio's client throttles to 15 fps when unfocused; to force it, burn ~58 ms in a
  RenderStepped handler from the client command bar, and disconnect it after.
- **Turn 5 (place v1431, 03:11 UTC):** the critic's last two (burst 7, sparks 7): the burst's two shock arcs read as
  strays (a "blue headband" over the target's eyes) and are cut (`burst2d.py` ARCS = []; only the body sheet changed);
  sparks 1.5x. Hit photo `studio_hit_shards_v1424.jpg`; a 13.7 s first-person clip went to main's notes folder.

### The blade sweep: effects on the weapon's own plane (27 Nov 2026, place version 1448)
The owner: "make sure the effects follow the plane of the weapon and katana for example, are attached along the side
of the blade". The crescent was a card facing the lens; a melee swing is now a SWEEP (`AnimeFx.sweep`, STYLE "blade";
"card" keeps the old crescent, workspace attribute `AnimeFxStyle`):
- **What it is:** every frame of a swing the blade's `Mid` (45 % along it) and `Muzzle` (the tip) are sampled (every
  melee weapon has both; the katana's kill stretch moves its Muzzle) and a chain of flat Beams (FaceCamera off) runs
  through the samples: the ribbon lies in the plane the blade swept, its outer edge on the tip's path. Cross-section
  from `sweep2d.py`: a thin tinted rim, a white band on the outer edge, the tint, an ink line on the inner edge. The
  oldest 30 % of the path tapers to a point and fades; a four-point glint rides up the blade to the tip and pops there.
  First person samples in camera space (it rides with your view); third person and other players sweep the blade their
  body holds (the `TPGun` under the character), so it is seen from wherever you stand.
- **Beams, measured on a test beam in Edit:** a non-facing Beam's width runs along its attachments' Y axis; its
  texture's ROWS run along its length and its COLUMNS across its width, the left column on the +Y edge. (The first
  upload had the cross-section in rows: a stripe ran across the beam.) `BEAM_AXIS`/`BEAM_FLIP` hold the result.
- **The katana's first-person trail window is its WIND-UP** (the tip over your head and behind the lens): the cut
  comes after it. The sweep therefore keeps the CUT itself: samples count while the tip moves faster than 25 blade
  spans a second; a slow tip before a run is still winding up, after a run of 1.5 spans the cut has ended; first person
  drops a tip within 1 stud of the lens (and starts the next run afresh); a turn over 60 degrees starts it afresh.
- **First person faces the lens:** the true plane, drawn literally, blew up across the screen (the blade passes by your
  eye: `studio_sweep_fp_trueplane_first_try.jpg`), and seen edge-on it was a thread. In first person the ribbon keeps
  the tip's real path but turns its width to face the lens, on the blade's side, 55 % of Mid-to-tip wide.
- **Corners:** sparse samples made an angular V (`studio_sweep_side_corner_first_try.jpg`): Catmull-Rom points are
  added where the path turns over 12 degrees.
- **Seams:** where two segments meet, edge anti-aliasing showed a line; overlapping them let the next segment's blue
  draw over this one's white (per-beam sorting), and a ZOffset on the core moved it off the body (ZOffset shifts along
  the camera's look, not the view ray). Now the bodies meet exactly and only the cores overlap their neighbours.
- **The hit follows the swing:** the burst's longest shard points along the blade's motion on screen and the sparks fly
  on along it (`AnimeFx.swingDir`). **Guns:** someone else's front flash now faces down their barrel as yours does
  (VelocityPerpendicular); the side jet was already two crossed cards on the barrel and the puff already leaves along it.
- **The lab:** WEAPON SWING swings each melee weapon on a posed copy of you (a ThirdPerson test rig, `TPRig` +
  `TPWeapon`), side-on 8 studs ahead; walk round it or freeze it. STYLE: BLADE / CARD for before and after.
- Captures: `studio_sweep_fp_v1448.jpg`, `studio_sweep_tp_v1448.jpg` (the shoulder camera: the plane near edge-on),
  `studio_sweep_side_v1448.jpg` and `studio_sweep_top_v1448.jpg` (the same frozen ribbon from the side and above).
- **Round 2 (place version 1454), after the critic's 6/10** ("tape or a ruler" in first person; from the shoulder
  camera "a dotted thread ending in a chevron"): a crescent profile along the ribbon (nothing at the tail, fullest at
  70 %, closing to a point 5 % of its length past the tip); first person bows its path out by 7 % of its length; from
  outside, the width turns towards the viewer the more edge-on the swing's plane is (the blade's own plane when open to
  the camera); never under 7 px across where fullest; the white core at Brightness 1.25. Captures
  `studio_sweep_fp_v1454.jpg`, `studio_sweep_tp_v1454.jpg`, `studio_sweep_side_v1454.jpg`.
- **Round 3 (place version 1459), after 7/10 for first person and the side** ("both edges kink ... a joined
  polyline", seams fanning at a tight curl; the shoulder view already 8): the path is resampled so no piece turns more
  than about 8 degrees (a segment gets up to 8 Catmull-Rom points, as many as the sharper of the turns at its ends
  needs); the first-person bow comes after. Captures `studio_sweep_fp_v1459.jpg`, `studio_sweep_side_v1459.jpg`,
  `studio_sweep_tp_v1459.jpg`.
- **Round 4 (place version 1468), first person and the side at 8, the shoulder view of one swing 6** (its head "folds
  back on itself ... a U-turn arrow"): a turn (over 60 degrees in a step, or 100 within three) that heads BACK against
  the run so far ends the ribbon after a real cut (the return stroke is never drawn); any other turn starts a new
  stroke (third person's blade comes down, then sweeps round: ending there instead dropped the cut). Where the path
  curls tighter than the band, towards the band's side, the band's inner offset is held to 0.8 of the local radius.
  Captures `studio_sweep_tp_v1468.jpg`, `studio_sweep_side_v1468.jpg`.
- **Round 5 (place version 1479):** that swing's bent lead-in still stood in the tail as an angular bar ("a 7 or an
  ice axe"). Tighter restarts (45/75 degrees) chopped the swing's own curve into a shard, so they went back to 60/100;
  instead the oldest 12 % of the ribbon shows nothing and the width grows in after it. `studio_sweep_tp_v1479.jpg`.
- **Round 6 (place version 1487):** the lead-in was longer than any fixed share, so the ribbon now shows only from the
  lead-in's last sharp bend (the last sample where the tip turned over 45 degrees within three steps, in the first 60 %
  of the path) and the crescent grows in from there; nothing restarts. `studio_sweep_tp_v1487.jpg`,
  `studio_sweep_fp_v1487.jpg`.
- **Round 7 (place version 1497), after the shoulder view's 7** ("a sawtooth notch in the inner ink edge, mid-arc, where
  the curl clamp kicks in"): after the clamp, the width changes by at most a tenth of the widest piece from one piece
  to the next (both ways, only ever lowering the neighbour, never raising a clamped piece, which would fold again), then
  a 3-point smoothing that also only lowers; the centre line is rebuilt from the smoothed width.
  `studio_sweep_r7_shoulder.jpg` (+ `_crop.png`), `studio_sweep_r7_fp.jpg`.
- **Round 8 (after round 7's shoulder 8 but first person 6):** a cap per PIECE starved short paths: first person's
  ~10 pieces peaked at about a third of the width (12 px against 35). The cap now applies only when the curl clamp held
  a piece in, measured per LENGTH (the widest per fifth of the visible length, steeper than the crescent's own
  profile). The lower-only smoothing runs only within two pieces of a clamped piece. Swings with no clamped piece draw
  as in round 6. `studio_sweep_r8_fp.jpg`, `studio_sweep_r8_shoulder.jpg`, `studio_sweep_r8_shoulder2.jpg` (the
  combo's second and third swings).

### Lessons (the critic loop)
- **"Geometric" has a list of tells:** constant-radius arcs, symmetric widths, perpendicular cuts (a chord-cut head, a
  flat strand end, a straight base on a shard), rectangular steps, perfect rings, evenly spaced parts (a trefoil reads
  as a logo), lens or leaf shapes. The fixes: spirals, asymmetric profiles, comet tapers, raked teeth, pointed ends,
  slanted seams, uneven angles and lengths.
- **Grain in Cycles comes from two places:** coplanar transparent ribbons (z-fighting: lift each off the plane), and
  half-transparent fades (Cycles resolves the mix stochastically). Shapes leave by wipes and shrinks, not fades.
- **Render at 2x and box-downsample premultiplied;** nothing thinner than ~3-4 px at 256 should live past two frames.
- **Keep every pixel 6+ px inside its cell** (a 4x4 sheet bleeds neighbours under filtering): fit the camera
  orthographically to the effect's bounds, and check the alpha at the cell edges after every render.
- **A white additive blob vanishes on a bright sky:** keep a tinted rim outside the white.
- **The peak needs mass:** the critic measured shard widths by erosion; thin is right only for the exit.

- **The muzzle flash** (`mflash_bl.py` + `flash_sheet.py`; Fx `TEX.mflash/mflashN/mside/msideN`): four 2x2 drawings
  a view, composited body + core into one picture (Fx shows one random cell per shot), warm as drawn and a grey copy a
  skin's flash colour tints. FRONT: a soft-lobed hot core (two harmonics, the largest lobe 1.6x the smallest) with 4-6
  flame petals, one or two dominant. SIDE: a jet pinched at the muzzle, widest at 40-50 %, its front a convex curve with
  3-4 unequal triangular tongues and V notches (no straight wall), the white a hot bulb with two unequal off-axis prongs,
  at most one flame petal. No black (it read as soot on a flash): a deeper band of the same tint on every rim. Critic:
  front 6 → 8, side 5 → 6 → 7 → 8. `flash_sheet.py` measures the side drawings for Fx (`SIDE_X0/X1/TH` 0.068 / 0.889 /
  0.292); the drawings fill their cells, so the front's size factor went 1.8 → 1.3. The Kenney tongues' ids are kept in
  a comment by `TEX` for a one-line revert.
- **The puff** (`puff2d.py`, 2D numpy at 4x supersample; Fx `MPUFF`): metaballs in Blender read as clay and pearls, so
  the puff is drawn flat: hand-placed round bumps (a dominant one, a trailing one, a crown, an uneven bottom row), two
  flat tones with the shadow low and on the outer left (23-27 % of the area), an occlusion rim, satellite mini-clusters
  on f3-8; it splits into three contiguous little clouds that shrink to 40 % and are gone from f12 (a cloud that shrinks
  away, not a fade). Light islands under 40 px are folded into the shadow (`drop_light_islands`). The light is drawn
  from the upper right, so in Fx it turns at most 10° and never spins, and its frames are not blended. Critic: 5 (clay)
  → 6 → 7 → 8.
- **The bullet pop** (`pop2d.py` + `sheet.py comp`; Fx `POPS`, `popAt` in `Fx.impact`, not off dirt or cloth): one
  PAINTED sheet (orange ff8719, a deep d75a0a edge, white, black), 16 frames over 0.32 s, live on f0-f3. The drawing's
  up is the wall's normal and its hit point sits 0.4 of a half-width below the cell's centre (the spray only goes
  outward): Fx rolls the particle to the normal's direction on screen and moves it along that up by 0.4 x its Size.
  f0 a white splash crown of six concave needles (long ones ALONG the wall, none into it) with the deep edge; f1 the
  same orange with a white streak up each needle's middle, two black shards in the gaps, four lines growing out of the
  needles' tips; f2 the star at 35 % and the lines full, tails at the core; f3 the heads fly on as the lines shorten.
  A mirrored sheet on every other hit, the roll +-20°, the size 75-100 % (a shotgun reads as a spray, not a stamp).
  Critic 4 → 6 → 8: round 1 was a bird's foot / potted plant (short side spikes, a stub into the wall, a box core);
  round 2 had hairline orange and floating line pieces. `Fx.POP_ON = false` turns it off.
- **The error number (MAD)** after AnyVFX: `ref_frame.py` composites a sheet's cell on the background sampled from a
  Studio capture, turned by the particle's Rotation; `mad.py` compares it with the capture (per channel 0-255, at full
  size and after an 8x downsample). It measures what the game's drawing loses against the design.
- **The library in the lab:** six of game-vfx's CC0 flipbooks (fire burst, big explosion, smoke burst, lightning, frost,
  arcane) repacked and uploaded (`AnimeFx.LIB`, ids in `assets/vfx/anime.json`), playable in the lab next to ours. They
  are painted-realistic, not anime: candidates for a rocket's blast or the taser's arc, not used by any weapon yet.
- **The lab plays with the switch off:** `AnimeFx.LAB` is true while the lab is open (the effects check `ON or LAB`);
  its speed buttons slow Fx too (`Fx.setTimeScale`), so the gun's flash and puff can be watched at 0.1x.
- Round sheets: `docs/vfx/anime/`.
