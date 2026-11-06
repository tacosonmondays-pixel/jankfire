// Collision over a set of loaded chunks. The physics (shared/physics.js) works on one box array with its own grid, so
// the active set is kept as ONE array: the union of the loaded chunks' boxes, rebuilt (and its grid reset) only when
// the set changes (every 64 m or so). query / raycast / movePlayer keep their signatures: movement, bullets and
// grenades don't know the world is streamed. Used by the client streamer and the server's story rooms.
import { resetGrid, query, raycast, movePlayer } from '../physics.js';
import { CHUNK, chunkOf } from './plan.js';

export class ChunkWorld {
  constructor(boxes = []) { this.boxes = boxes; this.chunks = new Map(); this.extra = []; this.dirty = false; this.version = 0; }
  // id -> box objects (chunk.js chunkBoxes), one chunk at a time
  set(id, list) { this.chunks.set(id, list); this.dirty = true; }
  drop(id) { if (this.chunks.delete(id)) this.dirty = true; }
  has(id) { return this.chunks.has(id); }
  setExtra(list) { this.extra = list; this.dirty = true; } // doors, moving platforms, dropped things: not part of a chunk
  // rebuild the union array in place (callers that imported it see the new contents), then reset its grid
  sync() {
    if (!this.dirty) return false;
    const b = this.boxes; b.length = 0;
    for (const l of this.chunks.values()) for (let i = 0; i < l.length; i++) b.push(l[i]);
    for (const x of this.extra) b.push(x);
    resetGrid(b); this.dirty = false; this.version++;
    return true;
  }
  // is the chunk under (x, z) loaded? (the streamer holds a player in place rather than let them fall through a hole)
  readyAt(city, x, z) { return this.chunks.has(city + ':' + chunkOf(x) + ':' + chunkOf(z)); }
  query(minx, minz, maxx, maxz, out) { this.sync(); return query(this.boxes, minx, minz, maxx, maxz, out); }
  raycast(o, d, maxT) { this.sync(); return raycast(o, d, maxT, this.boxes); }
  movePlayer(pos, vel, dt, canStep) { this.sync(); return movePlayer(pos, vel, dt, this.boxes, canStep); }
}
export { CHUNK };
