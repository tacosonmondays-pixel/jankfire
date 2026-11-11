# Madam Chair and Oversight: model, clips and how to drive her

The presentation half of [HAT_LORD.md](HAT_LORD.md) (who she is, the Big Heart, her Act I scene). Working id
`hat_lord`. **She is not placed in any mission, and nothing here does damage.** To see her in the game:
`?story=1&hatlord=1` stands her 7 m in front of you and runs her whole set on a loop with a caption for each clip.

The owner's sketch: [`../cast_refs/hat_lord_owner_sketch.jpg`](../cast_refs/hat_lord_owner_sketch.jpg).

| what | in the game's renderer (`docs/story/cast/`) | from Blender (`tools/blender/sheets/`) |
|---|---|---|
| her silhouette beside the owner's sketch | `hl_game_silhouette.jpg`: the sketch, then from 30 m enlarged, the far model enlarged, and true size on a 16:9 screen | `c_hat_lord_silhouette.jpg` (front on, no perspective) |
| turnaround with a 1.8 m figure | `hl_game_turn.jpg` (the mannequin is you) | `c_hat_lord.jpg` |
| close-ups: the hat from above, its underside from where you stand, the band open, the growths, HER eye pair open and shut, one of its own eyes, her face under the brim, the eyeless reveal, her hands, the socket, the bar, the cape, the feeler, the far model | `hl_game_closeups.jpg` | `c_hat_lord_closeups.jpg` (also: her right eye very close, the growths over the back, the hat from behind) |
| one moment from each clip | `hl_game_poses.jpg` | `c_hat_lord_poses.jpg` |
| a contact strip per clip (marks called out) | `hlshots.cjs <port> <dir> clips` writes `hl_clip_<name>.jpg` (12 frames; not kept in the repo) | `c_hat_lord_clip_<name>.jpg` (10 frames, Workbench) |
| in the real game, story mode | `hl_ingame_hd_*.jpg` (Too HD: idle at 7 m, talk, the offer, the lunge, the reveal, the hat off, from 30 m), `hl_ingame_potato_*.jpg` | |

In every sheet "her right" is +x: the low wing and the feeler. Her left is the long wing.

## Files

| file | what |
|---|---|
| `public/models/cast/c_hat_lord.glb` | the model: `part_<joint>[__<tag>]` meshes at the rest pose, like every cast model, plus a far LOD per joint |
| `public/models/cast/c_hat_lord.parts.json` | every named part (joint, box), her joints and their rest, markers, the look-at marks, hit boxes |
| `public/js/story/hatlook.js` | her skeleton (`HATLORD`, and `EXTRA`: her own 36 joints), the code puppet (the fallback), the markers, her faces (`chair`, `chair_host`, `chair_flat`, `chair_hurt`) |
| `public/js/story/hatlord.js` | `HL`: clips, marks, the hat's look, her walk, the far LOD, the rehearsal |
| `public/js/story/hl_clipdata.js` | the clips as key poses. **Generated** by `tools/blender/cast/hl_clips.py` |
| `tools/blender/cast/make_cast_hat_lord.py` | the build. `hatkit.py` (kit), `hatbody.py` (the woman, the cape), `hathat.py` (the hat), `hatposes.py` (pose sheets) |
| `tools/blender/cast/hl_clips.py` | the clips: key poses, a small reach solver, the loop check. Writes `hl_clipdata.js` |
| `tools/blender/cast/hljoints.cjs`, `hlshots.cjs`, `hlgame.cjs` | her skeleton into `joints.json`; the in-game sheets and the actor-path check; the story-mode screenshots |
| `tests/story/hat_lord.test.mjs` | the parts file, the glb, the skeleton and the clips agree |

Touched in shared files: **two lines in `looks.js`** (an import and `hat_lord: () => hatLordLook({...})`), her entry
in `tools/blender/cast/joints.json`, a row in `tools/blender/README.md`. Nothing in `actors.js`, `boot.js`, the
content files or the server.

## Who you are looking at

- **Tall and narrow.** 2.96 m to the top of her head, 3.4 m with the hat. Shoulders 0.4 m, hips at 1.5 m, legs like
  a wading bird's with a point where each knee should be round. Her stance (every clip starts from it): arms held out
  from the shoulder along the bar, forearms dropping to hands held just outside the cape's widest point, long fingers
  pointing down. The fingers have a joint too many.
