// bots earn and use the overdrive rig (ws only). run the server with JF_RIG=2. usage: node t_rigbots.cjs [secs]
// ws from the game's checkout (regress2.sh exports JF_REPO), else from here
const WebSocket = (() => { for (const p of [process.env.JF_REPO, process.cwd(), __dirname + '/../..'].filter(Boolean)) { try { return require(require.resolve('ws', { paths: [p] })); } catch { /* next */ } } throw new Error('ws not found: set JF_REPO to the game checkout'); })();
const PORT = process.env.PORT || 3000, SECS = Number(process.env.RIGBOT_SECS || 45);
const ws = new WebSocket(`ws://localhost:${PORT}/ws`);
const ev = {}, kills = {}, rigBots = new Set(), flagSeen = { RIG: 0, BLOCK: 0, CHARGE: 0, LEAP: 0 };
let errs = 0, me = 0;
ws.on('open', () => ws.send(JSON.stringify({ t: 'join', name: 'watcher', mode: 'bots', cfg: { bots: 9, diff: 'hard' }, streaks: ['moonboots', 'scythe', 'overdrive'], item: 'frag' })));
ws.on('message', (d) => {
  const m = JSON.parse(d);
  if (m.t === 'welcome') me = m.id;
  if (m.t === 'rig') { ev[m.k] = (ev[m.k] || 0) + 1; if (m.k === 'on') rigBots.add(m.id); }
  if (m.t === 'kill' && /^rig/.test(m.w)) kills[m.w] = (kills[m.w] || 0) + 1;
  if (m.t === 'sn') for (const p of m.p) { const f = p[13]; if (f & 16384) { flagSeen.RIG++; if (f & 32768) flagSeen.BLOCK++; if (f & 65536) flagSeen.CHARGE++; if (f & 131072) flagSeen.LEAP++; } }
  if (m.t === 'err') errs++;
});
setTimeout(() => {
  console.log('rig bots', [...rigBots].length, 'events', JSON.stringify(ev));
  console.log('rig kills', JSON.stringify(kills), 'flag frames', JSON.stringify(flagSeen));
  const ok = rigBots.size > 0 && ev.punch > 0 && (ev.hit || 0) + (ev.miss || 0) > 0 && ev.thrust > 0 && flagSeen.RIG > 0; // (thrust: bots fly up to people, dodge, chase, save themselves)
  console.log(ok ? 'no errors' : 'FAIL: bots never used the rig');
  process.exit(ok ? 0 : 1);
}, SECS * 1000);
