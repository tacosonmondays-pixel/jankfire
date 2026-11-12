// mech drop, bots: a bots-only match (a JF_WATCH observer, no fighter) where bots earn the mech after one kill
// (JF_MECH=1), call it in near the fight, climb in, move, attack with both frames, and get ejected / blown up.
// logs what they do. starts its own server: node tests/mech_bots_ws.cjs [port] [seconds]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3149, secs = Number(process.argv[3]) || 75;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
(async () => {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_MECH: '1', JF_WATCH: '1', JF_MECH_HP: '0.5' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const ws = new WS(`ws://localhost:${port}/ws`), names = new Map(), log = [], seen = {}, frames = {}, inMech = new Map(), moved = new Map();
  const count = (k) => { seen[k] = (seen[k] || 0) + 1; };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') for (const p of m.players || []) names.set(p.id, p.name);
    if (m.t === 'pj') names.set(m.id, m.name);
    if (m.t === 'sn') { for (const e of m.p) if (inMech.has(e[0]) && (e[13] & (1 << 22))) { const a = inMech.get(e[0]); if (!a.p0) a.p0 = [e[1], e[3]]; moved.set(e[0], Math.max(moved.get(e[0]) || 0, Math.hypot(e[1] - a.p0[0], e[3] - a.p0[1]))); } return; }
    if (m.t === 'dmg' && typeof m.w === 'string' && m.w.startsWith('mech')) count('dmg:' + m.w);
    if (m.t !== 'mech') return;
    count(m.k);
    const pid = m.k === 'call' || m.k === 'land' ? m.o : m.id, who = names.get(pid) || pid;
    if (m.k === 'in') { frames[m.f] = (frames[m.f] || 0) + 1; inMech.set(m.id, { f: m.f }); }
    if (['call', 'land', 'in', 'out', 'down', 'clock', 'quake', 'jet', 'lunge', 'triple', 'swarm', 'crane', 'stomp', 'squash'].includes(m.k)) log.push(`${(Date.now() / 1000 % 1000).toFixed(1)} ${who} ${m.k}${m.f ? ' ' + m.f : ''}${m.to ? ' -> ' + (names.get(m.to) || m.to) : ''}${m.by ? ' by ' + (names.get(m.by) || m.by) : ''}`);
  });
  ws.on('open', () => ws.send(JSON.stringify({ t: 'join', name: 'watcher', mode: 'bots', cfg: { bots: 8, map: 'warehouse', diff: 'hard' } })));
  await sleep(secs * 1000);
  for (const l of log.slice(0, 60)) console.log('  ' + l);
  console.log('  events:', JSON.stringify(seen));
  console.log('  frames:', JSON.stringify(frames), 'moved (m):', JSON.stringify([...moved.values()].map((x) => Math.round(x))));
  ok((seen.call || 0) >= 1 && (seen.land || 0) >= 1, `bots call mechs in (${seen.call} calls, ${seen.land} landings)`);
  ok((seen.in || 0) >= 1, `bots climb in (${seen.in})`);
  ok([...moved.values()].some((x) => x > 8), 'bots move their mechs around');
  const atk = ['gun', 'swing', 'swarm', 'crane', 'lunge', 'jet', 'triple', 'quake'].filter((k) => seen[k]);
  ok(atk.length >= 2 && Object.keys(seen).some((k) => k.startsWith('dmg:mech')), `bots attack from their mechs (${atk.join(', ')}; damage: ${Object.keys(seen).filter((k) => k.startsWith('dmg:')).join(', ')})`);
  ok((seen.down || 0) + (seen.out || 0) >= 1, `mechs end: ${seen.down || 0} blown up, ${seen.out || 0} out`);
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 800) : ''));
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
