// BOARD GAME NIGHT: the board brain. bots answer every question the board asks (and AFK humans get it too, so a player
// who went to the fridge still plays, badly). minigames are played by the modes' own bot AI (server/room.js).
// (room.js reaches this through server/bgn.js: browser-safe)
import { BGN, BGN_ITEMS, BGN_HOUSE } from '../shared/bgn.js';
import { BOARD, FORK_A, FORK_B, aheadSet, PLATE_IDS } from '../shared/bgnboard.js';

// spaces from `from` to `to` walking the main loop forward (crease spaces count from their fork)
const fwd = (from, to) => ((to - (from >= 36 ? FORK_A : from)) % 36 + 36) % 36;

export function installBgnBots(Room) {
  Object.assign(Room.prototype, {
    // the bot's (or AFK player's) answer to the open question
    bgnBotAnswer(s, a) {
      const B = this.bgn;
      if (a.k === 'roll') {
        const use = !B.used && this.bgnBotItem(s);
        if (use && this.bgnUse(s, use.it, use.to)) { if (B.ask) B.ask.botAt = Date.now() + 500; return; } // (a lasso starts a duel and asks again after)
        this.bgnAnswer(true);
        return;
      }
      this.bgnAnswer(this.bgnBrain(a.k, s, a.opts));
    },
    bgnBrain(k, s, opts) {
      const B = this.bgn, rnd = B.rng, price = this.bgnPrice();
      if (k === 'path') { // the crease is short but sticky, and the bakery's never in it
        const onLoop = B.bakery > FORK_A && B.bakery < FORK_B;
        return onLoop && s.coupons >= price - 6 ? 0 : rnd() < 0.7 ? 1 : 0;
      }
      if (k === 'bread') return s.coupons >= price;
      if (k === 'shop') { // something useful, keeping enough for bread when it's close
        const keep = fwd(s.at, B.bakery) <= 12 ? price : 6;
        const can = opts.filter((it) => s.coupons - BGN_ITEMS[it].cost >= keep && s.bag.length < BGN.bagMax && !s.bag.includes(it));
        if (!can.length || rnd() < 0.25) return null;
        return can[Math.floor(rnd() * can.length)];
      }
      if (k === 'stake') return opts.includes('bread') && s.coupons >= 20 ? 'bread' : 'coupons';
      if (k === 'who') return opts.slice().sort((x, y) => B.seats[y].bread - B.seats[x].bread || B.seats[y].coupons - B.seats[x].coupons)[0];
      if (k === 'house') { const rank = this.bgnRank(); return rank[0].bread > s.bread && s.coupons >= 10 ? 0 : Math.floor(rnd() * BGN_HOUSE.length); }
      return opts && opts.length ? opts[0] : null;
    },
    // an item to use before rolling (or null)
    bgnBotItem(s) {
      const B = this.bgn, rnd = B.rng;
      for (const it of s.bag) {
        if (it === 'lasso' && s.lassoR < 1) { // yank whoever's got the most
          const t = B.seats.filter((o) => o !== s).sort((x, y) => y.bread - x.bread || y.coupons - x.coupons)[0];
          if (t && (t.bread > s.bread || t.coupons >= s.coupons + 10)) return { it, to: t.i };
        }
        if (it === 'cart' && fwd(s.at, B.bakery) > 6 && s.coupons >= this.bgnPrice()) return { it };
        if (it === 'peel' && !B.traps.has(s.at) && s.at !== B.bakery && rnd() < 0.6) return { it };
        if (it === 'sign' && rnd() < 0.5) { // in front of the bakery, so whoever's next stops short
          const ahead = [...aheadSet(s.at, BGN.signRange)].filter((id) => !B.traps.has(id) && id !== B.bakery);
          const near = ahead.find((id) => BOARD[id].next.includes(B.bakery)) ?? ahead[Math.floor(rnd() * ahead.length)];
          if (near != null) return { it, to: near };
        }
        if (it === 'fake' && rnd() < 0.6) { // a coupon space a few ahead of whoever's behind us
          const pool = BOARD.filter((sp) => sp.k === 'c' && !B.traps.has(sp.id) && sp.id !== B.bakery && !PLATE_IDS.includes(sp.id));
          if (pool.length) return { it, to: pool[Math.floor(rnd() * pool.length)].id };
        }
      }
      return null;
    },
  });
}
