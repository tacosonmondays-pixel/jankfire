# Madam Chair and Oversight: model, clips and how to drive her

The presentation half of [HAT_LORD.md](HAT_LORD.md) (who she is, the Big Heart, her Act I scene). Working id
`hat_lord`. **She is not placed in any mission, and nothing here does damage.** To see her in the game:
`?story=1&hatlord=1` stands her 7 m in front of you and runs her whole set on a loop with a caption for each clip.

**Current build: `tools/blender/cast/rebuild_hat_lord_tripo.py`**, which rebuilds her from the owner's own Tripo model
([`../cast_refs/hat_lord_tripo_owner.glb`](../cast_refs/hat_lord_tripo_owner.glb), licence note in
[`../cast_refs/TRIPO_LICENCE.md`](../cast_refs/TRIPO_LICENCE.md)). The older code-built version
(`make_cast_hat_lord.py` with `hatkit.py`, `hatbody.py`, `hathat.py`, `hatposes.py`) is kept in the repo but no
longer writes the shipped model; its sheets (`c_hat_lord.jpg`, `c_hat_lord_closeups.jpg`, `c_hat_lord_poses.jpg`,
`c_hat_lord_silhouette.jpg`) show that old model.

The owner's sketch: [`../cast_refs/hat_lord_owner_sketch.jpg`](../cast_refs/hat_lord_owner_sketch.jpg). The owner's
Tripo renders: `hat_lord_tripo_owner_turn.png`, `hat_lord_tripo_owner_anim.png` (same folder).

| what | in the game's renderer (`docs/story/cast/`) | from Blender (`tools/blender/sheets/`) |
|---|---|---|
| before and after: Tripo grey, the rebuild, the old code-built model; front, three-quarter, side, back | | `c_hat_lord_tripo_compare.jpg` |
| close-ups: her eyes, her right eye, the laced fingers, the socket, the band open (teeth), her hand, the raised finger, the cape from behind, the eyeless reveal, the crown's eyes, the feeler, the brim from below | `hl_game_closeups.jpg` | `c_hat_lord_tripo_closeups.jpg` |
| her silhouette beside the owner's sketch | `hl_game_silhouette.jpg` | |
| turnaround with a 1.8 m figure | `hl_game_turn.jpg` (the mannequin is you) | |
| one moment from each clip | `hl_game_poses.jpg` | |
| a contact strip per clip (12 frames, marks called out) | | `c_hat_lord_clip_<name>.jpg` (made in the game's renderer by `hlshots.cjs clips`) |
| in the real game, story mode | `hl_ingame_hd_*.jpg` (Too HD: idle at 7 m, talk, the offer, the lunge, the reveal, the hat off, from 30 m), `hl_ingame_potato_*.jpg` | |

In every sheet "her right" is +x: the low wing with the feeler hanging off it. Her left is the long wing.

## What came from Tripo, and what was added

The Tripo file is one fused mesh (10,336 triangles, one grey material, no textures) on a Mixamo rig (65 bones, 2
clips). The rebuild keeps **Tripo's shape**, and replaces its rig, clips and paint.

**Kept from Tripo** (cleaned, cut apart, holes closed): her whole figure and proportions (2.96 m, the long thin
limbs, the arms hanging down with long fingers, the pointed heels), her head and face (the long wedge of a head,
thin nose, the lips as their own shells), the suit's shape, the cape (two long panels and the slit up the back),
the collar with its two star brooches, the ring round the chest socket, the hat's brim (the huge lopsided wing,
the feeler hanging off her right side with its bulb), the crown with its ring of eye mounds, and the hat's fingers
laced over her face.

**Cleaned up**: the fused mesh split into islands before welding (so the lips and a stray quad are not glued on),
stray triangles dropped, the hat cut off at the brim and both sides closed (a skull dome tops her head at 2.96 m,
the hat gets a hollow the skull sits in), the face's two eye holes under the fingers and two pin holes at the
mouth closed (the reveal shows smooth skin with shallow hollows), a hole in the cape's hide on her left closed,
the laced fingers cut down the middle into two hands with rounded fingertips, Tripo's lumpy eye blobs replaced
by clean balls at their place and size, every non-manifold edge split and the normals made consistent.

