import { mk } from './h.mjs';
const { room, human } = mk('ffa');
room.cfg.map = 'crate';
const base = room.map.boxes.filter((b) => b.min[1] < 0); // keep the floor
const wall = [{ min: [-20, 0, -0.2], max: [-0.75, 4, 0.2] }, { min: [0.75, 0, -0.2], max: [20, 4, 0.2] }];
const boxes = [...base, ...wall];
Object.defineProperty(room, 'boxes', { get: () => boxes });
const A = human('A'), B = human('B');
for (const v of [10, 20, 30, 40]) {
  let lands = 0, tries = 0;
  for (let ph = 0; ph < 30; ph++) {
    const n = Date.now();
    // B ran along x at z=10 from x=-15 at v m/s, snapshots every 33 ms, the last one 'now'; it's now at x=+15-ish
    const tr = []; const T = 400;
    const t0 = n - T + ph * 1.1;
    for (let t = t0; t <= n; t += 33) tr.push([t, -v * 0.2 + (t - t0) / 1000 * v, 0, 10]);
    B.strail = tr; B.pos = [tr.at(-1)[1], 0, 10]; B.alive = true; B.vel = [v, 0, 0];
    A.pos = [0, 0, -10]; A.vel = [0, 0, 0]; A.alive = true; A.strail = [[n - 500, 0, 0, -10]]; A.w = 'ar'; A.hon = null;
    // only count if the hit is within the 650 ms window (else history can't cover regardless)
    if (T > 600) continue;
    tries++;
    if (room.honHit(A, { t: 'hit', to: B.id, w: 'ar', d: [0, 0, 1], n: 1, h: 0 })) lands++;
  }
  console.log(`target crossing a 1.5 m gap at ${v} m/s (shooter 10 m back, target 10 m past the wall), hit sent right after: lands ${lands}/${tries}`);
}
process.exit(0);
