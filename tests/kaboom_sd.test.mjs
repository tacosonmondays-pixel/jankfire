// node --test tests/kaboom_sd.test.mjs : Islands S&D's Mount Kaboom (shared/map.js kaboom(..., KABOOM_SD): a sloped cone of
// shaped ground, no stairs). you walk straight up it at a run from any side and down again, a bot steering by the walk
// graph gets up from every side, the throat's lava is where the pit rules expect it, the cone stays under the map's
// ceiling, and the ways from the spawns to the sites are what they were (nobody goes over the top to get there)
import test from 'node:test';
import assert from 'node:assert/strict';
import { MAPS } from '../shared/map.js';
import { navSteer, navLocate, navPath } from '../shared/nav.js';
import { movePlayer } from '../shared/physics.js';

const m = MAPS.islands_sd, C = [0, -13], T = m.boxes.terrain;
const sim = (pos, vel, ground) => { vel[1] -= 26 / 30; return !!movePlayer(pos, vel, 1 / 30, m.boxes, ground).ground; };
const run = (from, to, speed = 7, max = 12) => {
  const pos = from.slice(), vel = [0, 0, 0]; let ground = true, t = 0;
  for (; t < max; t += 1 / 30) {
    const dx = to[0] - pos[0], dz = to[2] - pos[2], d = Math.hypot(dx, dz);
    if (d < 0.4) break;
    vel[0] = dx / d * speed; vel[2] = dz / d * speed; ground = sim(pos, vel, ground);
  }
  return { pos, t };
};

test('S&D volcano: straight up from the foot to the summit at a run, from (almost) every side, at walking time', () => {
  const rocks = m.boxes.filter((b) => b.mat === 'basalt' && b.max[1] - b.min[1] < 3 && b.min[2] > -30 && b.max[2] < 4 && Math.hypot((b.min[0] + b.max[0]) / 2 - C[0], (b.min[2] + b.max[2]) / 2 - C[1]) > 6);
  let stuck = 0; const times = [], flat = run([60, 0.05, 30], [72.4, 0.05, 30]).t; // (the same 12.4 m on flat sand)
  for (let k = 0; k < 72; k++) {
    const a = k * Math.PI / 36, foot = [C[0] + Math.cos(a) * 16, 0, C[1] + Math.sin(a) * 16], top = [C[0] + Math.cos(a) * 3.6, 9, C[1] + Math.sin(a) * 3.6];
    foot[1] = (T.at(foot[0], foot[2]) ?? 0) + 0.05;
    const { pos, t } = run(foot, top);
    if (pos[1] > 8.85 && Math.hypot(pos[0] - top[0], pos[2] - top[2]) < 0.6) { times.push(t); assert.ok(t < flat * 1.7, `up from ${k * 5} deg took ${t.toFixed(2)} s (flat ${flat.toFixed(2)})`); continue; }
    stuck++; // (only ever against a boulder: cover on the way up, you go round it)
    assert.ok(rocks.some((b) => pos[0] > b.min[0] - 0.7 && pos[0] < b.max[0] + 0.7 && pos[2] > b.min[2] - 0.7 && pos[2] < b.max[2] + 0.7), `up from ${k * 5} deg: stopped at ${pos.map((v) => v.toFixed(1))}, no boulder there`);
  }
  assert.ok(stuck <= 6, `${stuck} of 72 ways straight up blocked`);
  times.sort((a, b) => a - b); assert.ok(times[times.length >> 1] < flat * 1.1, `the usual climb ${times[times.length >> 1].toFixed(2)} s, flat ${flat.toFixed(2)} s`); // (up the slope at the same run as on the beach)
});
test('S&D volcano: down again from the summit to the beach on every side, never into the throat', () => {
  for (let k = 0; k < 24; k++) {
    const a = k * Math.PI / 12, top = [C[0] + Math.cos(a) * 4.5, 9.05, C[1] + Math.sin(a) * 4.5], foot = [C[0] + Math.cos(a) * 17, 0, C[1] + Math.sin(a) * 17];
    const { pos } = run(top, foot); const vel = [0, 0, 0]; for (let i = 0; i < 40; i++) sim(pos, vel, false);
    assert.ok(pos[1] > -0.8 && pos[1] < 0.6 && Math.hypot(pos[0] - C[0], pos[2] - C[1]) > 12, `down to ${Math.round(k * 15)} deg: ended at ${pos.map((v) => v.toFixed(1))}`);
  }
});
test('S&D volcano: a bot steering by the walk graph gets up from every side and down again', () => {
  const bot = (from, goal) => {
    const pos = from.slice(), vel = [0, 0, 0], st = {}; let ground = true;
    for (let t = 0; t < 25; t += 1 / 30) {
      const s = navSteer(m.graph, st, pos, goal, t * 1000), l = Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) || 1;
      const [dx, dz] = s ? s : [(goal[0] - pos[0]) / l, (goal[2] - pos[2]) / l];
      if (s && s[2] && ground) vel[1] = 8;
      vel[0] = dx * 7; vel[2] = dz * 7; ground = sim(pos, vel, ground);
      if (Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) < 1 && Math.abs(goal[1] - pos[1]) < 0.7) return true;
    }
    return pos.map((v) => +v.toFixed(1));
  };
  const top = [[3.5, 9, -13], [-3.5, 9, -13], [0, 9, -8.5], [0, 9, -17.5]];
  for (const [from, goal] of [[[0, 0.1, 6], top[2]], [[0, 0.1, -32], top[3]], [[-24, 0.1, -13], top[1]], [[24, 0.1, -13], top[0]], [[-17, 0.1, 3], top[1]], [[17, 0.1, -28], top[0]],
    [top[2], [0, 0.1, 6]], [top[0], [24, 0.1, -13]], [top[1], [-20, 0.1, -26]]]) assert.equal(bot(from, goal), true, from + ' -> ' + goal);
});
test('S&D volcano: the throat (lava, the pit) where it was, the cone under the ceiling', () => {
  assert.deepEqual(m.pits[0].box, [-2, -15, 2, -11]);
  assert.ok(m.deco.some((b) => b.mat === 'lava' && b.min[0] === -2 && b.min[2] === -15), 'the lava down the throat');
  assert.equal(T.at(0, -13), null, 'no ground over the throat');
  let hi = 0; for (let x = -16; x <= 16; x += 0.5) for (let z = -30; z <= 4; z += 0.5) { const h = T.at(x, z); if (h != null) hi = Math.max(hi, h); }
  assert.ok(hi < m.ceiling - 0.15 && hi > 8.9, `the summit at ${hi.toFixed(2)} under the ceiling ${m.ceiling}`);
});
test('S&D: the ways from both spawns to both sites are what they were (within 10%), the walk graph whole', () => {
  const P = { att: [0, 0.1, 46], def: [0, 0.1, -62], A: [49, 0, -67], B: [-48, 0, -65] }, was = { 'att>A': 141.7, 'att>B': 133.8, 'def>A': 55.7, 'def>B': 49.2 };
  for (const [k, L0] of Object.entries(was)) {
    const [a, b] = k.split('>'), p = navPath(m.graph, navLocate(m.graph, P[a]), navLocate(m.graph, P[b])); assert.ok(p, k);
    let L = 0; for (let i = 1; i < p.length; i++) { const u = m.graph.nodes[p[i - 1]], v = m.graph.nodes[p[i]]; L += Math.hypot(v[0] - u[0], v[2] - u[2]); }
    assert.ok(Math.abs(L - L0) / L0 < 0.1, `${k}: ${L.toFixed(1)} m, was ${L0}`);
  }
  assert.deepEqual(m.graph.bad, []);
});