**Added, because Tripo did not have it**:

- **The band's mouth**: the crown is cut off the brim along the band, with an overhanging upper lip, a lower lip,
  gums, a roof and a floor; **two rings of 40 teeth** (one on the crown, one on the brim) and **five brass clasps**
  with rivets that hold it shut. `crown.x` opens it.
- **The neck the hat lunges on**: a stalk (5.2 cm radius) from the top of her skull into the hat, skinned to
  `hatNeck` and `hatNeckB`, so it stretches out and bends.
- **Her brown eye pair** at the front of the crown, in the biggest of Tripo's eye mounds: balls of 21 mm radius
  (life size for a woman 1.7 times a person's height), sunk in an almond opening of her own pale skin that grows
  out of the crown's flesh (a pink flush blending into the crimson), heavy upper lids tucked under that skin
  (`lidHR`, `lidHL` slide them down to shut; her left one sits lower), a wet pink lower rim, no brows. The whites
  are off-white and shaded with faint veins, the irises brown with small pupils.
- **The creature's eyes**: 14 balls (yellow, grey, red, blue, ochre, green, cream), five of them with lids of hat
  flesh (`lidCa` .. `lidCe`, the weak points).
- **The chest socket's depth and brass lip**: Tripo's ring becomes brass; the chest inside it is cut out and made
  round, then sunk 8.5 cm with ridged walls, dark wet red at the lip going to black, three tied-off vessel stubs at
  the bottom, and a bruise on the skin round it.
- **Paint** in the house look (below), a clean V neckline between her skin and the suit, and the cape's lining
  told apart from its hide by ray tests (pink only on the inside).

## Files

| file | what |
|---|---|
| `public/models/cast/c_hat_lord.glb` | the model: **skinned** `part_<joint>__<tag>` meshes on one skin whose 52 bones are her joints by name, plus a far LOD in rigid `part_<joint>__lod` pieces |
| `public/models/cast/c_hat_lord.parts.json` | every named part (joint, box), her joints and their rest, markers, the look-at marks, hit boxes, `skinned: true` |
| `public/js/story/hatlook.js` | her skeleton (`HATLORD`, `FIT`: the joints moved onto the Tripo body, `EXTRA`: her own 38 joints), the code puppet (the fallback), the markers (`MK`), her faces |
| `public/js/story/hatlord.js` | `HL`: clips, marks, the hat's look, her walk, the far LOD, the rehearsal |
| `public/js/story/hl_clipdata.js` | the clips as key poses. **Generated** by `tools/blender/cast/hl_clips.py` |
| `tools/blender/cast/rebuild_hat_lord_tripo.py` | **the build** (current). `hltripo.py` (import, cut, cap, bridge), `hlskin.py` (skin weights and the poser), `hl_fit.py` (reads the Mixamo bones and prints the joint fit) |
| `tools/blender/cast/make_cast_hat_lord.py` | the old code-built model (kept, not current) |
| `tools/blender/cast/hl_clips.py` | the clips: key poses, a small reach solver, the loop check. Writes `hl_clipdata.js` |
| `tools/blender/cast/hljoints.cjs`, `hlshots.cjs`, `hlgame.cjs` | her skeleton into `joints.json`; the in-game sheets and the actor-path check; the story-mode screenshots |
| `tests/story/hat_lord.test.mjs` | the parts file, the glb, the skeleton and the clips agree |

Touched in shared files: `looks.js` (the import and the `hat_lord` look line, and **skinned parts in `dressCast`**:
a `SkinnedMesh` in a cast glb is bound to the skeleton's own joints by bone name, at the rest the joints have when
dressed, and those joints lose their code meshes; rigid parts work as before), her entry in
`tools/blender/cast/joints.json`, two rows in `tools/blender/README.md` (the current build, and the old one marked as
old). Nothing in `actors.js`, `boot.js`, the
content files or the server.

## Who you are looking at

- **Tall and narrow.** 2.96 m to the top of her head, 3.74 m to the top of the hat, the brim 3.17 m across. Long
  wading-bird legs on pointed heels, a narrow suit, the arms hanging straight down with hands as long as a
  forearm and fingers like a spider's. Lavender-grey skin, dark burgundy suit.
- **The cape** hangs from her collar in two long dark burgundy panels, a slit up the back, the lining wet pink.
  Two brass star brooches at the collar, a brass yoke along the shoulders.
- **The chest socket**, left of the breastbone in the V of the suit: a round hole with a thick brass lip, 8.5 cm
  deep, red walls going black, cut vessels at the bottom, bruised skin round it. It is number 1.
- **The face**: Tripo's long wedge with a thin nose and small closed lips. The hat's eight fingers are laced
  across where her eyes would be; under them, smooth skin.
- **The hat, Oversight**: a wet crimson animal, the brim a huge lopsided wing (glossy crimson on top, veined pink
  underneath), the feeler hanging off her right side with a bulb on the end. The crown is ringed with eyes: hers
  at the front (the brown pair, calm, heavy-lidded) and 14 of its own. The band is a mouth: it opens into two rings
  of teeth. It sits on a neck rooted in her skull.

## Her joints

The 14 cast joints, and 38 of her own (`hatlook.js` `EXTRA`). For the rebuild the skeleton was **refitted to the
Tripo body**: `HATLORD` sets her proportions (leg scale 2.0, torso 0.62 m, upper arm 0.58 m, forearm 0.43 m), and
`FIT` moves each cast joint onto the Tripo rig's matching bone, with the rest turns of its A-pose (arms down). The
`EXTRA` joints (hat, brim, eyes, lids, fingers, cape) were refitted to where the Tripo parts are. Rest spots and
turns are in the parts file and `joints.json`.

| joints | on | what |
|---|---|---|
| `hatNeck` > `hatNeckB` > `hat` | head | the neck (the stalk stretches between them) and the hat |
| `crown` | hat | hinged at the back of the band: `crown.x` + opens the mouth |
| `brimR` > `brimRb` > `feeler` > `feelerB` | hat | her right wing, its outer part, the feeler |
| `brimL` > `brimLb` | hat | her left wing and its outer part |
| `brimF`, `brimB` | hat | front and back of the brim |
| `growthA`, `growthB`, `growthC` | crown | the eye clusters: her right, over the back, her left front |
| `eyeHR`, `eyeHL`, `lidHR`, `lidHL` | crown | HER eyes (turn to look) and their upper lids (`.x` about -1 shuts) |
| `lidCa` .. `lidCe` | growths, crown | a lid for each of the creature's five lidded eyes |
| `bandR`, `bandL` | head | the hat's fingers over her face: `bandR.y` - / `bandL.y` + swing them open |
| `capeR`, `capeL` | spine | the cape's halves |
| `idxR` > `idxRb`, `finR` > `finRb`, `thumbR` (and `L`) | hands | index finger, the other three together, thumb: two joints each, `.x` - curls |

**Skinning**: every vertex is weighted to up to 4 of these joints. The weights come from where Tripo's Mixamo bones
run (which finger, which limb), mapped onto our joints and blended across each joint over a width that suits it
(hip 12 cm, knee 9.5 cm, shoulder 7.5 cm, elbow 5.5 cm, wrist 3.5 cm, fingers 2-2.6 cm), gated so a limb only takes skin within
its own radius (the chest beside a shoulder stays on the chest), then smoothed and cut to 4. The brim is weighted
in lobes along its joint chains, the crown to its clusters, the cape to its halves with the collar blended to the
spine. Eyes, lids, teeth, clasps and the socket's vessels are rigid on one joint each. Weights are stored as
normalized bytes.

## Parts and markers

Named pieces (`part_<joint>__<tag>`, `L.parts[tag]` after `buildLook`): `body`, `cape`, `yoke`, `socket`, `brim`,
`crown`, `neck`, `clasps`, `teeth`, `bands`, `herEye`, `herLid`, `herOrbit` (her eye sockets: the almond of skin,
the wet lower rims), `hatEyes`, `hatLid`, and `lod` (the far model). The old model's `front`, `hair` and `gum`
are gone (nothing used them by name).

Markers (`HL.at(a, name)` gives the world point), all re-measured on the new model and copied into `MK`:
**`eyeAt`, `eyeHRAt`, `eyeHLAt`** (her eyes: **a camera or a look-at should treat these as her eyes, not her
face**), `faceAt`, `mouthAt`, `socketAt`, `hatMouthAt`, `hatTopAt`, `weakA` .. `weakE` (the creature's five lidded
eyes: the weak points), `brimTipR`, `brimTipL`, `feelerTip`, `palmR`, `palmL`, `fingerTipR`, `fingerTipL`. The
parts file's `look` block says the same in data; `hit` has a head box, a hat box, the weak points, her eye pair,
her hands and the socket. Her eye height for the game's look is 3.16 m.

## Clips

Authored in `hl_clips.py` as a few key poses each with an ease; `hatlord.js` plays them. She is **always** in one of
them (a spawned `hat_lord` with nothing playing is put into `hl_idle`), so a clip owns the whole of her: the cast's
joints are set outright, her own turn from their rest. The clips were **re-keyed for the Tripo body** (long legs,
long arms, arms hanging down at rest): her stance is the Tripo pose, the walk's stride is 1.74 m a loop, reaches
are re-solved for the longer arms, and the crouches keep her feet and cape above the floor. On top of the keys:

- **Overlap**: the far end of anything arrives late (outer wings, feeler, eye clusters, fingers).
- **The look**: the hat turns to put her eyes on whoever she looks at (`a.lookAt`, else the camera within 12 m, or
  `HL.look(a, point)`). Her eyes get there first, the hat follows, and her face stays level. Each clip says how much.
- **The walk**: whenever her root moves, `hl_walk`'s legs are laid over whatever clip is playing, run by distance
  (1.74 m a loop), so her feet do not slide at any speed.
- One clip runs into the next (0.3 s from wherever the last had her). A clip that ends goes back to `hl_idle`.

| clip | length | what happens | marks (s) |
|---|---|---|---|
| `hl_idle` | loop 8.0 | she barely moves. the hat breathes, wing against wing; the eye clusters pulse; the feeler twitches; her eyes blink together; the creature's five lids blink alone | |
| `hl_walk` | loop 2.0 | the stalk: knee first, like a wading bird, 1.74 m a loop. the hat sways against her hips, the wings trail | stepR 0, stepL 1.0 |
| `hl_duck` | 4.9 | under something low: the hat turns end on and folds its sides down, she sits back on her heels and goes under. She still needs an opening about 2.7 m high and 2.4 m wide | turn 0.4, folded 1.1, low 2.0, up 3.6, open 4.4 |
| `hl_talk` | loop 6.0 | the hat tips to hold her eyes on you; her right hand turns over twice | |
| `hl_offer` | held | one long hand out, palm up, at 1.5 m (the arm twists to turn the palm). the hat looks at the hand, then at you | lift 0.7, out 1.5, look 2.4 |
| `hl_bow` | 2.6 | a small bow, a hand on her chest. the hat's neck straightens as she goes down: it stays level, watching | low 1.1, rise 1.75 |
| `hl_lunge` | 4.8 | the hat goes for what is in front of her: wings up, out on its neck, the band open on its teeth. one raised finger. it goes back | fix 0.2, aye 0.5, stop 0.72, finger 1.5, back 2.0, shut 3.6, home 4.2 |
| `hl_reveal` | held | the hat lifts; its fingers open off her face: no eyes | lift 0.8, unlace 1.2, shown 2.2, looks 3.4 |
| `hl_reveal_end` | 2.2 | the fingers lace back over, the hat comes down | laced 0.9, down 1.4 |
| `hl_attack_tell` | held | it rears up and round to her left, low wing high | aye 0.25, up 0.9 |
| `hl_strike` | 1.5 | the wing sweeps round in front of her and carries past | sweep 0.16, hit 0.3, past 0.5, recover 1.0 |
| `hl_stagger` | 1.4 | knocked back a step: every eye on the hat shuts, the wings fly up | hit 0.02, foot 0.6 |
| `hl_hat_off` | held | the hat tears up and beats above her on its stretched neck; she kneels, eyeless, the cape kept off the floor | tear 0.6, free 1.4, knees 3.2, down 3.9 |

Loops are checked when the clips are written (`python3 tools/blender/cast/hl_clips.py`): no jump at the seam, and
no change of speed there sharper than the clip's own corners. **Every key carries every channel its clip touches.**

### The skin through every clip (frame by frame)

`rebuild_hat_lord_tripo.py --check-clips` poses the skinned model at 60 fps through every clip with the game's own
sum (the same skinning maths as three.js) and reports the biggest one-frame jump of any vertex (a pop) and the
worst squash and stretch of the body's edges (a collapsing knee or a candy-wrapper wrist shows as an edge gone
short or long). Last run:

