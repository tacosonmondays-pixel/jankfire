// BOARD GAME NIGHT minigames 11-15 (docs/party/DESIGN.md 3, 3.1, 3.2, 4.4), the server half:
//   THE BIG GUY (3v1, tdm): the leader climbs into an overdrive rig every life, and their kills count x3.
//   BOSS: THE LANDLORD / THE NIGHT MANAGER (4 vs BOSS, tdm): a 5th player on team 2, a bot already in his mech
//     (mechSpawnIn) with boosted armour. his armour breaking ends it (the four win, most damage = MVP); the clock is his.
//   BUMPER CARTS (bgcarts, Crate): everyone rides a shopping cart. rams don't hurt, they throw you out of your cart and
//     toward the edge; off the edge you're out (2v2: 3 team lives). a boost on click, judged here. bots drive carts too.
//   DUCK CATCH (bgducks, Platform): rubber ducks fall where the server says, and it judges every catch from where it has
//     you (no grabbing from metres away). a slap makes you drop 3. every 10 s a cursed duck lands as a real black hole and
//     whoever it pulls in loses half their pile.
// installBgnMini(Room, H) adds the bgm* methods and wraps a few Room methods; the wraps only act while one of these is on.
// room.bgm = this minigame's state (null otherwise). piles, falls, outs and damage are by seat, so a bot that takes a
// seat over mid-game keeps them. (room.js imports this through server/bgn.js: browser-safe, shared/ imports only)
import { BGN_MINI, BGN_NAMES } from '../shared/bgn.js';
import { CART } from '../shared/primaries.js';
import { MECH, mechRoom } from '../shared/mech.js';
import { BODY } from '../shared/bodyhp.js';
import { WEAPONS, BOT_DIFF } from '../shared/weapons.js';
import { TEAMS, DUCKRAIN } from '../shared/modes.js';
import { raycast, movePlayer } from '../shared/physics.js';

const E = (typeof process !== 'undefined' && process.env) || {};
const K = { peace: !!E.JF_BGN_PEACE }; // test knob: passive bots (carts: they drive about and never ram, do they keep on the box? ducks: no errands, no slaps)
export const BGM_KNOBS = K;
const CM = BGN_MINI.carts, DK = BGN_MINI.ducks, BS = BGN_MINI.boss;
const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const hd = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);
const wrapA = (a) => { while (a > Math.PI) a -= Math.PI * 2; while (a < -Math.PI) a += Math.PI * 2; return a; };
const unit = (x, z) => { const l = Math.hypot(x, z); return l > 1e-6 ? [x / l, z / l] : [0, -1]; };
const cartMsg = (c) => ({ id: c.id, p: c.p.map(r2), v: c.v.map(r2), y: r2(c.yaw), st: c.st, o: c.o, r: c.rider || 0, s: c.solid ? 1 : 0 });
// Room.prototype[k] = fn(base, ...args), this = the room
function wrap(P, k, fn) {
  const base = P[k];
  if (typeof base !== 'function') throw new Error('bgnmini: no Room.' + k);
  P[k] = function (...a) { return fn.call(this, base, ...a); };
}

