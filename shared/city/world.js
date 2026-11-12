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
    Object.defineProperty(b, 'terrain', { value: joinFields(this.chunks), writable: true, configurable: true, enumerable: false });
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

// shaped ground (shared/city/ground.js): the loaded chunks' 'field' grids as ONE heightfield, the shape physics.js
// knows (boxes.terrain: at(x, z), the box a ray says it hit, the bounds rays clip to). null when none is loaded
const fieldY = (f, x, z) => {
  const fx = (x - f.x0) / f.cell, fz = (z - f.z0) / f.cell;
  if (fx < 0 || fz < 0 || fx > f.nx || fz > f.nz) return null;
  const i = Math.min(f.nx - 1, Math.floor(fx)), j = Math.min(f.nz - 1, Math.floor(fz)), u = fx - i, v = fz - j, vz = f.nz + 1, H = f.H;
  if (f.ok && !f.ok[i * f.nz + j]) return null; // (a field drawn only in places: the Gut's swells)
  return (H[i * vz + j] * (1 - u) + H[(i + 1) * vz + j] * u) * (1 - v) + (H[i * vz + j + 1] * (1 - u) + H[(i + 1) * vz + j + 1] * u) * v;
};
export function joinFields(chunks) {
  const by = new Map();
  let x0 = Infinity, z0 = Infinity, x1 = -Infinity, z1 = -Infinity, lo = Infinity, hi = -Infinity;
  for (const l of chunks.values()) if (l.fields) for (const f of l.fields) {
    const k = chunkOf(f.x0 + 0.01) * 4099 + chunkOf(f.z0 + 0.01);
    (by.get(k) || by.set(k, []).get(k)).push(f);
    x0 = Math.min(x0, f.x0); z0 = Math.min(z0, f.z0); x1 = Math.max(x1, f.x0 + f.nx * f.cell); z1 = Math.max(z1, f.z0 + f.nz * f.cell);
    lo = Math.min(lo, f.lo); hi = Math.max(hi, f.hi);
  }
  if (!by.size) return null;
  const at = (x, z) => {
    const l = by.get(chunkOf(x) * 4099 + chunkOf(z));
    if (l) for (const f of l) { const y = fieldY(f, x, z); if (y != null) return y; }
    return null;
  };
  const base = Math.floor(lo) - 2;
  return { x0, z0, nx: x1 - x0, nz: z1 - z0, lo, hi, base, at, fields: by, box: { min: [x0, base, z0], max: [x1, hi, z1], mat: 'ground', terr: 1 } };
}
