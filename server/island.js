// BATTLE ISLAND on the server, step 1: squads of 3, down-not-dead, revives, squad placements and squad bots.
// It rides on Jank Royale (server/royale.js does the blimp, loot, zone and the bots' looting): this adds the squad rules
// through one-line hooks (grep `isleOn` in server/room.js and server/royale.js). The server owns all of it: who's in
// which squad, who's down, every revive, the bleed-out, who's out and who won. The design: docs/modes/BATTLE_ISLAND.md.
import { GAMES } from '../shared/modes.js';
import { FLAGS } from '../shared/weapons.js';
import { zoneAt, ZONE } from '../shared/royale.js';
import { raycast } from '../shared/physics.js';
import { ISLE, ST } from '../shared/island.js';

const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const hdist = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);
const dist3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const vec3 = (a) => (Array.isArray(a) && a.length === 3 && a.every((x) => typeof x === 'number' && Number.isFinite(x) && Math.abs(x) < 1e6) ? a : null);
const LOG = !!process.env.JF_ISLE_LOG; // test knob: print how every island match went (downs, revives, squads out)
// test knobs: squad size, how many squads, bleed-out and revive seconds
const knob = (k, lo, hi) => { const v = Number(process.env[k]); return Number.isFinite(v) && v >= lo && v <= hi ? v : null; };
if (knob('JF_ISLE_SIZE', 1, 6)) ISLE.size = knob('JF_ISLE_SIZE', 1, 6) | 0;
if (knob('JF_ISLE_SQUADS', 2, 10)) ISLE.squads = knob('JF_ISLE_SQUADS', 2, 10) | 0;
if (knob('JF_ISLE_BLEED', 1, 300)) ISLE.down.bleed = knob('JF_ISLE_BLEED', 1, 300);
if (knob('JF_ISLE_REVIVE', 0.5, 30)) ISLE.revive.hold = knob('JF_ISLE_REVIVE', 0.5, 30);
const CAM = process.env.JF_ISLE_CAM || ''; // test knob: a person with this name is a ride-along camera (can't hurt or be hurt, doesn't count for squads: clips of bots matches)
if (knob('JF_ISLE_GAP', 200, 10000)) ISLE.revive.gap = knob('JF_ISLE_GAP', 200, 10000); // ms a held F may go quiet (slow test browsers stall for seconds on a screenshot)
if (knob('JF_ISLE_ZONE', 0.02, 5)) for (const z of ZONE) { z[0] *= knob('JF_ISLE_ZONE', 0.02, 5); z[1] *= knob('JF_ISLE_ZONE', 0.02, 5); } // x the zone's waits + shrinks (quick test matches; the royale's too)

// what a downed pilot can't do: shoot, swing, throw, call streaks, revive, loot, heal, hop in a cart or a mech
const DOWN_STOP = new Set(['fire', 'hit', 'push', 'slam', 'item', 'deploy', 'tbag', 'use', 'parry', 'spray', 'cart', 'car', 'rig', 'mech', 'lasso', 'lh', 'nv', 'brpick', 'brheal', 'brkick', 'brdrop', 'brswap', 'cough', 'lava']); // (cough: no running down your own clock)

