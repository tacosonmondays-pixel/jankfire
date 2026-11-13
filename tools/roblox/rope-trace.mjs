// the web game's own grapple (shared/hookphys.js classicRopeStep) run on a few set swings, in metres: the Luau port is
// checked against these (roblox/tests/run.luau). writes roblox/tests/rope-trace.json
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { classicRopeStep, classicRopeJump } from '../../shared/hookphys.js';
const HERE = path.dirname(fileURLToPath(import.meta.url));
const grav = 26, dt = 1 / 120;
const cases = [
  { name: 'hang from a ledge above', p: [0, 0, 0], v: [0, 0, 0], a: [12, 15, 4], steps: 360 },
  { name: 'swing in from a run', p: [0, 1, 0], v: [14, 0, 0], a: [20, 12, 30], steps: 480 },
  { name: 'falling, hook far below', p: [0, 30, 0], v: [3, -20, 2], a: [-40, 5, 60], steps: 600 },
];
const out = cases.map((c) => {
  const p = [...c.p], v = [...c.v], h = {}, pts = [];
  for (let i = 0; i < c.steps; i++) {
    v[1] -= grav * dt;
    classicRopeStep(h, c.a, p, v, dt, grav);
    for (let k = 0; k < 3; k++) p[k] += v[k] * dt;
    if (i % 30 === 29) pts.push([...p, ...v]);
  }
  const j = [...v]; classicRopeJump(j);
  return { ...c, pts, jump: j };
});
fs.writeFileSync(path.join(HERE, '..', '..', 'roblox', 'tests', 'rope-trace.json'), JSON.stringify({ grav, dt, cases: out }));
console.log('rope traces:', out.length);
