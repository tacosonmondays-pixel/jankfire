# Teacher anatomy: the six bought-pack effects the practice loop copies

Read from the packs' own settings, offline (`tools/roblox/vfx/packs/pack_templates.py`; the raw files stay in the vault).
Photos: Play stage, each effect frozen at 0.05 / 0.1 / 0.2 / 0.35 / 0.6 / 1.0 s, mid-grey and near-black walls
(`r0/`). Times in the curves below are **fractions of a particle's life**, not seconds. LE = LightEmission (1 = adds
light, black adds nothing; 0 = painted over; negative = the packs' "ink" trick, it draws darker than what's behind).

## 1. Hit flash: Combat "Punch-01" (our HitPunch1)
One layer does it all: a 4x4 hand-drawn flipbook played once over 0.5 s.
- The drawing is the animation: frame 1 a fat 4-point star, then a ring of small sparkles, then a thin broken ring.
- Size 0.44 → 3.3 studs (grows the whole life); transparency 1 → 0 by 10% of life, held to 30%, then out by 100%.
  So it **pops in a hair late (about 0.05 s), reads at full strength for 0.1 s, then thins away**.
- LE 1, white, flat to the viewer (VelocityPerpendicular along Front, so the sprite faces where it's aimed), random
  rotation, locked to the part, ZOffset 1 (drawn a little toward the camera).
- Photo: a crisp star at 0.05, a sparkle ring at 0.1, a thin ring at 0.2, gone by 0.35. It never covers the target:
  the middle is empty after frame 3.

## 2. Guard break: Combat "Guard break" + "Guard break 2"
Two layers, each a one-shot 4x4 flipbook, 0.5 s.
- **Ring** (Shockwave1): size 0.44 → 3.75 at half life → 5.1 at the end; LE 1, Brightness 5, flat to the viewer.
  Fast then slower (most of the growth in the first half).
- **Burst** (Break4): a big starburst drawn 3.4 → 4.4 studs (a small swell) then shrinking to nothing in the last
  third; LE 1, **Brightness 25** (overdriven, so its middle blooms to pure white), ZOffset 4 (always in front of the ring).
- Photo: a huge blown-out star at 0.05; at 0.1 several rings inside each other with the star's spikes; at 0.2 one wide
  ring with sparkles on it; gone by 0.35.
- Lesson: **overdrive the brightness of the first frame**; the bloom does the "impact" for you.

## 3. Dash: Combat "dash"
Six layers, all the same pale mint white (#ecfffc), LE 1, lives 0.2-0.6 s, and almost all fade in and out symmetrically
(transparency 1 → 0 at half life → 1).
- Streaks (VelocityParallel lines, 13), chips spinning at ±1000°/s (5), little squares drifting up and down
  (Acceleration ±4.7, 5 each), a glow (LE 0.5, very faint): all thrown out along -X at 7.8 studs/s, **0.11 s late**.
- Rings (9): start 4.8 studs **ahead** (+X) and travel back at 5.2 studs/s, growing 0 → 5.2 with a spin of -250°/s.
  They fire at once; everything else waits 0.11 s.
- Lesson: **the rings lead and the debris follows** (a two-beat effect); symmetric fades make it soft, not punchy.
- Photo: faint on a grey wall at 1.6x scale; it's built to be seen against a body moving through it.

## 4. Slash (spin slash): Combat "Slash-03"
Seven layers on an attachment 4.8 studs below the part, all flat (VelocityPerpendicular) and spinning.
- Two impact flashes: 0.3 s, grey #737373 at LE 1, one fixed at 2 studs and one growing 2 → 10, fading in over the
  first 20% and out over the last 20%.
- Four wind arcs, 1 s each: sizes 0 → 9 / 14 / 14 / 0 → 12 → 19.6; RotSpeed 250°/s (100 for the soft ones); thrown
  down at 17.5 studs/s (one at 2, one at 0-9.6 with drag 9 so it stops); grey at LE 0.75 (half glow, half paint) with
  one white at LE 0 and one darker grey at LE 1 / Brightness 0.3 (a ghost).
- Lesson: **grey at LE 0.75 reads as wind, not light**; stacking 3-4 arcs of different sizes and spin speeds makes
  the swirl.
- Photo: flat spirals widening over the ground from 0.1 s to 1 s.

## 5. Ground impact: Combat "Slam"
Six layers; the ground ones lie flat, the debris flies.
- Ground ring (×3 particles): a grey ring flipbook growing 0 → 22.8 ±4.2 studs over 0.55-0.85 s, spinning ±150°/s.
- Dust (50): a 2x2 smoke sheet, thrown out at 35-75 studs/s with **drag 10** (it shoots out and stops: a ring of dust
  without a ring texture), size 1 → 2.8.
- Rocks (28): speed 25-50, drag 15, VelocityParallel (stretched along their flight), Brightness 100.
- Flare (×2): a sparkle burst flat on the floor, 1.7 → 8.8 studs.
- Clouds (23): the pack's dark-edged cartoon puffs (LE -5), speed 5-25, drag 2, size swelling 0 → 2.4 → 0 over 0.65-1 s.
- Lesson: **high speed + high drag = a ring of debris that stops**, the main trick for any impact on a floor.

## 6. Explosion: 100+ pack #50 (an anime ink blast)
Eight layers in 0.75 s; all lock to the part.
- Flash: one frame (0.05 s) of a 20-stud white glow, 70% see-through, ZOffset 8 (in front of everything).
- Shards (20): stretched streaks (VelocityParallel) at 146-304 studs/s with drag 25 and gravity -85; size 9 → 2.9 by
  13% of life → 0. **Huge and fast for one frame, then tiny.**
- Ink (6 + 6): 4x4 blob flipbooks at LE -5 (they draw black), flung out at 134 studs/s with drag 40 (they stop within
  3 studs), squashed thin → stretched (Squash 0.29 → 1.6) over 0.1-0.25 s.
- Flame (6): the same but orange #ff681d, **invisible for its first 9% of life** (a beat late).
- Licks (4): bright 4x4 flipbook (Brightness 45) thrown out in an 80° cone, swelling 0 → 2.1 → 3.1 → 0.8.
- Dots (40): small dark specks (LE -1) at 25-114 studs/s, drag 7, shrinking away over 0.55-0.75 s.
- Fire ring: one orange ring flipbook 3.95 → 10.3 studs in 0.3 s.
- Lesson: **an explosion is a one-frame flash, then everything flies out and stops at once** (high drag), with colour
  arriving a beat after the white.
