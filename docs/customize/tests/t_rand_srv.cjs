// Random cosmetics, server side: join with random slots, fall into the void a few times, check each life's roll.
const WebSocket = require('ws');
const PORT = process.env.PORT || 3101, TOKEN = process.env.TOKEN;
const OWN = { finish: ['default', 'pink', 'wood', 'camo', 'chrome', 'ice', 'neon', 'gold'], hat: ['none', 'party', 'cone', 'cowboy', 'chef', 'crown'], effect: ['none', 'smoke', 'bubbles', 'sparkles', 'hearts'], kill: ['none', 'confetti', 'grave', 'cash', 'chicken'] };
function run(favs) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(`ws://localhost:${PORT}/ws`);
    let me = 0, seq = 0, rolls = [], kfxs = [], deaths = 0;
    const send = (m) => ws.send(JSON.stringify(m));
    const die = () => send({ t: 's', q: seq, p: [0, -9999, 0], v: [0, 0, 0], y: 0, x: 0, w: 'ar' });
    ws.on('open', () => send({ t: 'join', name: 'randbot', mode: 'training', token: TOKEN, skins: { ar: ['random', 'random', 'random', 'default', 'full'], knife: ['random', 'none', 'none', 'random', 'normal'] }, favs, kfx: 'random', item: 'frag' }));
    ws.on('message', (d) => {
      const m = JSON.parse(d);
      if (m.t === 'welcome') { me = m.id; seq = m.q; }
      if (m.t === 'sk' && m.id === me) { rolls.push(m.s); if (rolls.length >= 7) { ws.close(); res({ rolls, kfxs }); } else setTimeout(die, 150); }
      if (m.t === 'spawn') seq = m.q;
      if (m.t === 'kill' && m.v === me) { deaths++; setTimeout(() => send({ t: 'respawn' }), 100); }
    });
    ws.on('error', rej);
    setTimeout(() => rej(new Error('timeout, rolls ' + rolls.length)), 60000);
  });
}
(async () => {
  let bad = 0;
  const a = await run({ finish: ['camo', 'gold', 'crown'], hat: ['cowboy'], only: ['finish'] });
  const w = a.rolls.map((s) => s.ar[0]), h = a.rolls.map((s) => s.ar[1]), e = a.rolls.map((s) => s.ar[2]), km = a.rolls.map((s) => s.knife[3]);
  console.log('favs-only wraps', w.join(','), '| hats', h.join(','), '| effects', e.join(','), '| knife skins', km.join(','), '| modes', [...new Set(a.rolls.map((s) => s.ar[4]))].join(','));
  if (!w.every((x) => x === 'camo' || x === 'gold')) { bad++; console.log('FAIL: wrap outside favourites'); }
  if (new Set(w).size < 2) { bad++; console.log('FAIL: wrap never changed'); }
  if (!h.every((x) => OWN.hat.includes(x))) { bad++; console.log('FAIL: hat not owned'); }
  if (new Set(h).size < 2) { bad++; console.log('FAIL: hat never changed'); }
  if (!e.every((x) => OWN.effect.includes(x))) { bad++; console.log('FAIL: effect not owned'); }
  if (!km.every((x) => ['default', 'knife_kitchen', 'knife_bowie'].includes(x))) { bad++; console.log('FAIL: knife skin not owned / wrong weapon'); }
  if (a.rolls.some((s) => s.ar[4] !== 'full')) { bad++; console.log('FAIL: wrap mode lost'); }
  const b = await run({ only: [] });
  const w2 = b.rolls.map((s) => s.ar[0]);
  console.log('all-owned wraps', w2.join(','));
  if (!w2.every((x) => OWN.finish.includes(x))) { bad++; console.log('FAIL: wrap not owned'); }
  if (new Set(w2).size < 3) { bad++; console.log('FAIL: too few distinct'); }
  console.log(bad ? `${bad} FAIL` : 'ALL OK');
  process.exit(bad ? 1 : 0);
})().catch((e) => { console.log('ERR', e.message); process.exit(1); });
