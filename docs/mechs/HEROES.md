# Battle Island heroes: the rigs the game loads (names for the Gameplay session)

Batch 1 from `docs/mechs/ROSTER.md`. These are the concept models: they ship as the defaults so the heroes are playable
and look right now. When the owner's Tripo meshes come in, `tripo_swap.py` swaps them in onto the same joints, markers
and clips. Same conventions as PAPER PLANE / NIGHT SHIFT (`MECHS.md`):
- one glb per hero, `public/models/x_mech_<id>.glb`;
- joint nodes with rigid parts; rest frames = the world axes; the mech faces -z, +x is its right, y up, it stands on y = 0;
- markers are empty `mk_*` nodes, also in the meta (`marks`: joint, at, dir);
- the root never moves in a clip;
- the meta ("jf" on the root) has `joints`, `marks`, `clips` (name, dur, loop, hold, partial, note, events), `decal_slots` (with `mk_spray_<n>` markers), `palettes`, `height`.

The hero kit (`public/js/mechlook.js`: rim light, ink, glows, contrails, clip events) works as soon as `buildMech`
loads the file. Every hero also has the shared clips `idle`, `hit_react`, `jump`, `land`, `drop_fall`, `drop_in`,
`hero_intro`, `pilot_in`, `eject` and `destroy`. Look: clean (the owner's references, `docs/mechs/refs/` on
`claude/mech-refs`): glossy painted metal, crisp trims, few strong glows.

Build: `blender52 -b -P tools/blender/mechs/make_hero.py -- hero=<id> qa`. Sheets: `node tools/blender/mechs/clip_sheets.cjs docs/mechs/clips <id> 6`.
In the game before its code exists: `node tools/blender/mechs/hero_game.cjs <port> <out> <id> [preset]`.

## WRECKING BALL (`wrecking`, prefix `wb_`: not `wreckingball`, the killstreak's id)
A 4 m armoured steel ball (radius 2, centre at y = 2) that rolls inside a yoke that doesn't: two axle hubs and a pail
handle with a crane shackle on top. It has:
- team-colour plates on a gunmetal shell, with twin hazard treads it rolls on and thin white trims;
- an open porthole in front, where you see the pilot strapped into a hamster wheel (it spins with the roll);
- fold-out stabiliser feet on the hubs, and rockets under the hubs for PILE DRIVER;
- the grapple hook parked on its chain down the back.

About 33k tris. Height 4.86 m to the shackle.

**Joints:**
- root > hips: the centre, for bob / squash. In clips it moves the whole ball, the slam crater for example.
- hips > ball: the shell. It rolls about local x; **negative rx rolls it forward (-z)**.
- hips > cage: the hamster wheel and seat. It spins about x.
- hips > yoke: the hubs, handle, shackle and rockets. It never rolls.
- yoke > foot_L / foot_R: the stabiliser feet. Pivots at the hubs; rx -95 tucks them back for rolling.
- yoke > hook: the grapple hook and its chain. Set its transform after `poseMech`; the clips key its rotation.
- hook > chain_link: one chain link, the template to repeat along the grapple line.

**Markers:**

| marker | joint | what |
|---|---|---|
| `mk_chain` | yoke | the shackle: where the grapple chain starts (dir up) |
| `mk_hook_eye` | hook | where the chain meets the hook |
| `mk_window` | ball | the porthole's centre (dir -z at rest; it rolls with the ball) |
| `mk_seat` | cage | the pilot's seat in the hamster wheel (it spins with the wheel) |
| `mk_eject` | ball | the back hatch (rolls up to the top in `eject` / `pilot_in`) |
| `mk_slam` | hips | the floor under the ball: slam, PILE DRIVER and the landing |
| `mk_thrust_L` / `_R` | yoke | the rockets under the hubs, pointing down and back |
| `mk_mark` | yoke | above the shackle (overhead marks) |
| `mk_spray_0` / `_1` | ball | the spray / skin slots (front left and front right quarters) |

**Clips:**

