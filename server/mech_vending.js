// VENDING MACHINE, the battle island support (docs/mechs/ROSTER.md; numbers: MECH.vending in shared/mech.js). Movement
// is the client's, like every mech; the server judges the rest: the coin turret (hitscan from the coin slot, aim cone,
// rate), the colas (only the server spawns, owns and hands them out: allies only, a cap per machine), the OUT OF
// ORDER wall (it eats enemy fire: guns, mech guns, projectiles; allies shoot through), RESTOCK (a full ult, allies in
// range), STUCK (x2) and JAMMED (server dice), and the kick that unjams it (an on-foot ally, in reach). installVending
// hooks it into server/mech.js (KIT). Pilot state: p.mech.vm, which lives on the mech (charges, the jam) so hopping out
// keeps it. World state: room._vm { colas, walls }.
import { FLAGS, WEAPONS, QUIZ } from '../shared/weapons.js';
import { MECH, MF, vmCharges, vmWallCross } from '../shared/mech.js';
import { BR } from '../shared/royale.js';
import { raycast, rayBox, playerBoxes, PH } from '../shared/physics.js';

const VM = MECH.vending;
const rng = (k) => Math.random() < k; // (STUCK and JAMMED: the server's dice, never the client's)

export function installVending(Room, U) {
  const { now, vec3, r2, send, KIT, clear, hdist } = U;
  const fwdOf = (p) => [-Math.sin(p.yaw), -Math.cos(p.yaw)];
  const S = () => MECH.scale || 1; // (the size-1 machine's spots x the shared mech size)
  const slotOf = (p) => { const f = fwdOf(p), k = S(); return [p.pos[0] + f[0] * 0.9 * k, p.pos[1] + 4.0 * k, p.pos[2] + f[1] * 0.9 * k]; }; // the coin slot (mk_muzzle)
  const flapOf = (p) => { const f = fwdOf(p), k = S(); return [p.pos[0] + f[0] * 1.2 * k, p.pos[1] + 1.5 * k, p.pos[2] + f[1] * 1.2 * k]; }; // the delivery flap (mk_drop)
  const W = (room) => room._vm || (room._vm = { colas: new Map(), walls: new Map(), nc: 0, nw: 0, listT: 0 });
  const ally = (room, a, b) => !!a && !!b && (a === b || room.friendly(a, b));

  KIT.vending = {
    enter(p, M, m, n) { M.vm = m.vm || (m.vm = { ch: { n: VM.cola.charges, t: n }, jam: 0, dispT: 0, stockT: 0, coinT: 0 }); }, // (on the mech: hop out and back in, it's all still there)
    // out of it: a hop leaves the wall standing its 10 s; blowing up (or a quiet end: round over, left) takes it down
    exit(p, M, why) { if (why !== 'hop') this.vmWallsOf(p.id, why === 'boom' ? 'break' : 'gone'); },
    flags(p, M, want, n) { const V = M.vm; return (n < V.jam ? MF.VJAM : 0) | (n - V.stockT < VM.restock.hold * 1000 ? MF.VSTOCK : 0) | (n - V.coinT < 250 ? MF.VCOIN : 0); },
    // the flat speed: a waddle, and a cola's sugar rush while it lasts (the same allowance on foot: p.fastUntil)
    cap(p, M, f, n) { return VM.speed * (n < (p.fastUntil || 0) ? QUIZ.fast : 1); },
    msg(p, M, m, n, d) {
      switch (m.k) {
        case 'coin': if (d) this.vmCoin(p, d, n); break;
        case 'disp': this.vmDispense(p, vec3(m.p), n); break;
        case 'wall': this.vmWall(p, n); break;
        case 'stock': this.vmRestock(p, n); break;
      }
    },
    tick(p, M, n) { vmCharges(M.vm.ch, n); },
    en(p, M, n) { const V = M.vm, c = vmCharges(V.ch, n); return { ch: c, chT: c < VM.cola.charges ? Math.round(V.ch.t + VM.cola.every * 1000 - n) : 0, jam: V.jam > n ? Math.round(V.jam - n) : 0 }; },
    // someone on foot pokes this machine (server/mech.js mechPoke): the kick
    poke(p, t, M, k, n) { if (k === 'kick') this.vmKick(p, t, n); },
    bot(b, think, dt, n) { this.vmBot(b, think, dt, n); },
    world(n, dt) { this.vmWorld(n, dt); },
    leave(p) { this.vmWallsOf(p.id, 'gone'); this.vmColasOf(p.id); }, // disconnected: their colas and wall go with them
    reset() { const S = W(this); for (const w of [...S.walls.values()]) this.vmWallGone(w, 'gone'); for (const c of [...S.colas.values()]) this.vmColaGone(c); }, // a new round / map / mode
  };

  Object.assign(Room.prototype, {
    vmOn(p) { return this.mechOn(p) && p.mech.f === 'vending' && !!p.mech.vm; },
    // ---- the jank: 6% of uses jam. nothing comes out (nothing is spent either), Shift / E / Q lock until it's kicked
    vmJam(p, n, what) {
      if (!rng(VM.jam.p)) return false;
      const V = p.mech.vm;
      V.jam = n + VM.jam.lock * 1000;
      this.broadcast({ t: 'mech', k: 'vmjam', id: p.id, ms: VM.jam.lock * 1000, w: what });
      this.mechEn(p, true);
      return true;
    },
    // an on-foot ally kicks it (in reach): unjammed, and a free cola pops out ("UNSTUCK"). nothing else counts
    vmKick(p, t, n) {
      const V = t.mech && t.mech.vm;
      if (!V || !(V.jam > n) || p.mech || p.dn || p === t || !this.friendly(p, t)) return false; // (p.dn: battle island, down on the floor)
      if (hdist(p.pos, t.pos) > VM.jam.reach + VM.hw || Math.abs(p.pos[1] - t.pos[1]) > 3 * S()) return false;
      V.jam = 0;
      this.broadcast({ t: 'mech', k: 'vmkick', id: t.id, by: p.id });
      this.vmColaAt(t, this.vmDropSpot(t, null), 'kick');
      this.mechEn(t, true);
      return true;
    },

    // ---- LMB: the coin turret. a hitscan from the coin slot along your aim (in the cone round where the server has you
    // looking, no faster than the rate). gold coins; the OUT OF ORDER walls of the other side stop them
    vmCoin(p, d, n) {
      const M = p.mech, V = M.vm, C = VM.coin;
      if (n - V.coinT < 1000 / C.rate * 0.7 || !this.mechAimOk(p, d, C.cone)) return false;
      V.coinT = n;
      const o = slotOf(p), r = this.mechRay(p, o, d, C.range);
      const em = this.mechRayEmpty && this.mechRayEmpty(p, o, d, Math.min(C.range, Math.hypot(r.at[0] - o[0], r.at[1] - o[1], r.at[2] - o[2]))); // an empty parked mech in front of whatever it hit
      if (em) { r.t = null; r.wall = null; r.at = [o[0] + d[0] * em.t, o[1] + d[1] * em.t, o[2] + d[2] * em.t]; }
      this.broadcast({ t: 'mech', k: 'vmcoin', id: p.id, b: r.at.map(r2), h: r.t || em ? 1 : r.wall ? 2 : 0 }, p.isBot ? undefined : p.id);
      if (r.t) this.mechKitHurt(p, r.t, 'vmcoin', C.dmg * (r.head ? MECH.head : 1), [d[0] * 1.2, 0.4, d[2] * 1.2], { hs: r.head });
      else if (em) this.mechHarm(em.m, p, 'vmcoin', C.dmg, false, r.at);
      else if (r.wall) this.vmWallHurt(r.wall, C.dmg, r.at, p); // (only the first thing it hit takes it)
      return true;
    },

    // ---- Shift: DISPENSE. a Jank Cola out of the flap, lobbed onto the floor where you point (in reach, in sight), else
    // just in front. 3 charges, one back every 8 s. STUCK: 10% of the time two come out
    vmDispense(p, at, n) {
      const M = p.mech, V = M.vm, C = VM.cola;
      if (n < V.jam) { this.mechNo(p, 'jammed: get an ally to kick it'); return false; }
      if (n - V.dispT < C.gap * 1000) return false;
      if (vmCharges(V.ch, n) < 1) { this.mechNo(p, 'sold out'); this.mechEn(p, true); return false; }
      V.dispT = n;
      if (this.vmJam(p, n, 'disp')) return false;
      V.ch.n--;
      const spot = this.vmDropSpot(p, at), x2 = rng(VM.stuck);
      this.vmColaAt(p, spot, x2 ? 'x2' : '');
      if (x2) {
        const f = fwdOf(p), side = [-f[1], f[0]], s2 = this.vmFloor([spot[0] + side[0] * 0.9 * S(), spot[1], spot[2] + side[1] * 0.9 * S()]) || spot;
        this.vmColaAt(p, s2, 'x2');
        this.broadcast({ t: 'mech', k: 'vmstuck', id: p.id, w: 'disp' });
      }
      this.broadcast({ t: 'mech', k: 'vmdisp', id: p.id });
      this.mechEn(p, true);
      return true;
    },
    // where a can lands: the point asked for if it's a floor in toss range of the flap that the flap can see; else 2.4 m
    // in front (or right at the flap when there's a wall there)
    vmDropSpot(p, at) {
      const fl = flapOf(p), C = VM.cola;
      if (at && hdist(at, fl) <= C.toss + 0.5 && Math.abs(at[1] - p.pos[1]) < 4 && clear(fl, [at[0], at[1] + 0.4, at[2]], this.boxes)) { const g = this.vmFloor(at); if (g) return g; }
      const f = fwdOf(p), z = S(), h = raycast([p.pos[0], p.pos[1] + 0.6, p.pos[2]], [f[0], 0, f[1]], 2.9 * z, this.boxes), k = h ? Math.max(1.3 * z, h.t - 0.5) : 2.4 * z;
      return this.vmFloor([p.pos[0] + f[0] * k, p.pos[1] + 0.5, p.pos[2] + f[1] * k]) || [p.pos[0], p.pos[1], p.pos[2]];
    },
    vmFloor(at) { const h = raycast([at[0], at[1] + 1.2, at[2]], [0, -1, 0], 6, this.boxes); return h && !h.box.pad ? [at[0], h.point[1], at[2]] : null; },
    vmColaAt(p, spot, why) {
      const S = W(this), C = VM.cola, n = now();
      const mine = [...S.colas.values()].filter((c) => c.o === p.id);
      while (mine.length >= C.max) this.vmColaGone(mine.shift()); // (a cap per machine: the oldest goes flat)
      const c = { id: ++S.nc, o: p.id, p: spot.map(r2), born: n, until: n + C.life * 1000 };
      S.colas.set(c.id, c);
      this.broadcast({ t: 'mech', k: 'vmcola', id: p.id, c: c.id, p: c.p, from: flapOf(p).map(r2), ms: C.life * 1000, why });
      return c;
    },
    vmColaGone(c, drink) { const S = W(this); if (!S.colas.delete(c.id)) return; if (!drink) this.broadcast({ t: 'mech', k: 'vmcolax', c: c.id }); },
    vmColasOf(id) { const S = W(this); for (const c of [...S.colas.values()]) if (c.o === id) this.vmColaGone(c); },
    // someone on the right side walks over one: +40 HP (in a mech: +40 armour) and a sugar rush. it only goes if it helps
    vmDrink(c, t, owner, n) {
      const C = VM.cola;
      let a = 0;
      if (this.mechOn(t)) { const b = t.body; if (!b) return false; a = Math.min(C.armour, b.max - b.hp); b.hp += a; this.bodyFlush(t, true); }
      else { a = Math.max(0, Math.min(C.hp, 100 - t.hp)); this.heal(t, a, 100); } // (what it really healed, not always 40)
      t.fastUntil = Math.max(t.fastUntil || 0, n + C.boost * 1000); // (the speed allowance the game already gives a gold star)
      this.vmColaGone(c, true);
      this.broadcast({ t: 'mech', k: 'vmdrink', c: c.id, id: c.o, to: t.id, a: Math.round(a), ar: this.mechOn(t) ? 1 : 0, ms: C.boost * 1000 });
      if (owner && this.vmOn(owner) && a > 0) this.mechUlt(owner, a * 100 / VM.ult.dmg); // (healing charges the ult like damage)
      return true;
    },

    // ---- E: OUT OF ORDER. a 600 HP sign wall slammed down 3.5 m in front, facing you. it eats the other side's fire
    vmWall(p, n) {
      const M = p.mech, V = M.vm, Wl = VM.wall;
      if (n < V.jam) { this.mechNo(p, 'jammed: get an ally to kick it'); return false; }
      if (n < (M.cd.wall || 0) - 150) return false;
      if (this.vmWallOf(p.id)) { this.mechNo(p, 'one wall at a time'); return false; }
      if (this.vmJam(p, n, 'wall')) return false;
      M.cd.wall = n + Wl.cd * 1000;
      const f = fwdOf(p), h = raycast([p.pos[0], p.pos[1] + 1, p.pos[2]], [f[0], 0, f[1]], Wl.at + 0.5, this.boxes), k = h ? Math.max(MECH.vending.hw + 0.4, h.t - 0.5) : Wl.at;
      const g = this.vmFloor([p.pos[0] + f[0] * k, p.pos[1] + 1, p.pos[2] + f[1] * k]) || [p.pos[0] + f[0] * k, p.pos[1], p.pos[2] + f[1] * k];
      const x2 = rng(VM.stuck), S = W(this);
      // each half of the sign stops where a building is (at the knees and at chest height): it never pokes through a wall
      const rt = [Math.cos(p.yaw), 0, -Math.sin(p.yaw)], half = (sg) => { let e = Wl.w / 2; for (const y of [0.8 * MECH.scale, Wl.h * 0.6]) { const hh = raycast([g[0], g[1] + y, g[2]], [rt[0] * sg, 0, rt[2] * sg], Wl.w / 2, this.boxes); if (hh) e = Math.min(e, hh.t - 0.15); } return r2(Math.max(0.8, e)); };
      const w = { id: ++S.nw, o: p.id, p: g.map(r2), yaw: r2(p.yaw), wl: half(-1), wr: half(1), hp: Wl.hp * (x2 ? 2 : 1), max: Wl.hp * (x2 ? 2 : 1), until: n + Wl.life * 1000, x2, hitT: 0, acc: 0 };
      S.walls.set(w.id, w);
      this.broadcast({ t: 'mech', k: 'vmwall', id: p.id, w: w.id, p: w.p, yaw: w.yaw, wl: w.wl, wr: w.wr, hp: w.hp, max: w.max, ms: Wl.life * 1000, x2: x2 ? 1 : 0 });
      if (x2) this.broadcast({ t: 'mech', k: 'vmstuck', id: p.id, w: 'wall' });
      this.mechEn(p, true);
      return true;
    },
    vmWallOf(id) { for (const w of W(this).walls.values()) if (w.o === id) return w; return null; },
    vmWallsOf(id, why) { for (const w of [...W(this).walls.values()]) if (w.o === id) this.vmWallGone(w, why); },
    vmWallGone(w, why, by) { if (!W(this).walls.delete(w.id)) return; this.broadcast({ t: 'mech', k: 'vmwallx', w: w.id, id: w.o, why, by: by ? by.id : 0 }); },
    // the wall takes a hit instead of whoever's behind it: sparks and a clang (batched, so a shotgun is one clang)
    vmWallHurt(w, amt, at, by) {
      if (!(amt > 0)) amt = 1;
      w.hp -= amt; w.acc += amt;
      const n = now();
      if (w.hp <= 0) { this.broadcast({ t: 'mech', k: 'vmwhit', w: w.id, hp: 0, a: Math.round(w.acc), p: at.map(r2) }); this.vmWallGone(w, 'break', by); return; }
      if (n - w.hitT > 70) { w.hitT = n; this.broadcast({ t: 'mech', k: 'vmwhit', w: w.id, hp: Math.round(w.hp), a: Math.round(w.acc), p: at.map(r2) }); w.acc = 0; }
    },
    // does this wall stop what `shooter` fires? the owner's side shoots through it (a shooter who left: it stops it)
    vmStops(shooter, w) { if (shooter && shooter.id === w.o) return false; const o = this.players.get(w.o); return !(o && shooter && this.friendly(o, shooter)); },
    // the first wall on a-b that stops the shooter's fire: { wall, s (fraction of a-b), at }
    vmFirst(shooter, a, b) {
      const S = this._vm;
      if (!S || !S.walls.size) return null;
      let best = null;
      for (const w of S.walls.values()) {
        if (!this.vmStops(shooter, w)) continue;
        const x = vmWallCross(w, a, b);
        if (x && (!best || x.s < best.s)) best = { wall: w, s: x.s, at: x.at };
      }
      return best;
    },
    // room.js applyHitscan: a gun's hit lands only if no enemy wall is in the way. the shot goes along the shooter's
    // aim to where it meets the target's boxes (a shot past the wall's edge still lands); no meeting point (lag):
    // straight at their middle. the wall takes what the shot would have dealt
    vmBlockShot(p, t, wid, n, h, d, mul) {
      if (!this._vm || !this._vm.walls.size || !p || !t) return false;
      const e = [p.pos[0], p.pos[1] + PH.eye, p.pos[2]];
      let far = null;
      for (const hb of this.mechHitBoxes(t) || playerBoxes(t.pos)) { const r = rayBox(e, d, hb, 400); if (r && (far == null || r.t < far)) far = r.t; }
      const end = far != null ? [e[0] + d[0] * far, e[1] + d[1] * far, e[2] + d[2] * far] : this.mechCenter(t);
      const x = this.vmFirst(p, e, end);
      if (!x) return false;
      const w = WEAPONS[wid] || {};
      this.vmWallHurt(x.wall, (Number.isFinite(w.dmg) ? w.dmg : 10) * Math.max(1, n || 1) * (Number.isFinite(mul) ? mul : 1), x.at, p);
      return true;
    },
    // server/mech.js mechRay: a mech's hitscan stops at an enemy wall (which takes dmg)
    vmRayWall(p, o, d, len) { return this.vmFirst(p, o, [o[0] + d[0] * len, o[1] + d[1] * len, o[2] + d[2] * len]); }, // (the shooter hurts it: mechGun / vmCoin, once nothing nearer was hit)
    // a blast at `a` reaching `b`: an enemy wall in between takes it instead (explodeAt, the chicken, the rig's missiles)
    vmShield(owner, a, b) { return !!this.vmFirst(owner || null, a, b); },
    // the point just in front of the sign on the side something came from (prev): where it goes off / splats
    vmFace(x, prev) { const d = [prev[0] - x.at[0], prev[1] - x.at[1], prev[2] - x.at[2]], l = Math.hypot(d[0], d[1], d[2]) || 1, k = Math.min(0.3, l * 0.5); return [x.at[0] + d[0] / l * k, x.at[1] + d[1] / l * k, x.at[2] + d[2] / l * k]; },
    // room.js tickProjectiles: anything thrown or fired through an enemy wall stops there (grenades bounce off it)
    vmProj(pr, prev, owner) {
      const x = this.vmFirst(owner || null, prev, pr.p);
      if (!x) return false;
      const w = WEAPONS[pr.k] || {}, Wl = x.wall;
      if (pr.k === 'frag' || pr.k === 'smokegren' || pr.k === 'duck') { // off the sign and back the way it came
        const fx = -Math.sin(Wl.yaw), fz = -Math.cos(Wl.yaw), vn = pr.v[0] * fx + pr.v[2] * fz, sg = vn > 0 ? 1 : -1;
        pr.v[0] -= 1.6 * vn * fx; pr.v[2] -= 1.6 * vn * fz;
        pr.p = [x.at[0] - sg * fx * 0.2, x.at[1], x.at[2] - sg * fz * 0.2];
        this.broadcast({ t: 'pu', id: pr.id, p: pr.p.map(r2), v: pr.v.map(r2) });
        this.vmWallHurt(Wl, 5, x.at, owner);
        return true;
      }
      pr.p = this.vmFace(x, prev);
      this.vmWallHurt(Wl, Number.isFinite(w.dmg) ? w.dmg : 15, x.at, owner);
      if (pr.k === 'chicken') { this.projectiles.delete(pr.id); this.explode(pr); return true; } // (it goes off on the sign's face: the blast stops at the sign, vmShield)
      if (pr.k === 'banana') { const g = this.vmFloor(pr.p); this.removeProj(pr); if (g && this.makePeel) this.makePeel([pr.p[0], g[1], pr.p[2]], pr.o); return true; } // (it slides down the sign: a peel at its foot)
      this.broadcast({ t: 'fx', k: 'thwack', p: pr.p.map(r2), n: 0 }); // SPLAT on the sign
      this.removeProj(pr, { b: 1 });
      return true;
    },

    // ---- Q: RESTOCK (a full ult). every ally within 15 m (you too): 250 armour. on foot that's the mode's armour (the
    // royale / island vest, up to its max); with no armour in the mode, an overheal. mechs: armour back (up to its max),
    // full energy, every cooldown cleared (not the ult); a vending machine's cans refilled
    vmRestock(p, n) {
      const M = p.mech, V = M.vm, R = VM.restock;
      if ((M.ult || 0) < 100) { this.mechNo(p, 'ultimate not ready'); return false; }
      if (n < V.jam) { this.mechNo(p, 'jammed: get an ally to kick it'); return false; }
      M.ult = 0; V.stockT = n;
      const c = this.mechCenter(p), l = [];
      for (const t of this.players.values()) {
        if (!t.alive || t.dn || (t !== p && !this.friendly(p, t)) || t.watch) continue;
        const tc = this.mechCenter(t);
        if (Math.hypot(tc[0] - c[0], tc[1] - c[1], tc[2] - c[2]) > R.r) continue;
        let a = 0;
        if (this.mechOn(t)) {
          const T = t.mech, b = t.body;
          if (b) { a = Math.max(0, Math.min(R.armour, b.max - b.hp)); b.hp += a; this.bodyFlush(t, true); }
          T.E.v = MECH.energy.max; T.E.t = 0; T.E.at = n;
          T.cd = {}; if (T.vm) { T.vm.ch.n = VM.cola.charges; T.vm.ch.t = n; }
          this.mechEn(t, true);
        } else if (t.br) {
          a = Math.max(0, Math.min(R.armour, BR.armor.max - t.br.armor)); t.br.armor += a;
          if (this.brLoadout) this.brLoadout(t); else if (!t.isBot) send(t, { t: 'brar', ar: Math.round(t.br.armor) });
        } else { a = Math.max(0, Math.min(R.armour, R.hp - t.hp)); this.heal(t, a, R.hp); }
        l.push([t.id, Math.round(a)]);
      }
      this.broadcast({ t: 'mech', k: 'vmstock', id: p.id, p: p.pos.map(r2), r: R.r, l });
      this.mechEn(p, true);
      return true;
    },

    // ---- every tick: colas (drinking, going flat), walls (time's up), allied bots kicking jammed machines, late joiners
    vmWorld(n, dt) {
      const S = this._vm;
      if (!S) return;
      const C = VM.cola;
      for (const c of [...S.colas.values()]) {
        const o = this.players.get(c.o);
        if (!o || n > c.until) { this.vmColaGone(c); continue; }
        for (const t of this.players.values()) {
          if (!t.alive || t.dn || t.watch || (t.ai && t.ai.dummy)) continue;
          if (t.id === c.o ? n - c.born < C.mine * 1000 : !this.friendly(o, t)) continue; // (enemies can't drink it; yours after a moment)
          const m = this.mechOn(t), dy = t.pos[1] - c.p[1];
          if (hdist(t.pos, c.p) > (m ? MECH[t.mech.f].hw + C.reach * 0.6 : C.reach) || dy < -1.5 || dy > 2) continue;
          if (m ? !(t.body && t.body.hp < t.body.max) : t.hp >= 100) continue; // (full up: you walk past it)
          if (this.vmDrink(c, t, o, n)) break;
        }
      }
      for (const w of [...S.walls.values()]) if (n > w.until || !this.players.has(w.o)) this.vmWallGone(w, 'time');
      // a jammed machine: an allied bot on foot in reach gives it a kick (after a beat)
      for (const p of this.players.values()) {
        if (!this.vmOn(p) || !(p.mech.vm.jam > n)) continue;
        const V = p.mech.vm;
        for (const b of this.players.values()) {
          if (!b.isBot || !b.alive || b.mech || b === p || !this.friendly(b, p) || (b.ai && b.ai.dummy)) continue;
          if (hdist(b.pos, p.pos) > VM.jam.reach + VM.hw - 0.3) continue;
          if (!V.kickT) V.kickT = n + 300 + Math.random() * 500;
          else if (n >= V.kickT) { V.kickT = 0; this.vmKick(b, p, n); }
          break;
        }
      }
      if ((S.colas.size || S.walls.size) && n - S.listT > 2000) { // late joiners (and anyone who missed an event) catch up
        S.listT = n;
        this.broadcast({ t: 'mech', k: 'vmlist', c: [...S.colas.values()].map((c) => [c.id, c.o, ...c.p, Math.round(c.until - n)]),
          w: [...S.walls.values()].map((w) => [w.id, w.o, ...w.p, w.yaw, Math.round(w.hp), w.max, Math.round(w.until - n), w.x2 ? 1 : 0, w.wl, w.wr]) });
      }
    },

    // ---- bots: the support. stick near allies, coin enemies in sight, dispense when it or an ally is hurt (lobbed at
    // them), wall off whoever's shooting, RESTOCK a crowd (or itself when it's low). jammed: waddle to an ally for a kick
    vmBot(b, think, dt, n) {
      const M = b.mech, V = M.vm, v = b.vel, ai = b.ai, F = VM, B = M.bai || (M.bai = { nextCoin: 0, dispT: 0, orbit: Math.random() < 0.5 ? 1 : -1 });
      const easy = ai.diff === 'easy' ? 0.5 : 1;
      let t = this.players.get(ai.target);
      if (t && (!t.alive || this.friendly(b, t))) t = null;
      const e = slotOf(b), tc = t ? this.mechCenter(t) : null, dv = t ? [tc[0] - e[0], tc[1] - e[1], tc[2] - e[2]] : null;
      const dist = t ? Math.hypot(dv[0], dv[1], dv[2]) : 1e9, flat = t ? hdist(t.pos, b.pos) : 1e9, vis = !!(t && clear(e, tc, this.boxes));
      // the squad: the nearest ally, the most hurt one close by, how many a RESTOCK would reach
      let near = null, nd = 1e9, foot = null, fd = 1e9, hurt = null, hk = 1, crowd = 0;
      for (const o of this.players.values()) {
        if (o === b || !o.alive || o.watch || !this.friendly(b, o) || (o.ai && o.ai.dummy)) continue;
        const d = Math.hypot(o.pos[0] - b.pos[0], o.pos[1] - b.pos[1], o.pos[2] - b.pos[2]);
        if (d < nd) { nd = d; near = o; }
        if (!o.mech && d < fd) { fd = d; foot = o; } // (only someone on foot can kick it)
        if (d <= F.restock.r - 1) crowd++;
        const k = this.mechOn(o) ? (o.body ? o.body.hp / o.body.max : 1) : o.hp / 100;
        if (k < 0.7 && d < 16 && k < hk) { hk = k; hurt = o; }
      }
      const me = b.body ? b.body.hp / b.body.max : 1;
      const face = (q) => { const dx = q[0] - b.pos[0], dz = q[2] - b.pos[2]; if (Math.hypot(dx, dz) > 0.3) b.yaw = Math.atan2(-dx, -dz); };
      if (t && vis) { face(t.pos); b.pitch = Math.atan2(dv[1], Math.hypot(dv[0], dv[2])); }
      else if (near) face(near.pos);
      const free = n >= V.jam;
      // ---- the moves
      if (free && (M.ult || 0) >= 100 && (crowd >= 2 || me < 0.35 || (crowd >= 1 && hk < 0.4))) this.vmRestock(b, n);
      const shot = (M.hitT && n - M.hitT < 700) || (near && nd < 12 && near.lastAttackT && n - near.lastAttackT < 700 && near.lastAttacker !== b.id);
      if (free && t && vis && shot && flat > 5 && n >= (M.cd.wall || 0) && !this.vmWallOf(b.id) && Math.random() < dt * 4 * easy) { face(t.pos); this.vmWall(b, n); }
      if (free && n - B.dispT > 1400 && vmCharges(V.ch, n) > 0 && (me < 0.6 || hurt)) {
        B.dispT = n;
        const y0 = b.yaw;
        if (hurt) face(hurt.pos);
        this.vmDispense(b, hurt && hdist(hurt.pos, b.pos) < F.cola.toss + 1.5 ? hurt.pos.slice() : null, n);
        b.yaw = y0;
      }
      if (t && vis && dist < F.coin.range && n >= B.nextCoin) {
        B.nextCoin = n + 1000 / F.coin.rate + (ai.diff === 'easy' ? 90 : 0);
        const err = ai.diff === 'hard' ? 0.02 : ai.diff === 'easy' ? 0.07 : 0.04, r = () => (Math.random() - 0.5) * err * 2;
        const d = [dv[0] / dist + r(), dv[1] / dist + r(), dv[2] / dist + r()], l = Math.hypot(...d);
        this.vmCoin(b, d.map((x) => x / l), n);
      }
      // ---- where to walk: jammed = to the nearest ally (kick me); else stay with the squad, hold mid range on the enemy
      let goal = null, stop = 3;
      if (!free && (foot || near)) { goal = (foot || near).pos; stop = 1.8; }
      else if (hurt && hdist(hurt.pos, b.pos) > F.cola.toss) { goal = hurt.pos; stop = F.cola.toss - 1; }
      else if (near && nd > 10) { goal = near.pos; stop = 6; }
      else if (t && (flat > (near ? 20 : 15) || !vis)) { goal = t.pos; stop = 12; }
      let wx = think.wx, wz = think.wz;
      if (goal) { const dx = goal[0] - b.pos[0], dz = goal[2] - b.pos[2], l = Math.hypot(dx, dz) || 1; if (l > stop) { wx = dx / l; wz = dz / l; } else { wx = 0; wz = 0; } }
      else if (t) { const dx = t.pos[0] - b.pos[0], dz = t.pos[2] - b.pos[2], l = Math.hypot(dx, dz) || 1; wx = -dz / l * B.orbit; wz = dx / l * B.orbit; if (Math.random() < dt * 0.3) B.orbit *= -1; } // strafe round them
      const sp = F.speed * (n < (b.fastUntil || 0) ? QUIZ.fast : 1) * (easy < 1 ? 0.85 : 1);
      v[1] -= F.grav * dt;
      if (b.onGround && ((t && t.pos[1] - b.pos[1] > 2.5 && flat < 20) || (goal && goal[1] - b.pos[1] > 2)) && Math.random() < dt * 2) { v[1] = F.hop; b.onGround = false; } // a little hop up a step
      this.mechBotWalk(b, v, wx, wz, wx || wz ? sp : 0, F, dt, false);
      b.f = FLAGS.MECH | KIT.vending.flags.call(this, b, M, 0, n);
      if (v[1] < (M.minVy || 0)) M.minVy = v[1];
      if (b.onGround && M.minVy < MECH.stomp.vy) { M.minVy = 0; this.mechStomp(b, n); } else if (b.onGround) M.minVy = 0;
      if (b.onGround) b.ground = b.pos.slice();
    },
  });
}
