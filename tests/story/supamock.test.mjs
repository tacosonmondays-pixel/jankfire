// node tests/story/supamock.test.mjs : SupabaseStore's story methods against a fake PostgREST (fetch stubbed)
import assert from 'node:assert/strict';
process.env.SUPABASE_URL = 'https://fake.supabase.co'; process.env.SUPABASE_SERVICE_KEY = 'sb_secret_fake';
const { makeStore } = await import('../../server/store.js');
const db = { users: { bob: { name_lower: 'bob', inv: { skin: ['a'] } } }, story: [] };
let hasTable = false; const calls = [];
globalThis.fetch = async (url, o) => {
  const u = new URL(url), m = o.method; calls.push(`${m} ${u.pathname}${u.search}`);
  const ok = (b) => ({ ok: true, status: 200, text: async () => (b == null ? '' : JSON.stringify(b)) });
  if (u.pathname.endsWith('/jf_story')) {
    if (!hasTable) return { ok: false, status: 404, text: async () => '{"code":"PGRST205"}' };
    if (m === 'GET') return ok(db.story.filter((r) => u.search.includes(r.name_lower)));
    if (m === 'POST') { const row = JSON.parse(o.body); db.story = db.story.filter((r) => !(r.name_lower === row.name_lower && r.slot === row.slot)); db.story.push(row); return ok(null); }
  }
  if (u.pathname.endsWith('/jf_users')) {
    if (m === 'GET') return ok([db.users.bob]);
    if (m === 'PATCH') { Object.assign(db.users.bob, JSON.parse(o.body)); return ok(null); }
  }
  return { ok: false, status: 500, text: async () => 'unexpected' };
};
const st = makeStore('.');
const save = { v: 1, slot: 0, act: 1, chapter: 'return_to_sender', playtime: 9, coupons: 3, at: { map: 'story_test', p: [1, 2, 3], yaw: 0 }, data: { flags: ['f'] }, t: 1 };
assert.deepEqual(await st.storyInfo(), { slots: 1, table: false });
await st.putStory('bob', 0, save);
assert.deepEqual(db.users.bob.inv.skin, ['a'], 'other inv kept'); assert.equal(db.users.bob.inv.story[0].coupons, 3);
assert.equal((await st.getStory('bob'))[0].at.p[2], 3);
hasTable = true; st.storyT = 0; // the owner ran the sql; 10 min later we look again
assert.deepEqual(await st.storyInfo(), { slots: 3, table: true });
assert.equal((await st.getStory('bob'))[0].coupons, 3, 'old inv.story save still readable before the first table save');
await st.putStory('bob', 2, { ...save, slot: 2, coupons: 99 });
const g = await st.getStory('bob');
assert.equal(g.length, 1); assert.equal(g[0].slot, 2); assert.equal(g[0].coupons, 99); assert.deepEqual(g[0].at.p, [1, 2, 3]); assert.deepEqual(g[0].data, { flags: ['f'] });
console.log('supabase mock ok:', calls.length, 'calls');