- **The cape** is the sketch's body: two stiff halves (`capeR`, `capeL`) hinged on a pin down her back. Narrow at her
  collar, round-shouldered, 1.16 m at the hands, then long straight lines down to 0.41 m just above the floor and a
  small flare at the hem. Its hide bellies and folds (two and a half folds a half, deeper toward the hem); its back
  is two domed wing cases either side of a seam with a spine of eight knuckles of hide over the pin, a pair of gills
  each side (slits with swollen lips, dark inside), growth lines across, raised veins. Inside: wet pink, veined; the
  front edges turn back pink, so at rest a sliver of each dark shin shows between them, and in the walk the halves
  swing apart and the legs come through. **The bar** is its yoke: 1.46 m, satin on top, the ends turned down to
  brass points, two brass hooks over her own shoulders. Nothing hangs from the ends.
- **Her suit**: a fitted jacket with a flared skirt to it, satin lapels in a deep V, two brass buttons, narrow
  trousers with a crease, pointed court shoes with brass toe caps. In the V, left of the breastbone: **the socket**.
  A hole 6.6 cm across and 8.5 cm deep, its wall ridged like the inside of a vessel, wet red at the lip going to
  black; at the bottom three cut vessels, tied off. A thin brass lip with four small rivets is set into a swelling of
  bruised skin round it. No cap on it. It is number 1.
- **Her head** is a long wedge, 0.62 m, most of it up inside the hat. A small mouth (the game's own mouth rig, dark
  plum, needle teeth), a thin ridge of nose, a small chin. Where eyes would be: smooth skin and two shallow hollows.
  Hair slicked back into a knot at the nape.
- **The hat, Oversight.** A dark wet animal with a brim, more bat's wing than umbrella. The brim is skin on
  eighteen unevenly spaced ribs, and every rib is a row of bones: most are a finger's four, a few are an arm's two,
  each a different thickness, knuckled, bowed, wandering sideways along its length (the skin bends with it). Some
  rib tips ride high and some sag, so the edge rises and falls; the skin hangs back between the tips by a different
  amount in every gap, three gaps have torn back toward the crown (ragged), three old tears have grown back as
  raised pink scars. Where each big rib leaves the crown the skin is thick over it, a fleshy root. Veins branch over
  the top. The long wing droops under its own weight over its last half metre. Six pieces that hinge: her right
  wing (low, in two parts, ending in a two-jointed feeler with a bead and a barb), her left wing (long, in two
  parts), front, back. The underside is veined membrane and it is what you see from 1.8 m; the top is drier hide
  (`hl_hide`). **The crown is its body and the band is its mouth**: the crown lifts off the band and there are teeth
  all the way round; five brass clasps keep it shut. A second ring of teeth sits round the hole her head goes
  through, resting on her. It rides on **a neck of two sliding tubes** rooted in the top of her skull.
- **The growths are people and organs, not fruit**, heaviest on her right: three knuckled fists, three ears, a nose,
  back teeth come up through gum in three places, two small hands, and sacs on stalks from a wart's size to a fist's,
  wrinkled, leaning and bending, each with a puckered lip and a throat; liver, bruise, grey dead skin and sallow,
  dark where they leave the crown and in every crease, raw toward the lip. The hat's flesh is veined, not speckled.
- **Seven eyes on the hat. Two are hers.** A matched brown pair, life size and a little over (1.35x), each in its own
  socket sunk into the front of the crown: an almond of her own grey skin from under the lids out to where it was
  grafted in, raw at the graft, shadowed under the eye, a crease over the lid; the hat's flesh swells round it in a
  rim, heaviest over the top. Heavy upper lids (her left one 4 mm lower and more shut), a wet pink lower
  rim, fine lashes, no brows: a faint scar on the rim where her right one was. The iris is a dark brown with a small
  pupil, the white a little bloodshot. They blink together and look at whoever she is talking to: a calm, level
  stare. The other five are the creature's: different sizes, slit or clouded pupils, bile yellow, grey, red-rimmed,
  each on a mound with its own lid, blinking alone. One looks straight up. One looks backward.
- **The bands in the sketch** are the hat's two hands: eight fingers laced across her face where her eyes would be,
  hinged at her temples (`bandR`, `bandL`). They swing open for the reveal.

## Her joints

