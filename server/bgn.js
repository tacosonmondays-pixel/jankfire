// BOARD GAME NIGHT (docs/party/DESIGN.md): the party board mode on top of an ordinary bots / ffa Room. 4 seats (bots fill),
// the foam die, the kitchen-table board, coupons, golden bread, the corner store, duels, and an end-of-round minigame
// that's one of our own modes on a small map with a short clock. the server owns every number: clients only send
// choices ({ t: 'bg', k, ... }: roll, use, path, bread, buy, stake, who, house, ok), checked against the seat whose turn it is.
// room.bgn = the board, p.bench = sitting out (on the board everyone is). the board runs its own clock from tickRound;
// a minigame is a normal round (startRound) that endRound hands back here. mixed into Room by installBgn.
// (room.js imports this: browser-safe, no node: imports. the story's referee runs room.js in a worker)
import { BGN, BGN_NAMES, BGN_ITEMS, BGN_ITEM_ORDER, BGN_JANK_ORDER, BGN_HOUSE, BGN_MINIS, BGN_MINI_ORDER, BGN_FMTS, bgnRng } from '../shared/bgn.js';
import { BOARD, PLATE_IDS, LID, isSpace, aheadSet, loopDist } from '../shared/bgnboard.js';
import { GAMES, TEAMS, rollLadder, mapForGame } from '../shared/modes.js';
import { MAPS } from '../shared/map.js';
import { LOBBY } from '../shared/lobby.js';
import { randomContainer } from '../shared/cosmetics.js';
import { hubBackOpen, hubBackDue } from './hubback.js';
import { installBgnBots } from './bgnbots.js';
import { installBgnMini } from './bgnmini.js'; // minigames 11-15: the big guy, the bosses, bumper carts, duck catch

const E = (typeof process !== 'undefined' && process.env) || {};
const num = (v) => (v == null || v === '' ? NaN : Number(v));
// test knobs (docs/party/DESIGN.md 4.6)
const K = {
  rounds: Number.isInteger(num(E.JF_BGN_ROUNDS)) && num(E.JF_BGN_ROUNDS) > 0 ? Math.min(30, num(E.JF_BGN_ROUNDS)) : 0, // rounds per game
  fast: num(E.JF_BGN_FAST) > 1 ? Math.min(100, num(E.JF_BGN_FAST)) : 1, // board timings / this
  die: String(E.JF_BGN_DIE || '').split(',').map(Number).filter((v) => Number.isInteger(v) && v >= 1 && v <= 6), // the die rolls these first
  mg: E.JF_BGN_MG ? (Object.hasOwn(BGN_MINIS, E.JF_BGN_MG) ? E.JF_BGN_MG : BGN_MINI_ORDER.find((k) => BGN_MINIS[k].game === E.JF_BGN_MG) || null) : null, // force the minigame
  fmt: BGN_FMTS.includes(E.JF_BGN_FMT) ? E.JF_BGN_FMT : null, // force the format
  mgTime: num(E.JF_BGN_MGTIME) > 0 ? num(E.JF_BGN_MGTIME) : 0, // minigame seconds
  coupons: num(E.JF_BGN_COUPONS) >= 0 ? Math.floor(num(E.JF_BGN_COUPONS)) : null,
  price: num(E.JF_BGN_PRICE) > 0 ? Math.floor(num(E.JF_BGN_PRICE)) : 0,
  round: num(E.JF_BGN_ROUND) > 1 ? Math.floor(num(E.JF_BGN_ROUND)) : 1, // start at this round
  botDuel: !!E.JF_BGN_BOTDUEL, // bot vs bot duels get played out
  seed: num(E.JF_BGN_SEED) > 0 ? Math.floor(num(E.JF_BGN_SEED)) : 0, // seeded dice and board picks
  bakery: Number.isInteger(num(E.JF_BGN_BAKERY)) ? num(E.JF_BGN_BAKERY) : null, // the bakery starts on this plate
};
const T = (ms) => Math.max(1, Math.round(ms / K.fast));
const now = () => Date.now();
const has = (o, k) => typeof k === 'string' && Object.hasOwn(o, k);
const SEAT_COLORS = ['#ff4fd8', '#4fd8ff', '#ffe14d', '#7dff4f'];
const FIGHT = new Set(['fire', 'hit', 'deploy', 'item', 'use', 'push', 'parry', 'spray', 'tbag', 'respawn', 'lasso', 'lh', 'rig', 'mech', 'ans', 'reset', 'slam']);
const ASKS = ['roll', 'use', 'path', 'bread', 'buy', 'stake', 'who', 'house', 'ok'];
export const BGN_KNOBS = K;

