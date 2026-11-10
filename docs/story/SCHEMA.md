# OVERDUE story content format (WP8 engine)

All story content is plain data in `shared/story/content/**`. The engine (`shared/story/story.js`, `quests.js`,
`dialogue.js`, `cond.js`, `state.js`) loads it directly. A content pack is a module that exports any of:
`npcs`, `quests`, `scenes`, `codex`, `zones`, `things` (objects keyed by id). Packs are merged in load order.
Example pack: `shared/story/content/test/lab.js`. Tests: `node --test tests/story/*.test.mjs`.

## Conditions (`if`, `go`, `fail`, ...)
Strings, compiled once, no `eval`: `'!q.sauce.done && (flag.metChoir || standing.bottom >= 5)'`.

| name | value |
|---|---|
| `flag.X` or bare `X` | flag set? |
| `var.X` | number (default 0) |
| `q.ID.active` / `.started` / `.done` / `.failed` | quest state |
| `q.ID.step` | current step id (`q.sauce.step == 'drive'`) |
| `q.ID.at.STEP` | on that step right now |
| `q.ID.n` | total goal progress on the current step |
| `standing.corp` / `standing.bottom` | -100..100 |
| `met.NPC`, `seen.SCENE`, `codex.ID` | true once it happened |
| `has.ITEM` | asks the host (the inventory, WP3) |

Operators: `! && || == != < <= > >= ( )`, numbers, `'strings'`, `true`, `false`. A list of conditions = all of them.

## Actions (`do`, `done`, `onStart`, `onDone`, `onFail`, ...)
A list of `'verb:arg'` strings (or `{ do, arg, ... }` objects). `{ if, do: [...], else: [...] }` branches.

| action | effect |
|---|---|
| `flag:X` / `unflag:X` | set / clear a flag |
| `var:X=3` / `var:X+1` / `var:X-1` | numbers |
| `standing:bottom+5` / `standing:corp-3` | standing (clamped -100..100) |
| `quest:ID` (`quest.start:ID[/STEP]`) | start a quest (at a step) |
| `quest.step:ID/STEP` · `quest.done:ID[/END]` · `quest.fail:ID` | jump / finish (with an ending) / fail |
| `track:ID` | the HUD tracks this quest |
| `meet:NPC` · `codex:ID` · `seen:SCENE` · `log:text` | the codex / log |
| `emit:TYPE/ID` | fire a quest event (e.g. `emit:interact/valve`) |
| anything else (`give:ITEM`, `take:ITEM`, `coupons:N`, `scene:ID`, `toast:TEXT`, `music:ID`, ...) | handed to the host |

## NPCs (`npcs`)
```js
lumps: {
  id: 'lumps', name: 'LUMPS', title: 'the muscle. cries at sunsets',
  look: 'lumps',                      // a look id (public/js/story/looks.js): mannequin / normal / puppet builders
  voice: { kind: 'tuba', pitch: 0.55, rate: 0.8 }, // babble: tuba, kazoo, dialtone, crayon, grumble, beep, choir, wet
  home: { p: [x, y, z], face: yaw },  // where they stand (y = dropped onto the floor). real maps: world coords
  idle: 'sway',                       // idle style: idle, sway, fidget, write, sit
  walk: { loop: [[x, y, z], ...], speed: 1.4 }, // optional patrol loop
  schedule: [{ from: 6, to: 18, at: 'zoneId' }], // optional: where they are by district clock hour
  cam: 'closeup',                     // default talk camera: closeup, over, wide, low
  lines: { start: NODE, ... },
}
```
A **node**: `{ say: [LINE...], opts: [[text, next, { if, do, once }]...], do, go, next, cam, face, again, codex, end }`
- `say` lines: `'text'` (the NPC talks) · `'*does a thing*'` (an action line, no voice) · `['you', 'text']` /
  `['auntie', 'text', 'grin']` (someone else speaks, with a face) · `{ who, t, face, if, do }`.
- `opts`: the answers (shown after the last line). `if` hides one, `do` runs when picked, `once` hides it after.
  No `next` = the chat ends. Same `[text, next]` pairs as `shared/secrets.js`.
- `go: [[cond, node], ...]`: redirect on entry (first match). `again`: lines used the second time you enter.
- `next`: go on to another node after the last line (no answers). Faces: `grin`, `squint`, `sad`, `shock`, `angry`.
- Entering a node is a quest event `{ type: 'talk', npc, node }` and marks `met.NPC` (+ `codex.char.NPC`).

