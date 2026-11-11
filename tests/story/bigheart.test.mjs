// node tests/story/bigheart.test.mjs : the Big Heart in the Gut (shared/city/bigheart.js). Its collision module matches
// the model's json, the place and its marks are in the world, and the rib stair is really climbable: a player-sized
// box is walked with the game's own physics (shared/physics.js: 0.6 m step, no jumping) from the listening spot up
// every tread, across the three missing ones, to the top under the apex, at a walk, a run and a sprint.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { movePlayer, resetGrid, playerOverlap } from '../../shared/physics.js';
import { BIG_HEART as H, heartAt } from '../../shared/city/bigheart.js';
import { PLACES, SLICE } from '../../shared/city/slice.js';
import { LOCATIONS } from '../../shared/story/content/world.js';

// 1. the boxes are the model's (the tool re-derives them from the json and compares)
execFileSync(process.execPath, [new URL('../../tools/city/heart_boxes.mjs', import.meta.url).pathname, '--check'], { stdio: 'pipe' });
// 2. the place: in PLACES, in the writer's LOCATIONS, in the Gut, with its marks in the chunk it stands in
assert.ok(PLACES[H.id] && Object.hasOwn(LOCATIONS, H.id), 'gut:big_heart is a place and a location');
const g = SLICE.gut.rect; assert.ok(H.x - H.reach > g[0] && H.x + H.reach < g[2] && H.z - H.reach > g[1] && H.z + H.reach < g[3], 'it stands inside the Gut');
const boxes = [], marks = [];
for (let cx = -3; cx <= -1; cx++) for (let cz = -3; cz <= -1; cz++) { const p = packChunk(buildChunk('slice', cx, cz)); boxes.push(...chunkBoxes(p)); marks.push(...p.marks); }
resetGrid(boxes);
assert.equal(marks.filter((m) => m.id === H.id).length, 1); assert.equal(marks.filter((m) => m.id === 'gut.big_heart_top').length, 1);
// 3. you can stand where the marks say: at the listening spot, at the top of the stair, with the heart over your head
const spot = heartAt(H.markers.listening_spot), top = heartAt(H.markers.stair_top);
assert.ok(!playerOverlap([spot[0], spot[1] + 0.02, spot[2]], boxes), 'the listening spot is clear');
assert.ok(!playerOverlap([top[0], top[1] + 0.02, top[2]], boxes), 'there is headroom at the top of the stair');
// 4. the climb. waypoints: each tread that exists, a step toward its outer end (where you'd walk)
const axisAt = (y) => { const A = H.axis, i = Math.max(0, Math.min(A.length - 2, Math.floor(y / 1.5))), f = Math.max(0, Math.min(1, (y - A[i][0]) / 1.5)); return [A[i][1] + (A[i + 1][1] - A[i][1]) * f, A[i][2] + (A[i + 1][2] - A[i][2]) * f]; };
const way = [heartAt(H.markers.stair_foot), ...H.treads.filter((t) => t[3] !== 2).map((t) => { const [ax, az] = axisAt(t[0]), dx = t[1] - ax, dz = t[2] - az, d = Math.hypot(dx, dz); return [H.x + t[1] + dx / d * 0.3, H.y + t[0], H.z + t[2] + dz / d * 0.3]; })];
function climb(speed) {
  const pos = [spot[0], spot[1] + 0.05, spot[2]], vel = [0, 0, 0], dt = 1 / 60;
  let ground = false, wi = 0, stuck = 0, best = 1e9, t = 0;
  while (wi < way.length && t < 120 && stuck < 2) {
    const w = way[wi], dx = w[0] - pos[0], dz = w[2] - pos[2], d = Math.hypot(dx, dz);
    if ((d < 0.3 && pos[1] > w[1] - 0.3) || (d < 1 && ground && pos[1] > w[1] - 0.03)) { wi++; stuck = 0; best = 1e9; continue; }
    vel[0] = dx / (d || 1) * speed; vel[2] = dz / (d || 1) * speed; vel[1] -= 26 * dt; // (player.js C.grav; never a jump)
    if (d < best - 0.01) { best = d; stuck = 0; } else stuck += dt;
    const r = movePlayer(pos, vel, dt, boxes, ground); ground = !!r.ground && vel[1] <= 0.01; t += dt;
  }
  return { wi, y: pos[1] - H.y, t };
}
for (const v of [3, 5, 10, 14.5]) { const c = climb(v); assert.ok(c.wi === way.length && Math.abs(c.y - H.markers.stair_top[1]) < 0.05, `the stair is walkable at ${v} m/s (stopped at tread ${c.wi - 1} of ${way.length - 1}, ${c.y.toFixed(2)} m up)`); }
const gaps = H.treads.map((t, k) => [k, t[3]]).filter((q) => q[1]);
console.log(`big heart ok: ${Object.values(H.boxes).reduce((n, l) => n + l.length, 0)} boxes, ${way.length - 1} treads walked to ${H.markers.stair_top[1]} m with no jump; gone: ${gaps.filter((q) => q[1] === 2).map((q) => q[0]).join(', ')}; stubs: ${gaps.filter((q) => q[1] === 1).map((q) => q[0]).join(', ')}`);