| clip | biggest one-frame step | worst squash | worst stretch |
|---|---|---|---|
| `hl_idle` | 5.6 cm (brim) | 52% (armpit) | 127% |
| `hl_walk` | 5.4 cm | 12% (behind the knee) | 284% (seat) |
| `hl_duck` | 10.2 cm (brim, folding) | 13% (behind the knee) | 333% (seat) |
| `hl_talk` | 2.5 cm | 39% (fingers) | 338% (armpit) |
| `hl_offer` | 4.9 cm | 17% (armpit) | 385% (top of the shoulder) |
| `hl_bow` | 9.1 cm | 27% (elbow) | 282% (armpit) |
| `hl_lunge` | **33.7 cm** (brim, the bite) | 28% (fingers) | 376% (armpit) |
| `hl_reveal` / `_end` | 2.8 cm | 52% | 134% |
| `hl_attack_tell` | 15.1 cm (brim, rearing) | 52% | 238% |
| `hl_strike` | **83.6 cm** (brim tip, the sweep at 0.10 s) | 42% (cape at the collar) | 238% |
| `hl_stagger` | **47.1 cm** (the flinch at 0.02 s) | 43% (cape at the collar) | 363% (armpit) |
| `hl_hat_off` | 12.8 cm (brim) | **3%** (behind the knee, kneeling) | 269% |

