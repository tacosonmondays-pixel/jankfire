# OVERDUE systems API (the systems lane: WP0, WP3-WP5)

How the story pieces talk to each other. Other lanes (world, scenes, co-op) build on these; keep them stable.

## Flag
Story mode only exists with `?story=1` in the URL or `localStorage.jfStory = '1'`. Without it `main.js` never imports
`public/js/story/`, so the live game is unchanged. Remove the check when the owner approves the slice.

## Hosts (WP0)
- **Solo:** `public/js/story/host.js` `WorkerSocket` is a stand-in WebSocket over a web worker
  (`public/js/story/simworker.js`) that runs `shared/story/sim.js`. `net.connect(hello, onClose, mkSocket)` takes it, so
  the normal client (movement, weapons, HUD) plays story mode with no server room.
- **Co-op (WP10):** `server/story.js` `StoryRoom` will run the same `createSim` per room (stub + room cap of 8 for now).

## Worlds (`shared/story/worlds.js`)
- `worldOf(mapId)` gives `{ id, spawn, yaw, killY, terminal, locker, clinic }`.
- The default (a New Game) is the Bottom in the streamed city slice: `story_slice`, from the world lane's
  `shared/city/storyworld.js`.
- The slice's Locker and clinic stand by the Machine (with simple stand-in meshes) until the world lane builds them.
  Add `locker` / `clinic` to `STORY_SLICE` and they move.
- `?storytest=1` starts New Games on the test lot (`story_test`), which the e2e tests use.
- `sim.world` / `sim.zone` say where a run is; the save's `at.map` picks it on load.

## The sim (`shared/story/sim.js`, pure)
- `sim.state` is the story engine state (`shared/story/state.js` `fromSave(save.data)`); `snapshot()` writes `toSave(sim.state)` back to the top of `save.data`. Pass it to `makeStory({ state: sim.state })`.
- `createSim({ send, save })` -> `sim` with `msg(m)`, `tick(dt)` (20 Hz), `snapshot()` (the save as it stands),
  `sty(kind, o)` (send `{ t: 'sty', k: kind, ...o }` to the client), `me` (the player), `save`, `clock`.
- Speaks the normal protocol for the basics: `join` -> `welcome` (mode `story`, map `story_test`), `pi` -> `po`,
  `s` (movement) is kept for the save, falling under `killY` sends `spawn` (re-dispensed by the Machine).
- **Systems plug in** with `addSystem({ id, init(sim), tick(sim, dt), msg(sim, m) -> true if handled, save(sim) ->
  part, load(sim, part) })`. Each system's save part is `save.data[id]`. Quests, loot, inventory, implants and Late
  Fees each register one.

## Client story API (`G.story`, set by `public/js/story/main.js`)
- `G.story.on(kind, fn)` listen to the sim's `sty` messages (many listeners per kind; `net.on` keeps only one per type,
  so use this instead).
- `G.story.send(kind, o)` -> the sim gets `{ t: 'sty', k: kind, ...o }`.
- `G.story.save(why)` asks the sim for a snapshot and stores it (server slot if logged in, else this browser).
- `G.story.cur` the last save held; `G.story.active()` true while you're in the story world.
- The Machine terminal (F at the vending machine) saves, opens the normal PLAY menu, and when you leave the sim match
  you're put back on the same spot (`sessionStorage.jfStoryBack`).

## Saves (`shared/story/save.js`, pure)
- `newSave(slot)`, `cleanSave(raw, { slot, prev, maxBytes })` -> `{ save } | { error }`, `saveCard(save)`,
  `savePart(key, fn)` (register a cleaner for `save.data[key]`), `SAVE` (3 slots, 64 KB, 1 save / 10 s), `FALLBACK`
  (1 slot, 24 KB).
- A save: `{ v, slot, act, chapter, playtime, coupons, at: { map, p, yaw }, data: { flags, quests, seen, clock, ... } }`.
  Act can only go up by one per save. No `_` keys, depth <= 8, strings <= 2000, finite numbers only.
- Endpoints (`server/story.js`, Bearer token): `POST /api/story/list`, `/api/story/load { slot }`,
  `/api/story/save { slot, save }`.
- Storage (`server/store.js` `storyInfo` / `getStory` / `putStory`): Supabase table `jf_story` once the owner runs
  `docs/story/jf_story.sql`; until then one slot in `jf_users.inv.story` (no SQL re-run needed). The file store acts
  like the table (`JF_STORY_FALLBACK=1` makes it act like the fallback, for tests). `inv.story` is kept out of `/api/me`.

