// FRIENDS (docs/menu/HUB_LOBBY.md section 5, build step 3): accounts only. One row per pair of accounts (a < b by
// name_lower): who asked, and 'pending' / 'friends' / 'nah' (a request said no to: the same person can't ask again
// for a day). Supabase keeps them in jf_friends (the SQL the owner runs; until then friends are just off: { off: 1 },
// the menu hides the button). The file store keeps them in the db file's friends list. Presence (in the menu, in a
// lobby, in a match) comes from the party connections (server/party.js presenceOf).
// HTTP, with the account token like /api/me: /api/friends (the list), /api/friends/add { name },
// /api/friends/answer { name, yes }, /api/friends/remove { name }
import { presenceOf } from './party.js';

export const FRIENDS = { max: 100, perDay: 20, nah: 86400000, perMin: 40 };
const hits = new Map(); // account -> request times in the last minute
const enc = encodeURIComponent;
const okName = (s) => typeof s === 'string' && s.length >= 1 && s.length <= 24;
const pair = (x, y) => (x < y ? [x, y] : [y, x]);

export function makeFriends(store) {
  const file = store.kind === 'file';
  let table = file ? true : null, tT = 0;
  if (file) store.db.friends ||= [];
  const F = {
    // is the table there? (Supabase: look again every 10 minutes, the SQL may have been run meanwhile)
    async on() {
      if (file) return true;
      if (typeof store.req !== 'function') return false;
      if (table == null || (!table && Date.now() - tT > 600000)) {
        tT = Date.now();
        try { await store.req('GET', '?limit=0', null, null, '/jf_friends'); table = true; }
        catch { if (table == null) console.warn('  !! no jf_friends table: friends are off until the SQL in docs/menu/HUB_LOBBY.md is run in Supabase'); table = false; }
      }
      return table;
    },
    async rows(n) {
      if (file) return store.db.friends.filter((r) => r.a === n || r.b === n);
      return (await store.req('GET', `?or=(a.eq.${enc(n)},b.eq.${enc(n)})&select=a,b,asked_by,status,created_at&limit=400`, null, null, '/jf_friends')) || [];
    },
    async row(x, y) {
      const [a, b] = pair(x, y);
      if (file) return store.db.friends.find((r) => r.a === a && r.b === b) || null;
      const r = await store.req('GET', `?a=eq.${enc(a)}&b=eq.${enc(b)}&select=a,b,asked_by,status,created_at`, null, null, '/jf_friends');
      return (r && r[0]) || null;
    },
    async put(row) {
      if (file) { const i = store.db.friends.findIndex((r) => r.a === row.a && r.b === row.b); if (i >= 0) store.db.friends[i] = row; else store.db.friends.push(row); store.save(); return; }
      await store.req('POST', '?on_conflict=a,b', row, { Prefer: 'resolution=merge-duplicates,return=minimal' }, '/jf_friends');
    },
    async del(x, y) {
      const [a, b] = pair(x, y);
      if (file) { store.db.friends = store.db.friends.filter((r) => !(r.a === a && r.b === b)); store.save(); return; }
      await store.req('DELETE', `?a=eq.${enc(a)}&b=eq.${enc(b)}`, null, { Prefer: 'return=minimal' }, '/jf_friends');
    },
    // display names for a list of name_lowers (one query)
    async names(list) {
      if (!list.length) return {};
      if (file) return Object.fromEntries(list.map((n) => [n, (store.db.users[n] && store.db.users[n].name) || n]));
      const r = await store.req('GET', `?name_lower=in.(${list.map((n) => '"' + n.replace(/"/g, '') + '"').map(enc).join(',')})&select=name_lower,name`);
      const out = Object.fromEntries(list.map((n) => [n, n]));
      for (const u of r || []) out[u.name_lower] = u.name;
      return out;
    },
    async areFriends(x, y) { if (!x || !y || x === y || !(await F.on())) return false; const r = await F.row(x, y); return !!(r && r.status === 'friends'); },
  };
  return F;
}

