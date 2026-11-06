# OVERDUE WP1: city streaming tech

How the open-world city loads round you. Everything here is behind the debug page `/storytest.html` (WP0's STORY
button takes over from it); the live game never loads any of it.

## Try it
`/storytest.html?city=stress&jank=3` (the 1 km stress test) or `?city=slice` (The Bottom + The Gut + the Commute).
Click to look, WASD, SPACE jump, SHIFT sprint, F fly, E grab a washing line / grapple, 1-4 graphics presets, F3 numbers,
T back to the spawn. Query knobs: `at=x,y,z`, `yaw=`, `fly=1`, `perf=0`.

## How it works
| piece | file | what it does |
|---|---|---|
| plan | `shared/city/plan.js` | the 64 m chunk grid, cities and districts (rects, sky, fog, light), ring radii per preset, hashes |
| chunk | `shared/city/chunk.js` | runs the district generators for one chunk; collision boxes are clipped to the chunk, props / deco / shapes / triggers / lights are kept by the chunk their anchor is in; packed into typed arrays (the transfer, the server cache and the hash) |
| mesh | `shared/city/mesh.js` | chunk -> GPU buffers with no three.js (it runs in the worker): one indexed buffer per kind (solid / flesh / glow / glass / acid) = 1-5 draw calls a chunk; lod 1 for the mid ring; 4 x 4 impostor cells for the far ring |
| world | `shared/city/world.js` | collision over the loaded chunks as ONE box array, so `movePlayer` / `raycast` / `stepProjectile` work unchanged |
| walk graphs | `shared/city/cnav.js` | a 1 m grid per chunk (3 floors a cell, 36 KB), built on a 0.5 m occupancy grid; half links stitch chunks with no knowledge of each other; A* with a greedy heuristic |
| worker | `public/js/city/chunkworker.js` | builds + meshes chunks off the main thread, LRU of 400 packed chunks, the far mesh, the horizon |
| streamer | `public/js/city/stream.js` | rings: collision 5 x 5 chunks, props, near (full mesh), mid (lod 1), far (one impostor mesh for every far chunk); collision gets its own request lane; a frame budget for uploads; LRU drop a ring past where a mesh is drawn; district sky / fog / light blended over 40 m; the nearest 24 lights to the shader |
| materials | `public/js/city/mats.js` | one canvas atlas (a tile per material family) sampled with world UVs wrapped inside the tile; flesh that breathes on a heartbeat; per-pixel light pools; the Potato vertex snap |
| props | `public/js/city/props.js`, `propcode.js` | instanced props, Blender model up close (`public/models/story/s_<id>.glb`, listed in `index.json`, outside the folder the PvP game loads) and a code box model further out or when the file is missing |
| server | `server/citycache.js`, `server/cityworker.js` | ONE read-only chunk cache for every story room (80 MB budget, LRU, pinned while a room uses a chunk), max 8 story rooms ("the city is full"); a `CityView` per room keeps the chunks within 160 m of its players for collision; chunk builds and NPC paths run in a worker thread |
| tests | `tools/city/*.mjs, *.cjs` | see below |

## Numbers (headless Chromium + SwiftShader, so fps is the software renderer's, not a laptop's)
**Hash test** (`tools/city/perf.cjs`): 40 / 40 chunks built in the browser's worker hash the same as in Node.

**Borders** (`node tools/city/borders.mjs`): 4,000 bullets along and across chunk borders, 426 bouncing grenades thrown
across them, 278 walks along and over them: identical to the same area built in one piece; 0 seam stops.

**Stress city fly / walk-through** (`tools/city/perf.cjs <port> <out> stress 0,3`), worst values over the run:
| preset | phase | draw calls | triangles | streamer main thread max / avg | geometry | JS heap |
|---|---|---|---|---|---|---|
| Potato | roofs 60 m/s | 34 | 38k | 11.5 / 0.29 ms | 3.5 MB | 22 MB |
| Potato | high 120 m/s | 31 | 37k | 2.5 / 0.35 ms | 3.7 MB | 22 MB |
| Potato | walk | 41 | 44k | 2.0 / 0.28 ms | 4.1 MB | 18 MB |
| Too HD | roofs 60 m/s | 187 | 172k | 10.1 / 1.65 ms | 11.1 MB | 44 MB |
| Too HD | high 120 m/s | 191 | 169k | 7.3 / 1.12 ms | 12.1 MB | 24 MB |
| Too HD | walk | 188 | 159k | 6.3 / 1.15 ms | 9.1 MB | 20 MB |
Budgets: Too HD <= 600 calls / 600k tris, Potato <= 250 / 150k; no hitch > 50 ms (0 hitches in every run).

