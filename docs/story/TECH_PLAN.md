# OVERDUE tech plan: an open-world city in a browser FPS

How story mode runs inside the current game: Three.js client (`public/js/`), Node `ws` server (`server.js`,
`server/`), shared rules (`shared/`), Supabase accounts (`server/store.js`, `supabase.sql`), on a Render starter plan
(512 MB RAM, V8 heap ~256 MB).

Companion docs: [DESIGN.md](DESIGN.md) · [ART_BIBLE.md](ART_BIBLE.md) · [SLICE_PLAN.md](SLICE_PLAN.md)

---

## 1. The size of the thing

| | Jankburg (BR, today) | Greater Jankburg (story) |
|---|---|---|
| playable area | 500 × 500 m (360 m walled core) | **~1,600 × 1,600 m** (10 districts of ~350-500 m) |
| collision boxes | one array, built at load (`build()` in `shared/jankburg.js`) | **~250k boxes**, split into chunks, never all loaded on a client |
| nav graph | ~140k nodes, ~1M links, packed typed arrays (`shared/nav.js`) | built **per chunk**, loaded on demand |
| players | up to the BR cap, one room | 1 (solo) to 4 (co-op) per story room |

The slice (The Bottom + The Gut) is ~500 × 400 m: about Jankburg's size, so it's a safe first step.

## 2. The world format: chunks

- The city is a grid of **64 × 64 m chunks** (25 × 25 = 625 chunks for the full city, ~50 for the slice).
- Each district is a **generator module** like `shared/jankburg.js`: a `PLAN` (roads, streets, lots, landmarks,
  heights) plus a `build(chunk)` that emits only the boxes, deco and props whose bounds touch that chunk. Builders are
  deterministic (seeded `rng` from `shared/map.js`), so the server and every client get the same chunk with no
  download.
- **New files:** `shared/city/plan.js` (the city master plan: district rects, the hill heightfield, highways, the
  chunk grid), `shared/city/<district>.js` per district, `shared/city/chunk.js` (build / cache a chunk: `{ boxes,
  deco, props, lanes, nav, spawns, triggers }`).
- **Reuse:** the `builder`, `wall`, `slab`, `stairs`, `windows`, `shell`, `tower`, `streetlight`, `billboard`, `stall`,
  ... kit already exported from `shared/map.js`.
- **Physics:** `shared/physics.js` already uses an 8 m broadphase grid per box array. For the city, the active box
  set is the **union of loaded chunks** (a chunk keeps its own grid; `query` / `raycast` walk the 1-4 chunks a ray or
  AABB touches). New helper: `shared/city/world.js` with the same `query`, `raycast`, `movePlayer` signatures over a
  chunk set, so movement, hits and projectiles don't change.
- **Heights:** the city is on a hill. Ground is boxes on terraces (steps of 0.5-4 m), plus ramps and stairs, so the
  existing AABB physics still works (no heightmap collision needed). The Long Stairs and steep streets are slopes
  built as stepped boxes with a smooth visual mesh on top.

## 3. Client streaming, LOD and rendering

**Rings around the camera:**
| ring | radius | what's loaded |
|---|---|---|
| **active** | 0-96 m (3 × 3 chunks) | collision, props, NPCs, traffic, triggers, full-detail meshes |
| **near** | 96-224 m (7 × 7) | full meshes, no collision, crowd impostors, parked cars |
| **mid** | 224-480 m | one **merged mesh per chunk** (all buildings, vertex colour, no props) |
| **far** | 480 m + | **skyline impostors**: per-district billboard cards and a few huge landmark low-polys (the ☺ Spire, the Big Stomach, the smokestacks) behind fog |

- **Building chunks off the main thread:** chunk generation runs in a **Web Worker** (`public/js/city/chunkworker.js`),
  which returns typed arrays (positions, colours, box mins/maxs). The main thread only uploads them. Target: a chunk
  builds in < 30 ms in the worker; at most one chunk upload per frame.
- **Merging:** every static building piece in a chunk is merged into 1-3 meshes per material (the `cars.js` approach:
  vertex colour + one merged mesh). Target ≤ 6 draw calls per chunk.
