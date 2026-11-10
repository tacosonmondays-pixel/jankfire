# The Big Heart: where it stands, and what beats with it

The model is `docs/story/gut/GUT_HEART_MODEL.md`. This page is the world side: the spot, the collision, the one clock
that the heart, the fog and the thud share, the low red ground fog, and every knob.

Story mode only (`?story=1`). Nothing here is loaded by a multiplayer map.

## Where
`gut:big_heart`, "the Big Heart". The tower's foot is at **x -96, y 40, z -78** (`SLICE.heart` in
`shared/city/slice.js`), not turned: the heart's front faces south (the border and the gate), its apex points east.
The place's own point (`PLACES['gut:big_heart']`, the `gut:big_heart` mark) is its listening spot, 9 m out in front
at (-94.5, 40, -69.1). A second mark, `gut.big_heart_top`, is the top of the rib stair (-94.2, 65.6, -77.7).

It stands on the open ground behind Meat Mechanics, between that shop's east wall and the low flesh wall of the old
time-office plaza, a few metres north of the campus street at z -60.

### Why there
The generator leaves very little flat, empty ground in the Gut: every block is offices unless something reserves it.
A scan of the district (every 4 m, a 12 m clear circle, then rays from where players stand to nine points
up the tower and the heart) left three kinds of spot:

| spot | from the Gut Border Gate landing | from Peristalsis Avenue | from the Big Stomach |
|---|---|---|---|
| the strip between the Big Stomach's east rim and the offices (-111, -160) | the top 6 m over a 24 m office, 160 m off in 55% fog | all of it, 31 m | all of it, 67 m |
| the Tooth Market side (x 0 to 96) | hidden | 150 m+, in fog | hidden |
| **behind Meat Mechanics (-96, -78)** | **most or all of the heart from 101 of 147 standing spots on the landing, 82 m** | **all of it, 57 m** | **all but the foot, 89 m** |

So it is the skyline as you come up the Long Stairs: through the gate it is at your ten o'clock, 49 m tall, 80 m
away. From the exact `gut:border` point the gate's west pillar is in the way; two steps either side and it is there.
From the old plaza and the campus street it fills the view. It is also seen from the Bottom's top terrace (the
Sunset Wall, the top of the Down Escalator) as a shape up the hill.

Nothing was moved for it. The spot had no props, no shapes and no marks inside the footprint; the only thing taken
out is any baked bile-puddle light within 7 m of the foot (none there today: the filter is for the day the scatter
changes). The nearest things: Meat Mechanics' back wall (8.9 m), the plaza's wall (10 m), a kerb parking spot (14 m).

## Collision
`shared/city/bigheart.js` adds the boxes to the Gut's chunk as hidden collision (`B.add(..., { hide: true })`), the
same way rib arches and lungs get theirs, so the server's story rooms, the nav grid and the client build the
identical boxes from the same module.

The boxes are `shared/city/bigheart_boxes.js`, **generated** from the model's json by
`node tools/city/heart_boxes.mjs` (run it again when the model is rebuilt; `tests/story/bigheart.test.mjs` fails if
it is stale). Two things in the json's boxes had to be redone there, because with them as shipped the stair could
not be climbed:

- **The spine.** The json has ten square 3 m lifts. Their corners stick 0.4 m out of the round, leaning spine and
  catch heads and treads. It is boxed again from the stair's own axis (centre and radius every 1.5 m): a square and
  a cross per lift, all inside the circle. 60 boxes.
- **The thigh-bone buttresses.** The json has five fat slabs a bone (2 x 3 x 2 m round a 0.8 m shaft); they fill the
  first two turns of the stair. Each bone is boxed again as 12 thin boxes along its axis, and the 23 of those that
  would take a climber's headroom over a tread are left out. You brush through the bone where it crosses the stair
  (five crossings, all below 10 m) instead of being walled off. Elsewhere the bones are solid.

Mound, heart and the 98 tread pads are the json's.

**The stair is climbable.** The test walks a player-sized box up it with the game's physics (0.6 m step, no jump)
from the listening spot to the top at 3, 5, 10 and 14.5 m/s. Treads 44, 51 and 63 are gone: each leaves a 0.5 m
rise over a 0.2 to 0.3 m gap, which the step-up takes without a jump. Treads 11, 25, 27, 52, 55 and 85 are stubs
(half a tread, about 0.9 m of ledge against the spine): walkable, keep to the outside. At the top there is 1.98 m
under the heart's lowest box; the hanging hearts at the apex are within reach.

## The one beat
`public/js/city/gutbeat.js`: `gutBeat`, ticked once a frame.

