// node --test tests/bi_wreck.test.mjs : Battle Island's RETURN TO SENDER (shared/bi_wreck.js). every model is built to
// exactly its boxes; the ship stands where it should (aground, listing, its deck at the right height) with all its boxes
// `still`; you wade in through the tear, stand on the sand in the hold, climb its ladder to the deck, climb the outside
// ladder to the bridge wing and walk into the wheelhouse; a mech-sized body fits through the tear; a bot steering by the
// walk graph gets from the drop pad into the hold; walk into an open box on the beach
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { MAPS } from '../shared/map.js';
import '../shared/royale.js';
import { navSteer } from '../shared/nav.js';
import { movePlayer } from '../shared/physics.js';
import { PLAN, KILL_Y } from '../shared/battleisland.js';
import { RS, SPILL, BOX40 } from '../shared/bi_wreck.js';

const m = MAPS.battleisland, T = m.boxes.terrain;
const ground = (x, z) => T.at(x, z);
const [CX, CZ] = RS.c, c = Math.cos(RS.list * Math.PI / 180), s = Math.sin(RS.list * Math.PI / 180);
const W = (x, y, z) => [CX + x, RS.ky + y * c - z * s, CZ + z * c + y * s]; // the ship's frame -> the world
const sim = (pos, vel, g) => { vel[1] -= 26 / 30; return !!movePlayer(pos, vel, 1 / 30, m.boxes, g).ground; };
const metaOf = (id) => { const buf = fs.readFileSync(new URL(`../public/models/p_${id}.glb`, import.meta.url)), len = buf.readUInt32LE(12); const gl = JSON.parse(buf.slice(20, 20 + len).toString('utf8')); return JSON.parse(gl.nodes.find((n) => n.extras && n.extras.jf).extras.jf); };
// walk toward each waypoint in turn at a run; returns where you ended up
const walk = (from, pts, secs = 20, speed = 6) => {
  const pos = from.slice(), vel = [0, 0, 0]; let g = true, k = 0;
  for (let t = 0; t < secs && k < pts.length; t += 1 / 30) {
    const [gx, gz] = pts[k], dx = gx - pos[0], dz = gz - pos[2], l = Math.hypot(dx, dz);
    if (l < 0.35) { k++; continue; }
    vel[0] = dx / l * speed; vel[2] = dz / l * speed; g = sim(pos, vel, g);
    if (pos[1] < KILL_Y) return pos;
  }
  for (let t = 0; t < 0.5; t += 1 / 30) { vel[0] = vel[2] = 0; g = sim(pos, vel, g); } // (settle)
  return pos;
};

test('Return to Sender: every model is built to exactly its boxes, every box is `still`', () => {
  for (const id of ['wreck_ship', 'wreck_box', 'wreck_burst', 'wreck_boat', 'wreck_hatch']) {
    const ps = m.boxes.props.filter((q) => q.id === id), meta = metaOf(id);
    assert.ok(ps.length, id + ' is placed');
    for (const p of ps) for (let i = 0; i < 3; i++) {
      assert.ok(Math.abs(meta.box[0][i] - p.lo[i]) < 0.01, `${id} lo[${i}] ${meta.box[0][i]} vs ${p.lo[i]}`);
      assert.ok(Math.abs(meta.box[1][i] - p.hi[i]) < 0.01, `${id} hi[${i}] ${meta.box[1][i]} vs ${p.hi[i]}`);
    }
    const mine = m.boxes.filter((b) => b.pv === id);
    assert.ok(mine.length && mine.every((b) => b.still), id + ': its boxes are tagged and still');
  }
  assert.equal(m.boxes.props.filter((q) => q.id === 'wreck_ship').length, 1);
  assert.ok(m.boxes.filter((b) => b.pv === 'wreck_ship').length > 200, 'the ship is a real set of boxes');
});

