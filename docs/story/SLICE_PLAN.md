# OVERDUE vertical slice plan

**The slice:** The Bottom + The Gut + a strip of The Commute between them, Act I from **C1 "Please Take Your Item"**
to **C5 "Second Stomach"**: win a sim match and get dispensed out of the Machine into the ruins, steal a car, drive soup
across The Commute while the Unpaid raid you, meet Gristle & Sons' Choir, fight Mr. Overtime on the Gut border, rip out his
punch-clock heart, install it. With loot, the quick bar, 3 implants, Late Fees with a car chase, and 2-player co-op
drop-in. About 45-60 minutes of play.

**Done means:** a new player clicks STORY, plays the whole slice solo or with a friend, and it looks and feels like
JANKFIRE (juice, jank, the comic UI), runs at 60 fps on a mid laptop at the default preset, and the multiplayer modes
pass the full regression unchanged.

Companion docs: [DESIGN.md](DESIGN.md) · [ART_BIBLE.md](ART_BIBLE.md) · [TECH_PLAN.md](TECH_PLAN.md)

Sizes: **S** ≈ 1 session, **M** ≈ 2-3 sessions, **L** ≈ 4-6 sessions, **XL** ≈ 7+ sessions (one session = one feature
branch + builder/reviewer/fixer pass, as in CLAUDE.md). Each package is a `claude/f-story-<name>` branch and a
worktree; packages merge into `claude/int-story` one at a time, then a PR to `main` per wave. Everything is behind the
STORY button, so `main` can take half-built packages without touching multiplayer.

---

## The work packages

### WP0. Story shell + STORY button (S)
- **Scope:** the STORY button on the home screen, save-slot picker (empty slots for now), `public/js/story/main.js`
  entry that loads a test map and the normal player controller; a **Machine terminal** that opens the normal PLAY menu
  and brings you back afterwards (the PvP is the sims); `shared/story/` and `shared/city/` folders;
  `server/story.js` with an empty `StoryRoom` and the `/api/story/*` endpoints using the `inv.story` fallback.
- **Files:** `public/js/home.js` (one button), `public/js/story/main.js`, `server/story.js`, `server.js` (wire-up
  only), `server/store.js` (`getStory` / `putStory`), `supabase.sql` (the `jf_story` block, see TECH_PLAN §7).
- **Acceptance:** STORY opens the picker; New Game drops you on a test map with your loadout; the terminal round-trips
  into an Online/Bots match and back to the same spot; a save round-trips
  through the server (ws test); every multiplayer regression passes; endpoints reject bad input (fuzz test).
- **Depends on:** nothing. **Do first.**

### WP1. City streaming tech (XL)
- **Scope:** the chunk grid, `shared/city/plan.js` + `chunk.js` + `world.js` (box query/raycast over chunk sets), the
  chunk worker, the LOD rings (active / near / mid merged / far impostors), instancing, culling, per-district fog
  blending, budgets per render preset, a perf HUD (F3: chunks, draw calls, tris, heap).
- **Files:** `shared/city/*`, `public/js/city/*` (`stream.js`, `chunkworker.js`, `impostor.js`), adapters in
  `shared/physics.js` callers (additive).
- **Acceptance:** a 1 × 1 km stress city of generic blocks streams with no hitches > 50 ms while sprinting and
  grappling across it at max speed; Too HD ≤ 600 draw calls, Potato ≤ 250; JS heap stays under budget after 10
  minutes (Playwright perf script); movement, bullets and grenades collide correctly across chunk borders (test that
  fires along borders); server builds a chunk deterministically identical to the client's (hash test).
- **Depends on:** WP0.

### WP2. The Bottom + The Gut districts (XL, art max effort)
- **Scope:** the two district generators plus a Commute strip (stacked pastel scrap houses on a rubble hill, washing-line rails, the Long Stairs,
  the Lost & Found; intestine streets, rib arches, lungs, peristalsis streets, the Big Stomach, the Gut border with
  flesh creeping over houses, a stretch of dead-traffic highway with a raider camp), sky/fog/light per district, the first ~19 assets from ART_BIBLE §6 (1-4 incl. the Machine, 8-15, 17,
  25, 27, 29, 30), the two traversal gimmicks (washing-line ziplines, peristalsis + lung trampolines), district music beds.
