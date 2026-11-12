// battle island squads with parties (server/isleparty.js): a party lands together, a big one spills over in chunks,
// solo players and bots fill the gaps, and with no parties it's the old fill order. late boarders join a partymate.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { islePlan, islePartySquad } from '../server/isleparty.js';

let id = 0;
const P = (party, isBot = false) => ({ id: ++id, party, isBot });
const sqs = (plan, ps) => ps.map((p) => plan.get(p));

test('no parties: the old fill (1,1,1,2,2,2,...)', () => {
  const l = [P(), P(), P(), P(), P(), P(null, true), P(null, true)];
  assert.deepEqual(sqs(islePlan(l, 3), l), [1, 1, 1, 2, 2, 2, 3]);
});
test('two parties of 2 land in their own squads, solos fill around them', () => {
  const s1 = P(), a1 = P('p1'), s2 = P(), b1 = P('p2'), a2 = P('p1'), b2 = P('p2'), bot = P(null, true), bot2 = P(null, true);
  const plan = islePlan([s1, a1, s2, b1, a2, b2, bot, bot2], 3);
  assert.equal(plan.get(a1), plan.get(a2)); assert.equal(plan.get(b1), plan.get(b2)); assert.notEqual(plan.get(a1), plan.get(b1));
  const n = new Map(); for (const v of plan.values()) n.set(v, (n.get(v) || 0) + 1);
  assert.ok([...n.values()].every((c) => c <= 3), 'never more than a squad');
  assert.equal(n.size, 3, '8 people in squads of 3 = 3 squads');
});
test('a party of 5 with squads of 3 spills into a second squad (3 + 2)', () => {
  const ps = [1, 2, 3, 4, 5].map(() => P('big')), solo = P();
  const plan = islePlan([solo, ...ps], 3);
  assert.deepEqual(sqs(plan, ps), [1, 1, 1, 2, 2]); assert.equal(plan.get(solo), 2);
});
test('bots never count as a party, bad party values are ignored', () => {
  const b1 = P('p9', true), b2 = P('p9', true), h = P(5), h2 = P(5);
  const plan = islePlan([h, b1, h2, b2], 2);
  assert.deepEqual(sqs(plan, [h, b1, h2, b2]), [1, 1, 2, 2]);
});
const U = (o) => ({ alive: true, br: {}, ...o });
const R = (list, tickets) => ({ fighters: () => list, isleIn: (o) => !!o.sq, isleUp: () => true, br: { isle: { sqOut: new Map() } }, tickets });
test('late boarder joins a partymate whose squad has room (not a full or out one)', () => {
  const mate = U({ id: 1, party: 'p1', sq: 2 }), x = U({ id: 2, sq: 2 }), y = U({ id: 3, sq: 1 }), me = U({ id: 4, party: 'p1' });
  const room = R([mate, x, y, me]);
  assert.equal(islePartySquad(room, me, 3), 2);
  assert.equal(islePartySquad(room, me, 2), 0, "mate's squad full: the usual pick (only you left to place)");
  room.br.isle.sqOut.set(2, 1); assert.equal(islePartySquad(room, me, 3), 0, 'squad out: the usual pick');
  assert.equal(islePartySquad(room, U({ id: 5 }), 3), 0, 'no party: the usual pick');
});
test('the first of a party in: a squad with room for all of them (counting unused tickets), else a new one', () => {
  const a = U({ id: 1, sq: 1 }), b = U({ id: 2, sq: 1 }), c = U({ id: 3, sq: 2 }), lead = U({ id: 4, party: 'p7' });
  const tk = new Map([['t1', { party: 'p7', until: Date.now() + 9e4 }], ['t2', { party: 'p3', until: Date.now() + 9e4 }]]);
  assert.equal(islePartySquad(R([a, b, c, lead], tk), lead, 3), 2, 'squad 1 has 1 seat, squad 2 has 2: squad 2');
  tk.set('t3', { party: 'p7', until: Date.now() + 9e4 });
  assert.equal(islePartySquad(R([a, b, c, lead], tk), lead, 3), -1, 'a party of 3 coming: a new squad');
  assert.equal(islePartySquad(R([a, b, c, lead], new Map()), lead, 3), 0, 'a party of one: the usual pick');
  tk.set('t1', { party: 'p7', until: Date.now() - 1 }); tk.delete('t3');
  assert.equal(islePartySquad(R([a, b, c, lead], tk), lead, 3), 0, 'stale tickets do not count');
});
