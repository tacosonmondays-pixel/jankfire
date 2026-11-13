// the slower blimp, server-side (shared/royale.js BR.blimp.speed, and server/royale.js stamps path.v). Jank Royale and
// Battle Island (which rides on the royale) both send a blimp path with v = the server's speed, ~23% slower than the
// old 24 m/s, and blimpAt moves at exactly that. Two servers, one after the other.
// starts its own servers: node tests/mapdetail_ws.cjs [port]
const WS = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const port = Number(process.argv[2]) || 3176;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };
const near = (a, b, e = 0.01) => Math.abs(a - b) <= e;

async function getPath(game) {
  const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_TRAFFIC: 'off', JF_GAME: game }, stdio: ['ignore', 'pipe', 'pipe'] });
  let err = ''; srv.stderr.on('data', (d) => { err += d; }); srv.stdout.on('data', (d) => { if (/Error|uncaught/i.test(String(d))) err += d; });
  for (let i = 0; i < 60; i++) { try { await new Promise((res, rej) => { const w = new WS(`ws://localhost:${port}/ws`); w.on('open', () => { w.close(); res(); }); w.on('error', rej); }); break; } catch { await sleep(500); } }
  const ws = new WS(`ws://localhost:${port}/ws`);
  const got = { path: null };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'br' && m.k === 'start' && m.path && !got.path) got.path = m.path; });
  await new Promise((res) => ws.on('open', res));
  ws.send(JSON.stringify({ t: 'join', name: 'Jumper', mode: 'ffa' }));
  for (let i = 0; i < 60 && !got.path; i++) await sleep(250);
  ws.close();
  await new Promise((res) => { srv.on('exit', res); srv.kill(); });
  return { path: got.path, err };
}

(async () => {
  const { blimpAt, BR } = await import('../shared/royale.js');
  const OLD = 24, lo = OLD * 0.75, hi = OLD * 0.8; // "20-25% slower" = 18 to 19.2 m/s
  ok(BR.blimp.speed >= lo && BR.blimp.speed <= hi, `the blimp speed is ${BR.blimp.speed} m/s (20-25% slower than ${OLD})`);

  for (const game of ['br', 'island']) {
    const { path: pth, err } = await getPath(game);
    ok(!!pth, `${game}: got a blimp path`);
    if (!pth) { ok(false, `${game}: no path, skipping`); continue; }
    ok(near(pth.v, BR.blimp.speed), `${game}: the path carries the server's speed (v=${pth.v})`);
    // blimpAt uses path.v: 10 s of travel (after the 2.5 s wait) covers v * 10 metres
    const d10 = blimpAt(pth, pth.t0 + (BR.blimp.wait + 10) * 1000);
    const moved = Math.hypot(d10[0] - pth.a[0], d10[2] - pth.a[1]);
    ok(near(moved, pth.v * 10, 1.5), `${game}: blimpAt moves at v (${moved.toFixed(1)} m in 10 s, want ${(pth.v * 10).toFixed(0)})`);
    // the slower speed means it takes longer to cross: old 24 covered the full path (len*2) in len*2/24 s; now it's longer
    const fullOld = (BR.blimp.len * 2) / OLD, fullNow = (BR.blimp.len * 2) / pth.v;
    ok(fullNow > fullOld * 1.2, `${game}: a full crossing takes ${fullNow.toFixed(1)} s now vs ${fullOld.toFixed(1)} s before (more time to pick a spot)`);
    ok(!/Error|uncaught/i.test(err), `${game}: no server errors`);
  }
  console.log(fails ? `${fails} FAILED` : 'ALL OK'); process.exit(fails ? 1 : 0);
})();
