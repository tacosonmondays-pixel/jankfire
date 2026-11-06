// The rifle pack, server half: the Hat Trick's bursts (3/3 on one person = BURST!), the Yeehaw's damage ramp (keep
// hitting the same person), the Second Opinion's quick-scope bonus, and how bots fire and space themselves with them.
// Mixed into Room by installRifles: every method runs as a Room method (this = the room). The ramp and the burst are
// judged from hit times the server sees, so a client can't fake them. The quick-scope flag is the shooter's word: it
// only buys a little, at most once every QS_CD ms.
import { WEAPONS } from '../shared/weapons.js';

let H; // helpers from server.js (now, send)
const QS_CD = 1200;
// how far away bots like to stand with each one (metres: closer than [0] backs off, further than [1] walks in)
export const RIFLE_PREF = { burst: [12, 34], lmg: [8, 26], dmr: [18, 48], lever: [9, 28], autoshot: [2.5, 9] };
export const RIFLE_BOTS = ['burst', 'lmg', 'dmr', 'lever', 'autoshot'];

export function installRifles(Room, helpers) {
  H = helpers;
  Object.assign(Room.prototype, rifles);
}

const rifles = {
  // a hitscan hit is about to land (parries already checked). null = drop it (more hits than a burst can fire),
  // else { mul, add, kb } on top of the normal damage + knockback
  rifleShot(p, t, wid, h) {
    const w = WEAPONS[wid], n = H.now();
    if (w.burst) {
      // a burst is `burst` shots 1/rate apart, then burstGap. any window that long holds at most `burst` hits
      const span = ((w.burst - 1) / w.rate + w.burstGap * 0.8) * 1000;
      const log = (p.burstLog || (p.burstLog = [])).filter((x) => n - x < span);
      if (log.length >= w.burst) { p.burstLog = log; return null; }
      log.push(n); p.burstLog = log;
      const b = p.bst, inBurst = b && n - b.t0 <= ((w.burst - 1) / w.rate) * 1000 + 140;
      if (!inBurst) p.bst = { to: t.id, k: 1, t0: n };
      else if (b.to === t.id) { b.k++; if (b.k === w.burst && !p.isBot) H.send(p, { t: 'rfx', k: 'burst', v: t.id, hs: h > 0 ? 1 : 0 }); }
      else b.to = -1; // split between two people: no BURST!
      return { mul: 1, add: 0, kb: 0 };
    }
    if (w.ramp) { // Yeehaw: the chain grows while you keep hitting the same person in time
      const L = p.lev;
      const k = L && L.to === t.id && n - L.t <= w.chain * 1000 ? Math.min(w.rampMax, L.k + 1) : 0;
      p.lev = { to: t.id, k, t: n };
      if (!p.isBot && k) H.send(p, { t: 'rfx', k: 'lever', n: k, v: t.id });
      return { mul: 1 + w.ramp * k, add: 0, kb: 0 };
    }
    if (w.quick && p.qsHit && n - (p.qsT || 0) >= QS_CD) { // Second Opinion quick-scope: a bit more, a little shove
      p.qsT = n;
      if (!p.isBot) H.send(p, { t: 'rfx', k: 'qs', v: t.id });
      return { mul: 1, add: w.qsDmg, kb: w.qsKb };
    }
    return { mul: 1, add: 0, kb: 0 };
  },

  // after botFire set the next shot: burst guns fire their burst, then wait the gap
  rifleBotShot(b, w, D) {
    if (!w.burst) return;
    b.ai.bn = ((b.ai.bn || 0) + 1) % w.burst;
    if (b.ai.bn === 0) b.ai.nextShot += (w.burstGap * 1000) / D.rate;
  },
};
