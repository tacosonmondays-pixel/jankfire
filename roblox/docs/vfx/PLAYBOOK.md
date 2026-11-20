# VFX PLAYBOOK: what makes an effect read

These are lessons from copying the bought packs layer by layer and having a critic score each copy (the practice loop:
`docs/vfx/practice/`). Kill effects, finishers and anything new should start here. Each rule names the lesson it came
from.

## The shape of an effect in time
- **An impact is three beats.**
  1. An instant flash that is oversized for one frame.
  2. A ring or burst that widens fast in about 0.15 s.
  3. Debris that flies out and stops (high drag) over about 0.3-0.5 s.

  Most pack effects are gone by 0.35 s; anything still full-size at 0.35 s reads as slow and soft. (Hit, guard break and
  explosion teachers, round 0.)
- **The flash is the loudest thing, and the shortest.**
  - The explosion's white flash lasts 0.05 s at 20 studs, 70% see-through, drawn in front of everything (ZOffset 8).
  - The guard break overdrives one frame with Brightness 25, so it blooms to pure white.
  - Make the flash hit hard and leave fast: don't make it bigger or longer to compensate.
  - Keep it see-through. Round 2 made it 30% see-through to hold it longer, and it became a blown-out white ball that
    hid everything else (explosion 5 → 4). The pack's 70% is right.
- **Match where each effect peaks, not just its size.** Find the teacher's strongest frame and its faintest.
  - The pack's hit is busiest at 0.1 s (a ring of chunky sparkles) and nearly gone at 0.2 s.
  - Round 3 had the timing right but put our strongest frame at 0.2 s: a full doubled ring. It read wrong although
    every phase was on time.
- **Match the beat, not just the size.** In round 2 our hit and guard break had the right shapes but were still a star
  at 0.1 s, when the packs had already turned into rings. Each phase needs the right share of the flipbook: the star
  only in frames 0-1.
- **Colour comes a beat after the white.** The explosion's orange flame stays invisible for its first 9% of life.
- **Two beats beat one.**
  - Dash: the rings fire at once; the streaks, chips and dots wait 0.11 s.
  - Slash: the arcs grow over 1 s, with a 0.1 s-late ghost arc.

## Shapes
- **Hand-drawn flipbooks do the animation.**
  - A single 4x4 OneShot sheet can carry a whole hit: a star, then a sparkle ring, then a thin ring, then empty.
  - Leave the last frames **empty**, so the particle's life doesn't have to be cut to the frame.
  - Keep phases apart: overlapping the star frames with the ring frames made a "spiky ball". (Hit, round 1: 4/10.)
- **Cel edges, not soft gradients.**
  - The packs' stars, bursts and ink splats have hard alpha edges. Our soft-glow stars read as lens flares, not as hits.
  - To get one, snap alpha around 0.5 when drawing. (Hit, guard break, explosion, round 1.)
- **Thin means thin.**
  - Speed lines and dash rings are hairlines, nearly invisible on black: a 3 px line on a 256 px canvas.
  - A thick soft ring at LE 1 blows out to a white band. (Dash, round 1: 2/10.)
- **Use square canvases for streaks.**
  - A 64x256 streak texture is stretched to the particle's square, so it reads as a blob.
  - Draw the line along v (the axis a VelocityParallel particle points) on a square canvas. (Dash, round 1.)
- **Wind is lines, not a crescent.** A swirl of 6-8 thin broken streak lines at grey LE 0.75 reads as air. A solid
  crescent reads as an object. (Slash, round 1: 4/10.)

