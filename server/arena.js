// ISLAND ARENA on the server (numbers + the play area: shared/arena.js; design: docs/modes/BATTLE_ISLAND.md). A team
// deathmatch on Battle Island's middle that reuses the pieces: the teams (room.js), the mech (server/mech.js: the call,
// climbing in, the armour, MECH DOWN) and Battle Island's MECH METER and hero picks (server/islemeter.js, which asks
// arenaOn / arenaIn / arenaMeterOn / arenaAfter where it asked about squads). Hooked in by wrapping a few Room methods,
// so room.js only installs it. The server owns everything: the score, the meter, every call, the fence.
// Messages out: { t: 'arena', k: 'st', sc, target, left, area } (the match), { k: 'sc', sc, by, o, f } (a mech kill),
// { k: 'fence', id } (pushed back in). In: { t: 'hero', h } (the next mech), { t: 'deploy', r: 'mechdrop', at } (the call).
import { GAMES } from '../shared/modes.js';
import { ISLE } from '../shared/island.js';
import { HEROES, HERO_IDS, isHero, heroFor, heroName } from '../shared/heroes.js';
import { ARENA, arenaArea, inArena } from '../shared/arena.js';
import { MECH } from '../shared/mech.js';
import { raycast } from '../shared/physics.js';

const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const LOG = !!process.env.JF_ARENA_LOG; // test knob: print the match (calls, mech kills, fence pushes)

