# THE HEADLINER: model, clips and how to drive him

The presentation half of [JESTER_LORD.md](JESTER_LORD.md) (who he is, the Midway, his boss sketch). Working id
`jester_lord`. **He is not placed in any mission, and nothing here does damage.** To see him in the game:
`?story=1&jesterlord=1` stands him 7 m in front of you and runs his whole set on a loop with a caption for each clip.
Madame Velvet is not part of this; she comes later.

**The build: `tools/blender/cast/make_cast_jester_lord.py`** (built from code, `blender52`), on his skeleton in
`jl_rig.py`. The owner's sketch: [`refs/jester_lord_owner_sketch.jpg`](refs/jester_lord_owner_sketch.jpg).

| what | in the game's renderer (`docs/story/cast/`) | from Blender (`tools/blender/sheets/`) |
|---|---|---|
| turnaround beside a 1.8 m mannequin | `jl_game_turn.jpg` | `c_jester_lord.jpg` (in his stance) |
| close-ups: face, the long nose, the profile, his eyes open, the hat and horns, a horn bell, the dummy jaw talking, the collar and ruff, the marotte, the hand on his hip, the stockings at a knee, a foot and its bell, the big top, the thorax, the stump, the far model | `jl_game_closeups.jpg` | `c_jester_lord_close.jpg` (face, nose, hat, collar, marotte, knee, bell, big top) |
| his silhouette beside the owner's sketch: his head from his left like the sketch, from 30 m enlarged, the far model, true size at 30 m | `jl_game_silhouette.jpg` | |
| one moment from each clip | `jl_game_poses.jpg` | |
| a contact strip per clip (12 frames, the marks called out) | | `c_jester_lord_clip_<name>.jpg` (made in the game's renderer by `jlshots.cjs clips`) |
| in the real game, story mode | `jl_ingame_hd_*.jpg` (Too HD: idle at 7 m, talk, bow, scuttle, web hang, leg off, from 30 m), `jl_ingame_potato_*.jpg` (the same at Potato) | |
| the rehearsal, recorded in story mode at Too HD | `jl_rehearsal.mp4` | |

In every sheet "his right" is +x: the pink horn, the pink half of his doublet, and the leg that comes off (RB).

## Who you are looking at

A puppet jester from the waist up on a big spider. **3.32 m to the top of his cap, 3.82 m to the bells on his
horns, 4.9 m across the legs** (knees 2.13 m up). He is one of the Off-Spec: one thing huge, one thing tiny. The huge
thing is his head and grin, the tiny thing is his waist.

- **The head** (from the sketch): white greasepaint on a big egg, rosy cheeks, a black diamond painted through each
  eye, the eyes shut (heavy white lids, a dark lash line, three lashes flicking out at the corners: smug), thin
  arched brows, a long pointed nose with a candy-pink tip, and a grin from ear to ear: magenta lips, a row of
  tombstone teeth on top, smaller ones on a **ventriloquist dummy's jaw** (the chin drops between two slot lines).
- **The hat**: a jester hood (pink on his right, yellow on his left, black piping round his face), a band of black
  and white diamonds, a split cap, and **two horns that sweep back and curl up like the sketch's**, a brass bell
  hanging off each tip.
- **The collar**: eight petals, pink and yellow, a brass bell on every point, a white ruff at the neck.
- **The doublet**: his right half pink, his left yellow, a placket of black and white diamonds with three yellow
  pom-poms, ten pointed hem flaps over the spider's back. Pumpkin-striped puffed sleeves, diamond sleeves, frill
  cuffs, white gloves. His right hand sits on his hip; his left holds up **the marotte**: his own head, a quarter
  size, on a striped stick (it nods along when he talks and glances at you when he idles).
- **The spider**: a lacquered plum-black thorax with a pink and yellow carousel band and four red bead eyes, a brass
  ring where the jester stands in it. The abdomen is **a circus big top**: pink and yellow tent stripes up to a brass
  finial and a pink pennant, a valance of black and white diamonds, pointed flaps, brass spinnerets underneath.
- **The legs**: eight, front and back pairs longest like a real spider, knees up above the body. Each: a black ball
  at the hip, a white lace stocking top, the femur in pink and yellow harlequin diamonds, a black knee, the tibia in
  black and white diamonds, a black ankle, a black patent shoe with a curled toe (yellow or pink, alternating), and a
  **brass jingle bell hanging off every toe**. The diamonds are cut along the triangles' own edges, so they are
  crisp at any distance and need no texture.

## Files

| file | what |
|---|---|
| `public/models/cast/c_jester_lord.glb` | the model: `part_thorax__spider` and `part_spine__jester` (**skinned**, one skin whose 61 joints are his joints by name), `part_thorax__dmgStump` (rigid on the thorax, hidden until the leg comes off), `part_thorax__lod` (the far model, skinned). 1,293 KB |
| `public/models/cast/c_jester_lord.parts.json` | every named part (joint, box, triangles), his joints and their rest, markers, the look, hit boxes (head, jester, thorax, abdomen, and every leg as capsules along its joints) |
| `public/js/story/jesterlook.js` | his skeleton (built from `jl_clipdata.js`), the code puppet (the fallback), the markers (`MK`), his faces |
| `public/js/story/jesterlord.js` | `JL`: clips, marks, the scuttle by distance, the dangling bells, the web, the stump, the far LOD, the rehearsal |
| `public/js/story/jl_clipdata.js` | his skeleton and clips as key poses. **Generated** by `tools/blender/cast/jl_clips.py` |
| `tools/blender/cast/jl_rig.py` | his skeleton in one place (sizes, legs, a leg solver, fk), plain python |
| `tools/blender/cast/jl_clips.py` | the clips: key poses, the arm and leg solvers, the loop and foot-slide checks. Writes `jl_clipdata.js` and his `joints.json` entry |
| `tools/blender/cast/make_cast_jester_lord.py` + `jlkit.py` | **the build**: the mesh builder (game coordinates, a colour per face corner, joint weights per vertex, lattice tubes for the diamonds, bells, frills, decals), the model, skin, AO, far model, asset gate, parts file, Blender sheets |
| `tools/blender/cast/jlshots.cjs`, `jlgame.cjs`, `jlrec.cjs` | the actor-path check and the in-game sheets; the story-mode shots; the recording |
| `tests/story/jester_lord.test.mjs` | the glb, the parts file, his skeleton and the clips agree |

Touched in shared files: `looks.js` (one import and the `jester_lord` look line), his entry in
`tools/blender/cast/joints.json`, a row in `tools/blender/README.md`. Nothing in `actors.js`, `boot.js`, the content
files or the server. Story mode's background prefetch (`prefetchCast(LOOK_IDS)`) fetches his glb like the other
looks.

## His joints

The 14 cast joints (the human legs `legL` .. `kneeR` stay as empty joints inside the thorax: he has a spider) and
47 of his own, **61 in all** (the hat lord has 52; the boss budget is 64). Every joint turns from its rest: local =
rest x the clip's delta (three.js XYZ euler).

| joints | on | what |
|---|---|---|
| `thorax` | body | the spider's middle, 1.25 m up. `spine` (the jester's waist) rides it |
| `abdo` | thorax | the big top, hinged at the pedicel |
| `fem`, `tib`, `foot`, `bell` + side `R`/`L` + pair `A`..`D` (`femRA` .. `bellLD`) | thorax | eight legs, front (A) to back (D): femur (`.y` swings round, `.z` lifts), tibia and foot (`.z` bends), the bell on the toe (it dangles: see below) |
| `hatR` > `hatRb` > `bellHR` (and `L`) | head | each horn in two pieces and the bell on its tip. The horn is skinned across them, so it bends smoothly |
| `jaw` | head | the dummy's chin: `.x` + drops it |
| `lidR`, `lidL` | head | the shut lids: `.x` + lifts them (his eyes open, once) |
| `browR`, `browL` | head | `.py` + raises them |
| `collar` | spine | the collar's bells (the petals blend onto it toward their tips) |
| `marotte` | handL | the little head on the stick: `.x` nods it |