- **Instancing:** repeated props (teeth cobbles, washing lines, chairs, streetlights, rib arches, crowd extras) use
  `THREE.InstancedMesh`, one per prop type per ring.
- **Culling:** frustum culling per chunk (one bounding box each), plus cheap occlusion: districts on the hill hide
  each other, so chunks behind a "skyline" wall (marked in the plan) skip the mid ring when the camera is low.
- **Fog** per district (the existing per-map sky/fog, blended when you cross a border over 40 m).
- **Render presets:** Potato drops the near ring to 128 m and uses impostors from 160 m; Too HD pushes mid to 640 m.

**Client budgets (Too HD / Potato):**
| | Too HD | Potato |
|---|---|---|
| draw calls | ≤ 600 | ≤ 250 |
| triangles | ≤ 600k | ≤ 150k |
| GPU memory (geometry + textures) | ≤ 350 MB | ≤ 150 MB |
| JS heap | ≤ 450 MB | ≤ 300 MB |
| chunks resident | ~150 | ~60 |
| frame time on a mid laptop | 16 ms | 16 ms at 0.5x res |

Chunks leave memory in LRU order once outside the near ring + 1.

## 4. Server: rooms, memory, simulation

### Solo vs co-op
- **Solo runs on the client.** A **story sim** runs in the browser (a Web Worker): NPCs, enemies, traffic, Late Fees,
  quests, loot rolls. That's the whole "server" for solo, and it costs the Render box nothing.
- **Co-op runs on the server**, in a new `StoryRoom` (2-4 players). Same sim code.
- **One sim, two hosts:** the sim lives in `shared/story/` as pure modules (no Node APIs, no DOM): `sim.js` (tick),
  `npc.js`, `enemy.js`, `latefees.js`, `quests.js`, `loot.js`, `implants.js`, `cars.js`. The server's `StoryRoom`
  and the client's worker both import them. The existing server modules that are already pure (`shared/weapons.js`,
  `shared/physics.js`, `shared/traffic.js`, `shared/bodyhp.js`, `shared/rig.js`) are reused as is.
