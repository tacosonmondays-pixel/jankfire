# REVENUE PROTECTION: the fight (first playable)

The boss of `m06_tickets_please`. The design is [TRAIN.md](../TRAIN.md) §4, the model is
[REVENUE_PROTECTION_MODEL.md](REVENUE_PROTECTION_MODEL.md). This page is what is built, the numbers, and what is not.

Try it: `?story=1&storytest=1&train=1`, STORY, NEW GAME. You start on the wagon with the Blood Drive and the fight
starts by itself. Add `&storydev=1` to stage it by hand (`G.story.send('bossdev', { ... })`, below).

## What is built
- **The arena** (`shared/story/train.js`, map `story_train`): three cars you fight on and the loco, standing still in
  a 9.2 m bore. Everything about its size is one table (`HW`, `CARS`, `COVER`, `CREW`) that the room's collision boxes,
  the grips, the sweeps, the fall-off, the client's stand-in train and the tests all read: a Blender train can be built
  to it and replace the stand-in (the train's boxes carry `pv: 'rp_train'`; the client registers a prop of that name
  and draws the boxes itself, one group a car).

  | car | z (m, from the back) | deck | what |
  |---|---|---|---|
  | `wagon` | 0.2 – 9.2 (9 m) | 1.0 | low and open, a 0.75 m rail round three sides, two crates |
  | `flat` | 9.8 – 19.8 (10 m) | 1.3 | the flatbed: three crates (one tall), the chained-down fridge |
  | `van` | 20.4 – 27.4 (7 m) | 1.3 | the tool van: four steps up its left side to a flat roof at 3.45 on posts (2 m of headroom under it, open sides), two tool lockers |
  | `loco` | 28.0 – 33.0 | | the front wall |

  The deck is 4.2 m wide (`HW` 2.1), which leaves about 2 m of wall each side for the arms. Cover is never more than
  about 4 m away and the middle lane is clear. The crew's three spots (Jack at the back rail, Lumps on the flatbed,
  Gordo by the van's stairs) have static stand-ins: no AI. The client scrolls ribs, sleepers and a string of weak
  bulbs past the train; the bulbs go out where the mask has been.
- **THE GAP**: the room owns it. It starts at 22 m (TRAIN.md says 30: from the wagon the mask read small at that
  distance, so the whole band is closer), every arm that has the rail closes it 1 m/s, a severed arm opens it 2 m, a
  flinch 5 m. At 0 m it has you. It is measured from the back of the train, and is the big number on the HUD.
