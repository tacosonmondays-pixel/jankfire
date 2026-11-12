// node tests/mapedits.test.mjs : the owner's shipped map edits (shared/mapedits) are valid and still fit their maps.
// fails when a map was remodelled under an edit: re-export the edit from the editor (or drop the stale ops)
import assert from 'node:assert/strict';
import { MAPS } from '../shared/map.js';
import { EDITS } from '../shared/mapedits/index.js';
import { validEdits } from '../shared/mapedit.js';
const { EDIT_REPORT } = await import('../shared/mapedits/apply.js');
let n = 0;
for (const [id, e] of Object.entries(EDITS)) {
  assert.ok(validEdits(e), id + ': a valid edit file'); assert.equal(e.map, id, id + ': filed under its own map');
  assert.ok(MAPS[id], id + ': a real map');
  assert.equal(EDIT_REPORT[id].stale, 0, `${id}: ${EDIT_REPORT[id].stale} edits no longer fit the map`);
  n++;
}
console.log(`ok ${n} shipped map edit file(s)`);
