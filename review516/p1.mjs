import { mk } from './h.mjs';
const { room, human } = mk('ffa');
room.cfg.map = 'crate';
const A = human('A'), B = human('B');
const n = Date.now();
const put = (p, pos, trail) => { p.pos = pos.slice(); p.vel = [0, 0, 0]; p.alive = true; p.strail = trail || [[n - 900, ...pos], [n - 10, ...pos]]; };
const hit = (w = 'ar', d = [0, 0, 1]) => { A.w = w; A.hon = null; return room.honHit(A, { t: 'hit', to: B.id, w, d, n: 1, h: 0 }); };
// a) soap bubble edge showing past the block (body hidden)
put(A, [0, 0, -8]); put(B, [4.6, 0, 4]); B.trap = { until: n + 5000 };
console.log('a) bubble edge only visible (x=4.6): honHit =', hit());
B.trap = null;
// b) body sliver: body edge at 5.12..; visible threshold x>5.45 at crossing
for (const x of [4.9, 4.95, 5.0, 5.05]) { put(B, [x, 0, 4]); console.log(`b) target x=${x} (body edge ${(x + 0.52).toFixed(2)} vs visible > 5.45): honHit =`, hit()); }
// c) fast target crossing a gap seen only between samples: moving at 30 m/s along x behind block, samples every 33 ms
{
  const tr = []; // from x=-12 to x=12 over 0.8 s at z=4 ... only visible when |x|>5.45, choose path visible only in mid window
  // instead: a narrow gap. use two crate pillars? emulate with sample positions skipping the exposed area
  for (let i = 0; i <= 24; i++) tr.push([n - 800 + i * 33, 6.2 - 0 + 0, 0, 4]);
}
process.exit(0);