- **Arms**, owned by the room, each with a wrist knot (the weak point: the content's x2) and one HP pool:
  - **Grabber**: walks along the wall from a rim socket to one of eight spots on the rear car (three a side and two
    on the back: the wagon's rail, or the flatbed's edge once the wagon is gone), 3.5 s: the tell. Then it grips.
  - **Sweeper**: lies across behind the train at knee or head height for 1.4 s, then runs every deck to the front of
    the van at 12 m/s, keeping its height over the deck under it. Knee height: be 0.55 m off the deck as it passes.
    Head height: slide or crouch. On the van's roof both pass under you. Hit: 22, and thrown sideways.
  - **Snatcher** (v1: it goes for you): 2.2 s to reach, then 6 s over your head. Shoot the wrist, or 40 damage and 5 m
    of THE GAP. From phase 2 they come in pairs. While you are up on the van's roof the next arm is a Snatcher 6
    times in 10.
- **Phase 1, TICKETS, PLEASE**: the mask shrugs bolts off. Sever four arms inside ten seconds and it flinches: both
  eye housings swing open for 5 s and bolts put into them count (x2). The phase ends at 60%, or when Jack's bar (90 s)
  runs out; either way the room clears the arms, sets THE GAP to 6 m, emits `phase` (PENALTY FARE, `invuln: true`)
  and waits. The client plays `mo_carry_the_bit_that_works`; the room holds until the scene lets go, plus a second.
- **Phase 2, PENALTY FARE**: you have the marrow (the Blood Drive is free). Each of the twelve plates has 240 HP: it
  crazes at half and falls at 0, and the hole stays. The break stages come at HP lines, in order: `hairline` (60%),
  `left_eye` (45%: the left housing blows and stays a way in), `smile` (30%: the lower third drops, arms start coming
  out of the mouth).
- **Phase 3, END OF THE LINE** (25%, the health layer): the Inspector's chest is the crit spot (x2.5), his body
  counts in full, everything else at a quarter. It lunges: it rears for 1.5 s, then takes 4 m. The first lunge bites
  the rear wagon off: its boxes leave the room, whoever was on it loses 35 and is thrown onto the flatbed, and THE GAP
  is measured from the flatbed's back from then on (the mask is that much nearer). Later lunges bite the back 3.5 m of
  the train when THE GAP is inside 6 m.
- **The finish**: at 0 the room emits one `kill` with `boss: 'revenue_protection_1', defeat: true` and the boss leaves
  the room. The client plays BLOOD CROSSED: a cross grows out of the middle until it touches the tunnel on four sides,
  the face falls forward flat, the plug comes apart into its four wedges, and the train leaves it behind.
- **The fail**: THE GAP at 0 m (or dying any other way). Black hands close over the screen one at a time, "fare
  evaded. briefly.", and the fight starts again from the beginning of the phase you were in.
- **Falling off the train**: the track takes 25 HP and you are put back on the wagon (fairer than a death: a sweeper
  that knocks you over the side would otherwise be a one-hit kill).
- **The Blood Drive** (`WEAPONS.blooddrive`, `public/js/story/blooddrive.js`): spin-up 0.8 s, 14 bolts a second, 18
  damage, 2 HP a bolt, every sixth bolt in the same target blooms a cross. Judged by the room in story rooms only
  (spin-up, rate, range, cost, what the ray hit). `slot: null`: it is not in any loadout, ladder, crate or bot.
  It is in your hands whenever you are on the train. Code-built view model: six barrels that show your HP.
- **The quest**: on `m06`'s `hold` and `break` steps the client goes to the train (`G.story.travel`) and asks the
  referee for the boss. Phase 1's end sets `rp_phase1_done`; the defeat is the step's `killBoss`. After the mission it
  goes back to where you were.

## The numbers
From the content (`content/bosses.js`, `boss_fights.js`): HP 5000, the armour layer 3750 on top of the Inspector's
1250, phases at 60% and 25%, crits (wrists x2, eye housings x2, the Inspector x2.5).

`RP` in `shared/story/train.js` (D = TRAIN.md gives it, C = chosen for this build):

| what | number | |
|---|---|---|
| THE GAP: start, max | 22 m | C (D says 30) |
| a gripping Grabber closes it | 1 m/s each | D |
| it holds for the middle scene at | 6 m | D |
| a severed arm opens it / a flinch opens it | 2 m / 5 m | C |
| a retry (phase 2 or 3) starts at | 16 m | C |
| an arm's HP (knot x2, so 9 bolts) | 320 | C |
| a hit on the rope or the hand counts | x0.15 | C |
| arms at once, phase 1 / 2 / 3 | 4 / 4 / 5 | D (4), C |
| seconds between arms, phase 1 / 2 / 3 | 3–4.5 / 2.6–3.8 / 1.9–2.8 | C |
| mix grab : sweep : snatch, phase 1 / 2 / 3 | 5:3:2 / 5:3:3 / 6:3:2 | C |
| blood back for a sever | 20 HP | C |
| Grabber: reach | 3.5 s | C |
| Sweeper: tell, speed, damage | 1.4 s, 12 m/s, 22 | C |
| Sweeper: the bar over the deck (knee / head), clear a knee-high one by, both pass under you from | 0.45 / 1.65 m, 0.55 m, 1.75 m up | C |
| Snatcher: reach, hold, damage, gap lost, favours the roof | 2.2 s, 6 s, 40, 5 m, 0.6 | D (6 s), C |
| flinch: severs, inside, eyes open for | 4, 10 s, 5 s | D, D, C |
| a plate's HP, crazed at | 240, half | C |
| holes, lamps, blasts (phase 2) | x0.5 | C |
| anything but the Inspector (phase 3) | x0.25 | C |
| stages: hairline / left eye / smile | 60% / 45% / 30% | C |
| Jack's bar | 90 s | C |
| lunge: every, tell, takes, bites inside, reach, damage | 8–11 s, 1.5 s, 4 m, 6 m, 3.5 m, 35 | C |
| the first lunge takes the rear wagon | always | D |
| deck width, wagon / flatbed / van length | 4.2 m, 9 / 10 / 7 m | owner (2026-11-10) |
| Gordo's blood bag | 20 HP every 10 s | C |
| off the train | 25 HP, put back | C |
| Blood Drive: spin-up, rate, damage, cost | 0.8 s, 14/s, 18, 2 HP | D |
| Blood Drive: bloom every, bloom damage on the boss, blood back for a kill | 6th bolt, 60, 10 HP | D, C, C |

Damage the fight does to you is what lands: the room softens every bot's hit to 0.6, so the fight asks for more.

## Screenshots
Headless, Too HD, staged with the dev messages below (a headless frame takes seconds, so nothing here is timing).

| file | what |
|---|---|
| `fight_01_mask_arms.jpg` | the mask behind the wagon at 17 m, arms along both walls, a blue knot at each wrist |
| `fight_02_grabber_rail.jpg` | a Grabber's hand closed over the wagon's rail, its knot above it |
| `fight_03_severed_flinch.jpg` | four hands dropping onto the track, the eye housings open (this one is from before THE GAP panel moved to the left edge) |
| `fight_04_plates_left_eye.jpg` | phase 2: plates gone, the left eye blown |
| `fight_05_smile.jpg` | the lower third off: the mouth |
| `fight_06_end_of_the_line.jpg` | phase 3: half a face, hanging |
| `fight_07_inspector.jpg` | the Inspector in the mouth, his chest marked, from the back of the wagon at 7 m |
| `fight_08_blood_crossed.jpg` | the finish: the cross out to the rim |
| `fight_09_comes_apart.jpg` | the face flat on the track, the plug splitting along the cross |

## Dev messages (`?storydev=1`)
`G.story.send('bossdev', o)`: `calm` (no arms, lunges or Jack's clock by themselves), `want: 'grab' | 'sweep' | 'snatch'
| 'lunge'` (+ `hi`, `side`), `grip: true` (skip the tells), `sever: true` (every arm), `gap: n`, `pin` (THE GAP holds still), `dmg: n` (+ `part`,
`i`: where it lands; by default the part that counts in this phase). `window.JF_TRAIN` is the client's state.

## Not built
- The Brakeman.
- The crew: Jack at the rail (his bar is a 90 s clock), Lumps, Gordo (his blood bags arrive by themselves), Dale's
  shouts. Snatchers go for you, not for a crewmate, and nobody blocks a sweeper for you.
- The middle scene's [FIRE] and [TAKE] buttons. The scene engine cuts a "moment" scene at 3 s, so the scene plays its
  first three seconds and the step's flags are then set by the fight's glue (`trainfight.js`, marked).
- Lost property thrown out of the left eye, crosses chaining within 3 m, HP past full after the marrow, the tunnel
  lit red from inside on a cross, daylight ahead, the 90 s countdown.
- The Blood Drive as an item in the Tote Bag (`give:blood_drive` still gives the loot table's legendary on the Blood
  Cross base), its Blender model, the marrow's other perks.
- Cover is only somewhere to stand behind: sweepers do not clear crates, crates do not block a sweeper, and nothing
  in this fight shoots. The crew stand-ins do nothing and can't be hurt or snatched.
- The train is a stand-in made of the table's boxes: the Blender train comes later, built to the same table.
- Co-op: the arena is sized for four players and the room's rules loop over every human, but only solo has been run.
- Shots are checked against the mask as it hangs straight: its phase 3 swing (a few degrees) is only drawn.
- The slice city has no referee yet, so the trip to the train is the only way the mission's fight can run there.
