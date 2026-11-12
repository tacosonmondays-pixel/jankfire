// royale ground spots: the flat city keeps its street-level rule; shaped ground (the island) uses the terrain surface
// and never the sea. (bots land, loot and the zone's rings go on these)
import test from 'node:test';
import assert from 'node:assert/strict';
import '../shared/royale.js';
import { MAPS } from '../shared/map.js';
import { onGround, groundSpots } from '../server/royale.js';

test('flat maps: street level only (Jankburg as before)', () => {
  const m = { boxes: Object.assign([], { terrain: { at: () => 5 } }) }; // (Jankburg has shaped ground too, but no sea: the old rule)
  assert.equal(onGround(m, [0, 0.2, 0]), true);
  assert.equal(onGround(m, [0, 1.59, 0]), true);
  assert.equal(onGround(m, [0, 5, 0]), false); // a roof (or a hill: as before)
  const g = groundSpots(MAPS.jankburg);
  assert.ok(g.length > 100 && g.every((s) => s.p[1] < 1.6));
});
test('shaped ground: on the terrain surface, above the sea', () => {
  const at = (x) => (x < 0 ? -3 : x * 0.5); // the sea floor west of x = 0, a hill rising east
  const m = { boxes: Object.assign([], { terrain: { at } }), seaY: -0.25 };
  assert.equal(onGround(m, [10, 5, 0]), true); // on the hillside, 5 m up
  assert.equal(onGround(m, [10, 5.25, 0]), true); // (within 0.3)
  assert.equal(onGround(m, [10, 9, 0]), false); // on something above the hill (a roof)
  assert.equal(onGround(m, [-10, -3, 0]), false); // the sea bed
  assert.equal(onGround(m, [0.2, 0.1, 0]), true); // the beach
});
