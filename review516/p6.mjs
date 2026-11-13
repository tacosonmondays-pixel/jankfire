import { mk, raycast } from './h.mjs';
const { room, human } = mk('ffa');
room.cfg.map = 'crate';
const A = human('A'), B = human('B');
const n = Date.now();
A.pos = [0, 0, -8]; B.pos = [0, 0, 6];
for (const p of [A, B]) { p.vel = [0, 0, 0]; p.alive = true; p.strail = [[n - 900, ...p.pos], [n - 5, ...p.pos]]; }
const tryHit = (w, d) => { A.w = w; A.hon = null; return room.honHit(A, { t: 'hit', to: B.id, w, d, n: 1, h: 0 }); };
console.log('B fully behind the block: AR straight', tryHit('ar', [0, 0, 1]));
console.log('revolver, claimed straight', tryHit('revolver', [0, 0, 1]));
// the last leg comes "up off the floor" from a spot beside the block that A can see: d points from the floor spot (6.5,0,4) to B's chest
const from = [6.5, 0, 4], to = [0, 1.1, 6], d = to.map((v, i) => v - from[i]), l = Math.hypot(...d);
console.log('revolver, claimed floor bounce from a visible spot (a real client could not: its first leg would have to come from A down to that spot and reflect to B)', tryHit('revolver', d.map((x) => Math.round(x / l * 100) / 100)));
// would a real bounce do this? reflect the claimed last leg off the floor: the incoming leg goes (-dx, -dy, -dz) mirrored -> its source direction
const inc = [d[0] / l, -d[1] / l, d[2] / l]; // incoming direction before the floor bounce
const back = [-inc[0], -inc[1], -inc[2]]; // from the floor spot back toward the shooter
const t = (1.6 - 0) / back[1]; console.log('the real first leg would start at', [from[0] + back[0] * t, 1.6, from[2] + back[2] * t].map((x) => x.toFixed(1)), 'vs A eye at', [0, 1.6, -8]);
process.exit(0);
