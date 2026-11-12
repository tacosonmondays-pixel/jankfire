// FRIENDS over HTTP + the party socket (server/friends.js, server/party.js): needs accounts (guests get told), ask,
// accept, the list with presence (in the menu, in a lobby, in a match), NAH and the day's wait, remove, invites and
// joining a friend's party (friends only), junk ignored
// (start a server first: PORT=3100 node server.js; then node tests/friends_ws.cjs 3100)
const WS = require('ws');
const port = process.argv[2] || 3100, base = `http://localhost:${port}`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const api = async (path, body, token) => { const r = await fetch(base + path, { method: body ? 'POST' : 'GET', headers: { 'content-type': 'application/json', ...(token ? { authorization: 'Bearer ' + token } : {}) }, body: body ? JSON.stringify(body) : undefined }); return { code: r.status, ...(await r.json()) }; };
const tag = Math.random().toString(36).slice(2, 7);
async function account(n) { const name = n + tag, r = await api('/api/register', { name, pass: 'hunter22hunter' }); return { name, token: r.token }; }
function hub(token, name) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, party: null, errs: [], inv: [] };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'party') c.party = m; if (m.t === 'perr') c.errs.push(m.m); if (m.t === 'pinvite') c.inv.push(m); });
  c.send = (m) => ws.send(JSON.stringify(m));
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'hub', name, token, look: {} }); setTimeout(() => res(c), 500); }));
}
(async () => {
  const A = await account('fa'), B = await account('fb'), C = await account('fc');
  ok(A.token && B.token && C.token, 'three accounts');
  const g = await api('/api/friends');
  ok(g.code === 401 && /account/.test(g.error), 'a guest is told friends need an account');
  const l0 = await api('/api/friends', null, A.token);
  if (l0.off) { console.log('friends are off on this server (no jf_friends table): nothing more to test'); process.exit(0); }
  ok(Array.isArray(l0.friends) && !l0.friends.length, 'a new account has no friends (yet)');
  ok((await api('/api/friends/add', { name: A.name }, A.token)).code === 400, "can't friend yourself");
  ok((await api('/api/friends/add', { name: 'nobody' + tag }, A.token)).code === 400, 'no such account: told');
  ok((await api('/api/friends/add', { name: { x: 1 } }, A.token)).code === 400, 'junk name: refused');
  ok((await api('/api/friends/add', { name: B.name.toUpperCase() }, A.token)).ok, 'A asks B (any case)');
  ok((await api('/api/friends/add', { name: B.name }, A.token)).code === 400, 'asking twice: told');
  const lb = await api('/api/friends', null, B.token);
  ok(lb.incoming.includes(A.name) && !lb.friends.length, "B sees A's request");
  ok((await api('/api/friends/answer', { name: A.name, yes: true }, A.token)).code === 400, "A can't accept their own request");
  ok((await api('/api/friends/answer', { name: A.name, yes: true }, B.token)).ok, 'B says yes');
  // presence
  const HA = await hub(A.token, A.name), HB = await hub(B.token, B.name), HC = await hub(C.token, C.name);
  let la = await api('/api/friends', null, A.token);
  ok(la.friends.length === 1 && la.friends[0].name === B.name && la.friends[0].on && la.friends[0].on.where === 'menu', 'A sees B, online, in the menu ' + JSON.stringify(la.friends));
  HB.send({ t: 'pbusy', on: true, what: 'JANK ROYALE<script>' }); await sleep(400);
  la = await api('/api/friends', null, A.token);
  ok(la.friends[0].on.where === 'match' && la.friends[0].on.what === 'JANK ROYALEscript', 'B in a match: A sees which (cleaned) ' + JSON.stringify(la.friends[0].on));
  HB.send({ t: 'pbusy', on: false }); await sleep(700);
  // invites + joining a friend's party: friends only
  HA.send({ t: 'pinvite', name: B.name }); await sleep(600);
  ok(HB.inv.length === 1 && HB.inv[0].code === HA.party.code, "A invites B: B gets A's code");
  HC.send({ t: 'pinvite', name: A.name }); await sleep(600);
  ok(!HA.inv.length && HC.errs.some((e) => /only friends/.test(e)), 'C (not a friend) cannot invite A');
  HC.send({ t: 'pjoinf', name: A.name }); await sleep(1700);
  ok(HA.party.ms.length === 1, "C cannot join A's party without being a friend");
  HB.send({ t: 'pjoinf', name: A.name.toUpperCase() }); await sleep(700);
  ok(HA.party.ms.length === 2 && HB.party.code === HA.party.code, "B joins A's party from the friends list");
  HB.send({ t: 'pjoinf', name: 12 }); HB.send({ t: 'pinvite', name: 'x'.repeat(500) }); await sleep(300);
  ok(HB.party.code === HA.party.code, 'junk invites: ignored');
  // NAH: C asks A, A says nah, C can't ask again today; remove
  await api('/api/friends/add', { name: A.name }, C.token);
  ok((await api('/api/friends/answer', { name: C.name, yes: false }, A.token)).ok, 'A says nah to C');
  const again = await api('/api/friends/add', { name: A.name }, C.token);
  ok(again.code === 400 && /nah/.test(again.error), 'C asks again the same day: told to wait');
  ok(!(await api('/api/friends', null, A.token)).incoming.length, "the nah'd request is gone from A's list");
  ok((await api('/api/friends/remove', { name: B.name }, A.token)).ok && !(await api('/api/friends', null, B.token)).friends.length, 'A removes B: gone for both');
  for (const h of [HA, HB, HC]) h.ws.close();
  console.log(fails ? `${fails} FAILED` : 'all ok');
  process.exit(fails ? 1 : 0);
})();
