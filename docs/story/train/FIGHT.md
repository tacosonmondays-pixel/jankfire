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
  Gordo by the van's stairs) have static stand-ins: no AI. The client scrolls the tunnel (the kit in
  [TRAIN_MODEL.md](TRAIN_MODEL.md): lining, track, cables, a string of weak bulbs) past the train; the bulbs go out
  where the mask has been.
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
  referee for the boss. Where you left from is kept in the save (`data.travelFrom`), so a Continue on the train still
  has its way back; with nothing to go back to, the way back is the default world's spawn. Phase 1's end sets `rp_phase1_done`; the defeat is the step's `killBoss`. After the mission it
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
Headless, Too HD, FOV 80, staged with the dev messages below (a headless frame takes seconds, so nothing here is
timing). The quest tracker in them shows mission 1 because the `&train=1` test route starts a fresh save; in the
mission it tracks m06.

| file | what |
|---|---|
| `fight_00_start.jpg` | the start: the wider wagon, a crate, Jack's stand-in at the back rail, the mask at 22 m |
| `fight_00b_from_the_roof.jpg` | from the tool van's roof: the flatbed (crates, the fridge, Lumps' stand-in), the wagon, the mask |
| `fight_01_mask_arms.jpg` | the mask at 17 m, arms along the wall (charred, matt), a Grabber on the back rail |
| `fight_02_grabber_rail.jpg` | the same Grabber: its hand over the rail, the blue knot above it |
| `fight_03_severed_flinch.jpg` | a flinch: a hand dropping, the eye housings open and red |
| `fight_04_plates_left_eye.jpg` | phase 2: plates gone, the left eye blown |
| `fight_05_inspector.jpg` | phase 3 from the back of the wagon at 7 m: the lower third gone, the Inspector's chest marked |
| `fight_06_before_the_bite.jpg` | phase 3 from the flatbed, the wagon still on: THE GAP 12 m |
| `fight_07_wagon_gone.jpg` | the same view after the first lunge: the wagon is gone, the mask is at the flatbed's back, 8.3 m |
| `fight_07b_sweeper.jpg` | a knee-high Sweeper's bar across the wagon, wall to wall (held still for the picture) |
| `fight_07c_blooddrive.jpg` | the Blood Drive firing at the mask: tracers kept on screen for the picture, the HP cost on the HUD |
| `fight_07d_fail.jpg` | the fail: the hands have closed, "fare evaded. briefly." |
| `fight_08_blood_crossed.jpg` | the finish: the cross out to the rim (taken on the earlier, narrower wagon) |
| `fight_09_comes_apart.jpg` | the face flat on the track, the plug splitting along the cross (the earlier wagon too) |

How big the mask reads (it fills the bore at its own depth, so this is only distance): from the middle of the wagon it
is about 19 degrees across at THE GAP 22 m, 26 at 15 m, 42 at 7 m, out of a view about 112 wide at FOV 80.

