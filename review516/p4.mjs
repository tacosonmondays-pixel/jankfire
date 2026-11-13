import { mk, raycast } from './h.mjs';
const { MAPS } = await import((process.env.ROOT || process.cwd()) + '/shared/map.js');
const { room, human } = mk('ffa');
const A = human('A'), B = human('B');
for (const map of ['jankburg', 'desert', 'forest', 'suburb', 'islands', 'bazaar']) {
  if (!MAPS[map]) { console.log('no map', map); continue; }
  room.cfg.map = map;
  const bx = room.boxes; let lo = [1e9, 1e9], hi = [-1e9, -1e9];
  for (const b of bx) { if (b.max[0] - b.min[0] > 200) continue; lo = [Math.min(lo[0], b.min[0]), Math.min(lo[1], b.min[2])]; hi = [Math.max(hi[0], b.max[0]), Math.max(hi[1], b.max[2])]; }
  const ground = (x, z) => { const h = raycast([x, 300, z], [0, -1, 0], 600, bx); return h ? h.point[1] + 0.05 : null; };
  let worst = 0, tot = 0, cnt = 0, fails = 0, cw = 0; raycast([0,50,0],[1,0,0],10,bx); raycast([0,50,0],[0,-1,0],100,bx);
  const rnd = (a, b) => a + Math.random() * (b - a);
  for (let i = 0; i < 400 && cnt < 60; i++) {
    const ax = rnd(lo[0], hi[0]), az = rnd(lo[1], hi[1]), bxp = ax + rnd(-80, 80), bzp = az + rnd(-80, 80);
    const ay = ground(ax, az), by = ground(bxp, bzp); if (ay == null || by == null) continue;
    const n = Date.now();
    A.pos = [ax, ay, az]; A.vel = [6, 0, 0]; A.alive = true; A.trail = [[n - 600, ax - 3, ay, az]]; A.strail = []; for (let t = 600; t >= 0; t -= 33) A.strail.push([n - t, ax - t / 100, ay, az]);
    B.pos = [bxp, by, bzp]; B.vel = [6, 0, 0]; B.alive = true; B.strail = []; for (let t = 1000; t >= 0; t -= 33) B.strail.push([n - t, bxp - t / 100, by, bzp]);
    for (const w of ['ar', 'revolver']) {
      A.w = w; A.hon = null; const t0 = process.hrtime.bigint();
      const ok = room.honHit(A, { t: 'hit', to: B.id, w, d: [0.6, -0.1, 0.79], n: 1, h: 0 });
      const ms = Number(process.hrtime.bigint() - t0) / 1e6;
      if (!ok) { fails++; worst = Math.max(worst, ms); tot += ms; cnt++; A.hon = { prevW: null, swapT: 0, pend: [], looks: [], lo: {}, life: A.spawnT, fails: Array(8).fill(Date.now()) }; const t1 = process.hrtime.bigint(); room.honHit(A, { t: 'hit', to: B.id, w, d: [0.6, -0.1, 0.79], n: 1, h: 0 }); cw = Math.max(cw, Number(process.hrtime.bigint() - t1) / 1e6); }
    }
  }
  console.log(`${map}: ${bx.length} boxes, ${cnt} refused full checks, avg ${(tot / cnt).toFixed(2)} ms, worst ${worst.toFixed(2)} ms, cheap worst ${cw.toFixed(2)} ms`);
}
process.exit(0);
