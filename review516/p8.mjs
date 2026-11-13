// static honest hitscan: client ray from its eye (stand 1.6 / crouch 1.05 / slide 0.95) to a random spot on the target's
// (distance-scaled) hitboxes is clear of BOXES -> would the server agree? nobody moving, positions rounded like snapshots
import { mk, raycast } from './h.mjs';
const { playerBoxes } = await import((process.env.ROOT || process.cwd()) + '/shared/physics.js');
const { room, human } = mk('ffa');
const A = human('A'), B = human('B');
const r2 = (x) => Math.round(x * 100) / 100;
for (const map of (process.env.MAPS || 'crate,warehouse,suburb,desert,islands,bazaar,backrooms,deadmall,jankburg').split(',')) {
  room.cfg.map = map; const bx = room.boxes;
  const ground = (x, z) => { const h = raycast([x, 200, z], [0, -1, 0], 400, bx); return h ? h.point[1] + 0.0 : null; };
  let tot = 0, bad = 0; const ex = [], byEye = {};
  const S = map === 'crate' ? 14 : map === 'jankburg' ? 250 : 120;
  for (let i = 0; i < 60000 && tot < 600; i++) {
    const ax = (Math.random() - 0.5) * 2 * S, az = (Math.random() - 0.5) * 2 * S, bxp = ax + (Math.random() - 0.5) * 100, bzp = az + (Math.random() - 0.5) * 100;
    const ay = ground(ax, az), by = ground(bxp, bzp); if (ay == null || by == null) continue;
    const A0 = [ax, ay + 0.002, az], B0 = [bxp, by + 0.003, bzp];
    const eh = [1.6, 1.05, 0.95][i % 3], e = [A0[0], A0[1] + eh, A0[2]];
    // must not be inside a box at the eye
    const dist = Math.hypot(B0[0] - A0[0], B0[1] - A0[1], B0[2] - A0[2]); if (dist < 3) continue;
    const k = 1 + Math.max(0, Math.min(1, (dist - 25) / 60)) * 0.8;
    const hb = playerBoxes(B0)[Math.random() < 0.3 ? 1 : 0];
    const pt = [0, 1, 2].map((j) => { const lo = B0[j] + (hb.min[j] - B0[j]) * k, hi = B0[j] + (hb.max[j] - B0[j]) * k; return lo + Math.random() * (hi - lo); });
    const d = pt.map((v, j) => v - e[j]), l = Math.hypot(...d);
    if (raycast(e, d.map((x) => x / l), l - 0.01, bx)) continue; // client ray blocked: not an honest hit
    // also the client's own body would not be inside geometry: the eye must be in the open (cheap check: up 0.3 clear)
    if (raycast([A0[0], A0[1] + 0.3, A0[2]], [0, 1, 0], eh - 0.3, bx)) continue;
    A.pos = A0.map(r2); B.pos = B0.map(r2);
    for (const p of [A, B]) { p.vel = [0, 0, 0]; p.alive = true; p.strail = null; p.trail = null; }
    A.w = 'ar'; A.hon = null;
    tot++;
    if (!room.honHit(A, { t: 'hit', to: B.id, w: 'ar', d: d.map((x) => r2(x / l)), n: 1, h: 0 })) { bad++; byEye[eh] = (byEye[eh] || 0) + 1; if (ex.length < 3) ex.push({ A: A0.map((x) => +x.toFixed(2)), B: B0.map((x) => +x.toFixed(2)), eh, pt: pt.map((x) => +x.toFixed(2)) }); }
  }
  console.log(`${map}: ${bad}/${tot} honest static hits refused ${JSON.stringify(byEye)}`, ex.length ? JSON.stringify(ex) : '');
}
process.exit(0);
