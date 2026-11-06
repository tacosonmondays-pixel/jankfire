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
