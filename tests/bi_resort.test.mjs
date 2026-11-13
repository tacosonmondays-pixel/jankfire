// node --test tests/bi_resort.test.mjs : Battle Island's THE ALL-INCLUSIVE (shared/bi_resort.js). every model is built to
// exactly its boxes; everything stands on the ground (or the deck, the jetty) with its boxes `still`; in through the
// lobby's glass front and out of its back doors; up the stair tower, floor by floor, onto the roof; along a balcony
// walk; down into the pool and up onto the swim-up bar's stools side; the drop pad stays clear; a bot steering by the
// walk graph gets from the pad to the pool deck and into the lobby
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { MAPS } from '../shared/map.js';
import '../shared/royale.js';
import { navSteer } from '../shared/nav.js';
import { movePlayer } from '../shared/physics.js';
import { PLAN, KILL_Y } from '../shared/battleisland.js';
import { AI } from '../shared/bi_resort.js';

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
const H = AI.hotel, Tw = AI.tower, hy = () => m.boxes.props.find((q) => q.id === 'ai_hotel').a[1];
const IDS = ['ai_hotel', 'ai_canopy', 'ai_deck', 'ai_cabana', 'ai_lounger', 'ai_umbrella', 'ai_lifeguard', 'ai_jetty', 'ai_jetski', 'ai_sign'];
const LIFTED = new Set(['ai_canopy', 'ai_deck', 'ai_lounger', 'ai_umbrella', 'ai_jetty', 'ai_jetski']); // (on the deck, the jetty, afloat)

test('The All-Inclusive: every model is built to exactly its boxes, every box is `still` and stands on the ground', () => {
  for (const id of IDS) {
    const ps = m.boxes.props.filter((q) => q.id === id), meta = metaOf(id);
    assert.ok(ps.length, id + ' is placed');
    for (const p of ps) {
      for (let i = 0; i < 3; i++) {
        assert.ok(Math.abs(meta.box[0][i] - p.lo[i]) < 0.01, `${id} lo[${i}] ${meta.box[0][i]} vs ${p.lo[i]}`);
        assert.ok(Math.abs(meta.box[1][i] - p.hi[i]) < 0.01, `${id} hi[${i}] ${meta.box[1][i]} vs ${p.hi[i]}`);
      }
      if (!LIFTED.has(id)) assert.ok(Math.abs(p.a[1] - ground(p.a[0], p.a[2])) < 1.0, `${id} at ${p.a.map((v) => v.toFixed(1))} stands on the ground (${ground(p.a[0], p.a[2]).toFixed(2)})`);
    }
    const mine = m.boxes.filter((b) => b.pv === id);
    assert.ok(mine.length && mine.every((b) => b.still), id + ': its boxes are tagged and still');
  }
  assert.equal(m.boxes.props.filter((q) => q.id === 'ai_cabana').length, AI.cabanas.length);
  assert.equal(m.boxes.props.filter((q) => q.id === 'ai_lounger').length, AI.loungers[0].length + AI.loungers[1].length);
});

test('The All-Inclusive: in through the lobby\'s glass front, past the desk, out of the back doors', () => {
  const y0 = hy(), fx = (H.front[0] + H.front[1]) / 2, bx = (H.back[0] + H.back[1]) / 2;
  const inn = walk([fx, ground(fx, H.z1 + 5) + 0.2, H.z1 + 5], [[fx, H.z1 - 4]], 10, 5);
  assert.ok(inn[2] < H.z1 - 3 && Math.abs(inn[1] - (y0 + 0.12)) < 0.2, `in the lobby: ${inn.map((v) => v.toFixed(2))}`);
  const out = walk(inn, [[bx, H.z0 + 2], [bx, H.z0 - 3]], 10, 5);
  assert.ok(out[2] < H.z0 - 2, `out of the back: ${out.map((v) => v.toFixed(2))}`);
  const glass = walk([H.front[0] - 4, inn[1], H.z1 + 3], [[H.front[0] - 4, H.z1 - 3]], 4, 5); // (beside the doors: the glass stops you)
  assert.ok(glass[2] > H.z1 - 0.2, `the glass front stops you: ${glass.map((v) => v.toFixed(2))}`);
});