## Tests
`node tests/story/save.test.mjs` (save cleaner + sim protocol), `node tests/story/supamock.test.mjs` (Supabase store,
fake PostgREST), `node tests/story/api.int.mjs <port>` (endpoints + fuzz against a running server).

## Inventory (WP3)
**Data** (`shared/story/items.js`, pure): an item is `{ u, b, r, s, n?, q? }` (id in this inventory, base weapon /
gear / streak / story-item id, rarity, loot seed, name, stack count). An inventory is
`{ bag: [item|null] x cap (20, up to 60), cap, bar: [u|null] x 8, locker: [item], next }`.
- `kindOf(b)` -> `gun | melee | gear | streak | snack | junk | quest | null`; `infoOf(item)`; `stackOf(b)`
  (streaks stack to 3, gear to 5).
- `makeItem(b, { r, s, n, q })`, `invAdd(inv, item)` -> u (0 = full: `item.q` is what didn't fit), `invTake(inv, u, n)`,
  `count(inv, b)`, `hasItem(inv, b, n)`, `barWeapons(inv)`, `starterInv(loadout)`, `cleanInv(raw)` (the save cleaner,
  registered as `savePart('inv')`).
- `invOp(inv, { op, ... }, { atLocker })` is the only way a client edits: `bar {slot, u|null}`, `move {from, to}`,
  `drop {u, n?}`, `stash {u}` / `unstash {i}` (only at a locker). Quest items can't be dropped or barred.
- `addStoryItem(id, { kind, name, color, desc, heal?, stack?, value?, quest? })` registers story things (snacks, junk,
  quest items). The writer's content can add more.

**In the sim** (`shared/story/invsys.js`): `sim.inv`, `sim.drops`, plus `sim.give(item)` -> u (a full bag drops it at
your feet), `sim.dropAt(item, p)`, `sim.takeItem(b, n)` -> bool, `sim.hasItem(b, n)`, `sim.invChanged()`. Quests call
these for `pickup`, `deliver` and rewards.
- Client -> sim: `sty` `inv` (an op above), `pick {id}` (within 3.2 m), `starter {lo}` (new game only), `gear {u}`
  (makes it your G item), `eat {u}`. The normal `item` message uses one of the G stack.
- Sim -> client: `inv {inv, err?}`, `drops {list}`, `drop+ {d}`, `drop- {id}`, plus the normal `ic` and `heal`.
- `give {b, slot, q}` only works with `?storydev=1` (tests).
- `shared/story/solohost.js` does the bits of a server room solo needs: the Card Deck's hand for now.

**Client** (`public/js/story/bar.js`, `wheel.js`, `bag.js`):
- The bar is keys 1-8 (scroll still cycles weapons).
- The bridge hands the bar's weapons to the normal weapon code: `setSlots` with an empty box for every non-weapon
  slot. Gear becomes your G item, snacks are eaten, and streaks wait for HYPE (WP5).
- Hold Q for the wheel: time runs at 20%, the mouse picks, and nothing else gets through.
- I opens the Tote Bag: drag (or click, then click) to the bar, between cells, onto DROP, or into the Locker.
- F picks up the nearest drop, or opens the Locker when you're standing at it.
- `IV.inv` is the last inventory, `IV.on(fn)` runs after each change, and `iconOf(b)` / `itemCell(item)` draw items.
- Story keys are added at runtime with `keys.js` `extendActions('Story', ...)`, so they only exist (and only show in
  CONTROLS) while story mode is loaded.

## Loot (WP4)
**Data** comes from the writer: `shared/story/content/loot.js` (`BRANDS`, `MODIFIERS`, `LEGENDARIES`, `LOOT_TABLES`).
The engine is `shared/story/loot.js` (pure):
- A rolled weapon item is `{ b, r, s, br?, m?, lg? }`.
  - `r` is the rarity: common / rare / epic / legendary / premium.
  - `s` is the seed; `s: 0` means a stock item with no roll (the starter kit, quest weapons).
  - `br` is the brand, `m` is up to 2 modifiers, `lg` is a named legendary.
  - `items.js` keeps only real ids, so a junk brand, mod or legendary is dropped.
- `rollTable(id, rand, { late })` -> `[item]`: a table's `rolls`, weighted entries, late night doubles premium.
  - `rollEntry(e)`, `rollWeapon({ rarity, base, brand }, rand)`, `legendaryItem(id, rand)`.
  - An `item:` entry nothing knows yet (organ cores, before WP5) rolls nothing rather than a ghost item.
- `statsOf(item)` -> `{ dmg, rate, mag, reload, spread, kb, speed, tags, brand, mods, quirk, part }`.
  - The numbers are multipliers (1 = base) rebuilt from the seed, never stored.
  - Rarity ranges: common ±10%, rare 0..15, epic 5..25, legendary 10..35, premium 20..45.
  - ☺ CORP narrows the roll and tightens spread; Bottom Scrap adds a random extra part; Bouncy ×1.8 knockback,
    Fleshy ×1.2 mag, On Loan ×1.25 damage.
  - Behaviour mods and brand rules (sticky, haunted, punctual, overdue, rounded, greasy, rubbery, regen, grudge, jam,
    numbers) are listed in `tags` for combat to act on.
- `compare(a, b)` gives the ▲▼ rows; `statsFor(base)` lists the stats a base has (a cigarette has no magazine);
  `nameOf(item)` is "Bouncy Rounded Cigarette" or the legendary's name.
- `QUIRKS[lg]`, `hitWith(item, ctx)` -> `{ dmg, fx }` and `killWith(item, ctx)` -> `[fx]` are the hooks combat calls.
  - Effects are plain objects: `{heal}`, `{say}`, `{slip}`, `{coupons}`, `{splash:{r,cone,dmg}}`,
    `{puddle:{r,life,kind}}`.
  - The slice's four are in: Late Bloomer, Grandma's Hands, Mother's Ladle, Severance Package.
  - Lumps' Ring's base (`rigpunch`) isn't holdable, so it falls back to the Hand Slapper.

**The stat hook** in `public/js/weapons.js`: `STAT.mul = fn(id, key)` for rate, mag, reload time and spread.
- `story/bar.js` sets it to the held bar item's stats and clears it outside story mode, so the sims are plain.
- Damage multipliers are applied by the host (the solo worker / StoryRoom), not by `server.js`.

**In the sim:** `sim.lootDrop(table, p, ctx)` rolls a table onto the floor. Floor loot is saved per zone
(`save.data.floor`: newest 40 per zone, and at most 60 live before the oldest rot away).

**Client:** `story/lootfx.js` has `beamFor(r)` (per-tier beams, legendary and premium spin rays; they fade when you
stand in them), `lootSound(r, pos, pick)` (blip / chime / double chime / fanfare / choir, made with `audio.js`
`synth`), and `lootCard(item, vs)` (the zine card with ▲▼ against what you hold). The card shows next to the nearest
drop and on hover in the Tote Bag.

## Implants, HYPE and Coupons (WP5)
**Data** comes from the writer: `shared/story/content/implants.js` (50 implants: 12 shop, 23 organ cores, 15 secret;
10 body slots). The engine is `shared/story/implants.js` (pure):
- The body is `{ slots: { slot: { b, ql? } }, perm }`, and an implant is a Tote Bag item `{ b: implant id, ql? }`
  (`ql` is an organ core's quality: bruised ×0.7 / fresh ×1 / prime ×1.2 / premium ×1.5).
- `budget({ act, cats })` is 3, +1 per act after the first, +1 per 3 board cats.
- `driftOf(body, ctx)` is (installed over budget) + permanent drift. `driftBand(d)` is `cale` (0-1), `fading` (2-3) or
  `employee` (4+).
- Over budget, every downside's chance is ×1.5 (`OVERLOAD`).
- `installOp(body, inv, { op: 'install', u } | { op: 'uninstall', slot }, { takeItem, giveItem })`: installing swaps
  the old implant back into the bag. An implant's `drift` is added to `perm` for good.
- `perk(body, id, ctx)` gives the slice's four as numbers (quality and overload applied):
  - `pigeon_eyes { seeLoot 40, wobble, flipEvery 30, flipFor 0.3 }`
  - `spring_knees { jump 1.8, fall 0.5, fold 1/20, stumble 0.6 }`
  - `core_second_stomach { eat by rarity, burpEvery 30, vomitAfter 3, eatHold 0.8 }`
  - `core_cracked_punch_clock { freeMagEvery 60/q, slowAt 20, slowFor 3q, tickR 12, clockEvery 120, clockStill 5, fine 10 }`
- `eatHp(p, rarity)`, `rollQuality(rand)` (loot tables' `core_*` entries roll one).

**In the sim** (`shared/story/bodysys.js`):
- State: `sim.body` (save part `body`), `sim.hype` 0-100 (save part `hype`), `save.coupons`.
- `sim.addHype(n, why)`: HYPE drains 1.5/s after 8 s quiet. Combat should call `sim.addHype(HYPE.kill)` /
  `(HYPE.style)` on kills.
- `sim.addCoupons(n)` returns false if you can't afford a negative n. `sim.bodyChanged()`.
- Client -> sim (`sty`):
  - `clinic { op: buy | install | uninstall }`: only at a clinic. Buying needs a shop implant and the coupons;
    uninstalling costs 150.
  - `streak { u }`: pays `hypeCost(id)` (Moon Boots 25 .. Giant Duck 100), uses one of the stack, then sends the
    normal `{ t: 'streak', reward }` so the existing streak code switches it on.
  - `hypeEv { ev: 'grapple', n }`: capped, rate limited.
  - `eatDrop { id }`: Second Stomach, within 4 m, weapons only.
  - `fine {}`: Punch-Clock, rate limited.
- Sim -> client: `body { body, drift, budget, band }`, `hype { v, need?, why? }`, `coupons { v, d }`, `installed`,
  `ate`, `fined`, `clinicErr`.

**Client** (`public/js/story/body.js`):
- The HUD shows the HYPE bar, a ☺ COUPONS sticker, and DRIFT once it's 2+.
- The perks:
  - Spring Knees: `player.js ME.jumpMul` (the one additive hook, 1 everywhere else) and the fold-on-landing stumble.
  - Pigeon Eyes: x-ray beams within 40 m, view wobble, the 0.3 s back-eye flip.
  - Second Stomach: hold F on a weapon to eat it (a tap still picks it up), burps, vomiting your held gun on the
    third in a row.
  - Punch-Clock: a free magazine every 60 s, a once-a-life slow under 20 HP, ticking, the clock-in or a 10 HP fine.
- The Meat Mechanic clinic (F at the chair) shows your mannequin with its implants, the body slots with TAKE OUT,
  implants in your bag with INSTALL, the shop with prices, and budget / drift text.
- `implantLook(character, ids, over)` puts code-built stand-ins on the mannequin. The art lane's models (ART_BIBLE §6,
  items 20-22) replace them later.

## Cars (WP7)
**Physics** (`shared/story/drive.js`, pure): an arcade car over any box world (`{ query, raycast }`: BOXES on the
client, a `ChunkWorld` on a server).
- `newCar(ty, p, h)`, and `stepCar(car, { f, b, l, r, hand, boost }, dt, world, { slip })` -> events
  `[{ crash, v } | { eject, v } | { land, v } | { overheat }]`.
- Heading `h`: forward is `(sin h, cos h)`, and steering right lowers `h`.
- Handling:
  - top speed by mass (`topOf`): hatch ~35 m/s, bus ~18;
  - a brake, then a slow reverse;
  - steering that tightens at speed;
  - a handbrake drift (grip 2 instead of 11);
  - a boost (×1.55 top, ×1.8 acceleration) that overheats after 4 s and locks out for 3 s;
  - kerbs up to 0.65 m are climbed, anything taller is a wall;
  - no ground means you keep flying (ramps);
  - wall hits bounce (restitution 0.35): over 13 m/s is a crash (car hp), over 27 m/s throws the driver out.
- `opts.slip(x, z)` gives a grip multiplier for peels, marbles and soup.
- `MAXV(ty)` is the most a car can ever do; servers use it to cap claims. `carType`, `seatOf`, `carBoxes`, `fwdOf`,
  `speedOf`. `STORY_CARS.sofa` is the Bottom's sofa-car.

**In the sim** (`shared/story/carsys.js`):
- `sim.cars`, `sim.addCar(ty, p, h, col)`, `sim.carOf()`. Parked cars per world (the Bottom has the sofa-car and a
  hatch by the Machine), saved per zone (`save.data.cars`).
- Client -> sim: `carIn { id }` (within 4.5 m, nobody in it), `car { id, p, h, v, hp }` (~10/s; the driver only),
  `carOut { id, p, h }`.
- Each update is checked: no more than `MAXV × dt + 3` m, no 80 m teleports, no flying up, no claimed speed over the
  cap, at most 40 updates/s, and hp only goes down.
- A refused update comes back as `carFix { id, p, h, why }` and the client snaps back. A car left in the void is towed
  back to the Machine.

**Client** (`public/js/story/drive.js`):
- F next to a car gets in; F again gets out (the left door, else the right / back / front / sunroof, never inside a wall).
- `main.js` runs `G.story.drive(STEP, inp)` instead of `stepPlayer` while you drive (W/S/A/D, Space handbrake, Shift
  boost), and hides the first-person view.
- A chase camera follows the mouse and is kept out of walls. Only a sidearm fires (drive-bys); getting in switches to
  your bar's sidearm.
- The HUD shows boost heat and km/h. Crashes go CRUNCH and shake the screen; a big one throws you out the front.
- The sofa-car is a code stand-in until the art lane's model 9.

## Combat referee (solo)

Story fights run on the game's real room code. `shared/story/refsys.js` (sim system `ref`) starts a `Room` from
`server/room.js` in mode `'story'` inside the story's web worker. `server/storyref.js` is that mode's installer.
The browser loads the room code from `/server/`, which serves only `room.js` and the server modules it imports.

- **Who owns what.** The room owns you while it runs: HP, hits, deaths, respawns and your `seq`. The sim mirrors
  `sim.me` from it for the save. Every normal game message (`fire`, `hit`, `item`, `use`, `parry`, `grap`, `s`,
  `pi`…) goes to `room.handle`. The room's messages go back to the client unchanged, so enemies are remote players
  and the HUD, kill feed and killcam all work.
- **Worlds.** It runs on the test lot (`?storytest=1`) and on the train (`story_train`, the REVENUE PROTECTION fight). The slice is next: worker-side city chunks. Until then the
  slice runs without a referee, as before.
- **Enemies.** These are the game's bots with a story kind: `sk = { kind, max, side, tags, npc, boss, hold }`.
  - The room's HP stays 0..100. The kind's own pool is scaled onto it, and events carry the real numbers.
  - Sides replace teams, so the same side never hurts or hunts itself.
  - Enemies don't respawn. Bodies clear after 4 s of sim time.
  - Default kinds are in `ENEMY_KINDS`. A spawn message can override `name`, `hp` and `w`.

Story → sim:

| message | what |
|---|---|
| `{ t:'sty', k:'spawn', kind, at, n?, id?, name?, hp?, w?, npc?, side? }` | up to 8 at once, within 220 m of you, 24 alive at most; queued while the room loads |
| `{ t:'sty', k:'despawn', id? \| kind? }` | gone, with no kill and no loot |
| `{ t:'sty', k:'damage', id, dmg, why? }` | a scripted hurt (`id:'me'` = you) |
| `{ t:'sty', k:'hold', id? \| kind? \| all:true, on }` | freeze / let go (cutscenes, talks) |

Sim → client:
- `{ t:'sty', k:'refOn', id }` when the room is up.
- `{ t:'sty', k:'refOff', why }` if it couldn't start.
- `{ t:'sty', k:'combat', ev }`, which the client hands to `G.story.combat(ev)` once each.

`ev` follows the format agreed with the story engine (WP8):

| `ev.type` | fields |
|---|---|
| `hit` | `target, kind, dmg, by, weapon, head, hp, max` |
| `kill` | `target, kind, by, weapon, head, at, boss, tags, npc?` |
| `down` | `who, by` |
| `up` | `who` |

`target` / `who` is `'me'`, the story id or NPC id given at spawn, or `'e<n>'`. `by` is `'me'`, `'ally'`, an enemy's
id, `'world'` or `'self'`. Bosses add more: see below.

### Bosses

A boss is a story enemy with a fight on top (`server/storyboss.js`, installed by `storyref.js`). The room owns his HP,
layers, parts, phases, attacks and where he stands. The client only shows them (`public/js/story/bossfight.js` for
the cutscenes, clips and damage states; `bossref.js` for the boss bar, his real size when you shoot, and the actor
standing where the room has him). Built so far: Mr. Overtime's first fight, `overtime_1`, and REVENUE PROTECTION, `revenue_protection_1` (its own part, below).

- **Spawn.** `{ t:'sty', k:'spawn', kind:'overtime_1', at, id? }`. A kind that is a boss in `content/bosses.js`
  spawns as one. One boss at a time. His numbers are the content's: a spawn message cannot change them.
  The client asks for him when the quest reaches his fight step (`JF_STORY.boss.spawn('overtime_1')` by hand).
- **Where the numbers come from.**
  - `content/bosses.js` + `boss_fights.js`: `hp` (4200), `phases[].hp` (the thresholds), `layers` (armour 1500 on
    top of health 2700), `weakPoints[0].crit` (2.5), and each phase's mechanics by name.
  - `public/models/cast/c_<who>.parts.json`: part boxes, the body capsule, clip marks, and the offsets of his hips
    and right stapler through each clip.
  - `BOSS` in `server/storyboss.js`: what the design does not give a number for (attack damage, staple speed, the
    gaps between attacks, the 0.5 for hits off the weak point).
- **Hits.** A `hit` message's ray is tested against his parts in the room. The client's claimed headshots are dropped.
  - plate on: the plate takes hits in full, everything else at half. Damage with no ray (explosions, fire, scripted
    hurts) counts as a hit on the plate.
  - plate off (armour gone): the heart crits (x2.5) from the front. Everything else is at half.
  - the slot crits while it is open (Punch In).
  - one hit never carries past the plate or past a phase's end.
- **Phases.** At a phase's end (50%, then 45%) he stops, and nothing hurts him until the client's cutscene lets him
  go (`hold`), plus one second. Phase 1 is the coffee break: he sits for 15 s or until 45%, and does nothing.
- **Attacks.** Each is an `act` event at the start of its clip. The damage lands on the clip's mark:
  - `staple` (`ot_staple`): aimed at where you stood on the second clack, fired on `fire`.
  - `fan` (`ot_fan`): five staples at chest height on `fan`. A slide goes under them.
  - `slam` (`ot_slam`): on `land` a ring runs out 12 m in 0.9 s and hits whoever is on the floor as it passes.
  - `punchin` (`ot_punchin`): on `grab`, if you are within 5.5 m and in front of him.
  - A staple that misses stays where it hit (`fx` event). Soaked (`soakUntil`), his gaps are 1.5x longer.
- **The end.** At 0 he is beaten, not killed: one `kill` event with `defeat: true`, then he leaves the room. The
  story does the rest (the Heart Rip step, the talk, his retreat).

Sim → client, on top of the events above:

| message / `ev.type` | fields |
|---|---|
| `{ t:'sty', k:'boss', on:true, ... }` | `id, pid` (his room id), `hp, max, health, name, phase, who` |
| `{ t:'sty', k:'boss', on:false, id, pid }` | he left the room (beaten or despawned) |
| `hit` | as above, plus `part` (`plate` `heart` `slot` `head` `gunR` `gunL` `body` `blast`), `crit`, `boss` |
| `phase` | `target, kind, boss, phase, name, line, invuln` (sent twice: `invuln:true` at the change, `false` when he is back) |
| `part` | `target, kind, boss, part, state` (`plate` / `plate_off`) |
| `act` | `target, kind, boss, move, clip, t0, at, yaw` |
| `fx` | `target, kind, boss, k:'staple', at, n` (a missed staple and the wall's normal) |
| `kill` | `target, kind, boss, by, weapon, head:false, at, tags, defeat:true` |

On boss events `boss` is his content id (`'overtime_1'`), not `true`. On a plain enemy's `kill` it stays `false`.

Tests only (`?storydev=1`): `{ t:'sty', k:'bossdev', want:'slam' }` makes that his next attack, and
`{ ..., calm:true }` makes him attack only when asked.

Not built yet: the pin and the mash-free on a staple hit, Fines, the slam's 2 s time freeze, the 3 s "scheduled"
hold inside the slot, the grapple yank on a loose plate, the collectors, the truck set piece, the water / taser
bonus beyond the slower gaps, and the arena on the slice (the referee has no slice world yet).

#### REVENUE PROTECTION (the train fight)

`revenue_protection_1` is a boss the same way (`spawn`, `hold`, the `boss` message, `hit` / `phase` events, one
`kill` with `defeat: true`), but not a walking bot: `server/storytrain.js` (installed after `storyboss.js`) runs it.
Its room player sits in the middle of the mask at `z = -gap` and does nothing by itself. What is built, every number
and what is missing: `docs/story/train/FIGHT.md`.

- **The world.** `story_train` (`shared/story/train.js`, in `worlds.js`): the wagon, the flatbed, the tool van and the
  loco in the bore, all sized by one table (`HW`, `CARS`, `COVER`, `CREW`). The train's boxes carry `car` and `pv: 'rp_train'`:
  the client draws them itself, and the room drops the wagon's when the first phase 3 lunge bites it off. A new game
  with `?storytest=1&train=1` starts there; `G.story.travel('story_train')` / `G.story.travelBack()` move a run
  between worlds (it saves, then starts the same run in the other world's sim).
- **Where the numbers come from.** `content/bosses.js` + `boss_fights.js`: `hp` (5000), `layers` (armour 3750 on the
  Inspector's 1250), `phases[].hp` (60%, 25%), `weakPoints` by name (wrists x2, eye housings x2, the Inspector x2.5).
  `public/models/story/revenue_protection.parts.json`: the rim and mouth sockets, the eye housings, the Inspector's
  crit spot, the smile crack. `RP` in `shared/story/train.js`: everything else, in one table.
- **THE GAP.** Starts 22 m, measured from the train's back (`rear`: 0, then the flatbed's back). Each arm that grips
  closes it 1 m/s; a sever opens it 2 m, a flinch 5 m; 0 m is the fail. The mask is at `z = rear - gap`.
- **Arms** are the room's (`grab`, `sweep`, `snatch`). Each has one HP pool: the wrist knot takes the hit x2, the
  rope and the hand x0.15. `armPose` (shared) is the path both the room's ray and the client's chain use.
- **Hits.** A Blood Drive bolt, or a `hit` from any other gun, is a ray tested in the room (`rayFight`): `knot`,
  `rope`, `plate`, `hole`, `eye`, `lamp`, `insp`, `inspbody`, `mass`. Phase 1: only an open eye housing counts.
  Phase 2: plates in full (and they break), the rest at half. Phase 3: the Inspector, the rest at a quarter.
- **Phases.** At 60% (or when Jack's 90 s run out) the room clears the arms, sets the gap to 6 m, emits `phase`
  `{ phase: 1, invuln: true }` and waits for the client's scene (`hold`), plus a second. The same at 25%.
- **The Blood Drive.** `{ t: 'fire', w: 'blooddrive', k: 'spin' | 'stop' }` and `{ t: 'fire', w: 'blooddrive', o, d }`
  per bolt. Story rooms only. The room checks the 0.8 s spin-up, 14 bolts a second, the 90 m range, walls, and takes
  2 HP a bolt (never your last one; `{ t: 'bdrive', k: 'dry' }` when it can't). Free once `jack_marrow_taken` or
  `seen_mo_carry` is set, or once this fight is past its middle.

Its events (`ev.type`, all with `target`, `kind`, `boss: 'revenue_protection_1'`):

| `ev.type` | fields |
|---|---|
| `state` | `gap, rear, hp, max, phase, name, stage, plates[12] (0 on, 1 crazed, 2 gone), open, marrow, arms[], jack` (on spawn and after a reset) |
| `gap` | `gap, rate` (m/s, so the client can run it between messages), `jack` (his bar, 1..0) |
| `arm` | `id, k, sock, mouth, st (reach / tell / grip / sweep / hold / cut / back / gone), dur, tgt, hi, side, wa?, gp?, hp, max, blood?` |
| `arms` | `clear: true` (a phase change, the end) |
| `hit` | as for every boss, plus `arm` when it was one |
| `plate` | `i, st` |
| `stage` | `stage` (1..3), `name` (`hairline`, `left_eye`, `smile`) |
| `flinch` | `open` (seconds), `gap` |
| `shrug`, `bloom` | `at` (a bolt off the enamel; a cross where the sixth bolt went in) |
| `swept`, `snatched`, `lunge`, `bag`, `off` | what happened to you: `hi` · `gap` · `st: tell / hit, bit, cut?, rear?` · `hp` · (the track) |
| `fail`, `reset` | `why: gap / dead`, `line`; then the fight is back at the phase's start |

Tests only (`?storydev=1`): `{ t:'sty', k:'bossdev', calm?, pin?, want?, hi?, side?, grip?, sever?, gap?, dmg?, part?, i? }`.

For other systems:
- `sim.ref` (`{ room, me }` once up);
- `sim.refSpawn(def, at)` → room id;
- `sim.refEnemies()`.
