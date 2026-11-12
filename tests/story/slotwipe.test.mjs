// node tests/story/slotwipe.test.mjs : POST /api/story/delete (the slot picker's WIPE IT) against a real server on a
// throwaway file store: needs a token, a slot that's an integer in range, only ever wipes your own slot, rate limited.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '../..');
const PORT = 3900 + Math.floor(Math.random() * 90);
const srv = spawn(process.execPath, ['server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(PORT), JF_DATA_DIR: fs.mkdtempSync(path.join(os.tmpdir(), 'jfwipe-')) }, stdio: 'ignore' });
const B = `http://localhost:${PORT}`;
for (let i = 0; i < 80; i++) { try { await fetch(B + '/health'); break; } catch { await new Promise((r) => setTimeout(r, 200)); } }
const post = async (p, body, tok) => { const r = await fetch(B + p, { method: 'POST', headers: { 'content-type': 'application/json', ...(tok ? { authorization: 'Bearer ' + tok } : {}) }, body: typeof body === 'string' ? body : JSON.stringify(body) }); let j = null; try { j = await r.json(); } catch { /* fine */ } return { code: r.status, j }; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };
const save = (slot, coupons) => ({ v: 1, slot, act: 1, chapter: 'return_to_sender', playtime: 61, coupons, at: { map: 'story_slice', p: [1, 8, 2], yaw: 0 }, data: { flags: { x: true }, quests: {} } });
try {
  const reg = async (name) => { const r = await post('/api/register', { name, pass: 'pass1234' }); assert.equal(r.code, 200, JSON.stringify(r.j)); return r.j.token; };
  const A = await reg('wa' + Math.floor(Math.random() * 1e7)), Bt = await reg('wb' + Math.floor(Math.random() * 1e7));
  assert.equal((await post('/api/story/save', { slot: 0, save: save(0, 5) }, A)).code, 200);
  assert.equal((await post('/api/story/save', { slot: 0, save: save(0, 77) }, Bt)).code, 200);
  await sleep(10100); // (one save per 10 s per account)
  assert.equal((await post('/api/story/save', { slot: 1, save: save(1, 6) }, A)).code, 200);

  await t('no token / a bad token: 401, nothing wiped', async () => {
    assert.equal((await post('/api/story/delete', { slot: 0 })).code, 401);
    assert.equal((await post('/api/story/delete', { slot: 0 }, 'junk.token')).code, 401);
    assert.ok((await post('/api/story/list', {}, A)).j.saves[0], 'still there');
  });
  await t('bad slots: a clean 400 every time (never a 500), nothing wiped', async () => {
    for (const body of [{ slot: -1 }, { slot: 3 }, { slot: 99 }, { slot: '0' }, { slot: 0.5 }, { slot: null }, { slot: [0] }, { slot: { valueOf: 0 } }, {}, 'not json']) {
      const r = await post('/api/story/delete', body, A);
      assert.ok(r.code >= 400 && r.code < 500, `${JSON.stringify(body)} -> ${r.code}`);
    }
    const L = (await post('/api/story/list', {}, A)).j.saves; assert.ok(L[0] && L[1], 'both slots still there');
    // a __proto__ key can't change which slot goes: this wipes the (empty) slot 2 and only that
    const r = await post('/api/story/delete', '{"slot":2,"__proto__":{"slot":1}}', A);
    assert.ok(r.code === 200 || (r.code >= 400 && r.code < 500), 'proto key: ' + r.code);
    const L2 = (await post('/api/story/list', {}, A)).j.saves; assert.ok(L2[0] && L2[1], 'slots 0 and 1 untouched by the __proto__ trick');
  });
  await sleep(3100);
  await t('your slot 1: wiped; your slot 0 and the other account untouched', async () => {
    const r = await post('/api/story/delete', { slot: 1 }, A);
    assert.equal(r.code, 200); assert.equal(r.j.ok, true);
    const L = (await post('/api/story/list', {}, A)).j.saves;
    assert.equal(L[1], null, 'slot 1 is empty'); assert.ok(L[0], 'slot 0 kept');
    assert.ok((await post('/api/story/list', {}, Bt)).j.saves[0], "the other account's slot 0 kept");
    assert.equal((await post('/api/story/load', { slot: 1 }, A)).j.save, null);
  });
  await t('a second wipe straight away: 429 (it is a button)', async () => {
    assert.equal((await post('/api/story/delete', { slot: 0 }, A)).code, 429);
    assert.ok((await post('/api/story/list', {}, A)).j.saves[0], 'slot 0 still there');
  });
  await sleep(3100);
  await t('wiping slot 0 (your own) never touches the other account, and a new game can save at once', async () => {
    assert.equal((await post('/api/story/delete', { slot: 0 }, A)).code, 200);
    assert.equal((await post('/api/story/list', {}, A)).j.saves[0], null);
    const b = (await post('/api/story/list', {}, Bt)).j.saves[0];
    assert.ok(b && b.coupons === 77, "B's save is B's: " + JSON.stringify(b));
    assert.equal((await post('/api/story/save', { slot: 0, save: save(0, 1) }, A)).code, 200, 'the save gap is reset by a wipe');
  });
  await sleep(3100);
  await t('wiping an empty slot is fine', async () => {
    assert.equal((await post('/api/story/delete', { slot: 2 }, A)).code, 200);
  });
} finally { srv.kill(); }
console.log(`slotwipe: ${n} ok`);
