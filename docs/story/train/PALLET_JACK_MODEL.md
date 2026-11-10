# Pallet Jack: model, clips and how to drive him

Jack Marsh, 41, the Bottom's delivery man (`pallet_jack`, [TRAIN.md](../TRAIN.md) §2 and §5). A wide, unhurried man
with an Overdrive Rig put *into* him, one part a year, paid for in soup. He dies at the end of Act I. This page is the
presentation half: how he looks, how he moves, and what the scene and fight code call. **He is not placed in any
mission and nothing here does damage.**

Sheets (all looked at while building; the list of what is still weak is at the bottom):

| what | in the game's renderer | from Blender |
|---|---|---|
| turnaround, next to Lumps and the mannequin | `docs/story/train/pj_game_turn.jpg` | `tools/blender/sheets/c_pallet_jack.jpg`, `c_pallet_jack_scale.jpg` |
| the face at talk distance, and the faces his clips use | `pj_game_face.jpg` | `c_pallet_jack_face.jpg` |
| the three damage states, the far LOD | `pj_game_damage.jpg` | `c_pallet_jack_damage.jpg` |
| the rig parts close up, at rest and with the rig up | `pj_game_parts.jpg` | `c_pallet_jack_parts.jpg` |
| one key pose a clip | `pj_game_poses.jpg` | `c_pallet_jack_poses.jpg` |
| a contact sheet per clip (12 frames, marks called out) | `pj_clip_<name>.jpg` | `tools/blender/sheets/c_pallet_jack_clip_<name>.jpg` (8 frames) |
| the hand truck | in the turnaround and `pj_clip_idle.jpg` | `tools/blender/sheets/s_handtruck.jpg` |

## Files

| file | what |
|---|---|
| `public/models/cast/c_pallet_jack.glb` | the model: `part_<joint>[__<tag>]` meshes at the rest pose, like every cast model |
| `public/models/cast/c_pallet_jack.parts.json` | every named part (joint, box), the moving pieces (pivot, axis), markers, states, clip marks and samples, prop spots |
| `public/models/story/s_handtruck.glb` | his hand truck (a story prop, in `story/index.json`): nodes `frame`, `wheelL`, `wheelR` |
| `public/js/story/jacklook.js` | his skeleton, the code puppet (the fallback), the markers, his faces (`jack`, `jack_hurt`, `jack_gone`) |
| `public/js/story/palletjack.js` | `PJ`: clips, marks, damage states, the machine, vest, LOD, steam |
| `public/js/story/pj_clipdata.js` | the clips as key poses. **Generated** by `tools/blender/cast/pj_clips.py` |
| `tools/blender/cast/make_cast_pallet_jack.py` | the build. `jackkit.py` (kit), `jackbody.py` (the man), `jackrig.py` (the machine), `jackdmg.py` (damage), `jacktruck.py`, `jackposes.py` (pose sheets) |
| `tools/blender/cast/pjshots.cjs`, `pjparts.cjs` | the in-game sheets; the game half of the parts file |

Touched in shared files: **two lines in `looks.js`** (an import and `pallet_jack: () => palletJackLook({...})` in
`LOOKS`), one entry in `public/models/story/index.json` (`s_handtruck`), and his entry in
`tools/blender/cast/joints.json` (written by `joints.cjs`). Nothing in `actors.js`, `boot.js`, the content files or
the server.

## Who you are looking at

- **Built like the thing he's named after.** About as tall as the player (2.14 m at the root's x1.24), nearly twice as
  wide, short thick legs, big flat boots. Off-Spec like Lumps, but all width and density where Lumps is forearms; the
  line-up sheet puts the three side by side.
- **A specific man at talk distance.** A broad face that stays wide down to the jaw, a heavy brow, tired eyes that sit
  back under it (bags under them), a nose broken once and set by nobody (it jogs to his left; a pale line across the
  bridge), a second old scar through his right brow, stubble up to the sideburns, big ears (the left one thickened),
  short hair going back at the temples with grey coming in. Eyes, lids, brows and mouth are the game's code face
  (`face.js`), as on every cast model; his resting face is `jack` (lids a little down, the inner brows up, the corners
  of the mouth up).
