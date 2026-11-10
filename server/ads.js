// The Laptop (item), server half: who gets the pop-up ads. Mixed into Room by installAds (methods run as Room methods).
// The server picks the victim (nearest your aim, in range, in sight), keeps the timers, lets a reverse card send the ads
// back, makes bots that are reading ads shoot worse and lets bots carry one. What the ads say is the victim's client's job.
import { ITEMS, ADS, BOT_DIFF } from '../shared/weapons.js';

let H; // helpers from room.js (now, send, raycast, eyeOf, lookOf, norm, dist3, r2)

export function installAds(Room, helpers) {
  H = helpers;
  const P = Room.prototype, botGear = P.botGear, botFire = P.botFire;
  Object.assign(P, ads);
  P.botGear = function (b, n) { botGear.call(this, b, n); this.adsBot(b, n); };
  // a bot with ads all over its screen can't aim for toffee
  P.botFire = function (b, t, D) { return botFire.call(this, b, t, H.now() < (b.adsUntil || 0) ? { ...D, err: D.err + ADS.botErr } : D); };
}

const ads = {
  // the enemy nearest to where p aims: alive, not a friend, in range, inside the cone, nothing solid in between
  adsTarget(p, o, d) {
    const n = H.now();
    let best = null, bd = Math.cos(ADS.cone);
    for (const t of this.players.values()) {
      if (t === p || !t.alive || this.friendly(p, t) || n < (t.adsSafe || 0) || (t.ai && t.ai.dummy && this.mode !== 'training')) continue;
      const to = [t.pos[0] - o[0], t.pos[1] + 1.1 - o[1], t.pos[2] - o[2]], dist = Math.hypot(...to);
      if (dist > ADS.range || dist < 0.01) continue;
      const dot = (to[0] * d[0] + to[1] * d[1] + to[2] * d[2]) / dist;
      if (dot < bd) continue;
      const wall = H.raycast(o, to.map((x) => x / dist), dist, this.boxes);
      if (wall && wall.t < dist - 0.6) continue;
      best = t; bd = dot;
    }
    return best;
  },
  // G with the laptop, after useItem spent the charge (c: their charges; bots have none). nobody to advertise to = charge back
  laptopUse(p, o, d, c) {
    let t = this.adsTarget(p, o, d);
    const n = H.now();
    if (!t) {
      if (c) { c.n = Math.min(ITEMS.laptop.charges, c.n + 1); if (c.n >= ITEMS.laptop.charges) c.next = 0; this.sendIc(p); }
      if (!p.isBot) H.send(p, { t: 'ads!' });
      return false;
    }
    let by = p;
    if (t.reverseUntil > n) { by = t; t = p; } // reverse card: the ads come home
    t.adsUntil = n + ADS.dur * 1000;
    t.adsSafe = t.adsUntil + ADS.safe * 1000;
    this.tag(t, by, 'laptop'); // walked off the map reading about bread: that's the laptop's kill
    if (!t.isBot) H.send(t, { t: 'ads', by: by.id, n: ADS.n, dur: ADS.dur, sure: ADS.sure });
    this.broadcast({ t: 'fx', k: 'ads', id: p.id, to: t.id, dur: ADS.dur });
    return true;
  },
  // bots carry one too (server/gear.js GEAR): open it at whoever they're fighting, from a bit of distance
  adsBot(b, n) {
    const ai = b.ai;
    if (!ai || ai.gear !== 'laptop' || this.brOn || (this.isEcon && this.isEcon()) || b.zmz || this.mode === 'training' || this.modeWeapon(b) || (this.chaosKit && this.chaosKit.noItem)) return;
    if (b.trap || b.quiz || n < (b.frozenUntil || 0) || n < (b.sleepUntil || 0) || n < (b.blindUntil || 0) || n < (ai.gearNext || 0)) return;
    const t = this.players.get(ai.target);
    if (!t || !t.alive || !ai.seenAt || n - ai.seenAt < (BOT_DIFF[ai.diff] || BOT_DIFF.normal).react || n < (t.adsSafe || 0)) return;
    const e = H.eyeOf(b), dist = H.dist3(t.pos, b.pos);
    if (dist < 6 || dist > ADS.range * 0.8) return;
    const d = H.norm([t.pos[0] - e[0], t.pos[1] + 1.1 - e[1], t.pos[2] - e[2]]);
    ai.gearNext = n + ITEMS.laptop.recharge * 1000 * (d && this.laptopUse(b, e, d, null) ? 0.9 + Math.random() * 0.8 : 0.15);
  },
};
