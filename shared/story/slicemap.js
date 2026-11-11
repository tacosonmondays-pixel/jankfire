// the city slice as a map the combat referee's room can play on (the story worker, a co-op StoryRoom later): every
// chunk's collision boxes in one array, built once (80 chunks, ~56k boxes, ~0.2 s). the client streams the same
// chunks (deterministic, chunk.js), so bullets, bots and grenades agree with what you see. pure: no dom, no node.
//   buildSliceMap() -> a shared/map.js-style map { boxes, spawns, killY, bounds, floorY, story }
import { CHUNK } from '../city/plan.js';
import { SLICE } from '../city/slice.js';
import { buildChunk, packChunk, chunkBoxes } from '../city/chunk.js';
import { STORY_SLICE } from '../city/storyworld.js';

let MAP = null;
export function buildSliceMap() {
  if (MAP) return MAP;
  const boxes = [];
  for (let cx = Math.floor(SLICE.x0 / CHUNK); cx < Math.ceil(SLICE.x1 / CHUNK); cx++)
    for (let cz = Math.floor(SLICE.z0 / CHUNK); cz < Math.ceil(SLICE.z1 / CHUNK); cz++) for (const b of chunkBoxes(packChunk(buildChunk('slice', cx, cz)))) boxes.push(b);
  // spawns: bots that fall out come back near the middle of each district, never in the void
  const spawns = [STORY_SLICE.spawn.slice(), [-44, 36.2, -10], [-120, 40.2, -130], [182, 1, 230]];
  MAP = { name: STORY_SLICE.name, size: 'story', boxes, deco: [], spawns, killY: STORY_SLICE.killY, floorY: -4, bounds: STORY_SLICE.bounds, story: true, spawnSafe: 30 };
  return MAP;
}
