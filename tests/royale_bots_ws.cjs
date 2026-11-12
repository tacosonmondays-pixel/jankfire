// jank royale still plays solo next to battle island: a bots-only royale (a JF_WATCH observer, a quick zone) plays to one
// winner with no squads, no downs, RETURN TO SENDER still on and placements per person.
// starts its own server: node tests/royale_bots_ws.cjs [port] [max seconds]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3185, secs = Number(process.argv[3]) || 260;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
(async () => {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_WATCH: '1', JF_ISLE_ZONE: '0.3' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const ws = new WS(`ws://localhost:${port}/ws`), seen = {}, places = [];
  let win = null, over = null, game = '';
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'round' && m.start) game = m.game;
    if (m.t === 'isle') seen['isle:' + m.k] = (seen['isle:' + m.k] || 0) + 1;
    if (m.t === 'br') { seen[m.k] = (seen[m.k] || 0) + 1; if (m.k === 'out') places.push(m.place); if (m.k === 'win') win = m; }
    if (m.t === 'round' && m.over) over = m;
  });
  ws.on('open', () => ws.send(JSON.stringify({ t: 'join', name: 'watcher', mode: 'bots', cfg: { bots: 8, map: 'jankburg', diff: 'hard', game: 'br' } })));
  const t0 = Date.now();
  while (!over && Date.now() - t0 < secs * 1000) await sleep(1000);
  console.log('  events:', JSON.stringify(seen), `places: ${places.join(',')}`, `match took ${Math.round((Date.now() - t0) / 1000)}s`);
  ok(game === 'br', 'it plays Jank Royale');
  ok(!Object.keys(seen).some((k) => k.startsWith('isle:')), 'no squads, no downs');
  ok((seen.mail || 0) >= 1, `RETURN TO SENDER still happens (${seen.mail || 0})`);
  ok(places.length >= 10 && places.every((p) => p >= 2) && new Set(places).size === places.length, 'everyone out gets their own place');
  ok(!!win && win.id > 0 && !win.sq, 'one winner (a person, not a squad)');
  ok(!!over && !over.isle && over.br && over.br.filter((r) => r[1] === 1).length === 1, 'the round end has one #1');
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 800) : ''));
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
