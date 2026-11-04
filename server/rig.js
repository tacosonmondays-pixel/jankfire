// Overdrive Rig killstreak, the server side. Movement is the client's, but everything that hurts or helps is judged here:
// the overshield and the block (in Room.damage), the rocket punch (from the server's own positions along the dash), wall
// slams, quickhacks (range, line of sight, cooldown), the homing missiles (server projectiles) and leap landings.
// installRig(Room, helpers) adds these methods to Room; server.js calls them from one-line hooks.
import { FLAGS, STREAKS } from '../shared/weapons.js';
import { RIG, RIG_BITS, punchDmg, punchDist, dashDir, lerpK, inFront } from '../shared/rig.js';
import { raycast, stepProjectile, movePlayer } from '../shared/physics.js';

const P = RIG.punch, M = RIG.miss, L = RIG.leap, H = RIG.hack;
const chest = (p) => [p.pos[0], p.pos[1] + 1.35, p.pos[2]];
const head = (p) => [p.pos[0], p.pos[1] + 2.4, p.pos[2]];
// shortest distance from point c to the segment a-b
function segDist(a, b, c) {
  const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], l2 = ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2];
  const t = l2 > 1e-9 ? Math.max(0, Math.min(1, ((c[0] - a[0]) * ab[0] + (c[1] - a[1]) * ab[1] + (c[2] - a[2]) * ab[2]) / l2)) : 0;
  return Math.hypot(a[0] + ab[0] * t - c[0], a[1] + ab[1] * t - c[1], a[2] + ab[2] * t - c[2]);
}
// nothing solid between a and b
function clear(a, b, boxes) {
  const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], l = Math.hypot(d[0], d[1], d[2]);
  return l < 0.35 || !raycast(a, [d[0] / l, d[1] / l, d[2] / l], l - 0.3, boxes);
}
// turn unit vector a toward unit vector b by at most `max` radians (missile homing)
function turnToward(a, b, max) {
  const dot = Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2])), ang = Math.acos(dot);
  if (ang <= max) return b.slice();
  const k = max / ang, o = [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k], l = Math.hypot(o[0], o[1], o[2]) || 1;
  return [o[0] / l, o[1] / l, o[2] / l];
}

