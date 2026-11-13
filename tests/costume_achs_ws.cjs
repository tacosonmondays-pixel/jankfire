// Poultry in Motion + Sworn Protector over plain ws: a Chicken Rocket kill bumps chicken_kills, a knife kill bumps
// melee_kills, a gun kill bumps neither, and each achievement pops at its goal and is saved to the account.
// Self-contained: starts its own server on a throwaway local account store (JF_DATA_DIR, never Supabase), with one
// account seeded a kill short of both goals.  node tests/costume_achs_ws.cjs [port]
const WS = require('ws');
const fs = require('fs'), os = require('os'), path = require('path'), crypto = require('crypto');
const { spawn } = require('child_process');
const port = Number(process.argv[2]) || 3197;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = 0; const ok = (c, msg) => { console.log((c ? 'ok   ' : 'FAIL ') + msg); if (!c) fails++; };

// the store: one account, 24 chicken kills and 49 melee kills in (the FileStore's own format)
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'jf-achs-'));
const salt = crypto.randomBytes(16).toString('hex'), hash = crypto.scryptSync('cluck1234', salt, 32).toString('hex');
fs.writeFileSync(path.join(dir, 'jankfire-db.json'), JSON.stringify({ secret: crypto.randomBytes(32).toString('hex'), wingsMoved: 1, users: { cluckers: {
  name_lower: 'cluckers', name: 'Cluckers', salt, hash, created_at: new Date().toISOString(), profile: {}, inv: { gifts: [] }, crates: 0, bags: 0, boxes: 0,
  kills: 0, deaths: 0, bot_kills: 0, wins: 0, best_wave: 0, top_speed: 0, xp: 0, playtime: 0, void_kills: 0, headshots: 0, tbags: 0, chicken_kills: 24, melee_kills: 49 } } }));
const srv = spawn(process.execPath, ['--max-old-space-size=256', 'server.js'], { cwd: path.join(__dirname, '..'), env: { ...process.env, PORT: String(port), JF_DATA_DIR: dir, SUPABASE_URL: '', SUPABASE_SERVICE_KEY: '' }, stdio: ['ignore', 'pipe', 'pipe'] });
let log = ''; srv.stdout.on('data', (d) => { log += d; }); srv.stderr.on('data', (d) => { log += d; });
const api = async (url, body, token) => { const r = await fetch(`http://localhost:${port}${url}`, { method: body ? 'POST' : 'GET', headers: { 'content-type': 'application/json', ...(token ? { authorization: 'Bearer ' + token } : {}) }, body: body ? JSON.stringify(body) : undefined }); return r.json(); };

function client(name, token) {
  const ws = new WS(`ws://localhost:${port}/ws`), c = { ws, got: [], id: 0, q: 0, hp: 100, alive: true };
  ws.on('message', (d) => { const m = JSON.parse(d); if (m.t === 'welcome') { c.id = m.id; c.q = m.q; } if (m.t === 'spawn') c.q = m.q; if (m.t === 'sn') { const r = m.p.find((x) => x[0] === c.id); if (r) c.hp = r[10]; return; } c.got.push(m); });
  c.send = (m) => ws.send(JSON.stringify(m));
  c.place = (p, w = 'ar') => c.send({ t: 's', q: c.q, p, v: [0, 0, 0], y: 0, x: 0, w });
  c.take = (t, f) => { const i = c.got.findIndex((m) => m.t === t && (!f || f(m))); return i < 0 ? null : c.got.splice(i, 1)[0]; };
  return new Promise((res) => ws.on('open', () => { c.send({ t: 'join', name, mode: 'ffa', ...(token ? { token } : {}) }); setTimeout(() => res(c), 900); }));
}

