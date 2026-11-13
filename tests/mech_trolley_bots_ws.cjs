// TROLLEY, bots: a bots-only Team Deathmatch (a JF_WATCH observer, so the bots have allies) where every bot's mech is
// the trolley (JF_MECH_FRAME) and the ult charges fast (JF_MECH_ULT): they race about, drift to build the ram charge
// (the DRIFT flag in their snapshots, at speed), push people, toss cans, CLEAN UP AISLE 5 (scoop and dump), and allies
// hop into the child seat now and then.
// starts its own server: node tests/mech_trolley_bots_ws.cjs [port] [seconds] [map]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3745, secs = Number(process.argv[3]) || 150, map = process.argv[4] || 'warehouse';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const MECHF = 1 << 22, DRIFT = 1 << 23;
(async () => {
  const taken = await new Promise((res) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(true); }); w.on('error', () => res(false)); });
  if (taken) { console.log(`port ${port} is taken: pick another`); process.exit(2); }
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_MECH: '1', JF_WATCH: '1', JF_MECH_HP: '0.5', JF_MECH_FRAME: 'trolley', JF_MECH_ULT: '6' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const ws = new WS(`ws://localhost:${port}/ws`), names = new Map(), seen = {}, inMech = new Map(), moved = new Map(), top = new Map(), drifted = new Set(), log = [];
  const count = (k, n = 1) => { seen[k] = (seen[k] || 0) + n; };
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') for (const p of m.players || []) names.set(p.id, p.name);
    if (m.t === 'pj') names.set(m.id, m.name);
    if (m.t === 'sn') {
      for (const e of m.p) {
        if (!inMech.has(e[0]) || !(e[13] & MECHF)) continue;
        const a = inMech.get(e[0]); if (!a.p0) a.p0 = [e[1], e[3]];
        moved.set(e[0], Math.max(moved.get(e[0]) || 0, Math.hypot(e[1] - a.p0[0], e[3] - a.p0[1])));
        if (a.last) { const dt = (m.s - a.last.s) / 1000; if (dt > 0.05 && dt < 0.5) top.set(e[0], Math.max(top.get(e[0]) || 0, Math.hypot(e[1] - a.last.x, e[3] - a.last.z) / dt)); }
        a.last = { s: m.s, x: e[1], z: e[3] };
        if (e[13] & DRIFT) drifted.add(e[0]);
      }
      return;
    }
    if (m.t === 'dmg' && typeof m.w === 'string' && m.w.startsWith('tr')) count('dmg:' + m.w);
    if (m.t === 'chat' && /hopped in/.test(m.m || '')) { count('hopin'); log.push('  ' + m.m); }
    if (m.t !== 'mech') return;
    const k = m.k === 'trhold' ? `hold:${m.s || ''}:${m.on ? 'on' : 'off:' + m.why}` : m.k === 'traisle' ? `aisle:${m.on ? 'on' : 'off:' + m.why}` : m.k;
    if (m.k === 'en' || m.k === 'trtoss') { count(m.k); return; }
    count(k);
    if (m.k === 'in') inMech.set(m.id, { f: m.f });
    if (m.k === 'trpush') count(m.c >= 0.6 ? 'push:charged' : 'push:flat');
    if (/^(in|down|trpush|traisle|trhold)$/.test(m.k)) log.push(`${(Date.now() / 1000 % 1000).toFixed(1)} ${names.get(m.id) || m.id} ${k}${m.f ? ' ' + m.f : ''}${m.v ? ' -> ' + (names.get(m.v) || m.v) : ''}${m.k === 'trpush' ? ' c' + m.c : ''}`);
  });
  ws.on('open', () => ws.send(JSON.stringify({ t: 'join', name: 'watcher', mode: 'bots', cfg: { bots: 10, map, diff: 'hard', game: 'tdm' } })));
  await sleep(secs * 1000);
  for (const l of log.slice(0, 70)) console.log('  ' + l);
  console.log('  events:', JSON.stringify(seen));
  console.log('  moved (m):', JSON.stringify([...moved.values()].map((x) => Math.round(x))), 'top speeds:', JSON.stringify([...top.values()].map((x) => Math.round(x))));
  const frames = [...inMech.values()].map((x) => x.f);
  ok(frames.length >= 2 && frames.every((f) => f === 'trolley'), `bots climb into trolleys (${frames.length})`);
  ok([...moved.values()].some((x) => x > 25) && [...top.values()].some((x) => x > 18), 'they race about');
  ok(drifted.size >= 1, `they drift (${drifted.size} trolleys showed the drift flag)`);
  ok((seen['push:charged'] || 0) >= 1, `they push with a built-up charge (${seen['push:charged'] || 0} charged, ${seen['push:flat'] || 0} flat)`);
  ok((seen['dmg:trpush'] || 0) >= 1, `pushes land (${seen['dmg:trpush'] || 0})`);
  ok((seen.trtoss || 0) >= 10 && (seen['dmg:trcan'] || 0) >= 2, `they toss cans (${seen.trtoss || 0} thrown, ${seen['dmg:trcan'] || 0} bonks)`);
  ok((seen['aisle:on'] || 0) >= 1, `they CLEAN UP AISLE 5 (${seen['aisle:on'] || 0})`);
  ok((seen['hold:scoop:on'] || 0) >= 1 && (seen['hold:scoop:off:dump'] || 0) + (seen['hold:scoop:off:dead'] || 0) >= 1, `they scoop people and dump them (${seen['hold:scoop:on'] || 0} scooped, ${seen['hold:scoop:off:dump'] || 0} dumped)`);
  console.log(`  (allies hopping in: ${seen['hold:ride:on'] || 0}; rams: ${seen['dmg:trram'] || 0})`);
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 800) : ''));
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