- **Files:** `shared/city/bottom.js`, `shared/city/gut.js`, `tools/blender/make_story_*.py`, `public/models/s_*.glb`,
  `public/js/story/gimmicks.js`, `public/js/music.js` (new tracks, additive).
- **Acceptance:** screenshots + an HD clip of both districts at Too HD and Potato; turnaround sheets for every new
  model; the Blender QA gate; flying the whole slice area at speed with no holes, no floating buildings, nothing
  you can fall through (bot walkers + a Playwright free-fly); the gimmicks work and feel good (clip).
- **Depends on:** WP1 (chunks). Art can start in parallel on day one.

### WP3. Quick bar + weapon wheel + inventory (M)
- **Scope:** the 8-slot quick bar (1-8, scroll), the hold-Q radial wheel with time slow (solo), the Tote Bag grid UI,
  drag-to-bar, safehouse locker, item pickup/drop, the inventory data model in `shared/story/items.js`.
- **Files:** `shared/story/items.js`, `public/js/story/bar.js`, `public/js/story/wheel.js`, `public/js/story/bag.js`,
  a loadout bridge so the existing weapon code reads from the bar.
- **Acceptance:** every existing weapon, gear and melee works from any slot (automated sweep in Training-like story
  test room); the wheel opens/closes with no input leaks (can't fire while open); inventory survives save/load; the UI
  matches the zine style (screenshots); server rejects bar/bag edits for items you don't have (co-op ws test).
- **Depends on:** WP0.

### WP4. Loot drops (M)
- **Scope:** rarity rolls (Common → ☺ PREMIUM), stat ranges per rarity, brands, 1-2 modifiers, 4 named legendaries for
  the slice (The Late Bloomer, Grandma's Hands, Mother's Ladle, Severance Package), item seeds → stats, loot beams +
  per-tier sounds, the compare card (▲▼), the stat multiplier hook in the fire/damage code (defaults to 1).
- **Files:** `shared/story/loot.js`, `shared/story/legendaries.js`, `public/js/story/lootfx.js`, `public/js/audio.js`
  (new sounds, additive), small additive hooks in weapon fire/damage paths.
- **Acceptance:** 10,000-roll distribution test matches the table; seeds rebuild identical stats on client and server;
  multiplayer damage unchanged (regression + a unit test with multiplier 1); legendary quirks each have a test; HD clip
  of drops and the ☺ PREMIUM choir beam.
- **Depends on:** WP3.

### WP5. Three implants + the first organ core install (M, models high effort)
- **Scope:** body slots, the implant data model, the Meat Mechanic clinic UI, the Body Budget; three implants:
  **Pigeon Eyes** (loot through walls; backwards eye wobble), **Spring Knees** (huge jump; the wrong knee folds 1 in 20
  landings), **Second Stomach** (eat weapons for HP; burps). Plus the **Cracked Punch-Clock** core from WP9. Visible
  model changes on the mannequin (ART_BIBLE §6, 20-22).
- **Files:** `shared/story/implants.js`, `public/js/story/implants.js`, `public/js/story/clinic.js`, models.
- **Acceptance:** each perk and each downside measurably happens (tests: jump height, eat → HP by rarity, burp
  broadcast in co-op); installs persist; other players see the implants; screenshots of each look.
- **Depends on:** WP3 (items). The Punch-Clock core needs WP9 for its drop, not for its code.

### WP6. Late Fees + Unpaid raiders + a chase (L)
- **Scope:** **Unpaid raiders** (on foot and on a war-rig, built on the existing bot AI) for the Sauce Run ambush and
  the raider camp; the Late Fees meter (★1-★3 in the slice: Punctuality Officers on foot, Timekeeping cruisers, Collections
  vans with repo hooks), crimes that add fees, line-of-sight search + drain, hiding in the Gut (overdue zone, Corp
  won't follow past ★3), the Late Desk, the ☺ clock-face HUD stars, cop AI on foot and in cars (pursuit, box-in, PIT,
  roadblocks on lanes ahead).
- **Files:** `shared/story/latefees.js`, `shared/story/cops.js`, `public/js/story/feeshud.js`, traffic refactor
  (per-room, lanes from chunks) in `server/traffic.js` + `shared/traffic.js` (additive), models 23, 24, 26.
- **Acceptance:** scripted crimes raise the right stars; each tier spawns its units; a 2-minute chase clip where cops
  ram, box in and set a roadblock; losing them works by LOS, by the Gut, and by paying; multiplayer traffic unchanged
  (regression on Suburb/Jankburg traffic).
- **Depends on:** WP1, WP7 (for car chases; foot-only ★1 can start earlier).

### WP7. Drivable car basics (L)
- **Scope:** get in / yank out (driver ragdolls), arcade driving (throttle, brake, handbrake drift, overheating boost),
  momentum kept, jank on marbles/peels, crash ejection, cars as projectiles for the existing crash/explosion rules,
  shooting from the driver seat (sidearm), a passenger seat, the sofa-car (model 9), garage at a safehouse. Co-op:
  client-driven like player movement, server-validated (speed caps, teleport checks).
- **Files:** `shared/story/drive.js`, `public/js/story/drive.js`, `public/js/cars.js` (wheel/steer hooks, additive),
  `server/story.js` (validation).
- **Acceptance:** drive the slice end to end; drift and boost clips; crash physics funny and readable; anti-cheat ws
  tests (impossible speeds and teleports rejected); passenger shooting in co-op.
- **Depends on:** WP1.

### WP8. One questline with NPC dialogue + cutscenes (L, animation max effort)
- **Scope:** the quest engine (goal types from TECH_PLAN §6), the extended dialogue format (`if` / `do` / `cam` /
  `voice`), the babble voices, the quest HUD + map markers, mission start/end cards; the **scene player** (cinematic
  timelines, comic panels, talk camera, boss intro cards, skip + co-op skip vote); the slice's content: quests *Return
  to Sender*, *Sauce Run*, *Something's Digesting*, *Clocking In*, *Second Stomach*, plus two side quests (*Leg Day*,
  *Hairball*); scenes **C1 (sim-to-real), P1b "The Final Quarter", P2, C3, C4,
  C5**, the Heart Rip moment, the Mr. Overtime title card; characters Auntie
  Spreadsheet, Lumps, Wee Gordo, a Choir singer, the Meat Mechanic (models 5-7, 16, 18) with face rigs.