(async () => {
  for (let i = 0; i < 40 && !log.includes('localhost:' + port); i++) await sleep(250);
  try {
    const login = await api('/api/login', { name: 'Cluckers', pass: 'cluck1234' });
    ok(login.token && login.me.stats.chicken_kills === 24 && login.me.stats.melee_kills === 49, 'logged in: 24 chicken kills, 49 melee kills, neither achievement yet');
    ok(!login.me.achs.includes('poultry') && !login.me.achs.includes('protector'), 'achs: ' + JSON.stringify(login.me.achs));
    const A = await client('Cluckers', login.token), B = await client('target');
    const y = 90, at = [0, y, 0], bAt = [0, y, -6];
    // kill B with weapon w: keep both in place (B's spawn number follows its respawns), act() every `every` ms
    const killWith = async (w, act, every, ms = 12000) => {
      A.got.length = 0;
      for (let t = 0; t < ms; t += 100) {
        A.place(at, w); B.place(bAt);
        if (t % every === 0) act();
        const k = A.take('kill', (m) => m.v === B.id);
        if (k) { await sleep(300); return k; }
        await sleep(100);
      }
      return null;
    };
    const aim = (p) => { const o = [at[0], at[1] + 1.6, at[2]], d = [p[0] - o[0], p[1] - o[1], p[2] - o[2]], l = Math.hypot(...d); return { o, d: d.map((v) => v / l) }; };
    // 1. a gun kill: no chicken, no melee
    const k0 = await killWith('ar', () => { const { d } = aim([bAt[0], bAt[1] + 1.2, bAt[2]]); A.send({ t: 'hit', w: 'ar', to: B.id, d, n: 1, h: 0 }); }, 100);
    ok(k0 && k0.k === A.id && k0.w === 'ar', 'a rifle kill: ' + JSON.stringify(k0 && { k: k0.k, w: k0.w }));
    ok(!A.take('ach', (m) => m.id === 'poultry' || m.id === 'protector'), 'a rifle kill unlocks neither');
    await sleep(2800); // B respawns
    // 2. a Chicken Rocket kill: Poultry in Motion (out here the blast usually knocks them into the void: that counts too)
    const k1 = await killWith('chicken', () => { const { o, d } = aim([bAt[0], bAt[1] + 0.3, bAt[2]]); A.send({ t: 'fire', w: 'chicken', o, d }); }, 1000);
    ok(k1 && k1.k === A.id && (k1.w === 'chicken' || k1.via === 'chicken'), 'a Chicken Rocket kill (blown up, or blown off the map): ' + JSON.stringify(k1 && { k: k1.k, w: k1.w, via: k1.via }));
    await sleep(300);
    ok(A.take('ach', (m) => m.id === 'poultry'), 'the 25th chicken kill pops POULTRY IN MOTION');
    ok(!A.take('ach', (m) => m.id === 'protector'), 'and not Sworn Protector');
    await sleep(2800);
    // 3. a knife kill (in reach, B a step away): Sworn Protector
    const near = [0, y, -1.4];
    A.got.length = 0;
    let k2 = null;
    for (let t = 0; t < 12000 && !k2; t += 100) {
      A.place(at, 'knife'); B.place(near);
      if (t % 800 === 0) { const d = [0, 0, -1]; A.send({ t: 'fire', w: 'knife', o: [at[0], at[1] + 1.6, at[2]], d }); A.send({ t: 'hit', w: 'knife', to: B.id, d }); }
      k2 = A.take('kill', (m) => m.v === B.id);
      await sleep(100);
    }
    ok(k2 && k2.k === A.id && k2.w === 'knife', 'a knife kill: ' + JSON.stringify(k2 && { k: k2.k, w: k2.w }));
    await sleep(300);
    ok(A.take('ach', (m) => m.id === 'protector'), 'the 50th melee kill pops SWORN PROTECTOR');
    // 4. garbage on the paths this touches never crashes or counts
    for (const bad of [{ t: 'hit', w: 'constructor', to: B.id, d: [0, 0, -1] }, { t: 'hit', w: 'parry', to: B.id, d: [0, 0, -1] }, { t: 'fire', w: '__proto__', o: [0, 0, 0], d: [0, 0, 1] }, { t: 'hit', w: 'knife', to: 'x', d: 'y' }]) { A.send(bad); await sleep(150); }
    ok(A.ws.readyState === 1, 'garbage weapon ids: still connected');
    // 5. leave: the stats are saved, and the account has both achievements
    A.ws.close(); B.ws.close(); await sleep(1800);
    const me = await api('/api/me', null, login.token);
    ok(me.me && me.me.stats.chicken_kills === 25 && me.me.stats.melee_kills === 50, `saved: chicken_kills ${me.me && me.me.stats.chicken_kills}, melee_kills ${me.me && me.me.stats.melee_kills}`);
    ok(me.me && me.me.achs.includes('poultry') && me.me.achs.includes('protector'), 'saved achs: ' + JSON.stringify(me.me && me.me.achs));
  } catch (e) { ok(false, 'threw: ' + e.message); }
  if (/TypeError|ReferenceError|crash/i.test(log)) { ok(false, 'server log has an error'); console.log(log.split('\n').filter((l) => /Error|crash/.test(l)).slice(0, 5).join('\n')); }
  srv.kill(); fs.rmSync(dir, { recursive: true, force: true });
  console.log(fails ? `${fails} FAILED` : 'all passed');
  process.exit(fails ? 1 : 0);
})();