| | |
|---|---|
| `rate` | 0.72 beats a second |
| `t`, `ph` | beats since the page loaded; where in this beat (0..1) |
| `lub` | 0.06: when in the beat the big beat peaks, the fog snaps shut and the thud lands |
| `dub` | 0.21: how much later the dub comes, on all three |
| `span` | 0.55: the ripple takes this much of a beat from the top of the heart to the apex |
| `k` | how hard the fog is squeezed now (1 on the lub, 0.6 on the dub) |
| `fix` | set to a number to hold the clock at that beat (screenshots, tests); `null` runs |

What reads it:

| ph | what happens |
|---|---|
| 0.04 | the thud's lub starts (14 ms attack) |
| **0.06** | **the lub.** The whole heart is at full swell, all at once. The district's distance fog closes in and flushes (`ingame.js`, PR #159's curve, now on this clock). The ground fog swells and lights. |
| 0.06 to 0.12 | the ripple sets off: the pacemaker (top right of the heart) reaches full swell at 0.12 |
| 0.12 to 0.67 | the ripple crosses the small hearts to the apex |
| 0.27 | the dub: the whole heart again (60% of the lub), the fog, the thud (0.29 s after the lub) |
| to 1.0 | the ripple goes on down the sleeve, the aorta and the roots |
| from 0.9 | a ring runs out through the ground fog from the roots, 80 m a beat |

The city's own flesh (the breathing walls, the moving street's surf timing) still runs on the streamer's older
72-a-minute `uBeat`. It was left alone: Peristalsis Avenue's surf window is timed to it.

## Drawing it
`public/js/city/bigheart.js`, hooked into `ingame.js` (`startHeart`, `updateHeart`, `stopHeart`).

- Its own `GLTFLoader` (the prop path strips `uv1`). Textures nearest-filtered, the props' studio reflection.
- **The one big beat** (the owner asked for it): every flesh vertex of the heart moves out from the heart's middle by
  `big` of its distance from it, on the lub and (60%) on the dub, all at the same moment. A vertex below the apex does
  not move (the weight runs from 0 at y 26.5 to 1 at y 32.5), so the sleeve and the tower's vessels stay fused to the
  bone and the collision boxes still fit. The whole heart also flushes and glows a little with it.
- **The ripple** rides on top, and is the model doc's snippet: swell along the normal by `aPulse.y`, timed by
  `aPulse.x`, plus the travelling flush and the pits' glow. From far off you see the heart beat; close up you see
  the small hearts go one after another across a heart that is itself beating.
- **Its own light.** The Gut is dim and lit from above, and this is mostly seen from below, where the hemisphere
  light is nearly black. The flesh gives off 30% of its own colour at rest and up to 90% more as the wave passes, with
  a wet red rim; the bone gives off 20%. Without it the heart is a black shape.
- Potato's vertex snap and the city's lamp lights, as on props. The scene's distance fog applies as to anything.
- Near model inside 120 m on Mid and Too HD, 84 m on Crusty, 48 m on Potato (8 m of slack either way).
- **Cost when you are not there:** nothing is fetched until you are within 340 m; it is not drawn past the fog's far
  distance or 320 m; no thud past 150 m. Two baked lights (red at the roots, dimmer under the heart) are chunk data.