The 14 cast joints, and 36 of her own (`hatlook.js` `EXTRA`; rest spots and turns are in the parts file):

| joints | on | what |
|---|---|---|
| `hatNeck` > `hatNeckB` > `hat` | head | the neck (two tubes that slide out of each other) and the hat. The hat's rest is the sketch's tilt: 0.24 forward, 0.245 down to her right |
| `crown` | hat | hinged at the back of the band: `crown.x` + opens the mouth |
| `brimR` > `brimRb` > `feeler` > `feelerB` | hat | her right wing, its outer part (folds on a line 0.84 m out), the feeler |
| `brimL` > `brimLb` | hat | her left wing and its outer part (folds 1.04 m out) |
| `brimF`, `brimB` | hat | front and back of the brim |
| `growthA`, `growthB`, `growthC` | crown | the clusters: her right (the big one), over the back, her left front |
| `eyeHR`, `eyeHL`, `lidHR`, `lidHL` | crown | HER eyes (turn to look) and their upper lids (`.x` about -1 shuts) |
| `lidCa` .. `lidCe` | growths, crown | a lid for each of the creature's five eyes |
| `bandR`, `bandL` | head | the hat's fingers over her face: `bandR.y` - / `bandL.y` + swing them open |
| `idxR` > `idxRb`, `finR` > `finRb`, `thumbR` (and `L`) | hands | index finger, the other three together, thumb: two joints each, `.x` - curls |

## Parts and markers