export function installRig(Room, U) {
  const { now, num, vec3, norm, r2, center, safe, REC_T } = U;
  REC_T.add('rig'); // punches, hacks, missiles and landings show up in the play of the round

  Object.assign(Room.prototype, {
    rigOn(p, n = now()) { return !!(p && p.alive && p.rig && p.rig.until > n); },
    rigShrug(v) { return v.map((x) => x * RIG.kbTake); }, // knockback on a rig: mostly ignored

    // ------------------------------------------------------------ on / off
    rigStart(p) {
      const n = now(), dur = (STREAKS.overdrive.dur || RIG.dur) * 1000;
      // +1 s: the client's own timer ends it, this only cleans up after a client that never says so
      p.rig = {
        until: n + dur + 1000, shield: RIG.shield, store: 0, punchT: 0, hackT: 0, missT: 0, leapT: 0,
        ch: { t0: 0, t1: 0 }, lp: { t0: 0, t1: 0 }, dash: null, leap: null, sq: null, sqT: 0,
      };
      p.g = null; p.hackedUntil = 0;
      this.broadcast({ t: 'rig', k: 'on', id: p.id, dur, sh: RIG.shield });
    },
    rigEnd(p) {
      p.rig = null; p.f &= ~RIG_BITS;
      this.broadcast({ t: 'rig', k: 'off', id: p.id });
    },
    // died: quietly (every client bursts the frame open from the kill message), and no rig at the respawn point
    // until the respawned client speaks
    rigDeath(t) { t.rig = null; t.f &= ~RIG_BITS; t.rigSlam = null; t.hackedUntil = 0; },
    rigReset(p) { if (p.rig) this.rigEnd(p); p.hackedUntil = 0; p.rigSlam = null; },

    // ------------------------------------------------------------ snapshots
    // the rig flags only count from someone who activated the rig, and nobody in the rig (or hacked) has a rope.
    // a held punch / leap counts from the first snapshot that had its flag (a hitch of up to a second doesn't restart it)
    rigSnap(p) {
      const n = now(), R = p.rig;
      if (p.hackedUntil > n) p.g = null;
      if (!R || !(R.until > n) || !(p.f & FLAGS.RIG)) { p.f &= ~RIG_BITS; return; }
      p.g = null;
      for (const [bit, h] of [[FLAGS.RIG_CHARGE, R.ch], [FLAGS.RIG_LEAP, R.lp]]) {
        if (!(p.f & bit)) continue;
        if (!h.t0 || n - h.t1 > 1000) h.t0 = n;
        h.t1 = n;
      }
      if (R.leap && !R.leap.landed) R.leap.top = Math.max(R.leap.top, p.pos[1]);
    },
    // how long (ms) a charge was really held: from the first snapshot with its flag to the let-go message (+ a snapshot
    // of slack). it has to have been flagged lately: no charging up in secret
    rigHeld(h, n) {
      const ms = h.t0 && n - h.t1 < 1000 ? n - h.t0 + 60 : 0;
      h.t0 = 0;
      return ms;
    },

    // ------------------------------------------------------------ damage: block, then the overshield
    // called from damage() before HP: returns what's left for HP. blocking (forearms up, judged from the server's yaw)
    // cuts hits from the front by 80% and every blocked point charges the next punch
    rigSoak(t, amt, attacker, w, from) {
      const R = t.rig, n = now();
      if (!R || !(R.until > n) || !(amt > 0)) return amt;
      let blocked = 0;
      const src = attacker && attacker !== t ? attacker.pos : from;
      if ((t.f & FLAGS.RIG_BLOCK) && src && inFront(t.yaw, t.pos, src)) {
        blocked = amt * RIG.block.cut;
        amt -= blocked;
        R.store = Math.min(1, R.store + blocked / RIG.block.full);
      }
      const sh = Math.min(R.shield, amt);
      R.shield -= sh; amt -= sh;
      if (blocked > 0 || sh > 0) {
        const q = R.sq || (R.sq = { a: 0, b: 0, from: new Set(), src: null });
        q.a += sh + blocked; q.b += blocked;
        if (attacker && attacker !== t) q.from.add(attacker.id);
        if (src) q.src = src;
        if (sh > 0 && R.shield <= 0) this.rigFlush(t); // it just broke: say so right away
      }
      return amt;
    },
    // shield + block hits go out batched (a minigun is 25 hits a second): who hit it (hitmarkers), how much, what's left
    rigFlush(t) {
      const R = t.rig, q = R && R.sq;
      if (!q) return;
      R.sq = null; R.sqT = now();
      this.broadcast({ t: 'rig', k: 'sh', id: t.id, s: Math.round(R.shield), a: Math.round(q.a), b: Math.round(q.b), st: r2(R.store), from: [...q.from].slice(0, 8), p: q.src ? q.src.map(r2) : undefined });
    },

    // ------------------------------------------------------------ client messages ({ t: 'rig', k })
    onRig(p, m) {
      const n = now();
      if (!this.rigOn(p, n) || typeof m.k !== 'string') return;
      if (m.k === 'punch') this.rigPunch(p, m, n);
      else if (m.k === 'hack') this.rigHack(p, m, n);
      else if (m.k === 'miss') this.rigMissiles(p, m, n);
      else if (m.k === 'leap') this.rigLeap(p, m, n);
      else if (m.k === 'land') this.rigLand(p, m, n);
    },

    // rocket punch: the client says it let go (and how charged it thinks it is); the server believes the charge it
    // saw held (or what blocking stored), runs the dash itself (the same straight rush the client makes, stopped by the
    // same walls) from where it has the rig, and smashes whoever the fist passes. no client says who got hit
    rigPunch(p, m, n) {
      const R = p.rig, d = norm(vec3(m.d));
      if (!d || n - R.punchT < P.cd * 1000 - 120) return;
      const held = this.rigHeld(R.ch, n) / (P.charge * 1000);
      const c = Math.max(0, Math.min(1, num(m.c) || 0, Math.max(held, R.store)));
      R.store = 0; R.punchT = n;
      const dir = dashDir(d), at = chest(p);
      R.dash = { c, dir, dist: this.rigDashLen(p, dir, punchDist(c)), from: at, prev: at, t0: n, hit: new Set() };
      this.broadcast({ t: 'rig', k: 'punch', id: p.id, c: r2(c), d: dir.map(r2) });
      this.rigDash(p, n); // whoever is right in front of you gets it now
    },
    // how far the dash really goes before a wall stops it: the client's move (120 Hz steps, the rig's box), on the server's map
    rigDashLen(p, dir, dist) {
      const pos = p.pos.slice(), v = [0, 0, 0], h = 1 / 120;
      for (let t = 0; t < dist / P.speed; t += h) {
        v[0] = dir[0] * P.speed; v[1] = dir[1] * P.speed; v[2] = dir[2] * P.speed;
        if (movePlayer(pos, v, h, this.boxes, true).wall) break;
      }
      return Math.min(dist, Math.hypot(pos[0] - p.pos[0], pos[1] - p.pos[1], pos[2] - p.pos[2]));
    },
    rigDash(p, n) {
      const D = p.rig.dash;
      // the fist moves down the dash line at dash speed from when the punch came in (a short grace after it stops)
      const along = Math.min(D.dist, P.speed * (n - D.t0) / 1000);
      if (n - D.t0 > (D.dist / P.speed) * 1000 + 120) { p.rig.dash = null; return; }
      const a = D.prev, b = [D.from[0] + D.dir[0] * along, D.from[1] + D.dir[1] * along, D.from[2] + D.dir[2] * along];
      D.prev = b;
      const tip = [b[0] + D.dir[0] * P.reach, b[1] + D.dir[1] * P.reach, b[2] + D.dir[2] * P.reach];
      for (const t of this.players.values()) {
        if (t === p || !t.alive || D.hit.has(t.id) || this.friendly(p, t)) continue;
        const tc = center(t), reach = P.radius + 0.55 + (this.rigOn(t, n) ? 0.45 : 0) + Math.hypot(t.vel[0], t.vel[2]) * 0.06;
        if (segDist(a, tip, tc) > reach) continue;
        if (!clear(b, tc, this.boxes) && !clear(a, tc, this.boxes)) continue; // not through walls
        D.hit.add(t.id);
        this.rigSmash(p, t, D, n);
      }
    },
    // the punch lands: damage + a huge launch the way the punch was going. watch them for a wall (rigWall)
    rigSmash(p, t, D, n) {
      const hl = Math.hypot(D.dir[0], D.dir[2]) || 1, fx = D.dir[0] / hl, fz = D.dir[2] / hl;
      const kb = lerpK(P.kb, D.c), up = lerpK(P.up, D.c) + Math.max(0, D.dir[1]) * kb * 0.5;
      const tc = center(t);
      const got = this.hurt(t, p, 'rigpunch', punchDmg(D.c), [fx * kb, up, fz * kb]);
      this.broadcast({ t: 'rig', k: 'hit', id: p.id, to: t.id, p: tc.map(r2), c: r2(D.c), d: [r2(fx), r2(fz)] });
      // (seeded with the launch speed: someone punched while standing against a wall reads as stopped dead at once)
      if (got === t && t.alive) t.rigSlam = { by: p.id, until: n + P.wallWin * 1000, dir: [fx, fz], pv: kb * (this.rigOn(t, n) ? RIG.kbTake : 1) };
    },
    // wall slam: a punched body that stops dead (its speed along the punch drops by half from one reading to the
    // next) with a wall right there in front of it. humans' speeds come from their snapshots, bots' from the server
    rigWall(t, n) {
      const s = t.rigSlam;
      if (!t.alive || n > s.until) { t.rigSlam = null; return; }
      const v = t.vel[0] * s.dir[0] + t.vel[2] * s.dir[2], was = s.pv;
      if (v === was) return; // no new reading yet
      s.pv = v;
      if (was == null || was < 10 || v > was * 0.55) return;
      const c = center(t), dir = [s.dir[0], 0, s.dir[1]];
      const h = raycast(c, dir, 1.7, this.boxes) || raycast([c[0], c[1] + 0.8, c[2]], dir, 1.7, this.boxes) || raycast([c[0], c[1] - 0.6, c[2]], dir, 1.7, this.boxes);
      if (!h || h.axis === 1) return;
      t.rigSlam = null;
      this.hurt(t, this.players.get(s.by) || null, 'rigslam', P.wall, null);
      this.broadcast({ t: 'rig', k: 'wall', id: s.by, to: t.id, p: h.point.map(r2), n: h.normal, v: Math.round(was) });
    },

    // quickhack: fry their grapple. in range, in front of you (the server's view is a snapshot old: 35 degrees of
    // slack), line of sight, cooldown. bots just can't hook for a while; players are told (their rope snaps)
    rigHack(p, m, n) {
      const R = p.rig;
      if (n - R.hackT < H.cd * 1000 - 150) return;
      const t = this.players.get(m.to);
      if (!t || t === p || !t.alive || this.friendly(p, t) || this.bubbleBlocks(p, t)) return;
      const e = head(p), tc = center(t), d = [tc[0] - e[0], tc[1] + 0.4 - e[1], tc[2] - e[2]], l = Math.hypot(d[0], d[1], d[2]);
      if (l > H.range + 2 || l < 0.1) return;
      const cp = Math.cos(p.pitch), look = [-Math.sin(p.yaw) * cp, Math.sin(p.pitch), -Math.cos(p.yaw) * cp];
      if ((look[0] * d[0] + look[1] * d[1] + look[2] * d[2]) / l < Math.cos(0.6)) return;
      if (raycast(e, [d[0] / l, d[1] / l, d[2] / l], l - 0.4, this.boxes)) return;
      R.hackT = n;
      t.hackedUntil = n + H.dur * 1000;
      t.g = null;
      if (t.ai) { t.ai.hook = null; t.ai.nextHook = Math.max(t.ai.nextHook || 0, t.hackedUntil); }
      this.broadcast({ t: 'rig', k: 'hack', id: p.id, to: t.id, dur: H.dur * 1000 });
    },

    // homing missiles: a salvo out of the back rack, split over the two best targets ahead of you
    rigMissiles(p, m, n) {
      const R = p.rig, d = norm(vec3(m.d));
      if (!d || n - R.missT < M.cd * 1000 - 300) return;
      R.missT = n;
      const tg = this.rigTargets(p, head(p), d, M.cos, M.seek).slice(0, 2);
      this.broadcast({ t: 'rig', k: 'miss', id: p.id, tg: tg.map((t) => t.id) });
      for (let i = 0; i < M.n; i++) {
        setTimeout(safe('rigmiss', () => {
          if (this.players.get(p.id) !== p || !this.rigOn(p)) return; // the rack went down with its rig
          const s = Math.sin(p.yaw), c = Math.cos(p.yaw), side = i % 2 ? 1 : -1, row = i >> 1;
          const fw = [-s, -c], rt = [c, -s];
          const pos = [p.pos[0] + rt[0] * side * 0.72 - fw[0] * 0.5, p.pos[1] + 3.1 + row * 0.22, p.pos[2] + rt[1] * side * 0.72 - fw[1] * 0.5];
          const out = 3.5 + Math.random() * 2, upv = 13 + Math.random() * 3;
          const vel = [rt[0] * side * out + fw[0] * 3 + p.vel[0] * 0.4, upv, rt[1] * side * out + fw[1] * 3 + p.vel[2] * 0.4];
          const pr = this.makeProj(p, 'rigmissile', pos, vel, { tg: tg.length ? tg[i % tg.length].id : 0, aim: d, seekT: 0 });
          pr.born = now();
        }), i * M.gap);
      }
    },
    // enemies ahead of `from` (within the cone around d and range), in plain sight, best first (near the middle, close)
    rigTargets(p, from, d, cos, range) {
      const out = [];
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t)) continue;
        const tc = center(t), v = [tc[0] - from[0], tc[1] - from[1], tc[2] - from[2]], l = Math.hypot(v[0], v[1], v[2]);
        if (l > range || l < 1) continue;
        const dot = (v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / l;
        if (dot < cos || raycast(from, [v[0] / l, v[1] / l, v[2] / l], l - 0.5, this.boxes)) continue;
        out.push({ t, s: (1 - dot) * 60 + l * 0.35 });
      }
      return out.sort((a, b) => a.s - b.s).map((e) => e.t);
    },
    // one missile, every tick (tickProjectiles hands them over): straight up out of the pod, then it homes in
    rigMissileStep(pr, dt) {
      const n = now(), owner = this.players.get(pr.o), age = (n - pr.born) / 1000, v = pr.v;
      if (!owner) { this.removeProj(pr); return; }
      if (age > M.boost) {
        let t = pr.tg ? this.players.get(pr.tg) : null;
        if (t && (!t.alive || this.friendly(owner, t))) t = null;
        if (!t && n >= pr.seekT) { // lost its target (or never had one): look again ahead of where it's flying
          pr.seekT = n + 200;
          const sp = Math.hypot(v[0], v[1], v[2]) || 1;
          t = this.rigTargets(owner, pr.p, [v[0] / sp, v[1] / sp, v[2] / sp], 0.55, 45)[0] || null;
        }
        pr.tg = t ? t.id : 0;
        let dir = norm(v) || [0, 1, 0], sp = lerpK(M.speed, (age - M.boost) / 0.7);
        if (t) {
          const tc = center(t), dist = Math.hypot(tc[0] - pr.p[0], tc[1] - pr.p[1], tc[2] - pr.p[2]);
          if (dist < 1.4) { this.rigBoom(pr, owner, t); return; } // proximity fuse
          // close in, it slows and turns harder (or it would orbit someone standing right in front of you)
          const close = Math.max(0, Math.min(1, 1 - dist / 18)), lead = Math.min(0.5, dist / sp);
          sp *= 1 - close * 0.45;
          const aim = norm([tc[0] + t.vel[0] * lead - pr.p[0], tc[1] + t.vel[1] * lead * 0.4 - pr.p[1], tc[2] + t.vel[2] * lead - pr.p[2]]);
          if (aim) dir = turnToward(dir, aim, M.turn * (1 + close * 2.5) * dt);
        } else if (pr.aim && age < M.boost + 0.8) dir = turnToward(dir, pr.aim, M.turn * 0.8 * dt); // dumb fire: arc over where you aimed
        v[0] = dir[0] * sp; v[1] = dir[1] * sp; v[2] = dir[2] * sp;
      } else { v[0] *= 1 - dt * 1.5; v[2] *= 1 - dt * 1.5; }
      const prev = pr.p.slice();
      const wall = stepProjectile(pr, dt, this.boxes, 0);
      const hit = this.sweep(prev, pr.p, pr.r + 0.1, (t) => t.id === pr.o || this.friendly(owner, t));
      if (hit.length) { pr.p = hit[0].at; this.rigBoom(pr, owner, hit[0].t); return; }
      if (wall || age > M.life || pr.p[1] < this.map.killY) { this.rigBoom(pr, owner, null); return; }
      pr.sync -= dt;
      if (pr.sync <= 0) { pr.sync = 0.06; this.broadcast({ t: 'pu', id: pr.id, p: pr.p.map(r2), v: v.map(r2) }); }
    },
    rigBoom(pr, owner, direct) {
      this.removeProj(pr);
      this.broadcast({ t: 'rig', k: 'boom', id: pr.o, p: pr.p.map(r2) });
      for (const t of this.players.values()) {
        if (!t.alive || t === owner || this.friendly(owner, t)) continue;
        const c = center(t), to = [c[0] - pr.p[0], c[1] - pr.p[1], c[2] - pr.p[2]];
        let d = Math.hypot(to[0], to[1], to[2]);
        if (t === direct) d = 0;
        else if (d > M.r || (d > 0.4 && raycast(pr.p, [to[0] / d, to[1] / d, to[2] / d], d - 0.3, this.boxes))) continue;
        const f = 1 - d / M.r, dir = d > 0.1 ? to.map((x) => x / d) : norm(pr.v) || [0, 1, 0], k = M.kb * (0.5 + 0.5 * f);
        this.hurt(t, owner, 'rigmissile', M.dmg * (0.35 + 0.65 * f), [dir[0] * k, dir[1] * k * 0.5 + 5 * f, dir[2] * k], { from: pr.p });
      }
    },

    // charged leap: the client jumps (movement is its own); the server notes how charged it really was, then the
    // landing (rigLand) has to come from that leap, near where the server has the rig, onto a real floor
    rigLeap(p, m, n) {
      const R = p.rig;
      if (n - R.leapT < L.cd * 1000 - 150) return;
      const c = Math.max(0, Math.min(1, num(m.c) || 0, this.rigHeld(R.lp, n) / (L.charge * 1000)));
      R.leapT = n;
      R.leap = { t: n, c, top: p.pos[1], landed: false };
      this.broadcast({ t: 'rig', k: 'leap', id: p.id, c: r2(c) }, p.id);
    },
    rigLand(p, m, n) {
      const R = p.rig, Lp = R.leap;
      if (!Lp || Lp.landed || n - Lp.t < 200 || n - Lp.t > 6000) return;
      let at = vec3(m.p);
      if (!at || Math.hypot(at[0] - p.pos[0], at[2] - p.pos[2]) > 4 + Math.hypot(p.vel[0], p.vel[2]) * 0.15 || Math.abs(at[1] - p.pos[1]) > 4) at = p.pos.slice();
      const fl = raycast([at[0], at[1] + 0.6, at[2]], [0, -1, 0], 3, this.boxes);
      if (!fl || Lp.top - fl.point[1] < 0.6) return; // it has to come down onto something, from up there
      Lp.landed = true;
      const r = lerpK(L.r, Lp.c), c = [at[0], fl.point[1] + 0.3, at[2]];
      this.broadcast({ t: 'rig', k: 'land', id: p.id, p: [r2(at[0]), r2(fl.point[1]), r2(at[2])], r: r2(r), c: r2(Lp.c) });
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t)) continue;
        const tc = center(t), to = [tc[0] - c[0], tc[1] - c[1], tc[2] - c[2]], d = Math.hypot(to[0], to[1], to[2]);
        if (d > r || !clear(c, tc, this.boxes)) continue; // a shockwave: not through walls or floors
        const f = 1 - d / r, hl = Math.hypot(to[0], to[2]), out = hl > 0.2 ? [to[0] / hl, to[2] / hl] : [0, 0], k = L.kb * (0.4 + 0.6 * f);
        this.hurt(t, p, 'rigquake', L.dmg * (0.35 + 0.65 * f), [out[0] * k, 7 + 6 * f, out[1] * k]);
      }
    },

    // ------------------------------------------------------------ every tick
    tickRig() {
      const n = now();
      for (const p of this.players.values()) {
        const R = p.rig;
        if (R && (!(R.until > n) || !p.alive)) this.rigEnd(p); // ran out
        else if (R) {
          if (R.dash) this.rigDash(p, n);
          if (R.sq && n - R.sqT >= 70) this.rigFlush(p);
        }
        if (p.rigSlam) this.rigWall(p, n);
      }
    },
  });
}