**Skinning**: almost everything is rigid on one joint (each piece of the model is built knowing its joint), so the
puppet reads as a puppet: ball joints at the hips, knees and ankles, puffs and cuffs at the shoulders and elbows. The
horns blend from the head over `hatR` to `hatRb`, the collar petals from the spine to `collar`, the pedicel from the
thorax to the abdomen, the neck from the neck to the head. Weights are stored as bytes.

Leg solver (`jl_rig.leg_ik`): each leg lies in the upright plane through its hip and foot; the foot segment keeps a
62 degree slope down, the femur and tibia solve the rest with the knee up. Every key of every clip puts the planted
feet back on their spots, whatever the body is doing.

## Clips

Authored in `jl_clips.py` as key poses with an ease each; `jesterlord.js` plays them. He is **always** in one of
them (a spawned `jester_lord` with nothing playing is put into `jl_idle`), so a clip owns all of him. On top of the
keys:

- **Overlap**: the horn tips, the collar, the marotte, the hands and the big top arrive late.
- **The bells dangle**: every bell (8 feet, 2 horns) hangs straight down in the world whatever its foot or horn is
  doing, and swings on a damped pendulum when its spot is shoved about (a stepping foot, a bow, the leap). Upside
  down in the web they still point at the floor.
- **The scuttle**: whenever his root moves, `jl_walk`'s legs are laid over whatever clip is playing, run by distance
  (1.5 m a loop), so the feet don't slide at any speed.
