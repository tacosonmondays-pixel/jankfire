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
| c1 | scene c1 | | works | (C1 also plays on the mission card at New Game, so this step is already done by then) |
| tray | take your item (interact) | `bottom:machine` | | |
| first | talk to Dale | Dale by the Machine | | |
| name | talk to Gordo | Gordo at the returns counter | | |
| bins | pick up a lost property weapon | `bottom:lostfound` | | |
| vend | shoot the dead vending machine (interact) | `bottom:lostfound` | | the tutorial loot drop is a USE spot for now, not a vending machine you shoot |
| swing | grapple onto the Wok Roofs | `bottom:rooftops`: the roofs east of the depot's yard, 10 m up | | the e2e puts you on the roof; grappling there by hand is untested headless |
| line | ride a washing line back to the Lost & Found | `bottom:lostfound` | | any way back counts (the zone) |
| dinner | talk to Auntie | Auntie at the fire barrel | | |
| sleep | sleep (interact) | `bottom:lostfound` | | |

## m02 SAUCE RUN
| step | goal | where | status | notes |
|---|---|---|---|---|
| brief | talk to Sharon | her soup stall in the market (`bottom:soup_kitchen`) | | |
| car | steal a car | any parked car | | getting in now tells the quest engine (it never did) |
| pot | load the soup pot | `bottom:soup_kitchen` | | |
| drive | drive to the Ring Road | `commute:ring_road` (the highway's foot, r 14) | | |
| ambush | survive the Unpaid (90 s) | | C | |
| deliver | deliver the soup | `gut:border` (the gate) | | |

## m03 SOMETHING'S DIGESTING
| step | goal | where | status | notes |
|---|---|---|---|---|
| drive | drive into the Gut | `gut:peristalsis` (r 12) | | |
| walk | follow Lumps down Peristalsis Avenue | to `gut:digester_wall` | | Lumps waits on the avenue at the step's start (cast_slice.js STAGE); him walking ahead is C's escort |
| dot | talk to Dot | Dot IN the Digester Wall | | Dot uses c_dot.glb; Mina has no model (puppet stand-in) |
| agenda | talk to Sister Agenda | inside the Choir Lung's door | | |
| bishop | (reach the Choir Lung) | `gut:choir_lung` | | you're already there |
| out | get out of the Gut | `gut:border` | | the stomach-dog chase on the way is C's |

## m04 CLOCKING IN
| step | goal | where | status | notes |
|---|---|---|---|---|
| sunset | scene c4 | `bottom:sunset_spot` | | the scene plays when the step starts, wherever you are (not when you reach the Sunset Wall): see "for the lead" |
| fight | kill Mr. Overtime | `gut:border` | B | |
| rip | scene: the heart rip | | | |
| after | talk to Overtime (rescheduled) | | B | he has to be standing there after the fight |
| truck | the truck (choice) | | C | the collectors' truck |
| home | go back to the Lost & Found | `bottom:lostfound` | | |

## m05 SECOND STOMACH
| step | goal | where | status | notes |
|---|---|---|---|---|
| clinic | take the core to Bev | `gut:clinic_bev`: a flesh-eaten bungalow 40 m west of the gate, her back room | | |
| install | scene c5 | | | |
| tutorial | talk to Bev (parts) | Bev in her back room | | |
| home | go home | `bottom:lostfound` | | |

## m06 TICKETS, PLEASE
| step | goal | where | status | notes |
|---|---|---|---|---|
| plan | talk to Gordo | Gordo at the returns counter | | |
| fitted | talk to Bev (loaner) | Bev's clinic | | |
| board | board the train | `bottom:service_tunnel`: a STAFF ONLY door under the depot, west side of its yard | | B links the train from here |
| ride | scene c6 | | B | |
| hold | keep it off the train | on the train (`commute:underhill_loop`) | B | |
| jack | scene: carry the bit that works | | B | |
| break | break its face | on the train | B | |
| terminus | scene c6b | `commute:tunnel_mouth`: the Loop's portal in the Commute's east cliff | B | |
| p5b | scene: Employee 4417 (END OF ACT I) | | | |

## Places added for B and C (A)
- `commute:underhill_loop` [311, groundY, -96]: the Loop's portal in the east cliff of the Commute (black mouth, rails, signal lamps).
  `commute:tunnel_mouth` [292, groundY, -96]: the rails' end out in the open in front of it. Coming back from the train
  could land you here (B: `travelHome` / the train's way out).
- `bottom:service_tunnel` [-205.8, 4, 206.2]: the staff door under the Lost & Found (west of its front steps).
- `gut:digester_wall` [-87, 40, -137.4] on Peristalsis Avenue's north side; Lumps' escort runs from `gut:peristalsis`
  [-120, 40, -130] east to it (C).
- `gut:clinic_bev` [-84.3, 36, -3.2]: Bev's doorstep on the Gut border.
- Exact NPC spots and per-step moves: `shared/city/cast_slice.js` (NPC_SPOTS, STAGE).

## For the lead
- (filled in from the playthrough)