test('Return to Sender: the ship is aground off the point, listing to the beach; the spill lies on the sand', () => {
  const p = m.boxes.props.find((q) => q.id === 'wreck_ship');
  assert.deepEqual(p.a, [CX, RS.ky, CZ]);
  const P = PLAN.pois.find((q) => q.id === 'wreck');
  assert.ok(Math.hypot(CX - P.c[0], CZ - P.c[1]) < P.r, 'in the POI');
  // the main deck: the sea side higher than the beach side (the list), both well above the water
  const deckAt = (z) => { const [x, y, wz] = W(10, RS.D + 1.5, z); let best = -1e9; for (const b of m.boxes) if (b.pv === 'wreck_ship' && x > b.min[0] && x < b.max[0] && wz > b.min[2] && wz < b.max[2] && b.max[1] < y && b.max[1] > best) best = b.max[1]; return best; };
  const sea = deckAt(-6.2), beach = deckAt(6.2);
  assert.ok(sea > 6 && beach > 5.5 && sea - beach > 0.6 && sea - beach < 1.5, `listing: sea side deck ${sea.toFixed(2)}, beach side ${beach.toFixed(2)}`);
  // the walk-in boxes, the boat, the hatch cover: their floors at the sand (not floating, not buried)
  for (const [id, x, z] of SPILL) { const q = m.boxes.props.find((r) => r.id === id && Math.abs(r.a[0] - x) < 0.01 && Math.abs(r.a[2] - z) < 0.01); assert.ok(q, id + ' placed at ' + x + ',' + z); assert.ok(Math.abs(q.a[1] - ground(x, z)) < 0.6, `${id} at ${x},${z}: foot ${q.a[1].toFixed(2)}, sand ${ground(x, z).toFixed(2)}`); }
  // the drop pad stays clear (the beach in front of the tear)
  const [dx, dz, r] = P.drop[0], px = P.c[0] + dx, pz = P.c[1] + dz;
  for (const b of m.boxes) if (/^wreck/.test(b.pv || '') || b.pv === 'container') assert.ok(b.max[0] < px - r || b.min[0] > px + r || b.max[2] < pz - r || b.min[2] > pz + r || b.min[1] > 40, `the pad at ${px},${pz} is clear (${b.pv} at ${b.min.map((v) => v.toFixed(1))})`);
});

test('Return to Sender: wade in through the tear onto the sand in the hold, climb the hold ladder to the deck', () => {
  const [t0, t1] = RS.hole, xm = (t0 + t1) / 2, hx = CX + xm;
  const out = [hx, ground(hx, CZ + 11) + 0.05, CZ + 11];
  assert.ok(out[1] > KILL_Y + 0.5, 'the shallows outside the tear are wadeable');
  const inside = walk(out, [[hx, CZ + 2]]);
  assert.ok(Math.abs(inside[2] - (CZ + 2)) < 0.5 && Math.abs(inside[1] - RS.sand) < 0.2, `in the hold, on the sand: ${inside.map((v) => v.toFixed(2))}`);
  // the ladder: from its foot up to the deck at the hatch's aft end, then out onto the deck
  const [lx0, lx1, lz0, lz1] = RS.ladder, lz = (lz0 + lz1) / 2;
  const top = walk(inside, [[CX + lx0 - 1.5, W(0, 0, lz)[2]], [CX + lx0 + 0.5, W(0, 2, lz)[2]], [CX + lx1 + 1.2, W(0, RS.D, lz)[2]]], 25, 4);
  const deck = W(lx1 + 1.2, RS.D, lz)[1];
  assert.ok(Math.abs(top[1] - deck) < 0.2 && top[0] > CX + lx1, `up the ladder onto the deck (${top.map((v) => v.toFixed(2))}, the deck at ${deck.toFixed(2)})`);
});