- **The look**: the game turns his head to you; `x.look` says how much of it he keeps (none upside down).
- **Talking**: when the actor talks (dialogue), the dummy jaw goes with the voice.
- One clip runs into the next (0.3 s from wherever the last had him; 0.6 s out of `jl_leg_off`). A clip that ends
  goes back to `jl_idle`.

| clip | length | what happens | marks (s) |
|---|---|---|---|
| `jl_idle` | loop 6.0 | holding court: the big top breathes, his head tips one way then the other, a brow goes up, the marotte nods and glances at you, the horns sway. A front foot drums tip-tap-tap, a back leg lifts and re-plants, another shifts | tap 0.68, 0.84, 1.0, step 3.65, jingle 4.0 |
| `jl_talk` | loop 4.8 | the showman: "ladies, gentlemen, and whatever you are". His right hand presents palm out, sweeps out to the side, comes to his chest, points at the sky; the dummy jaw flaps, the brows work, the marotte nods along, a front foot keeps the beat | ladies 0, gentlemen 0.9, whatever 1.9, you are 2.9 |
| `jl_bow` | 3.7 | a flourish (hand up, marotte flung out), then he folds at his tiny waist with a hand across his belly and **the whole spider curtsies** (front legs fold, the big top lifts behind), his grin still on you. Up into a TA-DA, both arms up | flourish 0.55, down 1.15, low 2.0, tada 2.45 |
| `jl_walk` | loop 0.8 | **the scuttle**: alternating tetrapod like a real spider (L1 R2 L3 R4, then R1 L2 R3 L4), each foot down 56% of the loop, high quick swings, the body bobbing once per push; the jester rides it level, the horns and bells bouncing. 1.5 m a loop | stepA 0, stepB 0.4 |
| `jl_hang` | held | a crouch, a spring, he rolls over in the air and his feet catch **the web, 5.4 m up** (`jesterlord.js` spins it over him). He hangs under it belly up, the jester head down, arms folded, grinning at you upside down, swinging a little | spring 0.4, catch 1.6 |
| `jl_drop` | 2.7 | lets go of the web, rolls back over as he falls, lands in a squash, springs up into a TA-DA | let go 0.25, land 1.25, tada 1.7 |
| `jl_leg_off` | held | a shot takes his right second leg off at the hip: it **flies up and out, tumbling, and lands 3 m off** on its side with a bounce; the spider drops on that side and the legs either side step in to cover the gap. The jester's arms fly up, his head snaps round to the leg and **his eyes open** (the one time you see them: tiny pupils). He reels, shuts his eyes, straightens his hat and presents the stump: the show goes on, on seven legs. The torn stocking and its stuffing show while the leg is away | hit 0, honk 0.02, eyes 0.06, thud 1.0, reel 2.0, compose 2.75, show must go on 3.75 |
| `jl_leg_back` | 3.1 | he's a puppet: the leg stirs, hops back to him across the floor, flips up into its socket and **screws itself in** | stir 0.1, hop 0.45, hop 1.15, pop 2.55 |