The three big steps are meant: the strike's wing tip moves at about 50 m/s, the stagger's flinch and the lunge's
bite are deliberate snaps. The stretch numbers are single short edges in creases (the armpit when an arm lifts,
the seat when she sits back); the squash is the inside of a fold (behind the knee, inside the elbow). See weak
spots.

## Driving her

```js
import { HL } from './hatlord.js';           // also window.JF_HL
const a = spawnActor('madam_chair', { look: 'hat_lord', voice: {...} }, [x, y, z], yaw);
HL.play(a, 'hl_offer');                      // any hl_* clip. held ones stay; the rest go back to hl_idle
HL.look(a, [x, y, z]);                       // what the hat looks at (null = nothing, undefined = back to the default)
HL.at(a, 'eyeAt');                           // a marker's world position (THREE.Vector3)
HL.on((ev) => { /* { type: 'hl', mark, id, clip, at } */ });
```

- `hatlord.js` registers the clips the first time her look is built; plain `play(a, 'hl_bow')` from `actors.js`
  works too.
- The host can call `hlFrame(dt, cam)` every frame next to `otFrame` (one import and one line in `boot.js`). Until
  it does, the file ticks itself.
- Scenes: aim a close-up at `eyeAt`, not her head. `hl_duck` is in place: walk her through while it plays.
- Past 34 m the far LOD swaps in (30 m coming back).
- Her mouth is Tripo's (closed lips, it does not move): the game's code mouth is hidden when the model is loaded.
- **Load her early.** Story mode gives the cast 12 s to load; on a slow machine her skinned glb can miss that and
  she shows as the code puppet. `loadCast(['hat_lord'])` before her scene avoids it (`hlgame.cjs` does).