export function installBgn(Room, H) {
  const { send, stat, store } = H;
  installBgnBots(Room);
  const P = Room.prototype;
  Object.assign(P, {
    // ---------------------------------------------------------------- start, seats, bench
    bgnStart(rounds) {
      const rng = K.seed ? bgnRng(K.seed) : Math.random;
      const want = K.rounds || (BGN.roundOpts.includes(rounds) ? rounds : BGN.rounds);
      const B = this.bgn = {
        ph: 'intro', round: Math.min(K.round, want), rounds: want, last: null, lastOn: false, seats: [], order: [], turn: 0,
        bakery: PLATE_IDS.includes(K.bakery) ? K.bakery : PLATE_IDS[Math.floor(rng() * PLATE_IDS.length)], traps: new Map(), ask: null, walk: null, mg: null, res: null, final: null,
        hist: { fmt: [], mg: [], jank: null, duel: [] }, at: 0, next: null, used: false, cart: false, rng, dieQ: K.die.slice(), ok: new Set(), queue: [], cont: null,
      };
      this.game = 'bgn';
      this.score = { 1: 0, 2: 0 };
      const people = this.humans().filter((p) => !p.watch);
      const bots = [...this.players.values()].filter((p) => p.isBot && !(p.ai && p.ai.dummy));
      for (let i = 0; i < BGN.seats; i++) {
        let p = people[i];
        if (!p) p = bots.shift() || this.addBot();
        B.seats.push({ i, pid: p.id, name: this.bgnName(p), color: SEAT_COLORS[i], bot: !!p.isBot, coupons: K.coupons ?? BGN.coupons, bread: 0,
          at: LID, stuck: false, bag: [], lassoR: 0, trail: [], stats: { duels: 0, spent: 0, mgWins: 0 } });
      }
      for (const b of bots) this.remove(b); // (more bots than seats: the rest go home)
      for (const p of people.slice(BGN.seats)) B.queue.push(p.id); // (a party of 5-6: the extras wait for a seat, like a late joiner)
      for (const p of this.players.values()) { this.bgnBench(p, true); if (p.air) { p.air = null; send(p, { t: 'air', end: 1, ok: 0 }); } } // (no Never Landed run: the online lobby's startRound may have started one)
      this.assignTeams(); // everyone back in their own colours
      if (this.round) { this.round.over = false; this.round.ends = now() + 3600e3; this.round.target = 0; }
      this.bgnState();
      this.bgnSay('intro');
      this.bgnLater(BGN.introMs, () => this.bgnDibs());
      console.log(`[bgn] ${this.id}: board game night, ${want} rounds, ${people.length} human(s)`);
    },
    bgnName(p) { return String(p.name || '').replace(/ \[bot\]$/, '').slice(0, 20); },
    bgnKey(p) { return p.acct ? 'a:' + p.acct.n : 'n:' + p.name; }, // who someone is, for coming back to their seat (an account, else the name)
    // roomFor (online lobby): is a seat here kept warm for whoever this is? (they dropped out: their bot has it)
    bgnBackFor(key) { const B = this.bgn; return !!(B && this.lobby && !this.closed && B.ph !== 'done' && B.seats.some((s) => s.bot && s.back === key)); },
    // sitting out: dead with no respawn (the JF_WATCH observer's trick, but switchable)
    bgnBench(p, on) {
      p.bench = !!on;
      if (!on) return;
      if (p.alive) { p.alive = false; p.hp = 0; }
      p.respawnAt = p.minRespawnAt = Infinity; p.vel = [0, 0, 0];
      this.resetLife(p); // no rig, mech, rope or ball carries over
    },
    bgnSeatOf(p) { return this.bgn ? this.bgn.seats.find((s) => s.pid === p.id) || null : null; },
    bgnPlayer(s) { return this.players.get(s.pid) || null; },
    // how many bots fillBots should keep: exactly the ones in seats (+ none to add). the board does its own seating
    bgnBotWant() { return [...this.players.values()].filter((p) => p.isBot && !(p.ai && p.ai.dummy) && !p.leaving).length; },
    // a human walked in (addHuman): the first one in a bgn room starts the night, later ones wait for a bot's seat
    bgnJoin(p, m) {
      if (!this.bgn) {
        if (this.game !== 'bgn' || this.lobby) return;
        const c = m && m.cfg && typeof m.cfg === 'object' ? m.cfg : {};
        this.bgnStart(Number.isInteger(c.rounds) ? c.rounds : this.cfg.bgnRounds);
        if (p.air) { p.air = null; send(p, { t: 'air', end: 1, ok: 0 }); }
        return;
      }
      this.bgnBench(p, true);
      if (p.air) { p.air = null; send(p, { t: 'air', end: 1, ok: 0 }); } // (no Never Landed run on a board)
      if (!p.watch && !p.isBot) this.bgn.queue.push(p.id);
      if (this.bgn.ph === 'intro' || this.bgn.ph === 'dibs') this.bgnSeatQueue();
      send(p, { t: 'bg', k: 'st', s: this.bgnInfo() });
    },
    // between turns: people waiting take bots' seats (coupons, bread and bag come with the seat)
    bgnSeatQueue() {
      const B = this.bgn;
      while (B.queue.length) {
        const p = this.players.get(B.queue[0]);
        if (!p || this.bgnSeatOf(p)) { B.queue.shift(); continue; }
        const free = (x) => x.bot && !(B.ask && B.ask.seat === x.i) && !(B.walk && B.walk.seat === x.i);
        const own = B.seats.find((x) => x.bot && x.back === this.bgnKey(p)), s = own ? (free(own) ? own : null) : B.seats.find(free); // back from a disconnect: your own seat ("<name>'s bot" gives it back), as soon as it's between turns
        if (!s) return;
        B.queue.shift();
        const b = this.players.get(s.pid);
        s.pid = p.id; s.bot = false; s.name = this.bgnName(p); s.back = null;
        if (b) this.remove(b);
        this.broadcast({ t: 'chat', id: 0, m: `${s.name} took a seat at the table` });
        this.bgnState();
      }
    },
    // a human left (remove): a bot takes their seat at once, named after them, on their side
    bgnLeave(p) {
      const B = this.bgn;
      if (!B || p.isBot) return;
      B.queue = B.queue.filter((id) => id !== p.id);
      const s = B.seats.find((x) => x.pid === p.id);
      if (!s || !this.humans().length) return;
      const b = this.addBot();
      b.name = `${s.name}'s bot`.slice(0, 24);
      this.broadcast({ t: 'pj', ...this.info(b) }); // (the new name)
      s.pid = b.id; s.bot = true; s.name = b.name; s.back = this.bgnKey(p); // (they can come back to it)
      const mg = B.mg;
      if (B.ph === 'mg' && mg && mg.seats.includes(s.i)) { this.bgnSide(b); this.broadcast({ t: 'teams', game: this.game, list: [[b.id, b.team || 0, b.color]] }); }
      else this.bgnBench(b, true);
      if (B.ask && B.ask.seat === s.i) { B.ask.until = Math.min(B.ask.until, now() + 1000); B.ask.botAt = now() + 1000; } // mid-choice: the bot answers in a second
      this.broadcast({ t: 'chat', id: 0, m: `${p.name} left. a bot is keeping their seat warm` });
      this.bgnState();
    },

    // ---------------------------------------------------------------- the clock (tickRound: true = handled)
    bgnLater(ms, fn) { this.bgn.at = now() + T(ms); this.bgn.next = fn; },
    bgnTick(n) {
      const B = this.bgn;
      if (B.ph === 'mg') { this.bgnMgTick(n); return false; } // a minigame: the round machinery runs it
      if (B.ph === 'done') return this.bgnDoneTick(n);
      const a = B.ask;
      if (a) {
        const s = B.seats[a.seat];
        if (s.bot && n >= a.botAt) this.bgnBotAnswer(s, a);
        else if (!s.bot && n >= a.until) { this.bgnSay('afk'); this.bgnBotAnswer(s, a); } // AFK: the bots' brain plays it (badly)
        return true;
      }
      if (B.next && n >= B.at) { const f = B.next; B.next = null; f(); }
      return true;
    },
    // a question for one seat. fn gets the answer (already checked)
    bgnAsk(k, s, opts, fn) {
      const B = this.bgn, n = now(), online = this.humans().filter((p) => !p.watch).length > 1;
      const think = BGN.botThink[0] + B.rng() * (BGN.botThink[1] - BGN.botThink[0]);
      B.ask = { k, seat: s.i, opts, until: n + T(online ? BGN.choice.online : BGN.choice.offline), botAt: n + T(think), fn };
      this.bgnState();
    },
    bgnAnswer(v) {
      const a = this.bgn.ask;
      if (!a) return;
      this.bgn.ask = null;
      a.fn(v);
    },

    // ---------------------------------------------------------------- what clients get
    bgnInfo() {
      const B = this.bgn, n = now();
      if (!B) return null;
      const a = B.ask, mg = B.mg;
      return {
        ph: B.ph, round: B.round, rounds: B.rounds, last: B.last, lc: B.lastOn ? 1 : 0, price: this.bgnPrice(),
        seats: B.seats.map((s) => ({ i: s.i, id: s.pid, name: s.name, color: s.color, bot: s.bot ? 1 : 0, c: s.coupons, b: s.bread, at: s.at, stuck: s.stuck ? 1 : 0, bag: s.bag.slice(), lr: s.lassoR })),
        order: B.order.slice(), turn: B.turn, bakery: B.bakery, traps: [...B.traps].map(([at, t]) => [at, t.k, t.by]),
        ask: a ? { k: a.k, seat: a.seat, opts: a.opts, left: Math.max(0, a.until - n) } : null,
        walk: B.walk ? { seat: B.walk.seat, left: B.walk.left } : null, used: B.used ? 1 : 0, cart: B.cart ? 1 : 0,
        mg: mg ? { id: mg.id, fmt: mg.fmt, sides: mg.sides, one: mg.one, seats: mg.seats, stake: mg.stake, sd: mg.sd ? 1 : 0, left: Math.max(0, (mg.ends || n) - n), x: this.bgmInfo() } : null, // (x: minigames 11-15's own state)
        res: B.res, final: B.final, card: B.ph === 'mgintro' || B.ph === 'mgres' ? Math.max(0, B.at - n) : 0,
      };
    },
    bgnState() { this.broadcast({ t: 'bg', k: 'st', s: this.bgnInfo() }); },
    bgnEv(k, o) { this.broadcast({ t: 'bg', k, ...o }); },
    bgnSay(kind) { const L = BGN_NAMES.lines[kind]; if (L) this.bgnEv('say', { line: L[Math.floor(this.bgn.rng() * L.length)] }); },
    bgnCall(c, o) { this.bgnEv('call', { c, ...o }); },
    bgnPrice() { return this.bgn && this.bgn.last === 'cheap' ? 10 : K.price || BGN.price; },
    bgnCash(s, d, why) {
      const was = s.coupons;
      s.coupons = Math.max(0, s.coupons + Math.round(d));
      const real = s.coupons - was;
      if (real || d) this.bgnEv('cash', { seat: s.i, d: real, why });
      return real;
    },
    bgnBread(s, d, why) {
      const was = s.bread;
      s.bread = Math.max(0, s.bread + d);
      if (s.bread !== was) this.bgnEv('bread', { seat: s.i, d: s.bread - was, why });
      return s.bread - was;
    },
    bgnDie() { const B = this.bgn; return B.dieQ.length ? B.dieQ.shift() : 1 + Math.floor(B.rng() * 6); },
    // standings: most bread, then coupons (ties: seat order)
    bgnRank() { return this.bgn.seats.slice().sort((a, b) => b.bread - a.bread || b.coupons - a.coupons || a.i - b.i); },

    // ---------------------------------------------------------------- dibs, rounds, turns
    bgnDibs() {
      const B = this.bgn;
      B.ph = 'dibs';
      this.bgnSeatQueue();
      const rolls = B.seats.map((s) => [s.i, [this.bgnDie()]]);
      // ties throw again (only the tied ones), until everyone has their own place
      for (let guard = 0; guard < 20; guard++) {
        const key = (r) => r[1].join(',');
        const groups = new Map();
        for (const r of rolls) { const k = key(r); (groups.get(k) || groups.set(k, []).get(k)).push(r); }
        const tied = [...groups.values()].filter((g) => g.length > 1);
        if (!tied.length) break;
        for (const g of tied) for (const r of g) r[1].push(this.bgnDie());
      }
      const cmp = (x, y) => { for (let i = 0; i < Math.max(x[1].length, y[1].length); i++) { const d = (y[1][i] || 0) - (x[1][i] || 0); if (d) return d; } return x[0] - y[0]; };
      B.order = rolls.slice().sort(cmp).map((r) => r[0]);
      this.bgnEv('dibs', { rolls, order: B.order });
      this.bgnCall('dibs');
      this.bgnState();
      this.bgnLater(BGN.dibsMs, () => this.bgnRoundStart(true));
    },
    bgnRoundStart(first) {
      const B = this.bgn;
      if (B.round > B.rounds) { this.bgnEnd(); return; }
      for (const [at, t] of [...B.traps]) if (t.until < B.round) { B.traps.delete(at); this.bgnEv('trap', { at, k: null }); } // traps last 3 rounds
      for (const s of B.seats) s.lassoR = 0;
      if (!first) B.order = this.bgnRank().reverse().map((s) => s.i); // last place goes first
      B.turn = 0;
      B.ph = 'turn';
      const lastFrom = B.rounds - Math.min(BGN.lastRounds, B.rounds) + 1;
      if (!B.lastOn && B.round >= lastFrom) { this.bgnLastCall(); return; }
      this.bgnTurn();
    },
    // LAST CALL: coupon spaces pay double, and last place picks a house rule
    bgnLastCall() {
      const B = this.bgn;
      B.lastOn = true; B.ph = 'last';
      this.bgnEv('last', {});
      this.bgnCall('last');
      this.bgnSay('last');
      const loser = this.bgnRank().pop();
      this.bgnLater(BGN.eventMs, () => this.bgnAsk('house', loser, BGN_HOUSE.map((h) => h.id), (i) => {
        B.last = BGN_HOUSE[i].id;
        if (B.last === 'rush') B.rush = true;
        this.bgnEv('house', { seat: loser.i, i, id: B.last });
        this.bgnLater(BGN.eventMs, () => this.bgnTurn());
        this.bgnState();
      }));
      this.bgnState();
    },
    bgnTurn() {
      const B = this.bgn;
      if (B.turn >= B.order.length) { this.bgnRoundMg(); return; }
      this.bgnSeatQueue();
      const s = B.seats[B.order[B.turn]];
      B.used = false; B.cart = false; B.walk = null; B.ph = 'turn';
      this.bgnCall('yourTurn', { seat: s.i });
      this.bgnAsk('roll', s, null, () => this.bgnRoll(s));
    },
    bgnNextTurn() { this.bgn.turn++; this.bgnTurn(); },
    bgnRoll(s) {
      const B = this.bgn;
      const v = [this.bgnDie()];
      if (B.cart) v.push(this.bgnDie());
      let n = v.reduce((a, b) => a + b, 0);
      const stuck = s.stuck;
      if (stuck) { n = Math.ceil(n / BGN.stuckDiv); s.stuck = false; }
      B.ph = 'roll';
      this.bgnEv('roll', { seat: s.i, v, n, stuck: stuck ? 1 : 0 });
      if (v.length === 1 && v[0] === 1) this.bgnSay('one');
      if (v.length === 1 && v[0] === 6) this.bgnSay('six');
      this.bgnState();
      this.bgnLater(BGN.dieMs, () => { B.walk = { seat: s.i, left: n, pick: null }; B.ph = 'move'; this.bgnStep(); });
    },
    // one hop. forks ask, the lid pays, the bakery asks, a sign stops you, a peel slips you back
    bgnStep() {
      const B = this.bgn, w = B.walk, s = B.seats[w.seat];
      if (w.left <= 0) { this.bgnLand(s); return; }
      const nx = BOARD[s.at].next;
      if (nx.length > 1 && w.pick == null) {
        this.bgnAsk('path', s, [0, 1], (i) => { w.pick = nx[i]; this.bgnEv('path', { seat: s.i, i }); this.bgnStep(); });
        return;
      }
      const to = w.pick != null ? w.pick : nx[0];
      w.pick = null;
      s.trail.push(s.at); if (s.trail.length > 8) s.trail.shift();
      s.at = to; w.left--;
      this.bgnEv('step', { seat: s.i, to });
      const go = () => { if (B.walk === w) this.bgnLater(BGN.hop, () => this.bgnStep()); };
      if (to === LID) { this.bgnCash(s, BGN.allowance, 'allowance'); this.bgnCall('allowance', { seat: s.i }); }
      const trap = B.traps.get(to);
      if (trap && trap.k === 'sign') { B.traps.delete(to); this.bgnEv('trap', { at: to, k: null, hit: s.i }); this.bgnCall('sign', { seat: s.i }); w.left = 0; }
      if (trap && trap.k === 'peel') { B.traps.delete(to); this.bgnEv('trap', { at: to, k: null, hit: s.i }); this.bgnSlip(s); w.left = 0; this.bgnLater(BGN.landMs, () => this.bgnStep()); return; }
      const fake = trap && trap.k === 'fake' && trap.by !== s.i;
      if ((to === B.bakery || fake) && !B.cart) { this.bgnBakery(s, fake ? trap : null, to, go); return; }
      go();
    },
    bgnSlip(s) {
      this.bgnCall('slip', { seat: s.i });
      for (let k = 0; k < BGN.peelBack; k++) {
        const back = s.trail.length ? s.trail.pop() : BOARD[s.at].prev[0];
        s.at = back;
        this.bgnEv('step', { seat: s.i, to: back, back: 1 });
      }
    },
    // the bakery (or a fake one): BUY GOLDEN BREAD? one per visit
    bgnBakery(s, fake, at, cont) {
      const price = this.bgnPrice();
      if (s.coupons < price) { this.bgnEv('broke', { seat: s.i, n: price }); this.bgnLater(BGN.landMs, cont); return; }
      this.bgnAsk('bread', s, [true, false], (yes) => {
        if (yes && s.coupons >= price) {
          if (fake) { // a sponge: the price goes to whoever set it up
            this.bgn.traps.delete(at);
            this.bgnCash(s, -price, 'fake');
            const owner = this.bgn.seats[fake.by];
            if (owner) this.bgnCash(owner, price, 'fake');
            this.bgnEv('trap', { at, k: null, hit: s.i });
            this.bgnCall('sponge', { seat: s.i });
          } else {
            this.bgnCash(s, -price, 'bread');
            this.bgnBread(s, 1, 'bakery');
            s.stats.spent += price;
            this.bgnCall('bread', { seat: s.i });
            this.bgnMoveBakery('sold');
          }
        }
        this.bgnState();
        this.bgnLater(BGN.landMs, cont);
      });
    },
    // the bakery hops to another plate at least 8 spaces away, in a puff of flour
    bgnMoveBakery(why) {
      const B = this.bgn;
      let opts = PLATE_IDS.filter((id) => id !== B.bakery && loopDist(id, B.bakery) >= BGN.bakeryMin && !B.traps.has(id));
      if (!opts.length) opts = PLATE_IDS.filter((id) => id !== B.bakery);
      B.bakery = opts[Math.floor(B.rng() * opts.length)];
      this.bgnEv('bakery', { at: B.bakery, why });
      this.bgnCall('moved');
      this.bgnSay('moved');
    },
    bgnLand(s) {
      const B = this.bgn;
      B.walk = null; B.ph = 'land';
      this.bgnState();
      const others = B.seats.filter((o) => o !== s && o.at === s.at);
      const after = () => this.bgnSpace(s, () => this.bgnNextTurn());
      if (others.length) this.bgnLater(BGN.landMs, () => this.bgnDuel(s, others, after));
      else after();
    },
    // the space's effect
    bgnSpace(s, cont) {
      const B = this.bgn, sp = BOARD[s.at], trap = B.traps.get(s.at);
      let k = sp.k;
      if (s.at === B.bakery || (trap && trap.k === 'fake')) k = 'b'; // (the bakery asked on the way in)
      if (k === 'f' && B.last === 'nofees') k = 'j';
      if (k === 'c') { const n = BGN.coupon * (B.lastOn ? BGN.lastMul : 1); this.bgnCash(s, n, 'coupon'); this.bgnCall('coupon', { seat: s.i, n }); }
      else if (k === 'f') { this.bgnCash(s, -BGN.fee, 'fee'); this.bgnCall('fee', { seat: s.i }); }
      else if (k === 'p') { s.stuck = true; this.bgnCall('spill', { seat: s.i }); }
      else if (k === 'j') { this.bgnCall('jank', { seat: s.i }); this.bgnState(); this.bgnLater(BGN.landMs, () => this.bgnJank(s, cont)); return; }
      else if (k === 's') {
        if (B.cart) this.bgnCall('cart', { seat: s.i }); // carts don't have brakes
        else { this.bgnCall('store', { seat: s.i }); this.bgnShop(s, cont); return; }
      }
      this.bgnState();
      this.bgnLater(BGN.landMs, cont);
    },
    // CORNER STORE: 3 of the 5 items. buy one (bag max 3) or leave
    bgnShop(s, cont) {
      const B = this.bgn, pool = BGN_ITEM_ORDER.slice(), stock = [];
      while (stock.length < BGN.storeStock && pool.length) stock.push(pool.splice(Math.floor(B.rng() * pool.length), 1)[0]);
      stock.sort((a, b) => BGN_ITEM_ORDER.indexOf(a) - BGN_ITEM_ORDER.indexOf(b));
      this.bgnAsk('shop', s, stock, (it) => {
        if (it && stock.includes(it) && s.coupons >= BGN_ITEMS[it].cost && s.bag.length < BGN.bagMax) {
          this.bgnCash(s, -BGN_ITEMS[it].cost, 'store');
          s.stats.spent += BGN_ITEMS[it].cost;
          s.bag.push(it);
          this.bgnEv('buy', { seat: s.i, it });
        }
        this.bgnState();
        this.bgnLater(BGN.landMs, cont);
      });
    },
    // JANK: the rules guy spins the wheel (never the same event twice in a row)
    bgnJank(s, cont) {
      const B = this.bgn, opts = BGN_JANK_ORDER.filter((e) => e !== B.hist.jank);
      const e = opts[Math.floor(B.rng() * opts.length)];
      B.hist.jank = e; B.ph = 'event';
      this.bgnEv('jank', { e, seat: s.i });
      if (e === 'marbles') { // everyone slides 1-3, either way. no duels from sliding
        for (const o of B.seats) {
          const n = 1 + Math.floor(B.rng() * 3), fwd = B.rng() < 0.5;
          for (let k = 0; k < n; k++) { const to = fwd ? BOARD[o.at].next[0] : o.trail.length ? o.trail.pop() : BOARD[o.at].prev[0]; if (fwd) { o.trail.push(o.at); if (o.trail.length > 8) o.trail.shift(); } o.at = to; this.bgnEv('step', { seat: o.i, to, slide: 1 }); }
        }
      } else if (e === 'ducks') { // 3 spaces near the pawns get a duck
        const near = new Set();
        for (const o of B.seats) { near.add(o.at); for (const id of aheadSet(o.at, 2)) near.add(id); }
        const pool = [...near], hit = [];
        while (hit.length < BGN.duckSpaces && pool.length) hit.push(pool.splice(Math.floor(B.rng() * pool.length), 1)[0]);
        this.bgnEv('ducks', { at: hit });
        for (const o of B.seats) if (hit.includes(o.at)) this.bgnCash(o, -BGN.duckLoss, 'ducks');
      } else if (e === 'tax') { // the richest pays the poorest
        const by = B.seats.slice().sort((a, b) => b.coupons - a.coupons || B.rng() - 0.5), rich = by[0], poor = by[by.length - 1];
        if (rich !== poor && rich.coupons > poor.coupons) { const d = -this.bgnCash(rich, -BGN.tax, 'tax'); this.bgnCash(poor, d, 'tax'); }
      } else if (e === 'misread') this.bgnMoveBakery('misread');
      else if (e === 'swap') {
        const others = B.seats.filter((o) => o !== s);
        const o = others[Math.floor(B.rng() * others.length)];
        [s.at, o.at] = [o.at, s.at]; s.trail = []; o.trail = [];
        this.bgnEv('swap', { a: s.i, b: o.i });
      }
      this.bgnState();
      this.bgnLater(BGN.eventMs, cont);
    },

    // ---------------------------------------------------------------- items (before your roll, one a turn)
    bgnUse(s, it, to) {
      const B = this.bgn;
      if (!has(BGN_ITEMS, it) || !s.bag.includes(it) || B.used || !B.ask || B.ask.k !== 'roll' || B.ask.seat !== s.i) return false;
      if (it === 'peel') { if (B.traps.has(s.at) || s.at === B.bakery) return false; }
      else if (it === 'sign') { if (!isSpace(to) || !aheadSet(s.at, BGN.signRange).has(to) || B.traps.has(to)) return false; }
      else if (it === 'fake') { if (!isSpace(to) || BOARD[to].k !== 'c' || B.traps.has(to) || to === B.bakery) return false; }
      else if (it === 'lasso') { if (!Number.isInteger(to) || to < 0 || to >= B.seats.length || to === s.i || s.lassoR >= 1) return false; }
      s.bag.splice(s.bag.indexOf(it), 1);
      B.used = true;
      this.bgnEv('use', { seat: s.i, it, to: to ?? null });
      if (it === 'peel' || it === 'sign' || it === 'fake') {
        const at = it === 'peel' ? s.at : to;
        B.traps.set(at, { k: it, by: s.i, until: B.round + BGN.trapRounds });
        this.bgnEv('trap', { at, k: it, by: s.i });
      } else if (it === 'cart') { B.cart = true; this.bgnCall('cart', { seat: s.i }); }
      else if (it === 'lasso') { // yank them onto your space: a duel, then your roll
        const t = B.seats[to], a = B.ask;
        s.lassoR++;
        t.at = s.at; t.trail = [];
        this.bgnEv('step', { seat: t.i, to: s.at, yank: 1 });
        this.bgnCall('lasso', { seat: s.i, to: t.i });
        B.ask = null;
        this.bgnLater(BGN.landMs, () => this.bgnDuel(s, [t], () => { B.ph = 'turn'; this.bgnAsk('roll', s, null, a.fn); }));
      }
      this.bgnState();
      return true;
    },

    // ---------------------------------------------------------------- duels
    bgnDuel(s, others, cont) {
      const B = this.bgn;
      B.ph = 'duel';
      const pickWho = (fn) => (others.length > 1 ? this.bgnAsk('who', s, others.map((o) => o.i), (i) => fn(B.seats[i])) : fn(others[0]));
      pickWho((t) => {
        const opts = ['coupons'];
        if (B.round >= BGN.duelFrom && t.bread > 0 && s.coupons >= BGN.duelFee) opts.push('bread');
        const go = (stake) => this.bgnDuelGo(s, t, stake, cont);
        if (opts.length > 1) this.bgnAsk('stake', s, opts, go); else go('coupons');
      });
    },
    bgnDuelGo(a, b, stake, cont) {
      const B = this.bgn;
      if (stake === 'bread') this.bgnCash(a, -BGN.duelFee, 'stake'); // (paid even on a loss)
      a.stats.duels++; b.stats.duels++;
      this.bgnEv('duel', { a: a.i, b: b.i, stake });
      this.bgnCall('duel', { seat: a.i, to: b.i });
      this.bgnSay('duel');
      const settle = (win, ms, r) => { this.bgnDuelPay(a, b, stake, win, r); this.bgnState(); this.bgnLater(ms, cont); };
      if (a.bot && b.bot && !K.botDuel) { // nobody's watching it up close: settled on the board ("they settled it outside")
        this.bgnState();
        const pa = 0.5 + (a.coupons < b.coupons ? 0.05 : a.coupons > b.coupons ? -0.05 : 0); // a weighted coin: the poorer one gets a little luck
        this.bgnLater(BGN.botDuelMs, () => { this.bgnCall('settled'); settle(B.rng() < pa ? a : b, BGN.landMs); });
        return;
      }
      const recent = B.hist.duel.slice(-3), pool = BGN_MINI_ORDER.filter((k) => BGN_MINIS[k].fmts.includes('duel'));
      let id = K.mg && BGN_MINIS[K.mg].fmts.includes('duel') ? K.mg : null;
      if (!id) { const fresh = pool.filter((k) => !recent.includes(k)); const L = fresh.length ? fresh : pool; id = L[Math.floor(B.rng() * L.length)]; }
      B.hist.duel.push(id);
      this.bgnMgStart(id, 'duel', { seats: [a.i, b.i], sides: [[a.i], [b.i]], stake }, (r) => settle(r.win != null ? B.seats[r.win] : null, BGN.mgRes, r));
    },
    // the stake changes hands (coupons: up to 10; bread: one loaf, if they have it). null = HUNG JURY, the stake goes back
    bgnDuelPay(a, b, stake, win, r) {
      if (!win) { this.bgnCall('hung'); if (stake === 'bread') this.bgnCash(a, BGN.duelFee, 'refund'); return; }
      const lose = win === a ? b : a;
      let d = 0;
      win.stats.mgWins++;
      if (stake === 'bread') { if (this.bgnBread(lose, -1, 'duel')) { this.bgnBread(win, 1, 'duel'); d = 1; } }
      else { d = -this.bgnCash(lose, -BGN.duelCoupons, 'duel'); this.bgnCash(win, d, 'duel'); }
      if (r) r.pay = [[win.i, d], [lose.i, -d]];
      this.bgnEv('dwin', { seat: win.i, lose: lose.i, stake, d });
    },

    // ---------------------------------------------------------------- the end-of-round minigame
    bgnRoundMg() {
      const B = this.bgn, ws = BGN.fmtW;
      const allowed = BGN_FMTS.filter((f) => f !== 'boss' || BGN.bossOn);
      let fmt = K.fmt && allowed.includes(K.fmt) ? K.fmt : null;
      if (!fmt && B.rush) { fmt = BGN.bossOn ? 'boss' : '3v1'; B.rush = false; } // BOSS RUSH (the bosses come next PR: everyone vs the leader for now)
      if (!fmt && BGN.bossOn && B.round === Math.ceil(B.rounds / 2)) fmt = 'boss'; // HALFTIME BOSS
      if (!fmt) {
        const opts = allowed.filter((f) => f !== B.hist.fmt[B.hist.fmt.length - 1]);
        let r = B.rng() * opts.reduce((a, f) => a + ws[f], 0);
        fmt = opts[opts.length - 1];
        for (const f of opts) { r -= ws[f]; if (r < 0) { fmt = f; break; } }
      }
      let id = K.mg;
      if (id && !BGN_MINIS[id].fmts.includes(fmt)) fmt = BGN_MINIS[id].fmts.find((f) => allowed.includes(f)) || 'ffa';
      if (!id) {
        const pool = BGN_MINI_ORDER.filter((k) => BGN_MINIS[k].fmts.includes(fmt));
        const fresh = pool.filter((k) => !B.hist.mg.slice(-4).includes(k));
        const L = fresh.length ? fresh : pool;
        id = L[Math.floor(B.rng() * L.length)];
      }
      B.hist.fmt.push(fmt); B.hist.mg.push(id);
      const all = B.seats.map((s) => s.i), rank = this.bgnRank();
      let sides = null, one = null;
      if (fmt === '2v2') {
        if (B.round <= 1) { const sh = all.slice().sort(() => B.rng() - 0.5); sides = [[sh[0], sh[1]], [sh[2], sh[3]]]; }
        else sides = [[rank[0].i, rank[3].i], [rank[1].i, rank[2].i]]; // 1st + 4th vs 2nd + 3rd
      } else if (fmt === '3v1') { // EVERYONE VS THE LEADER (random if tied)
        const top = rank.filter((s) => s.bread === rank[0].bread && s.coupons === rank[0].coupons);
        one = top[Math.floor(B.rng() * top.length)].i;
        sides = [all.filter((i) => i !== one), [one]];
      } else if (fmt === 'boss') sides = [all, []]; // all four vs him (team 2: server/bgnmini.js)
      this.bgnCall('mg');
      this.bgnMgStart(id, fmt, { seats: all, sides, one }, (r) => this.bgnMgPay(r));
    },
    // the intro card: the map loads while it's up
    bgnMgStart(id, fmt, o, cont) {
      const B = this.bgn, def = BGN_MINIS[id];
      B.mg = { id, fmt, seats: o.seats, sides: o.sides || null, one: o.one ?? null, stake: o.stake || null, teams: (fmt === '2v2' || fmt === '3v1' || fmt === 'boss') && def.game !== 'inf', sd: false, ends: 0 }; // (infection picks its own sides)
      B.cont = cont; B.res = null;
      B.ph = 'mgintro'; B.ok = new Set();
      const map = mapForGame(def.game, MAPS, def.map);
      if (this.cfg.map !== map) { this.cfg.map = map; this.smokes.clear(); this.broadcast({ t: 'cfg', cfg: this.cfg }); }
      this.bgnEv('mg', { id, fmt, sides: B.mg.sides, one: B.mg.one, seats: o.seats, ms: T(BGN.mgIntro) });
      this.bgnLater(BGN.mgIntro, () => this.bgnMgGo());
      this.bgnState();
    },
    bgnMgGo() {
      const B = this.bgn, mg = B.mg, def = BGN_MINIS[mg.id];
      if (def.lives) mg.lives = def.lives;
      if (def.ladder) { const L = rollLadder(this.ladder); mg.ladder = [L[0], L[1], L[10], L[11], L[15], 'knife'].slice(-def.ladder); }
      const inIt = new Set(mg.seats.map((i) => B.seats[i].pid));
      for (const p of this.players.values()) this.bgnBench(p, !inIt.has(p.id));
      for (const p of this.players.values()) { p.streak = 0; p.pocket = []; if (!p.isBot) send(p, { t: 'streak', reset: 1 }); } // each minigame starts fresh: no streaks or pocketed killstreaks from the last one
      this.setGame(def.game);
      B.ph = 'mg';
      this.startRound(); // (teams from the board: bgnTeams. the bench stays down: resetWorld skips it)
      const n = now();
      this.round.ends = mg.ends = n + (K.mgTime || def.time) * 1000;
      if (def.target) this.round.target = mg.fmt === 'tie' ? 1 : def.target;
      this.bgmGo(mg, def); // minigames 11-15 set up their own bits (server/bgnmini.js)
      this.bgnState();
    },
    // per-room knobs the modes read: one-shot wonder's lives, the speed ladder, infection's patient zero
    bgnLives() { return this.bgn && this.bgn.mg && this.bgn.mg.lives; },
    bgnLadder() { return this.bgn && this.bgn.mg && this.bgn.mg.ladder; },
    bgnOne() { const mg = this.bgn && this.bgn.mg; return mg && mg.one != null ? this.bgnPlayer(this.bgn.seats[mg.one]) : null; },
    // sides from the board, not teamPlan (assignTeams). true = done
    bgnTeams() {
      const mg = this.bgn.mg;
      if (!mg || !mg.teams || this.bgn.ph !== 'mg') return false;
      const list = this.fighters();
      for (const p of list) this.bgnSide(p);
      this.broadcast({ t: 'teams', game: this.game, list: list.map((p) => [p.id, p.team, p.color]) });
      return true;
    },
    bgnSide(p) { // joinTeam: a seat's side (or no team)
      const mg = this.bgn.mg, s = this.bgnSeatOf(p);
      if (!p.ownColor) p.ownColor = p.color;
      if (!mg || !mg.teams || !s || !mg.sides) return false;
      p.team = mg.sides[0].includes(s.i) ? 1 : mg.sides[1].includes(s.i) ? 2 : 0;
      if (p.team) p.color = TEAMS[p.team].color;
      return true;
    },
    // a seat's score in this minigame (higher is better)
    bgnScore(p) {
      if (!p) return -1e9;
      const g = GAMES[this.game];
      if (g.ladder) return (p.gg || 0) * 1000 + p.kills;
      if (g.lives) return (p.oitc && !p.oitc.out ? p.oitc.lives : 0) * 1000 + p.kills;
      if (g.lava) return p.kills - p.deaths; // hot floor: deaths count against you
      return p.kills;
    },
    // every tick of a minigame: a duel's sudden death ends on the first point; a stuck minigame is ended
    bgnMgTick(n) {
      const B = this.bgn, mg = B.mg;
      if (!mg || !this.round || this.round.over) return;
      if (mg.sd && mg.sdBase) {
        const sc = mg.seats.map((i) => this.bgnScore(this.bgnPlayer(B.seats[i])));
        if (sc.some((v, k) => v !== mg.sdBase[k]) && new Set(sc).size > 1) this.endRound();
        return;
      }
      if (n > (this.round.ends || n) + BGN.mgGrace) this.endRound();
    },
    // endRound's hook: no end screen, perf, rolls or vote. rank, pay, back to the board
    bgnMgEnd() {
      const B = this.bgn, mg = B && B.mg;
      if (!mg || B.ph !== 'mg') return;
      const def = BGN_MINIS[mg.id];
      const pl = (i) => this.bgnPlayer(B.seats[i]);
      const r = { id: mg.id, fmt: mg.fmt, seats: mg.seats.slice(), sides: mg.sides, one: mg.one, stake: mg.stake, scores: mg.seats.map((i) => [i, Math.max(0, this.bgnScore(pl(i)) % 1000), pl(i) ? pl(i).kills : 0]) };
      if (mg.fmt === 'duel' || mg.fmt === 'tie') {
        const sc = mg.seats.map((i) => this.bgnScore(pl(i))), top = Math.max(...sc), lead = mg.seats.filter((_, k) => sc[k] === top);
        if (lead.length > 1 && !mg.sd) { // sudden death: +20 s, first point wins
          mg.sd = true; mg.sdBase = sc;
          this.round.ends = mg.ends = now() + (K.mgTime ? Math.min(BGN.sudden, K.mgTime * 1000) : BGN.sudden);
          if (def.target) this.round.target = 1e6;
          this.bgnCall('sd');
          this.bgnState();
          return;
        }
        r.win = lead.length === 1 ? lead[0] : mg.fmt === 'tie' ? lead[Math.floor(B.rng() * lead.length)] : null;
        r.place = mg.seats.slice().sort((a, b) => (b === r.win) - (a === r.win));
      } else if (mg.fmt === 'ffa') {
        const list = mg.seats.map((i) => [i, this.bgnScore(pl(i)), pl(i) ? pl(i).deaths : 0, B.rng()]);
        list.sort((a, b) => b[1] - a[1] || a[2] - b[2] || a[3] - b[3]);
        r.place = list.map((x) => x[0]);
      } else if (mg.fmt === '2v2') {
        const team = (side) => this.bgmTeam(side, mg) ?? (this.game === 'tdm' || this.game === 'tags' ? this.score[side === mg.sides[0] ? 1 : 2] : side.reduce((a, i) => a + Math.max(0, this.bgnScore(pl(i))), 0)); // (bumper carts: team lives)
        const a = team(mg.sides[0]), b = team(mg.sides[1]);
        r.sc = [a, b];
        r.winSide = a === b ? -1 : a > b ? 0 : 1;
      } else if (mg.fmt === '3v1') {
        const res = this.round.res;
        if (this.game === 'inf') r.winSide = res && res.side === 'inf' ? 1 : 0; // the 1 turned everyone: they win. else the three
        else { r.sc = [this.score[1], this.score[2]]; r.winSide = this.score[2] > this.score[1] ? 1 : 0; } // the big guy: more (x3) kills than the three, or the three win
      } else if (mg.fmt === 'boss') this.bgmBossRes(r, mg); // boss down: the four win (+ the MVP). else he does
      const won = mg.fmt === 'ffa' ? [r.place[0]] : r.winSide >= 0 ? mg.sides[r.winSide] : [];
      for (const i of won) B.seats[i].stats.mgWins++; // (duels count in bgnDuelPay)
      this.bgmEnd(mg, r); // minigames 11-15 tidy up (the boss goes home, the ducks go away)
      // back to the board: everyone sits down, the field is cleared, colours back
      this.round.over = true;
      this.mechReset(); this.projectiles.clear(); this.peels.clear(); this.holes.clear(); this.clearCarts(); this.mpatches.clear();
      this.broadcast({ t: 'clear' });
      for (const p of this.players.values()) this.bgnBench(p, true);
      B.mg = null;
      this.game = 'bgn'; // (no setGame: the map stays loaded, the board covers it)
      this.score = { 1: 0, 2: 0 };
      this.assignTeams();
      B.res = r; B.ph = 'mgres'; B.ok = new Set(); B.next = null;
      const cont = B.cont; B.cont = null;
      if (cont) cont(r); // pays now, schedules what's next after the results card
      if (!B.next) this.bgnLater(BGN.mgRes, () => this.bgnRoundStart()); // (safety)
      this.bgnEv('res', r);
      this.bgnState();
    },
    // the round's minigame pays out (duels pay in bgnDuelPay)
    bgnMgPay(r) {
      const B = this.bgn, pay = [];
      const give = (i, d) => { const s = B.seats[i]; this.bgnCash(s, d, 'mg'); pay.push([i, d]); };
      if (r.fmt === 'ffa') r.place.forEach((i, k) => give(i, BGN.pay.ffa[k] ?? 0));
      else if (r.fmt === '2v2') { const [w, l] = BGN.pay.v2; r.sides.forEach((side, k) => side.forEach((i) => give(i, r.winSide === -1 ? BGN.pay.v2tie : r.winSide === k ? w : l))); }
      else if (r.fmt === '3v1') { if (r.winSide === 1) { give(r.sides[1][0], BGN.pay.v31.one); this.bgnCall('rent'); } else for (const i of r.sides[0]) give(i, BGN.pay.v31.three); }
      else if (r.fmt === 'boss') { // boss down: +8 each, +5 more for the MVP (most damage). he lives: +2 each (the pity)
        const P = BGN.pay.boss;
        for (const i of r.seats) give(i, r.winSide === 0 ? P.win + (i === r.mvp ? P.mvp : 0) : P.lose);
        if (r.winSide !== 0) this.bgnCall('rent');
      }
      r.pay = pay;
      B.round++;
      this.bgnLater(BGN.mgRes, () => this.bgnRoundStart());
    },

    // ---------------------------------------------------------------- the end
    bgnEnd() {
      const B = this.bgn, rank = this.bgnRank(), top = rank.filter((s) => s.bread === rank[0].bread && s.coupons === rank[0].coupons);
      if (top.length > 1) { // TIEBREAKER: a sudden-death spoon fight between the tied seats
        this.bgnCall('tie');
        if (top.every((s) => s.bot) && !K.botDuel) { this.bgnLater(BGN.botDuelMs, () => { this.bgnCall('settled'); this.bgnFinish(top[Math.floor(B.rng() * top.length)]); }); return; }
        this.bgnMgStart('spoons', 'tie', { seats: top.map((s) => s.i), sides: null }, (r) => this.bgnLater(BGN.mgRes, () => this.bgnFinish(B.seats[r.win])));
        return;
      }
      this.bgnFinish(rank[0]);
    },
    bgnFinish(win) {
      const B = this.bgn, rank = this.bgnRank();
      const order = [win, ...rank.filter((s) => s !== win)];
      B.ph = 'done';
      B.final = { win: win.i, place: order.map((s) => [s.i, s.bread, s.coupons]) };
      this.bgnEv('cere', { final: B.final });
      this.bgnCall('toast', { seat: win.i });
      this.bgnSay('end');
      // the winner gets the normal match win (offline: 3 bots in the seats, online: 2 real people)
      const p = this.bgnPlayer(win), people = B.seats.filter((s) => !s.bot).length;
      let roll = null;
      if (p && !p.isBot) {
        const eligible = people >= 2 || B.seats.filter((s) => s.bot).length >= 3;
        if (!p.acct) roll = { n: 0, guest: 1 };
        else if (!eligible) roll = { n: 0, why: 'need 3 bots or 2 real players at the table' };
        else { stat(p, 'wins', 1); stat(p, 'xp', 50); const kind = randomContainer(); store.grantRolls(p.acct.n, kind, 1).catch((e) => console.error('roll grant failed', e.message)); roll = { n: 1, kind, why: 'won board game night' }; }
      }
      for (const s of B.seats) { const q = this.bgnPlayer(s); if (q && !q.isBot && q !== p) stat(q, 'xp', 10 + s.bread * 5); }
      if (roll) send(p, { t: 'roll+', ...roll });
      if (this.round) { this.round.over = true; this.round.next = now() + T(BGN.endMs); }
      B.hbAt = now() + T(BGN.toastMs); // the end screen's PLAY AGAIN / LOBBY after the toasting
      this.bgnState();
      console.log(`[bgn] ${this.id}: ${win.name} won with ${win.bread} bread`);
    },
    bgnDoneTick(n) {
      const r = this.round, B = this.bgn;
      if (B.hbAt && n >= B.hbAt) { B.hbAt = 0; if (this.hubBack) hubBackOpen(this); }
      if (!r || n < r.next) return true;
      if (this.hubBack && hubBackDue(this, n)) return true;
      const rounds = this.bgn.rounds;
      if (this.lobby) { this.bgn = null; for (const p of this.players.values()) p.bench = false; this.cfg.map = 'crate'; this.smokes.clear(); this.enterWarm(LOBBY.again); return true; } // (the warm-up's back on the crate, not the last minigame's map)
      this.bgnStart(rounds); // play again
      return true;
    },

    // ---------------------------------------------------------------- messages
    // handle()'s first look: board choices go to onBgn; no fighting while you sit out. true = done with it
    bgnHandle(p, m) {
      if (m.t === 'bg') { this.onBgn(p, m); return true; }
      if (m.t === 'cfg') return true; // no settings changes mid-game (the map and mode belong to the board)
      if (!FIGHT.has(m.t)) return false;
      return !!p.bench || this.bgn.ph !== 'mg';
    },
    onBgn(p, m) {
      const B = this.bgn;
      if (!B || p.isBot || p.watch) return;
      const n = now();
      p.bgnT = (p.bgnT || []).filter((t) => n - t < 1000);
      if (p.bgnT.length >= BGN.rate) return; // roll spam
      p.bgnT.push(n);
      if (m.k === 'boost') { this.bgmBoost(p); return; } // bumper carts' boost (server/bgnmini.js judges it)
      if (typeof m.k !== 'string' || !ASKS.includes(m.k)) return;
      const s = this.bgnSeatOf(p);
      if (!s) return;
      if (m.k === 'ok') { // skip a card: every human = go now
        if (B.ph !== 'mgintro' && B.ph !== 'mgres' && B.ph !== 'intro') return;
        B.ok.add(p.id);
        if (B.seats.every((x) => x.bot || B.ok.has(x.pid))) B.at = Math.min(B.at, n);
        return;
      }
      const a = B.ask;
      if (!a || a.seat !== s.i || s.pid !== p.id) return; // not your turn (or not that question)
      switch (m.k) {
        case 'roll': if (a.k === 'roll') this.bgnAnswer(true); break;
        case 'use': if (a.k === 'roll' && has(BGN_ITEMS, m.it) && (m.to === undefined || m.to === null || Number.isInteger(m.to))) this.bgnUse(s, m.it, m.to ?? null); break;
        case 'path': if (a.k === 'path' && Number.isInteger(m.i) && m.i >= 0 && m.i < a.opts.length) this.bgnAnswer(m.i); break;
        case 'bread': if (a.k === 'bread' && typeof m.yes === 'boolean' && (!m.yes || s.coupons >= this.bgnPrice())) this.bgnAnswer(m.yes); break;
        case 'buy': if (a.k === 'shop' && (m.it === null || (has(BGN_ITEMS, m.it) && a.opts.includes(m.it) && s.coupons >= BGN_ITEMS[m.it].cost && s.bag.length < BGN.bagMax))) this.bgnAnswer(m.it); break;
        case 'stake': if (a.k === 'stake' && typeof m.s === 'string' && a.opts.includes(m.s)) this.bgnAnswer(m.s); break;
        case 'who': if (a.k === 'who' && Number.isInteger(m.seat) && a.opts.includes(m.seat)) this.bgnAnswer(m.seat); break;
        case 'house': if (a.k === 'house' && Number.isInteger(m.i) && m.i >= 0 && m.i < BGN_HOUSE.length) this.bgnAnswer(m.i); break;
      }
    },
  });
  installBgnMini(Room, H); // (after: it wraps some of these)
}
