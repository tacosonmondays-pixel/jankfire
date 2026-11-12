// battle island, bots: a bots-only island match (a JF_WATCH observer, no fighter) on a royale map with a quick zone
// (JF_ISLE_ZONE). 17 bots in 6 squads: they jump with their squad, go down, pick each other up, and play to a last
// squad standing. logs what they did. starts its own server: node tests/island_bots_ws.cjs [port] [max seconds]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3181, secs = Number(process.argv[3]) || 260;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const failed = []; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) { fails++; failed.push(msg.slice(0, 80)); } };
(async () => {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_WATCH: '1', JF_ISLE_LOG: '1', JF_ISLE_ZONE: process.env.JF_ISLE_ZONE || '0.6', JF_ISLE_METER: process.env.JF_ISLE_METER || '3' }, stdio: ['ignore', 'pipe', 'pipe'] });
  let srvErr = '', srvOut = ''; srv.stderr.on('data', (d) => { srvErr += d; }); srv.stdout.on('data', (d) => { srvOut += d; if (/Error|uncaught/i.test(String(d))) srvErr += d; });
  process.on('exit', () => srv.kill());
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const ws = new WS(`ws://localhost:${port}/ws`), names = new Map(), seen = {}, sq = new Map(), jumps = [], heroes = new Map(), cells = new Set(), mech = {};
  let cellTakes = 0;
  let win = null, over = null;
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') for (const p of m.players || []) names.set(p.id, p.name);
    if (m.t === 'pj') names.set(m.id, m.name);
    if (m.t === 'br' && m.k === 'jump') jumps.push([m.id, Date.now()]);
    if (m.t === 'br' && m.k === 'win') win = m;
    if (m.t === 'br' && m.k === 'start') for (const l of m.loot) if (l[1] === 'cell') cells.add(l[0]);
    if (m.t === 'br' && m.k === 'take' && cells.has(m.i)) cellTakes++;
    if (m.t === 'mech') mech[m.k] = (mech[m.k] || 0) + 1;
    if (m.t === 'round' && m.over) over = m;
    if (m.t !== 'isle') return;
    seen[m.k] = (seen[m.k] || 0) + 1;
    if (m.k === 'rvx') seen['rvx:' + m.why] = (seen['rvx:' + m.why] || 0) + 1;
    if (m.k === 'sq') { for (const [id, s] of m.l) sq.set(id, s); for (const [id, h] of m.hero || []) heroes.set(id, h); }
  });
  ws.on('open', () => ws.send(JSON.stringify({ t: 'join', name: 'watcher', mode: 'bots', cfg: { bots: 8, map: process.env.ISLE_TEST_MAP || 'jankburg', diff: 'hard', game: 'island' } })));
  const t0 = Date.now();
  while (!over && Date.now() - t0 < secs * 1000) await sleep(1000);
  for (const l of srvOut.split('\n').filter((l) => l.startsWith('[isle]'))) console.log('  ' + l);
  console.log('  events:', JSON.stringify(seen), `match took ${Math.round((Date.now() - t0) / 1000)}s`);
  const sizes = {}; for (const s of sq.values()) sizes[s] = (sizes[s] || 0) + 1;
  console.log('  squads:', JSON.stringify(sizes));
  ok(sq.size === 17 && Object.keys(sizes).length === 6 && Object.values(sizes).every((n) => n <= 3), `17 bots in 6 squads of up to 3 (${JSON.stringify(sizes)})`);
  // squads jump together: bots in the same squad leave the blimp within a moment of each other
  const bySq = new Map(); for (const [id, t] of jumps) { const s = sq.get(id); if (s) (bySq.get(s) || bySq.set(s, []).get(s)).push(t); }
  const together = [...bySq.values()].filter((ts) => ts.length >= 2 && Math.max(...ts) - Math.min(...ts) < 600).length;
  ok(together >= 4, `squads jump together (${together}/6 squads left the blimp within 0.6 s)`);
  ok((seen.down || 0) >= 3, `bots go down (${seen.down || 0} downs)`);
  ok((seen.rv || 0) >= 1 && (seen.down || 0) >= 3, `bots go for downed squadmates (a revive is a coin flip in a firefight; how each ended: ${seen.rv || 0} started, ${seen.up || 0} done, ${seen.rvx || 0} interrupted)`);
  ok((seen.sqout || 0) >= 4, `squads get knocked out (${seen.sqout || 0})`);
  ok(!!win && win.sq > 0 && Array.isArray(win.ids) && win.ids.every((id) => sq.get(id) === win.sq), `a last squad standing: ${win ? `squad ${win.sq} (${(win.ids || []).map((id) => names.get(id)).join(', ')})` : 'none'}`);
  ok(!!over && over.isle && over.isle.win === (win && win.sq) && over.isle.sq.length === 6, 'the round end lists every squad and the winner');
  console.log('  mechs:', JSON.stringify(mech), `cells: ${cellTakes} of ${cells.size} picked up`);
  const byHero = new Map(); for (const [id, h] of heroes) { const k = sq.get(id) + ':' + h; byHero.set(k, (byHero.get(k) || 0) + 1); }
  ok(heroes.size === 17 && [...byHero.values()].every((n) => n <= 2), `every bot has a hero, at most 2 of one per squad of 3 (${JSON.stringify(Object.fromEntries(byHero))})`);
  ok(cells.size >= 10 && cellTakes >= 3, `bots pick up energy cells (${cellTakes})`);
  ok((seen.call || 0) >= 1 && (mech.in || 0) >= 1, `bots call their mechs in near fights and climb in (${seen.call || 0} calls, ${mech.in || 0} in)`);
  ok((mech.down || 0) + (mech.gone || 0) >= 1, `mechs end (${mech.down || 0} blown up, ${mech.gone || 0} flew off)`);
  ok(!/uncaught|TypeError|ReferenceError|RangeError/.test(srvErr), 'no server errors' + (srvErr ? ': ' + srvErr.slice(0, 800) : ''));
  console.log(fails ? `${fails} FAILED: ${failed.join(' | ')}` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