test('The All-Inclusive: up the stair tower floor by floor onto the roof; along a balcony walk from its landing', () => {
  const y0 = hy(), top = y0 + H.g + H.floors * H.fh + 0.3, xw = Tw.x0 + Tw.w / 2, xe = Tw.x1 - Tw.w / 2, [r0, r1] = Tw.run;
  const pts = [[xw, Tw.z1 - 1.0]];
  for (let k = 0; k <= H.floors; k++) pts.push([xw, r0 - 1.0], [xe, r0 - 1.0], [xe, r1 + 1.6], [xw, r1 + 1.6]); // (north up the west flight, across, south up the east one)
  pts.push([Tw.x0 - 6, r1 + 1.4]); // (west off the top landing through the parapet's gap onto the roof)
  const roof = walk([xw, y0 + 0.2, Tw.z1 + 1.5], pts, 90, 4);
  assert.ok(Math.abs(roof[1] - top) < 0.15 && roof[0] < Tw.x0 - 4, `on the roof: ${roof.map((v) => v.toFixed(2))} (roof at ${top.toFixed(2)})`);
  // the second floor's balcony: up one pair of flights, then west along the walk
  const bal = walk([xw, y0 + 0.2, Tw.z1 + 1.5], [[xw, Tw.z1 - 1.0], [xw, r0 - 1.0], [xe, r0 - 1.0], [xe, r1 + 1.6], [Tw.x0 - 2, H.z1 + H.bal / 2], [H.x0 + 10, H.z1 + H.bal / 2]], 30, 4);
  assert.ok(Math.abs(bal[1] - (y0 + H.g)) < 0.15 && bal[0] < H.x0 + 11, `along the balcony: ${bal.map((v) => v.toFixed(2))}`);
});

test('The All-Inclusive: into the pool and out again; the canopy clears the drive; the drop pad stays clear', () => {
  const D = AI.deck, P = AI.pool, y0 = hy(), dz = (P.z0 + P.z1) / 2;
  const sw = walk([D.x0 - 2, ground(D.x0 - 2, dz) + 0.2, dz], [[P.x0 + 2.5, dz]], 8, 5); // (up the step, onto the deck, down into the pool)
  assert.ok(sw[0] > P.x0 + 2 && sw[1] < y0 + D.h - 0.2, `in the pool: ${sw.map((v) => v.toFixed(2))}`);
  const C = AI.canopy, cx = (C.x0 + C.x1) / 2; // (a mech, 4 x 6 m, drives in under the porte-cochere, up to the balconies)
  for (let z = C.z1 + 4; z >= H.z1 + H.bal + 2.05; z -= 0.5) {
    const y = Math.max(ground(cx, z), y0) + 0.05;
    const hit = m.boxes.find((b) => !b.ter && b.max[1] > y + 0.6 && b.min[1] < y + 6 && b.max[0] > cx - 2 && b.min[0] < cx + 2 && b.max[2] > z - 2 && b.min[2] < z + 2); 
    assert.ok(!hit, `a mech under the canopy at z ${z} hits ${hit && hit.pv}`);
  }
  const R = PLAN.pois.find((q) => q.id === 'resort');
  for (const [dx, dz2, r] of R.drop) {
    const px = R.c[0] + dx, pz = R.c[1] + dz2;
    for (const b of m.boxes) if (/^ai_/.test(b.pv || '')) assert.ok(b.max[0] < px - r || b.min[0] > px + r || b.max[2] < pz - r || b.min[2] > pz + r, `the pad at ${px},${pz} is clear (${b.pv})`);
  }
});

test('The All-Inclusive: a bot gets from the drop pad onto the pool deck and into the lobby', () => {
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
  const R = PLAN.pois.find((q) => q.id === 'resort'), [dx, dz] = R.drop[0], pad = [R.c[0] + dx, 0, R.c[1] + dz]; pad[1] = ground(pad[0], pad[2]) + 0.1;
  const deck = [AI.deck.x0 + 1.2, hy() + AI.deck.h, (AI.pool.z0 + AI.pool.z1) / 2];
  assert.equal(go(pad, deck, 40), true, 'pad -> the pool deck');
  const lobby = [(H.front[0] + H.front[1]) / 2, hy(), H.z1 - 4];
  assert.equal(go(deck, lobby, 40), true, 'pool deck -> the lobby');
});
