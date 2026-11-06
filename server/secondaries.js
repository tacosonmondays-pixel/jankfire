// New secondaries + the speed trap, server half: the Water Pistol (soaks), the Taser (stuns, chains through the soaked),
// the TV Remote (pause / rewind) and the Speed Trap item (radar readings, tickets, jail cages). Mixed into Room by
// installSec: every method runs as a Room method (this = the room). Movement is the client's, but every effect here is
// the server's: who got hit (range, aim, line of sight from server positions), how fast someone was going (from the
// positions it saw, never their claimed velocity), where they were 2 s ago, how long a stun / pause / cage lasts.
// Wraps a few Room methods (handle, onFire, useItem, applyHitscan, botThink, botFire, modeSpeed, resetLife...) so
// server.js only needs the install line.
import { WEAPONS, FLAGS, ITEMS, SPEED, BOT_DIFF } from '../shared/weapons.js';

let H; // helpers from server.js
const WP = WEAPONS.water, TZ = WEAPONS.taser, RM = WEAPONS.remote;
const SEC_BITS = FLAGS.SOAK | FLAGS.STUN | FLAGS.PAUSE | FLAGS.JAIL | FLAGS.TICKET | FLAGS.RADAR;
const STOPPED = new Set(['fire', 'hit', 'push', 'item', 'deploy', 'tbag', 'use', 'parry', 'spray', 'radar', 'slam']);
const HIST_MS = 3000, HIST_GAP = 100; // rewind history: 10 Hz, 3 s
const ri = (x) => Math.round(x);
const chestOf = (p) => [p.pos[0], p.pos[1] + 1.1, p.pos[2]];

export function installSec(Room, helpers) {
  H = helpers;
  for (const t of ['jail', 'jailx', 'ticket', 'ticketx', 'soak']) H.REC_T.add(t); // cages + tickets show up in killcams
  for (const k of ['zap', 'pause', 'rewind', 'radar', 'rmiss']) H.REC_FX.add(k);
  const P = Room.prototype, orig = {};
  for (const k of ['handle', 'onFire', 'useItem', 'applyHitscan', 'botThink', 'botFire', 'modeSpeed', 'resetLife', 'resetWorld', 'gearJoin', 'tickGear', 'gearSnap', 'kill']) orig[k] = P[k];
  Object.assign(P, sec, {
    handle(p, m) {
      if (m && STOPPED.has(m.t) && this.secStopped(p)) return; // stunned, paused or caged: hands off everything
      if (m && m.t === 'radar') { this.onRadar(p, m); return; }
      return orig.handle.call(this, p, m);
    },
    onFire(p, m) {
      const w = m && typeof m.w === 'string' && Object.hasOwn(WEAPONS, m.w) ? WEAPONS[m.w] : null;
      if (w && (w.kind === 'zap' || w.kind === 'remote')) { this.secFire(p, m); return; }
      return orig.onFire.call(this, p, m);
    },
    // the speed trap's G press is free (holding it just raises the radar gun): only a ticket spends a charge
    useItem(p, m) {
      if (m && m.i === 'radar') { this.sendIc(p); return; }
      return orig.useItem.call(this, p, m);
    },
    // water pistol: every squirt that really lands soaks them (players' hit reports and bots' shots both come here)
    applyHitscan(p, t, wid, n, h, d, mul) {
      const wet = WEAPONS[wid] && WEAPONS[wid].water && this.soakable(p, t);
      orig.applyHitscan.call(this, p, t, wid, n, h, d, mul);
      if (wet) this.soak(t, p);
    },
    botThink(b, dt) {
      if (this.secStopped(b)) return { wx: 0, wz: 0, jump: false };
      const o = orig.botThink.call(this, b, dt);
      if (b.ticket && o) { o.wx *= 0.25; o.wz *= 0.25; o.jump = false; } // SLOW DOWN: it pulls over
      return o;
    },
    botFire(b, t, D) {
      if (this.secStopped(b)) return;
      if (this.secBotFire(b, t, D)) return;
      return orig.botFire.call(this, b, t, D);
    },
    modeSpeed(b) { return orig.modeSpeed.call(this, b) * (H.now() < (b.soakUntil || 0) ? WP.soak.slow : 1); },
    resetLife(p) { orig.resetLife.call(this, p); this.secReset(p); },
    resetWorld() { for (const p of this.players.values()) if (p.jail) this.unjail(p, 'gone'); orig.resetWorld.call(this); },
    gearJoin(p) { orig.gearJoin.call(this, p); this.secJoin(p); },
    tickGear(n) { orig.tickGear.call(this, n); this.tickSec(n); },
    gearSnap(p) { orig.gearSnap.call(this, p); this.secSnap(p); },
    kill(t, a, w) { if (t.alive) this.secDeath(t); return orig.kill.call(this, t, a, w); },
  });
}