- **Honesty:** in solo, the client is trusted for story progress (it's your own game). Anything that crosses into
  multiplayer (cosmetics, containers, account stats) is only granted by the server, from a **checkpoint report**: the
  client sends the boss kill / mission end with a short log (timings, damage dealt, position samples), the server
  sanity-checks it (plausible times and damage, mission order, rate limits) before granting. Co-op is fully server-side
  like today.

### Server memory (512 MB box, ~256 MB heap)
- **The city is shared, read-only:** chunks are built once per process and shared by every `StoryRoom` (an LRU chunk
  cache keyed by chunk id). Rooms only hold their own dynamic state.
- Budget: **≤ 80 MB** for the chunk cache (≈ 120 chunks with boxes + packed nav), **≤ 6 MB per StoryRoom** (players,
  NPCs, enemies, cars, loot, quest state), **max 8 story rooms** per process (more → "the city is full, try solo").
  That leaves the existing Online / Bots / BR rooms their current headroom.
- **Nav per chunk:** the `shared/nav.js` graph builder runs per chunk with a border overlap of one cell, packed into
  typed arrays (the existing `packNav` approach). Stitching between chunks is by shared border node keys. A city
  chunk's nav is ~3-5k nodes: ~0.3 MB packed.
- Only chunks within 160 m of a co-op player are simulated; NPCs outside it freeze (or are despawned and re-seeded
  later).
- **Tick:** the story sim runs at 20 Hz (the existing rooms' cadence); far NPCs tick at 2-5 Hz.

## 5. NPC crowds and traffic at city scale

- **Three tiers of NPC:**
  1. **Extras** (crowd, ~200 visible): purely cosmetic, client-side, seeded per chunk (`hash(chunk, time slot)`),
     follow sidewalk splines, react with canned animations (flee, wave, ragdoll). Never networked. In co-op every
     client sees the same extras because the seed and the Schedule time are shared (close enough).
  2. **Citizens** (~30 active): can be talked to, robbed, flung. Simulated by the sim, networked in co-op at low rate.
  3. **Actors** (quest NPCs, enemies, cops, bosses): full sim, server-owned in co-op, network like bots do today.
- **The Schedule drives crowds:** each extra has a slot (commute, lunch, home), so Corp Hill empties at night and the
  Gut is always busy. Cheap: a lookup on the district clock.
- **Traffic:** `server/traffic.js` already drives lane-following cars with junctions, honking, crashes and
  explosions, for one map. For the city: lanes are part of each chunk (`lanes`), cars only exist in the active +
  near rings around players (spawn at ring edge, despawn behind), ~25 cars per player. In solo it runs in the
  worker; in co-op on the server (the current module, refactored so the per-map state is per room and lanes come
  from chunks).
- **Police AI** builds on traffic: cop cars use the lane net to path, then leave it for pursuit (steer toward the
  target's predicted point; box-in and PIT are steering offsets); roadblocks spawn on lanes ahead of the player.

## 6. Quests, dialogue and cutscenes: data formats

All story content is **data** in `shared/story/content/`, so writing a quest doesn't need engine work.

### Dialogue
The existing lore-NPC format (`shared/secrets.js`: `lines: { node: { say: [...], opts: [[text, next]] } }`) is kept
and extended:
```js
// shared/story/content/npcs/lumps.js
export default {
  id: 'lumps', name: 'LUMPS', look: 'lumps', voice: { kind: 'tuba', pitch: 0.6, rate: 0.8 },
  home: { chunk: 'bottom:3:5', p: [12.4, 3.0, -8.1], face: 1.2 },
  lines: {
    start: { say: ['...', 'i need soup.'], opts: [['what kind of soup?', 'soup', { if: '!q.sauce.done' }], ['bye', 'bye']] },
    soup: { say: ['the red kind.'], do: ['quest.start:sauce'], cam: 'closeup' },
    bye: { say: ['*cries a little*'] },
  },
};
```
New keys: `if` (condition strings over flags, quest state, standing), `do` (actions: start quest, give item, set flag,
change standing, play cutscene), `cam` (a dialogue camera preset), `voice` (the babble voice).

### Quests
```js
// shared/story/content/quests/sauce.js
export default {
  id: 'sauce', title: 'SAUCE RUN', giver: 'lumps', act: 1, kind: 'main',
  steps: [
    { id: 'car', text: 'steal a car', goal: { type: 'enterCar' } },
    { id: 'pot', text: 'pick up the soup pot', goal: { type: 'pickup', item: 'soup_pot' }, marker: 'bottom:lostfound' },
    { id: 'drive', text: 'deliver soup to the gut border (don\'t spill it)', goal: { type: 'reach', zone: 'gut:border' },
      fail: { type: 'flag', flag: 'soupSpilled' }, timer: 180 },
  ],
  reward: { coupons: 300, item: { roll: 'weapon', rarity: 'rare' }, flags: ['metChoir'], standing: { bottom: 5 } },
  scenes: { start: 'p2_sauce', end: null },
};
```
Goal types (a small fixed set the sim knows): `reach`, `pickup`, `deliver`, `kill`, `killBoss`, `talk`, `enterCar`,
`survive`, `escort`, `photo`, `interact`, `loseFees`, `flag`. Quest state is a tiny object (`{ step, n, t, done }`).

### Cutscenes
Cutscenes are **timelines**, played in-engine by `public/js/story/scene.js`:
```js
// shared/story/content/scenes/c4_clocking_in.js
export default {
  id: 'c4_clocking_in', kind: 'cinematic', skip: true, len: 58, music: 'overtime_theme',
  cast: { ot: { look: 'overtime', at: 'gut:stairs_top' }, lumps: { look: 'lumps', at: 'bottom:sunset_spot' }, you: { look: 'player' } },
  tracks: [
    { t: 0, cam: { path: 'c4_sunset', dur: 6, fov: 50 } },
    { t: 1, say: ['lumps', '*sniff*'] },
    { t: 6, fx: 'clocksStop', sfx: 'tick_loud' },
    { t: 9, anim: ['ot', 'stair_step'], cam: { shot: 'lowAngle', target: 'ot', dur: 4 }, shake: 0.4 },
    { t: 20, say: ['ot', 'the bottom. you are forty years late. i\'m here to collect.'], face: ['ot', 'grin'] },
    { t: 31, anim: ['ot', 'staple_shot'], hitstop: 0.12, impact: 'red' },
    { t: 56, boss: 'overtime' }, // boss intro card, then gameplay
  ],
};
```
- Tracks: `cam` (named spline paths authored as point lists, or shot presets: closeup, overShoulder, lowAngle,
  dolly, whip), `anim` (clips from `anim.js` or a character's own), `say` (bubble + babble voice + jaw flap), `face`
  (puppet face poses), `move` (walk an actor along points), `fx` / `sfx` / `music`, `shake`, `hitstop`, `impact`
  (the anime red frame), `panel` (switch to comic panels: layout + captions + SFX words), `fade`, `letterbox`,
  `boss` (title card), `wait` (until a condition, for scenes mixed with gameplay).
- **Comic panels** render the live scene to 3-6 small render targets at chosen camera shots, then draw them as tilted
  panels with a halftone post-process and the zine UI (HTML/CSS bubbles over the canvas, like the current HUD).
- The player character is **the player's real model** (outfit, implants); in co-op every player's mannequin is cast as
  `you`, `you2`... and stands at marked spots.
- Skipping: hold SPACE solo; co-op uses the existing skip vote (`public/js/skipvote.js`, server `server/skip.js`).
  The server owns "scene done" in co-op, so everyone resumes together.
- A small **scene preview tool** (`tools/scene.cjs <sceneId>` with Playwright) records any scene to an mp4 at Too HD so
  scenes can be reviewed like the other clips.

## 7. Save data (Supabase)

Story saves are bigger and change more than the account row, so they get **their own table**. The existing
`jf_users` table isn't touched (story-earned cosmetics still go in `inv`, as today).

**What the owner would run in the Supabase SQL editor** (appended to `supabase.sql`, safe to run again):
```sql
-- Story mode saves (OVERDUE): 3 slots per account. Only the game server (service key) can read or write it.
create table if not exists jf_story (
  name_lower  text not null references jf_users(name_lower) on delete cascade,
  slot        smallint not null check (slot between 0 and 2),
  version     int not null default 1,          -- save format version (migrations happen in code)
  act         smallint not null default 1,
  chapter     text not null default 'return_to_sender',
  playtime    int not null default 0,          -- seconds
  coupons     bigint not null default 0,
  data        jsonb not null default '{}'::jsonb, -- flags, quests, standing, inventory, implants, cars, safehouses, position
  updated_at  timestamptz not null default now(),
  primary key (name_lower, slot)
);
alter table jf_story enable row level security;
-- story stats shown on the profile (and used by co-op matching). Safe to run again.
alter table jf_users add column if not exists story_act smallint not null default 0;
alter table jf_users add column if not exists bosses_killed int not null default 0;
```
That's the full list: **one new table (`jf_story`) and two new columns (`story_act`, `bosses_killed`)**. Until it's
run, the server falls back to keeping story saves in `inv.story` capped at 1 slot and 24 KB (so the slice can ship
before the SQL re-run), and warns in the log the way `store.js` already does for missing columns.

- **`data` shape** (validated on the server, ≤ 64 KB): `{ flags: [], quests: { id: state }, standing: { corp, bottom },
  turf: { district: ruler }, outposts: { camp: ruler }, bag: [items], bar: [8 refs], locker: [items],
  implants: { slot: item }, cores: [], cars: [], safehouses: [], at: { safehouse }, clocks: { district: minutes },
  seen: [scene ids] }`. Items are compact: `{ b: base, r: rarity, s: seed, n: name? }`
  (stats are rebuilt from the seed, so items stay tiny and can't be hand-edited into stronger ones without the seed
  matching).
- **When:** saves at safehouses, mission ends, boss kills (rate-limited: max 1 per 10 s per account). Solo saves are
  sent by the client, validated (types, sizes, item seeds, act ≤ known progress + 1). Co-op saves are written by the
  server for each player.
- **Store:** new methods in `server/store.js` (`getStory`, `putStory`), plus the same file-store fallback it already
  has for local dev.
- **Endpoints:** `/api/story/list`, `/api/story/load`, `/api/story/save` in `server/accounts.js` (signed token, body
  size cap, `tooDeep` guard, `_` keys stripped, `Object.hasOwn` checks on everything).

## 8. How it plugs into the current game

- **Home screen:** a new **STORY** button (`public/js/home.js`) next to PLAY. It opens a save-slot picker (comic
  panels of where you left off), then loads `public/js/story/main.js`.
- **The PvP is the Machine's training sims** (the story's lore). In story mode, a Machine terminal at a safehouse opens
  the normal PLAY menu as an overlay: the multiplayer code doesn't change at all, story mode just saves your spot,
  hands over to the existing lobby, and puts you back at the terminal when you leave the sim. Sim contracts (faction
  jobs inside a sim) are checked server-side from the match result (map, mode, weapon, win), which the server already
  knows.
- **C1's sim-to-real opening** reuses the real multiplayer HUD and a Training-style local match on the Suburb map,
  then the scene player takes over the camera (a render-to-texture of the match on the Machine's glass).
- **Shared with the rest of the game:** all weapons and their gimmicks (`shared/weapons.js`, the weapon modules and
  models), movement (`public/js/controls.js`, `shared/physics.js`: bhop, slide, grapple, infinite momentum, lasso),
  the mannequin rig and `anim.js` clips, cosmetics and outfits, the HUD and kill feed, `audio.js`, `fx.js`,
  `killfx.js`, the render presets, the traffic cars.
- **Story-only (new):** `public/js/story/*` (streaming, scene player, quest HUD, quick bar + wheel, inventory UI,
  implant UI, car driving, minimap, the turf map), `shared/story/turf.js` (who rules each district and what that
  changes: shop tables, patrol sets, look variants), `shared/story/*` (sim, content), `shared/city/*` (world), `server/story.js`
  (`StoryRoom`, endpoints), new Blender scripts and models.
- **Bridges:** the multiplayer code assumes one small map per room and a fixed loadout. Story needs: a box source that
  is a chunk set (§2), a loadout that is the quick bar (8 slots, any items), weapon instances with rolled stats (a
  stat multiplier object passed into the existing fire/damage code, defaulting to 1 everywhere so multiplayer is
  unchanged), and streaks as items (the existing streak activation, called from an item use instead of a kill count).

## 9. What changes, what's reused, risks

**Reused as is:** weapons, gimmicks and models; movement physics; the grapple and lasso; killstreak behaviours (Wrecking
Ball, Overdrive Rig, etc., `shared/bodyhp.js`, `shared/rig.js`); cosmetics; audio; FX; the mannequin rig and clips; the
Blender pipeline; the dialogue tree format; traffic car models; the skip vote; Supabase store patterns.

**Must change (carefully, additively):**
- Physics/hit code reading a single `boxes` array → accept a world object with the same API (an adapter; multiplayer
  passes a plain array as today).
- Traffic: per-room state and lanes from chunks, plus drivable cars (a client-side car controller, server-validated
  speeds/positions in co-op like player movement).
- Weapon damage/fire paths: an optional stat multiplier per weapon instance.
- Loadout: an inventory-backed quick bar in story rooms only.
- Server: a `StoryRoom` class beside `Room`, with its own message handlers (all validated: types, `Number.isFinite`,
  `Object.hasOwn`, ranges, rate limits, the message budget).

**Risks:**
| risk | why | mitigation |
|---|---|---|
| browser memory / frame time | a city is a lot of meshes | strict rings, merged chunks, impostors, worker builds, budgets checked by a perf test from the first slice package |
| the 512 MB server | co-op rooms + city chunks + existing modes | shared read-only chunk cache, room cap, solo in the browser, a memory test (`process.memoryUsage()` under 8 rooms) |
| solo cheating | the client runs solo | only cosmetics/stats cross into multiplayer, and only after server checks |
| scope | GTA-sized ambitions | the vertical slice first (2 districts), districts added one at a time as their own PR series |
| refactors breaking multiplayer | shared code paths | adapters with defaults that keep multiplayer identical; the full `regress2.sh` regression on every package |
| content load | 10 districts × quests × scenes | data-driven content, generator-built districts, a scene preview tool |
| co-op desync in cutscenes | different machines | server owns scene start/end; scenes are deterministic timelines |