Loops are checked when the clips are written (`python3 tools/blender/cast/jl_clips.py`): no jump at the seam, no
change of speed there sharper than the clip's own corners, every wobble a whole number of times round the loop. It
also measures how far a planted foot slides (the scuttle: 0.4 mm a frame; idle, talk and bow under 8 mm, all at a
foot's tap landing).

### Frame by frame

`make_cast_jester_lord.py --check-clips` poses the skinned model at 60 fps through every clip with the game's sums
and reports the biggest one-frame jump of any vertex. Last run:

| clip | biggest one-frame step | where |
|---|---|---|
| `jl_idle` | 3.3 cm | a front foot drumming |
| `jl_talk` | 4.0 cm | his right hand |
| `jl_bow` | 19.9 cm | his hand whipping up into the TA-DA |
| `jl_walk` | 9.8 cm | a back foot's swing (the scuttle is quick) |
| `jl_hang` | 36.5 cm | a front foot as he rolls over in the leap |
| `jl_drop` | 44.3 cm | a foot as he rolls back over, falling |
| `jl_leg_off` | 32.4 cm | his hand presenting the stump |
| `jl_leg_back` | 43.8 cm | the foot of the leg as it screws in |

The big ones are fast moves on purpose (the leap, the fall, the screw-in turn). Two pops were found and fixed on the
way: the flying leg's turn wrapped round in its euler between two keys (it spun through itself in one frame; every
femur is now kept on the nearest spelling of its turn, and the test checks it), and the screw-in snapped the covering
feet home in one frame.

## Driving him

```js
import { JL } from './jesterlord.js';           // also window.JF_JL
const a = spawnActor('headliner', { look: 'jester_lord', voice: {...} }, [x, y, z], yaw);
JL.play(a, 'jl_talk');                          // any jl_* clip. held ones stay; the rest go back to jl_idle
JL.at(a, 'eyeAt');                              // a marker's (or joint's) world position (THREE.Vector3)
JL.on((ev) => { /* { type: 'jl', mark, id, clip, at } */ });
```

- `jesterlook.js` registers the clips the first time his look is built; plain `play(a, 'jl_bow')` from `actors.js`
  works too. The host can call `jlFrame(dt, cam)` every frame; until it does, the file ticks itself.
- Markers (`JL.at`): `eyeAt` (between his shut eyes: what a camera or a look-at should treat as his eyes), `eyeRAt`,
  `eyeLAt`, `faceAt`, `mouthAt` (on the jaw), `noseTip`, `hatTipR`, `hatTipL` (the horn bells), `palmR`, `palmL`,
  `marotteAt`, `stumpAt` (where the leg comes off), `topAt` (the pennant), `spinneret`, `chestAt`; any joint name works
  too (`femRB`, `tibLC`...).
- The far LOD swaps in past 34 m (30 m coming back).
- **Load him early.** `loadCast(['jester_lord'])` before his scene, so he is the model and not the code puppet.
- Sounds are not made here. The marks are where they go: `tap` and `step` (a bell), `honk` (the leg comes off),
  `thud`, `pop`, `tada`.
- `jl_leg_off` takes off RB only. The parts file has every leg as capsules (`hit.legs`), so a boss fight can aim at
  any leg; the flight can be re-solved for another leg in `jl_clips.py` (`LEG`).

## Look: paint and materials

