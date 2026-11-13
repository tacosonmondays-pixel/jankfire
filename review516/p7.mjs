// chicken strike / duck aim points as a real client makes them (eye at the unrounded pos, crouch eye 1.05 too), checked by honAim
import { mk, raycast } from './h.mjs';
const { room, human } = mk('ffa');
const A = human('A');
const r2 = (x) => Math.round(x * 100) / 100;
for (const map of ['desert', 'islands', 'forest', 'suburb', 'jankburg']) {
  room.cfg.map = map; const bx = room.boxes;
  const ground = (x, z) => { const h = raycast([x, 300, z], [0, -1, 0], 600, bx); return h ? h.point[1] : null; };
  let tot = 0, bad = 0; const ex = [];
  for (let i = 0; i < 4000 && tot < 400; i++) {
    const x = (Math.random() - 0.5) * 300, z = (Math.random() - 0.5) * 300, gy = ground(x, z); if (gy == null || gy > 60) continue;
    const pos = [x + 0.003, gy + 0.0037, z - 0.004];
    for (const eh of [1.6, 1.05]) {
      const e = [pos[0], pos[1] + eh, pos[2]], yaw = Math.random() * 6.28, pit = -Math.random() * 0.08;
      const d = [-Math.sin(yaw) * Math.cos(pit), Math.sin(pit), -Math.cos(yaw) * Math.cos(pit)];
      const h = raycast(e, d, 300, bx); if (!h || h.t < 20) continue;
      const at = h.point.map(r2);
      A.pos = pos.map(r2); A.vel = [0, 0, 0]; A.alive = true; A.strail = null; A.trail = null;
      tot++; if (!room.honAim(A, at)) { bad++; if (ex.length < 2) ex.push({ eh, dist: h.t.toFixed(0), pit: pit.toFixed(3) }); }
    }
  }
  console.log(`${map}: ${bad}/${tot} honest aim points refused`, JSON.stringify(ex));
}
process.exit(0);
