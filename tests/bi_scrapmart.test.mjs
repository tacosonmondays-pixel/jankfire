// node --test tests/bi_scrapmart.test.mjs : Battle Island's SCRAP MART (shared/bi_scrapmart.js). every model is built to
// exactly its boxes; everything stands on the ground with its boxes `still`; a mech walks Hangar Road straight through
// the hangar (in one door, out the other); up the stairs onto the catwalk; into the parts office through its door; the
// drop pads stay clear; a bot steering by the walk graph gets from a drop pad into the hangar and across to the yard
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { MAPS } from '../shared/map.js';
import '../shared/royale.js';
import { navSteer } from '../shared/nav.js';
import { movePlayer } from '../shared/physics.js';
import { PLAN, KILL_Y, segDist } from '../shared/battleisland.js';
import { SM } from '../shared/bi_scrapmart.js';

const m = MAPS.battleisland, T = m.boxes.terrain;
const ground = (x, z) => T.at(x, z);
const sim = (pos, vel, g) => { vel[1] -= 26 / 30; return !!movePlayer(pos, vel, 1 / 30, m.boxes, g).ground; };
const metaOf = (id) => { const buf = fs.readFileSync(new URL(`../public/models/p_${id}.glb`, import.meta.url)), len = buf.readUInt32LE(12); const gl = JSON.parse(buf.slice(20, 20 + len).toString('utf8')); return JSON.parse(gl.nodes.find((n) => n.extras && n.extras.jf).extras.jf); };
const walk = (from, pts, secs = 20, speed = 6) => {
  const pos = from.slice(), vel = [0, 0, 0]; let g = true, k = 0;
  for (let t = 0; t < secs && k < pts.length; t += 1 / 30) {
    const [gx, gz] = pts[k], dx = gx - pos[0], dz = gz - pos[2], l = Math.hypot(dx, dz);
    if (l < 0.35) { k++; continue; }
    vel[0] = dx / l * speed; vel[2] = dz / l * speed; g = sim(pos, vel, g);
    if (pos[1] < KILL_Y) return pos;
  }
  for (let t = 0; t < 0.5; t += 1 / 30) { vel[0] = vel[2] = 0; g = sim(pos, vel, g); }
  return pos;
};
const H = SM.hangar, hy = () => m.boxes.props.find((q) => q.id === 'sm_hangar').a[1];
const IDS = ['sm_hangar', 'sm_gantry', 'sm_bale', 'sm_crusher', 'sm_tyres', 'sm_target', 'sm_bags', 'sm_berm', 'sm_sign'];

test('Scrap Mart: every model is built to exactly its boxes, every box is `still` and stands on the ground', () => {
  for (const id of IDS) {
    const ps = m.boxes.props.filter((q) => q.id === id), meta = metaOf(id);
    assert.ok(ps.length, id + ' is placed');
    for (const p of ps) for (let i = 0; i < 3; i++) {
      assert.ok(Math.abs(meta.box[0][i] - p.lo[i]) < 0.01, `${id} lo[${i}] ${meta.box[0][i]} vs ${p.lo[i]}`);
      assert.ok(Math.abs(meta.box[1][i] - p.hi[i]) < 0.01, `${id} hi[${i}] ${meta.box[1][i]} vs ${p.hi[i]}`);
      assert.ok(Math.abs(p.a[1] - ground(p.a[0], p.a[2])) < 1.0 || id === 'sm_bale', `${id} at ${p.a.map((v) => v.toFixed(1))} stands on the ground (${ground(p.a[0], p.a[2]).toFixed(2)})`);
    }
    const mine = m.boxes.filter((b) => b.pv === id);
    assert.ok(mine.length && mine.every((b) => b.still), id + ': its boxes are tagged and still');
  }
  assert.ok(m.boxes.filter((b) => b.pv === 'sm_bale').length >= 30, 'stacks of crushed cars');
});

