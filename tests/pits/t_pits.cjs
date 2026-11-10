// ws test for the pits: start a server (PORT=3190 node server.js), then: node tests/pits/t_pits.cjs 3190
// the lava pit burns over time and kills with hz, the afterburn stops, the sea / canyon / street kill at their surface
const WS = require('ws');
const port = process.argv[2] || 3190, sleep = (ms) => new Promise((r) => setTimeout(r, ms));
function client(name, map, mode = 'bots') {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, msgs: [], id: 0, seq: 0, hp: 100, alive: false, pos: null, kills: [], sizz: 0, burns: 0 };
  ws.on('open', () => ws.send(JSON.stringify({ t: 'join', name, mode, cfg: { map, bots: 0, botCount: 0, game: 'dm' } })));
  ws.on('message', (d) => { let m; try { m = JSON.parse(d); } catch (e) { return; }
    if (!c.first) { c.first = m; }
    if (m.t === 'init' || m.t === 'welcome') { c.id = m.id; c.init = m; }
    if (m.t === 'spawn' && (m.id === c.id || m.id == null)) { c.alive = true; c.seq = m.q ?? m.seq ?? c.seq; c.pos = m.p || m.pos; c.spawn = m; }
    if (m.t === 'kill') { c.kills.push(m); if (m.v === c.id) c.alive = false; }
    if (m.t === 'sizzle' && m.id === c.id) c.sizz++;
    if (m.t === 'fx' && m.k === 'burn' && m.id === c.id) c.burns++;
    if (m.t === 'hp' || m.hp != null && m.id === c.id) c.hp = m.hp;
    c.types = c.types || {}; c.types[m.t] = (c.types[m.t] || 0) + 1; c.last = c.last || {}; c.last[m.t] = m;
  });
  c.at = (p) => ws.send(JSON.stringify({ t: 's', q: c.seq, p, v: [0, 0, 0], y: 0, x: 0, w: 'knife' }));
  return c;
}
module.exports = { client, sleep };
if (require.main === module) (async () => {
  const out = [], ok = (n, v, d) => { out.push(`${v ? 'PASS' : 'FAIL'} ${n} ${d ?? ''}`); };
  const run = async (map, steps) => { const c = client('pit' + map.slice(0, 6), map); await sleep(1800); c.seq = c.first.q; c.alive = true; const r = await steps(c); c.ws.close(); await sleep(300); return r; };
  const hold = (c, p, ms) => new Promise((res) => { const t0 = Date.now(), iv = setInterval(() => { if (!c.alive || Date.now() - t0 > ms) { clearInterval(iv); res(Date.now() - t0); } else c.at(p); }, 50); });
  const hps = (c) => c.msgs;
  // 1. the volcano's lava: burns over time, kills with hz, the bits come back up
  await run('islands', async (c) => {
    await hold(c, [0, 9.4, 2], 600); ok('rim is safe', c.alive && c.sizz === 0, `sizz ${c.sizz}`);
    const ms = await hold(c, [0, 3.9, -3], 6000); const k = c.kills.find((m) => m.v === c.id);
    ok('lava kills', !c.alive && k && k.w === 'lava' && k.hz === 1, JSON.stringify(k));
    ok('over time, not at once', ms > 1200 && ms < 2600 && c.sizz >= 5, `${ms} ms, ${c.sizz} sizzles`);
    ok('erupts', k && k.vel[1] > 10, k && k.vel);
  });
  // 2. hop in and out: afterburn, survive
  await run('islands', async (c) => {
    await hold(c, [0, 3.9, -3], 420); const s = c.sizz; await hold(c, [0, 9.4, 2], 2600);
    ok('afterburn then it stops', c.alive && c.burns >= 3 && c.burns <= 6 && c.sizz === s, `sizz ${s} burns ${c.burns}`);
  });
  // 3. the sea: dead as your head goes under, fine while wading
  await run('islands', async (c) => {
    await hold(c, [26, -0.55, 0], 500); ok('wading is fine', c.alive);
    await hold(c, [40, -2.0, 30], 400); ok('neck deep still alive', c.alive);
    await hold(c, [40, -2.4, 30], 1500); const k = c.kills.find((m) => m.v === c.id); ok('under = void kill', !c.alive && k && k.w === 'void', JSON.stringify(k).slice(0, 120));
  });
  for (const [map, p, y0, y1] of [['desert', [0, 0, 30], -64, -65.7], ['platform', [60, 0, 0], -15.5, -16.3], ['rooftop', [26, 0, 5], -160, -161.7], ['skyline', [30, 0, 30], -118, -119.8]]) await run(map, async (c) => {
    if (c.first.cfg.map !== map) { ok(map + ' picked', false, c.first.cfg.map); return; }
    if (y1 == null) { await hold(c, [p[0], y0, p[2]], 6000); const k = c.kills.find((m) => m.v === c.id); ok(map + ' lava kills', !c.alive && k && k.hz === 1); return; }
    await hold(c, [p[0], y0, p[2]], 500); const a = c.alive; await hold(c, [p[0], y1, p[2]], 1500); const k = c.kills.find((m) => m.v === c.id);
    ok(`${map}: alive at ${y0}, dead at ${y1}`, a && !c.alive && k && k.w === 'void');
  });
  console.log(out.join('\n')); process.exit(out.some((l) => l.startsWith('FAIL')) ? 1 : 0);
})();
