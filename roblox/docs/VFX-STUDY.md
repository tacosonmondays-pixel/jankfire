# VFX study notes: techniques from three open-source Roblox VFX references

Read on 17 Nov 2026, as research the main session approved: three MIT-licensed GitHub repos, read as text on the
web. Nothing was cloned, installed or run, and no art was taken. Everything below is in our own words, with a source
line for each. It only covers what our own notes (`VFX-PIPELINE.md`, the vault's "VFX packs and references" and its
note C) did not already have. Their battlegrounds-scale numbers are left out: our guns stay small, short and quiet.

Sources:
- `adnvli/vfxskill`: an agent skill for Roblox VFX, with references it says were measured from about 5,000 particle
  emitters in published effects.
- `TabooHarmony/roblox-brain`: `skills/gameplay/roblox-animation-vfx`.
- `nonlooped/roblox-suite`: `roblox-vfx` and `roblox-user-interfaces/references/particles-in-ui.md`.

## Emitter facts to use

- **`ShapePartial` (0-1)**.
  - Disc: the share of the radius left empty in the middle. At 0.9-1 it emits only at the rim, which gives a clean
    ring emitter.
  - Sphere: how much of the sphere emits. At 0.5 it is a half-dome.
  - Use it for the frag's floor dust ring, the shield's and medkit's foot rings, and impact dust as a half-dome off the
    wall (aim the dome out of the wall's normal).
  - Sphere and Cylinder shapes need a BasePart parent.
  - *Source:* nonlooped/roblox-suite `roblox-vfx/references/shapes-flipbooks-and-advanced.md` (emitter shapes);
    adnvli/vfxskill `references/vfx-craft.md` (particle properties).
- **Which changes touch live particles.**
  - Acceleration bends particles already in flight; Speed only applies to new ones. We already knew Size and Color are
    live.
  - So per-shot speed or direction on one shared emitter is safe, but per-material gravity on one shared chips emitter
    would bend the last shot's chips mid-air.
  - Untested: whether Spread, Lifetime and Rotation are birth-only.
  - *Source:* nonlooped `roblox-vfx/references/particle-emitter-properties.md` (property interactions).
- **Orientation traps** (the repo says it checked these in Studio).
  - A `VelocityPerpendicular` sprite needs Speed of at least 0.001 or it doesn't draw. Our flash uses 0.01, so it's fine.
  - On `VelocityParallel`, Rotation -90 puts the image's top at the front of the motion and 0 lays it across.
  - It follows the particle's own velocity.
  - Streak Squash runs up to about ±3, often ramped from 3 to 1.
  - *Source:* adnvli `references/vfx-design.md` (layers and orientation).
- **Transparency keys above 1** (for example 0 → 1.3) make a particle vanish before its Lifetime ends. That gives an
  early fade without a shorter life. Negative keys do not make a soft texture solid.
  - *Source:* adnvli `vfx-design.md` (motion and curves).
- **Per-emitter TimeScale.**
  - Lingering layers (smoke, wind) can run at TimeScale 0.6-0.95 while the core stays at 1.
  - Our `FxTimeScale` freeze must multiply into each emitter's own scale rather than overwrite it, or slowed layers
    reset after a capture.
  - *Source:* adnvli `vfx-design.md` (timing), `templates/vfx/emit.lua` (read as text).
- **Trails ignore TimeScale.** In a slowed capture, lengthen a Trail's Lifetime by 1/scale (capped at 20 s), or it shows
  far too short. This may be why our katana trail photos read thin.
  - *Source:* adnvli `vfx-craft.md` (checking an effect).

## Layering

- **Sparks that cool.** Emit each spark twice: one copy glowing (LightEmission 1) that dies first, one solid
  (LightEmission 0) that lives a little longer. The spark goes from hot to ember.
  - Use it on metal impacts, the parry and the western skins' sparks.
  - *Source:* adnvli `vfx-design.md` (value).
- **An inside gradient from stacked copies.**
  - Three copies of one flame sheet, each a little wider, longer-lived and further back than the last:
    - Brightness 5 / 2 / 1;
    - ZOffset 0 / -0.1 / -0.2;
    - Squash 0.3 / 0.2 / 0.1;
    - Lifetime 0.6 / 0.7 / 0.8 s.
  - Use it on the angel flame rows, katana flames and the barrel's side flame.
  - *Source:* adnvli `vfx-design.md` (value).
- **Dark twins.**
  - A black copy of a coloured emitter with the same texture, size, life and delay, at the same ZOffset or one step in
    front, gives the dark layer our notes ask for.
  - Never make it smaller and behind: that reads as stray strokes.
  - Lopsided shapes need a locked Rotation and a shared RotSpeed so the copies line up.
  - How black reads by blend: LightEmission 0 is ink, 0.55 a faint veil, 1 invisible.
  - Use it on impacts and the frag.
  - *Source:* adnvli `vfx-design.md` (value).
- **Weapon trails come in pairs.**
  - A thin hot core: Lifetime 0.04-0.15 s, very bright.
  - A wide soft wisp: Lifetime 0.15-0.4 s, LightEmission about 0.6.
  - Both taper (WidthScale to 0) and both use a texture: untextured trails read as flat tubes.
  - Draw a trail texture as a vertical strip: the image's top is the head, its left edge Attachment0.
  - Use it on the katana and projectile trails.
  - *Source:* adnvli `references/vfx-motion.md` (beams and trails).
- **A hit flash's shape.**
  - Three pieces: a sprite that grows, one that shrinks fast (to 0 in about 0.1 s), and a thin flare line (negative
    Squash, 0.04-0.12 s).
  - The body should be a filled spiky shape: a thin four-ray flare alone reads as a "V" once rotated.
  - Use it on the parry, melee hit and impact flashes.
  - *Source:* adnvli `vfx-design.md` (timing), `references/vfx-textures.md`.

## Meshes, rings and lights

- **Crescent meshes.**
  - Set RenderFidelity to Precise (Automatic turns a thin crescent into a wedge at range) and DoubleSided on.
  - A MeshPart's texture ignores alpha, so fade the part's Transparency instead.
  - A tested swing: a white Neon core (Transparency 0.05 → 1 over 0.2 s) and a larger tinted glow (0.55 → 1 over
    0.32 s), both scaling 0.8 → 1.2 and spinning about 50°, Quart Out.
  - For the mesh kit (melee smear, parry, scythe).
  - *Source:* adnvli `references/vfx-mesh-shapes.md`.
- **Rings and shells.**
  - A shockwave ring flattens to 0.1-0.3 of its height while it widens 2-7x, over 0.2-1 s with a cubic ease-out.
  - A big shell below about 0.75 Transparency reads as solid tinted plastic: keep the bubble shield dome at 0.85-0.96.
  - A Decal's Color3 above 1 (set from a script) blooms. A glowing crack at about 10, tweened to black over 1.3 s.
  - *Source:* adnvli `vfx-mesh-shapes.md`, `vfx-design.md` (brightness and blending).
- **Lights grow as they fade.** As Brightness drops, Range can grow (Brightness about 3-9 falling to 0 while Range goes
  from 0-8 to 35-40, over 0.3-1 s). That fits explosions, not muzzle flashes.
  - *Source:* adnvli `references/vfx-camera-world.md`.
- **Impact frames.**
  - Only 1-3 frames.
  - A black frame is ColorCorrection Contrast 2-3 with Saturation -1; a white frame is Brightness 1 with Saturation -1.
  - *Source:* adnvli `vfx-camera-world.md`.
- **Camera shake without drift.** Multiplying an offset into the camera every frame builds up and tips the view. Undo
  last frame's offset just before the camera updates (`RenderPriority.Camera.Value - 1`), then apply the new one just
  after (`+ 1`).
  - *Source:* adnvli `vfx-camera-world.md`.

## Animation and tweens

- **Animation markers instead of fixed delays.**
  - Fire bursts from `AnimationTrack:GetMarkerReachedSignal("Name")`, disconnect on `Stopped`, and make the handler
    safe to run twice.
  - Our lever bursts wait a fixed 0.23 s, which drifts if the lever animation is retuned. A "Clack" marker would keep
    them in sync; keep 0.23 s as the fallback.
  - *Source:* TabooHarmony/roblox-brain `skills/gameplay/roblox-animation-vfx/references/full.md` (priorities and
    markers).
- **The tween restart trap.**
  - A new tween on the same property cancels the old one. `Completed` still fires, with state `Cancelled`, and
    `DelayTime` does not queue.
  - Return a pooled hitmarker, damage number or ring only on a real `Completed`, and chain phases on `Completed`, not on
    delays.
  - *Source:* roblox-brain `full.md` (tweening).
- **Reduced motion.**
  - When the player has asked for reduced motion, drop the non-essential layers: camera shake, the loot screen's
    shake, impact frames, screen flashes.
  - The repo doesn't name the API. `GuiService.ReducedMotionEnabled` is our guess: verify it before use.
  - *Source:* roblox-brain `full.md` (design).

## Effects in the UI (loot screen, shop cards, hitmarkers)

- **ViewportFrames draw no ParticleEmitter, Beam, Trail or Light**, and their only lighting is Ambient, LightColor and
  LightDirection. A skin's feathers or petals on a shop or loot card can only be a 2D overlay. `LootOpening` already
  strips emitters off its cards, and this is why.
  - *Source:* nonlooped `roblox-user-interfaces/references/particles-in-ui.md`.
- **2D particles.**
  - A pool of ImageLabels, capped at 30-80 live, each moving out along a random angle while fading and spinning.
  - The repo tweens each one; we'd rather run one RenderStepped loop for all of them (our hologram rule) and add
    gravity, drag and size over life.
  - Uses: a loot rarity reveal (6-20 shards) and a kill hitmarker (4-6). Never on body hits.
  - *Source:* nonlooped `particles-in-ui.md`, `roblox-user-interfaces/scripts/UIParticlePool.lua` (read as text).
- **CanvasGroup cost.**
  - A CanvasGroup renders to a target the size of its area on screen.
  - The loot reel is already one full-width CanvasGroup, so its cards should shimmer with UIGradient offsets and UIStroke
    tweens, not nested CanvasGroups.
  - *Source:* nonlooped `particles-in-ui.md`.

## Testing and cost

- **Measure the busy case, not one effect.** Our cost guard fires one gun alone. Add a run with 3-4 test shooters near
  the camera, plus a smoke bomb and a frag, at low and high graphics quality. The repo's rough cost estimate is
  rate × size × average opacity × overlap.
  - *Source:* nonlooped `roblox-vfx/SKILL.md` (performance); roblox-brain `full.md` (pooling and cleanup).
- **Preview a sheet before uploading.**
  - The vfxskill tool shows a PNG in Studio from a local `rbxasset://` address before uploading it.
  - That would cut uploads, and moderation exposure, for sheets we then reject.
  - Check how it's done (the folder Studio reads `rbxasset://` from) before relying on it.
  - *Source:* adnvli `vfx-textures.md` (drawing, previewing and uploading).
- **What good one-shot sheets look like.** Largest about a quarter of the way through, then breaking into a few
  pieces. Smoke wants a crisp outline with mottled light and dark inside: soft cel dust reads as cotton balls.
  - *Source:* adnvli `vfx-textures.md`.

## Claims that disagree with our notes (to settle with a one-emitter test in a capture turn)

- **OneShot flipbooks.**
  - Both repos (and the Roblox docs that note C cites) say a OneShot flipbook plays once over the particle's life.
  - We measured in round 2 that it plays at `FlipbookFramerate`: the fireball sat on its first frame.
  - Test: a 4x4 sheet, Lifetime 1, Framerate 1 vs 16, frozen at 0.5 s. `oneshot()` is harmless either way.
- **FlipbookMode Random.** One repo says it shows one random frame; another says Random always cross-fades. Our flash
  uses Loop + StartRandom + Framerate 0, which works.
- **Brightness and bloom.**
  - vfxskill says Brightness 1-3 reads as flat paint at a bloom threshold of 2. In the hits it measured, the hottest
    layer sits around 15, and a white-hot core at 50-150 for 0.03-0.1 s.
  - Ours: the flash runs at Brightness 1.0-1.15 and tracers at 0.85; our notes assumed 3-6 crosses our 2.1-2.4 threshold.
  - Measure before raising anything: the owner wants quiet guns.
- **Negative LightEmission** (-1 to -3) is said to give saturated solid colour with a dark rim (fire bodies at -1 to -5
  with high Brightness). We treat LightEmission as 0-1. Worth one test on the frag.
- **LightInfluence above 1** (0.35-2 on smoke). We treat it as 0-1.
- **Explosions keep growing.**
  - 7 of the 9 explosions vfxskill studied kept growing for 0.25-1.35 s after the hit.
  - Our "main action in the first 25%" rule may make the frag read as a pop.
  - Compare against the web reference before changing anything.
- **LockedToPart.** One repo's example implies a moving smoke trail wants it off. Ours stands for first person: on,
  measured in round 4.
- **Our own stale lines.**
  - VFX-PIPELINE.md's hologram section said 31 Highlights: fixed to 255 today.
  - Vault note C still says a flipbook's cross-fade can't be switched off (`FlipbookBlendFrames` exists).
  - Note C calls Drag "seconds to lose half the speed"; it is a rate (higher slows faster).

## Read and not adopted

- Battlegrounds scale: 40-60 emitters per hit, huge payoffs, heavy shake (2.5-5), FOV punches of 5-7° per hit, blur
  on release, hue tints, craters, rock-throwing beams, orbs, sigils, magic circles, Bezier volleys.
- Glow-first palettes with several hues, and "anticipation, hold, hit bigger" for ordinary hits.
- Clone-and-destroy emit helpers (both repos have one): we pool, and their cleanup timers ignore our TimeScale.
- A very large, faint additive glow layer: our critic already rejected the glow ball.
- Gravity written as -9.81: that's metres; Roblox gravity is 196.2 studs/s².
- Emitter culling at 100-300 studs: our ZoneCull and the 60-80 stud aura cutoff are tighter.
- Typewriter text with sparkle dust: against the no-flavour-text rule.
- vfxskill's clip-matching file (built for its own tool; its "compare at most twice" rule clashes with our critic loop)
  and its rendered-flipbooks file (we already bake in Blender).