## Quests (`quests`)
```js
sauce: {
  id: 'sauce', title: 'SAUCE RUN', giver: 'lumps', act: 1, kind: 'main', blurb: 'one line for the log',
  if: 'q.return.done',                 // optional: can only start when
  onStart: [...], onDone: [...],
  steps: [
    { id: 'car', text: 'steal a car', goal: { type: 'enterCar' } },
    { id: 'pot', text: 'grab the pot', goal: { type: 'pickup', item: 'soup_pot' }, marker: 'bottom:lostfound' },
    { id: 'drive', text: 'deliver the soup', goal: { type: 'reach', zone: 'gut:border' },
      timer: 180, fail: { type: 'flag', flag: 'soupSpilled' }, failText: 'you spilled it', failTo: 'pot', next: 'end:clean' },
    { id: 'fight', any: true, goals: [ { type: 'killBoss', boss: 'overtime' }, { type: 'flag', flag: 'talkedDown', to: 'spare' } ] },
  ],
  ends: { clean: { grade: 'EXCEEDS EXPECTATIONS', do: ['flag:cleanRun'] } },
  reward: { coupons: 300, item: {...}, flags: ['metChoir'], standing: { bottom: 5 }, codex: ['frag.option_c_1'] },
  scenes: { start: 'p2_sauce', end: null },
}
```
- A step waits for its `goal` (or all `goals`; `any: true` = the first one). A goal can have `n` (count), `text`
  (its HUD line), `marker` (waypoint: a zone id, NPC id or `[x, y, z]`), `optional`, `if`, and `to` (a branch: this
  goal finishing jumps to that step).
