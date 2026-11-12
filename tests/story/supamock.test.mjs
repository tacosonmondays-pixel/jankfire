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
    if (m === 'DELETE') { const nl = u.searchParams.get('name_lower'), sl = u.searchParams.get('slot'); assert.ok(/^eq\./.test(nl) && /^eq\.\d$/.test(sl), 'a delete names one account and one slot: ' + u.search); db.story = db.story.filter((r) => !(r.name_lower === nl.slice(3) && r.slot === Number(sl.slice(3)))); return ok(null); }
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
// wiping a slot (the picker's WIPE IT): the table row goes; an old inv.story copy of that slot goes too
await st.delStory('bob', 2);
assert.ok(!db.story.some((r) => r.slot === 2), 'row deleted');
assert.ok(calls.some((c) => /^DELETE .*\/jf_story\?name_lower=eq\.bob&slot=eq\.2$/.test(c)), 'one row, by account and slot: ' + calls.filter((c) => c.startsWith('DELETE')));
assert.deepEqual((await st.getStory('bob')).map((x) => x.slot), [0], 'the pre-table inv.story save shows again once the table has none');
await st.delStory('bob', 0);
assert.deepEqual(await st.getStory('bob'), [], 'and wiping slot 0 clears that old copy');
assert.deepEqual(db.users.bob.inv.skin, ['a'], 'the rest of inv untouched by a wipe');
// before the sql re-run (no table): the one inv.story slot
hasTable = false; st.storyTable = null;
await st.putStory('bob', 0, save); assert.equal((await st.getStory('bob')).length, 1);
await st.delStory('bob', 0); assert.deepEqual(await st.getStory('bob'), [], 'fallback slot wiped');
console.log('supabase mock ok:', calls.length, 'calls');