export function installIsland(Room, H) {
  const { send, movePlayer } = H;
  Object.defineProperty(Room.prototype, 'isleOn', { get() { return this.brOn && !!GAMES[this.game].squads; } });
  Object.assign(Room.prototype, {
    // ---------------------------------------------------------- squads
    // who plays this match (the royale's riders + anyone who's out), in this match
    isleIn(p) { return !!(p && p.br && this.br && p.br.match === this.br.id && p.sq); },
    isleMates(sq) { return this.fighters().filter((p) => p.sq === sq && this.isleIn(p)); },
    // up = alive and on their feet (riding the blimp counts: they're not out)
    isleUp(p) { return !!(p && p.alive && !p.dn && p.br && !p.br.out && !p.goblin && !p.cam); },
    isleFriendly(a, b) { return (!!a.sq && a.sq === b.sq) || !!a.cam || !!b.cam; }, // (friendly() hook: your squad)
    isleSquadsIn() { const s = new Set(); for (const p of this.fighters()) if (this.isleIn(p) && this.isleUp(p)) s.add(p.sq); return s; },
    // a match starts (brBoard hook): everyone gets a squad, people first in the order they came in (so a lobby's
    // people land together), then bots fill the gaps. late boarders get the emptiest squad that's still in
    isleBoard(p) {
      const B = this.br;
      const fresh = !B.isle;
      if (fresh) {
        B.isle = { sqOut: new Map(), peak: 0, t: now(), stT: 0, log: [] };
        const list = this.fighters().filter((o) => !o.goblin).sort((a, b) => (a.isBot - b.isBot) || a.id - b.id);
        const size = list.length <= ISLE.size ? Math.max(1, Math.ceil(list.length / 2)) : ISLE.size; // (too few for two squads: split them, or nobody could win)
        list.forEach((o, i) => { o.sq = Math.floor(i / size) + 1; o.dn = null; o.irv = null; }); // (more than squads x size: extra squads, never a 4th in one)
      }
      p.br.mailed = true; // no RETURN TO SENDER here: your squad picks you up instead
      p.cam = !!CAM && !p.isBot && p.name === CAM;
      p.dn = null; p.irv = null;
      if (!fresh || !p.sq) p.sq = this.isleFreeSquad(p); // a late boarder
    },
    // a late boarder's squad: while fewer than two squads are in it, a new one (or nobody could ever win). otherwise the
    // fullest squad that still has room (you land with whoever came in before you), else a new one. never a full one
    isleFreeSquad(p) {
      const I = this.br.isle, c = new Map(), live = new Set();
      for (const o of this.fighters()) if (o !== p && o.sq && this.isleIn(o)) { c.set(o.sq, (c.get(o.sq) || 0) + 1); if (o.alive && !o.br.out) live.add(o.sq); }
      const fresh = () => { for (let s = 1; ; s++) if (!c.has(s) && !I.sqOut.has(s)) return s; };
      if (live.size < 2) return fresh();
      let best = 0, bn = -1;
      for (const [s, n] of c) if (live.has(s) && !I.sqOut.has(s) && n < ISLE.size && n > bn) { bn = n; best = s; }
      return best || fresh();
    },
    // everyone's squad, for every client (markers, colours, the kill feed)
    isleSquads() { return this.fighters().filter((p) => p.sq && p.br && this.br && p.br.match === this.br.id).map((p) => [p.id, p.sq]); },
    isleStart() { if (this.br && this.br.isle) { this.isleHeroAll(); this.broadcast({ t: 'isle', k: 'sq', l: this.isleSquads(), size: ISLE.size, hero: this.isleHeroList() }); } },
    isleJoin(p) { if (this.br && this.br.isle && !p.isBot) send(p, { t: 'isle', k: 'sq', l: this.isleSquads(), size: ISLE.size, dn: this.fighters().filter((o) => o.dn && o.alive).map((o) => o.id), hero: this.isleHeroList() }); },

    // ---------------------------------------------------------- down, not dead
    // damage hook: this hit would kill t. down instead, if someone in the squad is still up (true = downed)
    isleDown(t, attacker, w) {
      if (!this.isleIn(t) || t.dn || t.br.out || t.br.inBlimp || t.goblin || w === 'void') return false;
      if (this.mechOn && this.mechOn(t)) return false;
      if (!this.isleMates(t.sq).some((o) => o !== t && this.isleUp(o))) return false; // the last one up: the squad's done
      const n = now();
      t.hp = 1;
      const shoved = n - (t.knockT || 0) < 300 && w !== 'zone'; // (the hit that put you down shoved you: you land where it threw you)
      t.dn = { left: ISLE.down.bleed * 1000, by: attacker && attacker !== t ? attacker.id : 0, w, t0: n, rv: 0, last: t.pos.slice(), bank: ISLE.down.slack + (shoved ? 8 : 2), ub: shoved ? 4 : 1, flung: shoved ? n + ISLE.down.flung : 0, snapT: n, fixT: 0 };
      t.br.heal = null; t.br.fly = null; t.g = null; t.f &= ~FLAGS.GLIDE;
      if (t.irv) this.isleRvStop(t, 'down');
      if (t.isBot && t.ai) { t.ai.hook = null; t.ai.route = null; }
      this.broadcast({ t: 'isle', k: 'down', id: t.id, by: t.dn.by, w });
      if (attacker && attacker !== t && attacker.br) attacker.br.knocks = (attacker.br.knocks || 0) + 1;
      if (LOG) this.br.isle.log.push(`${t.name} (sq${t.sq}) DOWN by ${attacker && attacker !== t ? attacker.name : w}`);
      return true;
    },
    // damage hook: a hit on someone who's down eats their bleed-out clock (enough of it finishes them)
    isleHit(t, amt, attacker, w) {
      const d = t.dn;
      d.left -= amt * ISLE.down.hurt * 1000;
      if (attacker && attacker !== t) this.isleMeter(attacker, amt * ISLE.meter.dmg, 'dmg');
      this.tag(t, attacker, w);
      this.broadcast({ t: 'dmg', to: t.id, from: attacker ? attacker.id : 0, a: Math.round(Math.min(amt, 999)), w, dn: 1 });
      if (d.left <= 0) {
        const fin = attacker && attacker !== t ? attacker : this.players.get(d.by) || null;
        if (LOG) this.br.isle.log.push(`${t.name} FINISHED by ${fin ? fin.name : w}`);
        this.kill(t, fin, attacker && attacker !== t ? w : d.w || w);
      }
      return true;
    },
    // ran out of time on the floor: the kill goes to whoever put them there
    isleBleed(t) {
      const d = t.dn, by = this.players.get(d.by) || null;
      if (LOG) this.br.isle.log.push(`${t.name} BLED OUT (downed by ${by ? by.name : d.w})`);
      this.kill(t, by, d.w || 'zone');
    },
    // the crawl: movement is the client's, so the server holds a downed pilot to a crawl: a budget of metres that fills
    // at crawl speed, and a budget for going up that fills slowly (slopes, a kerb). a real shove (isleKnock: a hit, not
    // the zone's push) lets you fly about for a moment and pays for the height it throws you. no rope, no jumping, and
    // no glide / slide / sprint flags (everyone sees you on the floor)
    isleSnap(p, m) {
      const d = p.dn, pos = vec3(m.p), n = now();
      m.g = 0; m.f = 0;
      if (!pos) return;
      const dt = Math.min(0.5, Math.max(0, (n - d.snapT) / 1000));
      d.snapT = n;
      const flung = n < d.flung, pushed = n < (d.push || 0), S = ISLE.down.slack;
      const cap = flung ? Math.max(8, d.bank) : pushed ? Math.min(Math.max(S, d.bank), S + 2) : S; // (what a shove paid for only lasts while you're flying)
      d.bank = Math.min(cap, d.bank + (flung ? 22 : ISLE.down.crawl * 1.25) * dt);
      d.ub = Math.min(flung ? Math.max(1.2, d.ub) : 1.2, d.ub + 0.6 * dt);
      const moved = hdist(pos, d.last), rise = pos[1] - d.last[1];
      d.bank -= moved;
      if (rise > 0) d.ub -= rise;
      if (d.bank < -0.01 || d.ub < -0.05) {
        m.p = d.last.slice(); m.v = [0, Math.min(0, Array.isArray(m.v) && Number.isFinite(m.v[1]) ? m.v[1] : 0), 0];
        d.bank = 0; d.ub = Math.max(0, d.ub);
        if (n - d.fixT > 300) { d.fixT = n; d.fixes = (d.fixes || 0) + 1; send(p, { t: 'isle', k: 'fix', p: d.last.map(r2) }); }
        return;
      }
      d.last = pos.slice();
    },

    // knock() hook (people only: bots are moved here): a shove pays for where it throws you. the zone's push buys only
    // its own few metres, not a free run
    isleKnock(t, v, w) {
      const d = t.dn;
      if (!d || t.isBot) return;
      const up = Math.max(0, v[1]), h = Math.hypot(v[0], v[2]);
      if (w === 'zone') { d.push = now() + 600; d.bank += Math.min(2, h / 5); d.ub += Math.min(0.4, up * up / 52 + 0.1); return; } // (a push slides a crawler about v / 5 m)
      d.flung = now() + ISLE.down.flung;
      d.bank += h * 1.2; d.ub += up * up / 52 + 1;
    },

    // ---------------------------------------------------------- revives (hold F: 'use' every 200 ms while it's held)
    isleCanRevive(p) { return this.isleIn(p) && this.isleUp(p) && !p.br.inBlimp && !p.br.fly && !(this.mechOn && this.mechOn(p)) && !p.trap; },
    isleReach(p, t) {
      const R = ISLE.revive;
      if (hdist(p.pos, t.pos) > R.r + R.slack || Math.abs(p.pos[1] - t.pos[1]) > R.dy) return false;
      const a = [p.pos[0], p.pos[1] + 1.1, p.pos[2]], clear = (y) => { const dv = [t.pos[0] - a[0], t.pos[1] + y - a[1], t.pos[2] - a[2]], l = Math.hypot(dv[0], dv[1], dv[2]) || 1; return !raycast(a, [dv[0] / l, dv[1] / l, dv[2] / l], l, this.boxes); };
      return clear(0.35) || clear(0.9); // your chest to their body or shoulders: not through a wall (a kerb in the way is fine)
    },
    isleUse(p) {
      const n = now(), R = ISLE.revive;
      if (n - (p.isleUseT || 0) < 90) return; // (the client sends 5 a second; anything faster buys nothing)
      p.isleUseT = n;
      if (!this.isleCanRevive(p)) { if (p.irv) this.isleRvStop(p, 'cant'); return; }
      const rv = p.irv, cur = rv && this.players.get(rv.id);
      if (cur && cur.dn && cur.dn.rv === p.id && this.isleReach(p, cur) && n - rv.last <= R.gap) { rv.last = n; return; } // still holding
      if (rv) this.isleRvStop(p, 'swap');
      // a new one: the nearest downed squadmate in reach that nobody else is picking up
      let best = null, bd = 1e9;
      for (const t of this.players.values()) {
        if (t === p || !t.alive || !t.dn || t.sq !== p.sq || !this.isleIn(t) || (t.dn.rv && t.dn.rv !== p.id) || !this.isleReach(p, t)) continue;
        const d = dist3(p.pos, t.pos);
        if (d < bd) { bd = d; best = t; }
      }
      if (!best) return;
      p.irv = { id: best.id, t0: n, last: n };
      best.dn.rv = p.id;
      this.broadcast({ t: 'isle', k: 'rv', id: best.id, by: p.id, ms: R.hold * 1000 });
    },
    isleRvStop(p, why) {
      const rv = p.irv, t = rv && this.players.get(rv.id);
      p.irv = null;
      if (t && t.dn && t.dn.rv === p.id) { t.dn.rv = 0; this.broadcast({ t: 'isle', k: 'rvx', id: t.id, by: p.id, why }); }
    },
    // the reviver of t that's still holding on (null = nobody: the clock runs)
    isleReviver(t, n) {
      const p = t.dn && t.dn.rv ? this.players.get(t.dn.rv) : null;
      if (!p || !p.irv || p.irv.id !== t.id) { if (t.dn) t.dn.rv = 0; return null; }
      if (n - p.irv.last > ISLE.revive.gap || !this.isleCanRevive(p) || !this.isleReach(p, t)) { this.isleRvStop(p, n - p.irv.last > ISLE.revive.gap ? 'let go' : 'moved'); return null; }
      return p;
    },
    isleRevive(t, by) {
      if (by) { by.irv = null; if (by.br) by.br.revives = (by.br.revives || 0) + 1; }
      t.dn = null;
      t.hp = ISLE.revive.hp;
      t.spawnT = 0; t.knockT = now(); // (the crawl budget is gone: back on your feet wherever you are)
      if (t.isBot && t.ai) { t.ai.route = null; t.ai.target = 0; }
      this.broadcast({ t: 'isle', k: 'up', id: t.id, by: by ? by.id : 0 });
      this.broadcast({ t: 'heal', id: t.id, a: ISLE.revive.hp - 1, hp: ISLE.revive.hp });
      if (LOG) this.br.isle.log.push(`${t.name} REVIVED by ${by ? by.name : '?'}`);
    },

    // ---------------------------------------------------------- deaths, squads out, placements
    // brKill's placement: 0 (not yet) while anyone in the squad is still up; the squad's place once it's out
    islePlace(t) {
      const I = this.br.isle;
      if (!I || !t.sq) return this.brAlive().length + 1;
      if (I.sqOut.has(t.sq)) return I.sqOut.get(t.sq);
      if (this.isleMates(t.sq).some((o) => o !== t && this.isleUp(o))) return 0;
      const place = [...this.isleSquadsIn()].filter((s) => s !== t.sq).length + 1;
      I.sqOut.set(t.sq, place);
      return place;
    },
    // kill hook (after brKill): nobody up in the squad = it's out. whoever's still down is finished off (the kill to
    // whoever put them down) and everyone in it gets the squad's place
    isleKilled(t, killer, w) {
      if (t.irv) this.isleRvStop(t, 'dead');
      if (t.dn) { const rv = t.dn.rv && this.players.get(t.dn.rv); if (rv && rv.irv) rv.irv = null; t.dn = null; this.broadcast({ t: 'isle', k: 'dead', id: t.id }); }
      const B = this.br, I = B && B.isle;
      if (LOG && I && t.sq) I.log.push(`${t.name} (sq${t.sq}) DEAD to ${killer && killer !== t ? killer.name : w}`);
      if (I && killer && killer !== t && !this.friendly(killer, t) && w !== 'left') this.isleMeter(killer, ISLE.meter.kill, 'kill');
      if (!I || !t.sq || !this.isleIn(t) || this.isleMates(t.sq).some((o) => this.isleUp(o))) return;
      const sq = t.sq, first = !I.done || !I.done.has(sq);
      if (!first) return;
      (I.done ||= new Set()).add(sq);
      if (!I.sqOut.has(sq)) I.sqOut.set(sq, [...this.isleSquadsIn()].length + 1);
      const place = I.sqOut.get(sq);
      for (const o of this.isleMates(sq)) if (o.alive && o.dn) this.kill(o, this.players.get(o.dn.by) || killer || null, o.dn.w || w);
      for (const o of this.isleMates(sq)) {
        if (!o.br.out) continue;
        o.br.place = place;
        const e = B.out.find((x) => x.id === o.id);
        if (e) e.place = place;
      }
      this.broadcast({ t: 'isle', k: 'sqout', sq, place, ids: this.isleMates(sq).map((o) => o.id), left: this.isleSquadsIn().size });
      if (LOG) I.log.push(`SQUAD ${sq} OUT: #${place} (${this.isleMates(sq).map((o) => o.name).join(', ')})`);
    },
    // last squad standing (tickBR hook, in place of royale's last one standing)
    isleWinCheck(n) {
      const B = this.br, I = B.isle;
      if (!I || B.endAt) return;
      const sqs = this.isleSquadsIn();
      I.peak = Math.max(I.peak, sqs.size);
      if (!((I.peak >= 2 && sqs.size <= 1) || !sqs.size || n >= this.round.ends)) return;
      let win = sqs.size === 1 ? [...sqs][0] : 0;
      if (!win && sqs.size > 1) { // out of time: the squad with the most people up
        const c = new Map();
        for (const p of this.fighters()) if (this.isleIn(p) && this.isleUp(p)) c.set(p.sq, (c.get(p.sq) || 0) + 1);
        const top = [...c].sort((a, b) => b[1] - a[1]);
        if (top.length && (top.length === 1 || top[0][1] > top[1][1])) win = top[0][0];
      }
      const mates = win ? this.isleMates(win) : [];
      for (const p of mates) p.br.place = 1;
      const up = mates.filter((p) => this.isleUp(p)), w0 = up[0] || mates[0];
      B.winner = w0 ? w0.id : 0;
      I.win = win;
      B.endAt = n + 3200;
      this.broadcast({ t: 'br', k: 'win', id: B.winner, sq: win, ids: mates.map((p) => p.id) });
      this.broadcast({ t: 'isle', k: 'win', sq: win, ids: mates.map((p) => p.id) }); // (the squad callout: clients hear 'br' in royale.js)
      if (LOG) {
        I.log.push(win ? `WINNERS: squad ${win} (${mates.map((p) => `${p.name}${p.isBot ? '' : '*'} ${p.br.kills || 0}k ${p.br.knocks || 0}kn ${p.br.revives || 0}rv${this.isleUp(p) ? '' : p.dn ? ' (down)' : ' (dead)'}`).join(', ')}), ${Math.round((n - B.t0) / 1000)}s` : 'no winner');
        console.log('[isle] ' + I.log.join('\n[isle] '));
      }
    },
    // the round's end: every squad and its place (the end screen groups them)
    isleResults() {
      const B = this.br, I = B && B.isle;
      if (!I) return undefined;
      const sq = new Map();
      for (const p of this.fighters()) if (this.isleIn(p)) { const e = sq.get(p.sq) || { sq: p.sq, place: I.win === p.sq ? 1 : I.sqOut.get(p.sq) || 0, ids: [] }; e.ids.push(p.id); sq.set(p.sq, e); }
      return { win: I.win || 0, sq: [...sq.values()].map((e) => [e.sq, e.place, e.ids]) };
    },

    // ---------------------------------------------------------- the clock (tickBR hook)
    tickIsle(n) {
      const I = this.br && this.br.isle;
      if (!I) return;
      const dt = Math.min(250, Math.max(0, n - I.t));
      I.t = n;
      for (const t of [...this.players.values()]) {
        if (!t.dn || !t.alive) continue;
        const rv = this.isleReviver(t, n);
        if (rv) { if (n - rv.irv.t0 >= ISLE.revive.hold * 1000 - 30) this.isleRevive(t, rv); continue; } // the clock waits while someone's on it
        if (this.br.endAt) continue; // (the match is won: nobody bleeds out in the last 3 s)
        t.dn.left -= dt;
        if (t.dn.left <= 0) this.isleBleed(t);
      }
      for (const p of this.players.values()) if (p.irv && !this.players.get(p.irv.id)) p.irv = null; // (they left)
      this.isleMeterTick(n, dt); // the mech meters (server/islemeter.js)
      if (n - I.stT >= 400) { I.stT = n; this.isleStatus(n); }
    },
    // the squad HUD: each squad hears about its own (hp, down + bleed left, who's picking them up)
    isleStatus(n) {
      const by = new Map();
      for (const p of this.fighters()) {
        if (!this.isleIn(p)) continue;
        const st = !p.alive || p.br.out ? ST.OUT : p.dn ? ST.DOWN : p.br.inBlimp || p.br.fly ? ST.SKY : ST.UP;
        const row = [p.id, Math.max(0, Math.round(p.hp)), st, p.dn ? Math.max(0, Math.round(p.dn.left / 100)) : 0, p.dn && p.dn.rv ? p.dn.rv : 0];
        (by.get(p.sq) || by.set(p.sq, []).get(p.sq)).push(row);
      }
      for (const p of this.players.values()) if (!p.isBot && p.sq && by.has(p.sq) && this.isleIn(p)) send(p, { t: 'isle', k: 'st', sq: p.sq, m: by.get(p.sq) });
    },

    // ---------------------------------------------------------- messages (true = swallowed: a downed pilot can't)
    isleHandle(p, m) {
      if (m.t === 'use' && m.up === 1) { if (p.irv) this.isleRvStop(p, 'let go'); return true; } // F let go: it stops now, not after the gap
      if (p.irv && (m.t === 'fire' || m.t === 'hit' || m.t === 'push') && !p.dn) this.isleRvStop(p, 'shot'); // shooting puts the revive down
      if (m.t === 'hero') { this.isleHeroPick(p, m.h); return true; } // the hero pick (server/islemeter.js)
      if (m.t === 'deploy' && !p.dn) { this.isleCall(p, m); return true; } // the streak key: your mech, when the meter's full
      if (!p.dn || !p.alive) return false;
      if (m.t === 's') { if (m.q === p.seq) this.isleSnap(p, m); return false; }
      return DOWN_STOP.has(m.t);
    },

    // ---------------------------------------------------------- bots
    // the squad's jumpmaster: its first person, else its first bot. the others jump when it does and glide after it
    isleLead(b) {
      const m = this.isleMates(b.sq).filter((o) => o.alive && !o.br.out);
      return m.find((o) => !o.isBot) || m.sort((a, c) => a.id - c.id)[0] || null;
    },
    // brJump hook: the squad's bots still on board follow the jumpmaster out
    isleJumped(p) {
      if (!this.isleIn(p) || this.isleLead(p) !== p) return;
      for (const b of this.isleMates(p.sq)) {
        if (b === p || !b.isBot || !b.br.inBlimp) continue;
        if (!b.br.ai) b.br.ai = this.brBotBrain(b);
        this.brJump(b);
        b.br.follow = p.id;
      }
    },
    // stepBot hook (before the royale's): down = crawl; on the blimp = wait for the jumpmaster; gliding = after it
    isleBotStep(b, dt) {
      const s = b.br;
      if (!this.isleIn(b) || s.out || !b.alive) return false;
      if (b.dn) { this.isleCrawl(b, dt); return true; }
      if (!s.inBlimp && !s.fly) this.isleBotMech(b, now()); // (server/islemeter.js: back into a mech that's waiting)
      const lead = this.isleLead(b);
      if (s.inBlimp && lead && lead !== b) { if (!lead.br.inBlimp) { if (!s.ai) s.ai = this.brBotBrain(b); this.brJump(b); s.follow = lead.id; } return true; }
      const f = s.fly && s.ai && this.players.get(s.follow);
      if (f && f.alive) { const a = (b.id % 3) * 2.1; s.ai.drop = [f.pos[0] + Math.cos(a) * 4, f.pos[1], f.pos[2] + Math.sin(a) * 4]; } // land next to them
      return false;
    },
    // a downed bot drags itself toward whoever's up in its squad
    isleCrawl(b, dt) {
      const v = b.vel, C = ISLE.down.crawl;
      let m = null, md = 1e9;
      for (const o of this.isleMates(b.sq)) if (o !== b && this.isleUp(o) && !o.br.inBlimp) { const d = hdist(o.pos, b.pos); if (d < md) { md = d; m = o; } }
      let wx = 0, wz = 0;
      if (m && md > 1.4) { wx = (m.pos[0] - b.pos[0]) / md; wz = (m.pos[2] - b.pos[2]) / md; b.yaw = Math.atan2(-wx, -wz); }
      if (b.onGround) { const k = Math.min(1, dt * 5); v[0] += (wx * C - v[0]) * k; v[2] += (wz * C - v[2]) * k; }
      v[1] -= 26 * dt;
      const res = movePlayer(b.pos, v, dt, this.boxes, b.onGround);
      b.onGround = !!res.ground && v[1] <= 0.01;
      b.f = 0; b.g = null;
      if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
    },
    // botGoal hook: the zone first, then pick up a downed squadmate (when it's safe enough), then stay with the squad
    isleBotGoal(b) {
      const s = b.br;
      if (!this.isleIn(b) || s.out || s.inBlimp || s.fly || !s.ai || b.dn) return this.brBotGoal(b);
      const n = now(), ai = s.ai, zn = zoneAt(this.br.zone, n);
      if (zn && Math.hypot(b.pos[0] - zn.c[0], b.pos[2] - zn.c[1]) > zn.r - 3) return this.brBotGoal(b); // (the royale's zone run)
      const t = this.players.get(b.ai.target), threat = t && t.alive && !t.dn && b.ai.seenAt && dist3(t.pos, b.pos) < ISLE.safe;
      let dn = null, dd = 60;
      for (const o of this.isleMates(b.sq)) if (o !== b && o.alive && o.dn && (!o.dn.rv || o.dn.rv === b.id)) { const d = hdist(o.pos, b.pos); if (d < dd) { dd = d; dn = o; } }
      if (dn && (!threat || b.irv)) { ai.why = 'revive'; return { p: dn.pos, use: true, r: ISLE.revive.r - 0.6, force: true }; }
      const g = this.brBotGoal(b);
      if (ai.why === 'zone' || ai.why === 'rotate' || ai.why === 'unstuck') return g;
      const h = this.isleBuddy(b);
      if (!h) return g;
      const cap = h.isBot ? ISLE.stick * 1.4 : ISLE.stick, d = hdist(b.pos, h.pos);
      if (d > cap) { ai.why = 'regroup'; return { p: h.pos, force: d > cap * 1.6, r: 0 }; }
      if (g && hdist(g.p, h.pos) <= cap) return g; // loot near the squad: fine
      const a = (b.id % 5) * 1.25 + 0.6; // otherwise hang about near them (each bot its own spot)
      ai.why = 'squad';
      return { p: [h.pos[0] + Math.cos(a) * 5, h.pos[1], h.pos[2] + Math.sin(a) * 5], r: 0 };
    },
    // who a bot sticks with: the nearest person in its squad who's up and landed, else (all-bot squads) the leader
    isleBuddy(b) {
      let h = null, hd = 1e9;
      for (const o of this.isleMates(b.sq)) if (o !== b && !o.isBot && this.isleUp(o) && !o.br.inBlimp && !o.br.fly) { const d = hdist(o.pos, b.pos); if (d < hd) { hd = d; h = o; } }
      if (h) return h;
      const l = this.isleLead(b);
      return l && l !== b && this.isleUp(l) && !l.br.inBlimp && !l.br.fly ? l : null;
    },
    // botTarget hook: leave people who are down alone, unless they're the last enemy there is
    isleBotTargetOk(b, t) {
      if (!t.dn) return true;
      for (const o of this.players.values()) if (o !== b && this.isleIn(o) && this.isleUp(o) && !o.br.inBlimp && !this.friendly(b, o)) return false;
      return true;
    },
  });
}
