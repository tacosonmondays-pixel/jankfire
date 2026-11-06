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
