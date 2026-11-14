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
import { islandH, PLAN, SEA, WADE, KILL_Y, grid, PK, PJP, segDist, RK, rockPlan, ROCK_KEEP } from '../shared/battleisland.js';
import { mechBody } from '../shared/mech.js';
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
  const ids = ['pj_quay', 'pj_bollard', 'pj_pier', 'pj_crane', 'pj_shed_cold', 'pj_shed_fish', 'pj_trawler', 'pj_bait', 'pj_cod', 'pj_park', 'bi_blossom', 'bi_leafy', 'pj_pub', 'pj_harbour'];
  for (const id of ids) {
    const ps = m.boxes.props.filter((q) => q.id === id), meta = metaOf(id);
    assert.ok(ps.length, id + ' is placed');
    for (const p of ps) for (let i = 0; i < 3; i++) { assert.ok(Math.abs(meta.box[0][i] - p.lo[i]) < 0.01, `${id} lo[${i}] ${meta.box[0][i]} vs ${p.lo[i]}`); assert.ok(Math.abs(meta.box[1][i] - p.hi[i]) < 0.01, `${id} hi[${i}] ${meta.box[1][i]} vs ${p.hi[i]}`); }
    for (const b of m.boxes.filter((q) => q.pv === id)) assert.ok(b.min[1] > (id === 'pj_trawler' || id === 'pj_quay' ? -1.45 : 1.25), `${id}: a box at y ${b.min[1].toFixed(2)}`);
    for (const p of ps) if (p.f !== undefined) for (const i of [0, 2]) assert.ok(Math.abs(p.lo[i] + p.hi[i]) < 0.01, `${id}: spun round its middle (lo ${p.lo[i]}, hi ${p.hi[i]})`); // (a spun prop is fitted round its own origin)
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

test('Port Jankton main street: in at each shop\'s street door, out its back door into the alley; the roof is solid', () => {
  for (const [x0, dir, x1] of [[23, -1, 3], [33, 1, 53]]) { // Bait & Tackle (front to the east), Oh My Cod! (front to the west)
    const pos = [x0, 1.65, 120], vel = [0, 0, 0]; let g = true;
    for (let t = 0; t < 4; t += 1 / 30) { vel[0] = dir * 7; vel[2] = 0; g = sim(pos, vel, g); }
    assert.ok(dir * (pos[0] - x1) > 0 && Math.abs(pos[2] - 120) < 0.5 && Math.abs(pos[1] - 1.6) < 0.2, 'through the shop and out the back: ' + pos.map((v) => v.toFixed(1)));
  }
  for (const x of [12, 44]) { const hit = raycast([x - 2, 20, 118], [0, -1, 0], 30, m.boxes); assert.ok(hit && Math.abs(20 - hit.t - 6.3) < 0.05, 'stand on the roof at ' + x); }
});

test('Petal Park: walk the paths from the gate to the fountain and out each side; hedges, trunks and the basin block; the trees stand on the ground', () => {
  const [cx, cz] = PK.c, y = 1.6;
  const walk = (from, dir, secs) => { const pos = [from[0], y + 0.05, from[1]], vel = [0, 0, 0]; let g = true; for (let t = 0; t < secs; t += 1 / 30) { vel[0] = dir[0] * 7; vel[2] = dir[1] * 7; g = sim(pos, vel, g); } return pos; };
  // in through the gate on the west path, over the fountain's rim (a step) into the water, up to the pedestal
  const p = walk([cx - 16, cz], [1, 0], 2.6);
  assert.ok(p[0] > cx - 2 && p[0] < cx - PK.fountain.ped && Math.abs(p[2] - cz) < 0.3 && p[1] > y, 'gate -> the fountain, stopped by the pedestal: ' + p.map((v) => v.toFixed(1)));
  // down each path from the plaza's edge out of the park: nothing in the way
  for (const [sx, sz, dx, dz] of [[cx + 5.5, cz, 1, 0], [cx, cz - 5.5, 0, -1], [cx, cz + 5.5, 0, 1], [cx - 5.5, cz, -1, 0]]) {
    const q = walk([sx, sz], [dx, dz], 1.6);
    assert.ok(Math.hypot(q[0] - sx, q[2] - sz) > 10 && Math.abs(q[1] - y) < 0.15, `out along the path toward ${dx},${dz}: ` + q.map((v) => v.toFixed(1)));
  }
  // a hedge (the west path's north one) and a cherry tree's trunk stop you
  const h = walk([cx - 9, cz - 5], [0, 1], 1.5); assert.ok(h[2] < cz - 2.3 && h[2] > cz - 3, 'the hedge stops you: ' + h[2].toFixed(2));
  const [bx, bz] = PK.blossoms[0], tr = walk([cx + bx - 3, cz + bz], [1, 0], 1.5); assert.ok(tr[0] < cx + bx - 0.25, 'the cherry trunk stops you: ' + tr[0].toFixed(2));
  // bullets stop in a crown, and nothing hangs in the air: every tree's trunk box stands on the ground
  const c = PK.blossoms[1]; assert.ok(raycast([cx + c[0] - 6, y + 4.3, cz + c[1]], [1, 0, 0], 12, m.boxes), 'the cherry crown stops a shot');
  for (const id of ['bi_blossom', 'bi_leafy']) for (const q of m.boxes.props.filter((o) => o.id === id)) {
    const g = ground(q.a[0], q.a[2]); assert.ok(q.a[1] <= g + 0.01 && q.a[1] > g - 0.4, `${id} at ${q.a[0]},${q.a[2]}: foot ${q.a[1].toFixed(2)}, ground ${g.toFixed(2)}`);
  }
  // the crowns' bars are each under 1.2 m across one way: the royale's loot spots skip them (no loot hidden up in a crown)
  for (const b of m.boxes.filter((q) => (q.pv === 'bi_blossom' || q.pv === 'bi_leafy') && q.min[1] > ground((q.min[0] + q.max[0]) / 2, (q.min[2] + q.max[2]) / 2) + 1)) assert.ok(Math.min(b.max[0] - b.min[0], b.max[2] - b.min[2]) < 1.2, 'a crown bar too wide: loot could land on it');
  // the mech drop pad (28, 82) stays clear, no energy cell lands in the park's boxes
  for (const b of m.boxes.filter((q) => q.pv === 'pj_park' || q.pv === 'bi_blossom' || q.pv === 'bi_leafy')) {
    assert.ok(b.max[0] < 28 - 8 || b.min[0] > 28 + 8 || b.max[2] < 82 - 8 || b.min[2] > 82 + 8, 'clear of the mech drop pad');
    for (const [x, , z] of m.royale.cells) assert.ok(!(x > b.min[0] - 1 && x < b.max[0] + 1 && z > b.min[2] - 1 && z < b.max[2] + 1), `cell ${x.toFixed(1)},${z.toFixed(1)} clear of ${b.pv}`);
  }
});

test('Port Jankton pub and harbour master: in the front and out the back, up to the terrace and the lookout, windows you shoot through, mechs keep the street and the pier, the pads and cells stay clear', () => {
  const y = 1.6, mine = m.boxes.filter((q) => q.pv === 'pj_pub' || q.pv === 'pj_harbour');
  // steer a player through waypoints at a run (stairs are steps: each under the 0.6 m step-up)
  const go = (from, pts, secs = 6, body = null) => {
    const pos = [from[0], (from[2] ?? y) + 0.05, from[1]], vel = [0, 0, 0]; let g = true, k = 0;
    for (let t = 0; t < secs && k < pts.length; t += 1 / 30) {
      const [tx, tz] = pts[k], dx = tx - pos[0], dz = tz - pos[2], d = Math.hypot(dx, dz);
      if (d < 0.25) { k++; continue; }
      vel[0] = dx / d * 7; vel[2] = dz / d * 7; vel[1] -= 26 / 30; g = !!movePlayer(pos, vel, 1 / 30, m.boxes, g, body).ground;
    }
    return { pos, k };
  };
  const [px, pz] = PJP.pub.c, [hx, hz] = PJP.hm.c;
  // the pub: in at the front doors (east, on the drag), past the snug and the end of the bar, out the back door (west)
  const a = go([px + 9, pz], [[px + 2, pz], [px - 4, pz + 5.3], [px - 9, pz + 5.3]]);
  assert.ok(a.k === 3 && Math.abs(a.pos[1] - y) < 0.2, 'through the pub, front door to back door: ' + a.pos.map((v) => v.toFixed(1)));
  // up the stair on its south side, onto the landing, through the parapet's gap onto the terrace (4.5 m up)
  const b = go([px + 7, pz + 8.65], [[px + 0.9, pz + 8.65], [px + 0.9, pz + 5]], 6);
  assert.ok(b.k === 2 && Math.abs(b.pos[1] - (y + 4.5)) < 0.1, 'up the stair onto the roof terrace: ' + b.pos.map((v) => v.toFixed(2)));
  // the harbour master: in its quay door, round the counter, out the back door into the alley
  const c = go([hx - 1, hz + 6], [[hx - 1, hz + 1.7], [hx + 2.7, hz + 1.7], [hx + 2.7, hz - 4.5]]);
  assert.ok(c.k === 3 && Math.abs(c.pos[1] - y) < 0.2, 'through the harbour master, quay door to back door: ' + c.pos.map((v) => v.toFixed(1)));
  // up the stair on its front, onto the roof, up the flight to the gallery, in at the lookout's door (7.4 m up)
  const d = go([hx + 5.5, hz + 3.7], [[hx + 1.2, hz + 3.7], [hx + 1.2, hz - 1.25], [hx - 2.2, hz - 1.25]], 8);
  assert.ok(d.k === 3 && Math.abs(d.pos[1] - (y + PJP.hm.top)) < 0.1, 'up to the lookout: ' + d.pos.map((v) => v.toFixed(2)));
  // the open windows: a shot goes in one and on across the room
  const hit = (o, dir) => raycast(o, dir, 40, m.boxes);
  const w1 = hit([px + 10, y + 1.5, pz - 4], [-1, 0, 0]); assert.ok(w1 && w1.t > 10 - (PJP.pub.w / 2 - PJP.pub.t), 'in the pub\'s front window: ' + (w1 && w1.t.toFixed(2)));
  const w2 = hit([px + 0.8, y + 1.5, pz - 14], [0, 0, 1]); assert.ok(w2 && w2.t > 14 - PJP.pub.d / 2 + 0.3, 'in its north window: ' + (w2 && w2.t.toFixed(2)));
  const w3 = hit([hx - 9, y + 1.5, hz], [1, 0, 0]); assert.ok(w3 && w3.t > 9 - PJP.hm.w / 2 + 0.3, 'in the harbour master\'s west window: ' + (w3 && w3.t.toFixed(2)));
  const w4 = hit([hx - 9, y + PJP.hm.top + 1.5, hz - 1.3], [1, 0, 0]); assert.ok(!w4 || w4.t > 9 + PJP.hm.tower[0] + 0.3, 'in the lookout\'s west window (and out its door): ' + (w4 && w4.t.toFixed(2)));
  const w5 = hit([hx - 2.2, y + PJP.hm.top + 1.5, hz + 9], [0, 0, -1]); assert.ok(!w5 || w5.t > 9 - PJP.hm.tower[3] + 0.3, 'and its south one (the view over the piers): ' + (w5 && w5.t.toFixed(2)));
  // mechs: nothing on the main drag or the ring road; the widest mech walks from the fish warehouse's quay door out
  // past the harbour master to the east pier's root, the tallest walks the drag past the pub
  const drag = PLAN.roads.find((r) => r.name === 'Main Drag'), ring = PLAN.roads.find((r) => r.name === 'Ring Road');
  for (const q of mine) for (const x of [q.min[0], q.max[0]]) for (const z of [q.min[2], q.max[2]]) {
    assert.ok(segDist(x, z, drag.pts) > drag.w / 2 + 1, `${q.pv} box corner ${x.toFixed(1)},${z.toFixed(1)} clear of the main drag`);
    assert.ok(segDist(x, z, ring.pts) > ring.w / 2 + 1, `${q.pv} box corner ${x.toFixed(1)},${z.toFixed(1)} clear of the ring road`);
  }
  const mw = go([71, 128], [[71, 144.5]], 6, mechBody('wrecking')); assert.ok(mw.k === 1, 'the wrecking ball rolls out the fish warehouse\'s quay door to the pier: ' + mw.pos.map((v) => v.toFixed(1)));
  const mt = go([26, 112], [[24.5, 84]], 8, mechBody('paperplane')); assert.ok(mt.k === 1, 'the paper plane walks the drag past the pub: ' + mt.pos.map((v) => v.toFixed(1)));
  // both drop pads stay clear, no energy cell lands in (or against) these boxes
  for (const q of mine) {
    for (const [x, , z, r] of m.royale.drops) assert.ok(q.max[0] < x - r || q.min[0] > x + r || q.max[2] < z - r || q.min[2] > z + r, `${q.pv} clear of the drop pad at ${x},${z}`);
    for (const [x, , z] of m.royale.cells) assert.ok(!(x > q.min[0] - 1 && x < q.max[0] + 1 && z > q.min[2] - 1 && z < q.max[2] + 1), `cell ${x.toFixed(1)},${z.toFixed(1)} clear of ${q.pv}`);
  }
});

test('The rocks: every model is built round its boxes and fitted per copy (meta.box x the copy\'s scale = its placement)', async () => {
  const fs = await import('node:fs');
  const metaOf = (id) => { const buf = fs.readFileSync(new URL(`../public/models/p_${id}.glb`, import.meta.url)), len = buf.readUInt32LE(12); const gl = JSON.parse(buf.slice(20, 20 + len).toString('utf8')); return JSON.parse(gl.nodes.find((n) => n.extras && n.extras.jf).extras.jf); };
  const plan = rockPlan();
  for (const id of Object.keys(RK)) {
    const meta = metaOf(id), K = RK[id], ps = [...m.boxes.props, ...m.deco.props].filter((q) => q.id === id);
    for (let i = 0; i < 3; i++) { assert.ok(Math.abs(meta.box[0][i] - K.ext[0][i]) < 0.01 && Math.abs(meta.box[1][i] - K.ext[1][i]) < 0.01, `${id} meta.box = RK ext (${i})`); }
    assert.ok(ps.length, id + ' is placed');
    assert.equal(ps.length, plan.filter((p) => p.id === id).length, id + ': one placement per planned rock');
    for (const p of ps) {
      const r = plan.find((q) => q.id === id && Math.hypot(q.a[0] - p.a[0], q.a[2] - p.a[2]) < 0.01);
      assert.ok(r, `${id} at ${p.a[0]},${p.a[2]} is in the plan`);
      for (let i = 0; i < 3; i++) { assert.ok(Math.abs(meta.box[0][i] * r.s[i] - p.lo[i]) < 0.01, `${id} lo[${i}] ${meta.box[0][i] * r.s[i]} vs ${p.lo[i]}`); assert.ok(Math.abs(meta.box[1][i] * r.s[i] - p.hi[i]) < 0.01, `${id} hi[${i}] ${meta.box[1][i] * r.s[i]} vs ${p.hi[i]}`); }
      assert.equal(p.f, undefined, 'fitted per axis (not spun)');
    }
  }
  // the cliff faces are look-only (map.deco); every other piece collides
  for (const id of ['bi_cliff_a', 'bi_cliff_b', 'bi_cliff_c']) assert.ok(!m.boxes.some((b) => b.pv === id) && m.deco.some((b) => b.pv === id), id + ' look-only');
  for (const id of Object.keys(RK).filter((k) => RK[k].col)) assert.ok(m.boxes.some((b) => b.pv === id), id + ' collides');
});

test('The rocks: nothing in the way (roads + a mech\'s width, POIs, pads, cells, the harbour, the river, the lagoon and its gap, the lighthouse), on the ground, deterministic', () => {
  const rocks = m.boxes.filter((b) => b.pv && RK[b.pv]), faces = m.deco.filter((b) => b.pv && RK[b.pv]);
  assert.ok(rocks.length > 300 && faces.length > 30, `rocks placed: ${rocks.length} boxes, ${faces.length} cliff faces`);
  const corners = (b) => [[b.min[0], b.min[2]], [b.max[0], b.min[2]], [b.min[0], b.max[2]], [b.max[0], b.max[2]], [(b.min[0] + b.max[0]) / 2, (b.min[2] + b.max[2]) / 2]];
  for (const b of rocks) {
    const tag = `${b.pv} box at ${b.min[0].toFixed(1)},${b.min[2].toFixed(1)}`;
    for (const [x, z] of corners(b)) {
      for (const r of PLAN.roads) assert.ok(segDist(x, z, r.pts) > r.w / 2 + 4, `${tag} clear of ${r.name}`);
      assert.ok(!PLAN.pois.some((p) => x > p.rect[0] - 1 && x < p.rect[2] + 1 && z > p.rect[1] - 1 && z < p.rect[3] + 1), `${tag} outside every POI`);
      assert.ok(Math.hypot((x - 30) / 84, (z - 196) / 66) > 1.3, `${tag} out of the harbour bay`);
      assert.ok(segDist(x, z, PLAN.river.pts) > PLAN.river.w / 2 + PLAN.river.bank + 4, `${tag} off the river`);
      const L = PLAN.lagoon; assert.ok(Math.hypot((x - L.c[0]) / L.r[0], (z - L.c[1]) / L.r[1]) > 1.3 && Math.hypot(x - L.gap[0], z - L.gap[1]) > 25, `${tag} out of the lagoon and its reef gap`);
      assert.ok(Math.hypot(x - ROCK_KEEP.flat[0], z - ROCK_KEEP.flat[1]) > 36, `${tag} off the lighthouse's flat`);
    }
    for (const [x, , z, r] of m.royale.drops) assert.ok(b.max[0] < x - r - 2 || b.min[0] > x + r + 2 || b.max[2] < z - r - 2 || b.min[2] > z + r + 2, `${tag} clear of the drop pad at ${x},${z}`);
    for (const [x, , z] of m.royale.cells) assert.ok(!(x > b.min[0] - 2 && x < b.max[0] + 2 && z > b.min[2] - 2 && z < b.max[2] + 2), `${tag} clear of the cell at ${x.toFixed(1)},${z.toFixed(1)}`);
  }
  // each rock stands on the ground: its foot box is at or under the ground at all its corners (nothing floats), and it
  // stands out of it (its top a good bit over the highest ground under it: no boxes buried for nothing)
  for (const p of m.boxes.props.filter((q) => RK[q.id] && RK[q.id].col)) {
    const mine = rocks.filter((b) => Math.abs(b.min[1] - (p.a[1] + p.lo[1])) < 0.02 && b.max[0] >= p.a[0] - 30 && b.min[0] <= p.a[0] + 30 && b.max[2] >= p.a[2] - 30 && b.min[2] <= p.a[2] + 30 && b.pv === p.id);
    assert.ok(mine.length, `${p.id} at ${p.a[0]},${p.a[2]} has its foot boxes`);
    let hi = -1e9; for (const b of mine) for (const [x, z] of corners(b)) { const g = ground(x, z); assert.ok(b.min[1] <= g + 0.01, `${p.id} at ${p.a[0]},${p.a[2]}: its foot floats (${b.min[1].toFixed(2)} over ${g.toFixed(2)})`); hi = Math.max(hi, g); }
    if (p.id !== 'bi_ledge') assert.ok(p.a[1] + p.hi[1] > hi + 0.3, `${p.id} at ${p.a[0]},${p.a[2]}: buried (top ${(p.a[1] + p.hi[1]).toFixed(2)}, ground up to ${hi.toFixed(2)})`);
  }
  // the lighthouse's cliff-top flat stays usable: nothing collides on it, and the cliff faces round it stay below its top
  const [fx, fz] = ROCK_KEEP.flat, top = ground(fx, fz);
  for (const b of faces) if (Math.hypot((b.min[0] + b.max[0]) / 2 - fx, (b.min[2] + b.max[2]) / 2 - fz) < 40) assert.ok(b.max[1] < top - 0.1, `a cliff face by the lighthouse flat tops out at ${b.max[1].toFixed(2)} (the flat: ${top.toFixed(2)})`);
  // deterministic: the same plan in a fresh process (the server and every client build the same rocks)
  const code = "const B = await import('./shared/battleisland.js'); console.log(JSON.stringify(B.rockPlan()));";
  const out = spawnSync(process.execPath, ['--input-type=module', '-e', code], { cwd: new URL('..', import.meta.url), encoding: 'utf8', maxBuffer: 1 << 26 });
  assert.equal(out.stdout.trim().split('\n').pop(), JSON.stringify(rockPlan()), 'the same rocks every time');
});

test('The rocks: you walk round the boulders on a beach, climb out of the sea onto a shelf, and mechs still walk the coast roads', () => {
  const walk = (from, dir, secs, body = null) => { const pos = [from[0], ground(from[0], from[1]) + 0.05, from[1]], vel = [0, 0, 0]; let g = true; for (let t = 0; t < secs; t += 1 / 30) { vel[0] = dir[0] * 7; vel[2] = dir[1] * 7; vel[1] -= 26 / 30; g = !!movePlayer(pos, vel, 1 / 30, m.boxes, g, body).ground; } return pos; };
  const all = m.boxes.props.filter((p) => RK[p.id] && RK[p.id].col), wOf = (p) => Math.max(p.hi[0] - p.lo[0], p.hi[2] - p.lo[2]) / 2;
  const land = all.filter((p) => ground(p.a[0], p.a[2]) > SEA + 0.3 && p.id !== 'bi_ledge');
  assert.ok(land.length > 20, 'boulders up on the land: ' + land.length);
  // any two rocks leave a gap you walk through (no slots to get stuck in)
  for (const p of all) for (const q of all) if (p !== q) assert.ok(Math.hypot(p.a[0] - q.a[0], p.a[2] - q.a[2]) > (wOf(p) + wOf(q)) + 0.9, `${p.id} at ${p.a[0]},${p.a[2]} and ${q.id} at ${q.a[0]},${q.a[2]} leave a gap`);
  // round every boulder on dry land: from a step outside its box, a walk past it (along each side) isn't stopped by it
  let n = 0;
  for (const p of land) {
    const w = wOf(p) + 1.4;
    if (all.some((q) => q !== p && Math.hypot(p.a[0] - q.a[0], p.a[2] - q.a[2]) < w + wOf(q) + 2.5)) continue; // (one with a neighbour close by: the walk past runs into that)
    for (const [sx, sz, dx, dz] of [[-w, -w, 1, 0], [-w, w, 1, 0], [-w, -w, 0, 1], [w, -w, 0, 1]]) {
      const x = p.a[0] + sx, z = p.a[2] + sz;
      if (ground(x, z) < SEA + 0.3 || ground(x + dx * 2 * w, z + dz * 2 * w) < SEA + 0.3 || m.boxes.some((b) => !b.ter && x > b.min[0] - 0.5 && x < b.max[0] + 0.5 && z > b.min[2] - 0.5 && z < b.max[2] + 0.5 && b.max[1] > ground(x, z) + 0.3)) continue;
      const q = walk([x, z], [dx, dz], 2 * w / 7 + 0.4);
      const blocker = m.boxes.find((b) => RK[b.pv] && q[0] > b.min[0] - 0.45 && q[0] < b.max[0] + 0.45 && q[2] > b.min[2] - 0.45 && q[2] < b.max[2] + 0.45 && q[1] < b.max[1]);
      if (Math.hypot(q[0] - x, q[2] - z) < 2 * w - 0.6) assert.ok(!blocker || q[1] > blocker.max[1] - 0.05, `stuck against a rock walking past the ${p.id} at ${p.a[0]},${p.a[2]}: ${q.map((v) => v.toFixed(1))}`);
      n++;
    }
  }
  assert.ok(n > 40, 'walked past the boulders: ' + n);
  // a shelf at the waterline: you step up onto it out of the water
  const sh = m.boxes.props.filter((p) => p.id === 'bi_ledge' && p.a[1] + p.hi[1] < SEA + 0.6);
  assert.ok(sh.length >= 3, 'shelves at the waterline: ' + sh.length);
  for (const p of sh) assert.ok(p.a[1] + p.hi[1] - Math.max(SEA - 1.4, ground(p.a[0], p.a[2])) > 0.3 && p.a[1] + p.hi[1] - SEA < 0.6, 'a shelf top just over the water');
  // mechs walk the coast roads past the cliffs: the Point Road out to the headland, the ring's west side and its north
  // (the wrecking ball sticks on the Point Road's bare slope at -188, -82 on main too: not a rock)
  const tall = mechBody('paperplane'), wide = mechBody('wrecking');
  for (const [body, pts] of [[tall, [[-150, -40], [-210, -110], [-245, -155]]], [tall, [[-170, 40], [-150, -40], [-120, -128]]], [wide, [[-120, -128], [-30, -178]]]]) {
    const pos = [pts[0][0], ground(pts[0][0], pts[0][1]) + 0.05, pts[0][1]], vel = [0, 0, 0]; let g = true, k = 1;
    for (let t = 0; t < 90 && k < pts.length; t += 1 / 30) {
      const [tx, tz] = pts[k], dx = tx - pos[0], dz = tz - pos[2], d = Math.hypot(dx, dz);
      if (d < 1.5) { k++; continue; }
      vel[0] = dx / d * 7; vel[2] = dz / d * 7; vel[1] -= 26 / 30; g = !!movePlayer(pos, vel, 1 / 30, m.boxes, g, body).ground;
    }
    assert.ok(k === pts.length, 'a mech walks the road ' + JSON.stringify(pts) + ': stopped at ' + pos.map((v) => v.toFixed(1)));
  }
});
