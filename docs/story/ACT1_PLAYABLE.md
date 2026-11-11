# ACT I PLAYABLE: the shared ledger

The to-do list for making Act I of OVERDUE (`?story=1`) playable start to finish, solo. Three sessions work on it:
**A** world wiring (places, zones, markers, who stands where, the playthrough script; branch `claude/act1-world`),
**B** fights (Mr. Overtime at the gate, Revenue Protection on the train, the train link; `claude/act1-fights`),
**C** encounters (the Unpaid ambush, the stomach-dogs, the Lumps escort, the collectors' truck; `claude/act1-encounters`).
The lead (Story session) merges. Update your rows when something changes.

**How it's checked:** `tests/story/e2e/t_act1.cjs` plays Act I in the real slice city from a fresh save (walks into
zones, talks with F and 1, uses spots, gets in a car) and prints this table's rows; fights and encounters are faked
with the rehearsal's own events until B and C land. `tests/story/act1world.test.mjs` checks every place and person is
a real spot you can walk to and back from.

Status: **works** (done for real in the playthrough) · **stand-in** (works, but with a placeholder: a model, a
skipped bit) · **B** / **C** (that session's part; faked in the run) · **BLOCKED** (can't be done; says why) ·
**untested**.

## m01 PLEASE TAKE YOUR ITEM
| step | goal | where | status | notes |
|---|---|---|---|---|
| sim | win the match (flag sim_won) | the Machine (`sims:suburb` = its terminal) | works | F at the Machine opens the sims; coming back from a match (story/main.js `onMain`) wins it and slams TRAINING COMPLETE. The e2e doesn't play a whole match headless: it comes back the way the menu does |
| c1 | scene c1 | | works | (C1 also plays on the mission card at New Game, so this step passes straight through) |
| tray | take your item (interact) | `bottom:machine` | works | F used to ALSO throw you into the sims (fixed: the story's prompt wins at the Machine) |
| first | talk to Dale | Dale by the Machine | works | |
| name | talk to Gordo | Gordo at the returns counter | works | |
| bins | pick up a lost property weapon | `bottom:lostfound` | works | |
| vend | shoot the dead vending machine (interact) | `bottom:lostfound` | stand-in | a glowing USE spot, not a vending machine you shoot (the loot drop: systems) |
| swing | grapple onto the Wok Roofs | `bottom:rooftops`: the roof stack east of the depot's yard, 10-12 m up, wok dishes on them | works (by hand) | a yellow ring on a gallows arm off the tall roof's edge: hold E, let go at the top, push forward (tested headless, two release timings). GRAPPLE UP! callout with the keys; Dumpling scores you when you land |
| line | ride a washing line back to the Lost & Found | `bottom:lostfound` | works (by hand) | Dumpling's washing line from the tall roof down to the depot's front steps: F to grab it, it drops you at the door (tested headless). RIDE IT HOME callout |
| dinner | talk to Auntie | Auntie at the fire barrel | works | |
| sleep | sleep (interact) | `bottom:lostfound` | stand-in | a USE spot in the hall, not the RETURNS box bed |

## m02 SAUCE RUN
| step | goal | where | status | notes |
|---|---|---|---|---|
| brief | talk to Sharon | her soup stall in the market (`bottom:soup_kitchen`) | works | |
| car | steal a car | a sedan on the lane right above the market, nose toward the slip road (+ the two in the depot) | works | was BLOCKED: no car near the market, no waypoint, getting in never told the quest engine. The market itself is a dead end for cars (the Long Stairs cut its terrace in two), so the car waits on the lane above it |
| pot | load the soup pot | `bottom:soup_kitchen` | works | |
| drive | drive to the Ring Road | `commute:ring_road` (the highway's foot, r 14) | works (in a car) | t_act1drive.cjs: lane east, slip road, round the deck's south end; the zone fires from the driver's seat (about 25 s of driving) |
| ambush | survive the Unpaid (90 s) | | C | |
| deliver | deliver the soup | `gut:border` (the gate) | works (car or foot) | was finishing by itself the moment you held the soup; now you get to the gate, and the trade post talk opens there. By car: the Unpaid's jump ramp over the collapse, up the hill, into the Gut, down the rib avenue and the cliff stairs (act1drive.test.mjs, 47 s) |

## m03 SOMETHING'S DIGESTING
| step | goal | where | status | notes |
|---|---|---|---|---|
| drive | drive into the Gut | `gut:peristalsis` (r 12) | works (car or foot) | c3 plays when you arrive (it played at the step start). By car: the same road as m02, avenue 8 down to Peristalsis Avenue and west along it (act1drive.test.mjs) |
| walk | follow Lumps down Peristalsis Avenue | to `gut:digester_wall` | works / C | the zone works; Lumps waits on the avenue (cast_slice.js STAGE); him leading the way is C's escort |
| dot | talk to Dot | Dot IN the Digester Wall | works | c_dot.glb; Mina has no model (puppet stand-in) |
| agenda | talk to Sister Agenda | inside the Choir Lung's door | works | |
| bishop | (reach the Choir Lung) | `gut:choir_lung` | works | |
| out | get out of the Gut | `gut:border` | works / C | the stomach-dog chase on the way is C's |

## m04 CLOCKING IN
| step | goal | where | status | notes |
|---|---|---|---|---|
| sunset__at, sunset | go to the Sunset Wall, scene c4 | `bottom:sunset_spot` | works | new arrive step: c4 plays when you get there (it used to play wherever you were); Lumps waits there |
| fight | kill Mr. Overtime | `gut:border` | B | |
| rip | scene: the heart rip | | B | |
| after | talk to Overtime (rescheduled) | | works / B | worked in the run (he stood by the gate); after a real fight B places him |
| truck | the truck (choice) | | works / C | the choice opens and takes an answer; the truck itself is C's |
| home | go back to the Lost & Found | `bottom:lostfound` | works | |

## m05 SECOND STOMACH
| step | goal | where | status | notes |
|---|---|---|---|---|
| clinic | take the core to Bev | `gut:clinic_bev`: a flesh-eaten bungalow 40 m west of the gate, her back room | works | |
| install | scene c5 | | works | |
| tutorial | talk to Bev (parts) | Bev in her back room | works | |
| home | go home | `bottom:lostfound` | works | |

## m06 TICKETS, PLEASE
| step | goal | where | status | notes |
|---|---|---|---|---|
| plan | talk to Gordo | Gordo at the returns counter | works | |
| fitted | talk to Bev (loaner) | Bev's clinic | works | |
| board | board the train | `bottom:service_tunnel`: a STAFF ONLY door under the depot, west side of its yard | works / B | the zone fires; the train link is B's |
| ride | scene c6 | | B | |
| hold | keep it off the train | on the train (`commute:underhill_loop`) | B | |
| jack | scene: carry the bit that works | | B | |
| break | break its face | on the train | B | |
| terminus | scene c6b | `commute:tunnel_mouth`: the Loop's portal in the Commute's east cliff | B | |
| p5b | scene: Employee 4417 (END OF ACT I) | | works | plays after the terminus |

## Places added for B and C (A)
- `commute:underhill_loop` [311, groundY, -96]: the Loop's portal in the east cliff of the Commute (black mouth, rails, signal lamps).
  `commute:tunnel_mouth` [292, groundY, -96]: the rails' end out in the open in front of it. Coming back from the train
  could land you here (B: `travelHome` / the train's way out).
- `bottom:service_tunnel` [-205.8, 4, 206.2]: the staff door under the Lost & Found (west of its front steps).
- `gut:digester_wall` [-87, 40, -137.4] on Peristalsis Avenue's north side; Lumps' escort runs from `gut:peristalsis`
  [-120, 40, -130] east to it (C).
- `gut:clinic_bev` [-84.3, 36, -3.2]: Bev's doorstep on the Gut border.
- Exact NPC spots and per-step moves: `shared/city/cast_slice.js` (NPC_SPOTS, STAGE).

## What's left (after run 4, 2026-11-11)
- **Run 5 (all fixes but the tutorial's):** END OF ACT I, all six missions done, no step faked except B/C's. Since then
  the tutorial grapple and line ride are done by hand (t_act1.cjs) and the Sauce Run drive in a real car (t_act1drive.cjs).
- **The jump (lead's call, built by A):** the Unpaid keep the Ring Road's two middle lanes clear and built a ramp of
  desks, doors and filing cabinets to a 3 m lip at the collapse's south edge (`shared/city/act1set.js` RAMP). JUMP IT!
  slams up when you line up on it; ~20+ m/s and you land on the deck past the gap (NAILED IT), slower and you drop into
  the half-metre-deep gap and drive up the planks at its far end (SHORT!). C's ambush ends at the ramp. Collision
  changed only in the deck's chunk column (2:-3 .. 2:3) and the Lost & Found's yard (-4:3, -3:3).
- **Not driven in a browser:** the tight turn onto the deck between the dead cars and on (the headless browser steers
  too late); the same car physics drives it in act1drive.test.mjs. The soup sloshing on the landing is C's/content.
- **A (small):** the narrow stairs between Bottom terraces end at the 0.9 m lip wall of the lane above (jump it). Not
  blocking, but janky; opening them touches many chunks' collision, so it's left for now.
- **B:** the train world has no way back: after END OF ACT I you're still on the train, and the next mission
  (m06_option_c) wants you at the Lost & Found. Coming out at `commute:tunnel_mouth` would fit the script.
- **C:** the ambush (m02), the escort walk (m03), the stomach-dog chase (m03), the truck (m04).
- **Systems / lead:** "shoot the dead vending machine" and "sleep" are USE spots, not the real thing.
- `talkAt: 'arrive'` (overdue.js): a reach step's talk opens when you get there. On (lead's call): m01 swing (Dumpling
  scores the landing), m04 home (aftermath), m05 home (night). Off: m02 drive (the car ride is on the way), m05 clinic
  (moving Bev's intro would open it together with the c5 install scene).
