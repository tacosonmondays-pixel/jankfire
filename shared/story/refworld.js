// the streamed slice for the solo referee (shared/story/refsys.js): the room plays on MAPS.story_slice, whose boxes are
// a ChunkWorld (shared/city/world.js) holding the chunks round you and round every story enemy that's up. the same
// chunk builder and box packing as the client streamer (public/js/city/stream.js), so the room's shots, staples and
// footsteps hit exactly the walls you see. pure: no node, no dom (the sim worker, tests, co-op later)
import { buildChunk, packChunk, chunkBoxes } from '../city/chunk.js';
import { ChunkWorld } from '../city/world.js';
import { CITIES, chunkOf, chunkId } from '../city/plan.js';
import { STORY_SLICE } from '../city/storyworld.js';

// r: chunks each way round a point (2 = 5 x 5, the client's collision ring) · per: chunks built per tick (~5 ms each)
// keep: built chunks kept for coming back (an LRU, so walking round the block doesn't rebuild it)
export const RW = { r: 2, per: 2, keep: 96, pts: 12 };
const CITY = 'slice';

export function sliceMap() {
  const world = new ChunkWorld([]), S = STORY_SLICE;
  return { name: S.name, stream: CITY, story: true, world, boxes: world.boxes, killY: S.killY, bounds: S.bounds.slice(), spawns: [S.spawn.slice()], home: S.spawn.slice(), cache: new Map() };
}
const OFFS = []; // the ring's offsets, nearest first (the chunk you stand in is always built first)
for (let dz = -RW.r; dz <= RW.r; dz++) for (let dx = -RW.r; dx <= RW.r; dx++) OFFS.push([dx, dz]);
OFFS.sort((a, b) => Math.hypot(...a) - Math.hypot(...b));

function boxesOf(map, cx, cz) {
  const id = chunkId(CITY, cx, cz), c = map.cache;
  let l = c.get(id);
  if (l) { c.delete(id); c.set(id, l); return l; } // (most recent last)
  l = chunkBoxes(packChunk(buildChunk(CITY, cx, cz)));
  c.set(id, l);
  while (c.size > RW.keep) c.delete(c.keys().next().value);
  return l;
}
// the chunks round pts (up to `budget` new builds; r: the ring to want, default the full one). the first point's
// chunks are wanted first. returns how many chunks it still wants (0 = everything round pts is in)
export function streamTo(map, pts, budget = RW.per, r = RW.r) {
  const W = map.world, C = CITIES[CITY], want = new Set(), order = [];
  for (const p of pts.slice(0, RW.pts)) {
    if (!p || !Number.isFinite(p[0]) || !Number.isFinite(p[2])) continue;
    const pcx = chunkOf(p[0]), pcz = chunkOf(p[2]);
    for (const [dx, dz] of OFFS) {
      if (Math.abs(dx) > r || Math.abs(dz) > r) continue;
      const cx = pcx + dx, cz = pcz + dz;
      if (cx < C.cx0 || cx > C.cx1 || cz < C.cz0 || cz > C.cz1) continue;
      const id = chunkId(CITY, cx, cz);
      if (!want.has(id)) { want.add(id); order.push([id, cx, cz]); }
    }
  }
  let built = 0, left = 0;
  for (const [id, cx, cz] of order) {
    if (W.has(id)) continue;
    if (built >= budget) { left++; continue; }
    W.set(id, boxesOf(map, cx, cz)); built++;
  }
  if (r >= RW.r) for (const id of [...W.chunks.keys()]) if (!want.has(id)) W.drop(id); // (a full pass: what nobody's near goes; a quick one round a spawn only adds)
  W.sync();
  return left;
}
// is the ground under p loaded? (a spawn there would fall through)
export const readyAt = (map, p) => map.world.readyAt(CITY, p[0], p[2]);