// the routes. accounts: the Accounts (verify, store); it keeps one makeFriends per store
export async function friendsApi(accounts, url, body, auth, send) {
  const u = await accounts.verify(auth);
  if (!u) return send(401, { error: 'friends need an account' });
  const F = accounts.friends || (accounts.friends = makeFriends(accounts.store));
  if (!(await F.on())) return send(200, { off: 1 });
  const me = u.name_lower, t = Date.now();
  const hl = (hits.get(me) || []).filter((x) => t - x < 60000); hl.push(t); hits.set(me, hl);
  if (hl.length > FRIENDS.perMin) return send(429, { error: 'slow down' });
  if (hits.size > 5000) for (const [k, v] of hits) if (t - v[v.length - 1] > 60000) hits.delete(k); // (old entries go)
  const other = okName(body.name) ? body.name.trim().toLowerCase() : null;
  switch (url) {
    case '/api/friends': {
      const rows = await F.rows(me), names = await F.names([...new Set(rows.map((r) => (r.a === me ? r.b : r.a)))]);
      const friends = [], incoming = [], outgoing = [];
      for (const r of rows) {
        const o = r.a === me ? r.b : r.a, nm = names[o] || o;
        if (r.status === 'friends') friends.push({ name: nm, on: presenceOf(o) });
        else if (r.status === 'pending') (r.asked_by === me ? outgoing : incoming).push(nm);
      }
      friends.sort((x, y) => (!!y.on - !!x.on) || x.name.localeCompare(y.name));
      return send(200, { friends, incoming, outgoing, max: FRIENDS.max });
    }
    case '/api/friends/add': {
      if (!other || other === me) return send(400, { error: other === me ? "you can't friend yourself. we checked" : 'who?' });
      const them = await accounts.store.get(other);
      if (!them) return send(400, { error: 'no account with that name' });
      const rows = await F.rows(me), r = rows.find((x) => (x.a === me ? x.b : x.a) === other);
      if (r && r.status === 'friends') return send(400, { error: 'you are already friends' });
      if (r && r.status === 'pending' && r.asked_by === me) return send(400, { error: 'already asked. they have to say yes' });
      if (r && r.status === 'pending') { await F.put({ ...r, status: 'friends' }); return send(200, { ok: 1, friends: 1 }); } // they asked you too: friends
      if (r && r.status === 'nah' && r.asked_by === me && t - Date.parse(r.created_at) < FRIENDS.nah) return send(400, { error: 'they said nah. give it a day' });
      if (rows.filter((x) => x.status !== 'nah').length >= FRIENDS.max) return send(400, { error: `${FRIENDS.max} friends is the most. remove someone` });
      if (rows.filter((x) => x.asked_by === me && t - Date.parse(x.created_at) < 86400000).length >= FRIENDS.perDay) return send(429, { error: 'that is a lot of friend requests for one day' });
      const [a, b] = pair(me, other);
      await F.put({ a, b, asked_by: me, status: 'pending', created_at: new Date(t).toISOString() });
      return send(200, { ok: 1 });
    }
    case '/api/friends/answer': {
      const r = other && (await F.row(me, other));
      if (!r || r.status !== 'pending' || r.asked_by === me) return send(400, { error: 'no request from them' });
      if (body.yes === true) await F.put({ ...r, status: 'friends' });
      else await F.put({ ...r, status: 'nah', created_at: new Date(t).toISOString() });
      return send(200, { ok: 1 });
    }
    case '/api/friends/remove': {
      const r = other && (await F.row(me, other));
      if (!r) return send(400, { error: 'not friends' });
      if (r.status === 'nah' && r.asked_by !== me) return send(200, { ok: 1 }); // (the one who said nah can't wipe the wait)
      await F.del(me, other);
      return send(200, { ok: 1 });
    }
  }
  return send(404, { error: 'nope' });
}