Named pieces (`part_<joint>__<tag>`, `L.parts[tag]` after `buildLook`): `cape`, `yoke`, `socket`, `front` (the V:
chest, lapels, buttons), `hair`, `bands`, `clasps`, `gum` (the ring of teeth round the hole), `herOrbit` (her eye
sockets: lower lids, the sunk skin, the hat's swollen rim, the scar), `herEye`, `herLid`, `hatEyes`, `hatLid`, and
`lod` on most big joints.

Markers (`HL.at(a, name)` gives the world point): **`eyeAt`, `eyeHRAt`, `eyeHLAt`** (her eyes: **a camera or a
look-at should treat these as her eyes, not her face**), `faceAt`, `mouthAt`, `socketAt`, `hatMouthAt`, `hatTopAt`,
`weakA` .. `weakE` (the creature's five eyes: the weak points), `brimTipR`, `brimTipL`, `feelerTip`, `palmR`,
`palmL`, `fingerTipR`, `fingerTipL`. The parts file's `look` block says the same in data; `hit` has a head box, a
hat box, the weak points, her eye pair and her hands.

## Clips

Authored in `hl_clips.py` as a few key poses each with an ease; `hatlord.js` plays them. She is **always** in one of
them (a spawned `hat_lord` with nothing playing is put into `hl_idle`), so a clip owns the whole of her: the cast's
joints are set outright, her own turn from their rest. On top of the keys:

- **Overlap**: the far end of anything arrives late (outer wings 0.10-0.13 s, feeler 0.16-0.24 s, growths, fingers).
- **The look**: the hat turns to put her eyes on whoever she looks at (`a.lookAt`, else the camera within 12 m, or
  `HL.look(a, point)`). Her eyes get there first, the hat follows, and the game's own head-turn is taken back out
  at the neck, so her face stays level. Each clip says how much (`x.look`).
- **The walk**: whenever her root moves, `hl_walk`'s legs are laid over whatever clip is playing, run by distance
  (1.45 m a loop), so her feet do not slide at any speed.
- One clip runs into the next (0.3 s from wherever the last had her). A clip that ends goes back to `hl_idle`.

| clip | length | what happens | marks (s) |
|---|---|---|---|
| `hl_idle` | loop 8.0 | she barely moves. the hat breathes, wing against wing; the growths pulse; the feeler twitches twice; her eyes blink together twice; the creature's five blink alone | |
| `hl_walk` | loop 2.0 | the stalk: knee first, like a wading bird. the hat sways against her hips, the wings trail | stepR 0, stepL 1.0 |
| `hl_duck` | 4.9 | under a doorway (1.25 x 2.3 m): the hat turns end on and folds its sides down, she goes under shoulder first | turn 0.4, folded 1.1, low 2.0, up 3.6, open 4.4 |
| `hl_talk` | loop 6.0 | the hat tips to hold her eyes on you; her right hand turns over twice | |
| `hl_offer` | held | one long hand out, palm up, at 1.5 m. the hat looks at the hand, then at you | lift 0.7, out 1.5, look 2.4 |
| `hl_bow` | 2.6 | a small bow, a hand on her chest. the hat's neck straightens as she goes down: it stays level, watching | low 1.1, rise 1.75 |
| `hl_lunge` | 4.8 | the hat goes for what is in front of her: wings up, out on its neck, the band open. one raised finger. it goes back | fix 0.2, aye 0.5, stop 0.72, finger 1.5, back 2.0, shut 3.6, home 4.2 |
| `hl_reveal` | held | the hat lifts; its fingers open off her face: no eyes | lift 0.8, unlace 1.2, shown 2.2, looks 3.4 |
| `hl_reveal_end` | 2.2 | the fingers lace back over, the hat comes down | laced 0.9, down 1.4 |
| `hl_attack_tell` | held | it rears up and round to her left, low wing high | aye 0.25, up 0.9 |
| `hl_strike` | 1.5 | the wing sweeps round in front of her and carries past | sweep 0.16, hit 0.3, past 0.5, recover 1.0 |
| `hl_stagger` | 1.4 | knocked back a step: every eye on the hat shuts, the wings fly up | hit 0.02, foot 0.6 |
| `hl_hat_off` | held | the hat tears free and beats above her; she kneels, eyeless. a stump of its neck stays in her | tear 0.6, free 1.4, knees 3.2, down 3.9 |

Loops are checked when the clips are written (`python3 tools/blender/cast/hl_clips.py`): no jump at the seam, and
no change of speed there sharper than the clip's own corners. Every wobble's frequency fits its loop a whole
number of times; `tests/story/hat_lord.test.mjs` checks that too. **Every key carries every channel its clip
touches** (0 where it rests): before, a channel at 0 in both keys of a stretch dropped out of the pose there and its
overlap snapped it home in one frame (the feeler in `hl_strike` at 1.0 s and `hl_stagger` at 0.6 s). Sampled at
60 fps the biggest one-frame steps left are meant: the lunge's bite (`hatNeck.x` at 0.52 s), the stagger's flinch
(every lid at 0.02 s) and the blinks.

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
- Sounds are not made here. The marks are where they go: `aye` (several voices at once), `stop`, `finger`, `tear`.

## Triangles and sizes

| | triangles | |
|---|---|---|
| the model | 25,032 | budget 18-25k. her own joints (the hat, its hands, the cape, her fingers) 19,162: the growth sacs 2,250, the cape 1,650 a half with its trim, the crown 1,116, the ribs 1,060, the hat's fingers over her face 770 |
| far LOD (past 34 m) | 1,854 | the cape, the brim, her chest and hair are built coarse; the rest is decimated |
| everything in the file | 26,886 | the game draws 27,560 near (the code mouth rig on top) |

`c_hat_lord.glb` 1,187 KB (under the 2 MB cap), parts file 16 KB, `hl_clipdata.js` 72 KB, `hatlord.js` 14 KB.
12 materials (`hl_suit`, `hl_satin`, `hl_lining`, `hl_skin`, `hl_brass`, `hl_flesh` (the crown and growths, wet),
`hl_hide` (the brim's top, drier, sharing the flesh texture), `hl_membrane`, `hl_bone`, `hl_eye`, `hl_mouth`, `hl_dark`)
and 9 small textures (the biggest 128 x 128; the flesh is veined, not speckled). Clear coats are 0.3 rough (0.12 on
the eyes and brass): wet, not mirrors. Colour is a vertex tint x baked AO in `COLOR_0`, as on Pallet Jack. About 130
draw calls up close: every joint is its own meshes.

## Rebuild

```sh
python3 tools/blender/cast/hl_clips.py                       # the clips -> public/js/story/hl_clipdata.js (prints the reach misses and the loop check)
blender52 -b --python tools/blender/cast/make_cast_hat_lord.py -- --stats --qa
#   builds her, bakes AO, makes the far LOD, runs the asset gate on the model and the far model, writes the glb and
#   the parts file, renders the silhouette / turnaround / close-up sheets (EEVEE: about 6 minutes on 4 cores)
#   --no-sheet  --sheet=sil,turn,close,poses,clips  --clip=hl_lunge  --quick (Workbench)  --no-ao  --no-export  --no-lod
# then, with the game served on a port (headless browsers through pwlock.cjs):
node tools/blender/cast/hlshots.cjs <port> docs/story/cast   # the actor-path check and the in-game sheets
node tools/blender/cast/hlgame.cjs <port> docs/story/cast    # story mode at Too HD and Potato
```

`hlgame.cjs` stands **her** where each shot wants her from you (it used to move you to her, and the server undoes
that teleport). In software GL the story map runs at about 14 s a frame at Too HD once its shaders are built (10
minutes in), so it waits for real frames before the first shot and gives each screenshot 10 minutes.

If her skeleton (`HATLORD` or `EXTRA` in `hatlook.js`) changes, run `node tools/blender/cast/hljoints.cjs <port>`
first. If a marker moves, copy the parts file's `markers` into `MK` in `hatlook.js` (the test fails until you do).

## Checks

- **Asset gate** (`blender-asset-qa`, profile `game`, z-fight eps 0.8 mm): PASS on the model and on the far model
  (contact tolerance 6 mm, and 4 cm for the far one). Look pass 2 (2026-11-11) found and fixed: the cape's pink
  facing lying flush on the hide and the lining (it now wraps the edge 3 mm proud of both, on the hide's own columns,
  so the two are chords of the same folds), the lashes lying in the lid's edge (lifted onto the lid), the brow scar
  floating off the rim (laid on the rim's crest), and a removed far piece left selected, which broke the export.
  Accepted warnings: UV overlap (box-projected tiling textures, on purpose), 36 duplicate verts where each eye's skin
  meets the hat's rim (a material seam), a few hidden back-to-back faces where pieces meet. Found on the way and fixed in the geometry: shin and thigh
  sleeves the same size where they overlap (the shin now tucks inside); eyelids that folded over their own pole
  (rebuilt hinged on the eye's corners); neighbouring fingers sharing a knuckle face (thinner, each a hair off the
  next one's plane); the socket's hole hidden behind the chest (a dark plate proud of it); brim pieces overlapping
  at their seams (they now meet edge to edge with a hair between); brows floating off the eye mask; and in the far
  model, thin shells that a decimate folded onto themselves (built coarse instead).
- **In the game** (`hlshots.cjs check`: `HL_CHECK ok`): `buildLook('hat_lord')` dresses the glb on the skeleton with
  every part, marker and joint of the parts file present; markers land within 0.1 mm of the file; each of the 13
  clips is stepped through its own code: joints move, nothing goes NaN, all 40 marks fire; the far LOD swaps in
  (27,560 triangles drawn near, 1,854 far) and back; the code puppet (80 simple meshes, no glb) stands and takes a
  clip.
- **Tests**: `node --test tests/story/*.test.mjs tests/browsable.test.mjs`: 46 pass. `hat_lord.test.mjs` checks
  that every part and marker the parts file names is a node of the glb on the joint it says, and that `MK` in
  `hatlook.js` matches the file.
- **Looked at**: every sheet above, from both renderers; look pass 2 went round four times on the model (Blender
  close-ups and turnaround each time) and once more on the clips (a pose a clip, the silhouette beside the sketch,
  a 60 fps pop check).

## Look pass 2 (2026-11-11): the lead's six notes

1. **Her eyes read cute** (a big pale lilac plate, two big round cartoon eyes, arched brows). Now life size and a
   little over (1.35x, radius 16.5 mm), each in its own socket sunk into the crown (the crown is pushed in behind
   it): an almond of her grey skin from under the lids, a crease over the lid, a shadow under it, raw where it was
   grafted in, then the hat's own flesh swollen round it, heaviest over the top. Heavy upper lids, a wet lower rim,
   fine lashes, no brows (a faint scar on the rim over her right eye), her left eye 4 mm lower and more shut, a darker
   iris with a small pupil, a bloodshot white. Lid joints, the look and the blink are unchanged.
2. **The growths read as fruit.** Round lumps with a hole (polyps) are gone. Sacs on stalks, wrinkled, leaning,
   bending, a puckered lip and a throat, from 12 mm to 70 mm; three fists, three ears, a nose, three sets of back
   teeth in gum, two small hands; liver, bruise, grey dead skin and sallow, dark at the root and in every crease,
   raw toward the lip; the hat's flesh texture is veins, not speckle.
3. **The hat reads as a parasol.** Every rib is a row of finger or arm bones of its own thickness, knuckled and
   bowed, wandering sideways (the skin follows); rib tips ride high or sag (the edge rises and falls); each gap hangs
   back by its own amount; three torn gaps (ragged), three grown-back scars; fleshy roots where the big ribs leave the
   crown; branching veins; the long wing droops over its last half metre. The outer wings stop where the skin does
   (no fin along the fold). The brim's top is drier hide so it no longer throws the lights back as a white sheet.
4. **The cape is a coffin slab.** Round shoulders, then long straight lines to 0.41 m at the floor (closer to the
   sketch's two taper lines) and a small flare at the hem; folds that deepen toward the hem; its back is two domed
   wing cases with a spine of knuckled hide down the seam, gills, growth lines, veins; the front edges turn back pink
   and stay a sliver apart so her dark shins show; the walk swings the halves open (`capeR.y` / `capeL.y`, already
   in every clip).
5. **The arms get lost inside the cape.** Her stance (`REST` in `hl_clips.py`, `STANCE` in the build: the same
   numbers) holds the arms out along the bar and drops the forearms to hands just outside the cape's widest point,
   long fingers (a joint too many) pointing down. The face under the brim is as it was.
6. **The socket reads as a brooch.** Now a deep dark hole (6.6 cm across, 8.5 cm deep, ridged wall, red going to
   black, cut vessels at the bottom) with a thin brass lip set into bruised, swollen skin.

## Weak spots (honest list)

- **She is rigid pieces on joints**, like the rest of the cast: nothing bends. The cape is two shells hinged on her
  spine, so a deep bow or the kneel swings its hem out behind her, and a raised arm can pass through its edge. The
  brim folds on six hinges; it does not ripple. Between the wings and the front and back pieces a gap opens when a
  wing flaps hard; the long wing shows a step at its fold, seen front on.
- **Her eyes are small on purpose.** At 7 m they are a few pixels; they read as eyes from about 3 m in, and as hers
  (lids, lashes, the sunk skin) from 2 m. The white below the iris catches dark reflections, which reads wet up
  close and grey from further away. Their sockets' skin is lit like her chest: pale under a strong light, grey under
  the brim.
- **The growths are still lumps at 30 m**, as anything that size would be. The fists, ears and nose read from about
  4 m; the sacs' wrinkles from 2 m. Their colours are vertex tint over one veined texture, so up close the veins on a
  small sac are coarse.
- **The cape's folds are geometry on a 13 x 16 grid**: they read as stiff pleats, not cloth, and they do not move.
- **The mouth is the game's code mouth** (two rows of lip segments). The Blender sheets show a stand-in for it.
- **No ankles and no foot planting beyond the walk's own maths**: her shoes are rigid on the shin, so in the stalk
  a toe tips into the floor at the end of a stride, and in the crouch (`hl_duck`) and the kneel the feet are
  approximate.
- **The lunge reaches about 1.3 m in front of her at 2 m off the floor.** To get the teeth "a hand from your chest"
  the scene has to stand you close, or stage it with the camera. Its neck is two short tubes: any further and they
  come apart. Its start is a deliberate snap (full speed from a standstill).
- **`hl_hat_off`**: the hat is still a child of her head. It is slid up 1.75 m to stay in the air while she
  kneels; the scene should swap in a free copy at the `free` mark if it needs to fly anywhere.
- **`hl_duck` clears a 1.25 x 2.3 m opening**, not a house door. She is 2.96 m with a 1.46 m bar.
- **The look is approximate**: it is worked out from her yaw and height, not her posed bones, so in a deep bow or
  the duck the hat's aim is a few degrees off. It is turned down or off in those clips.
- **Timing was judged from contact sheets and a 60 fps step check**, not watched at speed with sound.
- **The reveal shows smooth skin with shallow hollows, not sockets**, and the fingers swing open as two rigid hands.
- **Her hair from behind** is a glossy black helmet with a knot; it was not part of this pass.
- **Draw calls**: about 130 up close (52 joints, 12 materials). One of her is fine.
- **Blender clip strips are Workbench** (flat light, no vertex colour): EEVEE here is 20 s a frame.
- Not done: sound, any damage states, cloth, a free-flying hat, lip-sync beyond the jaw flap, her in a mission.