- **Files:** `shared/story/quests.js`, `shared/story/dialogue.js`, `shared/story/content/**`, `public/js/story/scene.js`,
  `public/js/story/panels.js`, `public/js/story/talk.js`, `public/js/story/questhud.js`, `public/js/audio.js` (babble,
  additive), `tools/scene.cjs` (scene recorder).
- **Acceptance:** play the questline start to end in a Playwright run (scripted inputs) solo and co-op; every scene
  recorded to mp4 at Too HD and reviewed (frame contact sheets); skip works solo and by vote; dialogue conditions and
  actions tested; puppet faces blink, flap and grin (pose sheet).
- **Depends on:** WP0; content needs WP2 for places; the scene player itself can start right away on a test map.

### WP9. The first nemesis fight + organ core drop (L, model and animation max effort)
- **Scope:** **Mr. Overtime** (model 19: rig, clips: walk, stair step, staple shot, punch-in grab, overtime slam,
  coffee break, stagger, retreat), the fight 1 arena on the Gut border (lungs bounce you over slams), the moveset
  (staples that pin you and stay as grapple points, Punch In grab with the scheduled timer, Overtime Slam time-freeze
  ring, paper fines on the HUD, coffee break), weak point (the punch-clock heart), boss HP scaling for co-op, the core
  drop (each player rolls quality: Bruised / Fresh / Prime / Premium), refight via "POSITION REFILLED".
- **Files:** `shared/story/bosses/overtime.js`, `public/js/story/bosses/overtime.js`, `tools/blender/make_overtime.py`,
  `public/models/c_overtime.glb`, sounds in `audio.js` (dial-tone babble, the tick, staples).
- **Acceptance:** the fight is beatable solo and in co-op (bot-driven test for completion + a human playtest clip),
  every move is telegraphed (clip review), he never gets stuck (arena nav test), the core drops and installs (with
  WP5), the refight shows the REHIRED card; turnaround + pose sheets; an HD fight clip.
- **Depends on:** WP2 (arena), WP5 (install), WP8 (intro card, C4 scene). The model and moveset can start on a test map
  on day one.

