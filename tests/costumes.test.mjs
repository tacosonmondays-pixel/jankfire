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

// the first batch of new costumes (Lifeguard, Hot Dog Guy, Budget Wizard, Referee): free, whole, and every new piece is
// really built by the client (a top clothes.js doesn't know gets no shirt; an accessory models.js doesn't know is left off)
import { readFileSync } from 'node:fs';
const NEW = { lifeguard: 'Lifeguard', hotdog: 'Hot Dog Guy', wizard: 'Budget Wizard', referee: 'Referee', // batch 1
  grandma: 'Grandma', astronaut: 'Homemade Astronaut', tourist: 'Tourist', chef: 'Chef', // batch 2
  gymbro: 'Gym Bro', pyjamas: 'Pyjamas' }; // batch 3 (the free ones)
const PIECES = { top: ['lifetank', 'hotdog', 'robe', 'refshirt', 'cardigan', 'spacesuit', 'hawaiian', 'chef', 'stringer', 'pjtop'], bottom: ['cargo', 'checks', 'pjpants'], head: ['strawhat', 'wizhat', 'boxhelmet', 'chefhat', 'sweatband', 'nightcap'], face: ['sunscreen', 'fakebeard', 'readers'], back: ['float', 'handbag', 'bottlepack', 'camera', 'shaker', 'teddy'] };
const src = (f) => readFileSync(new URL(`../${f}`, import.meta.url), 'utf8');
test('the new costumes (batches 1 and 2) are free for everyone and go on whole', () => {
  for (const [id, name] of Object.entries(NEW)) {
    assert.equal(COSTUMES[id].name, name);
    const f = costumeFor(id, NONE);
    assert.ok(!f.locked && !f.missing.length, id);
    for (let i = 0; i < 20; i++) {
      const l = costumeLook(id, NONE, (a) => a[(Math.random() * a.length) | 0]), worn = validLook({ ...DEFAULT_LOOK, ...l }, NONE);
      for (const [k, v] of Object.entries(l)) assert.equal(worn[k], v, `${id}.${k}`);
      assert.ok(wearing(id, worn, NONE), id);
    }
  }
});
test('the new pieces are free, named, and in the normal pickers', () => {
  const cat = { top: TOPS, bottom: BOTTOMS, head: ACCESSORIES.head, face: ACCESSORIES.face, back: ACCESSORIES.back };
  for (const [slot, ids] of Object.entries(PIECES)) for (const id of ids) {
    assert.ok(cat[slot][id] && cat[slot][id].name && !cat[slot][id].ach, `${slot}.${id}`);
    assert.equal(validLook({ ...DEFAULT_LOOK, [slot]: id }, NONE)[slot], id, `${slot}.${id}`);
  }
});
test('every top is cut by clothes.js, the new ones fitted by the vest; sleeved ones have first-person sleeves; every accessory is built', () => {
  const clothes = src('public/js/clothes.js'), models = src('public/js/models.js'), econ = src('public/js/econ3d.js'), hands = src('public/js/hands.js');
  const block = (s, from) => s.slice(s.indexOf(from), s.indexOf('\n};', s.indexOf(from)));
  const cut = block(clothes, 'const TOPS = {'), known = econ.match(/const KNOWN_TOPS = new Set\(\[([^\]]*)\]\)/)[1], sleeves = hands.match(/const SLEEVES = \{([^}]*)\}/)[1];
  for (const id of Object.keys(TOPS)) {
    if (id !== 'none') assert.match(cut, new RegExp(`\\n  ${id}: \\{ cut: `), `clothes.js TOPS.${id}`);
  }
  for (const id of PIECES.top) assert.ok(known.includes(`'${id}'`), `econ3d KNOWN_TOPS ${id}`);
  for (const id of ['robe', 'refshirt', 'cardigan', 'spacesuit', 'hawaiian', 'chef', 'stringer', 'pjtop']) assert.match(sleeves, new RegExp(`\\b${id}: `), `hands.js SLEEVES.${id}`);
  for (const id of Object.keys(BOTTOMS)) assert.match(block(clothes, 'const BOTTOMS = {'), new RegExp(`\\b${id}: `), `clothes.js BOTTOMS.${id}`);
  for (const slot of ['head', 'face', 'back']) for (const id of Object.keys(ACCESSORIES[slot])) if (id !== 'none') assert.ok(models.includes(`case '${id}'`), `models.js ${slot} ${id}`);
});
test('bots dress up as the new costumes too', () => {
  const seen = new Set();
  for (let s = 1; s < 20000 && seen.size < Object.keys(NEW).length; s++) {
    const { look, preset } = botLook(s, 1);
    if (!Object.hasOwn(NEW, preset)) continue;
    seen.add(preset);
    assert.equal(look.top, [].concat(COSTUMES[preset].look.top)[0], preset);
    assert.ok(wearing(preset, look, ALL), preset);
  }
  assert.equal(seen.size, Object.keys(NEW).length);
});
