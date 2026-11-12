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
