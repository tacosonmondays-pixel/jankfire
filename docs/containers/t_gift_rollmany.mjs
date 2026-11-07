// Gift + batch open, over HTTP against a running server with a FILE store (JF_DATA_DIR=<dir>).
// usage: node t_gift_rollmany.mjs <port> <data dir> <phase: 1|2>
//   phase 1: register "giftee": the gift lands once (+30/+25/+70 on top of the starting 1/1/1); logging in again gives nothing
//   (between phases the runner stops the server and adds "twins", a copy of giftee with no gifts and no containers)
//   phase 2: 4 logins of "twins" at the same moment: exactly one gets the gift; the batch endpoint; bad input
const [port, dir, phase] = process.argv.slice(2);
const B = `http://localhost:${port}/api/`;
let bad = 0; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) bad++; };
const call = async (path, body, token) => { const r = await fetch(B + path, { method: body ? 'POST' : 'GET', headers: { 'content-type': 'application/json', ...(token ? { authorization: 'Bearer ' + token } : {}) }, body: body ? JSON.stringify(body) : undefined }); return { status: r.status, j: await r.json().catch(() => ({})) }; };
const rolls = (me) => `${me.rolls.crate}/${me.rolls.bag}/${me.rolls.box}`;
if (phase === '1') {
  const r = await call('register', { name: 'giftee', pass: 'hunter22' });
  ok(r.status === 200 && r.j.gifts && r.j.gifts.length === 1 && r.j.gifts[0].id === 'g20261107', 'sign-up gets the gift: ' + JSON.stringify(r.j.gifts));
  ok(rolls(r.j.me) === '31/26/71', 'containers after sign-up (1/1/1 + 30/25/70): ' + rolls(r.j.me));
  const l = await call('login', { name: 'giftee', pass: 'hunter22' });
  ok(l.j.gifts.length === 0 && rolls(l.j.me) === '31/26/71', 'log in again: no second gift, ' + rolls(l.j.me));
  const m = await call('me', null, l.j.token);
  ok(m.j.gifts.length === 0 && rolls(m.j.me) === '31/26/71', '/api/me: no second gift, ' + rolls(m.j.me));
} else {
  const many = await Promise.all([0, 1, 2, 3].map(() => call('login', { name: 'twins', pass: 'hunter22' })));
  const got = many.filter((r) => r.j.gifts && r.j.gifts.length).length;
  ok(got === 1, `4 logins at once: ${got} got the gift`);
  const tok = many[0].j.token;
  const me0 = (await call('me', null, tok)).j.me;
  ok(rolls(me0) === '30/25/70', 'twins after the race: ' + rolls(me0));
  // a batch of 10 crates
  const inv0 = (me0.inv.model || []).length;
  const b = await call('rollmany', { kind: 'crate', n: 10 }, tok);
  ok(b.status === 200 && b.j.items.length === 10, 'x10 crates: 10 results');
  ok(b.j.me.rolls.crate === 20, 'crates 30 -> ' + b.j.me.rolls.crate);
  const newIds = b.j.items.filter(Boolean).map((i) => i.id);
  ok((b.j.me.inv.model || []).length === inv0 + newIds.length && new Set(newIds).size === newIds.length, `inventory +${newIds.length} skins, no repeats in the batch; xp ${b.j.xp}`);
  await new Promise((r) => setTimeout(r, 800));
  // bad input (each after the rate-limit gap)
  for (const [body, why] of [[{ kind: 'crate', n: 0 }, 'n=0'], [{ kind: 'crate', n: -1 }, 'n=-1'], [{ kind: 'crate', n: 'abc' }, 'n=abc'], [{ kind: 'crate', n: 1000 }, 'n=1000'], [{ kind: 'crate', n: 2.5 }, 'n=2.5'], [{ kind: 'crate', n: 21 }, 'n > owned (21 of 20)'], [{ kind: 'nope', n: 1 }, 'kind=nope'], [{ kind: '__proto__', n: 1 }, 'kind=__proto__'], [{ n: 1 }, 'no kind']]) {
    const r = await call('rollmany', body, tok);
    ok(r.status === 400, `rejected ${why}: ${r.status} ${r.j.error}`);
  }
  const anon = await call('rollmany', { kind: 'crate', n: 1 });
  ok(anon.status === 401, 'no token: 401');
  const me1 = (await call('me', null, tok)).j.me;
  ok(me1.rolls.crate === 20, 'nothing was spent by the rejected ones: ' + me1.rolls.crate);
  // rate limit: two right after each other
  await new Promise((r) => setTimeout(r, 800));
  const [a, c] = await Promise.all([call('rollmany', { kind: 'box', n: 5 }, tok), call('rollmany', { kind: 'box', n: 5 }, tok)]);
  ok([a.status, c.status].sort().join() === '200,429', `two batches at once: ${a.status} + ${c.status}`);
  const me2 = (await call('me', null, tok)).j.me;
  ok(me2.rolls.box === 65, 'boxes 70 -> ' + me2.rolls.box);
  // ALL of a kind (25 bags), capped at 100 a request on the client
  await new Promise((r) => setTimeout(r, 800));
  const all = await call('rollmany', { kind: 'bag', n: me2.rolls.bag }, tok);
  ok(all.status === 200 && all.j.items.length === 25 && all.j.me.rolls.bag === 0, `OPEN ALL bags: ${all.j.items && all.j.items.length} results, ${all.j.me && all.j.me.rolls.bag} left, ${all.j.items && all.j.items.filter((x) => !x).length} turned into xp (+${all.j.xp})`);
}
console.log(bad ? `${bad} FAIL` : 'ALL OK');
process.exit(bad ? 1 : 0);
