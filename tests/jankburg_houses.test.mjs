// Jankburg's city houses: every lot of a kind is the same size so one Blender house (public/models/arch/jbh_*.glb) fits
// them all. The lots moved when they were snapped, so: every copy of a kind has exactly the same boxes, bots can still get
// from every spawn to the plaza and through the gates (the server's walk graph), and a body walked with the shared
// physics along those routes gets there.
import test from 'node:test';
import assert from 'node:assert/strict';
import { MAPS } from '../shared/map.js';
import '../shared/royale.js';
import { navLocate, navPath } from '../shared/nav.js';
import { navCheck } from '../shared/navcheck.js';
import { movePlayer, PH } from '../shared/physics.js';

const J = MAPS.jankburg;
const inv = (x, z, r) => [[x, z], [z, -x], [-x, -z], [-z, x]][r & 3];
const r3 = (v) => Math.round(v * 1000) / 1000;

test('every lot of a kind has the same boxes (one Blender house per kind)', () => {
  const ids = [...new Set(J.boxes.arch.filter((a) => a.id.startsWith('jbh_')).map((a) => a.id))];
  assert.ok(ids.length >= 12, 'the city houses are tagged: ' + ids.join(' '));
  for (const id of ids) {
    const places = J.boxes.arch.map((a, i) => ({ ...a, ai: i })).filter((a) => a.id === id);
    const keys = places.map((p) => J.boxes.filter((b) => b.av === id && b.ai === p.ai).map((b) => {
      const [ax, az] = inv(b.min[0] - p.p[0], b.min[2] - p.p[2], p.r), [bx, bz] = inv(b.max[0] - p.p[0], b.max[2] - p.p[2], p.r);
      return [r3(Math.min(ax, bx)), r3(b.min[1]), r3(Math.min(az, bz)), r3(Math.max(ax, bx)), r3(b.max[1]), r3(Math.max(az, bz))].join(',');
    }).sort().join(';'));
    for (const k of keys) assert.equal(k, keys[0], id + ': a lot whose boxes differ');
  }
});

test('bots reach every spawn, the plaza and the four gates on the walk graph', () => {
  const r = navCheck(J, null);
  const bad = r.spots.filter((s) => !s.ok).map((s) => s.what);
  assert.deepEqual(bad, [], 'spots off the main walk area');
  const g = J.graph;
  const goals = [[0, 0.1, 40], [0, 0.1, -150], [0, 0.1, 150], [150, 0.1, 0], [-150, 0.1, 0]];
  for (const s of J.spawns) {
    const a = navLocate(g, s);
    for (const t of goals) assert.ok(navPath(g, a, navLocate(g, t)), `no route from spawn ${s.map((v) => v.toFixed(0))} to ${t}`);
  }
});

test('walked with the shared physics, a body follows the bot routes from spawns to the plaza', () => {
  const g = J.graph, dt = 1 / 30, speed = 6;
  for (const s of J.spawns.slice(0, 12)) {
    const path = navPath(g, navLocate(g, s), navLocate(g, [0, 0.1, 40]));
    assert.ok(path, 'a route');
    const pos = [s[0], s[1], s[2]], vel = [0, 0, 0];
    let k = 0, t = 0;
    while (k < path.length && t < 240) {
      const n = g.nodes[path[k]], dx = n[0] - pos[0], dz = n[2] - pos[2], d = Math.hypot(dx, dz);
      if (d < 1.0) { k++; continue; }
      vel[0] = dx / d * speed; vel[2] = dz / d * speed; vel[1] -= 20 * dt;
      const res = movePlayer(pos, vel, dt, J.boxes, true);
      if (res.ground !== null) vel[1] = 0;
      if (res.wall && vel[1] === 0) vel[1] = 5.5; // (a hop over a kerb, like the bots)
      t += dt;
    }
    assert.ok(Math.hypot(pos[0], pos[2] - 40) < 6, `from spawn ${s.map((v) => v.toFixed(0))}: stuck at ${pos.map((v) => v.toFixed(1))} after ${t.toFixed(0)} s (node ${k}/${path.length})`);
    assert.ok(pos[1] > -2 && pos[1] < PH.height + 20, 'stayed on the ground');
  }
});
