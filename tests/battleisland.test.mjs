// node --test tests/battleisland.test.mjs : Battle Island's ground (shared/battleisland.js). the island builds the same every
// time; the mode's fields are there (POIs, drop pads, energy cells, the finale); every drop pad is dry, level and open to
// the sky; a bot steering by the walk graph gets from the harbour to every POI's pad; walking out off the beach into deep
// water is the sea kill, wading the lagoon and the river isn't; the map stays out of the map lists until the mode lands
import test from 'node:test';
import assert from 'node:assert/strict';
import { MAPS, MAP_ORDER } from '../shared/map.js';
import '../shared/royale.js';
import { mapsFor } from '../shared/modes.js';
import { navSteer } from '../shared/nav.js';
import { movePlayer, raycast } from '../shared/physics.js';
import { islandH, PLAN, SEA, WADE, KILL_Y, GRID } from '../shared/battleisland.js';

const m = MAPS.battleisland, T = m.boxes.terrain;
const sim = (pos, vel, ground) => { vel[1] -= 26 / 30; return !!movePlayer(pos, vel, 1 / 30, m.boxes, ground).ground; };
const ground = (x, z) => T.at(x, z);

test('Battle Island: built, with the mode\'s fields, and hidden from the map lists', () => {
  assert.ok(m && T, 'the map and its shaped ground');
  assert.equal(m.royale.pois.length, 9);
  for (const p of m.royale.pois) for (const k of ['id', 'name', 'c', 'r']) assert.ok(p[k] != null, p.id + ' has ' + k);
  assert.equal(m.royale.drops.length, PLAN.pois.reduce((a, p) => a + p.drop.length, 0));
  assert.equal(m.royale.cells.length, PLAN.pois.reduce((a, p) => a + p.cells, 0), 'every POI got its energy cells');
  assert.equal(m.royale.finale.length, 2);
  assert.ok(MAP_ORDER.includes('battleisland') && m.wip, 'registered, marked wip');
  assert.ok(!mapsFor('br', MAPS, MAP_ORDER).includes('battleisland'), 'not in the royale list without ?wip=1 / JF_WIP_MAPS');
  assert.ok(!mapsFor('dm', MAPS, MAP_ORDER).includes('battleisland'), 'not in the other modes either (royale only)');
  for (const [x, z] of [[28, 118], [238, 40], [-372, 40], [-110, 30]]) assert.ok(Math.abs(GRID.at(x, z) - Math.max(-4.2, islandH(x, z))) < 0.01, 'grid = plan at ' + x + ',' + z);
});

test('Battle Island: every mech drop pad is dry, level and open to the sky; every cell is on dry land in its POI', () => {
  for (const [x, y, z, r] of m.royale.drops) {
    let lo = 1e9, hi = -1e9;
    for (let a = 0; a < 16; a++) for (const f of [0, 0.5, 1]) { const h = ground(x + Math.cos(a * Math.PI / 8) * r * f, z + Math.sin(a * Math.PI / 8) * r * f); lo = Math.min(lo, h); hi = Math.max(hi, h); }
    assert.ok(lo > SEA + 0.3, `pad ${x},${z} dry (${lo.toFixed(2)})`);
    assert.ok(hi - lo < 0.3, `pad ${x},${z} level (${(hi - lo).toFixed(2)} m)`);
    assert.ok(Math.abs(y - ground(x, z)) < 0.05, `pad ${x},${z} y is the floor`);
    for (const [dx, dz] of [[0, 0], [r * 0.7, 0], [-r * 0.7, 0], [0, r * 0.7], [0, -r * 0.7]]) assert.equal(raycast([x + dx, y + 0.3, z + dz], [0, 1, 0], 120, m.boxes), null, `pad ${x},${z}: nothing overhead`);
  }
  for (const [x, y, z] of m.royale.cells) {
    assert.ok(y > SEA + 0.3 && Math.abs(y - ground(x, z)) < 0.05, `cell ${x.toFixed(0)},${z.toFixed(0)} on the ground`);
    assert.ok(PLAN.pois.some((p) => Math.hypot(x - p.c[0], z - p.c[1]) < p.r), `cell ${x.toFixed(0)},${z.toFixed(0)} in a POI`);
  }
});

test('Battle Island: a bot steering by the walk graph gets from the harbour to every POI\'s drop pad', () => {
  const bot = (from, goal, max) => {
    const pos = from.slice(), vel = [0, 0, 0], st = {}; let g = true;
    for (let t = 0; t < max; t += 1 / 30) {
      const s = navSteer(m.graph, st, pos, goal, t * 1000), l = Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) || 1;
      const [dx, dz] = s ? s : [(goal[0] - pos[0]) / l, (goal[2] - pos[2]) / l];
      if (s && s[2] && g) vel[1] = 8;
      vel[0] = dx * 7; vel[2] = dz * 7; g = sim(pos, vel, g);
      if (pos[1] < KILL_Y) return 'drowned at ' + pos.map((v) => v.toFixed(0));
      if (Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) < 3) return true;
    }
    return 'stuck at ' + pos.map((v) => v.toFixed(1));
  };
  const port = m.royale.drops[0], from = [port[0], port[1] + 0.1, port[2]];
  for (const p of PLAN.pois) {
    const [dx, dz] = p.drop[0], gx = p.c[0] + dx, gz = p.c[1] + dz, goal = [gx, ground(gx, gz), gz];
    const d = Math.hypot(goal[0] - from[0], goal[2] - from[2]);
    assert.equal(bot(from, goal, d / 7 * 3 + 15), true, `port -> ${p.id}`);
  }
});

test('Battle Island: off the beach into deep water is the sea kill; wading the lagoon and the river is not', () => {
  const walk = (from, dir, secs) => { // walk one way at a run; lowest the feet got
    const pos = [from[0], ground(from[0], from[1]) + 0.05, from[1]], vel = [0, 0, 0]; let g = true, low = 1e9;
    for (let t = 0; t < secs; t += 1 / 30) { vel[0] = dir[0] * 7; vel[2] = dir[1] * 7; g = sim(pos, vel, g); low = Math.min(low, pos[1]); if (pos[1] < KILL_Y) break; }
    return low;
  };
  // the south-west beach (the dune spit), then straight out to sea
  assert.ok(walk([-230, 150], [-0.7, 0.7], 30) < KILL_Y, 'out to sea from the south-west beach');
  assert.ok(walk([-300, -60], [-1, 0], 30) < KILL_Y, 'out to sea from the west beach');
  // the lagoon: in from its inner shore and across the middle, never over your head
  const lag = walk([196, 44], [1, 0], 10); assert.ok(lag > KILL_Y && lag < SEA - 0.5, `the lagoon is wading depth (feet down to ${lag.toFixed(2)})`);
  assert.ok(SEA - ground(238, 40) <= WADE, 'the lagoon\'s middle is <= 1.5 m deep');
  const riv = walk([136, 60], [0, -1], 6); assert.ok(riv > KILL_Y, `across the river (feet down to ${riv.toFixed(2)})`);
});