const sec = {
  // ---------------------------------------------------------------- shared
  secStopped(p, n = H.now()) { return n < (p.stunUntil || 0) - 80 || !!(p.pause && n < p.pause.until) || !!(p.jail && n < p.jail.until); },
  // can p's thing land on t at all (the rules every hit follows, plus: not through a soap bubble, not your teammates)
  secOk(p, t) { return !!t && t !== p && t.alive && !t.trap && !this.hitBlocked(t, p, 'taser'); },
  soakable(p, t) { return this.secOk(p, t) && !(t.reverseUntil > H.now()); },
  // who p is pointing at: the one the client named if the server agrees (range, aim slack + their body, line of sight from
  // server positions), else the best one the server can find itself (bots, or a client that missed by a hair of lag)
  secTarget(p, d, to, range, cone, skip) {
    const e = H.eyeOf(p);
    let best = null, bs = 1e9;
    for (const t of this.players.values()) {
      if (t === p || !t.alive || (skip && skip(t)) || this.friendly(p, t)) continue;
      if (t.isBot && t.ai && t.ai.dummy && this.mode !== 'training') continue;
      const c = chestOf(t), v = [c[0] - e[0], c[1] - e[1], c[2] - e[2]], dist = Math.hypot(...v);
      const slack = 1.2 + Math.hypot(...t.vel) * 0.12 + Math.hypot(...p.vel) * 0.06;
      if (dist > range + slack || dist < 0.05) continue;
      const ang = Math.acos(Math.max(-1, Math.min(1, (v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / dist)));
      const allow = cone + Math.atan2(1.0 + slack * 0.25, dist) + 0.04;
      if (ang > allow) continue;
      if (H.raycast(e, v.map((x) => x / dist), Math.max(0, dist - 0.4), this.boxes) || this.smokeBlocks(e, c)) continue;
      const score = ang / allow + (t.id === to ? -10 : 0) + dist * 0.002;
      if (score < bs) { bs = score; best = t; }
    }
    return best;
  },
  // the aim the client sent, if it's close to where the server last saw them look (else the server's)
  secAim(p, m) {
    const L = H.lookOf(p), d = H.norm(H.vec3(m.d));
    return d && d[0] * L[0] + d[1] * L[1] + d[2] * L[2] > 0.55 ? d : L;
  },
  // how fast t really goes, km/h: the path through the positions the server saw over the last SPEED.window s (10 Hz steps,
  // so snapshot jitter doesn't add up; a jump of 8 m+ in one step is a teleport, not speed)
  speedKmh(t, n = H.now()) {
    const tr = t.trail;
    if (!t.alive || !tr || tr.length < 2) return 0;
    let d = 0, t0 = 0, t1 = 0, last = null;
    for (const s of tr) {
      if (s[0] < n - SPEED.window * 1000 - 60) continue;
      if (!last) { last = s; t0 = s[0]; continue; }
      if (s[0] - last[0] < 95 && s !== tr[tr.length - 1]) continue;
      const step = Math.hypot(s[1] - last[1], s[2] - last[2], s[3] - last[3]);
      if (step < 8) d += step;
      last = s; t1 = s[0];
    }
    const dt = (t1 - t0) / 1000;
    return dt < 0.2 ? 0 : (d / dt) * 3.6;
  },

  // ---------------------------------------------------------------- water pistol
  soak(t, by) {
    const n = H.now(), was = n < (t.soakUntil || 0), fire = t.burnUntil > n || t.lavaBurn > n;
    t.soakUntil = n + WP.soak.dur * 1000;
    t.burnUntil = 0; t.lavaBurn = 0; // the fire goes out
    if (by && by !== t) this.tag(t, by, 'water');
    if (was && !fire && n - (t.soakMsgT || 0) < 450) return; // (a stream of squirts refreshes it quietly)
    t.soakMsgT = n;
    this.broadcast({ t: 'soak', id: t.id, by: by ? by.id : 0, dur: WP.soak.dur, x: fire ? 1 : undefined });
  },

  // ---------------------------------------------------------------- taser + tv remote ('fire')
  secFire(p, m) {
    const n = H.now(), w = WEAPONS[m.w];
    if (!p.alive || this.rigOn(p) || this.isBall(p) || this.secStopped(p, n) || n < (p.staggerUntil || 0)) return;
    if (p.trap || p.quiz) return;
    const d = this.secAim(p, m);
    if (m.w === 'taser') {
      if (n - (p.lastFire.taser || 0) < w.cd * 900) return;
      p.lastFire.taser = n;
      this.zap(p, d, m.to);
    } else {
      const mode = m.m === 1 ? 'rewind' : 'pause', cd = (p.rmCd ||= {});
      if (n < (cd[mode] || 0) - 120 || n - (p.lastFire.remote || 0) < 250) return;
      cd[mode] = n + w[mode].cd * 1000;
      p.lastFire.remote = n;
      this.remoteUse(p, mode, d, m.to);
    }
  },
  // darts fly where you point; the first one they reach is stunned. then the current jumps soaked person to soaked person
  zap(p, d, to) {
    const n = H.now(), e = H.eyeOf(p);
    let t = this.secTarget(p, d, to, TZ.range, TZ.cone, (x) => x.trap);
    const links = [];
    const end = (x) => [...chestOf(x)].map(H.r2);
    if (!t) { // a miss: the darts land on whatever's there
      const wall = H.raycast(e, d, TZ.range, this.boxes), k = wall ? wall.t : TZ.range;
      this.broadcast({ t: 'fx', k: 'zap', id: p.id, o: e.map(H.r2), e: [e[0] + d[0] * k, e[1] + d[1] * k, e[2] + d[2] * k].map(H.r2), l: [] });
      if (n < (p.soakUntil || 0)) this.stunSelf(p);
      return;
    }
    let src = p;
    if (t.reverseUntil > n && this.secOk(p, t)) { this.broadcast({ t: 'fx', k: 'reflect', id: t.id, by: p.id }); src = t; t = p; } // reverse card: back down the wire
    const hit = new Set([t.id, src.id]);
    links.push([src.id, t.id, ...(src === p ? e.map(H.r2) : end(src)), ...end(t)]);
    const wet = (x) => n < (x.soakUntil || 0);
    this.zapOne(t, src, wet(t) ? TZ.stun * TZ.wet : TZ.stun, TZ.dmg);
    // the chain: breadth first from everyone zapped, only into the soaked, never your own side, line of sight, chainMax total
    const q = [t];
    while (q.length && hit.size - 1 < TZ.chainMax) {
      const a = q.shift(), ac = chestOf(a);
      for (const u of this.players.values()) {
        if (hit.has(u.id) || !u.alive || !wet(u) || u.trap || this.friendly(src, u)) continue;
        const uc = chestOf(u), v = [uc[0] - ac[0], uc[1] - ac[1], uc[2] - ac[2]], dist = Math.hypot(...v);
        if (dist > TZ.chainR || (dist > 0.3 && H.raycast(ac, v.map((x) => x / dist), dist - 0.3, this.boxes))) continue;
        hit.add(u.id);
        links.push([a.id, u.id, ...ac.map(H.r2), ...uc.map(H.r2)]);
        this.zapOne(u, src, TZ.chainStun, TZ.chainDmg);
        q.push(u);
        if (hit.size - 1 >= TZ.chainMax) break;
      }
    }
    this.broadcast({ t: 'fx', k: 'zap', id: p.id, o: e.map(H.r2), l: links });
    if (src === p && wet(p)) this.stunSelf(p); // fired it wet
  },
  stunSelf(p) {
    this.stun(p, null, TZ.self);
    this.broadcast({ t: 'fx', k: 'zap', id: p.id, o: H.eyeOf(p).map(H.r2), l: [[p.id, p.id, ...chestOf(p).map(H.r2), ...chestOf(p).map(H.r2)]], self: 1 });
  },
  zapOne(t, by, dur, dmg) {
    if (!this.secOk(by, t)) return false;
    const n = H.now();
    // the overdrive rig is insulated: dry, the darts just sting. soaked, it shorts out: a short stun and fried thrusters
    if (this.rigOn(t)) {
      this.hurt(t, by, 'taser', dmg, null);
      if (n < (t.soakUntil || 0)) { this.stun(t, by, 0.6); t.hackedUntil = Math.max(t.hackedUntil || 0, n + 2000); t.g = null; }
      else this.broadcast({ t: 'fx', k: 'grounded', id: t.id });
      return true;
    }
    if (!this.hurt(t, by, 'taser', dmg, [0, 2.5, 0])) { if (!t.alive) return true; }
    if (t.alive) this.stun(t, by, dur);
    return true;
  },
  stun(t, by, dur) {
    const n = H.now();
    t.stunUntil = Math.max(t.stunUntil || 0, n + dur * 1000);
    t.g = null; t.beam = null; t.laserT = 0;
    if (by && by !== t) this.tag(t, by, 'taser');
    if (t.isBot) { if (t.ai) { t.ai.hook = null; t.ai.nextShot = Math.max(t.ai.nextShot || 0, t.stunUntil + 200); } }
    else H.send(t, { t: 'stun', dur: H.r2(dur), by: by ? by.id : 0 });
  },
  // tv remote. pause: frozen in place (momentum saved and handed back when it ends). rewind: back where the server saw them
  remoteUse(p, mode, d, to) {
    const n = H.now(), e = H.eyeOf(p);
    let t = this.secTarget(p, d, to, RM.range, RM.cone, (x) => x.trap);
    if (!t) {
      const wall = H.raycast(e, d, RM.range, this.boxes), k = wall ? wall.t : RM.range;
      this.broadcast({ t: 'fx', k: 'rmiss', id: p.id, m: mode === 'rewind' ? 1 : 0, o: e.map(H.r2), e: [e[0] + d[0] * k, e[1] + d[1] * k, e[2] + d[2] * k].map(H.r2) });
      return;
    }
    let by = p;
    if (t.reverseUntil > n && this.secOk(p, t)) { this.broadcast({ t: 'fx', k: 'reflect', id: t.id, by: p.id }); by = t; t = p; }
    if (!this.secOk(by, t)) { this.broadcast({ t: 'fx', k: 'rmiss', id: p.id, m: mode === 'rewind' ? 1 : 0, o: e.map(H.r2), e: chestOf(t).map(H.r2) }); return; }
    if (mode === 'pause') this.pauseP(t, by);
    else this.rewindP(t, by);
  },
  pauseP(t, by) {
    const n = H.now(), dur = this.rigOn(t) ? RM.pause.rig : RM.pause.dur;
    t.pause = { until: n + dur * 1000, at: t.pos.slice(), vel: t.vel.slice(), by: by.id };
    t.g = null; t.beam = null; t.laserT = 0;
    this.tag(t, by, 'remote');
    if (t.isBot && t.ai) { t.ai.hook = null; t.ai.nextShot = Math.max(t.ai.nextShot || 0, t.pause.until + 150); }
    this.broadcast({ t: 'fx', k: 'pause', id: t.id, by: by.id, dur, p: t.pos.map(H.r2) });
  },
  rewindP(t, by) {
    const n = H.now(), h = t.hist || [], want = n - RM.rewind.back * 1000;
    let to = null;
    const path = [];
    for (const s of h) { if (s[0] <= want) to = s; else { if (!to) to = s; path.push([s[1], s[2], s[3]].map(H.r2)); } }
    if (!to) to = [n, ...t.pos];
    const a = t.pos.map(H.r2), b = [to[1], to[2], to[3]].map(H.r2);
    t.pos = b.slice(); t.vel = [0, 0, 0]; t.g = null; t.pause = null;
    if (t.jail) t.jail.at = b.slice(); // rewound out of a cage? no: the cage comes along
    this.tag(t, by, 'remote');
    t.knockT = n;
    t.rwd = { to: b.slice(), t: n, n: 0 };
    if (t.isBot && t.ai) { t.ai.hook = null; t.ai.route = null; t.ai.nav = null; t.onGround = false; }
    // the path back, newest first, a few points (the VHS trail everyone sees)
    const step = Math.max(1, Math.floor(path.length / 8));
    const tr = path.reverse().filter((_, i) => i % step === 0).slice(0, 10);
    this.broadcast({ t: 'fx', k: 'rewind', id: t.id, by: by.id, a, b, tr });
  },

  // ---------------------------------------------------------------- speed trap
  // {t:'radar', to, d}: G held, the client's crosshair is on `to` (0 = nobody). {t:'radar', off: 1}: let go
  onRadar(p, m) {
    const n = H.now();
    if (m.off === 1) { p.radarOn = 0; return; }
    if (!p.alive || !this.radarHeld(p) || this.rigOn(p) || this.isBall(p) || p.trap || p.quiz) return;
    if (this.modeWeapon(p) || (this.chaosKit && this.chaosKit.noItem)) return;
    p.radarOn = n + 600;
    if (n - (p.radarT || 0) < SPEED.scan * 800) return;
    p.radarT = n;
    const to = Number.isInteger(m.to) ? m.to : 0;
    const t = this.secTarget(p, this.secAim(p, m), to, SPEED.range, SPEED.cone, (x) => x.trap);
    if (!t) return;
    this.radarRead(p, t);
  },
  radarHeld(p) { return p.item === 'radar' || (p.isBot && !!p.ai && p.ai.gear === 'radar') || !!(p.ec && p.ec.it && p.ec.it.id === 'radar'); },
  // one reading: everyone sees the number over their head. over the limit = a ticket, way over = the cage
  radarRead(p, t) {
    const n = H.now(), v = this.speedKmh(t, n);
    this.broadcast({ t: 'fx', k: 'radar', id: p.id, to: t.id, v: ri(v) });
    if (v <= SPEED.limit || t.ticket || t.jail || n < (t.radarSafe || 0) || !this.secOk(p, t) || n < (p.ticketT || 0)) return;
    if (!this.radarSpend(p)) return;
    p.ticketT = n + 900;
    if (t.reverseUntil > n) { this.broadcast({ t: 'fx', k: 'reflect', id: t.id, by: p.id }); const s = p; p = t; t = s; } // you get the ticket
    if (v >= SPEED.jail) { this.jailP(t, p, v); return; }
    t.ticket = { by: p.id, until: n + SPEED.warn * 1000, v: ri(v), at: n };
    this.tag(t, p, 'radar');
    this.broadcast({ t: 'ticket', id: t.id, by: p.id, v: ri(v), s: SPEED.warn, lim: SPEED.limit });
  },
  // a ticket costs a charge (bots have their own cooldown). Plant & Defuse: the ones you bought
  radarSpend(p) {
    const n = H.now();
    if (p.isBot) { if (n < (p.ai.radarCd || 0)) return false; p.ai.radarCd = n + ITEMS.radar.recharge * 1000 * 0.6; return true; }
    const e = p.ec;
    if (e && this.isEcon && this.isEcon()) {
      if (!e.it || e.it.id !== 'radar' || e.it.n <= 0) return false;
      e.it.n--; if (e.it.n <= 0) e.it = null;
      this.econSync(p); this.econSend(p);
      return true;
    }
    if (p.item !== 'radar') return false;
    const c = this.itemCharges(p);
    if (c.n <= 0) { this.sendIc(p); return false; }
    c.n--;
    if (!c.next) c.next = n + ITEMS.radar.recharge * 1000;
    this.sendIc(p);
    return true;
  },
  jailP(t, by, v) {
    const n = H.now(), dur = this.rigOn(t) ? SPEED.rigJail : SPEED.jailT;
    t.ticket = null;
    t.jail = { until: n + dur * 1000, at: t.pos.slice(), by: by ? by.id : 0 };
    t.radarSafe = n + SPEED.safe * 1000;
    t.vel = [0, 0, 0]; t.g = null; t.beam = null; t.laserT = 0; t.pause = null;
    if (by) this.tag(t, by, 'radar');
    if (t.isBot && t.ai) { t.ai.hook = null; t.ai.route = null; t.ai.nextShot = Math.max(t.ai.nextShot || 0, t.jail.until + 200); }
    this.broadcast({ t: 'jail', id: t.id, by: by ? by.id : 0, p: t.pos.map(H.r2), dur, v: v != null ? ri(v) : undefined, rig: this.rigOn(t) ? 1 : undefined });
  },
  unjail(t, why) { if (!t.jail) return; t.jail = null; this.broadcast({ t: 'jailx', id: t.id, why }); },

  // ---------------------------------------------------------------- every tick
  tickSec(n) {
    for (const p of this.players.values()) {
      if (!p.alive) { p.hist = null; continue; }
      // rewind history (10 Hz, 3 s; a new life or a reset starts a new one)
      if (p.histSeq !== p.seq) { p.histSeq = p.seq; p.hist = []; }
      const h = (p.hist ||= []);
      if (!h.length || n - h[h.length - 1][0] >= HIST_GAP) { h.push([n, p.pos[0], p.pos[1], p.pos[2]]); while (h.length && h[0][0] < n - HIST_MS) h.shift(); }
      // statuses running out
      if (p.pause && n >= p.pause.until) { const v = p.pause.vel; p.pause = null; if (p.isBot) p.vel = v.slice(); }
      if (p.jail && n >= p.jail.until) this.unjail(p, 'time');
      if (p.ticket) this.tickTicket(p, n);
      // held in place (bots: here; players: in secSnap and by their own client)
      const at = p.jail ? p.jail.at : p.pause ? p.pause.at : null;
      if (at && p.isBot) { p.pos = at.slice(); p.vel = [0, 0, 0]; p.g = null; }
      p.f = (p.f & ~SEC_BITS) | this.secBits(p, n);
      if (p.isBot && p.ai && !p.ai.dummy) this.botRadar(p, n);
    }
  },
  secBits(p, n) {
    return (n < (p.soakUntil || 0) ? FLAGS.SOAK : 0) | (n < (p.stunUntil || 0) ? FLAGS.STUN : 0) | (p.pause ? FLAGS.PAUSE : 0) |
      (p.jail ? FLAGS.JAIL : 0) | (p.ticket ? FLAGS.TICKET : 0) | (n < (p.radarOn || 0) && this.radarHeld(p) ? FLAGS.RADAR : 0);
  },
  // SLOW DOWN: back under the limit (measured over the last half second) = a warning. out of time = jailed
  tickTicket(p, n) {
    const tk = p.ticket;
    if (n - tk.at < 300) return; // give the reading a moment to catch up with them braking
    if (this.speedKmh(p, n) <= SPEED.limit) {
      p.ticket = null; p.radarSafe = n + SPEED.warnSafe * 1000;
      this.broadcast({ t: 'ticketx', id: p.id, ok: 1 });
      return;
    }
    if (n >= tk.until) { this.broadcast({ t: 'ticketx', id: p.id, ok: 0 }); this.jailP(p, this.players.get(tk.by) || null, this.speedKmh(p, n)); }
  },
  // a player's snapshot: no claiming the server's flags, and no walking out of a cage or a pause
  secSnap(p) {
    const n = H.now();
    p.f = (p.f & ~SEC_BITS) | this.secBits(p, n);
    const at = p.jail ? p.jail.at : p.pause && n < p.pause.until ? p.pause.at : null;
    if (at) {
      const d = H.dist3(p.pos, at);
      if (d > 0.4) for (let k = 0; k < 3; k++) p.pos[k] = at[k] + (p.pos[k] - at[k]) * (0.4 / d);
      p.vel = [0, 0, 0]; p.g = null;
    }
    // rewound: snapshots still in flight from before are fine for a moment; after that you're where the remote put you
    const r = p.rwd;
    if (r) {
      const age = n - r.t;
      if (age > 2500) p.rwd = null;
      else if (age > 350 && H.dist3(p.pos, r.to) > 4 + age * 0.03 && r.n < 3) { r.n++; r.t = n; p.pos = r.to.slice(); H.send(p, { t: 'rwdfix', p: r.to }); }
    }
    if (n < (p.stunUntil || 0)) p.g = null;
  },
  secReset(p) {
    p.soakUntil = 0; p.stunUntil = 0; p.pause = null; p.ticket = null; p.radarOn = 0; p.rwd = null; p.hist = null; p.rmCd = null;
    if (p.jail) this.unjail(p, 'life');
  },
  secDeath(t) { t.pause = null; t.ticket = null; t.stunUntil = 0; t.soakUntil = 0; t.radarOn = 0; if (t.jail) this.unjail(t, 'dead'); },
  secJoin(p) { // a late joiner sees the cages and tickets (flags do the rest)
    const n = H.now();
    for (const t of this.players.values()) {
      if (t.jail) H.send(p, { t: 'jail', id: t.id, by: t.jail.by, p: t.jail.at.map(H.r2), dur: H.r2((t.jail.until - n) / 1000), late: 1 });
      if (t.ticket) H.send(p, { t: 'ticket', id: t.id, by: t.ticket.by, v: t.ticket.v, s: H.r2((t.ticket.until - n) / 1000), lim: SPEED.limit });
    }
  },

  // ---------------------------------------------------------------- bots
  // taser: only up close (botThink's own pref keeps it near). remote: pause whoever it fights, rewind anyone running off
  // with momentum (grapplers, rocket jumpers) or about to reach an objective
  secBotFire(b, t, D) {
    const w = WEAPONS[b.w], n = H.now();
    if (!w || (w.kind !== 'zap' && w.kind !== 'remote') || !t || !t.alive) return false;
    const aim = H.lookOf(b), dist = H.dist3(t.pos, b.pos);
    const miss = Math.random() < (D.err || 0.04) * 3; // easy bots fumble a few
    const d = miss ? H.norm([aim[0] + (Math.random() - 0.5) * 0.4, aim[1] + (Math.random() - 0.5) * 0.3, aim[2] + (Math.random() - 0.5) * 0.4]) : aim;
    if (w.kind === 'zap') {
      if (dist > w.range + 0.5) { b.ai.nextShot = n + 200; return true; }
      this.secFire(b, { w: 'taser', d, to: miss ? 0 : t.id });
      b.ai.nextShot = n + w.cd * 1000 / D.rate + Math.random() * 250;
      return true;
    }
    const cd = (b.rmCd ||= {}), fast = Math.hypot(t.vel[0], t.vel[2]) > 14 || Math.abs(t.vel[1]) > 12;
    const mode = n >= (cd.rewind || 0) && (fast || Math.random() < 0.35) ? 1 : n >= (cd.pause || 0) ? 0 : -1;
    if (mode < 0 || dist > w.range) { b.ai.nextShot = n + 300; return true; }
    this.secFire(b, { w: 'remote', m: mode, d, to: miss ? 0 : t.id });
    b.ai.nextShot = n + 600 / D.rate + Math.random() * 400;
    return true;
  },
  // bots with the speed trap watch whoever they're fighting, and anyone zooming past within range
  botRadar(b, n) {
    if (b.ai.gear !== 'radar' || this.mode === 'training' || this.modeWeapon(b) || (this.chaosKit && this.chaosKit.noItem)) return;
    if (this.secStopped(b, n) || b.trap || b.quiz || n < (b.blindUntil || 0) || this.rigOn(b)) return;
    if (n < (b.ai.radarNext || 0)) return;
    b.ai.radarNext = n + 250 + Math.random() * 200;
    const e = H.eyeOf(b);
    let best = null, bv = 0;
    for (const t of this.players.values()) {
      if (t === b || !t.alive || this.friendly(b, t) || (t.ai && t.ai.dummy) || t.ticket || t.jail || n < (t.radarSafe || 0)) continue;
      const c = chestOf(t), dist = H.dist3(c, e);
      if (dist > SPEED.range * 0.8 || !this.canSee(H.eyeOf(b), chestOf(t))) continue;
      const v = this.speedKmh(t, n);
      if (v > bv) { bv = v; best = t; }
    }
    if (!best || bv < SPEED.limit * 0.8) return;
    b.radarOn = n + 600; // everyone sees it raise the radar gun
    if (Math.random() < 0.5) this.radarRead(b, best);
  },
};