- Goal types: `reach` / `leave {zone}`, `talk {npc, node}`, `kill {kind | npc, n}`, `killBoss {boss}`, `pickup {item}`,
  `deliver {item, to}` (talk to `to` while you have it: it's taken), `enterCar {car}`, `interact {thing}`, `photo
  {target}`, `escort {zone}`, `loseFees`, `use {item}`, `scene {scene}` (a scene ended), and tick goals: `flag {flag | if}`,
  `wait {t}`, `survive {t}` (the step's timer doesn't fail it).
- `next`: a step id, `'end'` / `'end:NAME'` (finish with that ending), or `[{ if, to }, ...]`. Default: the next step.
- `timer` (s): runs out = the step fails. `fail`: a condition string, a `{ type: 'flag', flag }`, or an event goal
  (e.g. `{ type: 'leave', zone: 'x' }`). A failed step retries from `failTo` (default itself); `failQuest: true` fails
  the whole quest instead.
- Quest state in the save: `{ step, n: [per-goal counts], t, done?, failed?, end? }`.

## Zones, things, codex
- `zones: { 'gut:border': { p: [x, y, z], r: 6, name } }` (a sphere-ish cylinder; boxes `{ min, max }` later).
- `things: { soup_pot: { zone, item, name, look, if } }`: pickups / interactables the host draws (pickup or interact events).
- `codex: { 'lore.x': { kind: 'lore' | 'char' | 'frag', title, text } }`: the log. `char.NPC` unlocks when you meet them;
  `frag.*` are the Option C fragments.

## Scenes (`scenes`)
Played by `public/js/story/scene.js`; examples of every kind in `shared/story/content/test/lab.js`.
```js
c4_clocking_in: {
  id: 'c4_clocking_in', kind: 'cinematic', skip: true, len: 58,
  cast: { lumps: {}, ot: { look: 'overtime', name: 'MR. OVERTIME', at: 'gut:stairs_top', face: 3.1, scale: 1, voice: {...} } },
  tracks: [ { t: 0, cam: { shot: 'wide', target: 'lumps', dur: 6 } }, { t: 1, say: ['lumps', '*sniff*'] }, ... ],
  onEnd: ['flag:sawClockingIn', 'log:lumps|a caption for the recap'],
}
```
- `kind`: `cinematic` · `panels` (`panels: [...]`) · `talk` (`talk: { npc, node }`) · `boss` (`boss: { name, job, sub, color, target, rehired }`)
  · `moment` (1-3 s, `target`) · `recap` (built from the last 3 `log` entries, `'npc|caption'`).
- `cast`: `{}` = the actor already in the world with that id; otherwise a temporary actor (`look`, `npc` (copy a def),
  `at`, `face`, `scale`, `name`, `voice`, `hidden`). Marks: `[x, y, z]`, a zone id, an actor id, `{ near: actor, d, side }`.
- tracks (`{ t, ... }`, any mix on one entry):
  `cam: { shot, target, from, dur, fov, roll, offset, cut }` (shots: `closeup`, `extreme`, `over` (from → target), `two`,
  `lowAngle`, `wide`, `dolly`, `orbit`, `whip`, `top`) or `cam: { path: [marks], look, dur, fov }` ·
  `say: [who, text, face]` (subtitle + babble + jaw; `*text*` = an action) · `face: [who, face]` · `anim: [who, clip, hold]`
  (clips: wave, nod, shake, shrug, point, cry, flex, bow, stomp, think, write, hold, shock) · `move: [who, [marks], speed]`
  · `look: [who, target]` · `hide` / `show: who` · `sfx: name` (tick, tick_loud, stinger, clunk, beep, whoosh, splut, ding,
  or any `audio.js` sfx) · `fx: name, at` · `shake: 0..1` · `hitstop: s` · `impact: 'red' | 'white'` · `fade: [0..1, s]` ·
  `letterbox: bool` · `title: [big, small, s]` · `boss: {...}` · `slowmo: [k, s]` · `do: [actions]` · `wait: cond`.
- a panel: `{ at, shot: { target, shot, ... }, cap, say: [who, text], sfx: 'SPLUT', sound, face: [who, face],
  anim: [who, clip, t], rect: [x, y, w, h], tilt, bubL }` (3-6 per scene, slammed in about every 1.7 s).
- Every scene is skippable (hold jump) unless `skip: false`, marks `seen.ID`, runs `onEnd`, and fires the quest event
  `{ type: 'sceneEnd', scene }`. A quest's `scenes: { start, end }` play on start / completion.

## Save data
`toSave(state)` → `{ flags: [], vars: {}, quests: {id: state}, standing, met: [], seen: [], codex: [], log: [], track }`
merges into the save slot's `data` (TECH_PLAN §7; `met`, `codex`, `log`, `track` are new keys for the systems lane).
`fromSave(data)` validates types and sizes and never throws.

## Additions from the script (proposed, PR #75)
The full script is the pack `shared/story/content/overdue.js`. It's authored in the richer files beside it (see
`shared/story/content/index.js` and `docs/story/script/`) and converted into the engine shape above at import, so the
engine files are untouched. `tests/story/overdue.test.mjs` loads it through `makeStory` and an auto-player finishes
all 33 main missions and all 47 side questlines using only host-style events. What the pack needs that the schema
doesn't have yet:

**Pack keys**
- `init`: actions for a new game (who rules each district, counters, starting fates). The host runs `S.run(pack.init)` once.
- `autostart`: quest ids the host passes to `S.quests.start` whenever it likes (on load, after a quest ends). `start`
  already checks `if`, so this is how main missions chain and how giver-less side quests unlock. Side quests with a
  giver are offered from that NPC's `start` node instead.
- Systems data the engine doesn't own yet, exported as-is with their schemas documented at the top of each source
  file: `cast` (the full bible), `bosses` (phases, tells, lines, cores, refights), `implants` (perk, downside, look,
  slot, drift, secret clue trails), `loot` (brands, modifiers, legendaries, tables), `items`, `collectibles`,
  `collectibleSets`, `endings` (per-district epilogues by ruler), `activities`, `districts`, `factions`, `storyFlags`.

**Host actions** (`host.act`, beyond give / take / coupons / scene / toast / music)
- `talk:NPC/NODE`: open a conversation at a node. Steps use it for talks that play during a step, and choices use it
  on the pseudo-NPC `choice`. Scenes put it in a track's `do` (tracks may carry `do`).
- `turf:DISTRICT=FACTION` (the pack also sets the flags `turf.D.F`), `boss:ID`, `loot:TABLE`, `implant:ID`,
  `fees:+N` (Late Fees stars), `call:NPC` (a pager call), `unlock:ZONE`, `collect:ID` (the pack also sets
  `codex.col.ID` and `var.frags.SET`).

**Vars the host keeps**
- `var.drift`, `var.cats`, `var.clock.DISTRICT` (minutes past midnight, the district clock).
- The pack itself keeps `var.act`, `var.pages` and `var.frags.SET`.
- Fates are exclusive flags, `fate.CHARACTER.STATE`.

**Small shape notes**
- NPC `home` is `{ zone }` (a zone id) until the districts have coordinates.
- `zones` come with `{ name, district, p: null }`: the district generators fill `p`.
- `things` have `do` (actions on interact) and `how` (a hint).
- NPC `voice` keeps an extra `timbre` (the authored instrument), mapped onto the engine's babble kinds.

**Two engine findings**
- `stepDone` recurses forever when a step has `done` actions. `S.run(s.done)` at depth 0 re-checks the same step,
  which is still complete. The pack works around it by running a step's after-actions at the start of the next step.
- Dialogue stores a `said.*` flag per node visited. A first-option playthrough already reaches 602 flags (394 of them
  `said.*`), over `LIMITS.flags` (600). `said.*` probably wants its own capped store, or a bigger limit.

### Engine support for the additions (WP8, `public/js/story/boot.js` + `scene.js`)
- `init` runs once per new game (flag `init_done`); `autostart` is offered on load and after every quest ends.
- Host actions: `talk:NPC/NODE` opens the conversation once whatever is talking now ends (a scene holds its timeline
  while a choice is open; `choice` has no body, so the box shows without a camera). `boss:ID` plays the boss title
  card from `bosses[ID].card` / `subtitle`. `implant:ID` puts `implant.ID` in the bag, so `has.implant.ID` works.
  `turf`, `loot`, `fees`, `call`, `unlock`, `collect` show a toast until their systems land (fees keeps `var.fees`).
- Vars: `clock.DISTRICT` starts at 17:29 for every district (the sim's clock); `drift` and `cats` wait for their systems.
- `home: { zone }` and `zones` with `p: null`: until the districts have coordinates the client lays every zone out
  on the test lot (labelled signs, districts grouped, act I nearest the Lost & Found) and people stand at their zone.
  A zone's `p` (world coordinates), once the world lane fills it, wins.
- `things` with `do`: a spot at its zone you can use (once, flag `used.ID`). Steps' `pickup` / `interact` goals get
  a spot at their `zone` / `marker` / the thing's zone.
- Scenes in the script's shape (string `cast` values, `dir`, `panel` tracks, string `title` and `boss`, track `if`,
  `flashback`) are adapted on play: panel tracks become the panel list, lines without a camera get coverage
  (closeups on the speaker, two-shots), named camera paths fall back to an orbit until the world has them.
- Characters without a hand-made look get one seeded from their cast entry (`body`, and the `look` text picks the
  puppet's huge feature).
- Dialogue memory is `st.said` (not flags): `said.NPC.NODE` in conditions; packed per character in the save.
- Rehearsal: shift+R fakes the tracked step's next goal (for systems other lanes haven't built yet).

## Boss fights and mechanics (proposed, `claude/overdue-mechanics`)
The script's boss and mechanics data, for the systems and boss lanes. WP9, the first Overtime fight, is the first one
to build against it. Everything below is exported by the `overdue` pack as `bosses`, `mechanics` and `grapple`, and
checked by `validate.js`.

**Boss fight layer**: `shared/story/content/boss_fights.js`, merged into `bosses.js`. Every boss entry has:
- `zone`: the arena's zone id. (This field was called `arena` before; that name now holds the arena design below.)
- `arena: { name, layout, vertical, grapple: [..], hazards: [{ kind, where, effect }], cover: [{ what, breaks }] }`.
  - Hazard kinds: water, lava, acid, oil, electric, fire, void, gas, rad, paper, crush.
  - Liquids are written as hazards, so they can light up as the liquid system lands.
- `layers: [{ bar: 'armour' | 'shield' | 'health', of, how }]`: the health bars, top bar first. `how` says what
  strips each one best. A boss can have two `health` bars (the Twins: one per half).
- `weakPoints: [{ name, glow, exposedBy, crit }]`: the glowing crit spots. `exposedBy` is the action that opens one:
  grapple an armour plate off, parry, slip, shoot inside a slot, and so on.
- `weakness: { element, weapons: [weapon ids], why }`.
  - Elements: fire, water, shock, frost, slip, verdict, explosive, knockback, blood, sleep, grapple.
  - The listed weapons do well against that boss. Every fight is still beatable with anything.
- `adds: [{ name, count, personality, does }]`: minions, each with a personality.
- `setPiece: [{ kind: 'chase' | 'transform' | 'grapple' | 'vehicle' | 'climb', when, what }]`.
- `phases[i].twist`: the mechanical twist each phase adds, on top of its `mechanics` (each with a `tell`).
- `pinata`: the death burst. An organ core (`core`) is always guaranteed.
- `lootTable`: the boss's own loot table. It always has at least one dedicated legendary, so refights farm it.
- `scaling`: how refights scale.
- `uses`: the mechanics ids the fight asks of you. Every fight uses `grapple`.

**Mechanics**: `shared/story/content/mechanics.js`.
- `MECHANICS[id] = { name, kind, game, src, weapons, story: { traversal, puzzles, combat, bosses, side }, taught: { quest, how } }`.
- `GRAPPLE` holds the grapple's own section: routes, shortcuts, secrets, chases, fights, puzzles, races and upgrades.
- Every main mission (and most side quests) has a hook: `mechanic: { uses: [mechanics ids], hook }`.
- `docs/story/MECHANICS.md` is generated from all of this, with the coverage table.

**Grudges** (the Grudge Ledger): `shared/story/content/grudges.js`, exported as `CONTENT.GRUDGES = { RULES, FACTIONS, TRIGGERS, ADAPTATIONS, RESOLUTIONS, RECAPS, BARKS, BARK_KEYS, RECAP_FIELDS }`.
- `ADAPTATIONS[id] = { from (a TRIGGERS id), name, title, look, effect, counter }`; `TRIGGERS[id] = { name, when, weapons?, adaptation, opens }`; `BARKS[faction][key] = [lines]`.
- The rules, the save shape and why it's its own design: `docs/story/GRUDGES.md`. `docs/story/GRUDGE_LEDGER.md` is generated.