test('Scrap Mart: a mech walks Hangar Road straight through the hangar, in at one door and out of the other', () => {
  const road = PLAN.roads.find((r) => r.name === 'Hangar Road');
  const hw = 2.0, h = 6.0; // (a 5-6 m mech, arms and all)
  for (let x = H.x0 - 6; x <= H.x1 + 6; x += 0.5) {
    let z = 0, best = 1e9; for (let zz = 0; zz <= 60; zz += 0.25) { const d = segDist(x, zz, road.pts); if (d < best) { best = d; z = zz; } } // (the road's middle at this x)
    const y = Math.max(ground(x, z), hy() + 0.06) + 0.05;
    const hit = m.boxes.find((b) => !b.ter && b.max[1] > y + 0.6 && b.min[1] < y + h && b.max[0] > x - hw && b.min[0] < x + hw && b.max[2] > z - hw && b.min[2] < z + hw);
    assert.ok(!hit, `a mech on the road at ${x.toFixed(1)},${z.toFixed(1)} hits ${hit && hit.pv} ${hit && hit.min.map((v) => v.toFixed(1))}`);
  }
  const pos = walk([H.x0 - 8, ground(H.x0 - 8, 34) + 0.1, 34], [[H.x1 + 8, 28]], 20, 7);
  assert.ok(pos[0] > H.x1 + 7, 'walked through the shed: ' + pos.map((v) => v.toFixed(1)));
});

test('Scrap Mart: up the stairs by the east door onto the catwalk; into the parts office through its door', () => {
  const [sx0, sx1, sz0, sz1] = SM.stair, zs = (sz0 + sz1) / 2, y0 = hy();
  const top = walk([sx0 - 1.0, y0 + 0.1, SM.mezz.z0 - 2.5], [[sx0 + 0.35, zs], [sx0 - 0.3, zs], [SM.mezz.x0 + 12, zs]], 25, 4);
  assert.ok(Math.abs(top[1] - (y0 + SM.mezz.y)) < 0.15 && top[0] < sx1 - 2, `on the catwalk: ${top.map((v) => v.toFixed(2))}`);
  const [, , oz, , [d0, d1]] = SM.office, dx = (d0 + d1) / 2;
  const inn = walk([dx, y0 + 0.1, oz - 4], [[dx, oz + 1.6]], 10, 3);
  assert.ok(inn[2] > oz + 1.0 && Math.abs(inn[1] - (y0 + 0.06)) < 0.15, `in the office: ${inn.map((v) => v.toFixed(2))}`);
});

test('Scrap Mart: the drop pads stay clear; a bot gets from a pad into the hangar and over to the yard', () => {
  const P = PLAN.pois.find((q) => q.id === 'hangar');
  for (const [dx, dz, r] of P.drop) {
    const px = P.c[0] + dx, pz = P.c[1] + dz;
    for (const b of m.boxes) if (/^sm_/.test(b.pv || '')) assert.ok(b.max[0] < px - r || b.min[0] > px + r || b.max[2] < pz - r || b.min[2] > pz + r, `the pad at ${px},${pz} is clear (${b.pv})`);
  }
  const go = (from, goal, secs) => {
    const pos = from.slice(), vel = [0, 0, 0], st = {}; let g = true;
    for (let t = 0; t < secs; t += 1 / 30) {
      const sv = navSteer(m.graph, st, pos, goal, t * 1000), l = Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) || 1;
      const [ax, az] = sv ? sv : [(goal[0] - pos[0]) / l, (goal[2] - pos[2]) / l];
      if (sv && sv[2] && g) vel[1] = 8;
      vel[0] = ax * 7; vel[2] = az * 7; g = sim(pos, vel, g);
      if (Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) < 2.5) return true;
    }
    return 'ended at ' + pos.map((v) => v.toFixed(1));
  };
  const [dx, dz] = P.drop[0], pad = [P.c[0] + dx, 0, P.c[1] + dz]; pad[1] = ground(pad[0], pad[2]) + 0.1;
  const mid = [(H.x0 + H.x1) / 2, hy(), 30];
  assert.equal(go(pad, mid, 40), true, 'pad -> into the hangar');
  assert.equal(go(mid, [-112, 0, 0.5], 40), true, 'hangar -> the yard, under the crane');
});
