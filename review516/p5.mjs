// CPU of a hit flood: 300 blocked hits in one second through room.handle (what one connection's budget allows)
import { mk, raycast } from './h.mjs';
const { room, human } = mk('ffa');
const A = human('A'), B = human('B');
for (const map of (process.env.MAPS || 'islands,suburb,desert').split(',')) {
  room.cfg.map = map;
  const bx = room.boxes;
  const ground = (x, z) => { const h = raycast([x, 300, z], [0, -1, 0], 600, bx); return h ? h.point[1] + 0.05 : null; };
  // find a blocked pair ~60 m apart
  let found = null;
  for (let i = 0; i < 2000 && !found; i++) {
    const ax = (Math.random() - 0.5) * 200, az = (Math.random() - 0.5) * 200, bxp = ax + (Math.random() - 0.5) * 120, bzp = az + (Math.random() - 0.5) * 120;
    const ay = ground(ax, az), by = ground(bxp, bzp); if (ay == null || by == null || ay > 40 || by > 40) continue;
    const e = [ax, ay + 1.6, az], c = [bxp, by + 1.1, bzp], d = c.map((v, k) => v - e[k]), l = Math.hypot(...d);
    if (l > 30 && raycast(e, d.map((x) => x / l), l, bx)) { if (!room.honHit) { found = [[ax, ay, az], [bxp, by, bzp]]; continue; } A.pos=[ax,ay,az];A.vel=[0,0,0];A.alive=true;A.w='ar';A.hon=null;A.strail=null;B.pos=[bxp,by,bzp];B.alive=true;B.vel=[0,0,0];B.strail=null; if (!room.honHit(A,{t:'hit',to:B.id,w:'ar',d:[1,0,0],n:1,h:0})) found = [[ax, ay, az], [bxp, by, bzp]]; }
  }
  if (!found) { console.log(map, 'no pair'); continue; }
  const n = Date.now();
  A.pos = found[0]; A.vel = [0, 0, 0]; A.alive = true; A.w = 'ar'; A.spawnT = n; A.hon = null; A.strail = []; for (let t = 600; t >= 0; t -= 33) A.strail.push([n - t, ...found[0]]);
  B.pos = found[1]; B.vel = [0, 0, 0]; B.alive = true; B.spawnT = n - 5000; B.strail = []; for (let t = 1000; t >= 0; t -= 33) B.strail.push([n - t, B.pos[0], B.pos[1], B.pos[2]]);
  const t0 = process.hrtime.bigint();
  for (let i = 0; i < 300; i++) room.handle(A, { t: 'hit', to: B.id, w: 'ar', d: [1, 0, 0], n: 1, h: 0 });
  const ms = Number(process.hrtime.bigint() - t0) / 1e6;
  console.log(`${map}: 300 blocked AR hits through handle: ${ms.toFixed(0)} ms of CPU (B hp ${B.hp})`);
}
process.exit(0);
