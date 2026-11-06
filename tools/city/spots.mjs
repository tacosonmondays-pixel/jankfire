// node tools/city/spots.mjs: // every story spot (spawn, terminal, terminal + 1.6 m out, locker, clinic) is standing room: a body there isn't inside a box
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import { worldOf } from '../../shared/story/worlds.js';
import { playerOverlap } from '../../shared/physics.js';
const W = new ChunkWorld([]); for (const [cx, cz] of [[-4, 2], [-3, 2], [-4, 3], [-3, 3]]) W.set(cx + ':' + cz, chunkBoxes(packChunk(buildChunk('slice', cx, cz)))); W.sync();
const S = worldOf('story_slice');
const spots = { spawn: S.spawn, terminal: S.terminal.p, terminalOut: [S.terminal.p[0], S.terminal.p[1], S.terminal.p[2] + 1.6], locker: S.locker.p, clinic: S.clinic.p };
for (const [k, p] of Object.entries(spots)) { const q = [p[0], p[1] + 0.05, p[2]], v = [0, -1, 0]; const b = playerOverlap(q, W.boxes); W.movePlayer(q, v, 0.5, true); console.log(k, p.join(','), b ? 'INSIDE ' + JSON.stringify([b.min, b.max]) : 'clear', 'lands y', q[1].toFixed(2)); }
