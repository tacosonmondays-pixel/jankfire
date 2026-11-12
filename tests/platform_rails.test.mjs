// Platform's handrails and stairs (rigrails_<map>, tools/blender/arch/make_rigrails.py): one Blender model per rig map
// over every rail() / rigStair() box. look-only: those boxes stay the collision; the model was built from the map's
// current rails (its dump in tools/blender/arch/boxes/ matches what the map builds now)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import { MAPS } from '../shared/map.js';
import { ARCH_IDS } from '../public/js/archfield.js';

for (const id of ['platform', 'platform_sd']) {
  const av = 'rigrails_' + id;
  test(`${id}: every rail and stair is drawn by ${av}, look-only`, () => {
    const m = MAPS[id];
    assert.ok(ARCH_IDS.has(av), 'archfield knows the model');
    assert.ok(fs.existsSync(new URL(`../public/models/arch/${av}.glb`, import.meta.url)), 'the model is there');
    const pl = m.boxes.arch.findIndex((a) => a.id === av);
    assert.ok(pl >= 0, 'one placement');
    assert.deepEqual(m.boxes.arch[pl].p, [0, 0, 0]);
    const mine = m.boxes.filter((b) => b.av === av), deco = m.deco.filter((b) => b.av === av);
    assert.ok(mine.length > 400 && deco.length > 600, `${mine.length} solid, ${deco.length} look-only boxes`);
    for (const b of [...mine, ...deco]) { assert.equal(b.ai, pl); assert.ok(!b.pv, 'not inside a kit prop too'); }
    // every tagged box was noted by a rail or a stair
    const noted = new Set(); for (const r of m.boxes.rigkit) for (let i = r.b[0]; i < r.b[1]; i++) noted.add(i);
    m.boxes.forEach((b, i) => { if (b.av === av) assert.ok(noted.has(i), `box ${i} tagged but not noted`); });
    // the rails' solid parts are the top rails (yellow, 1.1 up) and the stairs' steps
    assert.ok(mine.every((b) => ['rigyellow', 'grating', 'deckplate'].includes(b.mat)), 'only rails and steps');
  });
  test(`${id}: the model's dump is the map as it is now`, () => {
    const fresh = JSON.parse(execFileSync(process.execPath, [new URL('../tools/arch/dumprig.mjs', import.meta.url).pathname, id], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }));
    const kept = JSON.parse(fs.readFileSync(new URL(`../tools/blender/arch/boxes/${av}.json`, import.meta.url), 'utf8'));
    assert.deepEqual(kept.rails, fresh.rails, 'rails changed: re-run tools/arch/dumprig.mjs and make_rigrails.py');
    assert.deepEqual(kept.stairs, fresh.stairs, 'stairs changed: re-run tools/arch/dumprig.mjs and make_rigrails.py');
  });
}