The house look: a vertex tint times baked AO in `COLOR_0`, small crusty tiling textures with nearest filtering on
box-projected UVs, clear coat on everything. Here the tint carries the colour (the diamonds, stripes and halves are
cut along the mesh's own edges), so **four materials** cover all of him:

- `jl_satin` (the doublet, stockings, hat, collar, gloves, ruff; a satin twill speckle, clear coat 0.5),
  `jl_lacquer` (the spider's shell, ball joints, shoes, the marotte's stick; candy clear coat 1.0), `jl_skin` (his
  face, lids, teeth, lips; rubbery, a few pores), `jl_brass` (bells, finial, rings, spinnerets; metal, crusty).
- Four textures, 64 x 64 each, seeded (rebuilds come out the same).
- **Draw calls**: 9 meshes up close (the two skinned halves split by material), 4 far.

## Triangles and sizes

| | triangles | |
|---|---|---|
| the model | **24,600** | the hat lord shipped 25,247. the spider half 11,568 (tibias 1,792, femurs 1,664, foot bells 1,312, the big top 952 ...), the jester half 13,032 (the head 1,696, the collar bells 672, teeth 576, hat band 576, horns 576 ...) |
| the stump | 672 | hidden until the leg comes off |
| far model (past 34 m) | **3,178** | built by the same code at a quarter of the segments, the small things (teeth, lashes, knees, ankles, bells, toes) left off; still skinned |

`c_jester_lord.glb` **1,293 KB** (under the 1.5 MB goal and the 2 MB cap). One skin, 61 joints, no animations.

## Rebuild

```sh
python3 tools/blender/cast/jl_clips.py      # the clips (and the skeleton) -> public/js/story/jl_clipdata.js, joints.json
blender52 -b --python tools/blender/cast/make_cast_jester_lord.py -- --qa --qa-warn --check-clips --sheet=stance,close
#   builds the model on jl_rig.py, skins it, bakes AO, builds the far model, runs the asset gate on the model, the
#   stump and the far model, writes the glb and the parts file, renders the Blender sheets
#   --no-export --no-ao --no-lod --quick (Workbench sheets) --only-check --islands --blend=<path>
# then, with the game served on a port (headless browsers through pwlock.cjs):
node tools/blender/cast/jlshots.cjs <port> <outDir>          # the actor-path check and the in-game sheets
node tools/blender/cast/jlgame.cjs <port> <outDir>           # story mode at Too HD and Potato
node tools/blender/cast/jlrec.cjs <port> <out.mp4>           # the rehearsal, recorded
```

If his skeleton changes (`jl_rig.py`), run `jl_clips.py` first, then the build. If a marker moves, the build prints
`JF_MK_JS`: copy it into `MK` in `jesterlook.js` (the test fails until you do).

## Checks

- **Asset gate** (`blender-asset-qa`, profile `game`, z-fight eps 0.8 mm, contact 6 mm): **PASS, 0 errors** on the
  model (24,600 tris), the stump and the far model. Fixed on the way: overlapping finger caps in the glove
  (z-fight), closed pieces wound inward (the hat band, the eye diamonds: every closed island is now checked and
  turned out as it is built), a tiny bell loop on the marotte's head whose volume flipped sign, the far model's
  shoes left floating once its ankles went. Accepted warnings: UV overlap (box-projected tiling textures, on
  purpose), 28 duplicate verts (where tube ends meet), back-to-back faces inside the head (the cap's floor, the
  chin's back), the lowest point 2 cm up (the shoes' rounded soles).
- **In the game** (`jlshots.cjs check`: `JL_CHECK ok`): the glb dresses the skeleton, both halves bound to all 61
  joints, every part, marker and joint of the parts file present, markers within 0.1 mm; each of the 8 clips stepped
  through its own code (nothing NaN, every one of its 37 marks fires), the web shows only in the web clips, the stump
  only while the leg is away, every bell within 0.8 degrees of straight down while he hangs upside down; the far LOD
  swaps in and back (24,624 -> 3,178 triangles, 9 -> 4 meshes); the code puppet stands and takes a clip.
- **Tests**: `node --test $(find tests -name "*.test.*")`: 286 pass, 0 fail (his own file: 4).
- **Looked at**: the Blender sheets after every pass, the in-game sheets and every clip strip, the story-mode shots
  and the recording. Passes: (1) the first build; (2) a bigger head and torso, a smaller big top; (3) the eyes (they
  were scaled twice), the hood, a thinner nose, the marotte off his face; (4) the clips: a shallower bow that keeps
  his grin on you, the leg-off lurch rolling about the thorax instead of the floor, the arms solved in the spine's
  frame, the flying leg's turn, the smoother leap and drop.

## Weak spots (honest list)

- **Timing was judged from contact strips, a 60 fps step check and a software-GL recording** (a few frames a
  second), not watched at full speed with sound.
- **The leap into the web and the drop are fast** (a leg tip moves 34-40 cm in a 60 fps frame at the quickest): meant
  as cartoon snaps, but at low frame rates they can look like a cut.
- **The web is drawn by the rehearsal**: a flat disc of silk threads 5.4 m up. A mission would put him under its own
  web; he needs about 5.4 m of headroom and 5 m of floor to hang.
- **Only RB comes off** in the clip set; other legs need the flight re-solved.
- **Nothing collides**: in the deep bow his head dips between his front legs (seen from the side a front femur
  crosses in front of his face), and the hands and the marotte are posed clear of the legs, not kept clear.
- **The flips turn over about his middle** but the legs are solved only at the keys: mid-leap and mid-fall the legs
  are tucked, not reaching for anything.
- **The far model** is a coarser build, not a decimation: its colours are flat mixes of the diamonds.
- **His mouth only opens as the dummy jaw**: no lip-sync shapes. His shut eyes have no blink (they are always shut).
- Not done: sound, damage states beyond the leg, cloth, his boss fight, Madame Velvet.