- Sounds are not made here. The marks are where they go: `aye` (several voices at once), `stop`, `finger`, `tear`.

## Look: paint and materials

House look: a vertex tint times baked AO in `COLOR_0`, small tiling textures with nearest filtering on box-projected
UVs (the crusty speckle), clear coat (`KHR_materials_clearcoat`) on everything wet or shiny.

- **11 materials**: `hl_skin` (lavender-grey, her face, hands, eye skin; flushed pink round her eyes), `hl_suit` (dark
  burgundy), `hl_hat` (wet crimson: the brim's top, the crown, the fingers, the creature's lids), `hl_under` (the
  brim's veined pink underside, the neck), `hl_mouth` (the socket's and the band's wet insides), `hl_dark` (the
  throats), `hl_cape` (dark burgundy hide), `hl_lining` (pink), `hl_brass` (the yoke, brooches, clasps, the socket's
  lip), `hl_eye`, `hl_teeth`.
- **9 textures**, all small (the biggest 128 x 128), including an eye atlas (her brown pair, the creature's colours).

## Triangles and sizes

| | triangles | |
|---|---|---|
| the model | **25,247** | budget about 25k, cap 30k. body 4,290; brim 3,834; crown 3,358; the creature's eyes 3,528 and their lids 1,280; the two rings of teeth 2,400; the cape 1,344; clasps 1,220; her eyes 792, lids 592, eye skin 912; the fingers over her face 845; the socket 360; the neck 336; the yoke and brooches 156 |
| far LOD (past 34 m) | **2,349** | the body, cape, brim, crown and neck decimated together, then cut into rigid pieces by the joint that moves each most |
| everything in the file | 27,596 | |

`c_hat_lord.glb` **1,137 KB** (under the 1.5 MB goal and the 2 MB cap). One skin, 52 bones, no animations (Tripo's
Mixamo rig and its 2 clips are dropped). About 38 draw calls up close (26 skinned parts, split by material).
Parts file 16 KB, `hl_clipdata.js` about 72 KB.

## Rebuild

```sh
python3 tools/blender/cast/hl_clips.py                       # the clips -> public/js/story/hl_clipdata.js (prints the reach misses and the loop check)
blender52 -b --python tools/blender/cast/rebuild_hat_lord_tripo.py -- --qa --qa-warn --check-clips --sheet=compare,close --old=<old c_hat_lord.glb>
#   imports the Tripo glb, cuts and cleans it, adds the missing parts, paints, weights and skins it to joints.json,
#   checks every clip frame by frame, bakes AO, makes the far LOD, runs the asset gate on the model and the far
#   model, writes the glb and the parts file, renders the compare and close-up sheets (about 4 minutes on 4 cores)
#   --no-export  --no-ao  --no-lod  --quick (Workbench)  --only-check (stop after the clip check)  --blend=<path>
#   --old=<glb> is the old code-built model for the compare sheet's third column (build it with make_cast_hat_lord.py)
# then, with the game served on a port (headless browsers through pwlock.cjs):
node tools/blender/cast/hlshots.cjs <port> docs/story/cast   # the actor-path check and the in-game sheets
node tools/blender/cast/hlgame.cjs <port> docs/story/cast    # story mode at Too HD and Potato
```

If her skeleton (`HATLORD`, `FIT` or `EXTRA` in `hatlook.js`) changes, run `node tools/blender/cast/hljoints.cjs
<port>` first, then rebuild. If a marker moves, the build prints `JF_MK_JS`: copy it into `MK` in `hatlook.js` (the
test fails until you do). If the Tripo file changes, check `hl_fit.py`'s numbers and the cut heights in
`hltripo.py` (they are measured on this file).

## Checks

- **Asset gate** (`blender-asset-qa`, profile `game`, z-fight eps 0.8 mm): **PASS** on the model (25,247 tris,
  contact tolerance 6 mm) and on the far model (2,349 tris, 4 cm). Fixed on the way: inconsistent winding where
  Tripo's mesh folded on itself (non-manifold edges split, normals recalculated), z-fights between the skull and
  the hat's hollow, the two hands' cut ends, her eyes and lids, the lips and the brim, and the lids and the eye
  skin; zero-area UVs on the backs of the eyes; the far model's missing UVs. Accepted warnings: UV overlap (box
  projected tiling textures, on purpose), a few duplicate verts where non-manifold edges were split, back-to-back
  faces between her lids and the skin they tuck under (they slide out when she blinks).