test('Return to Sender: up the outside ladder to the bridge wing, into the wheelhouse through its door', () => {
  const [sx0, sx1, sz0, sz1] = RS.stair, zl = (sz0 + sz1) / 2, [dA, , dW] = RS.decks, [wd0, wd1] = RS.wingDoor;
  const start = W(sx0 + 1.2, dA + 0.05, zl);
  const st = walk(start, [[CX + sx0 + 0.3, W(0, dA, zl)[2]], [CX + sx1 - 0.6, W(0, dW, zl)[2]]], 25, 4);
  assert.ok(Math.abs(st[1] - W(sx1 - 0.6, dW, zl)[1]) < 0.25, `on the beach wing (${st.map((v) => v.toFixed(2))})`);
  const wx = CX + (wd0 + wd1) / 2;
  const inn = walk(st, [[wx, W(0, dW, 6.4)[2]], [wx, W(0, dW, 2)[2]]], 15, 3);
  assert.ok(Math.abs(inn[2] - W(0, dW, 2)[2]) < 0.5 && Math.abs(inn[1] - W(0, dW, 2)[1]) < 0.25, `inside the wheelhouse (${inn.map((v) => v.toFixed(2))})`);
});

test('Return to Sender: a mech fits through the tear (6 m wide, open to the sky) and stands in the hold', () => {
  const [t0, t1] = RS.hole, xm = CX + (t0 + t1) / 2, hw = 2.0, h = 6.0; // (a 5-6 m mech, arms and all, with room)
  for (let z = CZ + 12; z > CZ + 1; z -= 0.25) {
    const y = Math.max(ground(xm, z), RS.sand) + 0.05;
    const hit = m.boxes.find((b) => !b.ter && b.max[1] > y + 0.6 && b.min[1] < y + h && b.max[0] > xm - hw && b.min[0] < xm + hw && b.max[2] > z - hw && b.min[2] < z + hw);
    assert.ok(!hit, `a mech at z ${z.toFixed(2)} hits ${hit && hit.mat} ${hit && hit.min.map((v) => v.toFixed(1))}`);
  }
});

test('Return to Sender: a bot steering by the walk graph gets from the drop pad into the hold', () => {
  const P = PLAN.pois.find((q) => q.id === 'wreck'), [dx, dz] = P.drop[0], from = [P.c[0] + dx, 0, P.c[1] + dz];
  from[1] = ground(from[0], from[2]) + 0.1;
  const goal = [CX + (RS.hole[0] + RS.hole[1]) / 2, RS.sand, CZ];
  const pos = from.slice(), vel = [0, 0, 0], st = {}; let g = true, ok = false;
  for (let t = 0; t < 40; t += 1 / 30) {
    const sv = navSteer(m.graph, st, pos, goal, t * 1000), l = Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) || 1;
    const [ax, az] = sv ? sv : [(goal[0] - pos[0]) / l, (goal[2] - pos[2]) / l];
    if (sv && sv[2] && g) vel[1] = 8;
    vel[0] = ax * 7; vel[2] = az * 7; g = sim(pos, vel, g);
    if (Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) < 2.5 && Math.abs(pos[1] - RS.sand) < 0.4) { ok = true; break; }
  }
  assert.ok(ok, 'the bot got into the hold: ended at ' + pos.map((v) => v.toFixed(1)));
});

test('Return to Sender: walk into an open box on the beach (in at its doors, stopped by its back wall)', () => {
  const [, x, z, q] = SPILL[0], p = m.boxes.props.find((r) => r.id === 'wreck_box' && r.a[0] === x && r.a[2] === z);
  const dir = [[1, 0], [0, -1], [-1, 0], [0, 1]][q], X = BOX40.L / 2; // (local +x: deeper in)
  const door = [x - dir[0] * (X + 2), 0, z - dir[1] * (X + 2)]; door[1] = ground(door[0], door[2]) + 0.1;
  const deep = [x + dir[0] * (X + 3), z + dir[1] * (X + 3)];
  const end = walk(door, [deep], 8, 5);
  const along = (end[0] - x) * dir[0] + (end[2] - z) * dir[1];
  assert.ok(along > X - 1.2 && along < X - 0.2, `stopped at the back wall: ${along.toFixed(2)} m along (the wall at ${X - BOX40.t})`);
  assert.ok(Math.abs(end[1] - (p.a[1] + BOX40.fl)) < 0.15, `standing on its floor (${end[1].toFixed(2)} vs ${(p.a[1] + BOX40.fl).toFixed(2)})`);
});
