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
See TECH_PLAN §6 and DESIGN §8. `{ id, kind: 'cinematic' | 'panels' | 'talk' | 'boss' | 'moment' | 'recap', skip, len,
cast, tracks: [{ t, ...one track }] }`; the scene player (`public/js/story/scene.js`) documents its track list.

## Save data
`toSave(state)` → `{ flags: [], vars: {}, quests: {id: state}, standing, met: [], seen: [], codex: [], log: [], track }`
merges into the save slot's `data` (TECH_PLAN §7; `met`, `codex`, `log`, `track` are new keys for the systems lane).
`fromSave(data)` validates types and sizes and never throws.

## Additions from the script (proposed, PR #75)
The full script is the pack `shared/story/content/overdue.js`. It's authored in the richer files beside it (see
`shared/story/content/index.js` and `docs/story/script/`) and converted into the engine shape above at import, so the
engine files are untouched. `tests/story/overdue.test.mjs` loads it through `makeStory` and an auto-player finishes
all 32 main missions and all 47 side questlines using only host-style events. What the pack needs that the schema
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
