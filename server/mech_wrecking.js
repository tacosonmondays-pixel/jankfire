// WRECKING BALL, the battle island dive tank (docs/mechs/ROSTER.md; numbers: MECH.wrecking in shared/mech.js). Movement
// is the client's, like every mech; the server judges what it does: rams by the speed it measures, the rev launch from
// how long it saw you rev, the chain only onto a surface you can see (in range), slams by the height you really fell,
// the PILE DRIVER only with a full ult and only off a real climb. installWrecking hooks it into server/mech.js (KIT).
// Its state lives on the pilot's p.mech.wb (energy, cooldowns and the ult live on the mech, like the others').
import { FLAGS } from '../shared/weapons.js';
import { MECH, MF, wbRam, wbSlam, wbPile, wbRevSpeed, spend } from '../shared/mech.js';
import { raycast } from '../shared/physics.js';

const WB = MECH.wrecking;
const COAST = 7; // m/s per s the speed cap comes back down after a launch / swing / dive (the client's drag is harder)

export function installWrecking(Room, U) {
  const { now, num, vec3, r2, center, safe, send, KIT, clear, lookOf, hdist } = U;
  const ballC = (p) => [p.pos[0], p.pos[1] + WB.r, p.pos[2]]; // the ball's middle
  const floorUnder = (room, p, d = 0.9) => raycast([p.pos[0], p.pos[1] + 0.3, p.pos[2]], [0, -1, 0], d, room.boxes);

  KIT.wrecking = {
    enter(p, M) { M.wb = { chain: null, revT: 0, slam: null, pile: null, coast: null }; },
    exit(p, M) { if (M.wb && M.wb.chain) this.wbChainOff(p, 'gone'); },
    // the flags it's allowed: A on the chain, B in a slam / pile driver, C in a rev launch
    flags(p, M, want, n) {
      const W = M.wb;
      let f = 0;
      if (W.chain) {
        const c = ballC(p), a = W.chain.at, d = Math.hypot(c[0] - a[0], c[1] - a[1], c[2] - a[2]);
        if (n - W.chain.t > WB.chain.life * 1000 || d > W.chain.len + WB.chain.snap) this.wbChainOff(p, 'snap'); else f |= MF.CHAIN;
      }
      if (W.pile || W.slam) f |= MF.PILE;
      if (M.dash && n < M.dash.until) f |= MF.REV;
      return f;
    },
    // the flat speed it may go right now (mechSnap): what it's doing, or what's left of the last burst of speed
    cap(p, M, f, n) {
      const W = M.wb;
      let c = WB.speed;
      if (W.chain) c = WB.chain.speed;
      if (W.pile) c = W.pile.ph === 'down' ? WB.pile.dive : 10;
      if (M.dash && n < M.dash.until) c = Math.max(c, M.dash.v);
      if (W.coast) c = Math.max(c, W.coast.v - COAST * Math.max(0, n - W.coast.t) / 1000);
      return c;
    },
    // going up: the chain pays for a climb to its anchor (and a bit); the pile driver paid its rise when it started
    budget(p, M) { const W = M.wb; if (W.chain) M.ub = Math.max(M.ub, W.chain.at[1] + 3 - p.pos[1]); },
    // it touched down after falling `drop` m (measured from the snapshots)
    land(p, M, drop, n) {
      const W = M.wb;
      if (W.pile && W.pile.ph === 'down') this.wbPileLand(p, drop, n);
      else if (W.slam) this.wbSlamLand(p, drop, n);
    },
    msg(p, M, m, n, d) {
      switch (m.k) {
        case 'rev': if (m.on === 1) this.wbRevStart(p, n); else if (m.on === 0) this.wbRevGo(p, n); break;
        case 'chain': if (m.off === 1) this.wbChainOff(p, 'let go'); else this.wbChain(p, vec3(m.p), n); break;
        case 'slam': this.wbSlamStart(p, n); break;
        case 'pile': this.wbPileStart(p, n); break;
        case 'pdrop': if (d) this.wbPileDrop(p, d, n); break;
      }
    },
    tick(p, M, n) {
      const W = M.wb;
      if (W.slam && n - W.slam.t > WB.slam.win * 1000) W.slam = null;
      if (W.pile) {
        const P = WB.pile, up = ((P.rise / P.up + P.hang) * 1000 + 300) * P.slow;
        if (n - W.pile.t > P.life * 1000 * P.slow) { W.pile = null; this.broadcast({ t: 'mech', k: 'wbpile', id: p.id, ph: 'off' }); }
        else if (W.pile.ph !== 'down' && n - W.pile.t > up) this.wbPileDrop(p, [0, -1, 0], n, true); // (hung there too long: straight down)
        else if (W.pile.ph === 'down' && (n > W.pile.dEnd || hdist(p.pos, W.pile.to) > W.pile.dl + 5)) { W.pile = null; M.bank = Math.min(M.bank, MECH.slack); this.broadcast({ t: 'mech', k: 'wbpile', id: p.id, ph: 'off' }); } // (the dive's 70 m/s is for the trip to its spot: no longer, and not away from it)
      }
      if (W.coast && W.coast.v - COAST * (n - W.coast.t) / 1000 < WB.speed) W.coast = null;
      if (!W.pile) this.wbRamTick(p, M, n);
    },
    // passive: rolling (or swinging, or diving) it shrugs off knockback entirely
    shrug(t) {
      const M = t.mech, W = M.wb, v = t.isBot ? [t.vel[0], t.vel[2]] : M.mv && now() - M.snapT < 300 ? M.mv : [0, 0]; // (measured, and only while it's still sending)
      if ((W && (W.chain || W.pile)) || Math.hypot(v[0], v[1]) > WB.shrug) return [0, 0, 0];
      return null;
    },
    bot(b, think, dt, n) { this.wbBot(b, think, dt, n); },
  };

  Object.assign(Room.prototype, {
    wbOn(p) { return this.mechOn(p) && p.mech.f === 'wrecking' && !!p.mech.wb; },
    // ---- ram: rolling into people. the speed is what the server measured (players) / its own (bots)
    wbRamTick(p, M, n) {
      const v = p.isBot ? [p.vel[0], p.vel[2]] : M.mv && n - M.snapT < 300 ? M.mv : [0, 0];
      const hs = Math.hypot(v[0], v[1]), h = wbRam(hs);
      if (!h) return;
      const fx = v[0] / hs, fz = v[1] / hs;
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t) || n < (M.ramT.get(t.id) || 0)) continue;
        const dx = t.pos[0] - p.pos[0], dz = t.pos[2] - p.pos[2], l = Math.hypot(dx, dz), dy = t.pos[1] - p.pos[1];
        const reach = WB.r + 0.35 + (this.mechOn(t) ? MECH[t.mech.f].hw : 0.45);
        if (l > reach || dy < -2 || dy > WB.h || (l > 0.3 && (dx * fx + dz * fz) / l < 0.2)) continue;
        if (!clear(ballC(p), this.mechCenter(t), this.boxes)) continue;
        M.ramT.set(t.id, n + WB.ram.cd * 1000);
        this.mechKitHurt(p, t, 'wbram', h.dmg, [fx * h.kb, h.up, fz * h.kb]);
        this.broadcast({ t: 'mech', k: 'ram', id: p.id, to: t.id, p: this.mechCenter(t).map(r2), big: h.dmg >= 45 ? 1 : 0, w: 'wbram' });
      }
    },
    // ---- rev (LMB): hold to spin up on the spot, let go to launch. the charge is what the server timed
    wbRevStart(p, n) {
      const M = p.mech, W = M.wb;
      if (W.pile || W.chain || (M.dash && n < M.dash.until)) return;
      W.revT = n;
      this.broadcast({ t: 'mech', k: 'wbrev', id: p.id, on: 1 }, p.isBot ? undefined : p.id);
    },
    wbRevGo(p, n) {
      const M = p.mech, W = M.wb, R = WB.rev;
      if (!W.revT) return;
      const c = (n - W.revT) / 1000;
      W.revT = 0;
      if (c < R.min || W.pile || W.chain) { this.broadcast({ t: 'mech', k: 'wbrev', id: p.id, on: 0 }); return; }
      if (!spend(M.E, R.cost, n)) { this.mechNo(p, 'no energy'); this.mechEn(p, true); this.broadcast({ t: 'mech', k: 'wbrev', id: p.id, on: 0 }); return; }
      const v = wbRevSpeed(c);
      M.dash = { k: 'rev', t0: n, until: n + R.len * 1000 + 200, v };
      W.coast = { v, t: n + R.len * 1000 };
      M.bank += 4;
      this.broadcast({ t: 'mech', k: 'wbrev', id: p.id, on: 2, v: r2(v) });
      this.mechEn(p, true);
      return v;
    },
    // ---- the chain (Shift): onto a wall / roof you can see, in range. its length is set when it bites
    wbChain(p, at, n) {
      const M = p.mech, W = M.wb, C = WB.chain;
      if (!at || W.pile || W.chain) return false;
      if (n < (M.cd.chain || 0) - 150) return false;
      const e = this.mechEyeOf(p), d = [at[0] - e[0], at[1] - e[1], at[2] - e[2]], l = Math.hypot(d[0], d[1], d[2]);
      if (l > C.range + 1 || l < 3) { this.mechNo(p, 'chain: out of reach'); return false; }
      if (at[1] < p.pos[1] + 1) { this.mechNo(p, 'chain: aim higher'); return false; }
      const h = raycast(e, [d[0] / l, d[1] / l, d[2] / l], l + 0.8, this.boxes);
      if (!h || h.t < l - 1.2 || h.box.pad) { this.mechNo(p, 'chain: nothing to hook'); return false; } // (it has to bite something solid, in plain sight)
      if (!spend(M.E, C.cost, n)) { this.mechNo(p, 'no energy'); this.mechEn(p, true); return false; }
      const c = ballC(p);
      W.chain = { at: h.point.slice(), len: Math.max(3, Math.hypot(c[0] - h.point[0], c[1] - h.point[1], c[2] - h.point[2])), t: n };
      W.revT = 0; W.slam = null;
      M.cd.chain = n + C.cd * 1000;
      this.broadcast({ t: 'mech', k: 'wbchain', id: p.id, p: W.chain.at.map(r2), len: r2(W.chain.len) });
      this.mechEn(p, true);
      return true;
    },
    wbChainOff(p, why) {
      const M = p.mech, W = M && M.wb;
      if (!W || !W.chain) return;
      W.chain = null;
      W.coast = { v: WB.chain.speed, t: now() }; // (the swing's speed carries on and fades)
      M.cd.chain = Math.max(M.cd.chain || 0, now() + WB.chain.cd * 1000);
      this.broadcast({ t: 'mech', k: 'wbchain', id: p.id, off: 1, why });
    },
    // ---- ground slam (E): in the air it dives; on the floor it hops first. the size is the height it really fell
    wbSlamStart(p, n) {
      const M = p.mech, W = M.wb, S = WB.slam;
      if (W.slam || W.pile || !this.mechCd(M, 'slam', S.cd, n)) return false;
      if (W.chain) this.wbChainOff(p, 'slam');
      W.slam = { t: n };
      if (floorUnder(this, p)) M.ub = Math.max(M.ub, S.hop * S.hop / (2 * WB.grav) + 0.8); // (the hop up is allowed)
      this.broadcast({ t: 'mech', k: 'wbslam', id: p.id });
      this.mechEn(p, true);
      return true;
    },
    wbSlamLand(p, drop, n) {
      const W = p.mech.wb;
      if (!W.slam || n - W.slam.t < 200) return;
      W.slam = null;
      const s = wbSlam(drop);
      this.wbBlast(p, s.r, (d) => { const f = 1 - d / s.r; return { dmg: s.dmg * (0.35 + 0.65 * f), kb: s.kb * (0.5 + 0.5 * f), up: s.up * (0.6 + 0.4 * f) }; }, 'wbslam');
      this.broadcast({ t: 'mech', k: 'wbquake', id: p.id, p: p.pos.map(r2), r: r2(s.r), sz: r2(s.k) });
      this.mechStomp(p, n);
    },
    // ---- PILE DRIVER (Q, a full ult): straight up, hang there aiming, then dive onto the spot you pick
    wbPileStart(p, n) {
      const M = p.mech, W = M.wb, P = WB.pile;
      if (W.pile) return false;
      if ((M.ult || 0) < 100) { this.mechNo(p, 'ultimate not ready'); return false; }
      if (W.chain) this.wbChainOff(p, 'pile');
      M.ult = 0; W.slam = null; W.revT = 0;
      W.pile = { ph: 'up', t: n, y0: p.pos[1] };
      M.ub = Math.max(M.ub, 0) + P.rise + 2; // (the rise is paid for: only this once)
      this.broadcast({ t: 'mech', k: 'wbpile', id: p.id, ph: 'up' });
      this.mechEn(p, true);
      return true;
    },
    // where it dives: along your aim onto a floor in range (in sight); none: straight down
    wbPileDrop(p, d, n, auto) {
      const W = p.mech.wb, P = WB.pile;
      if (!W.pile || W.pile.ph === 'down' || (!auto && n - W.pile.t < 300)) return;
      const e = this.mechEyeOf(p);
      let to = null;
      if (!auto && this.mechAimOk(p, d, 0.3) && d[1] < -0.15) {
        const h = raycast(e, d, P.range * 1.6, this.boxes);
        if (h && !h.box.pad && hdist(h.point, p.pos) <= P.range && h.point[1] < p.pos[1]) to = h.point.slice();
      }
      if (!to) { const h = raycast(e, [0, -1, 0], 200, this.boxes); to = h ? h.point.slice() : [p.pos[0], p.pos[1] - 40, p.pos[2]]; }
      W.pile.ph = 'down'; W.pile.to = to; W.pile.dT = n;
      W.pile.dl = hdist(p.pos, to);
      W.pile.dEnd = n + Math.hypot(to[0] - p.pos[0], to[1] - p.pos[1], to[2] - p.pos[2]) / P.dive * 2500 * P.slow + 1500; // (room for a slow client: it can't go anywhere but toward the spot anyway)
      this.broadcast({ t: 'mech', k: 'wbpile', id: p.id, ph: 'down', to: to.map(r2) });
    },
    wbPileLand(p, drop, n) {
      const W = p.mech.wb, P = WB.pile;
      W.pile = null;
      W.coast = null;
      if (drop < P.min) { this.broadcast({ t: 'mech', k: 'wbpile', id: p.id, ph: 'off' }); return; } // (it never really fell: a fizzle)
      this.wbBlast(p, P.r, wbPile, 'wbpile');
      this.broadcast({ t: 'mech', k: 'wbquake', id: p.id, p: p.pos.map(r2), r: P.r, sz: 1, big: 1 });
      this.mechStomp(p, n);
    },
    // a blast round the ball's foot: everyone in r it can see gets hit(d) and flung out and up
    wbBlast(p, r, hit, w) {
      const c = [p.pos[0], p.pos[1] + 0.8, p.pos[2]];
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t)) continue;
        const tc = this.mechOn(t) ? this.mechCenter(t) : center(t), to = [tc[0] - c[0], tc[1] - c[1], tc[2] - c[2]];
        const d = Math.max(0, Math.hypot(to[0], to[1], to[2]) - (this.mechOn(t) ? MECH[t.mech.f].hw : 0)), h = hit(d);
        if (!h || !clear(c, tc, this.boxes)) continue;
        const hl = Math.hypot(to[0], to[2]), out = hl > 0.2 ? [to[0] / hl, to[2] / hl] : [0, 0];
        this.mechKitHurt(p, t, w, h.dmg, [out[0] * h.kb, h.up, out[1] * h.kb], w === 'wbpile' ? { ult: 1 } : undefined);
      }
    },

    // ---- bots: roll at them, rev-launch from mid range, chain up to anyone above, slam crowds, pile-drive when full
    wbBot(b, think, dt, n) {
      const M = b.mech, W = M.wb, v = b.vel, ai = b.ai, B = M.bai || (M.bai = { revUntil: 0, chainUntil: 0, peak: b.pos[1], air: false });
      let t = this.players.get(ai.target);
      if (t && (!t.alive || this.friendly(b, t))) t = null;
      const e = this.mechEyeOf(b), tc = t ? this.mechCenter(t) : null, dv = t ? [tc[0] - e[0], tc[1] - e[1], tc[2] - e[2]] : null;
      const dist = t ? Math.hypot(dv[0], dv[1], dv[2]) : 1e9, flat = t ? hdist(t.pos, b.pos) : 1e9, vis = !!(t && clear(e, tc, this.boxes));
      if (t) { b.yaw = Math.atan2(-(t.pos[0] - b.pos[0]), -(t.pos[2] - b.pos[2])); b.pitch = Math.atan2(dv[1], Math.hypot(dv[0], dv[2])); }
      const easy = ai.diff === 'easy' ? 0.5 : 1;
      let wx = t ? (t.pos[0] - b.pos[0]) / (flat || 1) : think.wx, wz = t ? (t.pos[2] - b.pos[2]) / (flat || 1) : think.wz;
      let f = 0;
      const G = WB.grav;
      // ---- the plan
      if (W.pile) {
        if (W.pile.ph === 'up') { // straight up, then pick them
          v[0] *= 0.9; v[2] *= 0.9; v[1] = WB.pile.up;
          if (b.pos[1] - W.pile.y0 >= WB.pile.rise || n - W.pile.t > WB.pile.rise / WB.pile.up * 1000 + 400) { v[1] = 0; W.pile.ph = 'hang'; W.pile.hT = n; }
        } else if (W.pile.ph === 'hang') {
          v[0] = v[1] = v[2] = 0;
          if (n - W.pile.hT > 500) { const aim = t ? [tc[0] - e[0], t.pos[1] - e[1], tc[2] - e[2]] : [0, -1, 0], l = Math.hypot(...aim) || 1; b.pitch = Math.asin(Math.max(-1, Math.min(1, aim[1] / l))); this.wbPileDrop(b, aim.map((x) => x / l), n); }
        } else if (W.pile.ph === 'down') {
          const to = W.pile.to, dd = [to[0] - b.pos[0], to[1] - b.pos[1], to[2] - b.pos[2]], l = Math.hypot(...dd) || 1;
          for (let i = 0; i < 3; i++) v[i] = dd[i] / l * WB.pile.dive;
        }
        f |= MF.PILE;
      } else if (W.chain) { // swing: pendulum, let go when it's past them or high enough
        v[1] -= G * dt;
        if (t) { const sp = Math.hypot(v[0], v[2]) || 1; v[0] += (v[0] / sp) * WB.chain.pump * dt; v[2] += (v[2] / sp) * WB.chain.pump * dt; }
        if (n > B.chainUntil || (t && b.pos[1] > t.pos[1] + 2 && v[1] > 0)) this.wbChainOff(b, 'let go');
        f |= MF.CHAIN;
      } else if (B.revUntil) { // revving up on the spot, facing them
        v[0] *= Math.max(0, 1 - dt * 6); v[2] *= Math.max(0, 1 - dt * 6); v[1] -= G * dt;
        if (n >= B.revUntil) {
          B.revUntil = 0;
          const sp = this.wbRevGo(b, n);
          if (sp) { const d2 = t ? [wx, wz] : [-Math.sin(b.yaw), -Math.cos(b.yaw)]; v[0] = d2[0] * sp; v[2] = d2[1] * sp; }
        }
      } else {
        // pick a move
        const near = [...this.players.values()].filter((o) => o !== b && o.alive && !this.friendly(b, o) && hdist(o.pos, b.pos) < 7).length;
        if (t && vis && (M.ult || 0) >= 100 && flat < WB.pile.range - 5 && b.onGround) this.wbPileStart(b, n);
        else if (!W.slam && n >= (M.cd.slam || 0) && ((b.onGround && (near >= 2 || (near === 1 && Math.random() < dt * 0.8 * easy))) || (!b.onGround && t && b.pos[1] - t.pos[1] > 4 && flat < 9))) {
          if (this.wbSlamStart(b, n) && b.onGround) { v[1] = WB.slam.hop; b.onGround = false; b.pos[1] += 0.05; }
        } else if (t && vis && b.onGround && flat > 9 && flat < 38 && !(M.dash && n < M.dash.until) && M.E.v >= WB.rev.cost && Math.random() < dt * 0.7 * easy) {
          this.wbRevStart(b, n); B.revUntil = n + (500 + Math.random() * 400);
        } else if (t && n >= (M.cd.chain || 0) && n >= (B.chainTry || 0) && M.E.v >= WB.chain.cost + 5 && (t.pos[1] - b.pos[1] > 4 || flat > 24) && Math.random() < dt * 2 * easy) {
          // something to swing from: up toward them (steep to shallow), else up to either side of them
          B.chainTry = n + 700;
          for (const [ux, uz, uy] of [[wx, wz, 0.6], [wx, wz, 1], [wx, wz, 1.6], [wx - wz * 0.7, wz + wx * 0.7, 0.8], [wx + wz * 0.7, wz - wx * 0.7, 0.8]]) {
            const l = Math.hypot(ux, uy, uz), h = raycast(e, [ux / l, uy / l, uz / l], WB.chain.range, this.boxes);
            if (!h || h.box.pad || h.point[1] < b.pos[1] + 4 || h.t < 5) continue;
            if (this.wbChain(b, h.point, n)) { B.chainUntil = n + 1300 + Math.random() * 1000; if (b.onGround) { v[1] = 6; b.onGround = false; b.pos[1] += 0.05; } }
            break;
          }
        }
        // roll: slow to get going, slow to stop, faster than anything once it's going
        const hs = Math.hypot(v[0], v[2]);
        if (b.onGround) {
          if (hs > WB.speed) { const k = Math.max(0, hs - 16 * dt) / hs; v[0] *= k; v[2] *= k; }
          else if (hs > 0) { const k = Math.max(0, hs - Math.max(hs, 3) * WB.fric * 0.45 * dt) / hs; v[0] *= k; v[2] *= k; }
          const cur = v[0] * wx + v[2] * wz, sp = flat < 2.5 ? 0 : WB.speed * (easy < 1 ? 0.8 : 1);
          if (sp - cur > 0) { const a = Math.min(sp - cur, WB.accel * WB.speed * dt); v[0] += a * wx; v[2] += a * wz; }
        } else if (hs > WB.speed) { const k = Math.max(0, hs - 9 * dt) / hs; v[0] *= k; v[2] *= k; }
        if (W.slam && !b.onGround && v[1] < 4) v[1] = -WB.slam.dive; else v[1] -= G * dt;
        if (W.slam) f |= MF.PILE;
      }
      if (M.dash && n < M.dash.until) f |= MF.REV;
      // move: the chain holds the ball's middle on its sphere
      const was = b.onGround;
      this.mechBotMove(b, v, dt);
      if (W && W.chain) {
        const c = ballC(b), a = W.chain.at, d = [c[0] - a[0], c[1] - a[1], c[2] - a[2]], l = Math.hypot(...d);
        if (l > W.chain.len) {
          const u = d.map((x) => x / l), k = W.chain.len / l;
          b.pos = [a[0] + d[0] * k, a[1] + d[1] * k - WB.r, a[2] + d[2] * k];
          const out = v[0] * u[0] + v[1] * u[1] + v[2] * u[2];
          if (out > 0) for (let i = 0; i < 3; i++) v[i] -= u[i] * out;
          const sp = Math.hypot(...v); if (sp > WB.chain.speed) for (let i = 0; i < 3; i++) v[i] *= WB.chain.speed / sp;
        }
      }
      // landings: the height it really fell (a slam / the pile driver go off; a plain big drop stomps)
      if (!b.onGround) { if (was) B.peak = b.pos[1]; else B.peak = Math.max(B.peak, b.pos[1]); }
      else if (!was) {
        const drop = B.peak - b.pos[1];
        if (W.pile && W.pile.ph === 'down') this.wbPileLand(b, drop, n);
        else if (W.slam) this.wbSlamLand(b, drop, n);
        else if (drop > 2) this.mechStomp(b, n);
        B.peak = b.pos[1];
      }
      if (W.pile && W.pile.ph === 'down' && n - (W.pile.dT || n) > 3000) { W.pile = null; } // (stuck on something: give up)
      b.f = FLAGS.MECH | f;
      if (b.onGround) b.ground = b.pos.slice();
    },
  });
}
