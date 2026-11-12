// Overdrive Rig killstreak, the server side. Movement is the client's, but everything that hurts or helps is judged here:
// the overshield and the block (in Room.damage), the rocket punch (from the server's own positions along the dash), wall
// slams, quickhacks (range, line of sight, cooldown), the homing missiles (server projectiles) and leap landings.
// installRig(Room, helpers) adds these methods to Room; server.js calls them from one-line hooks.
import { FLAGS, STREAKS } from '../shared/weapons.js';
import { BODY } from '../shared/bodyhp.js';
import { RIG, RIG_BITS, punchDmg, punchDist, dashDir, leapVel, lerpK, inFront, thrustVel, useThrust } from '../shared/rig.js';
import { raycast, stepProjectile, movePlayer } from '../shared/physics.js';

const P = RIG.punch, M = RIG.miss, L = RIG.leap, H = RIG.hack;
const look = (p) => { const c = Math.cos(p.pitch || 0); return [-Math.sin(p.yaw) * c, Math.sin(p.pitch || 0), -Math.cos(p.yaw) * c]; };
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
  const { now, num, vec3, norm, r2, center, safe, REC_T, WEAPONS } = U;
  const WEAPONS_kind = (t) => (WEAPONS[t.w] || {}).kind;
  REC_T.add('rig'); // punches, hacks, missiles and landings show up in the play of the round

  Object.assign(Room.prototype, {
    rigOn(p, n = now()) { return !!(p && p.alive && p.rig && p.rig.until > n); },
    rigShrug(v) { return v.map((x) => x * RIG.kbTake); }, // knockback on a rig: mostly ignored

    // ------------------------------------------------------------ on / off
    rigStart(p) {
      const n = now(), dur = (STREAKS.overdrive.dur || RIG.dur) * 1000;
      // it lasts until its armour breaks (server/bodyhp.js): dur is only a safety net, +1 s for a client that never says
      p.rig = {
        until: n + dur + 1000, shield: BODY.overdrive.hp, store: 0, punchT: 0, hackT: 0, missT: 0, leapT: 0,
        ch: { t0: 0, t1: 0 }, lp: { t0: 0, t1: 0 }, dash: null, leap: null, sq: null, sqT: 0, thr: { n: RIG.thrust.n, next: 0, t: 0 },
      };
      p.g = null; p.hackedUntil = 0;
      this.broadcast({ t: 'rig', k: 'on', id: p.id, dur, sh: BODY.overdrive.hp });
      this.bodyStart(p, 'overdrive');
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
      // then the armour takes everything (bodySoak: no HP lost; at 0 the rig breaks). the floor / zone still hurt you
      const before = amt;
      amt = this.bodySoak(t, amt, attacker, w);
      const sh = before - amt;
      R.shield = t.body ? Math.max(0, t.body.hp) : 0;
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
      else if (m.k === 'thrust') this.rigThrust(p, n);
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
      const M = pr.M || RIG.miss; // (the mech's swarm brings its own numbers)
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
      const M = pr.M || RIG.miss;
      this.removeProj(pr);
      this.broadcast({ t: 'rig', k: 'boom', id: pr.o, p: pr.p.map(r2) });
      for (const t of this.players.values()) {
        if (!t.alive || t === owner || this.friendly(owner, t)) continue;
        const c = center(t), to = [c[0] - pr.p[0], c[1] - pr.p[1], c[2] - pr.p[2]];
        let d = Math.hypot(to[0], to[1], to[2]);
        if (t === direct) d = 0;
        else if (d > M.r || (d > 0.4 && raycast(pr.p, [to[0] / d, to[1] / d, to[2] / d], d - 0.3, this.boxes))) continue;
        const f = 1 - d / M.r, dir = d > 0.1 ? to.map((x) => x / d) : norm(pr.v) || [0, 1, 0], k = M.kb * (0.5 + 0.5 * f);
        this.hurt(t, owner, pr.k, M.dmg * (0.35 + 0.65 * f), [dir[0] * k, dir[1] * k * 0.5 + 5 * f, dir[2] * k], { from: pr.p });
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

    // thrusters: the server counts the charges (3, one back every 2.6 s, a beat between bursts), so a client can't
    // spam them: a burst it doesn't believe isn't shown to anyone. a thrust also lets a leap's landing count from the
    // new top (rigSnap keeps tracking it)
    rigThrust(p, n) {
      const R = p.rig;
      if (!useThrust(R.thr, n)) return false;
      this.broadcast({ t: 'rig', k: 'thrust', id: p.id, n: R.thr.n }); // (the thruster's own client syncs its charges from n)
      return true;
    },

    // ------------------------------------------------------------ bots
    // a bot that gets the streak suits up a beat later (bots have no tray: they use it right away)
    rigBotEarn(b) {
      if (b.rig || this.isBall(b)) return;
      setTimeout(safe('botrig', () => {
        if (this.players.get(b.id) !== b || !b.alive || b.rig || this.isBall(b) || (this.round && this.round.over)) return;
        this.rigStart(b); // (every client says who's in it from the 'on' event)
      }), 700);
    },
    // a bot in the rig: its own heavy movement (like a player's in public/js/rig.js), and a little plan. up close it
    // charges a punch sized to the gap and throws it; further out it walks in behind its block and fires missiles; it
    // fries the rope of anyone grappling; it leaps at far targets. every hit goes through the same checks as a player's
    rigBotStep(b, think, dt, n) {
      const R = b.rig, v = b.vel, ai = b.ai, D = RIG, B = R.bai || (R.bai = { mode: '', t0: 0, c: 0, lost: 0, blockT: 0 });
      b.g = null; ai.hook = null;
      let t = this.players.get(ai.target);
      if (t && (!t.alive || this.friendly(b, t))) t = null;
      const e = head(b), tc = t ? center(t) : null, dv = t ? [tc[0] - e[0], tc[1] - e[1], tc[2] - e[2]] : null;
      const dist = t ? Math.hypot(dv[0], dv[1], dv[2]) : 1e9, vis = !!(t && ai.seenAt);
      let ang = t ? Math.abs(Math.atan2(-dv[0], -dv[2]) - b.yaw) % (Math.PI * 2) : 9;
      if (ang > Math.PI) ang = Math.PI * 2 - ang;
      if (vis) B.lost = n;
      // ---- decisions
      if (B.mode === 'charge') {
        R.ch.t1 = n;
        const held = (n - B.t0) / (P.charge * 1000);
        if (n - B.lost > 900) B.mode = ''; // lost them: put it down
        else if (held >= B.c || (vis && dist < 3.4 && held > 0.12)) { this.rigPunch(b, { c: Math.min(1, held), d: look(b) }, n); B.mode = ''; if (R.dash) R.bdash = { dir: R.dash.dir, until: n + (R.dash.dist / P.speed) * 1000 }; }
      } else if (B.mode === 'leap') {
        R.lp.t1 = n;
        const k = (n - B.t0) / (L.charge * 1000);
        if (!b.onGround) B.mode = '';
        else if (k >= B.c) {
          const d = t ? [dv[0], Math.max(0.15, dv[1] / (dist || 1)), dv[2]] : look(b), lv = leapVel(Math.min(1, k), d);
          v[0] = lv[0]; v[1] = lv[1]; v[2] = lv[2]; b.onGround = false; b.pos[1] += 0.02;
          this.rigLeap(b, { c: Math.min(1, k) }, n);
          R.botLeap = true; B.mode = '';
        }
      } else if (!R.bdash) {
        const easy = ai.diff === 'easy' ? 0.5 : 1;
        if (vis && dist < 15 && ang < 0.35 && n - R.punchT > P.cd * 1000 + 250) { // wind up a punch sized to the gap (blocking stored some already)
          B.mode = 'charge'; B.t0 = n - R.store * P.charge * 1000; B.c = Math.max(0.15, Math.min(1, (dist - 3) / 11 + Math.random() * 0.15)); R.ch.t0 = n; R.ch.t1 = n;
        } else if (vis && dist < H.range && n - R.hackT > H.cd * 1000 && ang < 0.5 && (t.g || (dist > 12 && Math.random() < dt * 0.12))) this.rigHack(b, { to: t.id }, n); // grappling? not any more (and now and then, so they can't)
        else if (vis && dist > 12 && dist < M.seek && n - R.missT > M.cd * 1000 && Math.random() < dt * 2 * easy) this.rigMissiles(b, { d: look(b) }, n);
        else if (b.onGround && t && dist > 20 && n - R.leapT > 2500 && Math.random() < dt * 0.9 * easy) { B.mode = 'leap'; B.t0 = n; B.c = 0.6 + Math.random() * 0.4; R.lp.t0 = n; R.lp.t1 = n; }
      }
      // walking in on someone with a gun: guard up (it soaks their shots and charges the next punch)
      const block = B.mode === '' && !R.bdash && vis && dist > 14 && dist < 60 && (WEAPONS_kind(t) !== 'melee');
      // ---- movement
      if (R.bdash) {
        const d = R.bdash.dir;
        if (n < R.bdash.until) { v[0] = d[0] * P.speed; v[1] = d[1] * P.speed; v[2] = d[2] * P.speed; }
        else { R.bdash = null; v[0] *= 0.28; v[2] *= 0.28; v[1] = Math.min(v[1], 2); }
      } else {
        const wl = Math.hypot(think.wx, think.wz), wx = wl ? think.wx / wl : 0, wz = wl ? think.wz / wl : 0;
        let top = D.speed * Math.min(1, wl) * (block ? D.block.slow : 1) * (B.mode === 'charge' ? 0.75 : 1) * (B.mode === 'leap' ? 0.3 : 1);
        if (b.onGround) {
          const hs = Math.hypot(v[0], v[2]);
          if (hs > 0) { const ns = Math.max(0, hs - Math.max(hs, 3) * D.fric * (wl ? 0.45 : 1) * dt) / hs; v[0] *= ns; v[2] *= ns; }
          if (wl) { const cur = v[0] * wx + v[2] * wz, add = top - cur; if (add > 0) { const a = Math.min(add, D.accel * top * dt); v[0] += a * wx; v[2] += a * wz; } }
          // the hop goes ~6 m up: for getting up to someone (or now and then, for the show), not every step
          const up = t && dv[1] > 2.5 && dist < 30;
          if (B.mode === '' && (up ? Math.random() < dt * 3 : think.jump && Math.random() < 0.06)) { v[1] = D.hop; b.onGround = false; }
        } else if (wl) { const cur = v[0] * wx + v[2] * wz, add = D.airCap - cur; if (add > 0) { const a = Math.min(add, D.airAccel * dt); v[0] += a * wx; v[2] += a * wz; } }
      }
      // thrusters: climb to someone above, dodge when shot, chase someone far off, and never fall into the void
      if (!b.onGround && !R.bdash && B.mode === '') {
        const below = !raycast([b.pos[0], b.pos[1] + 0.5, b.pos[2]], [0, -1, 0], 40, this.boxes);
        const hitNow = R.sqT && n - R.sqT < 250;
        const want = below && v[1] < 0 ? 'save' : t && dv[1] > 1.5 && v[1] < 3 ? 'up' : hitNow && Math.random() < 0.4 ? 'dodge' : t && dist > 25 && v[1] < 0 && Math.random() < dt * 2 ? 'chase' : '';
        if (want && this.rigThrust(b, n)) {
          let d = look(b);
          if (want === 'save') { const c = this.map.spawns ? this.map.spawns[0] : [0, 0, 0]; d = [c[0] - b.pos[0], 0, c[2] - b.pos[2]]; }
          else if (want === 'dodge') { const s = Math.random() < 0.5 ? 1 : -1; d = [Math.cos(b.yaw) * s, 0, -Math.sin(b.yaw) * s]; }
          thrustVel(v, d);
        }
      }
      if (!R.bdash) v[1] -= D.grav * dt * 0.5; // (half before the move, half after, like the client)
      const was = b.onGround;
      const res = movePlayer(b.pos, v, dt, this.boxes, was);
      if (!R.bdash && !res.ground) v[1] -= D.grav * dt * 0.5;
      b.onGround = !!res.ground && v[1] <= 0.01;
      if (res.wall && R.bdash) { R.bdash = null; v[0] *= 0.28; v[2] *= 0.28; }
      if (b.onGround && res.ground.pad) { const pd = res.ground.pad; v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2]; b.onGround = false; }
      if (R.leap && !R.leap.landed) R.leap.top = Math.max(R.leap.top, b.pos[1]);
      if (b.onGround && !was && R.botLeap) { R.botLeap = false; this.rigLand(b, { p: b.pos.slice() }, n); }
      if (b.onGround) b.ground = b.pos.slice();
      b.f = FLAGS.RIG | (block ? FLAGS.RIG_BLOCK : 0) | (B.mode === 'charge' ? FLAGS.RIG_CHARGE : 0) | (B.mode === 'leap' ? FLAGS.RIG_LEAP : 0);
      if (block) R.blockT = n;
      if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
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
