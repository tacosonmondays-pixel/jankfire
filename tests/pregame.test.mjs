// node --test tests/pregame.test.mjs : the pre-game deck (shared/pregame.js) on every map a mode lobby can pick:
// past the play area's edge, nothing of the map in its way, every spawn lands on the deck (real physics), off the deck
// is caught, the board ranks the best of whoever's there, and the weekly look rotation stays in range
import test from 'node:test';
import assert from 'node:assert/strict';
import '../shared/royale.js';
import '../shared/zombies.js';
import { MAPS, MAP_ORDER } from '../shared/map.js';
import { mapsFor } from '../shared/modes.js';
import { padFor, offPad, boardRows, lookFor, LOOKS, PREGAME, LAYOUT, PODIUMS, SCREEN } from '../shared/pregame.js';
import fs from 'node:fs';
import { movePlayer } from '../shared/physics.js';

const ids = [...new Set(['bomb', 'br', 'zm'].flatMap((g) => mapsFor(g, MAPS, MAP_ORDER)))];
test('the deck sits clear of every lobby map and holds its spawns', () => {
  assert.ok(ids.length >= 8, 'lobby maps: ' + ids.join(','));
  for (const id of ids) {
    const m = MAPS[id], pad = padFor(m);
    assert.equal(padFor(m), pad, id + ': cached');
    const edge = m.bounds ? m.bounds[3] : Math.max(...m.boxes.filter((b) => b.max[2] - b.min[2] < 400 && b.max[0] - b.min[0] < 400).map((b) => b.max[2]));
    assert.ok(pad.lo[2] >= edge + PREGAME.gap - 0.5, `${id}: past the edge (${pad.lo[2]} vs ${edge})`);
    assert.ok(pad.c[1] > m.killY + 20, id + ': well above killY');
    const all = m.boxes.concat(pad.boxes); all.terrain = m.boxes.terrain;
    for (const s of pad.spawns) {
      assert.ok(!offPad(pad, s), id + ': spawn on the deck');
      const p = [s[0], s[1] + 0.5, s[2]], v = [0, 0, 0];
      for (let i = 0; i < 120; i++) { v[1] -= 20 / 60; movePlayer(p, v, 1 / 60, all, true); }
      assert.ok(Math.abs(p[1] - s[1]) < 0.05, `${id}: spawn ${s.map(Math.round)} settles on the floor (${p[1].toFixed(2)})`);
    }
    assert.ok(offPad(pad, [pad.c[0], pad.c[1] - 10, pad.c[2]]) && offPad(pad, [pad.c[0] + 40, pad.c[1], pad.c[2]]) && offPad(pad, [pad.c[0], m.killY - 5, pad.c[2]]), id + ': off the deck is caught');
  }
});
test('the board: ranked first, then unranked people, bots last; junk ignored', () => {
  const ps = [
    { id: 1, name: 'guest', level: 9 },
    { id: 2, name: 'ace', acct: {}, inv: { ms: { bomb: { rw: 40 }, zm: { round: 12 } } }, level: 5 },
    { id: 3, name: 'mid', acct: {}, inv: { ms: { bomb: { rw: 10 } } }, msd: { bomb: { rw: 35 } }, level: 2 },
    { id: 4, name: 'Bot [bot]', isBot: true, level: 50, inv: { ms: { bomb: { rw: 999 } } } },
    { id: 6, name: 'hax', acct: {}, inv: { ms: { bomb: { rw: 'lots' }, zm: { round: Infinity } } }, level: 1 },
    { id: 7, name: 'zmguy', acct: {}, inv: { ms: { zm: { round: 8 } } }, msd: { zm: { round: 15 } }, level: 1 },
  ];
  assert.deepEqual(boardRows('bomb', ps).map((r) => [r.name, r.v]), [['mid', 45], ['ace', 40], ['guest', null]]);
  assert.deepEqual(boardRows('zm', ps).map((r) => [r.name, r.v]), [['zmguy', 15], ['ace', 12], ['guest', null]]); // (highest round: the best, not a sum)
  assert.deepEqual(boardRows('br', [ps[3], ps[0]]).map((r) => r.name), ['guest', 'Bot [bot]']);
  assert.deepEqual(boardRows('__proto__', ps).map((r) => r.v), [null, null, null]);
});
test('the look of the week is always a real look', () => {
  for (let d = 0; d < 400; d += 3) assert.ok(LOOKS.some((l) => l.id === lookFor(Date.UTC(2026, 0, 1) + d * 864e5)));
});
test('every look has its Blender deck, built on the same boxes, podiums and screen as the game', () => {
  for (const L of LOOKS) {
    const f = new URL(`../public/models/x_lobby_${L.id}.glb`, import.meta.url), buf = fs.readFileSync(f);
    assert.equal(buf.readUInt32LE(0), 0x46546c67, 'a glb');
    const json = JSON.parse(buf.subarray(20, 20 + buf.readUInt32LE(12)).toString('utf8'));
    const root = json.nodes.find((n) => n.extras && n.extras.jf), meta = JSON.parse(root.extras.jf);
    assert.equal(meta.id, L.id);
    assert.deepEqual(meta.boxes, LAYOUT, 'the model was built on shared/pregame.js LAYOUT');
    assert.deepEqual(meta.podiums, PODIUMS); assert.deepEqual(meta.screen, SCREEN);
    const names = new Set(json.nodes.map((n) => n.name));
    for (const n of ['screen', ...meta.fans, ...meta.balloons]) assert.ok(names.has(n), 'node ' + n);
    assert.ok(json.materials.length <= 16, 'draw calls: ' + json.materials.length + ' materials');
  }
});
