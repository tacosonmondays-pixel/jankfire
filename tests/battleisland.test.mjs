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
import { islandH, PLAN, SEA, WADE, KILL_Y, grid } from '../shared/battleisland.js';
import { spawnSync } from 'node:child_process';

const m = MAPS.battleisland, T = m.boxes.terrain;
const sim = (pos, vel, ground) => { vel[1] -= 26 / 30; return !!movePlayer(pos, vel, 1 / 30, m.boxes, ground).ground; };
const ground = (x, z) => T.at(x, z);

test('Battle Island: importing the maps doesn\'t build it (no cost to boot or page load until something asks)', () => {
  const code = "const t0 = performance.now(); const { MAPS } = await import('./shared/map.js'); await import('./shared/royale.js'); const t1 = performance.now(); const d = Object.getOwnPropertyDescriptor(MAPS, 'battleisland'); console.log(JSON.stringify({ ms: t1 - t0, lazy: !!(d && d.get), listed: Object.keys(MAPS).includes('battleisland') }));";
  const r = spawnSync(process.execPath, ['--input-type=module', '-e', code], { cwd: new URL('..', import.meta.url), encoding: 'utf8' });
  const o = JSON.parse(r.stdout.trim().split('\n').pop());
  assert.ok(o.lazy, 'still a getter after import');
  assert.ok(!o.listed, 'not in Object.keys(MAPS) until built');
  console.log('import shared/map.js + royale.js:', o.ms.toFixed(0), 'ms');
});

test('Battle Island: built, with the mode\'s fields, and hidden from the map lists', () => {
  assert.ok(m && T, 'the map and its shaped ground');
  assert.equal(m.royale.pois.length, 9);
  for (const p of m.royale.pois) for (const k of ['id', 'name', 'c', 'r']) assert.ok(p[k] != null, p.id + ' has ' + k);
  assert.equal(m.royale.drops.length, PLAN.pois.reduce((a, p) => a + p.drop.length, 0));
  assert.equal(m.royale.cells.length, PLAN.pois.reduce((a, p) => a + p.cells, 0), 'every POI got its energy cells');
  assert.equal(m.royale.finale.length, 2);
  assert.ok(!MAP_ORDER.includes('battleisland') && m.wip, 'registered, marked wip, out of MAP_ORDER (no ?wip=1 / JF_WIP_MAPS)');
  assert.ok(Object.keys(MAPS).includes('battleisland'), 'an ordinary entry once built');
  assert.ok(!mapsFor('br', MAPS, MAP_ORDER).includes('battleisland'), 'not in the royale list without ?wip=1 / JF_WIP_MAPS');
  assert.ok(!mapsFor('dm', MAPS, MAP_ORDER).includes('battleisland'), 'not in the other modes either (royale only)');
  for (const [x, z] of [[28, 118], [238, 40], [-372, 40], [-110, 30]]) assert.ok(Math.abs(grid().at(x, z) - Math.max(-4.2, islandH(x, z))) < 0.01, 'grid = plan at ' + x + ',' + z);
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

test('Battle Island: Dead Air\'s Blender model is built to exactly its boxes (meta.box = the placement\'s extent)', async () => {
  const fs = await import('node:fs');
  const p = m.boxes.props.find((q) => q.id === 'deadair');
  assert.ok(p, 'the mast is a prop placement');
  const buf = fs.readFileSync(new URL('../public/models/p_deadair.glb', import.meta.url)), len = buf.readUInt32LE(12);
  const gl = JSON.parse(buf.slice(20, 20 + len).toString('utf8')), root = gl.nodes.find((n) => n.extras && n.extras.jf), meta = JSON.parse(root.extras.jf);
  for (let i = 0; i < 3; i++) { assert.ok(Math.abs(meta.box[0][i] - p.lo[i]) < 0.01, `lo[${i}] ${meta.box[0][i]} vs ${p.lo[i]}`); assert.ok(Math.abs(meta.box[1][i] - p.hi[i]) < 0.01, `hi[${i}] ${meta.box[1][i]} vs ${p.hi[i]}`); }
  assert.ok(Math.abs(p.a[1] - 50) < 0.01, 'stood on the summit (50 m)');
  const mine = m.boxes.filter((b) => b.pv === 'deadair');
  assert.ok(mine.length > 20, 'its boxes are tagged');
  for (const b of mine) assert.ok(b.min[1] > 49.99, `every Dead Air box on the summit (one at y ${b.min[1].toFixed(2)}: ${b.mat})`);
});

test('Port Jankton: every model is built to its boxes, everything stands on the town (not under it)', async () => {
  const fs = await import('node:fs');
  const metaOf = (id) => { const buf = fs.readFileSync(new URL(`../public/models/p_${id}.glb`, import.meta.url)), len = buf.readUInt32LE(12); const gl = JSON.parse(buf.slice(20, 20 + len).toString('utf8')); return JSON.parse(gl.nodes.find((n) => n.extras && n.extras.jf).extras.jf); };
  const ids = ['pj_quay', 'pj_bollard', 'pj_pier', 'pj_crane', 'pj_shed_cold', 'pj_shed_fish', 'pj_trawler'];
  for (const id of ids) {
    const ps = m.boxes.props.filter((q) => q.id === id), meta = metaOf(id);
    assert.ok(ps.length, id + ' is placed');
    for (const p of ps) for (let i = 0; i < 3; i++) { assert.ok(Math.abs(meta.box[0][i] - p.lo[i]) < 0.01, `${id} lo[${i}] ${meta.box[0][i]} vs ${p.lo[i]}`); assert.ok(Math.abs(meta.box[1][i] - p.hi[i]) < 0.01, `${id} hi[${i}] ${meta.box[1][i]} vs ${p.hi[i]}`); }
    for (const b of m.boxes.filter((q) => q.pv === id)) assert.ok(b.min[1] > (id === 'pj_trawler' || id === 'pj_quay' ? -1.45 : 1.25), `${id}: a box at y ${b.min[1].toFixed(2)}`);
  }
});

test('Port Jankton: walk in at a warehouse\'s quay door, out at its street door; the quay is a sheer step down to the basin', () => {
  const pos = [-15, 1.65, 138], vel = [0, 0, 0]; let g = true;
  for (let t = 0; t < 6; t += 1 / 30) { vel[0] = 0; vel[2] = -7; g = sim(pos, vel, g); }
  assert.ok(pos[2] < 108 && Math.abs(pos[0] + 15) < 0.5 && Math.abs(pos[1] - 1.6) < 0.2, 'through the cold store, out the street side: ' + pos.map((v) => v.toFixed(1)));
  const top = raycast([20, 5, 145.5], [0, -1, 0], 10, m.boxes), below = raycast([20, 5, 146.5], [0, -1, 0], 10, m.boxes);
  assert.ok(top && Math.abs(5 - top.t - 1.6) < 0.05, 'the quay\'s top at the town level');
  assert.ok(below && 5 - below.t < -1.3, 'a step off it: the basin, waist-deep');
});
