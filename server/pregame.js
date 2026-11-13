// The pre-game area (shared/pregame.js has the deck and the rules): while a mode lobby counts down (this.warm), the
// room plays on a small deck floating off the edge of the match's map instead of a warm-up deathmatch on it.
// the server's part: the deck's boxes join the room's (bots walk on them, rays hit them), spawns go on the deck, nothing
// can hurt or kill anyone, combat messages are dropped, someone off the deck is put back on it, a harmless shove, bots
// wander about, and the big board's top 3 (from what each account already has: no lookups, never blocks the tick).
// it wraps a few Room methods (installed late, after installReset) and only does anything while this.warm is set.
import { PREGAME, padFor, offPad, boardRows, lookFor, EMOTES, EMOTE } from '../shared/pregame.js';

const now = () => Date.now();
// nothing that hurts, uses up or spawns something gets through on the deck (sprays, READY, votes, loadout picks do)
const BLOCK = new Set(['hit', 'fire', 'item', 'deploy', 'slam', 'tbag', 'use', 'parry', 'car', 'cart', 'lasso', 'lh', 'rig', 'mech', 'lava', 'cough', 'sec', 'ans', 'nv', 'land', 'gavel', 'radar']);
const fin3 = (a) => Array.isArray(a) && a.length === 3 && a.every(Number.isFinite);

