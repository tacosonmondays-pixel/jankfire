// Lasso (secondary weapon), the server side. installLasso() puts these on Room, so server.js only carries a few hooks.
// The loop is a server projectile: this decides who it catches (never through walls; a katana parry cuts it, a reverse
// card flips the catch, a wrecking ball is too heavy, a shield bubble keeps it out). Once someone is caught, whoever
// holds them runs the body with the shared step (shared/lasso.js): a human holder's client streams it ('lh', ~30 Hz)
// and every sample is checked here (still holding, both alive, within the rope, sane speed, no jumps, never through
// the map) before it goes to the victim's client; a bot holder is simulated right here. Splats, credit and the
// distance flown are decided here too. Bots get held (they follow the stream) and use it in bot rooms.
import { LASSO, holdStep, flingVel, splatDmg, aimDir, throwRange, throwSpeed, ropeMax, clampLen } from '../shared/lasso.js';
import { FLAGS, BOT_DIFF } from '../shared/weapons.js';
import { stepProjectile, raycast, rayBox, movePlayer, PH, query } from '../shared/physics.js';

const now = () => Date.now();
const BOT_SHARE = process.env.JF_LASSO_BOTS != null ? Number(process.env.JF_LASSO_BOTS) || 0 : 0.2; // test knob: share of bot-room bots with the lasso
const r2 = (x) => Math.round(x * 100) / 100;
const dist3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const W = LASSO.waist;
const LOCK = 0.35; // s after a fling with no control (the client's tumble): the server holds them to the flight
// ms a holder's stream may go quiet before the rope drops (a hitch on the catch, a lag spike). test knob for slow
// headless browsers
const QUIET = Number(process.env.JF_LASSO_QUIET) || 1500;
// [x, y, z] of finite numbers off the network, or null
function vec3(a) {
  if (!Array.isArray(a) || a.length !== 3) return null;
  for (const x of a) if (typeof x !== 'number' || !Number.isFinite(x) || Math.abs(x) > 1e6) return null;
  return a.slice();
}
function norm(a) { if (!a) return null; const l = Math.hypot(a[0], a[1], a[2]); return l > 1e-6 ? [a[0] / l, a[1] / l, a[2] / l] : null; }
function send(p, obj) { if (p.ws && p.ws.readyState === 1) p.ws.send(JSON.stringify(obj)); }
const eyeOf = (p) => [p.pos[0], p.pos[1] + ((p.f & FLAGS.CROUCH) ? 1.05 : PH.eye), p.pos[2]];
const waistOf = (p) => [p.pos[0], p.pos[1] + W, p.pos[2]];
const capLen = (v, max) => { const l = Math.hypot(v[0], v[1], v[2]); return l > max ? v.map((x) => (x * max) / l) : v; };
// the player's box at pos, pushed m metres along axis ax (dir +-1), overlaps the map: they're right up against it
const qT = [];
function touching(boxes, pos, ax, dir, m = 0.14) {
  const hw = PH.halfW - 0.03, lo = [pos[0] - hw, pos[1] + 0.03, pos[2] - hw], hi = [pos[0] + hw, pos[1] + PH.height - 0.03, pos[2] + hw];
  if (dir > 0) { lo[ax] = hi[ax]; hi[ax] += m; } else { hi[ax] = lo[ax]; lo[ax] -= m; }
  for (const b of query(boxes, lo[0] - 0.05, lo[2] - 0.05, hi[0] + 0.05, hi[2] + 0.05, qT)) {
    if (lo[0] < b.max[0] && hi[0] > b.min[0] && lo[1] < b.max[1] && hi[1] > b.min[1] && lo[2] < b.max[2] && hi[2] > b.min[2]) return true;
  }
  return false;
}
// the straight path a -> b goes through the map, deeper than a swing clipping a corner (more than `deep` m of it is
// inside one box): a body that went through a wall between two samples
function throughWall(boxes, a, b, deep = 0.5) {
  const s = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], l = Math.hypot(s[0], s[1], s[2]);
  if (l < 0.05) return false;
  const d = [s[0] / l, s[1] / l, s[2] / l], h = raycast(a, d, l, boxes);
  if (!h) return false;
  const back = rayBox(b, [-d[0], -d[1], -d[2]], h.box, l); // from the far end back: where the path leaves that box
  return (back ? l - h.t - back.t : l - h.t) > deep;
}
// inside the map (a body the stream put in a wall). a hair of give for positions rounded to 1 cm
function inside(boxes, pos) {
  const hw = PH.halfW - 0.03, x0 = pos[0] - hw, x1 = pos[0] + hw, y0 = pos[1] + 0.03, y1 = pos[1] + PH.height - 0.03, z0 = pos[2] - hw, z1 = pos[2] + hw;
  for (const b of query(boxes, x0, z0, x1, z1, qT)) if (x0 < b.max[0] && x1 > b.min[0] && y0 < b.max[1] && y1 > b.min[1] && z0 < b.max[2] && z1 > b.min[2]) return true;
  return false;
}