### WP10. Co-op drop-in for 2 players (L)
- **Scope:** `StoryRoom` with 2 players (built to allow 4 later), join a friend from the friends/party UI if within one
  act, mission sync (host's mission; joiner gets credit or "temp contractor" rewards), instanced loot per player,
  shared Late Fees and HYPE, revives ("paperwork processed"), shared cutscenes with skip vote, both in one car,
  co-op saves written by the server, the shared read-only chunk cache and the room cap.
- **Files:** `server/story.js`, `shared/story/sim.js` (host-agnostic tick), `public/js/story/net.js`, the lobby join
  path (`server/lobby.js`, additive).
- **Acceptance:** 2 headless clients play the questline together (ws + Playwright), drop-in mid-mission and drop-out
  without breaking the host; loot is per-player; a memory test with 8 story rooms keeps the server under budget next to
  a full Online room; every story message handler fuzzed (bad types, NaN, huge arrays, deep nesting, spam).
- **Depends on:** WP0, WP1 (shared chunks), and the systems it syncs (WP3-WP9) for full coverage. Start the room + sync
  skeleton early, then fold systems in as they land.

### WP11. Slice polish + integration (M)
- **Scope:** the slice's balance pass, the Previously-on recap, the Chronicle, the first patch-notes line (added by the
  coordinator), a perf pass on low-end, a full regression, the showcase clip for the owner.
- **Acceptance:** a fresh account plays the slice in one go with no blockers (two playtest clips, solo and co-op);
  perf budgets hold; multiplayer regression green.
- **Depends on:** everything.

---

## Order and parallel lanes

```
week-ish 1  WP0 shell ─────┐
            art for WP2 + Overtime model (WP9 art) start right away
week-ish 2  WP1 streaming ──────────────┐      WP3 bar/bag ──┐      WP8 scene player (test map)
week-ish 3  WP2 districts (on chunks) ──┤      WP4 loot ─────┤      WP7 cars
week-ish 4  WP9 Overtime fight ─────────┤      WP5 implants ─┘      WP6 Late Fees + chase
week-ish 5  WP8 content (quests, scenes in the districts) ─────── WP10 co-op (skeleton since wk 2)
week-ish 6  WP11 polish + regression + showcase → PR to main
```

**Lanes that can run at once** (separate sessions, separate worktrees):
1. **World lane:** WP1 → WP2 (and later WP6's traffic refactor).
2. **Systems lane:** WP3 → WP4 → WP5.
3. **Vehicles lane:** WP7 → WP6.
4. **Story lane:** WP8 (scene player first, content last).
5. **Boss lane:** WP9 (art and moveset first, arena last).
6. **Net lane:** WP10 (skeleton early, folds systems in).

With usage limits, run 2-3 lanes at a time, in this priority: world, story, systems; then vehicles and the boss; net
last.

| WP | name | size | depends on |
|---|---|---|---|
| 0 | story shell + STORY button | S | — |
| 1 | city streaming | XL | 0 |
| 2 | The Bottom + The Gut | XL | 1 (art: none) |
| 3 | quick bar + wheel + inventory | M | 0 |
| 4 | loot drops | M | 3 |
| 5 | 3 implants + core install | M | 3 (core drop: 9) |
| 6 | Late Fees + raiders + chase | L | 1, 7 |
| 7 | drivable cars | L | 1 |
| 8 | questline, dialogue, cutscenes | L | 0 (content: 2) |
| 9 | Mr. Overtime fight 1 + core | L | 2, 5, 8 (art: none) |
| 10 | co-op drop-in (2p) | L | 0, 1, then 3-9 |
| 11 | polish + integration | M | all |

**Owner checkpoints** (things only the owner decides): the look of the Bottom and the Gut (screenshots after WP2's first
pass), Mr. Overtime's design (turnaround after the first model pass), the cutscene style (C1 clip), the `supabase.sql`
re-run for `jf_story` (exact click steps go in that PR: Supabase → SQL Editor → New query → paste the new block →
Run), and when to show the slice to players.

## After the slice
Districts ship one at a time as their own package series (district generator + art, its quests and scenes, its
takeover questline with the DEAL / TAKEOVER choice, its boss and core, its traversal gimmick). **Hostile Takeovers**
(`shared/story/turf.js`, the turf map, ruler-dependent shops and patrols) lands with the first company district: Pinstripe → The Checkout → Number Works → Mr. Overtime fight 2 (freeway chase) →
Chrome Gristle → Evergreen Acres → The Lates (fight 3) → The Margins → Corp Hill → Act V and the three endings. Late
Fees ★4-★5, the radio, races and the other side activities slot in between.