export function installPregame(Room, { send }) {
  const P = Room.prototype;
  const handle0 = P.handle, pick0 = P.pickSpawn, think0 = P.botThink, dmg0 = P.damage, hurt0 = P.hurt, kill0 = P.kill;
  const oob0 = P.oobCheck, tick0 = P.tickWarm, warm0 = P.enterWarm, start0 = P.startMatch, info0 = P.warmInfo;
  const bx = Object.getOwnPropertyDescriptor(P, 'boxes');
  // the room's solid boxes: the map's, plus the deck's while the lobby's on (one array per lobby, so the grid's built once)
  Object.defineProperty(P, 'boxes', {
    configurable: true,
    get() {
      const base = bx.get.call(this), pad = this.pgPad();
      if (!pad) return base;
      const c = this.pgBx;
      if (c && c.base === base && c.n === base.length && c.pad === pad) return c.all;
      const all = base.concat(pad.boxes); all.terrain = base.terrain || null;
      this.pgBx = { base, n: base.length, pad, all };
      return all;
    },
  });
  Object.assign(P, {
    pgPad() { return this.warm && this.lobby && this.map ? padFor(this.map) : null; },
    handle(p, m) {
      if (this.warm && m && typeof m === 'object' && this.pgHandle(p, m)) return;
      return handle0.call(this, p, m);
    },
    // true = dealt with here (or dropped)
    pgHandle(p, m) {
      const pad = this.pgPad();
      if (!pad) return false;
      if (BLOCK.has(m.t)) return true;
      if (m.t === 'push') return m.w !== 'hook'; // the grapple's tug still works (no damage); the blower and the rest don't
      if (m.t === 'shove') { this.pgShove(p, m.to); return true; }
      if (m.t === 'emote') { this.pgEmote(p, m); return true; }
      if (m.t === 's' && p.alive && m.q === p.seq && fin3(m.p) && offPad(pad, m.p)) { this.pgPutBack(p); return true; } // jumped off / flew off: back on the deck
      return false;
    },
    // back on the deck, on a free spot. the client's own check normally beats this to it
    pgPutBack(p) {
      const to = this.pickSpawn(p.isBot, p);
      p.pos = to.slice(); p.vel = [0, 0, 0]; p.oobAt = 0; p.g = null;
      if (!p.isBot) send(p, { t: 'tp', p: to });
    },
    // a shove: knockback, nothing else. close enough, both up, a cooldown each
    pgShove(p, to) {
      const S = PREGAME.shove, n = now();
      if (!p || !p.alive || p.watch || !Number.isInteger(to)) return;
      const t = this.players.get(to);
      if (!t || t === p || !t.alive || t.watch) return;
      if (n - (p.pgShoveT || 0) < S.cd) return;
      const dx = t.pos[0] - p.pos[0], dy = t.pos[1] - p.pos[1], dz = t.pos[2] - p.pos[2], h = Math.hypot(dx, dz);
      if (h > S.range || Math.abs(dy) > 2.5) return;
      p.pgShoveT = n;
      const ux = h > 0.05 ? dx / h : -Math.sin(p.yaw || 0), uz = h > 0.05 ? dz / h : -Math.cos(p.yaw || 0);
      this.knock(t, [ux * S.push, S.lift, uz * S.push], 'shove');
      this.broadcast({ t: 'pgs', by: p.id, to: t.id }); // everyone sees (and hears) the slap
    },
    // emotes: the hook (shared/pregame.js EMOTES). an unknown id is dropped
    pgEmote(p, m) {
      const n = now();
      if (!p || p.isBot || !p.alive || typeof m.e !== 'string' || !Object.hasOwn(EMOTES, m.e)) return;
      if (n - (p.pgEmoteT || 0) < EMOTE.cd) return;
      p.pgEmoteT = n;
      this.broadcast({ t: 'emote', id: p.id, e: m.e });
    },
    // spawns on the deck: the emptiest of its spots
    pickSpawn(forBot, who) {
      const pad = this.pgPad();
      if (!pad) return pick0.call(this, forBot, who);
      let best = pad.spawns[0], bestD = -1;
      for (const s of pad.spawns) {
        let d = 1e9;
        for (const p of this.players.values()) if (p !== who && p.alive && p.pos) d = Math.min(d, Math.hypot(s[0] - p.pos[0], s[2] - p.pos[2]));
        d += Math.random() * 1.5;
        if (d > bestD) { bestD = d; best = s; }
      }
      return [best[0] + (Math.random() - 0.5) * 0.6, best[1], best[2] + (Math.random() - 0.5) * 0.6];
    },
    // nothing hurts in the lobby: no damage, no deaths (falling off puts you back, see pgHandle)
    damage(t, ...a) { return this.pgPad() ? false : dmg0.call(this, t, ...a); },
    hurt(t, attacker, w, dmg, kb, opts) {
      if (!this.pgPad()) return hurt0.call(this, t, attacker, w, dmg, kb, opts);
      if (t && t.alive && kb && w === 'hook') this.knock(t, kb, w); // (the grapple tug: still a tug)
      return null;
    },
    kill(t, ...a) { return this.pgPad() ? undefined : kill0.call(this, t, ...a); },
    oobCheck(t, n) { if (this.pgPad()) { t.oobAt = 0; return false; } return oob0.call(this, t, n); },
    // bots on the deck: amble to a spot, stand about, hop, now and then shove whoever's next to them. no guns
    botThink(b, dt) {
      const pad = this.pgPad();
      if (!pad) return think0.call(this, b, dt);
      const ai = b.ai, n = now();
      if (offPad(pad, b.pos)) this.pgPutBack(b);
      if (!ai.pg || n > ai.pg.until || Math.hypot(ai.pg.to[0] - b.pos[0], ai.pg.to[2] - b.pos[2]) < 0.8) {
        const s = pad.spawns[Math.floor(Math.random() * pad.spawns.length)];
        ai.pg = { to: [s[0] + (Math.random() - 0.5) * 3, s[1], s[2] + (Math.random() - 0.5) * 3], until: n + 2500 + Math.random() * 5000, idle: Math.random() < 0.4 };
      }
      if (n - (ai.pgShoveT || 0) > 9000 && Math.random() < dt * 0.12) { // a cheeky shove, now and then (not a bonk-fest)
        ai.pgShoveT = n + Math.random() * 6000;
        for (const t of this.players.values()) if (t !== b && t.alive && Math.hypot(t.pos[0] - b.pos[0], t.pos[2] - b.pos[2]) < PREGAME.shove.range - 0.4) { b.yaw = Math.atan2(-(t.pos[0] - b.pos[0]), -(t.pos[2] - b.pos[2])); this.pgShove(b, t.id); break; }
      }
      if (ai.pg.idle) { b.yaw += Math.sin(n * 0.001 + b.id) * dt * 0.6; return { wx: 0, wz: 0, jump: Math.random() < dt * 0.15 }; }
      const dx = ai.pg.to[0] - b.pos[0], dz = ai.pg.to[2] - b.pos[2], h = Math.hypot(dx, dz) || 1;
      b.yaw = Math.atan2(-dx, -dz); b.pitch = 0;
      return { wx: dx / h, wz: dz / h, jump: Math.random() < dt * 0.25 };
    },
    warmInfo() {
      const r = info0.call(this);
      if (r && this.pgPad()) r.pg = { look: lookFor() }; // the client builds the deck for this map (shared/pregame.js)
      return r;
    },
    enterWarm(ms, first) {
      for (const p of this.players.values()) p.pgbK = null; // a fresh board for everyone
      this.pgBoardT = 0;
      return warm0.call(this, ms, first);
    },
    startMatch() { this.pgBx = null; return start0.call(this); },
    tickWarm(n) {
      const r = tick0.call(this, n);
      if (this.warm && n - (this.pgBoardT || 0) >= PREGAME.board.every) { this.pgBoardT = n; this.pgBoard(); }
      return r;
    },
    // the big board: the top 3 here, sent to whoever doesn't have this version yet
    pgBoard() {
      const rows = boardRows(this.lobby.kind, [...this.players.values()].filter((p) => !p.watch));
      const k = JSON.stringify(rows);
      for (const p of this.players.values()) if (!p.isBot && p.pgbK !== k) { p.pgbK = k; send(p, { t: 'pgb', k: this.lobby.kind, rows }); }
    },
  });
}
