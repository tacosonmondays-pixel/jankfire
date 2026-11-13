// VENDING MACHINE, bots: a bots-only Team Deathmatch (a JF_WATCH observer, so the bots have allies) where every bot's
// mech is the vending machine (JF_MECH_FRAME) and the ult charges fast (JF_MECH_ULT): they coin enemies, dispense
// colas when they or an ally are hurt (and allies drink them), wall off whoever's shooting, RESTOCK their squad, and
// (with the jam turned up, JF_VM_JAM) an allied bot on foot kicks a jammed one.
// starts its own server: node tests/mech_vending_bots_ws.cjs [port] [seconds] [map]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3645, secs = Number(process.argv[3]) || 150, map = process.argv[4] || 'warehouse';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
(async () => {
  const taken = await new Promise((res) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(true); }); w.on('error', () => res(false)); });
  if (taken) { console.log(`port ${port} is taken: pick another`); process.exit(2); }
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_MECH: '1', JF_WATCH: '1', JF_MECH_HP: '0.5', JF_MECH_FRAME: 'vending', JF_MECH_ULT: '6', JF_VM_JAM: '0.25' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const ws = new WS(`ws://localhost:${port}/ws`), names = new Map(), seen = {}, inMech = new Map(), moved = new Map(), log = [];
  const count = (k, n = 1) => { seen[k] = (seen[k] || 0) + n; };
  let bigStock = 0;
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') for (const p of m.players || []) names.set(p.id, p.name);
    if (m.t === 'pj') names.set(m.id, m.name);
    if (m.t === 'sn') { for (const e of m.p) if (inMech.has(e[0]) && (e[13] & (1 << 22))) { const a = inMech.get(e[0]); if (!a.p0) a.p0 = [e[1], e[3]]; moved.set(e[0], Math.max(moved.get(e[0]) || 0, Math.hypot(e[1] - a.p0[0], e[3] - a.p0[1]))); } return; }
    if (m.t === 'dmg' && m.w === 'vmcoin') count('dmg:vmcoin');
    if (m.t !== 'mech') return;
    if (m.k === 'vmcoin' || m.k === 'vmlist' || m.k === 'vmwhit') { count(m.k); return; }
    count(m.k === 'vmdrink' ? (m.to === m.id ? 'vmdrink:self' : 'vmdrink:ally') : m.k);
    if (m.k === 'in') inMech.set(m.id, { f: m.f });
    if (m.k === 'vmstock' && Array.isArray(m.l) && m.l.length >= 2) bigStock++;
    if (/^(in|down|vmwall|vmstock|vmjam|vmkick|vmdrink|vmstuck)$/.test(m.k)) log.push(`${(Date.now() / 1000 % 1000).toFixed(1)} ${names.get(m.id) || m.id} ${m.k}${m.f ? ' ' + m.f : ''}${m.to ? ' -> ' + (names.get(m.to) || m.to) : ''}${m.by ? ' by ' + (names.get(m.by) || m.by) : ''}${m.l ? ' ' + m.l.length + ' restocked' : ''}`);
  });
  ws.on('open', () => ws.send(JSON.stringify({ t: 'join', name: 'watcher', mode: 'bots', cfg: { bots: 10, map, diff: 'hard', game: 'tdm' } })));
  await sleep(secs * 1000);
  for (const l of log.slice(0, 60)) console.log('  ' + l);
  console.log('  events:', JSON.stringify(seen));
  console.log('  moved (m):', JSON.stringify([...moved.values()].map((x) => Math.round(x))));
  const frames = [...inMech.values()].map((x) => x.f);
  ok(frames.length >= 2 && frames.every((f) => f === 'vending'), `bots climb into vending machines (${frames.length})`);
  ok([...moved.values()].some((x) => x > 12), 'they waddle around');
  ok((seen['dmg:vmcoin'] || 0) >= 20, `they coin enemies (${seen['dmg:vmcoin'] || 0} coins landed)`);
  ok((seen.vmcola || 0) >= 2, `they dispense colas (${seen.vmcola || 0})`);
  ok((seen['vmdrink:ally'] || 0) + (seen['vmdrink:self'] || 0) >= 1, `colas get drunk (${seen['vmdrink:ally'] || 0} by allies, ${seen['vmdrink:self'] || 0} by themselves)`);
  ok((seen.vmwall || 0) >= 1, `they put OUT OF ORDER up (${seen.vmwall || 0}; ${seen.vmwhit || 0} hits soaked)`);
  ok((seen.vmstock || 0) >= 1, `they RESTOCK (${seen.vmstock || 0}, ${bigStock} reaching someone else too)`);
  console.log(`  (jams: ${seen.vmjam || 0}, kicked loose by an ally: ${seen.vmkick || 0}, STUCK x2: ${seen.vmstuck || 0})`);
  ok(!(seen.vmjam >= 3) || (seen.vmkick || 0) >= 1, 'an allied bot kicks a jammed one loose');
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 800) : ''));
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