// the rig (overdrive rig killstreak) is a heavy exo-frame: it can't throw a lasso and a loop slides off it
const rigged = (room, p, n) => !!(room.rigOn && room.rigOn(p, n));
// out of action: can't hold a rope like this (asleep on the floor, frozen solid, sitting a pop quiz)
const busy = (p, n) => n < (p.sleepUntil || 0) || n < (p.frozenUntil || 0) || !!p.quiz;
// the most the held body's speed can grow per second: the spring's force cap + gravity + the rope swinging them round
// you, with room for rounding and jitter. a client claiming more than this gets it clamped (no instant 120 m/s flings)
const GROW = (LASSO.aMax + 26) * 1.35 + 30;
// a teammate on your rope: a ride, not a weapon. they fly no faster than this and one wriggle press frees them
const TEAM_CAP = 45;

const M = {
  lz(p) { return p.lz || (p.lz = { hold: null, by: 0, loop: 0, next: 0, spin0: 0, wr: 0, wrT: 0, fl: null }); },
  lassoHeld(p) { return !!(p.lz && p.lz.by); },
  lassoHolding(p) { return !!(p.lz && p.lz.hold); },

  // ---------------------------------------------------------- messages
  // { t: 'lasso', k: 'throw', o, d, s } throw the loop (s = how much it spun, 0..1) · k: 'rel' let go (p, v = the body
  // as your client has it right now) · k: 'wr' a wriggle press (you're the one held)
  onLasso(p, m) {
    if (!p.alive || typeof m.k !== 'string') return;
    if (m.k === 'throw') this.lassoThrow(p, m);
    else if (m.k === 'rel') this.lassoRelease(p, m);
    else if (m.k === 'wr') this.lassoWriggle(p);
  },
  // { t: 'lh', p, v, L } the held body from the holder's client, ~30 times a second
  onLassoHold(p, m) {
    const H = p.lz && p.lz.hold;
    if (!H || H.sim || !p.alive) return;
    const n = now();
    // a token bucket: an honest 30 Hz stream (even bunched up by the network) always gets through, a flood doesn't
    H.tok = Math.min(8, (H.tok ?? 8) + ((n - (H.tokT || n)) / 1000) * LASSO.stream * 1.6); H.tokT = n;
    if (H.tok < 1) return;
    H.tok--;
    const V = this.players.get(H.v);
    if (!V || !V.alive || V.seq !== H.seq) { this.lassoEnd(p, 'gone'); return; }
    const pos = vec3(m.p), vel = vec3(m.v);
    if (!pos || !vel) return;
    if (typeof m.L === 'number' && Number.isFinite(m.L)) H.L = clampLen(m.L); // reeled in or out
    this.lassoAccept(p, H, V, pos, vel, n);
  },
  // one sample of the held body: it has to make sense before it counts. a run of bad ones ends the hold
  lassoAccept(h, H, V, pos, vel, n) {
    const dt = Math.max(0.016, Math.min(0.25, (n - H.lastT) / 1000));
    // speed can only grow as fast as the spring can pull (per real second here, so a flood of samples buys nothing)
    const sp0 = Math.hypot(H.vel[0], H.vel[1], H.vel[2]);
    vel = capLen(vel, Math.min(LASSO.cap * 1.25, sp0 + GROW * Math.max(0.004, Math.min(0.15, (n - H.lastT) / 1000)) + 1)); // (a long gap buys no more than 0.15 s)
    const e = eyeOf(h), w = [pos[0], pos[1] + W, pos[2]];
    // within the rope of where we have the holder (their position here is up to a snapshot old: slack for that)
    const slack = 2.5 + Math.min(40, Math.hypot(h.vel[0], h.vel[1], h.vel[2])) * 0.1;
    H.Lok = Math.max(H.L, (H.Lok || H.L) - LASSO.reel * 1.5 * dt); // reeling in: the body gets a moment to come in with it
    let bad = dist3(e, w) > ropeMax(H.Lok) + slack;
    // no teleports: no further than the fastest a body can go since the last good sample (at least one stream tick:
    // the network bunches samples up)
    if (!bad) bad = dist3(pos, H.pos) > (LASSO.cap * 1.25 + 10) * Math.max(dt, 1 / LASSO.stream) + 1.5;
    // never through the map: not through a wall since the last good sample, and not inside one
    if (!bad) bad = throughWall(this.boxes, [H.pos[0], H.pos[1] + W, H.pos[2]], w) || inside(this.boxes, pos);
    if (bad) {
      if (++H.bad > 15) this.lassoEnd(h, 'lag'); // half a second of nonsense
      return false;
    }
    const v0 = H.vel;
    H.bad = 0; H.lastT = n; H.pos = pos; H.vel = vel;
    V.pos = pos.slice(); V.vel = vel.slice();
    if (V.isBot) V.onGround = false;
    this.lassoImpact(h, V, v0, vel, pos);
    if (!V.isBot) send(V, { t: 'lh', p: pos.map(r2), v: vel.map(r2) });
    return true;
  },

  // ---------------------------------------------------------- the throw
  lassoThrow(p, m) {
    const n = now(), z = this.lz(p);
    if (p.w !== 'lasso' || z.hold || z.by || p.trap || this.isBall(p, n) || rigged(this, p, n) || busy(p, n) || n < (p.staggerUntil || 0)) return;
    if (this.round && this.round.over) return;
    if (n < z.next) return; // the last one has to come back first
    const d = norm(vec3(m.d));
    if (!d) return;
    let o = vec3(m.o);
    const ey = eyeOf(p);
    if (!o || dist3(o, ey) > 3) o = ey;
    // it can't claim more spin than its snapshots showed (a quick tap still throws a short one)
    const spun = z.spin0 ? (n - z.spin0) / 1000 / LASSO.spinT + 0.25 : 0.25;
    const s = Math.max(0, Math.min(1, typeof m.s === 'number' && Number.isFinite(m.s) ? m.s : 0, spun));
    if (z.loop && this.projectiles.has(z.loop)) this.removeProj(this.projectiles.get(z.loop));
    if (!this.lassoPay(p)) return;
    const wall = raycast(ey, d, 0.9, this.boxes), off = wall ? Math.max(0, wall.t - LASSO.r - 0.05) : 0.9;
    const sp = throwSpeed(s), pv = capLen(p.vel, 25); // your momentum carries it, within reason
    const pr = {
      id: this.nextProj++, k: 'loop', o: p.id, r: LASSO.r, bounce: 0, born: n, phase: 0, hit: new Map(), sync: 0, s, R: throwRange(s),
      p: [ey[0] + d[0] * off, ey[1] + d[1] * off, ey[2] + d[2] * off],
      v: [d[0] * sp + pv[0] * 0.3, d[1] * sp + 1.2 + pv[1] * 0.3, d[2] * sp + pv[2] * 0.3],
    };
    this.projectiles.set(pr.id, pr);
    z.loop = pr.id; z.spin0 = 0; z.next = n + 350;
    this.broadcast({ t: 'lasso', k: 'loop', id: pr.id, o: p.id, p: pr.p.map(r2), v: pr.v.map(r2), s: r2(s), R: r2(pr.R) });
  },
  // Plant & Defuse: only if you bought one, never in the buy phase, and each throw spends one of its throws
  lassoPay(p) {
    if (!this.isEcon || !this.isEcon()) return true;
    if (this.econBuying()) return false;
    const x = this.econInst(p, 'lasso');
    if (!x) return false;
    if (!x.lim) return true;
    if (x.m <= 0) { this.econAm(p, x); return false; }
    x.m--; x.fresh = false; // (the thrower's client counts it down too: econ.js)
    return true;
  },
  // the loop in flight (tickProjectiles hands every 'loop' here). phase 0 = flying open, 1 = missed and dropping,
  // 2 = being reeled back to the thrower's hand
  stepLoop(pr, n, owner, prev, dt) {
    if (!owner || !owner.alive || (owner.lz && (owner.lz.hold || owner.lz.by))) { this.removeProj(pr); return; }
    const z = this.lz(owner);
    if (pr.phase === 0) {
      const wall = stepProjectile(pr, dt, this.boxes, LASSO.grav);
      const c = this.sweep(prev, pr.p, pr.r, (t) => t === owner || pr.hit.has(t.id))[0];
      if (c && this.lassoTouch(pr, owner, c.t, c.at, prev)) return;
      if (wall || dist3(eyeOf(owner), pr.p) >= pr.R || n - pr.born > 2500 || pr.p[1] < this.map.killY) this.loopPhase(pr, 1, n, z);
    } else if (pr.phase === 1) {
      pr.v[0] *= Math.exp(-3 * dt); pr.v[2] *= Math.exp(-3 * dt);
      stepProjectile(pr, dt, this.boxes, 26);
      if (n - pr.t1 > LASSO.drop * 1000) this.loopPhase(pr, 2, n, z);
    } else {
      const e = eyeOf(owner);
      e[1] -= 0.45;
      const to = [e[0] - pr.p[0], e[1] - pr.p[1], e[2] - pr.p[2]], d = Math.hypot(to[0], to[1], to[2]);
      if (d < 1.4 || n - pr.t1 > 2500) { this.removeProj(pr, { c: 1 }); if (z.loop === pr.id) z.loop = 0; return; }
      const sp = Math.min(90, Math.max(LASSO.back, Math.hypot(owner.vel[0], owner.vel[1], owner.vel[2]) + 12));
      for (let k = 0; k < 3; k++) { pr.v[k] = (to[k] / d) * sp; pr.p[k] += pr.v[k] * dt; }
    }
  },
  loopPhase(pr, ph, n, z) {
    pr.phase = ph; pr.t1 = n;
    if (ph === 1) { pr.v[1] = Math.min(pr.v[1], 2); z.next = Math.max(z.next, n + LASSO.cd * 1000); } // a miss: short cooldown
    this.broadcast({ t: 'lasso', k: 'lu', id: pr.id, ph, p: pr.p.map(r2), v: pr.v.map(r2) });
  },
  // who can be caught: alive, not spawn protected, not frozen solid, not already on a rope (either end), not between
  // rounds. teammates can (a mobility trick: no damage, no credit)
  lassoCatchable(by, t, n) {
    if (!t.alive || t === by || (this.round && this.round.over)) return false;
    if (!t.isBot && n - t.spawnT < 1200) return false;
    if (t.frozenUntil > n || t.quiz) return false; // frozen solid / sitting a pop quiz: it just drops off them
    return !(t.lz && (t.lz.hold || t.lz.by));
  },
  // the open loop touched t at `at`. true = the loop's done (caught, cut, slid off, blocked)
  lassoTouch(pr, owner, t, at, prev) {
    const n = now(), z = this.lz(owner);
    pr.hit.set(t.id, n);
    const tc = [t.pos[0], t.pos[1] + 0.9, t.pos[2]], to = [tc[0] - at[0], tc[1] - at[1], tc[2] - at[2]], tl = Math.hypot(to[0], to[1], to[2]);
    if (tl > 0.3 && raycast(at, [to[0] / tl, to[1] / tl, to[2] / tl], tl - 0.3, this.boxes)) return false; // they're behind a wall
    pr.p = at.slice();
    // a katana parry cuts it clean through
    const foe = !this.friendly(owner, t);
    if (foe && t.parryT) {
      const inc = [prev[0] - at[0], prev[1] - at[1], prev[2] - at[2]];
      const pf = this.parryAt(t, Math.hypot(inc[0], inc[1], inc[2]) > 1e-4 ? inc : pr.v.map((x) => -x));
      if (pf) {
        this.parryFx(t, owner, pf === 2, 'lasso', this.parrySpot(t, inc), {});
        this.broadcast({ t: 'lasso', k: 'cut', id: pr.id, o: owner.id, by: t.id, p: at.map(r2) });
        this.removeProj(pr, { cut: 1 });
        z.loop = 0; z.next = n + LASSO.cd * 1000;
        return true;
      }
    }
    // a 2 m steel wrecking ball is far too heavy: the loop slides off
    if (this.isBall(t, n) || rigged(this, t, n)) { // (an overdrive rig too)
      this.broadcast({ t: 'lasso', k: 'slide', id: pr.id, on: t.id, p: at.map(r2) });
      pr.v = [pr.v[0] * -0.15, 5, pr.v[2] * -0.15];
      this.loopPhase(pr, 1, n, z);
      return true;
    }
    if (foe && this.bubbleBlocks(owner, t)) { this.broadcast({ t: 'fx', k: 'bubhit', p: at.map(r2) }); this.loopPhase(pr, 1, n, z); return true; }
    if (!this.lassoCatchable(owner, t, n)) { this.loopPhase(pr, 1, n, z); return true; } // it just drops off them
    // reverse card: the catch flips. they hold the rope and you're on the end of it
    let H = owner, V = t;
    if (foe && t.reverseUntil > n && this.lassoCatchable(t, owner, n)) {
      this.broadcast({ t: 'fx', k: 'reflect', id: t.id, by: owner.id });
      H = t; V = owner;
    }
    this.removeProj(pr, { c: 1 });
    z.loop = 0;
    this.lassoStart(H, V, H !== owner);
    return true;
  },
  lassoStart(H, V, rev) {
    const n = now(), zh = this.lz(H), zv = this.lz(V);
    const L = clampLen(dist3(eyeOf(H), waistOf(V)));
    zh.hold = { v: V.id, seq: V.seq, hseq: H.seq, L, Lok: Math.max(L, dist3(eyeOf(H), waistOf(V))), t0: n, lastT: n, pos: V.pos.slice(), vel: V.vel.slice(), st: {}, sim: !!H.isBot, bad: 0, n: 0 };
    if (zh.loop && this.projectiles.has(zh.loop)) this.removeProj(this.projectiles.get(zh.loop));
    zh.loop = 0;
    zv.by = H.id; zv.wr = 0; zv.wrT = 0; zv.fl = null;
    V.g = null;
    if (V.ai) V.ai.hook = null; // their grapple lets go
    if (!this.friendly(H, V)) this.tag(V, H, 'lasso');
    if (H.isBot) H.ai.lasso = { t0: n, ph: 0 };
    this.broadcast({ t: 'lasso', k: 'hold', id: H.id, v: V.id, L: r2(L), p: V.pos.map(r2), vel: V.vel.map(r2), rev: rev ? 1 : undefined });
  },

  // ---------------------------------------------------------- letting go
  lassoRelease(p, m) {
    const H = p.lz && p.lz.hold;
    if (!H) return;
    const V = this.players.get(H.v);
    // the body as the holder's client has it right now: one last sample (checked like the rest)
    if (!H.sim && V && V.alive && V.seq === H.seq) { const pos = vec3(m.p), vel = vec3(m.v); if (pos && vel) this.lassoAccept(p, H, V, pos, vel, now()); }
    this.lassoEnd(p, 'fling');
  },
  // h stops holding (why: fling = let go on purpose, the launch; anything else = the rope just drops them)
  lassoEnd(h, why) {
    const z = h.lz, H = z && z.hold;
    if (!H) return;
    z.hold = null;
    if (h.ai) h.ai.lasso = null;
    const V = this.players.get(H.v), zv = V && V.lz;
    if (zv && zv.by === h.id) zv.by = 0;
    if (!V || !V.alive || V.seq !== H.seq) { this.broadcast({ t: 'lasso', k: 'rel', id: h.id, v: H.v, why: 'gone' }); return; }
    // a fling keeps all their speed x mul plus yours. the rope dropping them (time, wriggling, death) keeps it as is
    let vel = why === 'fling' ? flingVel(H.vel, capLen(h.vel, 40)) : capLen(H.vel, LASSO.cap);
    if (this.friendly(h, V)) vel = capLen(vel, TEAM_CAP); // a teammate: a boost, not a trip into the void
    if (V.trap && why === 'fling') this.popTrap(V, 'hit', h, 'lasso'); // yanked out of a soap bubble: it pops, they fly
    V.pos = H.pos.slice(); V.vel = vel.slice();
    if (V.isBot) V.onGround = false;
    const sp = Math.hypot(vel[0], vel[1], vel[2]), fr = this.friendly(h, V);
    zv.fl = { by: h.id, t0: now(), p0: V.pos.slice(), lv: vel.slice(), sp, fr, why, sim: { pos: V.pos.slice(), vel: vel.slice(), t: now() } };
    if (!fr) this.tag(V, h, 'lasso'); // a fling into the void is yours (the usual last-attacker credit)
    this.broadcast({ t: 'lasso', k: 'rel', id: h.id, v: V.id, why, p: V.pos.map(r2), vel: vel.map(r2) });
  },
  // anything that ends p's part in it: death, leaving, a reset. ropes drop, a flight in progress gets its distance
  lassoDrop(p, why) {
    const z = p.lz;
    if (!z) return;
    if (z.hold) this.lassoEnd(p, why);
    if (z.by) { const h = this.players.get(z.by); if (h) this.lassoEnd(h, why); z.by = 0; }
    if (z.fl) this.lassoLand(p, true);
    if (z.loop && this.projectiles.has(z.loop)) this.removeProj(this.projectiles.get(z.loop));
    z.loop = 0; z.spin0 = 0;
  },
  // just the ropes (a photo frame teleported them, ...): whatever p holds or hangs off drops, flights and loops stay
  lassoCut(p, why) {
    const z = p.lz;
    if (!z) return;
    if (z.hold) this.lassoEnd(p, why);
    if (z.by) { const h = this.players.get(z.by); if (h) this.lassoEnd(h, why); z.by = 0; }
  },
  // the flight's over: tell everyone how far the fling took them
  lassoLand(V, died) {
    const fl = V.lz.fl;
    V.lz.fl = null;
    const d = Math.hypot(V.pos[0] - fl.p0[0], V.pos[2] - fl.p0[2]);
    if (fl.why === 'fling' && fl.sp > 8) this.broadcast({ t: 'lasso', k: 'land', id: V.id, by: fl.by, d: Math.round(d), s: Math.round(fl.sp), void: died ? 1 : undefined, p: V.pos.map(r2) });
  },

  // ---------------------------------------------------------- wriggling free
  lassoWriggle(p) {
    const z = p.lz;
    if (!z || !z.by) return;
    const n = now();
    if (n - z.wrT < LASSO.wrGap) return; // presses closer than this don't count (no macros)
    z.wrT = n;
    const h = this.players.get(z.by);
    z.wr += h && this.friendly(h, p) ? 1 : 1 / LASSO.wriggle; // a teammate's rope: one press and you're off
    if (z.wr >= 1) { if (h) this.lassoEnd(h, 'wriggle'); return; }
    if ((z.wrN = (z.wrN || 0) + 1) % 3 === 0) { send(p, { t: 'lasso', k: 'wr', n: r2(z.wr) }); if (h) send(h, { t: 'lasso', k: 'wr', id: p.id, n: r2(z.wr) }); }
  },

  // ---------------------------------------------------------- splats
  // speed lost against the map between two samples of a body on a rope or in flight: per axis, what it was doing into
  // a surface it's now right up against and isn't doing any more
  lassoImpactSpeed(v0, v1, pos) {
    let s2 = 0, ax = -1, best = 0;
    for (let i = 0; i < 3; i++) {
      const a = v0[i];
      if (Math.abs(a) < 6) continue;
      const keep = Math.sign(v1[i]) === Math.sign(a) ? Math.abs(v1[i]) : 0, lost = Math.abs(a) - keep;
      if (lost < Math.abs(a) * 0.6 || !touching(this.boxes, pos, i, Math.sign(a))) continue;
      s2 += lost * lost;
      if (lost > best) { best = lost; ax = i; }
    }
    return { s: Math.sqrt(s2), ax };
  },
  lassoImpact(by, V, v0, v1, pos) {
    const { s, ax } = this.lassoImpactSpeed(v0, v1, pos);
    if (s >= LASSO.splat[0]) this.lassoSplat(by, V, s, ax);
  },
  lassoSplat(by, V, s, ax) {
    const n = now(), z = this.lz(V);
    if (n - (z.splatT || 0) < 300) return;
    z.splatT = n;
    const dmg = splatDmg(s);
    this.broadcast({ t: 'lasso', k: 'splat', id: V.id, by: by ? by.id : 0, s: Math.round(s), ax, p: V.pos.map(r2), d: Math.round(dmg) });
    if (!by || this.friendly(by, V)) return; // teammates: a free ride, no damage
    if (V.trap) { this.popTrap(V, 'hit', by, 'lasso'); return; } // a soap bubble takes the hit (and pops)
    this.damage(V, dmg, by, 'lasso');
  },

  // ---------------------------------------------------------- every tick
  tickLasso(dt) {
    const n = now();
    for (const h of this.players.values()) {
      const z = h.lz;
      if (!z) continue;
      const H = z.hold;
      if (H) {
        const V = this.players.get(H.v);
        if (!h.alive || h.seq !== H.hseq) this.lassoEnd(h, 'dead');
        else if (!V || !V.alive || V.seq !== H.seq) this.lassoEnd(h, 'gone');
        else if (this.isBall(h, n) || h.trap || rigged(this, h, n) || busy(h, n)) this.lassoEnd(h, 'drop'); // turned into a ball / rigged up / sealed in soap / asleep, frozen or quizzed: the rope goes
        else if (this.isBall(V, n) || rigged(this, V, n) || V.quiz) this.lassoEnd(h, 'drop'); // the one on the end turned into a ball or rigged up (too heavy), or got a pop quiz
        else if (n - H.t0 > LASSO.time * 1000) this.lassoEnd(h, 'time');
        else if (!H.sim && n - H.lastT > QUIET) this.lassoEnd(h, 'lag'); // the holder's stream went quiet
        else if (H.sim) this.lassoSim(h, H, V, dt);
      }
      if (z.by) {
        if (n - z.wrT > 300) z.wr = Math.max(0, z.wr - LASSO.wrDecay * dt);
        if (h.isBot && h.ai && !h.ai.dummy && Math.random() < dt * (BOT_DIFF[h.ai.diff] || BOT_DIFF.normal).rate * 7) this.lassoWriggle(h); // bots mash too
      }
      if (z.fl && h.isBot) this.lassoFlight(h, n);
      if (h.isBot && h.ai && h.ai.lspin) h.f |= FLAGS.LASSO; // a bot spinning the loop (stepBot just reset its flags)
    }
  },
  // a bot holds someone: the same step their client would run, here
  lassoSim(h, H, V, dt) {
    const b = { pos: H.pos, vel: H.vel };
    const r = holdStep(b, { eye: eyeOf(h), dir: aimDir(h.yaw, h.pitch), L: H.L, hv: h.vel }, H.st, dt, this.boxes);
    V.pos = H.pos.slice(); V.vel = H.vel.slice();
    H.lastT = now();
    if (r.impact >= LASSO.splat[0]) this.lassoSplat(h, V, r.impact, r.n);
    if (!V.isBot && (H.n++ & 1) === 0) send(V, { t: 'lh', p: H.pos.map(r2), v: H.vel.map(r2) });
  },
  // a flung body: splats against whatever it hits, and the distance once it lands (humans: from their snapshots).
  // for the first LOCK s (their client gives them no control then either) a human's reports are held near where the
  // server's own copy of the flight has them, so a client can't just shrug a fling off
  lassoFlight(V, n) {
    const fl = V.lz.fl;
    if (!V.alive) { this.lassoLand(V, true); return; }
    if (!V.isBot && fl.sim && n - fl.t0 < LOCK * 1000) {
      const S = fl.sim, dt = Math.min(0.1, (n - S.t) / 1000);
      if (dt > 0) { S.vel[1] -= 26 * dt; movePlayer(S.pos, S.vel, dt, this.boxes, false); S.t = n; }
      const d = dist3(V.pos, S.pos), slack = 2 + Math.hypot(S.vel[0], S.vel[1], S.vel[2]) * 0.08;
      if (d > slack) { for (let k = 0; k < 3; k++) V.pos[k] = S.pos[k] + (V.pos[k] - S.pos[k]) * (slack / d); V.vel = S.vel.slice(); }
    } else fl.sim = null;
    const { s, ax } = this.lassoImpactSpeed(fl.lv, V.vel, V.pos);
    if (s >= LASSO.splat[0]) this.lassoSplat(this.players.get(fl.by) || null, V, s, ax);
    fl.lv = V.vel.slice();
    if (!V.lz.fl) return; // (the splat killed them)
    const landed = n - fl.t0 > 150 && V.vel[1] <= 0.5 && touching(this.boxes, V.pos, 1, -1, 0.1);
    if (landed || n - fl.t0 > 6000) this.lassoLand(V, false);
  },
  // snapshot hook ('s'): a held player is wherever the rope has them, whatever their own client says. also notes when
  // they started spinning the loop (a throw can't claim more spin than that) and checks flights for splats
  lassoSnap(p) {
    const z = p.lz;
    if (!z && !(p.f & FLAGS.LASSO)) return;
    const lz = this.lz(p);
    if (lz.by) {
      const h = this.players.get(lz.by), H = h && h.lz && h.lz.hold;
      if (H && H.v === p.id) { p.pos = H.pos.slice(); p.vel = H.vel.slice(); p.g = null; }
    }
    if ((p.f & FLAGS.LASSO) && p.w !== 'lasso') p.f &= ~FLAGS.LASSO; // only with the lasso out
    if (p.f & FLAGS.LASSO) { if (!lz.spin0) lz.spin0 = now(); } else lz.spin0 = 0;
    if (lz.fl) this.lassoFlight(p, now());
  },
  // stepBot hook: a bot on the end of a rope doesn't move itself (the holder does that)
  lassoBot(b) {
    if (!b.lz || !b.lz.by) return false;
    b.onGround = false; b.f = 0;
    if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
    return true;
  },
  // ---------------------------------------------------------- bots with the lasso (bot rooms)
  // some bots carry it instead of a gun (JF_LASSO_BOTS = the share of them, for tests)
  lassoArm(b) { if (this.mode === 'bots' && b.ai && !b.ai.dummy && Math.random() < BOT_SHARE) { b.w = 'lasso'; b.ai.ammo = 1; } },
  // botThink hook. not holding: spin up and throw at whoever it's after once they're close and in sight (the normal
  // think keeps it moving and aiming meanwhile). holding: let the rope out, shake them about, walk backwards toward
  // the best place to fling them (a drop, else a wall) and flick round, letting go at the peak
  lassoThink(b, dt) {
    if (b.w !== 'lasso' || !b.ai || b.ai.dummy) return null;
    const ai = b.ai, z = this.lz(b), n = now();
    if (z.hold) return this.lassoBotHold(b, z.hold, dt, n);
    const t = this.players.get(ai.target);
    if (ai.lspin) {
      if (!t || !t.alive || n - ai.lspin > 2500 || n < (b.staggerUntil || 0)) { ai.lspin = 0; z.spin0 = 0; return null; }
      if (n - ai.lspin > ai.lspinT) { this.lassoBotThrow(b, t, n); ai.lspin = 0; }
      return null;
    }
    const D = BOT_DIFF[ai.diff] || BOT_DIFF.normal, d = t && t.alive ? dist3(t.pos, b.pos) : 99;
    if (d < 1) { const a = ai.seed + n * 0.0007; return { wx: Math.cos(a) * D.speed, wz: Math.sin(a) * D.speed, jump: false }; } // spawned on top of them: step off first
    if (d < 21 && n >= z.next && !(z.loop && this.projectiles.has(z.loop)) && ai.seenAt && n - ai.seenAt > D.react && this.lassoCatchable(b, t, n)) {
      ai.lspin = n; z.spin0 = n; ai.lspinT = (d < 6 ? 250 : 450) + Math.random() * 600; // close: a quick flick of a throw
    }
    return null;
  },
  // lead them: where they'll be when the loop gets there, a bit high for its drop (plus the bot's aim error)
  lassoBotThrow(b, t, n) {
    const D = BOT_DIFF[b.ai.diff] || BOT_DIFF.normal, z = this.lz(b);
    const s = Math.min(1, (n - (z.spin0 || n)) / 1000 / LASSO.spinT + 0.25), e = eyeOf(b), sp = throwSpeed(s);
    const aim = [t.pos[0], t.pos[1] + W, t.pos[2]];
    let k = dist3(e, aim) / sp;
    for (let i = 0; i < 3; i++) aim[i] += t.vel[i] * k * 0.8;
    k = dist3(e, aim) / sp;
    aim[1] += 0.5 * LASSO.grav * k * k - 1.2 * k;
    const d = norm([aim[0] - e[0] + (Math.random() - 0.5) * D.err * 40, aim[1] - e[1] + (Math.random() - 0.5) * D.err * 20, aim[2] - e[2] + (Math.random() - 0.5) * D.err * 40]);
    if (d) { b.yaw = Math.atan2(-d[0], -d[2]); b.pitch = Math.asin(Math.max(-1, Math.min(1, d[1]))); this.lassoThrow(b, { o: e, d, s }); }
  },
  // which way to fling someone from here: toward the nearest drop into the void if there's one, else at a wall
  lassoTarget(b) {
    let best = null, bs = -1;
    const a0 = Math.random() * Math.PI * 2;
    for (let i = 0; i < 16; i++) {
      const a = a0 + (i / 16) * Math.PI * 2, d = [Math.sin(a), Math.cos(a)];
      let sc = Math.random() * 0.5;
      // a drop: no floor under where they'd come down
      let drop = 0;
      for (const r of [20, 35, 55, 80]) {
        const q = [b.pos[0] + d[0] * r, b.pos[1] + 3, b.pos[2] + d[1] * r];
        if (!raycast(q, [0, -1, 0], 80, this.boxes)) drop++;
      }
      if (drop >= 2) sc += 10 + drop;
      // a wall to splat them on: something solid 8-40 m away at body height
      const w = raycast([b.pos[0], b.pos[1] + 1.2, b.pos[2]], [d[0], 0, d[1]], 40, this.boxes);
      if (w && w.t > 8) sc += 3 + (40 - w.t) * 0.05;
      // walking backwards that way: is there floor for it?
      if (!raycast([b.pos[0] + d[0] * 3, b.pos[1] + 0.5, b.pos[2] + d[1] * 3], [0, -1, 0], 4, this.boxes)) sc -= 4;
      if (sc > bs) { bs = sc; best = d; }
    }
    return best;
  },
  lassoBotHold(b, H, dt, n) {
    const ai = b.ai, st = ai.lasso || (ai.lasso = { t0: n }), age = (n - st.t0) / 1000;
    if (!st.dir) { st.dir = this.lassoTarget(b) || [0, 1]; st.tf = 1.4 + Math.random() * 0.35; st.sgn = Math.random() < 0.5 ? 1 : -1; st.best = 0; st.f = 1.2 + Math.random() * 0.4; }
    H.L = Math.min(LASSO.len[1], H.L + LASSO.reel * 1.6 * dt); // all the rope out
    const fy = Math.atan2(-st.dir[0], -st.dir[1]), by = fy + Math.PI; // face away from where they're going, then flick round
    let wx = 0, wz = 0;
    if (age < st.tf) {
      if (st.y0 == null) st.y0 = b.yaw;
      const turn = Math.min(1, age / 0.45); // swing round to face away first, then shake them about
      let dy = by - st.y0; while (dy > Math.PI) dy -= Math.PI * 2; while (dy < -Math.PI) dy += Math.PI * 2;
      b.yaw = st.y0 + dy * turn + Math.sin(age * Math.PI * 2 * st.f) * 0.3 * Math.min(1, age / 0.4);
      b.pitch = 0.1;
      if (age > st.tf - 0.6) { wx = st.dir[0]; wz = st.dir[1]; } // walk backwards (toward the fling)
      st.yf = b.yaw;
    } else {
      const k = Math.min(1, (age - st.tf) / 0.17), e = k * k * (3 - 2 * k);
      let dy = fy - st.yf; while (dy > Math.PI) dy -= Math.PI * 2; while (dy < -Math.PI) dy += Math.PI * 2;
      if (Math.abs(dy) > 2.6) dy = st.sgn * Math.abs(dy); // nearly a half turn: either way round works
      b.yaw = st.yf + dy * e; b.pitch = 0.1 + 0.35 * e;
      if (age - st.tf < 0.35) { wx = st.dir[0]; wz = st.dir[1]; }
      if (k >= 1) { // let go at the peak: once they stop speeding up toward where we want them (and a bit up)
        const sp = H.vel[0] * st.dir[0] + H.vel[2] * st.dir[1] + Math.max(0, H.vel[1]) * 0.5;
        if ((st.best > 20 && sp < st.best * 0.97) || age > st.tf + 1.2) { this.lassoEnd(b, 'fling'); return { wx: 0, wz: 0, jump: false }; }
        st.best = Math.max(st.best, sp);
      }
    }
    if ((wx || wz) && b.onGround && !raycast([b.pos[0] + wx * 2.5, b.pos[1] + 0.5, b.pos[2] + wz * 2.5], [0, -1, 0], 6, this.boxes)) { wx = 0; wz = 0; } // not off the edge yourself
    const D = BOT_DIFF[ai.diff] || BOT_DIFF.normal;
    return { wx: wx * D.speed, wz: wz * D.speed, jump: false };
  },
  // late joiners: who's holding who right now
  lassoJoin(p) {
    for (const h of this.players.values()) {
      const H = h.lz && h.lz.hold;
      if (H) send(p, { t: 'lasso', k: 'hold', id: h.id, v: H.v, L: r2(H.L), p: H.pos.map(r2), vel: H.vel.map(r2), late: 1 });
    }
  },
};

export function installLasso(Room) { Object.assign(Room.prototype, M); }