**10-minute soak** (Crusty, 600 s of laps at 60 and 120 m/s and walking): 7,735 chunk builds, JS heap 26-30 MB the
whole way, geometry 4-6 MB, 0 hitches, streamer worst frame 19.5 ms, 0 page errors.

**Server heap** (`node --expose-gc --max-old-space-size=256 tools/city/heap.mjs <rooms> <city> 40`: rooms of 2 players
sprinting and driving straight across the city at 11 and 30 m/s, real physics, an NPC path a second per room):
| rooms | city | main heap after GC (delta) | cache | worker walk graphs | main tick avg / max | RSS |
|---|---|---|---|---|---|---|
| 1 | slice | 14.2 MB (+10.1) | 78 chunks, 10.1 MB | 2.7 MB | 0.85 / 23 ms | 147 MB |
| 4 | slice | 16.6 MB (+12.5) | 80 chunks, 10.2 MB | 2.8 MB | 2.4 / 25 ms | 180 MB |
| 8 | slice | 20.6 MB (+16.4) | 80 chunks, 10.2 MB | 2.8 MB | 5.0 / 34 ms | 184 MB |
| 8 | stress | 16.7 MB (+12.6) | 250 chunks, 5.8 MB | 8.8 MB | 3.0 / 16 ms | 223 MB |
The 9th room is refused. With a 6 MB budget (`JF_CITY_MB=6`) the cache evicts in LRU order and stays at 6 MB.

**Flag off**: no file the live game loads was changed (every change is a new file); a bots match on the branch joins
with 5 bots, 0 page errors, no FLAGS warnings, and never requests a story file.

## Sheets
`wp1_stress_3_roofs.jpg`, `wp1_stress_3_high.jpg` (Too HD), `wp1_stress_0_roofs.jpg`, `wp1_stress_0_walk.jpg` (Potato),
`wp1_stress_overview_toohd.jpg`.

## In the real game
A map with `stream: '<city>'` in `MAPS` is drawn by the streamer instead of world.js's one-mesh map: world.js
dynamic-imports `public/js/city/ingame.js` only for such a map (PvP never fetches it), the stream fills the game's own
`BOXES`, the district sky / fog / light go onto the scene, you're held in place until the ground under you is in,
and the gimmicks run on the real player. `public/js/city/storymap.js` registers `story_slice` (the story shell does this
at start-up). `shared/city/storyworld.js` `STORY_SLICE` is the sim-side data (id, spawn, yaw, killY, terminal = the
Machine) shaped like `shared/story/testmap.js` `TEST`: when the sim uses it instead of `TEST`, STORY drops you out of
the Machine into the Bottom. Test: `node tools/city/ingame.cjs <port> <out>`.

## Hooks for the other lanes
- WP0 / the story shell: `new CityStream({ scene, city: 'slice', preset, boxes: BOXES })` and `stream.update(camera, dt)`
  every frame; pass the game's `BOXES` array and every existing collision call works on the city. `stream.ready(x, z)`
  says if the ground under you is loaded (hold the player until it is). `stream.env` has the blended sky / fog / light.
- Gimmicks: `stepGimmicks(me, stream.triggers(), dt, input)` (`shared/city/gimmicks.js`) for ziplines, moving streets,
  lungs, acid, hot zones and paper storms.
- Quests / NPCs: `stream.marks()` (and `SLICE`/`PLACES` in `shared/city/slice.js`) has the places, crowd spots, NPC
  homes, boss spawns; a server `CityView` gives a room collision (`view.world`) and `await view.path(a, b)`.
