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

## The sim (`shared/story/sim.js`, pure)
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
fake PostgREST), `node tests/story/api.test.mjs <port>` (endpoints + fuzz against a running server).