- **The rig is in him, not on him.** Where the Overdrive Rig (`x_rig.glb`) has armour plates he has scar tissue grown
  over plate: both shoulder caps, the breastbone, both shoulder blades, the top of the right forearm, each with
  rivets pushing through and one bare corner the skin never took to. Hydraulic lines run under the skin as raised
  ridges: off the collarbone to the armpits, down both arms, up the neck, up the back from the boiler, down the calves.
- **Clothes.** A ribbed singlet with soup down it, cut away round the boiler. Navy work trousers turned up under the
  knee, clear of the pistons, a cargo pocket, knee patches. A brown lifting belt, tall at the back. Tan steel-toe
  boots worn through to the cap, a steel guard over the laces. Keys on a carabiner. A red-check tea towel with soup on
  it in the back right pocket. `THIS WAY UP` tattooed on the left forearm, rubber bands round that wrist.
- **The vest** is its own piece: hi-vis yellow (it gives a little light back, so it reads in the Bottom's dusk),
  silver bands, an arch cut out of the back for the boiler, a docket book and a pen in the pockets, and across the
  shoulders in marker: `MARSH` and under it `DELIVERIES`, which runs out of room.

## Parts

Every piece below is a tagged group on its joint (`part_<joint>__<tag>` in the glb, `L.parts[tag]` after `buildLook`),
so the game can hide it, move it, light it or break it. Boxes, pivots and axes are in the parts file.

| tag | joint | what | moves |
|---|---|---|---|
| `boiler` | spine | a beer keg sunk in his lower back (`RETURN EMPTY`, Bev's plate `BEV 15`), fire door, level glass, relief valve | |
| `fire` | spine | what glows: the fire door's slots (`pj_glow`), the level in the glass (`pj_marrow`) | emissive, by `PJ` |
| `gauge`, `needle` | spine | the pressure gauge on his left of the keg (`pj_dial`), its needle | the needle turns about its axis |
| `valveBody`, `valve` | spine | the bleed valve on his right of it, its red wheel | the wheel turns about +y |
| `stackBase` | spine | the copper manifold, the stacks' wrapped sleeves, the bar across | |
| `stackL`, `stackR` | spine | the thruster stacks (chrome going blue then black, an ember in the throat) | slide 0.07 up their own axis |
| `flapL`, `flapR` | spine | their rain caps | hinge open, about 1.2 rad |
| `collar` | spine | the welded steel collarbone; the weld is to his right of centre | |
| `shinL`, `shinR` | kneeL / kneeR | the shin pistons: red sleeve, chrome rod, down the front of the leg onto the boot's guard | |
| `lockL`, `lockR` | kneeL / kneeR | the shin locks: toggle levers, modelled open | turn `shut` rad about z and they slap up flat |
| `cock` | foreR | the cocking collar on the rocket forearm (red, a hazard band) | slides 0.04 up the arm |
| `ram` | handR | the chrome ram and wrist cuff, hidden up the forearm | move `handR` 0.24 down its -y and the fist rides out on it |
| `fist` | handR | his knuckles: bare steel, the skin worn off them | |
| `plates` | spine, arms, foreR | scar tissue over plate (`pj_scar`), rivets, bare corners | |
| `lines` | spine, neck, arms, forearms | the hydraulic lines under the skin (`pj_lines`) | the game can pulse the material |
| `vest` | spine | the hi-vis vest | hide it; `dmgVestFar` is its far LOD |
| `towel` | body | the tea towel | |
| `lod` | every joint | the far LOD (shown past 28 m) | |

Markers (in `L.parts`, groups with nothing in them; `PJ.at(a, name)` gives the world point):
`chest` (where your hand goes: his left of the weld), `weldAt`, `palmL` (his open hand), `gripR` (what his fist
holds), `fistAt` (the knuckles), `elbowAt` (the rocket's exhaust), `boilerAt`, `fireAt`, `gaugeAt`, `bleedAt`,
`stackTipL` / `R` (+ `stackTipBentL` / `R`), `woundAt` and `ventAt` (the hole, front and back), `armFrontEnd`,
`armBackEnd`, `marrowAt`, `seatAt`, `eyeAt`.

His right hand stays a fist (it is the rocket's); his left is open. Anything he holds is held in the left, and it is
the left that takes your hand.

## Damage states

Hidden pieces (named `dmg*`, because that is what `looks.js` starts hidden), swapped in by `PJ.dmg(a, state)`. They
add up in story order.

| state | shows | hides |
|---|---|---|
| `fresh` | | |
| `run_through` | `dmgWound` (the hole under his ribs: a wet lip, the singlet torn out round it and soaked to the belt), `dmgArm` (the length of arm still through him: snapped off in front with a lanyard and its card still on it, its hand out of his back), `dmgBoilerSplit` (the keg peeled back in petals where it came out, split chime to chime, lit from inside) | |
| `armour_broken` | + `dmgCollar` (the weld sprung: his right half of the bar stands out of his chest), `dmgLockL` / `R` (the shin locks blown, the glands weeping), `dmgStackL` / `R` (bent over) | `collar`, `lockL/R`, `stackL/R`, `flapL/R` |
| `marrow_taken` | `dmgWound`, `dmgMarrow` (the keg opened from behind like a cupboard, his lower spine inside it, a gap the length of a hand, the ends of the gap still lit) and the armour pieces | `boiler`, `fire`, and by default the arm (`PJ.arm(a, true)` keeps it) |

Stylised on purpose: flat dark holes, low-poly limbs, no texture gore. `pj_core` (the split) and `pj_marrow` are the
only emissive materials in the damage set; `PJ` flickers them and puts the fire out in `marrow_taken`.

## Clips

The cast is animated in code (joints of the code skeleton, `actors.js` `CLIPS`), like Mr. Overtime; so are his.
`pj_clips.py` holds each clip as a few key poses with an ease each; it writes `pj_clipdata.js`, which `palletjack.js`
turns into `CLIPS.pj_*` entries. The Blender pose and contact sheets pose the model from the same numbers.

What the clip player adds to plain keys:
- **Arms, forearms, hands and neck are absolute**: a hand that has to be on the truck, on the arm through him or on
  his chest stays there whatever the walk and the talking are doing underneath. Body, legs, spine and head add to the
  walk pose (so breathing, looking at you and walking still happen).
- **Overlap**: the far end of a limb gets there late (forearm 0.06 s, hand 0.09 s, head 0.07 s), so nothing arrives
  all at once; `back` eases overshoot and settle where something heavy lands or locks.
- **One clip runs into the next** without dropping to a stand first (0.22 s from wherever the last one had him).
  A clip that ends on its own (`pj_rocket_punch`, `pj_stagger`) hands over to the stance, the hurt one if he is hurt.
- The machine follows the clip: `x.rig` (shin locks left then right, then the stacks rise), `x.flap`, `x.cock`,
  `x.vent`.

| clip | length | what happens | marks (s) |
|---|---|---|---|
| `pj_idle` | loop 9.0 | weight on his left leg, his left hand on the truck's grip, looks about | |
| `pj_idle_eating` | loop 4.8 | sat on the wagon's back rail, legs hanging, eating out of a pan | scoop 0.6, eat 1.85 |
| `pj_walk_load` | held | a load on his forearms, leaning back off it; on top of the walk | |
| `pj_kneel_vest` | 6.0, held | down on a knee to the child, the vest off and onto them, a hand on their head | knee 0.95, vestOff 1.75, vestOn 3.7, pat 5.2 |
| `pj_rig_up` | 2.8, held | braces; shins lock; stacks come up and open; he racks the forearm | lockL 0.4, lockR 0.7, stacks 1.05, cock 2.1, ready 2.75 |
| `pj_fight_idle` | loop 2.4 | the stance, rig up | |
| `pj_rocket_punch` | 1.7 | winds back, fires, the fist rides out on the ram, recoil, racks it again | wind 0.3, fire 0.46, hit 0.56, home 1.0, cock 1.34 |
| `pj_block` | held | the forearm across, braced | up 0.14 |
| `pj_stagger` | 1.3 | knocked back a step and a half, finds his feet | hit 0.02, foot 0.7 |
| `pj_impaled` | 3.6, held | run through, lifted a metre, looks down at it, gets both hands on it | in 0.05, lift 0.22, looks 2.0, grip 3.5 |
| `pj_break_it` | 3.2, held | breaks it: the first try only hurts, the second goes | try1 0.58, snap 2.88 |
| `pj_land_kneel` | 1.5, held | drops, lands on his knees, a fist on the deck | land 0.4 |
| `pj_stand_anyway` | 3.3, held | a foot under him, up, a hand over the hole | foot 0.85, up 2.2 |
| `pj_fight_idle_hurt` | loop 3.2 | lower, slower, venting | vent 0, 1.6 |
| `pj_armour_break_fall` | 2.2, held | the armour goes, two steps back, down against the fridge | hit 0.04, armour 0.06, foot 0.7, down 1.04, fridge 1.05 |
| `pj_dying_talk` | 5.0, held | sat against it: takes your hand, puts it on his chest, holds it | take 2.45, place 4.1 |
| `pj_last_breath` | 3.6, held | the breath out; his hand comes off yours and stays open on the deck | breath 0.2, lets_go 2.3, hand_down 3.1 |
| `pj_carried` | a pose | limp across someone's arms | |

Marks that change him by themselves: `in` shows `run_through`, `armour` shows `armour_broken`, `vestOff` hides his
vest (between `vestOff` and `vestOn` a bundle of it is in his hands; on `vestOn` it is the child's: the scene shows it
on them). Everything else is a sound, a puff and an event for the scene.

## Driving him

```js
import { PJ } from './palletjack.js';        // also window.JF_PJ
const a = spawnActor('pallet_jack', { look: 'pallet_jack', voice: {...} }, [x, y, z], yaw);
PJ.play(a, 'pj_idle');                        // any pj_* clip; { hold: true } as with actors.play
PJ.vest(a, false);                            // he gave it away
PJ.dmg(a, 'run_through');                     // 'fresh' | 'run_through' | 'armour_broken' | 'marrow_taken'
PJ.arm(a, false);                             // the length of arm through him off (the scene has its own); null = his state decides
PJ.set(a, { rig: 1, flap: 1, cock: 1 });      // the machine by hand (0..1), when no clip is driving it
PJ.at(a, 'chest');                            // a marker's world position (THREE.Vector3)
PJ.on((ev) => { /* { type: 'pj', mark, id, clip, at } */ });
PJ.fx = false;                                // no steam, sparks or props from here (the scene draws its own)
```

- `palletjack.js` registers the clips the first time his look is built, so nothing needs importing for `play(a,
  'pj_idle')` from `actors.js` to work.
- The host can call `pjFrame(dt, cam)` every frame next to `otFrame` (one import and one line in `boot.js`: slow
  motion then reaches his marks and steam). Until it does, the file ticks itself with `requestAnimationFrame`.
- Always on: a wisp off each stack and a cap that lifts with it; more with the rig up; red and faster when he is run
  through; nothing once the marrow is taken. The fire door breathes, flickers when he is hurt, goes out at the end.
- Where the things he touches go is in the parts file under `props`, measured from the poses: `handtruck` (where
  `s_handtruck.glb` stands for `pj_idle`), `seat` (how far under the rail his root goes for `pj_idle_eating`), `load`,
  `fridge` (the door's z behind where he stood), `carry` (where the carrier's arms go), `hand` (where he takes your
  hand and where he holds it).
