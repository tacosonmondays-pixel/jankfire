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
- **Squash -1 widens a sprite.** Draw a speed line ACROSS the canvas (along u), not along it (round 2's dashes came out
  as short ticks).
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
