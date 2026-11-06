// the Long Stairs walk: node tools/city/longstairs.mjs (a body walking north from the market reaches the Gut gate, no jumps)
// walk up the Long Stairs from the bottom to the gate with the real physics
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import '../../shared/city/gens.js';
const W = new ChunkWorld([]);
for (let cx = -2; cx < 1; cx++) for (let cz = -1; cz < 4; cz++) W.set(cx + ':' + cz, chunkBoxes(packChunk(buildChunk('slice', cx, cz))));
W.sync();
const p = [-44, 0.2, 252], v = [0, 0, 0]; let g = false, maxY = 0, jumps = 0;
for (let k = 0; k < 60 * 60; k++) { v[0] = 0; v[2] = -7; v[1] -= 24 / 60; const r = W.movePlayer(p, v, 1 / 60, g); g = !!r.ground; if (r.wall && g) jumps++; maxY = Math.max(maxY, p[1]); if (p[2] < -10) break; }
console.log('end', p.map((x) => x.toFixed(1)), 'maxY', maxY.toFixed(1), 'wall stops', jumps);