Knobs (`HEART_FX`): **`big` 0.07** (the big-beat swell: 7% of its size, about 0.4 m at the heart's flank and 1 m at
the top of the arch), **`amp` 0.09 m** (the ripple swell at a small heart's crown), `flush` 0.6, `glow` 1.1,
`self` 0.3, `lit` 0.9, `rim` 0.3, `bone` 0.2.

## The thud
`sfx.bigHeart(v, pos, gap)` in `public/js/audio.js`: a sine falling 58 to 35 Hz with an octave on top (so small
speakers play something) and a little low-passed noise, 14 ms attack; the dub is 70 to 42 Hz, quieter, 0.29 s later.
Volume is `(1 - d / 150)²`: full at the foot, a fifth at 80 m, nothing at 150 m. Panned gently toward the tower. No
music was changed (the Gut's music bed has its own heartbeat at its own tempo).

## The low red fog
`public/js/city/gutfog.js`: flat sheets stacked just over the ground, 0.14 m to 0.9 m up (wrist high: you look over
it), each one quad with scrolling noise for lumps and thin patches: two slow fields, a fine one that you see curling
round your shins, and 50 m banks that wander the district.

- the plateau (y 40), with a hole over the Big Stomach's crater and a soft east edge
- the border band (y 36): the spill at the foot of the cliff, gone 40 m south of it
- a pool in the Big Stomach's bowl over the acid: the thickest
- round the heart's roots it thickens and the holes close

Every sheet reads nearly the same spot of the noise, so a lump is one lump through the whole stack (wide at the
floor, narrower at the top) with thinner ground beside it.

Why sheets and not height fog in the city shaders: they fog ground, props and people's shins alike without touching
another material, and a stack of sheets cannot get thicker than its layers however flat you look along it.

The owner asked for it thicker, on the ground and visible round you, so: there is no clear ring round the camera
(it starts 0.3 m from your eye, which is to say at your own knees), the stack's cap is **72%** (`cap`: a stack of
sheets never covers more than that, however far or flat the view), and the Gut's distance fog came in from 34 / 250 m
to 26 / 205 m (`fogNear` / `fogFar` in `shared/city/slice.js`). What keeps a fight readable: it stops at 0.9 m, so
heads, chests and guns are over it; sheets fade as your eye crosses them (a slide or a crouch does not white out);
and it is drawn before every other see-through thing, so sparks, glass, tracers and outlines stay on top of it.
Glowing bile puddles shine through it (they are drawn after it). Something lying flat on the floor in a thick lump
is 72% covered: if pickups get lost, `cap` is the knob.

It only exists in the Gut and the border band, and is not drawn when the camera is more than 110 m from the Gut.
Layers by preset: Potato 3, Crusty 4, Mid 5, Too HD 6 (plus the border's and the pool's: 8 to 14 quads in all; the
border's are skipped deep in the Gut and the pool's away from the Big Stomach). Each sheet is two triangles and
four texture reads a pixel.

Knobs (`GUT_FOG`): `on`, `top` 0.9 m (the highest sheet), `cap` 0.72, `gain` 1.6 (how much of a lump sits on the
cap), `holes` 0.26 (how much thin ground between lumps), `glow` 0.7 (how much it lights on the beat), `color`
0xc81a30, `drift` 1, `near` 110 m.

## The darker Gut
The owner picked the darker look for the Gut (flesh #8e1622 going to #34060c in folds with #c23a40 highlights, bone
#c4b288, veins #221634, glow about #c01828). The Art lane re-exports the Blender props; the code side is here:

| where | what changed |
|---|---|
| `shared/city/gut.js` | the `FLESH` scatter palette, the plateau's ground tints, roof skins, the stomach's lining, the avenue's tube and floor, the border's flesh ground and cliff, the low walls; bone tints (stairs, the Choir Lung's floor and columns); the heart lamps' light |
| `shared/city/playground.js` (the Gut part) | the Wishbone's bone, the stomach's hanging strands |
| `shared/city/plan.js` | the base colours of `flesh`, `liver`, `fat`, `rib`, `bruise` (bruise is the vein colour now) |
| `public/js/city/mats.js` | the flesh tile's mottling and veins, the rib tile's grooves, the gum cobbles (dark gum, old-bone teeth), the flesh shader's vein and wet-rim colours |

Flesh-family materials are only used by the Gut, its border and its edges (and one box in the `blocks` test city),
so nothing in the Bottom or the Commute moved, and none of it is loaded outside story mode. Not changed: bile and the
Big Stomach's acid (their colour is in the shared liquid shader, `public/js/liquidmats.js`, which multiplayer maps
use too), the office blocks' greys, the Gut Border Gate's pastel houses.

## A fix that came with it
`refreshMapVisuals()` in `public/js/world.js` redraws a map's boxes when the game's models finish downloading. In story
mode the map's box list is the city's live collision, so if the models landed after you had entered, every wall got a
dark stone copy and every hidden collision box (rib arch legs, lungs, grapple brackets, and now this whole tower)
stood there as a black block. A streamed map now skips that redraw. Multiplayer maps are untouched.

## Looking at it
```js
const gb = (await import('/js/city/gutbeat.js')).gutBeat; gb.fix = 0.3;      // hold the beat; null to let go
(await import('/js/city/gutfog.js')).GUT_FOG.on = false;                     // fog off
(await import('/js/city/bigheart.js')).heartState();                         // { state, lod, visible, d }
(await import('/js/player.js')).ME.pos = [-94.5, 40, -66];                   // the foot
```

## Files
| | |
|---|---|
| `shared/city/slice.js` | `SLICE.heart`, `PLACES['gut:big_heart']` |
| `shared/city/bigheart.js`, `bigheart_boxes.js` | the spot, collision, lights, marks |
| `shared/city/gut.js` | one call: `bigHeart(B)` |
| `tools/city/heart_boxes.mjs` | json to boxes |
| `public/js/city/gutbeat.js` | the clock |
| `public/js/city/bigheart.js` | loader, shader, near / far, the thud's trigger |
| `public/js/city/gutfog.js` | the ground fog |
| `public/js/city/ingame.js` | the hooks; the distance fog reads the clock |
| `public/js/audio.js` | `sfx.bigHeart` |
| `public/js/world.js` | one line: a streamed map doesn't redraw its boxes |
| `shared/story/content/world.js` | the `gut:big_heart` location |
| `tests/story/bigheart.test.mjs` | boxes fresh, place and marks, the climb |
