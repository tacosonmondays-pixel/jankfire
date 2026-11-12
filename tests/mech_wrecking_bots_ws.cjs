// WRECKING BALL, bots: a bots-only match (a JF_WATCH observer) where every bot's mech is the ball (JF_MECH_FRAME) and
// the ult charges fast (JF_MECH_ULT): they roll at people, rev-launch, chain up, slam crowds and pile-drive.
// starts its own server: node tests/mech_wrecking_bots_ws.cjs [port] [seconds] [map]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3163, secs = Number(process.argv[3]) || 80, map = process.argv[4] || 'warehouse';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
(async () => {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_MECH: '1', JF_WATCH: '1', JF_MECH_HP: '0.5', JF_MECH_FRAME: 'wrecking', JF_MECH_ULT: '8' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const ws = new WS(`ws://localhost:${port}/ws`), names = new Map(), seen = {}, inMech = new Map(), moved = new Map(), log = [];
  const count = (k) => { seen[k] = (seen[k] || 0) + 1; };
  let topV = 0;
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') for (const p of m.players || []) names.set(p.id, p.name);
    if (m.t === 'pj') names.set(m.id, m.name);
    if (m.t === 'sn') { for (const e of m.p) if (inMech.has(e[0]) && (e[13] & (1 << 22))) { const a = inMech.get(e[0]); if (!a.p0) a.p0 = [e[1], e[3]]; moved.set(e[0], Math.max(moved.get(e[0]) || 0, Math.hypot(e[1] - a.p0[0], e[3] - a.p0[1]))); } return; }
    if (m.t === 'dmg' && typeof m.w === 'string' && m.w.startsWith('wb')) count('dmg:' + m.w);
    if (m.t !== 'mech') return;
    const k = m.k === 'wbrev' ? 'wbrev' + m.on : m.k === 'wbquake' ? (m.big ? 'pile!' : 'slam!') : m.k === 'wbchain' ? (m.off ? 'chainoff' : 'chain') : m.k === 'wbpile' ? 'pile:' + m.ph : m.k;
    count(k);
    if (m.k === 'wbrev' && m.on === 2) topV = Math.max(topV, m.v);
    if (m.k === 'in') inMech.set(m.id, { f: m.f });
    if (/^(in|down|wbrev2|chain|slam!|pile!|pile:up|pile:down)$/.test(k) || (m.k === 'ram' && m.w === 'wbram')) log.push(`${(Date.now() / 1000 % 1000).toFixed(1)} ${names.get(m.id) || m.id} ${k}${m.f ? ' ' + m.f : ''}${m.to && !Array.isArray(m.to) ? ' -> ' + (names.get(m.to) || m.to) : ''}`);
  });
  ws.on('open', () => ws.send(JSON.stringify({ t: 'join', name: 'watcher', mode: 'bots', cfg: { bots: 8, map, diff: 'hard' } })));
  await sleep(secs * 1000);
  for (const l of log.slice(0, 50)) console.log('  ' + l);
  console.log('  events:', JSON.stringify(seen));
  console.log('  moved (m):', JSON.stringify([...moved.values()].map((x) => Math.round(x))), 'top launch', topV);
  const frames = [...inMech.values()].map((x) => x.f);
  ok(frames.length >= 1 && frames.every((f) => f === 'wrecking'), `bots climb into wrecking balls (${frames.length})`);
  ok([...moved.values()].some((x) => x > 15), 'they roll around');
  ok((seen['dmg:wbram'] || 0) >= 1, `they ram people (${seen['dmg:wbram'] || 0} rams)`);
  ok((seen.wbrev2 || 0) >= 1, `they rev-launch (${seen.wbrev2 || 0})`);
  ok((seen['slam!'] || 0) >= 1, `they slam (${seen['slam!'] || 0})`);
  ok((seen['pile:up'] || 0) >= 1 && (seen['pile!'] || 0) >= 1, `they PILE DRIVE (${seen['pile:up'] || 0} launched, ${seen['pile!'] || 0} landed)`);
  console.log(`  (chain: ${seen.chain || 0} throws: only where something's above them)`);
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 800) : ''));
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
