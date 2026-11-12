// island arena, bots: a bots-only 6v6 (a JF_WATCH observer, no fighter) on Battle Island. every bot gets a hero and
// starts in its mech; they fight in mechs, eject, call their mechs again when the meter's full, stay inside the fence,
// and play to a winner. a short match (JF_ARENA_KILLS / JF_ARENA_TIME) and a quicker meter (JF_ISLE_METER).
// starts its own server: node tests/arena_bots_ws.cjs [port] [max seconds]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3195, secs = Number(process.argv[3]) || 420;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const failed = []; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) { fails++; failed.push(msg.slice(0, 80)); } };
(async () => {
  const env = { ...process.env, PORT: String(port), JF_WATCH: '1', JF_WIP_MAPS: '1', JF_ARENA_LOG: '1', JF_ARENA_KILLS: process.env.JF_ARENA_KILLS || '8', JF_ARENA_TIME: process.env.JF_ARENA_TIME || '360', JF_ISLE_METER: process.env.JF_ISLE_METER || '3' };
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = '', srvOut = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { srvOut += d; if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const ws = new WS(`ws://localhost:${port}/ws`), names = new Map(), team = new Map(), heroes = new Map(), mech = {}, kills = [], ins = new Map(), calls = new Map();
  let over = null, st = null, sc = [];
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') for (const p of m.players || []) { names.set(p.id, p.name); team.set(p.id, p.team); }
    if (m.t === 'pj') { names.set(m.id, m.name); team.set(m.id, m.team); }
    if (m.t === 'teams') for (const [id, t] of m.list) team.set(id, t);
    if (m.t === 'mech') { mech[m.k] = (mech[m.k] || 0) + 1; if (m.k === 'in') ins.set(m.id, (ins.get(m.id) || 0) + 1); }
    if (m.t === 'isle' && m.k === 'hero') heroes.set(m.id, m.h);
    if (m.t === 'isle' && m.k === 'call') calls.set(m.id, (calls.get(m.id) || 0) + 1);
    if (m.t === 'kill') kills.push(m);
    if (m.t === 'arena' && m.k === 'st') st = m;
    if (m.t === 'arena' && m.k === 'sc') sc.push(m);
    if (m.t === 'round' && m.over) over = m;
  });
  ws.on('open', () => ws.send(JSON.stringify({ t: 'join', name: 'watcher', mode: 'bots', cfg: { bots: 12, map: 'battleisland', diff: 'hard', game: 'arena' } })));
  const t0 = Date.now();
  while (!over && Date.now() - t0 < secs * 1000) await sleep(1000);
  for (const l of srvOut.split('\n').filter((l) => l.startsWith('[arena]')).slice(-40)) console.log('  ' + l);
  const took = Math.round((Date.now() - t0) / 1000);
  console.log('  mech events:', JSON.stringify(mech), `match took ${took}s`);
  const sizes = { 1: 0, 2: 0 }; for (const [id, t] of team) if (names.get(id) !== 'watcher' && t) sizes[t] = (sizes[t] || 0) + 1;
  ok(sizes[1] === 6 && sizes[2] === 6, `6v6 bots (${JSON.stringify(sizes)})`);
  ok(st && Array.isArray(st.area) && st.target > 0, `the match is on: area ${st && JSON.stringify(st.area)}, first to ${st && st.target}`);
  const byHero = {}; for (const [id, h] of heroes) { const k = team.get(id) + ':' + h; byHero[k] = (byHero[k] || 0) + 1; }
  ok(heroes.size >= 12 && Object.values(byHero).every((n) => n <= 3), `every bot has a hero, at most 3 of one a team (${JSON.stringify(byHero)})`);
  ok([...ins.keys()].length >= 10, `bots start in their mechs (${ins.size} climbed in)`);
  ok((mech.down || 0) >= 3 && sc.length >= 3, `mechs break: ${mech.down || 0} MECH DOWNs, ${sc.length} scored`);
  const recall = [...calls.values()].filter((n) => n >= 2).length;
  ok(recall >= 2, `bots call their mechs again when the meter fills (${recall} bots called 2+ times)`);
  const sea = kills.filter((k) => k.w === 'void' || k.w === 'sea' || k.w === 'oob');
  ok(!sea.length, `no deaths by sea or void (${sea.length}; ${kills.length} deaths in all)`);
  ok(!!over && over.winTeam > 0 && Array.isArray(over.sc), `a winner: ${over ? (over.winTeam === 1 ? 'RED' : 'BLUE') + ' ' + over.sc.join('-') : 'none'} after ${took}s`);
  ok(over && sc.length && sc[sc.length - 1].sc.join() === over.sc.join(), 'the end score is the mech kills');
  const fences = srvOut.split('\n').filter((l) => l.includes('fence:')).length;
  console.log(`  fence pushes: ${fences}`);
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 800) : ''));
  console.log(fails ? `${fails} FAILED: ${failed.join(' | ')}` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
