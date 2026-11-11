// costumes: one table for bots and players, only real pieces, and the server's validLook still decides what's worn
import test from 'node:test';
import assert from 'node:assert/strict';
import { COSTUMES, COSTUME_IDS, costumeFor, costumeLook, wearing } from '../shared/costumes.js';
import { validLook, TOPS, BOTTOMS, HAIRS, ACCESSORIES, SKIN_TONES, HAIR_COLORS, CLOTH_COLORS, ACHIEVEMENTS, LEGACY_ACHS, DEFAULT_LOOK } from '../shared/looks.js';
import { PRESETS, botLook } from '../server/botlook.js';

const ALL = new Set([...Object.keys(ACHIEVEMENTS), ...Object.keys(LEGACY_ACHS)]), NONE = new Set();
const CAT = { top: TOPS, bottom: BOTTOMS, hair: HAIRS, head: ACCESSORIES.head, face: ACCESSORIES.face, back: ACCESSORIES.back, skin: SKIN_TONES, hairColor: HAIR_COLORS, topColor: CLOTH_COLORS, bottomColor: CLOTH_COLORS };
test('every costume has a name, a line, and only pieces and colours that exist', () => {
  assert.ok(COSTUME_IDS.length >= 9);
  for (const [id, C] of Object.entries(COSTUMES)) {
    assert.ok(C.name && C.desc && C.desc.length < 90, id);
    for (const [k, v] of Object.entries(C.look)) for (const x of [].concat(v)) assert.ok(Array.isArray(CAT[k]) ? CAT[k].includes(x) : !!CAT[k][x], `${id}.${k} = ${x}`);
  }
});
test('the bots dress from the same table', () => {
  for (const id of COSTUME_IDS) assert.equal(PRESETS[id], COSTUMES[id].look);
  const b = botLook(12345, 1);
  assert.ok(COSTUME_IDS.includes(b.preset));
});
test('with every achievement: every costume goes on whole and survives the server check', () => {
  for (const id of COSTUME_IDS) {
    const f = costumeFor(id, ALL), l = costumeLook(id, ALL);
    assert.ok(!f.locked && !f.missing.length, id);
    const worn = validLook({ ...DEFAULT_LOOK, ...l }, ALL);
    for (const [k, v] of Object.entries(l)) assert.equal(worn[k], v, `${id}.${k}`);
    assert.ok(wearing(id, worn, ALL), id);
  }
});
test('with no achievements: locked clothes lock the costume, unearned accessories are left off, nothing locked gets through', () => {
  const locked = COSTUME_IDS.filter((id) => costumeFor(id, NONE).locked);
  assert.deepEqual(locked.sort(), ['maid', 'nightshift']);
  assert.equal(costumeLook('maid', NONE), null);
  assert.match(costumeFor('maid', NONE).needs[0].ach, /Board Approved/);
  assert.match(costumeFor('nightshift', NONE).needs[0].ach, /Smarty Pants/);
  for (const id of COSTUME_IDS.filter((x) => !locked.includes(x))) {
    for (let i = 0; i < 20; i++) {
      const l = costumeLook(id, NONE, (a) => a[(Math.random() * a.length) | 0]);
      assert.deepEqual(validLook({ ...DEFAULT_LOOK, ...l }, NONE), { ...validLook(DEFAULT_LOOK, NONE), ...l }, id); // the server changes nothing: no locked piece was in it
    }
  }
  const rk = costumeFor('ratking', NONE);
  assert.deepEqual(rk.missing.map((m) => m.slot), ['head']); // no crown yet
  assert.equal(costumeLook('ratking', NONE).head, 'none');
});
test('a forged look claiming a locked costume is stripped by the server', () => {
  const forged = validLook({ ...DEFAULT_LOOK, ...costumeLook('maid', ALL) }, NONE);
  assert.notEqual(forged.top, 'maid');
});