- **In the game** (`hlshots.cjs check`: `HL_CHECK ok`): `buildLook('hat_lord')` dresses the glb on the skeleton,
  every skinned part bound, every part, marker and joint of the parts file present, markers within a few tenths of
  a millimetre of the file; each of the 13 clips is stepped through its own code: joints move, nothing goes NaN,
  all 40 marks fire; the far LOD swaps in and back; the code puppet still stands and takes a clip.
- **Tests**: `node --test tests/story/*.test.mjs tests/browsable.test.mjs`: 46 pass.
- **Looked at**: the compare and close-up sheets after every pass, the in-game sheets and clip strips, the
  story-mode shots. Look passes on the rebuild: (1) the first split and skin; (2) arms down like the owner's model,
  clips re-keyed, cape lining and collar; (3) the lead's notes: her eyes (cartoony lids and whites), pink blotches
  on the cape and chest, a flat star of a socket, a white panel round it, a pink cape.

## Weak spots (honest list)

- **Deep bends collapse a little**, as plain skinning does: behind the knee in the kneel (an edge goes to 3% of its
  length) and the duck, inside the elbow in the bow. The seat stretches when she sits back (duck, walk), and the
  armpit when an arm lifts (offer, talk, lunge). From the front at play distance it reads; up close behind her
  knees it creases hard.