## Light and colour
- **LE 1 adds light, LE 0 paints.**
  - Use LE 1 for anything that glows. Black backgrounds then vanish; see the black-backed rule in VFX-PIPELINE.
  - Use LE 0 for dust, rocks, cracks and anything that must read on a bright floor.
  - Negative LE only darkens what is already dark in the texture. On a white texture, LE -5 only darkened the soft edge
    (round 2's "white petals with dark rims"). The packs' black ink textures are drawn dark. For black ink from a white
    shape, use Color #000 at LE 0 with LightInfluence 0.
- **A VelocityParallel particle flies along its texture's u axis (left-right).**
  - Draw speed lines, needles and daggers across the canvas, or give them Rotation 90.
  - Round 2's vertical hairlines came out as short ticks across the flight.
  - Round 3's vertical daggers made a polygon "cage" round the blast instead of needles pointing out.
  - World finishers, round 6 (20 Nov): our soft streak (127914373549121) and spark (73042129135061) textures are both
    drawn along v, so a rising crown or plume of them flew sideways until they got Rotation 90.
- **A ring with one bright side reads as motion.** The dash's rings are a single hair line, bright on one side.
  A double line read as a stack of contour lines.
- **Grey at LE 0.75 is wind; white at LE 1 is energy.**
- **Calm palette:**
  - White with a pale-gold tint (#fff8e8, #fff0d0) instead of saturated orange.
  - Black ink and dark grey cracks for contrast.
  - Our orange flame ring was the loudest thing on the round-1 sheet, and the pack had none.

## Ground effects
- **High speed + high drag = a ring that stops.** Dust at 35-75 studs/s with drag 10 shoots out and stops in a belt.
  No ring texture is needed. (Slam teacher.)
- **The floor itself must change.** Dark branching cracks (LE 0, about 30 studs, held about 1.5 s) are half the
  pack's slam. Without them it's just a cloud. (Slam, round 1: 3/10.)
- **Big overlapping puffs, not popcorn.** The pack's clouds are fewer, bigger (about 4 studs at peak), packed into a
  belt. Small separate balls over a disc read as popcorn.
- **The belt's width comes from speed over drag.** Clouds at 5-25 studs/s with drag 2 spread about 12 studs into a flat
  3:1 belt. At 10-16 with drag 4 they stop within about 4 studs and heap into a round pile (round 2).
- **Cracks go under the clouds and are fine lines.**
  - Use ZOffset -3, about 1% line width, a pale grey (#5a5650), full length from the first frame.
  - Draw them radiating: little random turning per step, or they curl into a bush.
- **Fade a puff by shrinking it, not by eating holes.** Holes show as dark-rimmed "eyes" on black.
- **Hide the helper ring.** The pack's ground ring is barely visible. A bright ring becomes the biggest shape on screen.

## Process
- Shoot every effect on mid-grey AND near-black: halos and dark squares hide on one or the other.
- New textures need a moment to load: preload them (ContentProvider:PreloadAsync) before the first photo, or the first
  shot shows nothing.
- Freeze-photo the life at fixed ages (0.05 / 0.1 / 0.2 / 0.35 / 0.6 / 1.0 s), pack and ours in the same frame.
- **For floor effects, check both rows are seen from the same angle.** A row above the camera's axis is seen from lower
  down than a row below it. Our first rig showed the pack's floor from 18° and ours from 54°, so our ground impact looked
  round and tall for three rounds. Tilt each row by its own line of sight, or shoot each row alone.
- **Small textures blur big particles.** A 4x4 flipbook cell is 128 px; stretched over a 30-stud crack, a 1-pixel line
  becomes a blurry rope. Long thin floor marks need one big image (1024 px), not a flipbook.
- **Clean concentric rings read as a target symbol.** Break rings into arcs and wrap them in jagged shards.

## Rounds 4-5 (the practice loop's later lessons)
- **Even spacing reads as a badge.**
  - Eight sparkles evenly round a ring looked like a wreath (hit, round 4: 7).
  - Five uneven sparkles at irregular angles and sizes read as an impact (round 5: 8).
  - Spikes evenly round a ring read as a sun or a gear. Clusters where the star's arms were read as the burst
    breaking up.
- **Small breaks, not dashes.** Ring breaks of 10-15° read as a shock ring cracking; 30-40° gaps read as a dashed crown.
- **A sprite's silhouette must fill its cell.** Two layers can share a Size and still read as different sizes if one
  texture's shape fills 40% of its square and the other's fills 90%. Our dust looked like popcorn until the puff filled
  its cell (ground impact, 5 → 7).
- **Fade a shape by its drawing or by its curve, not both.** The puff's frames faded and its Transparency curve faded
  too, so it was a grey ghost at 0.6 s while the pack's was still solid.
- **Black ink must sit in front of the flash.** With the flash at ZOffset 8, the ink needs ZOffset 9 or the flash
  whitewashes it. Then keep the black core short (gone by 0.1 s) and let thin daggers fly out, with gaps between them.
- **Check the critic's measurements too.** In rounds 3-4 the critic measured two touching copies of the pack's slam as
  one 330 px belt and asked for a wider spread; the real width was 180 px, which we already matched. Each effect's six
  copies are a cell apart: measure one.

## Round 6 (the last round)
- **Know what each setting is doing before you change it.** Before touching a layer, write down which visible feature it
  makes, and leave alone any value that a feature which already matches depends on.
  - The ground impact's fast clouds (10-40 studs/s) were what kept the middle of the ring hollow.
  - Round 6 set them back to the pack's speed (5-25) to match a number, and the hollow ring filled into a mound
    (ground impact 7 → 6).
- **Turn "more visible" up in half steps, one setting at a time.** Change Brightness, or Size, or Count, not all three.
  The dash's speed lines went from invisible on black (round 5) to the loudest thing on grey (round 6).
- **Bloom wipes out fine edges.** At high Brightness a ±10% wobble or a thin notch disappears, and the shape reads as a
  clean icon (the guard star still read as a smooth 4-point sparkle). Draw roughness as spikes or notches of at least
  about 8% of the radius.
- **Final scores** (round 1 → best): hit 4 → 8, slash 4 → 8, explosion 5 → 8, guard break 3 → 7, dash 2 → 7, ground
  impact 3 → 7 (round 5; round 6 slipped to 6). Sheets: `docs/vfx/practice/progress/`.

## Fire on a body (kill effects; the Ember practice, 20 Nov, kill-effects session)
Ember was rebuilt in seven critic rounds against the Combat pack's fire aura. Scores: before 3, then 4, 4, 6, (4 not
scored: a regression), 5, 6, 6. Sheet: `docs/flair/ember-practice-r1-vs-final.jpg`. Rounds and scores are in
`docs/FLAIR.md`.
- **A Highlight fill draws over particles.**
  - Any flame inside a charred body's outline vanished under the Highlight fill (rounds 3-4). The only fire that read
    stuck out past the silhouette.
  - Char a body with a **shell** instead: clone each part client-side, strip its textures (SurfaceAppearance, decals,
    TextureID), colour it charcoal. It is real geometry, so flames on its surface depth-sort in front of it.
  - Keep the Highlight only for a rim, as an outline on the shell.
- **The pack's fire hugs every part.** It does this with three layers per part, emitted from the part's surface (Box,
  Surface style):
  - solid colour flames (low LightEmission, high Brightness, so they read on grey);
  - a smaller near-black flame inside them;
  - dark specks streaking up.

  One big emitter for the whole body reads as a pillar or a column.
- **Pick parts by name, not by size.** The "ten biggest parts" were hats, hair and a sword. The arms and legs never
  caught (round 2).
- **Squash: positive stretches a particle taller and thinner; negative widens it.** Round 3's "wider" flames came out as
  slivers.
- **Fire dies with its part.** When a part has burned away, `Clear()` its emitters. Otherwise tongues hang 1.5-2 studs
  in the air over nothing, the most-cited fault (rounds 2, 6).
- **A burn line cuts, it doesn't pop.**
  - Slice each shell part down its own up axis as the line passes: set Size and CFrame per frame. Do this only for
    upright parts without a SpecialMesh.
  - Long parts (a sword, a cape) need their fade capped to about 1.5 studs past the line, or they linger as see-through
    ghosts.
- **Catch on frame one.** `Emit()` a burst on every part at once. A rate ramp leaves the first frames bare.
- **Pure black vanishes on a dark wall.** Use a charcoal around (58,42,34) for char.
- **Stacked additive flames blow out to white.** The core layer stays at LightEmission ≤ 0.7.
- **A pack texture on a black background needs LightEmission 1.** Below 1 its black square shows. Quiet it with
  Brightness and transparency instead (Static, v1125 → v1133).
- **Photos of VfxEmit effects:** VfxEmit parks and clears an effect on its own clock, even when the effect is frozen.
  For a frozen photo, add a hidden emitter with `EmitDelay` 25 to the templates and pooled clones.
- **Practice rounds without touching the place:** upload the module as a lab model, load it in Play only (the server
  `LoadAsset`s it into ReplicatedStorage, the client clones it next to its siblings and requires it). Push and save only
  the round you keep.
