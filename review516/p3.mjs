import { mk, raycast } from './h.mjs';
const { room, human } = mk('ffa');
room.cfg.map = 'crate';
const base = room.map.boxes.filter((b) => b.min[1] < 0);
const boxes = [...base, { min: [-20, 0, -0.2], max: [20, 4, 0.2] }];
Object.defineProperty(room, 'boxes', { get: () => boxes });
const A = human('A'), B = human('B');
const n = Date.now();
B.pos = [0, 0, 6]; B.alive = true; B.vel = [0, 0, 0]; B.strail = [[n - 700, 0, 0, 6], [n - 5, 0, 0, 6]];
// A rocket-jumped 100 ms ago from y=0 at 25 m/s straight up; last snapshot (now) at y=2.3 (eye 3.9, just under the wall top 4)
// its client fires 30 ms later from y=3.05 (eye 4.65): can it see B's head over the wall from z=-1?
const eyeC = [0, 3.05 + 1.6, -1], head = [0, 2.1, 6];
const d = [head[0] - eyeC[0], head[1] - eyeC[1], head[2] - eyeC[2]], l = Math.hypot(...d);
console.log('client view clear from its fire-time eye:', !raycast(eyeC, d.map((x) => x / l), l, boxes));
for (const [label, tr] of [
  ['trail: 600 ms of standing then 100 ms rising (rocket jump just now)', [[n - 600, 0, 0, -1], [n - 300, 0, 0, -1], [n - 100, 0, 0, -1], [n - 50, 0, 1.2, -1], [n, 0, 2.3, -1]]],
  ['trail: steady 25 m/s for 600 ms (impossible here, upper bound)', [[n - 600, 0, 2.3 - 15, -1], [n, 0, 2.3, -1]]],
]) {
  A.pos = [0, 2.3, -1]; A.vel = [0, 25, 0]; A.alive = true; A.trail = tr; A.strail = tr.map((x) => x.slice()); A.w = 'ar'; A.hon = null;
  console.log(label, '| speedOf =', room.speedOf(A).toFixed(1), '| honHit =', room.honHit(A, { t: 'hit', to: B.id, w: 'ar', d: [0, -0.3, 0.95], n: 1, h: 1 }));
}
process.exit(0);
