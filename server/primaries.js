// The new primaries, the server half. Mixed into Room by installPrimaries (this = the room); server.js calls these
// from one-line hooks. The server owns all of it:
//   Nail Gun: counts each shooter's nails per victim; enough in a short window pins them to the wall behind them.
//   Tennis Ball Launcher: simulates every ball against the map boxes, counts bounces, scales the damage by them.
//   Shopping Cart Cannon: simulates carts (fly, roll, park, ridden), ploughs people, and parked carts are real boxes
//   (bullets and players stop on them) through a per-room box list that adds them on top of the map's.
import { WEAPONS } from '../shared/weapons.js';
import { NAILS, stepBall, ballDmg, CART, cartBox, boxHit, stepCart, ploughOf, yawOfV } from '../shared/primaries.js';
import { raycast, playerOverlap, playerBoxes } from '../shared/physics.js';

let H; // helpers from server.js
const T = WEAPONS.tennis, CW = WEAPONS.cart;
const hyp2 = (v) => Math.hypot(v[0], v[2]);
const plain = (c) => ({ id: c.id, p: c.p.map(H.r2), v: c.v.map(H.r2), y: H.r2(c.yaw), st: c.st, o: c.o, r: c.rider || 0, s: c.solid ? 1 : 0 });

export function installPrimaries(Room, helpers) {
  H = helpers;
  H.REC_T.add('pin'); // pins in killcams and the play of the round (carts ride along in the frames' projectile list)
  // parked carts are solid: the room's boxes are the map's plus theirs (rebuilt only when a cart parks or leaves)
  // (wraps the room's own getter: Zombies swaps in its shutter boxes there)
  const own = Object.getOwnPropertyDescriptor(Room.prototype, 'boxes'), baseOf = own && own.get ? own.get : function () { return this.map.boxes; };
  Object.defineProperty(Room.prototype, 'boxes', {
    configurable: true,
    get() {
      const base = baseOf.call(this), cb = this.cartBoxes;
      if (!cb || !cb.list.length) return base;
      if (cb.base !== base || !cb.all) { cb.base = base; cb.all = base.concat(cb.list); }
      return cb.all;
    },
  });
  Object.assign(Room.prototype, prims);
}

