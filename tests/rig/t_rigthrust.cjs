// overdrive rig thrusters, server side (ws only): in training, put the rig on, then try to spam the thrusters. the
// server has to allow 3 bursts, refuse the rest, give one back after 2.6 s, and refuse bursts closer than 0.25 s.
const WebSocket = (() => { for (const p of [process.env.JF_REPO, process.cwd(), __dirname + '/../..'].filter(Boolean)) { try { return require(require.resolve('ws', { paths: [p] })); } catch { /* next */ } } throw new Error('ws not found: set JF_REPO to the game checkout'); })();
const PORT = process.env.PORT || 3000;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const ws = new WebSocket(`ws://localhost:${PORT}/ws`);
  let me = 0, on = false, pocket = [];
  const thr = [];
  ws.on('message', (d) => {
    const m = JSON.parse(d);
    if (m.t === 'welcome') me = m.id;
    if (m.t === 'streak' && Array.isArray(m.pocket)) pocket = m.pocket;
    if (m.t === 'rig' && m.id === me && m.k === 'on') on = true;
    if (m.t === 'rig' && m.id === me && m.k === 'thrust') thr.push(m.n);
  });
  await new Promise((r) => ws.on('open', r));
  const send = (o) => ws.send(JSON.stringify(o));
  send({ t: 'join', name: 'thruster', mode: 'training', streaks: ['overdrive', 'moonboots', 'scythe'], item: 'frag' });
  await sleep(1500);
  for (let i = 0; i < 10 && !on; i++) { send({ t: 'deploy', r: 'overdrive', at: [0, 0, 0] }); await sleep(500); }
  const out = [];
  if (!on) out.push('rig never came on');
  for (let i = 0; i < 6; i++) { send({ t: 'rig', k: 'thrust' }); await sleep(20); } // a burst of spam: only 1 gets through (0.25 s apart)
  await sleep(300);
  const a = thr.length;
  for (let i = 0; i < 5; i++) { send({ t: 'rig', k: 'thrust' }); await sleep(300); } // spaced: 2 more, then empty
  const b = thr.length;
  await sleep(2700);
  send({ t: 'rig', k: 'thrust' }); await sleep(300); // one came back
  send({ t: 'rig', k: 'thrust' }); await sleep(300); // and that's it
  const c = thr.length;
  console.log('spam', a, 'spaced', b, 'after refill', c, 'charges left', JSON.stringify(thr));
  if (a !== 1) out.push(`spam let ${a} through (want 1)`);
  if (b !== 3) out.push(`spaced let ${b} through (want 3)`);
  if (c !== 4) out.push(`refill gave ${c - b} (want 1)`);
  console.log(out.length ? 'FAIL: ' + out.join('; ') : 'no errors');
  ws.close(); process.exit(out.length ? 1 : 0);
})();
