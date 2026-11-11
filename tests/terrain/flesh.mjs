// node tests/terrain/flesh.mjs : the flesh field (shared/terrain.js fleshField / fieldTerrain): the same everywhere,
// seamless between chunks, level where it's told to be, walkable and hittable at a base height that isn't 0
import { fleshField, fieldTerrain, attachTerrain } from '../../shared/terrain.js';
import { movePlayer, raycast } from '../../shared/physics.js';
const out = [], ok = (n, v, d = '') => out.push(`${v ? 'PASS' : 'FAIL'} ${n} ${d}`);
const O = { seed: 7, flat: [[-20, -20, 20, 10]], cords: [{ pts: [[30, -40], [50, -20], [80, -25]], w: 1.6, h: 0.6 }] };
const f = fleshField(O), g = fleshField(O);
let same = true, mx = -9, mn = 9, veinN = 0, growN = 0, poreN = 0, n = 0, slope = 0;
for (let x = -100; x <= 100; x += 0.5) for (let z = -100; z <= 100; z += 0.5) { const h = f(x, z); if (h !== g(x, z)) same = false; mx = Math.max(mx, h); mn = Math.min(mn, h); const p = f.parts(x, z); n++; if (p.vein > 0.05) veinN++; if (p.growth > 0.3) growN++; if (p.growth < -0.1) poreN++; slope = Math.max(slope, Math.abs(h - f(x + 0.5, z)) / 0.5); }
ok('same answer twice', same);
ok('has range', mx > 1.5 && mn < -0.5, `lo ${mn.toFixed(2)} hi ${mx.toFixed(2)}`);
ok('veins, growths and pores all show up', veinN / n > 0.03 && veinN / n < 0.3 && growN / n > 0.02 && poreN > 0, `veins ${(veinN / n * 100).toFixed(1)}% growths ${(growN / n * 100).toFixed(1)}% pores ${(poreN / n * 100).toFixed(2)}% steepest ${slope.toFixed(2)}`);
let flat = 0; for (let x = -20; x <= 20; x++) for (let z = -20; z <= 10; z++) flat = Math.max(flat, Math.abs(f(x, z)));
ok('the flat rectangle is level', flat === 0, `max ${flat}`);
ok('eases in from its edge', Math.abs(f(21, 0)) < 0.45 && Math.abs(f(20.5, 0)) < 0.2, `${f(20.5, 0).toFixed(2)} ${f(21, 0).toFixed(2)}`);
ok('a drawn cord is raised', f.parts(40, -30).vein > 0.5, f.parts(40, -30).vein.toFixed(2));
// two chunks side by side: their shared edge is the same heights
const A = fieldTerrain(f, { region: [0, 0, 32, 32], y: 40, mat: 'flesh' }), B = fieldTerrain(f, { region: [32, 0, 64, 32], y: 40, mat: 'flesh' });
let seam = 0; for (let j = 0; j <= 32; j++) seam = Math.max(seam, Math.abs(A.H[32 * 33 + j] - B.H[j]));
ok('chunks meet at the seam', seam === 0, `max gap ${seam}`);
// walk across one at y = 40 with the shared physics, and shoot down onto it
const T = fieldTerrain(f, { region: [-100, -100, 100, 100], y: 40, mat: 'flesh' }), boxes = []; attachTerrain(boxes, T);
const pos = [-90, T.at(-90, 55), 55], vel = [0, 0, 0]; let on = true, off = 0, air = 0, ticks = 0;
for (let t = 0; t < 60 * 20; t++) { vel[0] = 8; vel[2] = 0.6; vel[1] -= 26 / 60; const r = movePlayer(pos, vel, 1 / 60, boxes, on); on = !!r.ground && vel[1] <= 0.01; const gg = T.at(pos[0], pos[2]); if (gg == null) break; ticks++; if (!on) air++; else if (Math.abs(pos[1] - gg) > 0.01) off++; }
ok('walks on it at y 40', ticks > 1000 && off === 0 && air / ticks < 0.08, `ticks ${ticks} air ${air} off ${off} y ${pos[1].toFixed(2)}`);
const hit = raycast([33, 60, 41], [0, -1, 0], 40, boxes);
ok('a ray down lands on it', !!hit && Math.abs(hit.point[1] - T.at(33, 41)) < 0.01 && hit.box.mat === 'flesh', hit && hit.point[1].toFixed(2));
console.log(out.join('\n')); process.exit(out.some((l) => l.startsWith('FAIL')) ? 1 : 0);
