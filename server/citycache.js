// The story city on the server: ONE read-only chunk cache shared by every story room (boxes + packed nav, built once
// per process, LRU-evicted past the byte budget), and a CityView per room that keeps the chunks within 160 m of its
// players loaded for collision (ChunkWorld) and NPC paths (NavWorld). Rooms hold only references into the cache, so
// 8 rooms walking the same streets cost about one set of chunks.
// Budget: <= 80 MB of cache (TECH_PLAN §4), <= 8 story rooms a process (openRoom says no past that: "the city is full").
import { buildChunk, packChunk, chunkBoxes, packedBytes } from '../shared/city/chunk.js';
import { buildChunkNav, NavWorld } from '../shared/city/cnav.js';
import { ChunkWorld } from '../shared/city/world.js';
import { CHUNK, CITIES, inCity, chunkId } from '../shared/city/plan.js';
import '../shared/city/slice.js';

export const CITY_BUDGET = { bytes: Number(process.env.JF_CITY_MB || 80) * 1048576, rooms: Number(process.env.JF_STORY_ROOMS || 8), radius: 160, buildMsPerTick: 12 };
// measured heap per box object (min/max arrays + the object): ~170 B (tests/city_heap.mjs); the estimate errs high
const BOX_BYTES = 200;

export class CityCache {
  constructor(o = {}) {
    this.max = o.bytes ?? CITY_BUDGET.bytes; this.maxRooms = o.rooms ?? CITY_BUDGET.rooms;
    this.map = new Map(); // id -> { id, city, cx, cz, packed, boxes, nav, bytes, pins }
    this.clock = o.clock || (() => performance.now()); // tests run game time faster than real time
    this.bytes = 0; this.rooms = new Set(); this.builds = 0; this.evicted = 0; this.buildMs = 0; this.maxBuildMs = 0;
  }
  // a story room asks to open: null when the city is full
  openRoom(key) { if (this.rooms.has(key)) return key; if (this.rooms.size >= this.maxRooms) return null; this.rooms.add(key); return key; }
  closeRoom(key) { this.rooms.delete(key); }
  // chunk builds share one time budget per 50 ms tick across ALL rooms, so 8 rooms driving into new streets at once
  // never stall the process (the rest wait a tick or two; their players stand on whatever is already in)
  canBuild() { const w = Math.floor(this.clock() / 50); if (w !== this.win) { this.win = w; this.spent = 0; } return this.spent < CITY_BUDGET.buildMsPerTick; }
  peek(city, cx, cz) { return this.map.get(chunkId(city, cx, cz)) || null; }
  // the chunk, built if needed. pinned chunks (in some room's view) are never evicted
  get(city, cx, cz) {
    if (!CITIES[city] || !Number.isInteger(cx) || !Number.isInteger(cz) || !inCity(city, cx, cz)) return null;
    const id = chunkId(city, cx, cz);
    let e = this.map.get(id);
    if (e) { this.map.delete(id); this.map.set(id, e); return e; } // LRU order = Map order
    const t = performance.now();
    const packed = packChunk(buildChunk(city, cx, cz)), boxes = chunkBoxes(packed), nav = buildChunkNav(packed);
    const ms = performance.now() - t;
    this.builds++; this.buildMs += ms; this.spent = (this.spent || 0) + ms; this.maxBuildMs = Math.max(this.maxBuildMs, ms);
    e = { id, city, cx, cz, packed, boxes, nav, pins: 0, bytes: packedBytes(packed) + boxes.length * BOX_BYTES + nav.bytes };
    this.map.set(id, e); this.bytes += e.bytes;
    this.trim();
    return e;
  }
  trim() {
    if (this.bytes <= this.max) return;
    for (const [id, e] of this.map) {
      if (this.bytes <= this.max * 0.9) break;
      if (e.pins > 0) continue;
      this.map.delete(id); this.bytes -= e.bytes; this.evicted++;
    }
  }
  stats() { return { chunks: this.map.size, mb: +(this.bytes / 1048576).toFixed(1), rooms: this.rooms.size, builds: this.builds, evicted: this.evicted, avgBuildMs: this.builds ? +(this.buildMs / this.builds).toFixed(1) : 0, maxBuildMs: +this.maxBuildMs.toFixed(1) }; }
}

// one room's slice of the city: the chunks within `radius` of any of its players. update() at the room's tick rate;
// new chunks are built nearest first, inside the cache's per-tick time budget, so a fast car never stalls the server
export class CityView {
  constructor(cache, city, o = {}) {
    this.cache = cache; this.city = city; this.radius = o.radius ?? CITY_BUDGET.radius;
    this.world = new ChunkWorld([]); this.nav = new NavWorld(); this.held = new Map(); // id -> cache entry
  }
  update(points) {
    const want = new Map();
    for (const p of points) {
      if (!p || !Number.isFinite(p[0]) || !Number.isFinite(p[2])) continue;
      const r = Math.ceil(this.radius / CHUNK), pcx = Math.floor(p[0] / CHUNK), pcz = Math.floor(p[2] / CHUNK);
      for (let dx = -r; dx <= r; dx++) for (let dz = -r; dz <= r; dz++) {
        const cx = pcx + dx, cz = pcz + dz;
        if (!inCity(this.city, cx, cz)) continue;
        const x0 = cx * CHUNK, z0 = cz * CHUNK, d = Math.hypot(Math.max(x0 - p[0], 0, p[0] - x0 - CHUNK), Math.max(z0 - p[2], 0, p[2] - z0 - CHUNK));
        const id = chunkId(this.city, cx, cz);
        if (d <= this.radius && (!want.has(id) || want.get(id)[2] > d)) want.set(id, [cx, cz, d]);
      }
    }
    let builds = 0;
    for (const [id, [cx, cz]] of [...want].sort((a, b) => a[1][2] - b[1][2])) {
      if (this.held.has(id)) continue;
      let e = this.cache.peek(this.city, cx, cz);
      if (!e) { if (!this.cache.canBuild()) continue; e = this.cache.get(this.city, cx, cz); builds++; }
      if (!e) continue;
      e.pins++; this.held.set(id, e);
      this.world.set(id, e.boxes); this.nav.set(cx, cz, e.nav);
    }
    for (const [id, e] of this.held) if (!want.has(id)) { e.pins--; this.held.delete(id); this.world.drop(id); this.nav.drop(e.cx, e.cz); }
    this.world.sync();
    return builds;
  }
  ready(x, z) { return this.world.readyAt(this.city, x, z); }
  path(a, b, max) { return this.nav.path(a, b, max); }
  close() { for (const e of this.held.values()) e.pins--; this.held.clear(); this.world = new ChunkWorld([]); this.nav = new NavWorld(); }
}

export const cityCache = new CityCache(); // the process's one cache