export function installArena(Room, H) {
  const { send } = H;
  const P = Room.prototype, orig = {};
  for (const k of ['startRound', 'pickSpawn', 'resetLife', 'streaksOn', 'botGoal', 'kill', 'handle', 'tickMech', 'mechSnap']) {
    if (typeof P[k] !== 'function') throw new Error('arena: Room is missing ' + k);
    orig[k] = P[k];
  }
  Object.defineProperty(P, 'arenaOn', { get() { return (this.mode === 'ffa' || this.mode === 'bots') && !!GAMES[this.game].arena && !!arenaArea(this.map); } });

  // ---------------------------------------------------------- the match
  P.startRound = function () {
    orig.startRound.call(this);
    if (this.arenaOn) this.arenaRound();
  };
  P.streaksOn = function () { return !this.arenaOn && orig.streaksOn.call(this); }; // no killstreaks: the meter is your streak
  P.pickSpawn = function (forBot, who) { return this.arenaOn && who && who.team ? this.arenaSpot(who) : orig.pickSpawn.call(this, forBot, who); };
  P.resetLife = function (p) {
    orig.resetLife.call(this, p);
    if (this.arenaOn && p.mm && this.A && p.mm.match === this.A.id && !p.mech) { p.mm.v = Math.max(p.mm.v, this.arenaAfter()); this.isleMeterSend(p, true); } // back as a pilot: at least 60%
  };
  P.kill = function (t, attacker, w) {
    const was = t.alive;
    orig.kill.call(this, t, attacker, w);
    if (!was || !this.arenaOn || t.alive) return;
    const k = attacker && attacker !== t ? attacker : t.lastAttacker && now() - (t.lastAttackT || 0) < 10000 ? this.players.get(t.lastAttacker) : null;
    if (k && k !== t && !this.friendly(k, t)) this.isleMeter(k, ISLE.meter.kill, 'kill'); // a kill fills your meter (Battle Island's +25%)
  };
  P.handle = function (p, m) {
    if (this.arenaOn && m && (m.t === 'hero' || m.t === 'deploy')) { if (!p.quiz && !p.trap) this.arenaMsg(p, m); return; }
    return orig.handle.call(this, p, m);
  };
  P.tickMech = function (n, dt) {
    orig.tickMech.call(this, n, dt);
    if (this.arenaOn) this.tickArena(n, dt);
  };
  P.mechSnap = function (p) { // every snapshot: the mech's own checks, then the fence (before the void check)
    orig.mechSnap.call(this, p);
    if (this.arenaOn) this.arenaFence(p);
  };
  P.botGoal = function (b) { return this.arenaOn ? this.arenaBotGoal(b) : orig.botGoal.call(this, b); };

  Object.assign(P, {
    arenaAfter() { return ARENA.after; },
    arenaIn(p) { return !!(p && this.A && p.mm && p.mm.match === this.A.id && !p.watch && !(p.ai && p.ai.dummy)); },
    arenaMeterOn(p) { return this.arenaIn(p) && p.alive && !p.mech && !this.mechOf(p); },
    // a new match: the clock, a hero + a meter for everyone, then everyone's mech drops onto their team's pads
    arenaRound() {
      const A = this.A = { id: (this.A ? this.A.id : 0) + 1, t: now(), stT: 0, fenceT: new Map(), log: [] };
      this.round.ends = now() + ARENA.time * 1000;
      this.round.target = ARENA.kills;
      for (const p of this.fighters()) if (!p.watch) p.mm = null;
      this.arenaHeroAll();
      for (const p of this.fighters()) if (!p.watch) this.arenaEnlist(p, true);
      this.arenaSend();
      if (LOG) console.log(`[arena] match ${A.id}: ${this.fighters().filter((p) => p.mm).length} fighters, first to ${ARENA.kills}, ${ARENA.time}s`);
    },
    // a hero each, no more than half a team on one (heroFor's cap): people's picks first, then bots fill the gaps
    arenaHeroAll() {
      for (const team of [1, 2]) {
        const list = this.fighters().filter((p) => p.team === team && !p.watch).sort((a, b) => (a.isBot - b.isBot) || a.id - b.id), taken = [];
        for (const p of list) { p.hero = heroFor(p.isBot ? HERO_IDS[(Math.random() * HERO_IDS.length) | 0] : p.heroWant || p.mechFrame, taken, list.length); taken.push(p.hero); }
      }
    },
    // into the match: a meter (and a hero), and if you're up, your mech drops onto you (start = the match's first drop)
    arenaEnlist(p, drop) {
      if (!this.A || p.watch || (p.ai && p.ai.dummy) || !p.team) return;
      if (!isHero(p.hero)) p.hero = heroFor(p.isBot ? HERO_IDS[(Math.random() * HERO_IDS.length) | 0] : p.heroWant || p.mechFrame, this.fighters().filter((o) => o !== p && o.team === p.team).map((o) => o.hero), this.fighters().filter((o) => o.team === p.team).length);
      p.mm = { match: this.A.id, v: 0, sv: -1, sT: 0, out: false };
      p.heroMatch = this.A.id;
      if (drop && p.alive && !this.arenaDrop(p)) p.mm.v = ARENA.late; // (no room for it here: call it yourself)
      this.isleMeterSend(p, true);
      this.broadcast({ t: 'isle', k: 'hero', id: p.id, h: p.hero });
    },
    // your mech falls onto where you stand (MECH DROP's own call: a floor, open sky) and you're in it when it lands
    arenaDrop(p) {
      if (p.mech || this.mechOf(p)) return true;
      const f = HEROES[p.hero] ? HEROES[p.hero].frame : 'paperplane';
      if (!this.mechCall(p, p.pos.slice(), f)) return false;
      const m = this.mechOf(p);
      if (m) m.auto = true; // (mechLand climbs you in, people too)
      this.broadcast({ t: 'isle', k: 'call', id: p.id, h: p.hero });
      return true;
    },
    // a spawn: a free spot round one of your team's pads (a ring per pad, not on top of a teammate or a waiting mech)
    arenaSpot(who) {
      const A = arenaArea(this.map), pads = A.pads[who.team === 2 ? 2 : 1];
      const busy = (x, z) => { for (const o of this.players.values()) if (o !== who && o.alive && Math.hypot(o.pos[0] - x, o.pos[2] - z) < ARENA.ring - 0.5) return true; for (const m of this.mechMap().values()) if (Math.hypot(m.p[0] - x, m.p[2] - z) < ARENA.ring - 0.5) return true; return false; };
      const start = (Math.random() * pads.length) | 0;
      for (let i = 0; i < pads.length; i++) {
        const d = pads[(start + i) % pads.length], k = Math.max(1, Math.floor((d[3] || 7) * 0.7 * 6.28 / ARENA.ring));
        const spots = [[0, 0]];
        for (let j = 0; j < k; j++) { const a = j / k * 6.28 + d[0]; spots.push([Math.cos(a) * (d[3] || 7) * 0.7, Math.sin(a) * (d[3] || 7) * 0.7]); }
        for (const [dx, dz] of spots) {
          const x = d[0] + dx, z = d[2] + dz;
          if (busy(x, z)) continue;
          const h = raycast([x, d[1] + 20, z], [0, -1, 0], 40, this.boxes);
          if (h && !h.box.pad) return [x, h.point[1] + 0.05, z];
        }
      }
      const d = pads[start];
      return [d[0] + (Math.random() - 0.5) * 4, d[1] + 0.3, d[2] + (Math.random() - 0.5) * 4]; // (all taken: on top of each other is still the pad)
    },
    // a mech broken (piloted or empty): +1 for whoever broke it, if they're on the other team
    arenaMechDown(o, by) {
      if (!this.round || this.round.over || !o || !by || by === o || !by.team || by.team === o.team) return;
      this.score[by.team]++;
      by.mechKills = (by.mechKills || 0) + 1;
      this.broadcast({ t: 'arena', k: 'sc', sc: [this.score[1], this.score[2]], by: by.id, o: o.id, team: by.team });
      if (LOG) console.log(`[arena] MECH DOWN: ${by.name} (team ${by.team}) broke ${o.name}'s ${heroName(o.hero)} · ${this.score[1]}-${this.score[2]}`);
    },
    // { t: 'hero', h } (your next mech; rate-limited, a team can't be more than half one hero) and the call
    arenaMsg(p, m) {
      if (m.t === 'deploy') { if (p.alive && !p.dn) this.isleCall(p, m); return; } // (the meter's own call: 100%, MECH DROP's marker checks)
      const n = now();
      if (n - (p.heroT || 0) < 250) return;
      p.heroT = n;
      if (!isHero(m.h) || !this.arenaIn(p)) return;
      const mates = this.fighters().filter((o) => o.team === p.team && o !== p && this.arenaIn(o)).map((o) => o.hero);
      if (heroFor(m.h, mates, mates.length + 1) !== m.h) { send(p, { t: 'isle', k: 'hero', id: p.id, h: p.hero, no: 1, why: `your team has enough ${heroName(m.h)}s` }); return; }
      p.hero = m.h; p.heroWant = m.h;
      this.broadcast({ t: 'isle', k: 'hero', id: p.id, h: m.h });
      this.isleMeterSend(p, true);
    },
    // the match for everyone (or one person): the score, the clock, the play area
    arenaSend(to) {
      const A = arenaArea(this.map), r = this.round;
      const m = { t: 'arena', k: 'st', sc: [this.score[1], this.score[2]], target: ARENA.kills, left: r ? Math.max(0, r.ends - now()) : 0, area: [r2(A.c[0]), r2(A.c[1]), r2(A.r)], heroes: this.fighters().filter((p) => this.arenaIn(p)).map((p) => [p.id, p.hero]) };
      if (to) send(to, m); else this.broadcast(m);
    },
    // ---------------------------------------------------------- the fence: nobody leaves the middle (no sea kills here)
    // out of the circle or over deep water (the river): back to the last spot you were fine, else onto the circle
    arenaFence(p) {
      if (!p.alive || p.watch) return;
      const A = arenaArea(this.map), x = p.pos[0], z = p.pos[2];
      if (inArena(A, x, z) && !this.arenaDeep(x, z)) { if (!p.arenaOk || Math.hypot(p.arenaOk[0] - x, p.arenaOk[2] - z) > 1) p.arenaOk = p.pos.slice(); return; }
      let q = p.arenaOk && inArena(A, p.arenaOk[0], p.arenaOk[2]) ? p.arenaOk.slice() : null;
      if (!q) { const d = Math.hypot(x - A.c[0], z - A.c[1]) || 1, k = (A.r - 3) / d, qx = A.c[0] + (x - A.c[0]) * k, qz = A.c[1] + (z - A.c[1]) * k, h = raycast([qx, 200, qz], [0, -1, 0], 260, this.boxes); q = [qx, h ? h.point[1] + 0.1 : p.pos[1], qz]; }
      const back = [A.c[0] - q[0], A.c[1] - q[2]], bl = Math.hypot(back[0], back[1]) || 1, v = [back[0] / bl * 5, 3, back[1] / bl * 5]; // (a little shove back in)
      p.pos = q.slice();
      const n = now();
      if (!p.isBot && n - (p.fenceSendT || 0) < 120) return; // (snapshots still on their way from out there: the server has you back already)
      p.fenceSendT = n;
      if (p.isBot) { p.vel = v.slice(); p.onGround = false; if (p.ai) { p.ai.route = null; p.ai.wp = null; } }
      else if (p.mech) { p.mech.last = q.slice(); p.mech.grace = now() + 400; send(p, { t: 'mech', k: 'fix', p: q.map(r2), v: [0, 0, 0] }); }
      else send(p, { t: 'mech', k: 'pos', p: q.map(r2), v: v.map(r2) }); // (mech.js's 'pos': puts your client back)
      const T = this.A ? this.A.fenceT : new Map();
      if (n - (T.get(p.id) || 0) > 1500) { T.set(p.id, n); if (!p.isBot) send(p, { t: 'arena', k: 'fence' }); if (LOG) console.log(`[arena] fence: ${p.name} pushed back in`); }
    },
    // water over your head here (the river)? the island's ground vs the sea
    arenaDeep(x, z) {
      const map = this.map, T = map.boxes && map.boxes.terrain;
      if (!T || map.seaY == null) return false;
      const g = T.at(x, z);
      return g == null || map.seaY - g > (map.wade || 1.5) - 0.3;
    },
    // ---------------------------------------------------------- every tick (after tickMech)
    tickArena(n, dt) {
      if (!this.A && this.round && !this.round.over && this.fighters().length) this.arenaRound(); // (an online room that opened in this mode, JF_GAME: no startRound came first)
      const A = this.A;
      if (!A || !this.round || this.round.over) return;
      for (const p of this.fighters()) {
        if (p.watch || (p.ai && p.ai.dummy) || !p.team) continue;
        if (!p.mm || p.mm.match !== A.id) { this.arenaEnlist(p, true); if (!p.isBot) this.arenaSend(p); } // (in mid-match: your mech drops onto your spawn too)
        if (p.isBot) { this.arenaFence(p); if (p.alive) this.isleBotMech(p, n); }
      }
      this.isleMeterTick(n, dt * 1000); // the meters (server/islemeter.js): time, and bots call theirs in when it's full
      if (n - A.stT > 2000) { A.stT = n; this.arenaSend(); }
    },
    // bots: fight whoever's near, stay well inside the fence, head for the other team's side when nobody's around
    arenaBotGoal(b) {
      const A = arenaArea(this.map), ai = b.ai, n = now();
      const d = Math.hypot(b.pos[0] - A.c[0], b.pos[2] - A.c[1]);
      const t = this.players.get(ai.target), fighting = t && t.alive && ai.seenAt;
      if (d > A.r - 14) return { p: [A.c[0], b.pos[1], A.c[1]], r: 0, force: true }; // near the fence: back to the middle
      if (fighting && inArena(A, t.pos[0], t.pos[2], -6)) return null; // a fight in here: fight it
      if (!ai.arenaGoal || n > ai.arenaGoalT || Math.hypot(ai.arenaGoal[0] - b.pos[0], ai.arenaGoal[2] - b.pos[2]) < 8) { // somewhere to go: the enemies' pads or the middle
        const pads = A.pads[b.team === 1 ? 2 : 1], g = Math.random() < 0.6 && pads.length ? pads[(Math.random() * pads.length) | 0] : [A.c[0] + (Math.random() - 0.5) * A.r, 0, A.c[1] + (Math.random() - 0.5) * A.r];
        ai.arenaGoal = [g[0], g[1], g[2]]; ai.arenaGoalT = n + 12000 + Math.random() * 8000;
      }
      return { p: ai.arenaGoal, r: 0 };
    },
  });
}
// (the hero list's frames have to be mechs: a new hero is a row in shared/heroes.js + its frame in shared/mech.js)
for (const h of HERO_IDS) if (!MECH[HEROES[h].frame]) console.warn(`arena: hero ${h} has no mech frame`);