## Wiring Pallet Jack in (next: his model and clips are on `claude/overdue-jack`, not merged here)
His stand-in is spawned as `rp_pallet_jack` at `CREW[0]` (the wagon's back rail) and hides after phase 1. From
`PALLET_JACK_MODEL.md` on that branch, the clips and marks this fight will use:

| when (this fight's event) | clip | marks to hang things on |
|---|---|---|
| the fight starts (`state`, phase 0) | `pj_rig_up`, then `pj_fight_idle_hurt` (he arrives run through: `PJ.dmg(a, 'run_through')`) | `ready` 2.75: he can act |
| a Grabber grips near him (`arm`, `st: 'grip'`) | `pj_rocket_punch` | `fire` 0.46, `hit` 0.56: when the room should sever that arm (a new rule: his punches) |
| a Sweeper's tell (`arm`, `k: 'sweep'`, `st: 'tell'`), once in phase 1 | `pj_block` | `up` 0.14: the room skips that sweep's hit for whoever is behind him |
| a Sweeper hits him | `pj_stagger` | `foot` 0.7 |
| his bar (`gap.jack`, 1..0) | slower punches, shorter block, `pj_fight_idle_hurt`'s `vent` | |
| phase 1 ends (`phase`, `phase: 1, invuln: true`) | `pj_armour_break_fall` | `armour` 0.06 (`armour_broken`), `down` 1.04, `fridge` 1.05 |
| the middle scene, 26 s and [FIRE] | `pj_dying_talk`, then `pj_last_breath` | `take` 2.45, `place` 4.1 · `lets_go` 2.3, `hand_down` 3.1 |
| [TAKE] | `PJ.dmg(a, 'marrow_taken')` | |
| `c6b_terminus` | `pj_carried` (on Lumps) | |

One thing to settle when wiring: he falls "against the fridge", and the fridge is on the flatbed (`COVER`, z 16.4), 15 m
from his spot at the back rail. Either the Sweeper that breaks his armour throws him up the train, or his phase 1
spot moves to the flatbed's back.

## Dev messages (`?storydev=1`)
`G.story.send('bossdev', o)`: `calm` (no arms, lunges or Jack's clock by themselves), `want: 'grab' | 'sweep' | 'snatch'
| 'lunge'` (+ `hi`, `side`), `grip: true` (skip the tells), `sever: true` (every arm), `gap: n`, `pin` (THE GAP holds still), `dmg: n` (+ `part`,
`i`: where it lands; by default the part that counts in this phase). `window.JF_TRAIN` is the client's state.

## Checked, and not
- Rules: `tests/story/train.test.mjs` (14 tests: the table, spawn, THE GAP, each arm, the flinch, phases and the hold,
  plate stages, the Inspector, the wagon bitten off, the finish, the fail, the Blood Drive, junk input, a normal room).
- In a headless browser: the arena, the mask and arms, grips, a flinch, phase 2 and 3 looks, the wagon going, the
  finish, and the mission's steps end to end (the trip to the train, the hold round the middle scene, the defeat,
  the trip back).
- In a browser with drawing switched off while the logic runs (so it runs in real time, 6 to 15 frames a second
  here), then on again for the picture: the Blood Drive really fired at a wrist (the trigger, 6 knot hits, a bloom on
  the sixth bolt, the sever and its blood back, the bolts-left line on the HUD counting down to "thin blood", tracers,
  the trigger dropping on window blur); a Sweeper's tell and its bar running the decks (it rides the deck under it,
  it took 22 off someone standing in it); the fail at 0 m (the hands closed, the line, then gone on the retry).
- Sounds, by spying on the calls (nobody can listen to a headless page): the ring's wind-up, each bolt, the dry
  click, a knot hit, a sever, the bloom, a bolt off the enamel, the haul, the heal, being caught were all called on
  their events. The plate, flinch, lunge, cross and punch-click sounds were not exercised in that run, and the
  Sweeper's two sounds were added after it.
- Still not seen: the hit-stop on screen (its clock is tested in node), the fight played by a person at a real frame
  rate (so the balance is unplayed), co-op.

## Left for later (from the code review, 2026-11-11)
- The Blood Drive's path in the room skips the room's other can't-fire checks (stagger, a soap bubble, a pop quiz, the
  rig, the wrecking ball), and the client decides for itself whether to show blood as free. Neither matters solo;
  both need doing before co-op.
- The arm chains make garbage every frame (a fresh path and joint list an arm a frame). Pool them if a profile says so.
- A run reloaded at m06's `jack` or `break` step picks the fight up at the start of phase 2 (16 m), with the middle
  scene replayed first if it was the `jack` step. A reload in phase 3 also goes back to phase 2's start.

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
- The train and the tunnel are drawn from the Blender train set where its files load ([TRAIN_MODEL.md](TRAIN_MODEL.md)); the
  table's boxes are still the collision and the fallback (`?trainbox=1` shows them).
- Co-op: the arena is sized for four players and the room's rules loop over every human, but only solo has been run.
- Shots are checked against the mask as it hangs straight: its phase 3 swing (a few degrees) is only drawn.
- The slice city has no referee yet, so the trip to the train is the only way the mission's fight can run there.
