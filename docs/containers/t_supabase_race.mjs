// The Supabase store's gift claim + batch open against a fake PostgREST (in memory, honours the eq. filters, every
// request takes a few random ms so parallel calls interleave the way real ones do). No network.
process.env.SUPABASE_URL = 'https://fake.supabase.co'; process.env.SUPABASE_SERVICE_KEY = 'sb_secret_fake';
const { makeStore } = await import('../../server/store.js');
const { GIFTS } = await import('../../shared/gifts.js');
const s = makeStore('.');
const rows = { bob: { name_lower: 'bob', name: 'bob', crates: 1, bags: 1, boxes: 1, inv: {} } };
const wait = () => new Promise((r) => setTimeout(r, Math.random() * 15));
s.req = async (method, query, body) => {
  await wait();
  const q = new URLSearchParams(query.replace(/^\?/, ''));
  const name = (q.get('name_lower') || '').replace(/^eq\./, ''), row = rows[name];
  if (method === 'GET') return row ? [JSON.parse(JSON.stringify(row))] : [];
  if (method === 'PATCH') {
    if (!row) return [];
    for (const [k, v] of q) if (k !== 'name_lower' && v.startsWith('eq.') && String(row[k]) !== v.slice(3)) return []; // a filter didn't match: nothing changed
    Object.assign(row, JSON.parse(JSON.stringify(body)));
    return [JSON.parse(JSON.stringify(row))];
  }
  throw new Error('fake: ' + method);
};
let bad = 0; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) bad++; };
const g = GIFTS[0];
const res = await Promise.all([0, 1, 2, 3, 4].map(() => s.claimGift('bob', g)));
ok(res.filter(Boolean).length === 1, `5 claims at once: ${res.filter(Boolean).length} won`);
ok(rows.bob.crates === 31 && rows.bob.bags === 26 && rows.bob.boxes === 71 && rows.bob.inv.gifts.length === 1, `bob: ${rows.bob.crates}/${rows.bob.bags}/${rows.bob.boxes}, gifts ${JSON.stringify(rows.bob.inv.gifts)}`);
ok(!(await s.claimGift('bob', g)), 'claiming again later: no');
const items = Array.from({ length: 10 }, (_, i) => ({ type: 'finish', id: 'w' + i }));
const two = await Promise.all([s.spendRolls('bob', 'crate', 10, items), s.spendRolls('bob', 'crate', 10, items)]);
ok(two.filter(Boolean).length === 1 && rows.bob.crates === 21 && rows.bob.inv.finish.length === 10, `two batches of 10 at once: ${two.filter(Boolean).length} went through, crates ${rows.bob.crates}, items ${rows.bob.inv.finish.length}`);
ok(!(await s.spendRolls('bob', 'crate', 22, items)), 'more than you have: no');
console.log(bad ? `${bad} FAIL` : 'ALL OK');
