// TROLLEY, the battle island speed hero (docs/mechs/ROSTER.md; numbers: MECH.trolley in shared/mech.js). Movement is
// the client's, like every mech; the server judges what it does: rams by the speed it measures, the drift's RAM CHARGE
// only while it measures you going fast (and by its own clock), the push from that charge, tin cans as its own bouncing
// projectiles, CLEAN UP AISLE 5 (a full ult) scooping enemies into the basket, where they go where the trolley goes until
// the dump, and allies riding in the child seat (the pound coin lock). installTrolley hooks it into server/mech.js (KIT).
// Its state lives on the pilot's p.mech.tr; everyone it carries has t.mheld (server/mech.js lets go on every cleanup).
import { FLAGS, WEAPONS } from '../shared/weapons.js';
import { MECH, MF, trSpot, trPush, trRam, trDrive } from '../shared/mech.js';
import { raycast, playerOverlap } from '../shared/physics.js';
import { outOfBounds } from '../shared/bounds.js';
import { stepBall } from '../shared/primaries.js';

const TR = MECH.trolley;
const COAST = 16; // m/s per s the speed cap comes back down after a push / AISLE 5 (the client's own drag over top speed)

export function installTrolley(Room, U) {
  const { now, norm, r2, center, send, KIT, clear, segDist, hdist } = U;
  const fwdOf = (p) => [-Math.sin(p.yaw), -Math.cos(p.yaw)];
  // how fast it's really going: measured from the snapshots (players), its own (bots)
  // (mechMv: the net travel backs it, so wiggling in place reads as parked)
  const speedOf = (room, p, M, n) => room.mechMv(p, M, n);
  // what it hits / drifts / scoops with: the measured speed, never more than it may go right now (the kit's cap) nor a jump
  // from the window before (a trolley that sat still then "moved" 10 m in one snapshot counts as sitting still). the way
  // it's going is a unit vector off the raw velocity, so nothing can scale the knockback up
  const moveOf = (room, p, M, n) => {
    const v = speedOf(room, p, M, n), T = M.tr, raw = Math.hypot(v[0], v[1]);
    if (!p.isBot && M.mv !== T.mvRef) { T.mvRef = M.mv; T.hsPrev = T.hsNow || 0; T.hsNow = M.mv ? Math.hypot(M.mv[0], M.mv[1]) : 0; }
    const hs = Math.min(raw, KIT.trolley.cap.call(room, p, M, p.f, n), p.isBot ? 1e9 : (T.hsPrev || 0) + 12);
    return { hs, fx: raw > 1e-6 ? v[0] / raw : 0, fz: raw > 1e-6 ? v[1] / raw : 0 };
  };
  // the measured velocity, clamped the same way (cans and the dump fling ride on it)
  const velOf = (room, p, M, n) => { const m = moveOf(room, p, M, n); return [m.fx * m.hs, m.fz * m.hs]; };
  const chargeOf = (T, n) => (n - T.chT <= TR.drift.keep * 1000 ? T.ch : 0);

  KIT.trolley = {
    enter(p, M) { M.tr = { ch: 0, chT: 0, aisle: null, held: [], rider: 0, riderUntil: 0, coast: null, canT: 0, holdT: 0, offerT: 0 }; },
    exit(p, M, why) { if (M.tr) { this.trLetGoAll(p, M, why === 'boom' ? 'break' : 'quiet'); M.tr.aisle = null; } },
    // the flags it's allowed: A drifting (only while the server measures real speed: that's what builds the charge),
    // B in AISLE 5, C in the push
    flags(p, M, want, n, dt) {
      const T = M.tr;
      let f = 0;
      if ((want & MF.DRIFT) && moveOf(this, p, M, n).hs >= TR.drift.min) {
        f |= MF.DRIFT;
        T.ch = Math.min(1, chargeOf(T, n) + (dt || 0) / TR.drift.build); T.chT = n;
      }
      if (T.aisle) f |= MF.AISLE;
      if (M.dash && n < M.dash.until) f |= MF.PUSH;
      return f;
    },
    // the flat speed it may go right now: top speed, AISLE 5's, the push's, or what's left of the last burst
    cap(p, M, f, n) {
      const T = M.tr;
      let c = T.aisle ? TR.aisle.speed : TR.speed;
      if (M.dash && n < M.dash.until) c = Math.max(c, M.dash.v);
      if (T.coast) c = Math.max(c, T.coast.v - COAST * Math.max(0, n - T.coast.t) / 1000);
      return c;
    },
    msg(p, M, m, n, d) {
      switch (m.k) {
        case 'can': if (d) this.trCan(p, d, n); break;
        case 'push': this.trPushGo(p, n); break;
        case 'aisle': if (m.on === 1) this.trAisle(p, n); else if (m.on === 0) this.trDump(p, 'q'); break;
      }
    },
    tick(p, M, n, dt) {
      const T = M.tr;
      if (T.ch && n - T.chT > TR.drift.keep * 1000) T.ch = 0;
      if (T.coast && T.coast.v - COAST * Math.max(0, n - T.coast.t) / 1000 < TR.speed) T.coast = null;
      if (T.aisle && n >= T.aisle.until) this.trDump(p, 'time');
      if (M.dash) this.trPushSweep(p, M, n);
      if (!M.dash && !T.aisle && !T.coast && T.boost) { T.boost = false; M.bank = Math.min(M.bank, MECH.slack + TR.speed * 1.12 * 0.35); } // (the push's / AISLE 5's extra bank goes with them)
      else if (T.aisle && this.trScoop(p, M, n)) this.trRamTick(p, M, n, true); // (room in the basket: only what won't fit in it gets rammed)
      else this.trRamTick(p, M, n);
      this.trCarry(p, M, n, dt);
      this.trRiders(p, M, n);
    },
    bot(b, think, dt, n) { this.trBot(b, think, dt, n); },
    en(p, M, n) { const T = M.tr; return { ch: r2(chargeOf(T, n)), au: T.aisle ? Math.round(T.aisle.until - n) : 0, bk: T.held.length }; },
    // carrying people (server/mech.js): still got them? where do they go? let them go
    holds(c, M, t) { const T = M.tr; return !!T && (T.rider === t.id || T.held.some((h) => h.id === t.id)); },
    heldAt(c, M, t) {
      const T = M.tr, h = t.mheld && t.mheld.k === 'scoop' ? T.held.find((x) => x.id === t.id) : null;
      return trSpot(c.pos, c.yaw, h ? TR.scoop[h.i] : TR.seat);
    },
    unhold(c, M, t, why) { this.trRelease(c, t, why === 'dead' ? 'dead' : 'quiet'); },
    // the pound coin lock (server/mech.js mechPoke): 'ride' climbs an ally into the child seat, 'unride' hops them out
    poke(p, c, M, k, n) {
      const T = M.tr;
      if (k === 'unride') { if (T.rider === p.id) this.trRelease(c, p, 'hop'); return; } // (scooped: no getting out)
      if (k !== 'ride') return;
      if (!this.friendly(c, p)) { this.mechNo(p, "that's not your trolley"); return; }
      this.trRideStart(c, p, n);
    },
    // tin cans (tickProjectiles -> mechProjStep): bounce off things a few times, bonk the first enemy they touch
    proj(pr, dt, n) { this.trCanStep(pr, dt, n); },
  };

  Object.assign(Room.prototype, {
    trOn(p) { return this.mechOn(p) && p.mech.f === 'trolley' && !!p.mech.tr; },
    trHolding(p, t) { const T = p.mech && p.mech.tr; return !!(T && (T.rider === t.id || T.held.some((h) => h.id === t.id))); },

    // ---- tin-can toss (LMB): a lobbed can from the handle, 3 a second. the server throws it along your aim
    trCan(p, d, n) {
      const M = p.mech, T = M.tr, C = TR.can;
      if (n - T.canT < 1000 / C.rate * 0.75 || !this.mechAimOk(p, d, C.cone)) return null;
      T.canT = n;
      let o = trSpot(p.pos, p.yaw, TR.muzzle);
      const e = this.mechEyeOf(p);
      if (!clear(e, o, this.boxes) || raycast(o, d, 0.4, this.boxes)) o = e; // (backed into a wall: from the cockpit)
      const mv = velOf(this, p, M, n);
      const vel = [d[0] * C.speed + mv[0] * 0.5, d[1] * C.speed + C.up, d[2] * C.speed + mv[1] * 0.5];
      const pr = this.makeProj(p, 'trcan', o, vel, { b: 0, born: n, r: TR.can.r }); // (r: the can grows with the mechs)
      this.broadcast({ t: 'mech', k: 'trtoss', id: p.id }, p.isBot ? undefined : p.id);
      return pr;
    },
    trCanStep(pr, dt, n) {
      const owner = this.players.get(pr.o), C = TR.can, prev = pr.p.slice();
      if (!owner) { this.removeProj(pr); return; }
      const st = stepBall(pr, dt, this.boxes, WEAPONS.trcan.grav, C.minB, C.e);
      if (this.parryProj(pr, prev)) return; // batted back by a katana parry
      const x = this.vmFirst ? this.vmFirst(owner, prev, pr.p) : null;
      if (x) { // an enemy OUT OF ORDER sign: BONK off its face and back the way it came (that counts as a bounce)
        const Wl = x.wall, fx = -Math.sin(Wl.yaw), fz = -Math.cos(Wl.yaw), vn = pr.v[0] * fx + pr.v[2] * fz, sg = vn > 0 ? 1 : -1;
        pr.v[0] -= (1 + C.e) * vn * fx; pr.v[2] -= (1 + C.e) * vn * fz;
        pr.p = [x.at[0] - sg * fx * (pr.r + 0.05), x.at[1], x.at[2] - sg * fz * (pr.r + 0.05)];
        if (!pr.wallHit) { pr.wallHit = 1; this.vmWallHurt(Wl, C.dmg, x.at, owner); this.broadcast({ t: 'mech', k: 'trbonk', id: pr.o, to: 0, p: x.at.map(r2) }); }
        st.n = (st.n || 0) + 1;
      }
      if (this.mechProjHit && this.mechProjHit(pr, prev, owner)) return; // an empty parked enemy mech: it takes the can
      const age = (n - pr.born) / 1000;
      const vs = this.sweep(prev, pr.p, pr.r, (t) => t.id === pr.o || (this.friendly(owner, t) && !t.trap) || (pr.o === owner.id && this.trHolding(owner, t)));
      if (vs.length) {
        const v = vs[0], d = norm([pr.v[0], 0, pr.v[2]]) || [0, 0, -1];
        pr.p = v.at;
        this.removeProj(pr, { b: 1 });
        this.broadcast({ t: 'mech', k: 'trbonk', id: pr.o, to: v.t.id, p: v.at.map(r2) });
        this.mechKitHurt(owner, v.t, 'trcan', C.dmg, [d[0] * C.kb, C.kbUp, d[2] * C.kb]);
        return;
      }
      if (st.n) {
        pr.b += st.n;
        if (pr.b > C.bounces) { this.removeProj(pr); return; } // that was its last bounce
        this.broadcast({ t: 'pu', id: pr.id, p: pr.p.map(r2), v: pr.v.map(r2), b: pr.b });
      }
      if (age > C.life || pr.p[1] < this.map.killY || (Math.hypot(pr.v[0], pr.v[1], pr.v[2]) < 0.6 && age > 0.6)) this.removeProj(pr);
    },

    // ---- TROLLEY PUSH (E): a lunge forward. its speed and hit come from the ram charge the server built, and spend it
    trPushGo(p, n) {
      const M = p.mech, T = M.tr, P = TR.push;
      if (M.dash && n < M.dash.until) return null;
      if (!this.mechCd(M, 'push', P.cd, n)) return null;
      const c = chargeOf(T, n), h = trPush(c);
      T.ch = 0;
      M.dash = { k: 'push', t0: n, until: n + P.len * 1000 + 150, v: h.v, h, dir: fwdOf(p), prev: p.pos.slice(), hit: new Set() };
      T.coast = { v: h.v, t: n + P.len * 1000 };
      M.bank += 3; T.boost = true;
      this.broadcast({ t: 'mech', k: 'trpush', id: p.id, c: r2(c), v: r2(h.v) });
      this.mechEn(p, true);
      return h;
    },
    // the push hits everyone on the bumper's path (the path the server has it on), once each
    trPushSweep(p, M, n) {
      const D = M.dash;
      if (n > D.until) { M.dash = null; return; }
      const f = D.dir, R = TR.hw + 0.3, h = D.h;
      const y = TR.h * 0.42, a = [D.prev[0] + f[0] * R, D.prev[1] + y, D.prev[2] + f[1] * R], b = [p.pos[0] + f[0] * R, p.pos[1] + y, p.pos[2] + f[1] * R]; // (the bumper's height)
      D.prev = p.pos.slice();
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t) || D.hit.has(t.id) || this.trHolding(p, t)) continue;
        const tc = this.mechCenter(t);
        if (segDist(a, b, tc) > TR.push.r + (this.mechOn(t) ? MECH[t.mech.f].hw : 0.6) || !clear(this.mechCenter(p), tc, this.boxes)) continue;
        D.hit.add(t.id);
        this.broadcast({ t: 'mech', k: 'trhit', id: p.id, to: t.id, p: tc.map(r2), big: h.k >= 0.6 ? 1 : 0 });
        this.mechKitHurt(p, t, 'trpush', h.dmg, [f[0] * h.kb, h.up, f[1] * h.kb]);
      }
      this.trEmpties(p, a, b, TR.push.r, D.hit, 'trpush', h.dmg); // (an empty parked enemy mech on the path gets it too)
    },
    // an empty parked enemy mech the trolley's path a-b comes within r of: hit once per `hit` set (push / ram)
    trEmpties(p, a, b, r, hit, w, dmg) {
      if (!this.mechEmpties) return;
      for (const m of this.mechEmpties()) {
        if (hit.has('m' + m.id) || !this.mechCanHit(m, p)) continue;
        const q = this.mechNear(m, b);
        if (segDist(a, b, q) > r || !this.mechSeen(m, this.mechCenter(p))) continue;
        hit.add('m' + m.id);
        this.mechHarm(m, p, w, dmg, false, q);
        this.broadcast({ t: 'mech', k: 'trhit', id: p.id, to: 0, p: q.map(r2), big: dmg >= 60 ? 1 : 0 });
      }
    },
    // ---- ram: driving into people at speed (what the server measured)
    // too big (or busy) for the basket: a mech, a rig, a ball, a bubble, anyone on a lasso
    trBig(t) { return !!(t.mech || (t.br && (t.br.inBlimp || t.br.fly)) || t.trap || (t.rig && this.rigOn(t)) || this.isBall(t) || (t.lz && (t.lz.by || t.lz.hold))); },
    trRamTick(p, M, n, big) {
      const { hs, fx, fz } = moveOf(this, p, M, n), h = trRam(hs), R = TR.ram;
      if (!h) return;
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t) || this.trHolding(p, t) || n < (M.ramT.get(t.id) || 0) || (big && !this.trBig(t))) continue;
        const dx = t.pos[0] - p.pos[0], dz = t.pos[2] - p.pos[2], l = Math.hypot(dx, dz), dy = t.pos[1] - p.pos[1];
        if (l > TR.hw + 0.5 + (this.mechOn(t) ? MECH[t.mech.f].hw : 0.45) || dy < -1.8 || dy > TR.h || (l > 0.3 && (dx * fx + dz * fz) / l < 0.2)) continue;
        if (!clear(this.mechCenter(p), this.mechCenter(t), this.boxes)) continue;
        M.ramT.set(t.id, n + R.cd * 1000);
        this.broadcast({ t: 'mech', k: 'ram', id: p.id, to: t.id, p: this.mechCenter(t).map(r2), big: h.dmg >= 28 ? 1 : 0, w: 'trram' });
        this.mechKitHurt(p, t, 'trram', h.dmg, [fx * h.kb, h.up, fz * h.kb], M.tr.aisle ? { ult: 1 } : undefined); // (AISLE 5's rams don't charge the next one)
      }
      // empty parked enemy mechs it drives into (once per ram cooldown each)
      const rh = M.trRamM || (M.trRamM = new Map()), seen = new Set([...rh].filter(([, u]) => n < u).map(([k]) => k)), b0 = [p.pos[0], p.pos[1] + TR.h * 0.42, p.pos[2]];
      this.trEmpties(p, b0, [b0[0] + fx * (TR.hw + 0.3), b0[1], b0[2] + fz * (TR.hw + 0.3)], 0.4, seen, 'trram', h.dmg);
      for (const k of seen) if (!rh.has(k) || n >= rh.get(k)) rh.set(k, n + R.cd * 1000);
    },

    // ---- CLEAN UP AISLE 5 (Q, a full ult): top speed for 6 s; enemies it runs into go in the basket. Q again (or the
    // time running out) dumps them: the basket tips and they fly
    trAisle(p, n) {
      const M = p.mech, T = M.tr, A = TR.aisle;
      if (T.aisle) return false;
      if ((M.ult || 0) < 100) { this.mechNo(p, 'ultimate not ready'); return false; }
      M.ult = 0;
      T.aisle = { t0: n, until: n + A.dur * 1000 };
      M.bank += 4; T.boost = true;
      this.broadcast({ t: 'mech', k: 'traisle', id: p.id, on: 1, ms: A.dur * 1000 });
      this.mechEn(p, true);
      return true;
    },
    trDump(p, why) {
      const M = p.mech, T = M && M.tr;
      if (!T || !T.aisle) return;
      T.aisle = null;
      T.coast = { v: TR.aisle.speed, t: now() };
      const out = T.held.slice();
      this.broadcast({ t: 'mech', k: 'traisle', id: p.id, on: 0, n: out.length, why });
      for (const h of out) { const t = this.players.get(h.id); if (t) this.trRelease(p, t, 'dump'); }
      this.mechEn(p, true);
    },
    // anyone it runs into (in front of the basket, it moving): scooped, up to max. true = room left (only the big ones get
    // rammed), false = full (it rams everyone)
    trScoop(p, M, n) {
      const T = M.tr, A = TR.aisle;
      if (T.held.length >= A.max) return false;
      if (moveOf(this, p, M, n).hs < A.min) return true;
      const f = fwdOf(p), front = [p.pos[0] + f[0] * TR.hw, p.pos[1], p.pos[2] + f[1] * TR.hw];
      for (const t of this.players.values()) {
        if (T.held.length >= A.max) break;
        if (t === p || !t.alive || this.friendly(p, t) || t.mheld || this.trBig(t)) continue; // (a mech, a rig, a ball: too big for the basket. they get rammed)
        if (!t.isBot && n - (t.spawnT || 0) < 1200) continue; // (just spawned)
        const dx = t.pos[0] - front[0], dz = t.pos[2] - front[2], dy = t.pos[1] - p.pos[1];
        if (Math.hypot(dx, dz) > A.reach || dy < -1.5 || dy > TR.h) continue;
        if (!clear(this.mechCenter(p), center(t), this.boxes)) continue;
        const used = new Set(T.held.map((h) => h.i));
        let i = 0; while (used.has(i)) i++;
        T.held.push({ id: t.id, i, acc: 0 });
        this.mechHold(p, t, 'scoop');
        this.mechHeldPlace(p, t);
        this.tag(t, p, 'trscoop'); // (a fall out of the basket into the void is yours)
        this.broadcast({ t: 'mech', k: 'trhold', id: p.id, v: t.id, on: 1, s: 'scoop', i, n: T.held.length });
      }
      return T.held.length < A.max;
    },
    // ---- the pound coin lock: an ally rides in the child seat (keeps their guns, can't walk off with it)
    trRideStart(c, p, n) {
      const M = c.mech, T = M.tr;
      if (!p.alive || p.mech || p.mheld || p.trap || (p.br && (p.br.inBlimp || p.br.fly)) || (p.rig && this.rigOn(p)) || this.isBall(p) || p.ballUntil > n || (p.lz && (p.lz.by || p.lz.hold)) || (this.isleOn && p.dn)) { this.mechNo(p, 'not right now'); return false; }
      if (hdist(p.pos, c.pos) > TR.ride.reach + TR.hw || Math.abs(p.pos[1] - c.pos[1]) > 3) { this.mechNo(p, 'get closer'); return false; }
      if (T.rider) { this.mechNo(p, 'the seat is taken'); return false; }
      T.rider = p.id; T.riderUntil = p.isBot ? n + 7000 + Math.random() * 9000 : 0;
      this.mechHold(c, p, 'ride');
      this.mechHeldPlace(c, p);
      this.broadcast({ t: 'mech', k: 'trhold', id: c.id, v: p.id, on: 1, s: 'ride' });
      return true;
    },
    // someone out of the basket / seat. how: 'dump' (flung forward and up, 35), 'break' (the trolley broke: flung out),
    // 'hop' (a rider climbing out to the side), 'quiet' / 'dead' (let go where they are)
    trRelease(c, t, how) {
      const T = c.mech && c.mech.tr;
      const k = T && T.rider === t.id ? 'ride' : 'scoop';
      if (T) { T.held = T.held.filter((h) => h.id !== t.id); if (T.rider === t.id) T.rider = 0; }
      if (t.mheld && t.mheld.by === c.id) t.mheld = null;
      this.broadcast({ t: 'mech', k: 'trhold', id: c.id, v: t.id, on: 0, s: k, why: how });
      if (!t.alive || how === 'dead') return;
      const f = fwdOf(c), cv = c.isBot ? [c.vel[0], c.vel[2]] : c.mech && c.mech.tr ? velOf(this, c, c.mech, now()) : [0, 0];
      // somewhere it can't be inside a wall: their spot if the trolley's middle can see it, else the middle
      // (no wall between the trolley's middle and that spot, not inside anything, not off the map)
      let at = t.pos.slice();
      const mid = [c.pos[0], c.pos[1] + 0.4, c.pos[2]];
      if (!clear(mid, [at[0], at[1] + 0.4, at[2]], this.boxes) || playerOverlap(at, this.boxes) || (this.map.bounds && outOfBounds(this.map, at))) at = [c.pos[0], c.pos[1] + 0.3, c.pos[2]];
      let v = [cv[0] * 0.6, 2, cv[1] * 0.6];
      if (how === 'hop') { // out over the side with no wall
        const o = this.mechOutSpot(c.pos, [[Math.cos(c.yaw), -Math.sin(c.yaw)], [-Math.cos(c.yaw), Math.sin(c.yaw)], [Math.sin(c.yaw), Math.cos(c.yaw)]], TR.hw + 0.9);
        at = [o[0], Math.max(o[1], c.pos[1]) + 0.3, o[2]]; v = [cv[0] * 0.5, TR.ride.hop, cv[1] * 0.5];
      } else if (how === 'break') { const a = Math.random() * Math.PI * 2; v = [Math.cos(a) * 7, 13, Math.sin(a) * 7]; }
      else if (how === 'quiet') v = [0, 0, 0];
      t.pos = at; t.vel = v.slice();
      if (t.isBot) { t.onGround = false; t.pos[1] += 0.05; } else send(t, { t: 'mech', k: 'pos', p: at.map(r2), v: v.map(r2) });
      if (how === 'dump') { // the basket tips: forward and up, hard (an ult hit: it doesn't charge the next one)
        const A = TR.aisle;
        this.mechKitHurt(c, t, 'trdump', A.dmg, [f[0] * A.fling + cv[0] * 0.3, A.up, f[1] * A.fling + cv[1] * 0.3], { ult: 1 });
      }
    },
    trLetGoAll(p, M, how) {
      const T = M.tr, ids = [...T.held.map((h) => h.id), ...(T.rider ? [T.rider] : [])];
      for (const id of ids) { const t = this.players.get(id); if (t) this.trRelease(p, t, how); else { T.held = T.held.filter((h) => h.id !== id); if (T.rider === id) T.rider = 0; } }
    },
    // every tick: everyone in the basket goes where it goes (and the scooped take 8/s); anyone who isn't really in it
    // any more (died, left, a new life, popped out by a bubble or a rope) is let go
    trCarry(p, M, n, dt) {
      const T = M.tr, A = TR.aisle, resend = n - T.holdT > 1000;
      if (resend) T.holdT = n;
      for (const id of [...T.held.map((h) => h.id), ...(T.rider ? [T.rider] : [])]) {
        const t = this.players.get(id), h = T.held.find((x) => x.id === id);
        if (!t || !t.alive || !t.mheld || t.mheld.by !== p.id || t.seq !== t.mheld.seq) {
          T.held = T.held.filter((x) => x.id !== id); if (T.rider === id) T.rider = 0;
          if (t && t.mheld && t.mheld.by === p.id) t.mheld = null;
          this.broadcast({ t: 'mech', k: 'trhold', id: p.id, v: id, on: 0, why: 'gone' });
          continue;
        }
        if (t.trap || (t.lz && (t.lz.by || t.lz.hold))) { this.trRelease(p, t, 'quiet'); continue; }
        this.mechHeldPlace(p, t);
        if (resend && !t.isBot) send(t, { t: 'mech', k: 'trhold', id: p.id, v: t.id, on: 1, s: h ? 'scoop' : 'ride', i: h ? h.i : 0 }); // (in case they missed it)
        if (!h) { if (t.isBot && T.riderUntil && n > T.riderUntil) this.trRelease(p, t, 'hop'); continue; } // a bot rider gets bored and hops out
        h.acc += A.dps * dt;
        if (h.acc >= 2) { const a = Math.floor(h.acc); h.acc -= a; this.mechKitHurt(p, t, 'trscoop', a, null, { ult: 1 }); }
      }
    },
    // allied bots hop in sometimes: one on foot right next to a slow trolley with an empty seat
    trRiders(p, M, n) {
      const T = M.tr;
      if (T.rider || n < T.offerT) return;
      T.offerT = n + 1200;
      const v = speedOf(this, p, M, n);
      if (Math.hypot(v[0], v[1]) > 9 || Math.random() > 0.5) return;
      for (const b of this.players.values()) {
        if (!b.isBot || b === p || !b.alive || !this.friendly(p, b) || b.mech || b.mheld || (b.ai && b.ai.dummy)) continue;
        if (hdist(b.pos, p.pos) > TR.ride.reach + TR.hw || Math.abs(b.pos[1] - p.pos[1]) > 2.5) continue;
        if (this.trRideStart(p, b, n)) { this.broadcast({ t: 'chat', id: 0, m: `${b.name} hopped in ${p.name}'s trolley` }); return; }
      }
    },

    // ---- bots: race about, drift into fights to build a charge, push them, toss cans, AISLE 5 when someone's ahead
    trBot(b, think, dt, n) {
      const M = b.mech, T = M.tr, v = b.vel, ai = b.ai, D = M.bai || (M.bai = { driftUntil: 0, driftSide: 1, nextDrift: 0, nextCan: 0, peak: b.pos[1], pick: 0 });
      let t = this.players.get(ai.target);
      if (t && (!t.alive || this.friendly(b, t) || this.trHolding(b, t))) t = null;
      const e = this.mechEyeOf(b), tc = t ? this.mechCenter(t) : null;
      const flat = t ? hdist(t.pos, b.pos) : 1e9, vis = !!(t && clear(e, tc, this.boxes));
      const easy = ai.diff === 'easy' ? 0.5 : 1, hs = Math.hypot(v[0], v[2]);
      let wx = think.wx, wz = think.wz;
      // no fight about: drive over to an ally on foot so they can hop in
      if (!t || flat > 40) {
        if (!T.rider && this.teamsOn && this.teamsOn() && n > D.pick) {
          D.pick = n + 3000;
          D.ally = 0;
          for (const o of this.players.values()) if (o.isBot && o !== b && o.alive && this.friendly(b, o) && !o.mech && !o.mheld && hdist(o.pos, b.pos) < 30) { D.ally = o.id; break; }
        }
        const al = D.ally && this.players.get(D.ally);
        if (al && al.alive && !al.mheld && !T.rider) { const d = hdist(al.pos, b.pos) || 1; wx = (al.pos[0] - b.pos[0]) / d; wz = (al.pos[2] - b.pos[2]) / d; if (d < 3) wx = wz = 0; }
      } else { wx = (t.pos[0] - b.pos[0]) / (flat || 1); wz = (t.pos[2] - b.pos[2]) / (flat || 1); }
      let face = Math.hypot(wx, wz) > 0.1 ? Math.atan2(-wx, -wz) : b.yaw;
      if (t && vis) { face = Math.atan2(-(t.pos[0] - b.pos[0]), -(t.pos[2] - b.pos[2])); }
      // the plan
      let drifting = false;
      const ahead = t ? ((t.pos[0] - b.pos[0]) * -Math.sin(b.yaw) + (t.pos[2] - b.pos[2]) * -Math.cos(b.yaw)) / (flat || 1) : -1;
      if (t && vis && (M.ult || 0) >= 100 && !T.aisle && flat < 25 && ahead > 0.5) this.trAisle(b, n);
      if (T.aisle && T.held.length >= TR.aisle.max) this.trDump(b, 'full');
      if (!(M.dash && n < M.dash.until)) {
        // drift into the fight: swing out round them in an arc to build the charge, then push at them
        if (t && !T.aisle && n >= D.nextDrift && flat > 9 && flat < 45 && hs > TR.drift.min + 1 && chargeOf(T, n) < 0.9 && Math.random() < dt * 3 * easy) { D.driftUntil = n + 1500 + Math.random() * 500; D.driftSide = Math.random() < 0.5 ? 1 : -1; D.nextDrift = n + 3500; }
        if (n < D.driftUntil) {
          drifting = true;
          const a = 0.9 * D.driftSide, c = Math.cos(a), s = Math.sin(a); // (aim the wish off to the side: it slides round)
          [wx, wz] = [wx * c - wz * s, wx * s + wz * c];
          if (hs >= TR.drift.min) { T.ch = Math.min(1, chargeOf(T, n) + dt / TR.drift.build); T.chT = n; } // (the same rule as a player's: only at speed)
        }
        if (t && vis && n >= (M.cd.push || 0) && flat < 11 && ahead > 0.75 && (chargeOf(T, n) > 0.6 || flat < 4.5 || Math.random() < dt * 0.15)) {
          const h = this.trPushGo(b, n);
          if (h) { D.driftUntil = 0; const f = fwdOf(b); v[0] = f[0] * h.v; v[2] = f[1] * h.v; }
        }
      }
      // cans at anyone in sight (a lob: aim a bit high for the drop, lead them a little)
      if (t && vis && flat < 34 && n >= D.nextCan && !T.aisle) {
        D.nextCan = n + 1000 / TR.can.rate + (easy < 1 ? 250 : 40);
        const o = trSpot(b.pos, face, TR.muzzle), k = Math.hypot(tc[0] - o[0], tc[2] - o[2]) / TR.can.speed;
        const err = ai.diff === 'hard' ? 0.6 : ai.diff === 'easy' ? 2 : 1.1;
        const aim = [tc[0] + t.vel[0] * k * 0.6 + (Math.random() - 0.5) * err, tc[1] - 0.6 + 0.5 * WEAPONS.trcan.grav * k * k - TR.can.up * k, tc[2] + t.vel[2] * k * 0.6 + (Math.random() - 0.5) * err];
        const d = norm([aim[0] - o[0], aim[1] - o[1], aim[2] - o[2]]);
        if (d) { b.yaw = face; b.pitch = Math.asin(Math.max(-1, Math.min(1, d[1]))); this.trCan(b, d, n); }
      }
      b.yaw = face;
      if (t && !(t && vis)) b.pitch = 0;
      // drive: the cart's own physics (grip, drift, the push window, AISLE 5's top speed)
      let f = 0;
      const pushing = M.dash && n < M.dash.until;
      if (pushing) { const d = M.dash.dir; v[0] = d[0] * M.dash.v; v[2] = d[1] * M.dash.v; f |= MF.PUSH; }
      else {
        const top = (T.aisle ? TR.aisle.speed : TR.speed) * (easy < 1 ? 0.85 : 1), stop = !t && !(wx || wz);
        const h2 = [v[0], v[2]];
        trDrive(h2, stop ? 0 : wx, stop ? 0 : wz, dt, top, drifting, b.onGround, false);
        v[0] = h2[0]; v[2] = h2[1];
        if (b.onGround && t && t.pos[1] - b.pos[1] > 2.5 && flat < 14 && Math.random() < dt * 2) { v[1] = TR.hop; b.onGround = false; b.pos[1] += 0.05; }
      }
      if (drifting) f |= MF.DRIFT;
      if (T.aisle) f |= MF.AISLE;
      v[1] -= TR.grav * dt;
      const was = b.onGround;
      this.mechBotMove(b, v, dt);
      if (!b.onGround) { if (was) D.peak = b.pos[1]; else D.peak = Math.max(D.peak, b.pos[1]); }
      else if (!was) { if (D.peak - b.pos[1] > 2.5) this.mechStomp(b, n); D.peak = b.pos[1]; }
      b.f = FLAGS.MECH | f;
      if (b.onGround) b.ground = b.pos.slice();
    },
  });
}