const prims = {
  // ---------------------------------------------------------------- Nail Gun
  // after a nail gun hit lands (applyHitscan): n nails just went in from p
  nailHit(p, t, n, d) {
    if (!t || !t.alive || t === p) return;
    const now = H.now(), N = NAILS;
    if (t.reverseUntil > now) return; // a reverse card sent the nails back: nobody gets pinned
    const list = (t.nails ||= []).filter((x) => now - x.at < N.win * 1000);
    for (let i = 0; i < n; i++) list.push({ at: now, by: p.id });
    t.nails = list.slice(-24);
    if (now < (t.pinUntil || 0) + N.safe * 1000 || this.rigOn(t) || this.isBall(t) || t.trap) return;
    if (list.filter((x) => x.by === p.id).length < N.n) return;
    if (this.hitBlocked(t, p, 'nailgun')) return; // spawn protection, teammates, bubbles: no pin either
    t.nails = [];
    this.pinTo(t, p, d);
  },
  // stick t to the surface behind them (along the shot), lifted a bit like a poster. no wall in reach: the floor
  pinTo(t, by, d) {
    const N = NAILS, now = H.now();
    const l = Math.hypot(d[0], d[2]) || 1, dh = [d[0] / l, 0, d[2] / l];
    const c = [t.pos[0], t.pos[1] + 1.1, t.pos[2]];
    const w = raycast(c, dh, N.reach, this.boxes);
    let at = t.pos.slice(), nrm = [0, 1, 0];
    if (w && w.normal[1] === 0) {
      const off = 0.42;
      const cand = [w.point[0] + w.normal[0] * off, t.pos[1] + N.lift, w.point[2] + w.normal[2] * off];
      if (!playerOverlap(cand, this.boxes)) { at = cand; nrm = w.normal; }
      else { cand[1] = t.pos[1]; if (!playerOverlap(cand, this.boxes)) { at = cand; nrm = w.normal; } }
    }
    t.pinUntil = now + N.dur * 1000; t.pinAt = at;
    t.knockT = now; // EPIC: hanging on a wall isn't moving
    if (t.isBot) { if (!(t.ai.dummy && t.ai.dummy.move)) { t.ai.hook = null; t.g = null; t.ai.route = null; t.held = { at, until: t.pinUntil }; } }
    this.broadcast({ t: 'pin', id: t.id, by: by.id, p: at.map(H.r2), n: nrm, d: dh.map(H.r2), dur: N.dur });
  },

  // ---------------------------------------------------------------- Tennis Ball Launcher
  // one tick of a ball: real bounces off the boxes (counted), a hit = damage that grows with every bounce
  tennisStep(pr, dt, n) {
    const owner = this.players.get(pr.o), prev = pr.p.slice();
    pr.b ||= 0;
    const st = stepBall(pr, dt, this.boxes, T.grav, T.minBounce, T.bounce);
    if (this.parryProj(pr, prev)) return; // batted back by a katana parry (it's theirs now)
    const age = (n - pr.born) / 1000;
    // after its first bounce your own ball can bonk you too (no damage, just the shove: bank shots have a cost)
    const vs = this.sweep(prev, pr.p, pr.r, (t) => (t.id === pr.o && (pr.b === 0 || age < 0.25)) || (this.friendly(owner, t) && !t.trap));
    if (vs.length) {
      const v = vs[0], d = H.norm(pr.v) || [0, 0, -1];
      pr.p = v.at;
      this.removeProj(pr, { tb: pr.b, h: 1 });
      if (v.t.id === pr.o) { this.knock(v.t, [d[0] * T.kb, T.kbUp, d[2] * T.kb], 'tennis'); return; }
      const head = v.at[1] > v.t.pos[1] + 1.62;
      const k = 1 + 0.15 * pr.b;
      this.hurt(v.t, owner || null, 'tennis', ballDmg(pr.b) * (head ? 1.5 : 1), [d[0] * T.kb * k, T.kbUp, d[2] * T.kb * k], { hs: head });
      return;
    }
    if (st.n) {
      pr.b += st.n;
      if (pr.b > T.bounces) { this.removeProj(pr, { tb: pr.b }); return; } // the 6th bounce: dead ball
      this.broadcast({ t: 'pu', id: pr.id, p: pr.p.map(H.r2), v: pr.v.map(H.r2), b: pr.b });
    }
    if (age > T.life || pr.p[1] < this.map.killY || (Math.hypot(...pr.v) < 0.5 && age > 1)) this.removeProj(pr);
  },

  // ---------------------------------------------------------------- Shopping Cart Cannon
  fireCart(p, o, d) {
    const n = H.now();
    if (n - (p.lastFire.cart || 0) < CW.cd * 750) return;
    p.lastFire.cart = n;
    if (p.isBot) { const l = Math.hypot(d[0], d[2]) || 1; d = [d[0] / l * 0.995, -0.1, d[2] / l * 0.995]; } // bots bowl it along the floor at you (it rolls)
    const carts = (this.carts ||= new Map());
    const mine = [...carts.values()].filter((c) => c.o === p.id);
    if (mine.length >= CART.mine) this.dropCart(mine[0], 'old');
    if (carts.size >= CART.max) this.dropCart(carts.values().next().value, 'old');
    const wh = raycast(o, d, 1.3, this.boxes), off = wh ? Math.max(0, wh.t - 0.7) : 1.0;
    let pos = [o[0] + d[0] * off, o[1] + d[1] * off - 0.75, o[2] + d[2] * off];
    if (playerOverlap(pos, this.boxes)) pos = p.pos.slice(); // shooting point blank into a wall: it drops at your feet
    const c = {
      id: (this.nextCart = (this.nextCart || 0) + 1), k: 'cart', o: p.id, p: pos, born: n, st: 'fly', ground: false, fall: 0, restT: 0, sync: 0,
      v: [d[0] * CW.speed + p.vel[0] * 0.3, d[1] * CW.speed + CW.up + Math.max(0, p.vel[1]) * 0.3, d[2] * CW.speed + p.vel[2] * 0.3],
      yaw: Math.atan2(-d[0], -d[2]), hit: new Map(), solid: false, rider: 0,
    };
    c.ef = p.pos ? this.epicState(p) : null;
    carts.set(c.id, c);
    this.broadcast({ t: 'cart', k: 's', ...plain(c) });
  },
  dropCart(c, why) {
    if (!c || !this.carts || !this.carts.delete(c.id)) return;
    if (c.solid) this.cartSolid(c, false);
    if (c.rider) { const r = this.players.get(c.rider); if (r) r.ride = 0; }
    this.broadcast({ t: 'cart', k: 'x', id: c.id, p: c.p.map(H.r2), why });
  },
  clearCarts() {
    if (this.carts && this.carts.size) this.broadcast({ t: 'carts', l: [] }); // everyone's carts go too
    if (this.carts) this.carts.clear();
    this.cartBoxes = null;
    for (const p of this.players.values()) p.ride = 0;
  },
  cartSolid(c, on) {
    const cb = (this.cartBoxes ||= { list: [], all: null, base: null });
    cb.list = cb.list.filter((b) => b.cart !== c.id);
    c.solid = on;
    if (on) { const b = cartBox(c); b.mat = 'metal'; b.cart = c.id; cb.list.push(b); }
    cb.all = null; // next .boxes builds a fresh list (and grid)
  },
  // is anyone standing inside where this cart wants to park?
  cartBlocked(c) {
    const b = cartBox(c);
    for (const t of this.players.values()) {
      if (!t.alive) continue;
      for (const hb of playerBoxes(t.pos)) if (boxHit(b, hb)) return true;
    }
    return false;
  },
  tickCarts(dt) {
    if (!this.carts || !this.carts.size) return;
    const n = H.now();
    for (const c of [...this.carts.values()]) {
      if (n - c.born > CW.life * 1000 || c.p[1] < this.map.killY) { this.dropCart(c, 'gone'); continue; }
      const was = c.st;
      if (c.st === 'ride') {
        const r = this.players.get(c.rider);
        const far = r && Math.hypot(r.pos[0] - c.p[0], r.pos[1] - CART.top - c.p[1], r.pos[2] - c.p[2]) > 3.5; // they left it without saying so
        if (!r || !r.alive || r.ride !== c.id || this.rigOn(r) || this.isBall(r) || r.trap || this.pinned(r, n) || far) { this.cartLetGo(c, [0, 0, 0]); continue; }
        const np = [r.pos[0], r.pos[1] - CART.top, r.pos[2]], step = Math.hypot(np[0] - c.p[0], np[1] - c.p[1], np[2] - c.p[2]);
        if (step > 1e-4 || n - (c.mvT || 0) > 400) { // a new position from the rider (snapshots come slower than ticks)
          const moved = step / Math.max(0.03, (n - (c.mvT || n - 50)) / 1000);
          c.p = np; c.mvT = n;
          c.v = r.vel.slice(0, 3).map((x) => Math.max(-CART.ride.maxSp, Math.min(CART.ride.maxSp, x)));
          // it only ploughs as hard as it really moved (a rider who says they're fast but stands still, or jumps 10 m, does nothing)
          const say = Math.hypot(...c.v);
          if (moved > CART.ride.maxSp * 2) c.v = [0, 0, 0];
          else if (say > moved * 1.4 + 1.5) c.v = c.v.map((x) => x * ((moved * 1.4 + 1.5) / say));
        }
        c.yaw = yawOfV(c.v, c.yaw);
        this.plough(c, r, n);
      } else if (c.st === 'fly' || c.st === 'roll') {
        const res = stepCart(c, dt, this.boxes);
        if (res.ground) c.st = 'roll';
        const att = this.players.get(c.o) || null;
        this.plough(c, att, n);
        if (c.st === 'roll' && hyp2(c.v) < CART.restSp) {
          c.restT += dt;
          if (c.restT > CART.restT) { c.st = 'rest'; c.v = [0, 0, 0]; }
        } else c.restT = 0;
      } else if (c.st === 'rest') {
        if (!c.solid && !this.cartBlocked(c)) { this.cartSolid(c, true); this.broadcast({ t: 'cart', k: 'u', ...plain(c) }); }
        // the floor went away under it (a door, a lift, a shove): roll again
        if (!raycast([c.p[0], c.p[1] + 0.2, c.p[2]], [0, -1, 0], 0.35, this.map.boxes)) { this.cartMove(c, [0, 0, 0]); }
      }
      c.sync -= dt;
      if (c.st !== was || (c.st !== 'rest' && c.sync <= 0)) { c.sync = CART.sync; this.broadcast({ t: 'cart', k: 'u', ...plain(c) }); }
    }
    if ((this.cartSyncT = (this.cartSyncT || 0) + dt) > 2) { // everyone gets the full list now and then (joiners, missed packets)
      this.cartSyncT = 0;
      this.broadcast({ t: 'carts', l: [...this.carts.values()].map(plain) });
    }
  },
  cartMove(c, v) { // parked -> rolling (not solid any more)
    if (c.solid) this.cartSolid(c, false);
    c.st = 'roll'; c.v = v.slice(); c.ground = false; c.restT = 0;
  },
  cartLetGo(c, v) {
    const r = this.players.get(c.rider);
    if (r && r.ride === c.id) r.ride = 0;
    c.rider = 0;
    const V = (v || [0, 0, 0]).map((x) => Math.max(-CART.ride.maxSp, Math.min(CART.ride.maxSp, Number.isFinite(x) ? x : 0)));
    this.cartMove(c, V);
    this.broadcast({ t: 'cart', k: 'u', ...plain(c) });
  },
  // a moving cart runs over whoever it touches: harder the faster it goes
  plough(c, att, n) {
    const sp = Math.hypot(c.v[0], c.v[1] * 0.5, c.v[2]), P = ploughOf(sp);
    if (!P || (this.round && this.round.over)) return;
    const b = cartBox(c, 0.12), age = (n - c.born) / 1000;
    const dir = H.norm([c.v[0], 0, c.v[2]]) || [0, 0, -1];
    let hits = 0;
    for (const t of this.players.values()) {
      if (!t.alive || t.id === c.rider || (t.id === c.o && age < CART.ownerSafe + (c.st === 'fly' ? 0.4 : 0))) continue;
      if (n - (c.hit.get(t.id) || 0) < CART.hitCd) continue;
      if (!playerBoxes(t.pos).some((hb) => boxHit(b, hb))) continue;
      c.hit.set(t.id, n);
      hits++;
      const kb = [dir[0] * P.kb, P.up, dir[2] * P.kb];
      if (!att || t === att) { if (t.isBot || n - t.spawnT >= 1200) this.knock(t, kb, 'cart'); continue; } // nobody to blame (they left) / your own cart: just the shove (not on someone who just spawned)
      this.epicProj = c; // a kill counts from where it was fired
      this.hurt(t, att, 'cart', P.dmg, kb);
      this.epicProj = null;
    }
    if (hits) {
      this.broadcast({ t: 'fx', k: 'plough', p: [c.p[0], c.p[1] + 0.6, c.p[2]].map(H.r2), n: hits, s: H.r2(sp) });
      if (c.st !== 'ride') for (const i of [0, 2]) c.v[i] *= CART.slow;
    }
  },
  // { t: 'cart', k: 'ride', id } hop in (standing on it / landing on it) · { t: 'cart', k: 'off', v } hop out
  onCart(p, m) {
    const n = H.now();
    if (!this.carts) return;
    if (m.k === 'off') { // never rate limited: a dropped 'off' would leave the cart glued to you
      const c = this.carts.get(p.ride);
      if (!c || c.rider !== p.id) { p.ride = 0; return; }
      // it keeps rolling the way you were going, but never faster than the server saw the cart go
      const v = H.vec3(m.v) || p.vel, sp = Math.hypot(v[0], v[2]), cap = Math.hypot(c.v[0], c.v[2]) + 2;
      this.cartLetGo(c, sp > cap ? [v[0] * cap / sp, 0, v[2] * cap / sp] : [v[0], 0, v[2]]);
      return;
    }
    if (n - (p.cartMsgT || 0) < 150 || !p.alive) return; // hop-ins: a few a second at most
    p.cartMsgT = n;
    if (m.k !== 'ride' || !Number.isInteger(m.id) || p.ride || this.rigOn(p) || this.isBall(p) || p.trap || n < (p.pinUntil || 0)) return;
    const c = this.carts.get(m.id);
    if (!c || c.rider || c.st === 'fly' || hyp2(c.v) > 14) return;
    const top = [c.p[0], c.p[1] + CART.top, c.p[2]];
    if (Math.hypot(p.pos[0] - top[0], p.pos[2] - top[2]) > CART.ride.reach + 0.6 || Math.abs(p.pos[1] - top[1]) > CART.ride.upTol + 0.6) return;
    if (c.solid) this.cartSolid(c, false);
    c.st = 'ride'; c.rider = p.id; p.ride = c.id;
    this.broadcast({ t: 'cart', k: 'u', ...plain(c) });
  },
  cartsFor(p) { if (this.carts && this.carts.size) H.send(p, { t: 'carts', l: [...this.carts.values()].map(plain) }); },
  // the play of the round + killcams draw carts like projectiles (kind 'cartp', the 6th slot carries the yaw)
  cartRec() { return this.carts && this.carts.size ? [...this.carts.values()].map((c) => ['c' + c.id, 'cartp', H.r2(c.p[0]), H.r2(c.p[1]), H.r2(c.p[2]), H.r2(c.yaw)]) : []; },
  // bots: no riding, but they hop off anything weird. a pin holds people still (bots get t.held; humans' clients obey 'pin')
  pinned(t, n = H.now()) { return n < (t.pinUntil || 0); },
};