| clip | dur | play | events | note |
|---|---|---|---|---|
| `idle` | 2.4 | loop | | a slow breath; the cage rocks, the hook sways |
| `roll` | 1.0 | loop | dust at 0, 0.5 | **one full turn**, linear: set `timeScale = speed / (2 * pi * 2)`. Feet tucked, the pilot goes round with it |
| `cage_spin` | 0.6 | loop, partial | | only the hamster wheel, on top of anything (the pilot gets spun) |
| `chain_throw` | 0.55 | hold | burst at mk_chain 0.26 | fire the hook from `mk_chain` at 0.26 s; ends hanging-ready |
| `chain_swing` | 1.4 | loop | | dangling on the chain (the game swings the root) |
| `slam` | 0.9 | once | slam 0.28 (shake 0.6), dust at the feet | up, then down hard: the impact is at 0.28 s |
| `pile_driver` | 0.8 | hold | bursts at the rockets 0.34 | crouch, launch at 0.34 s (the game shoots it 30 m up); held |
| `pile_drop` | 0.6 | hold | | diving at the spot, feet up, spinning; then `slam` on impact |
| `jump` / `land` / `hit_react` | | | dust | as on the other mechs |
| `drop_fall` / `drop_in` / `hero_intro` | | | slam at the impact | the MECH DROP flow; hero_intro ends with a show-off roll, held with the window facing you |
| `pilot_in` / `eject` / `destroy` | | | pop at mk_eject | the hatch rolls up to the top; destroy slumps it on its side |

Spray slots: two on the ball's front quarters (0.62 m).

## TROLLEY (`trolley`, prefix `tr_`)
A 4 m shopping-trolley mech:
- a chrome wire basket (it tips) on a low steel chassis with team-colour side covers;
- a team-colour push handle with a yellow pound-coin lock;
- a rubber bumper and headlights for ramming;
- four caster wheels; the front-left one is wonky (red hub) and wobbles;
- a fold-down child seat for a rider;
- a rear deck where the pilot stands at the handle;
- a tall orange safety flag, and two boosters under the deck for CLEAN UP AISLE 5.

About 35k tris. 2.6 m to the basket top area, 3.15 m to the flag tip.

**Joints:**
- root > chassis: body bob, lean, the wheelie (keyed position).
- chassis > basket: hinged at its front-bottom edge. **rx -38 scoops, rx -82 dumps.**
- basket > seat: the child seat, hinged at the back rim. **rx +90 folds it down.**
- chassis > handle: the push bar, the coin lock, the posts.
- chassis > bumper.
- chassis > flag: waves, streams back at speed.
- chassis > caster_FL / FR / BL / BR: swivel about y.
- each caster > wheel_FL / FR / BL / BR: spin about x. **Negative rx rolls forward (-z).** Radius 0.32.

**Markers:**

| marker | joint | what |
|---|---|---|
| `mk_seat` | chassis | the pilot stands here on the deck, at the handle |
| `mk_rider` | basket | an ally riding in the basket (the pound-coin lock) |
| `mk_scoop` | basket | the basket's mouth: scooped people go in here |
| `mk_muzzle` | handle | tin cans lobbed from beside the handle (forward and up) |
| `mk_bumper` | bumper | the ram's contact point |
| `mk_thrust_L` / `_R` | chassis | the boosters, pointing back |
| `mk_wheel_FL` / `FR` / `BL` / `BR` | caster | where each wheel touches the floor (drift sparks and dust; on the casters, so they don't spin) |
| `mk_eject` | chassis | above the deck (the pilot gets kicked off) |
| `mk_mark` | flag | above the flag |
| `mk_spray_0` / `_1` | chassis | the spray / skin slots on the side covers (0.42 m) |

**Clips:**

| clip | dur | play | events | note |
|---|---|---|---|---|
| `idle` | 2.0 | loop | | a jiggle; the flag waves, the wonky wheel twitches |
| `drive` | 1.0 | loop | | **one wheel turn**, linear: `timeScale = speed / (2 * pi * 0.32)`. A rattle, the front-left wobble, the flag streaming back |
| `drift_L` / `drift_R` | 0.6 | loop | dust + sparks at the wheels | casters at 35 degrees, the chassis yawing into the turn and leaning out |
| `push` | 0.7 | once | spark at mk_bumper 0.24 (shake 0.35) | TROLLEY PUSH: rock back, ram, hit at 0.24 s |
| `scoop` | 0.8 | once | dust at mk_scoop 0.26 | the basket dips its nose (scooped people go to `mk_rider`) and comes back up |
| `dump` | 1.0 | once | dust at mk_scoop 0.34 | tips the basket right over |
| `seat_down` / `seat_up` | 0.4 | hold | | the child seat flips down / up |
| `boost` | 0.4 | loop | bursts at the boosters | CLEAN UP AISLE 5: a squat, the nose down, two wheel turns a loop, the flag flat out |
| shared | | | | `jump` (the casters flop), `land`, `hit_react` (the wonky wheel spins round), `drop_fall`, `drop_in`, `hero_intro` (a cocky wheelie, held), `pilot_in`, `eject`, `destroy` (the wonky wheel finally comes off) |