export function installBgnMini(Room, H) {
  const P = Room.prototype;
  Object.assign(P, {
    // ---------------------------------------------------------------- start / end (from server/bgn.js)
    bgmGo(mg, def) {
      this.bgm = null;
      const k = def.boss ? 'boss' : mg.id === 'bigguy' ? 'bigguy' : def.game === 'bgcarts' ? 'carts' : def.game === 'bgducks' ? 'ducks' : null;
      if (!k) return;
      const n = now(), S = this.bgm = { k, t0: n, mg };
      if (k === 'carts') {
        Object.assign(S, { out: new Set(), outAt: {}, outN: 0, falls: {}, kos: {}, pool: { 1: CM.lives, 2: CM.lives }, lives: Object.fromEntries(mg.seats.map((i) => [i, CM.solo])) }, this.bgmBox());
        for (const p of this.fighters()) { p.ride = 0; p.bgOffT = 0; p.bgBoostT = 0; if (p.alive) this.bgmMount(p); }
      } else if (k === 'ducks') Object.assign(S, { ducks: new Map(), id: 0, pile: {}, next: n + 1200, curseAt: n + DK.cursedEvery, curses: [], curseT: {} });
      else if (k === 'boss') this.bgmBossIn(def);
      this.bgnEv('mini', { x: this.bgmInfo() });
    },
    bgmEnd(mg, r) {
      const S = this.bgm;
      if (!S) return;
      if (S.k === 'carts') r.x = { falls: S.falls, kos: S.kos, out: [...S.out], pool: mg.teams ? S.pool : null };
      else if (S.k === 'ducks') { r.x = { pile: S.pile }; this.bgnEv('duckx', { all: 1 }); }
      else if (S.k === 'boss') { const b = this.players.get(S.boss); if (b) this.remove(b); } // he goes home
      for (const p of this.players.values()) { p.ride = 0; p.bgOffT = 0; }
      this.bgm = null;
    },
    // what clients get (bgnInfo's mg.x): enough to draw the HUD after a join
    bgmInfo() {
      const S = this.bgm;
      if (!S) return null;
      if (S.k === 'carts') return { k: 'carts', out: [...S.out], pool: S.mg.teams ? S.pool : null, lives: S.mg.teams ? null : S.lives, falls: S.falls };
      if (S.k === 'ducks') return { k: 'ducks', pile: S.pile };
      if (S.k === 'boss') return { k: 'boss', id: S.boss, hp: S.lastHp ?? S.max ?? 0, max: S.max || 0, down: S.down ? 1 : 0 };
      return { k: S.k };
    },
    // 2v2 team score (bgnMgEnd): bumper carts = last team with someone in, then lives left, then rams. null = the usual
    bgmTeam(side, mg) {
      const S = this.bgm;
      if (!S || S.k !== 'carts') return null;
      const team = side === mg.sides[0] ? 1 : 2, alive = side.some((i) => !S.out.has(i));
      return (alive ? 1000 : 0) + S.pool[team] * 10 + side.reduce((a, i) => a + (S.kos[i] || 0), 0);
    },
    // a boss result: down = the four win, the most damage is MVP. else he does
    bgmBossRes(r, mg) {
      const S = this.bgm || {};
      r.winSide = S.down ? 0 : 1;
      r.dmg = mg.seats.map((i) => [i, Math.round((S.dmg && S.dmg[i]) || 0)]);
      const top = r.dmg.slice().sort((a, b) => b[1] - a[1])[0];
      r.mvp = S.down && top && top[1] > 0 ? top[0] : null;
    },

    // ---------------------------------------------------------------- BOSS
    bgmBossIn(def) {
      const S = this.bgm, B = this.bgn, b = this.addBot(), nm = BGN_NAMES.boss[S.mg.id];
      b.name = nm ? nm.name : 'THE BOSS'; b.ai.diff = BS.diff; b.bgBoss = true;
      b.team = 2; b.color = b.ownColor = TEAMS[2].color;
      this.broadcast({ t: 'pj', ...this.info(b) }); // (his name)
      this.broadcast({ t: 'teams', game: this.game, list: [[b.id, 2, b.color]] });
      Object.assign(S, { boss: b.id, dmg: {}, down: 0, barT: 0, mul: BS.base + BS.perHuman * B.seats.filter((s) => !s.bot).length });
      if (!this.mechSpawnIn(b, def.boss, S.mul)) console.log(`[bgn] ${this.id}: no room for ${b.name}'s mech (he fights on foot)`);
      S.max = b.body ? Math.round(b.body.max) : 100; S.lastHp = S.max;
    },
    // a bot straight into his mech, no drop (mechCall + mechLand + mechEnter, minus the fall and the shockwave): the
    // first spot with room for the whole frame. mul = his armour x the frame's
    mechSpawnIn(b, f, mul) {
      const n = now(), F = MECH[f], sp = this.map.spawns || [];
      const mid = sp.reduce((a, s) => [a[0] + s[0] / sp.length, 0, a[2] + s[2] / sp.length], [0, 0, 0]);
      const spots = sp.map((s) => s.slice()).sort((a, c) => hd(a, mid) - hd(c, mid)); // the spawn nearest the middle with room for him (well away from the edges: he falls off less)
      if (!spots.length) spots.push(b.pos.slice());
      for (const s of spots) {
        const fl = raycast([s[0], s[1] + 1, s[2]], [0, -1, 0], 4, this.boxes);
        if (!fl || fl.box.pad) continue;
        const g = [s[0], fl.point[1], s[2]];
        if (!mechRoom(g, f, this.boxes)) continue;
        const id = this.nextMech = (this.nextMech || 0) + 1, yaw = r2(Math.random() * Math.PI * 2);
        const m = { id, o: b.id, f, p: g, yaw, st: 'wait', t: n, until: n + MECH.wait * 1000, hp: F.hp };
        this.mechMap().set(id, m);
        this.broadcast({ t: 'mech', k: 'land', id, o: b.id, f, p: g.map(r2), yaw });
        b.pos = g.slice(); b.vel = [0, 0, 0];
        if (!this.mechEnter(b, n)) { this.mechGone(m, 'reset'); return false; }
        if (b.body) { b.body.hp = b.body.max = Math.round(F.hp * mul); this.bodyFlush(b, true); }
        if (this.bgm) this.bgm.home = [g[0], g[1] + 0.5, g[2]];
        return true;
      }
      return false;
    },

    // ---------------------------------------------------------------- BUMPER CARTS
    // the play area: the biggest floor at about y 0 (Crate's 30 x 30 toy box)
    bgmBox() {
      let best = null, ba = 0;
      for (const b of this.map.boxes) { const a = (b.max[0] - b.min[0]) * (b.max[2] - b.min[2]); if (a > ba && Math.abs(b.max[1]) < 1.5) { ba = a; best = b; } }
      if (!best) return { cx: 0, cz: 0, hx: 15, hz: 15, top: 0 };
      return { cx: (best.min[0] + best.max[0]) / 2, cz: (best.min[2] + best.max[2]) / 2, hx: (best.max[0] - best.min[0]) / 2, hz: (best.max[2] - best.min[2]) / 2, top: best.max[1] };
    },
    bgmFloor(p) { const S = this.bgm; return p.pos[1] > S.top - 0.6 && p.pos[1] < S.top + 3 && !!raycast([p.pos[0], p.pos[1] + 0.3, p.pos[2]], [0, -1, 0], 0.8, this.map.boxes); },
    // a fresh cart under you, you in it (players' clients climb in when they see their id on it: public/js/bgnmini.js)
    bgmMount(p) {
      const S = this.bgm, n = now();
      const fl = raycast([p.pos[0], p.pos[1] + 1.2, p.pos[2]], [0, -1, 0], 3, this.map.boxes);
      if (!fl || fl.normal[1] < 0.5) return false;
      const carts = (this.carts ||= new Map()), free = [...carts.values()].filter((c) => !c.rider);
      if (carts.size >= CART.max + 2 && free.length) this.dropCart(free[0], 'old'); // (one more ridden cart: the oldest empty one goes back to the store)
      const c = { id: this.nextCart = (this.nextCart || 0) + 1, k: 'cart', o: p.id, p: [p.pos[0], fl.point[1], p.pos[2]], born: n, st: 'ride', ground: true, fall: 0, restT: 0, sync: 0,
        v: [0, 0, 0], yaw: Math.atan2(p.pos[0] - S.cx, p.pos[2] - S.cz), hit: new Map(), solid: false, rider: p.id, bg: 1 }; // (facing the middle)
      carts.set(c.id, c);
      p.ride = c.id; p.pos = [c.p[0], c.p[1] + CART.top, c.p[2]]; p.vel = [0, 0, 0]; p.bgOffT = 0;
      if (p.isBot) { p.yaw = c.yaw; p.ai.ry = c.yaw; p.ai.hook = null; p.g = null; p.ai.cg = true; }
      this.broadcast({ t: 'cart', k: 'u', ...cartMsg(c) });
      return true;
    },
    // a click in the cart: the server says if it counts (the ram's speed check lets a boost through for a moment)
    bgmBoost(p) {
      const S = this.bgm, n = now();
      if (!S || S.k !== 'carts' || !p.alive || !p.ride || n - (p.bgBoostT || 0) < CM.boostCd - 100) return;
      const c = this.carts && this.carts.get(p.ride);
      if (!c || c.rider !== p.id) return;
      p.bgBoostT = n;
      this.bgnEv('boost', { id: p.id });
    },
    // a moving cart meets someone: no damage, a big fling out of their cart toward wherever it was going
    bgmRam(c, n) {
      if (!this.round || this.round.over) return;
      const rider = c.st === 'ride' ? this.players.get(c.rider) || null : null;
      if (c.st === 'ride' && !rider) return;
      let v = c.v;
      if (rider) { // only as fast as a cart goes (+ slack), more only inside a boost the server okayed
        const cap = CART.ride.top + CM.slack + (n - (rider.bgBoostT || 0) < CM.boostMs ? CM.boost : 0), sp = Math.hypot(v[0], v[2]);
        if (sp > cap) v = [v[0] * cap / sp, v[1], v[2] * cap / sp];
      }
      const by = rider || this.players.get(c.by) || null;
      if (K.peace && (!by || by.isBot)) return; // (test knob: only people ram)
      for (const t of this.players.values()) {
        if (!t.alive || t === rider || t.bench || (t.isBot && t.ai && t.ai.dummy) || t.watch) continue;
        if (by && this.friendly(by, t)) continue;
        if (n - (t.spawnT || 0) < 1200 || n - (c.hit.get(t.id) || 0) < CART.hitCd) continue; // (spawn protection)
        const tc = t.ride && this.carts.get(t.ride), tp = tc ? tc.p : t.pos;
        const dx = tp[0] - c.p[0], dz = tp[2] - c.p[2], dy = tp[1] - c.p[1], d = Math.hypot(dx, dz);
        if (d > (tc ? CART.L + 0.3 : CART.L * 0.5 + 0.65) || dy < -1.2 || dy > 2) continue;
        const [ux, uz] = d > 0.05 ? [dx / d, dz / d] : unit(v[0], v[2]);
        const tv = tc ? tc.v : t.vel, close = (v[0] - tv[0]) * ux + (v[2] - tv[2]) * uz; // closing speed
        if (close < CM.minSp) continue;
        c.hit.set(t.id, n);
        const [hx, hz] = unit(v[0], v[2]), [fx, fz] = unit(hx * 0.6 + ux * 0.4, hz * 0.6 + uz * 0.4); // mostly the way the ram was going
        const k = close * CART.kbK * (rider ? CM.kb : CM.hazardKb);
        if (tc) { tc.by = by ? by.id : 0; this.cartLetGo(tc, [tv[0] + fx * k * 0.4, 0, tv[2] + fz * k * 0.4]); } // out of the cart: it rolls on without them (a hazard now)
        t.bgOffT = n;
        if (by && by !== t) this.tag(t, by, 'cart'); // (the void kill is theirs)
        this.knock(t, [fx * k, CART.kbUp * CM.up, fz * k], 'cart');
        if (rider) this.knock(rider, [-fx * close * CM.recoil, 0, -fz * close * CM.recoil], 'cart'); // bumper cars: you bounce back a bit too
        this.broadcast({ t: 'fx', k: 'plough', p: [tp[0], tp[1] + 0.8, tp[2]].map(r2), n: 1, s: r2(close) });
        this.bgnEv('ram', { a: by ? by.id : 0, b: t.id, s: r2(close) });
      }
    },
    // into the void: a life gone (2v2: the team's), and out when there are none left
    bgmFell(t, by) {
      const S = this.bgm, mg = S.mg, s = this.bgnSeatOf(t);
      if (!s || !mg.seats.includes(s.i)) return;
      S.falls[s.i] = (S.falls[s.i] || 0) + 1;
      const bs = by && by !== t ? this.bgnSeatOf(by) : null;
      if (bs) S.kos[bs.i] = (S.kos[bs.i] || 0) + 1;
      let out = true;
      if (mg.teams && mg.sides) { const side = mg.sides[0].includes(s.i) ? 1 : 2; if (S.pool[side] > 0) { S.pool[side]--; out = false; } }
      else { S.lives[s.i] = Math.max(0, (S.lives[s.i] ?? CM.solo) - 1); out = S.lives[s.i] <= 0; } // (1v1v1v1 / duel: your own lives)
      if (out) { S.out.add(s.i); S.outAt[s.i] = ++S.outN; t.respawnAt = t.minRespawnAt = Infinity; }
      this.bgnEv('fell', { seat: s.i, id: t.id, out: out ? 1 : 0, by: by && by !== t ? by.id : 0, x: this.bgmInfo() });
    },
    // a bot driving its cart: rams the nearest rival (with a little lead), boosts when lined up close, turns back for
    // the middle and brakes when it's about to go over the edge, backs off a crate it's stuck on. true = it moved
    bgmBotCart(b, dt) {
      const S = this.bgm, c = this.carts && this.carts.get(b.ride), n = now(), ai = b.ai, v = b.vel, R = CART.ride;
      if (!c || c.rider !== b.id) { b.ride = 0; return false; }
      if (ai.ry == null) ai.ry = b.yaw;
      let t = null, bd = 1e9;
      if (!K.peace) for (const o of this.fighters()) { if (o === b || !o.alive || this.friendly(b, o) || o.pos[1] < S.top - 1.5) continue; const d = hd(o.pos, b.pos); if (d < bd) { bd = d; t = o; } }
      const sx = S.hx - CM.edge, sz = S.hz - CM.edge; // the safe square
      const inside = (x, z) => [Math.max(S.cx - sx, Math.min(S.cx + sx, x)), Math.max(S.cz - sz, Math.min(S.cz + sz, z))];
      let want;
      if (t) { const lead = Math.min(0.8, bd / 16); want = inside(t.pos[0] + t.vel[0] * lead, t.pos[2] + t.vel[2] * lead); }
      else {
        if (!ai.cw || n > ai.cwT || Math.hypot(ai.cw[0] - b.pos[0], ai.cw[1] - b.pos[2]) < 2.5) { ai.cw = inside(S.cx + (Math.random() * 2 - 1) * sx, S.cz + (Math.random() * 2 - 1) * sz); ai.cwT = n + 3500; }
        want = ai.cw;
      }
      const px = b.pos[0] + v[0] * 0.65, pz = b.pos[2] + v[2] * 0.65, out = Math.abs(px - S.cx) > sx || Math.abs(pz - S.cz) > sz; // where it'll be in a moment
      if (out) want = [S.cx + (b.pos[0] - S.cx) * 0.3, S.cz + (b.pos[2] - S.cz) * 0.3];
      const back = n < (ai.backT || 0);
      const wy = Math.atan2(-(want[0] - b.pos[0]), -(want[1] - b.pos[2])), off = wrapA(wy - ai.ry);
      const turn = R.turn * (ai.diff === 'easy' ? 0.8 : ai.diff === 'hard' ? 1.15 : 1) * (back ? -0.8 : 1);
      ai.ry = wrapA(ai.ry + Math.max(-Math.abs(turn) * dt, Math.min(Math.abs(turn) * dt, off)) * Math.sign(turn));
      const fx = -Math.sin(ai.ry), fz = -Math.cos(ai.ry);
      let along = v[0] * fx + v[2] * fz, side = v[0] * -fz + v[2] * fx;
      side *= Math.exp(-7 * dt);
      let fw = 0;
      if (ai.cg) {
        const outward = (b.pos[0] - S.cx) * v[0] + (b.pos[2] - S.cz) * v[2] > 0;
        fw = back ? -1 : out && outward && along > 1.5 ? -1 : Math.abs(off) > 2.2 ? 0 : 1; // heading off the edge: feet down. facing the wrong way: turn first
        if (fw > 0 && along < R.top) along = Math.min(R.top, along + R.acc * dt);
        if (fw < 0) along = Math.max(-4, along - R.acc * 1.4 * dt);
        if (!fw) along -= Math.sign(along) * Math.min(Math.abs(along), R.fric * dt);
        const easy = ai.diff === 'easy' ? 1200 : 0;
        if (t && !out && bd < 10 && Math.abs(off) < 0.3 && n - (b.bgBoostT || 0) >= CM.boostCd + easy) { along += CM.boost; b.bgBoostT = n; this.bgnEv('boost', { id: b.id }); } // lined up, close: BOOST
      }
      along = Math.max(-R.maxSp, Math.min(R.maxSp, along));
      v[0] = fx * along - fz * side; v[2] = fz * along + fx * side;
      v[1] -= 26 * dt;
      const cp = [b.pos[0], b.pos[1] - CART.top, b.pos[2]], v0 = v.slice();
      const res = movePlayer(cp, v, dt, this.boxes, !!ai.cg);
      if (res.wall) for (const ax of [0, 2]) if (v[ax] === 0 && v0[ax]) v[ax] = -v0[ax] * CART.wallBounce;
      ai.cg = !!res.ground && v[1] <= 0.01;
      // pushing into a crate and going nowhere: back up and turn for a moment
      ai.stuck = ai.cg && fw > 0 && Math.hypot(v[0], v[2]) < 1.2 ? (ai.stuck || 0) + dt : 0;
      if (ai.stuck > 0.7) { ai.stuck = 0; ai.backT = n + 800; ai.cw = null; }
      b.pos = [cp[0], cp[1] + CART.top, cp[2]]; b.yaw = ai.ry; b.pitch = 0; b.onGround = false; b.f = 0;
      if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
      return true;
    },
    bgmCartsTick(n) {
      const S = this.bgm, mg = S.mg;
      for (const c of [...(this.carts || new Map()).values()]) { // ridden carts never time out; empty ones go back to the store after a while
        if (c.st === 'ride') { c.born = n; c.freeAt = 0; c.restAt = 0; continue; }
        c.freeAt ||= n;
        if (c.st === 'rest') c.restAt ||= n; else c.restAt = 0;
        if ((c.restAt && n - c.restAt > CM.rest) || n - c.freeAt > CM.hazardMs) this.dropCart(c, 'gone');
      }
      for (const p of this.fighters()) {
        const s = this.bgnSeatOf(p);
        if (s && S.out.has(s.i)) { if (p.alive) { p.alive = false; p.hp = 0; p.ride = 0; } p.respawnAt = p.minRespawnAt = Infinity; continue; } // out: watching (a bot that took the seat over too)
        if (!p.alive) continue;
        if (p.ride) { p.bgOffT = 0; continue; }
        if (!p.bgOffT) p.bgOffT = n;
        if ((n - (p.spawnT || 0) < 1500 || n - p.bgOffT > CM.remount) && this.bgmFloor(p) && this.bgmMount(p) && n - (p.spawnT || 0) >= 1500) this.bgnEv('cartback', { id: p.id }); // fresh cart (CART RETURN)
      }
      // last cart standing (2v2: last team)
      const left = mg.teams && mg.sides ? mg.sides.filter((side) => side.some((i) => !S.out.has(i))) : mg.seats.filter((i) => !S.out.has(i));
      if (left.length <= 1) this.endRound();
    },

    // ---------------------------------------------------------------- DUCK CATCH
    // somewhere a duck can land: open sky over it, a floor near whoever it's for (or near a spawn)
    bgmDuckSpot(near, r0 = 2, r1 = 9) {
      const sp = this.map.spawns || [[0, 0, 0]];
      for (let i = 0; i < 12; i++) {
        const c = near ? near.pos : sp[Math.floor(Math.random() * sp.length)], a = Math.random() * Math.PI * 2, r = r0 + Math.random() * (r1 - r0);
        const x = c[0] + Math.cos(a) * r, z = c[2] + Math.sin(a) * r;
        const h = raycast([x, c[1] + 3, z], [0, -1, 0], 9, this.boxes);
        if (!h || h.normal[1] < 0.7 || h.box.pad || h.point[1] < this.map.killY + 3) continue;
        if (raycast([x, h.point[1] + 0.3, z], [0, 1, 0], DK.h, this.boxes)) continue; // a roof over it: it'd come through the roof
        return [x, h.point[1], z];
      }
      return null;
    },
    // o: { at, h, ms, one (a dropped duck: always 1), not (the one who dropped it can't catch it straight back) }
    bgmDuckDrop(near, gold, o = {}) {
      const S = this.bgm, n = now(), at = o.at || this.bgmDuckSpot(near);
      if (!at) return null;
      const h = o.h ?? DK.h, ms = o.ms ?? (h / DK.fall) * 1000;
      const d = { id: ++S.id, p: at, h, t0: n, t1: n + ms, g: gold ? 1 : 0, one: o.one ? 1 : 0, not: o.not || 0, notT: n + 800 };
      S.ducks.set(d.id, d);
      this.bgnEv('duck', { id: d.id, p: at.map(r2), h: r2(h), ms: Math.round(ms), g: d.g, one: d.one });
      return d;
    },
    // ducks popping out of someone (a slap, the curse): up to DK.spit of them land round them, worth 1 each
    bgmSpit(t, k) {
      for (let i = 0; i < Math.min(k, DK.spit); i++) {
        const at = this.bgmDuckSpot(t, 1.4, 3.6);
        if (at) this.bgmDuckDrop(null, false, { at, h: 2.4, ms: 520, one: 1, not: t.id });
      }
    },
    bgmSlap(t, by) {
      const S = this.bgm, s = this.bgnSeatOf(t);
      if (!s) return;
      const lose = Math.min(DK.slap, S.pile[s.i] || 0);
      if (lose) S.pile[s.i] -= lose;
      this.bgnEv('slap', { a: by.id, b: t.id, seat: s.i, n: lose, pile: S.pile[s.i] || 0 });
      if (lose) this.bgmSpit(t, lose);
    },
    // pulled into the cursed duck's hole: half your pile, gone (some of it spat back out)
    bgmCurse(t) {
      const S = this.bgm, s = this.bgnSeatOf(t), n = now();
      if (!s || n - (S.curseT[s.i] || 0) < 3000) return;
      S.curseT[s.i] = n;
      const lose = Math.floor((S.pile[s.i] || 0) / 2);
      S.pile[s.i] = (S.pile[s.i] || 0) - lose;
      this.bgnEv('curse', { id: t.id, seat: s.i, n: lose, pile: S.pile[s.i] });
      if (lose) this.bgmSpit(t, Math.ceil(lose / 2));
    },
    // the cursed duck: a real sky duck (it lands as a black hole: tickHoles pulls), the usual red marker first
    bgmCursed(list) {
      const S = this.bgm, near = list.length ? list[Math.floor(Math.random() * list.length)] : null, at = this.bgmDuckSpot(near, 1, 6);
      if (!at) return;
      const w = WEAPONS.duck, y0 = at[1] + DK.h, v = DUCKRAIN.vy;
      const pr = this.makeProj({ id: 0 }, 'duck', [at[0], y0, at[2]], [0, -v, 0], { sky: true });
      pr.born = now();
      const dy = Math.max(0, y0 - at[1] - w.r), eta = (-v + Math.sqrt(v * v + 2 * w.grav * dy)) / w.grav;
      this.broadcast({ t: 'skyduck', id: pr.id, p: at.map(r2), ms: Math.round(eta * 1000) });
      S.curses.push({ p: at, until: now() + eta * 1000 + (DUCKRAIN.hole.time + 1) * 1000 });
      this.bgnEv('cursed', { p: at.map(r2), ms: Math.round(eta * 1000) });
    },
    bgmDucksTick(n) {
      const S = this.bgm, mg = S.mg, list = this.fighters().filter((p) => p.alive);
      const k = Math.max(0, Math.min(1, (n - S.t0) / Math.max(1, (mg.ends || n) - S.t0)));
      if (n >= S.next) { // more and faster as the clock runs down, most of them near someone
        S.next = n + (DK.every[0] + (DK.every[1] - DK.every[0]) * k) * 1000;
        const cnt = Math.max(1, Math.round(DK.n[0] + (DK.n[1] - DK.n[0]) * k + Math.random() - 0.5));
        for (let i = 0; i < cnt && S.ducks.size < DK.max; i++) this.bgmDuckDrop(list.length && Math.random() < 0.65 ? list[Math.floor(Math.random() * list.length)] : null, Math.random() < DK.goldP);
      }
      if (n >= S.curseAt) { S.curseAt = n + DK.cursedEvery; this.bgmCursed(list); }
      // catches: from where the server has everyone (a falling duck at your body's height, a landed one at your feet)
      for (const d of [...S.ducks.values()]) {
        const fall = n < d.t1, y = fall ? d.p[1] + d.h * (d.t1 - n) / (d.t1 - d.t0) : d.p[1];
        if (!fall && n > d.t1 + DK.floorMs) { S.ducks.delete(d.id); this.bgnEv('duckx', { id: d.id }); continue; }
        let got = null;
        for (const p of list) {
          if ((d.not === p.id && n < d.notT) || hd(p.pos, d.p) > (fall ? DK.catchR : DK.pickR)) continue;
          if (fall ? y < p.pos[1] - 0.3 || y > p.pos[1] + 2.4 : Math.abs(p.pos[1] - d.p[1]) > 1.6) continue;
          got = p; break;
        }
        const s = got && this.bgnSeatOf(got);
        if (!s) continue;
        const v = d.g ? DK.gold : d.one ? 1 : fall ? DK.air : DK.floor;
        S.pile[s.i] = (S.pile[s.i] || 0) + v;
        S.ducks.delete(d.id);
        this.bgnEv('duckx', { id: d.id, by: got.id, seat: s.i, v, air: fall ? 1 : 0, g: d.g, pile: S.pile[s.i] });
      }
      // the cursed duck's hole: anyone it's pulled in close (or that it landed on)
      S.curses = S.curses.filter((c) => n < c.until);
      for (const h of this.holes.values()) {
        if (!h.sky) continue;
        if (h.bgc === undefined) h.bgc = S.curses.some((c) => hd(c.p, h.p) < 6) ? new Set() : null;
        if (!h.bgc) continue;
        for (const p of list) {
          if (h.bgc.has(p.id)) continue;
          if (h.on !== p.id && Math.hypot(p.pos[0] - h.p[0], p.pos[1] + 1 - h.p[1], p.pos[2] - h.p[2]) > DK.cursedR) continue;
          h.bgc.add(p.id);
          this.bgmCurse(p);
        }
      }
    },
    // a bot's errand: the duck it can get to best (gold first, a catch beats a pickup), away from a cursed one
    bgmDuckGoal(b) {
      const S = this.bgm, n = now(), sp = 8.5 * ((BOT_DIFF[b.ai.diff] || BOT_DIFF.normal).speed || 1);
      const t = this.players.get(b.ai.target);
      if (t && t.alive && hd(t.pos, b.pos) < 3.5) return null; // slapping someone (botTarget only picks a rich one up close)
      for (const c of S.curses) { const d = hd(b.pos, c.p); if (d < 7) { const [ux, uz] = unit(b.pos[0] - c.p[0], b.pos[2] - c.p[2]); return { p: [b.pos[0] + ux * 8, b.pos[1], b.pos[2] + uz * 8], r: 0, force: true }; } }
      let best = null, bc = 1e9;
      for (const d of S.ducks.values()) {
        if (Math.abs(d.p[1] - b.pos[1]) > 3 || S.curses.some((c) => hd(c.p, d.p) < 5)) continue; // another deck / under the curse: no
        const need = hd(b.pos, d.p) / sp, left = (d.t1 - n) / 1000;
        const val = d.g ? DK.gold : d.one ? 1 : left > need - 0.3 ? DK.air : DK.floor;
        const cost = need - val * 0.9 - (b.ai.duck === d.id ? 0.4 : 0);
        if (cost < bc) { bc = cost; best = d; }
      }
      if (!best) return null;
      b.ai.duck = best.id;
      return { p: best.p, r: 0, force: true };
    },

    // ---------------------------------------------------------------- every tick (the tick wrap)
    bgmTick() {
      const S = this.bgm, B = this.bgn, n = now();
      if (!B || B.ph !== 'mg' || B.mg !== S.mg) { this.bgm = null; return; } // (safety)
      if (!this.round || this.round.over) return;
      if (S.k === 'carts') this.bgmCartsTick(n);
      else if (S.k === 'ducks') this.bgmDucksTick(n);
      else if (S.k === 'bigguy') { // a fresh rig every life
        const one = this.bgnOne();
        if (one && one.alive && one.bgRig !== one.spawnT && n - one.spawnT > 250 && !one.rig) { one.bgRig = one.spawnT; this.rigStart(one); if (one.body) { one.body.hp = one.body.max = Math.round(one.body.max * BGN_MINI.bigguy.armour); this.bodyFlush(one, true); } this.bgnEv('rig', { id: one.id }); }
      } else if (S.k === 'boss') {
        const b = this.players.get(S.boss);
        if (n - S.barT > BS.bar) { const hp = b && b.body ? Math.max(0, Math.round(b.body.hp)) : 0; S.barT = n; if (hp !== S.lastHp) { S.lastHp = hp; this.bgnEv('boss', { id: S.boss, hp, max: S.max }); } }
        if (!S.down && (!b || (!b.mech && n - S.t0 > 3000))) this.bgmBossDown(null); // (no mech: on foot, a kill counts as a break)
        if (S.down && n - S.down > BS.down) this.endRound();
      }
    },
    // the boss went over the side in his mech: a crane puts him back where he started. if someone knocked him off (hit in
    // the last 2.5 s by a real shove), the splash costs him BS.splash of his armour, credited to them. false = that broke it (BOSS DOWN)
    bgmBossBack(b, by) {
      const S = this.bgm, pushed = by && by !== b && now() - (b.knockT || 0) < 2500, cut = pushed ? Math.round(S.max * BS.splash) : 0; // (only a push costs him: walking off on his own doesn't)
      if (!b.body || b.body.hp <= cut || !S.home) return false;
      b.body.hp -= cut;
      const s = pushed ? this.bgnSeatOf(by) : null;
      if (s) S.dmg[s.i] = (S.dmg[s.i] || 0) + cut;
      b.pos = S.home.slice(); b.vel = [0, 0, 0]; b.onGround = false;
      this.bodyFlush(b, true);
      this.bgnEv('bossback', { id: b.id, p: b.pos.map(r2), cut });
      return true;
    },
    bgmBossDown(by) {
      const S = this.bgm;
      if (!S || S.down) return;
      S.down = now(); S.lastHp = 0;
      this.bgnEv('bossdown', { id: S.boss, by: by ? by.id : 0, seat: by && this.bgnSeatOf(by) ? this.bgnSeatOf(by).i : -1 });
    },
  });

  // ---------------------------------------------------------------- the wraps (each only acts during its minigame)
  wrap(P, 'tick', function (base, dt) { base.call(this, dt); if (this.bgm) this.bgmTick(); });
  wrap(P, 'stepBot', function (base, b, dt) {
    if (b.ride && this.bgm && this.bgm.k === 'carts' && b.alive && this.bgmBotCart(b, dt)) return;
    return base.call(this, b, dt);
  });
  wrap(P, 'plough', function (base, c, att, n) { if (this.bgm && this.bgm.k === 'carts') return this.bgmRam(c, n); return base.call(this, c, att, n); });
  // bumper carts: nothing hurts (only the void). duck catch / carts: the slapper flings and (ducks) knocks ducks loose
  wrap(P, 'damage', function (base, t, amt, attacker, w, hs, from) {
    if (this.bgm && this.bgm.k === 'carts' && w !== 'void' && w !== 'reset') return false;
    return base.call(this, t, amt, attacker, w, hs, from);
  });
  wrap(P, 'hurt', function (base, t, attacker, w, dmg, kb, opts) {
    const S = this.bgm;
    if (S && (S.k === 'ducks' || S.k === 'carts') && w === 'slapper' && t && t.alive && attacker && attacker !== t) {
      if (S.k === 'ducks' && !this.hitBlocked(t, attacker, w)) this.bgmSlap(t, attacker);
      return base.call(this, t, attacker, w, 0, kb && kb.map((x) => x * (S.k === 'ducks' ? DK.slapKb : 0.6)), opts);
    }
    if (S && S.k === 'bigguy' && attacker && attacker !== t && attacker.rig && this.bgnOne() === attacker) dmg *= BGN_MINI.bigguy.dmg; // (the big guy's rig, toned down)
    return base.call(this, t, attacker, w, dmg, kb, opts);
  });
  wrap(P, 'kill', function (base, t, attacker, w) {
    const S = this.bgm, was = t.alive, n = now();
    const one = S && S.k === 'bigguy' ? this.bgnOne() : null, k0 = one ? one.kills : 0;
    const by = w === 'void' || w === 'reset' ? (t.lastAttacker && n - (t.lastAttackT || 0) < 10000 ? this.players.get(t.lastAttacker) || null : null) : attacker; // (who threw them off)
    if (S && S.k === 'boss' && t.id === S.boss && w === 'void' && t.mech && !S.down && this.bgmBossBack(t, by)) return; // he fell off: back up on the deck, minus some armour
    base.call(this, t, attacker, w);
    if (!S || !was || t.alive || !this.round || this.round.over) return;
    if (S.k === 'carts') this.bgmFell(t, by);
    else if (S.k === 'ducks' && w === 'duck') this.bgmCurse(t);
    else if (S.k === 'boss' && t.id === S.boss) this.bgmBossDown(by);
    else if (one && one.kills > k0 && t !== one && this.teamsOn() && t.team !== one.team) this.score[one.team] += BGN_MINI.bigguy.mul - 1; // the big guy's kills count x3
  });
  // the boss's mech blowing up (armour gone, or died in it) = BOSS DOWN
  wrap(P, 'mechExit', function (base, p, why, by) {
    const S = this.bgm;
    if (S && S.k === 'boss' && p.id === S.boss && why === 'boom') this.bgmBossDown(by);
    return base.call(this, p, why, by);
  });
  // the boss's damage, per seat (the MVP): what really came off his armour
  wrap(P, 'bodySoak', function (base, t, amt, attacker, w) {
    const S = this.bgm;
    if (S && S.k === 'boss' && t.id === S.boss && attacker && attacker !== t && t.body && amt > 0 && this.bodyOn(t) && !BODY.bypass.includes(w)) {
      const s = this.bgnSeatOf(attacker);
      if (s) S.dmg[s.i] = (S.dmg[s.i] || 0) + Math.min(amt, BODY.cap, Math.max(0, t.body.hp));
    }
    return base.call(this, t, amt, attacker, w);
  });
  // scores the board ranks by: bumper carts (still in > out later > out first; rams break ties), ducks, boss damage
  wrap(P, 'bgnScore', function (base, p) {
    const S = this.bgm, s = S && p && this.bgnSeatOf(p);
    if (!s) return base.call(this, p);
    if (S.k === 'carts') return S.out.has(s.i) ? (S.outAt[s.i] || 0) * 10 + (S.kos[s.i] || 0) : 1000 - (S.falls[s.i] || 0) * 50 + (S.kos[s.i] || 0);
    if (S.k === 'ducks') return S.pile[s.i] || 0;
    if (S.k === 'boss') return Math.round(S.dmg[s.i] || 0);
    return base.call(this, p);
  });
  // the boss doesn't earn killstreaks (a rig on top of his mech was a bit much)
  wrap(P, 'rigBotEarn', function (base, b) { if (b.bgBoss) return; return base.call(this, b); });
  wrap(P, 'mechBotEarn', function (base, b) { if (b.bgBoss) return; return base.call(this, b); });
  // a boss is no seat: he's always team 2
  wrap(P, 'bgnSide', function (base, p) {
    if (p.bgBoss && this.bgn && this.bgn.mg) { if (!p.ownColor) p.ownColor = p.color; p.team = 2; p.color = TEAMS[2].color; return true; }
    return base.call(this, p);
  });
  // bots: duck catch picks errands (botGoal) and only slaps a rival with a pile (botTarget)
  wrap(P, 'botGoal', function (base, b) { if (this.bgm && this.bgm.k === 'ducks') return K.peace ? null : this.bgmDuckGoal(b); return base.call(this, b); });
  wrap(P, 'botTarget', function (base, b) {
    const S = this.bgm;
    if (!S || S.k !== 'ducks') return base.call(this, b);
    if (K.peace) return null;
    let best = null, bd = 3.5;
    for (const t of this.fighters()) {
      if (t === b || !t.alive || this.friendly(b, t) || Math.abs(t.pos[1] - b.pos[1]) > 2) continue;
      const s = this.bgnSeatOf(t), d = hd(t.pos, b.pos);
      if (s && (S.pile[s.i] || 0) >= 5 && d < bd) { bd = d; best = t; }
    }
    return best;
  });
  void H;
}