- **No ankles**: her shoes ride rigid on the shin, so a toe can tip into the floor at the end of a stride.
- **The cape is stiff skin, not cloth.** It bends with her spine and swings its halves, but has no folds that move;
  in the kneel it is lifted behind her like a train to keep it off the floor.
- **The neck in `hl_hat_off`** stretches into a long cord from her skull to the hat (skin cannot tear). The scene
  should swap in a free hat at the `free` mark if it needs to fly off.
- **Her mouth does not move**: Tripo's lips are kept and the code mouth is hidden, so no jaw flap when she talks.
- **`hl_duck` needs about 2.7 m x 2.4 m**: the hat is huge. She will not fit a house door.
- **The strike's wing whips** 84 cm in one frame at its fastest: meant, but at low frame rates it can look like a cut.
- **Box-projected UVs**: the crusty speckle tiles, and on long curved pieces (the brim, the cape) a seam where the
  projection changes axis can show up close.
- **Her eyes are still a little stylised**: the pink flush round them reads as a soft plate in strong light, and
  the lids are smooth (no lashes). They read as calm, human and heavy-lidded from about 2 m.
- **The far LOD is rigid pieces** (cut by joint): past 34 m a gap can open at a bent knee or elbow. At that
  distance it is a few pixels.
- **The look is approximate**: worked out from her yaw and height, not her posed bones, so in a deep bow or the
  duck the hat's aim is a few degrees off.
- **Timing was judged from contact sheets and a 60 fps step check**, not watched at speed with sound.
- Not done: sound, damage states, cloth, a free-flying hat, lip-sync, her in a mission.
