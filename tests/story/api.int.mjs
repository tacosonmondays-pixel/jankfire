// node tests/story/api.int.mjs <port> : /api/story/* against a running server (file store)
import assert from 'node:assert/strict';
const B = `http://localhost:${process.argv[2] || 3000}`;
const post = async (path, body, tok) => { let r; try { r = await fetch(B + path, { method: 'POST', headers: { 'content-type': 'application/json', ...(tok ? { authorization: 'Bearer ' + tok } : {}) }, body: typeof body === 'string' ? body : JSON.stringify(body || {}) }); } catch { return { code: 413, j: {} }; } /* (readJson hangs up on a body over 64 KB: that's a no too) */ return { code: r.status, j: await r.json().catch(() => ({})) }; };
const name = 'st' + Math.floor(Math.random() * 1e8);
const reg = await post('/api/register', { name, pass: 'pass1234' });
assert.equal(reg.code, 200, JSON.stringify(reg.j)); const tok = reg.j.token;
assert.equal((await post('/api/story/list', {})).code, 401, 'no token');
assert.equal((await post('/api/story/list', {}, 'junk.token')).code, 401);
const L = await post('/api/story/list', {}, tok); console.log('list', JSON.stringify(L.j));
assert.equal(L.code, 200); assert.ok(L.j.slots >= 1); assert.equal(L.j.saves.length, L.j.slots); assert.equal(L.j.saves[0], null);
const save = { v: 1, slot: 0, act: 1, chapter: 'return_to_sender', playtime: 61, coupons: 5, at: { map: 'story_test', p: [1, 0.1, 2], yaw: 1 }, data: { flags: ['x'], quests: {}, seen: [] } };
const S = await post('/api/story/save', { slot: 0, save }, tok); assert.equal(S.code, 200, JSON.stringify(S.j));
assert.equal((await post('/api/story/save', { slot: 0, save }, tok)).code, 429, 'rate limit');
const ld = await post('/api/story/load', { slot: 0 }, tok); assert.equal(ld.code, 200); assert.deepEqual(ld.j.save.at.p, [1, 0.1, 2]); assert.deepEqual(ld.j.save.data.flags, ['x']);
const me = await fetch(B + '/api/me', { headers: { authorization: 'Bearer ' + tok } }).then((r) => r.json()); assert.ok(!('story' in me.me.inv), 'inv.story kept out of /api/me');
// fuzz: every one of these must be a clean 4xx, never a 500
const fuzz = [
  ['/api/story/load', { slot: -1 }], ['/api/story/load', { slot: 99 }], ['/api/story/load', { slot: '0' }], ['/api/story/load', { slot: 0.5 }], ['/api/story/load', {}],
  ['/api/story/save', { slot: 0 }], ['/api/story/save', { slot: 7, save }], ['/api/story/save', { slot: 0, save: 'x' }], ['/api/story/save', { slot: 0, save: [] }],
  ['/api/story/save', { slot: 0, save: { ...save, act: 5 } }], ['/api/story/save', { slot: 0, save: { ...save, data: { _x: 1 } } }],
  ['/api/story/save', { slot: 0, save: { ...save, data: { big: 'z'.repeat(70000) } } }], ['/api/story/nope', {}], ['/api/story/save', '{"slot":0,"save":{"__proto__":{"a":1}}}'],
  ['/api/story/save', 'not json at all'], ['/api/story/save', JSON.stringify({ slot: 0, save: JSON.parse('['.repeat(500) + ']'.repeat(500)) })],
];
for (const [p, b] of fuzz) { const r = await post(p, b, tok); assert.ok(r.code >= 400 && r.code < 500, `${p} ${JSON.stringify(b).slice(0, 80)} -> ${r.code}`); }
console.log('all story api tests passed; slots', L.j.slots, 'table', L.j.table);
