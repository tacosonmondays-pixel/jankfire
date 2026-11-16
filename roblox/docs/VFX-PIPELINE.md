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
one-shot flipbook plays at most 30 frames a second (so short-lived effects use 16-frame sheets); `FlipbookBlendFrames`
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
| duck hole layers | `Fx.holeOpen(id, at, R, age)` / `Fx.holeMove` / `Fx.holePop(id, at?, r?)` | Utility hole functions |
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

- the model's own shape in a calm tint (Neon, see-through), its drawn skin set aside and put back on remove;
- a rim (Highlight fill + outline, depth-occluded);
- scanlines (a Blender-drawn soft line, `vfx_lines`, as Textures on each part, drifting up);
- a bright band sweeping up through it every few seconds, a faint flicker, the odd glitch slice flaring;
- optional projector (`projector = lensCFrame`): a soft cone of light up to the model, motes rising in it, a glowing lens;
- a scan-in build (a bright line rising, the pieces lighting up as it passes) and the reverse on remove;
- optional bob and turn round `pivot`.

One RenderStepped for all; nothing updates past 260 studs; in Studio it obeys `FxTimeScale` so the capture loop can
freeze its build. Highlights are capped at 31 on a client: a hologram uses one.

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
- **Rubber Duck hole:** a bright rim facing you (light bent round the edge), dust spiralling in, a flash and floor ring
  when it pops.

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
- A one-shot flipbook plays **at most 30 frames a second**: 64 frames over a 1.5 s fireball (or a 0.7 s puff) played
  too slowly, so the fireball was a dot at first and the muzzle puff never showed. Short-lived effects now use 16-frame
  sheets (`vfx_boom_4x4`, `vfx_smoke_4x4`) with `FlipbookBlendFrames` on.
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
