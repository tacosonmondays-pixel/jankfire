// Zombies: the Warranty Voider (weapon upgrades with side effects) and the other cola flavours. Installed onto Room by
// server/zombies.js; the mode calls in through a few zs* hooks. Rules and numbers: shared/zmshop.js.
import { WEAPONS } from '../shared/weapons.js';
import { ZM, zmAmmo } from '../shared/zombies.js';
import { ZM_COLAS, ZM_UP, ZM_UPFX, zmUpPrice, zmUpFx, zmShopTarget } from '../shared/zmshop.js';
import { hookCharges, hookSpend } from '../shared/royale.js'; // the grapple's charges: Jank Royale's rule (BR.hook), here too

let send = () => {};
const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const has = (o, k) => typeof k === 'string' && Object.hasOwn(o, k);
const FORCE_FX = has(ZM_UPFX, process.env.JF_ZM_UPFX) ? process.env.JF_ZM_UPFX : ''; // tests: every roll is this side effect

const methods = {
  // ---------------------------------------------------------- state
  zsJoin(p) { p.z.colas = []; p.z.up = {}; p.z.hook = null; }, // a fresh kit (zmJoin)
  // ---------------------------------------------------------- the grapple runs on charges (as in Jank Royale: no endless
  // swinging round the horde). the client asks, the server counts: a new rope (none before, or the point jumped somewhere
  // else) spends one; none left = the rope is cut for everyone and the client is told. grabbing a zombie spends it first,
  // so the rope that follows it in the next snapshot is free
  zsHookSnap(p, m) {
    const z = p.z, g = m.g;
    if (!z || !p.alive || !Array.isArray(g) || g.length !== 3 || !g.every(Number.isFinite)) return;
    if (p.g && Math.hypot(p.g[0] - g[0], p.g[1] - g[1], p.g[2] - g[2]) < 6) return; // the same rope
    if (now() - (z.hookPush || 0) < 1500) { z.hookPush = 0; return; } // the rope of a grab we just paid for
    if (!this.zsHookUse(p)) m.g = 0;
  },
  zsHookUse(p) {
    const z = p.z, n = now();
    if (!z || p.isBot) return true;
    const h = hookSpend(z.hook, n);
    if (!h) { if (n - (z.hookNoT || 0) > 350) { z.hookNoT = n; send(p, { t: 'zhook', h: z.hook, no: 1 }); } return false; }
    z.hook = h;
    send(p, { t: 'zhook', h });
    return true;
  },
  zsKit(p) { p.z.up = {}; }, // bled out, back to the start pistol: the warranty's back too
  zsHas(p, id) { return !!(p && p.z && p.z.colas && p.z.colas.includes(id)); },
  zsColaN(p) { return (p.z.colas ? p.z.colas.length : 0) + (p.z.cola ? 1 : 0); },
  zsGuns(p) { return this.zsHas(p, 'thirdhand') ? ZM_COLAS.thirdhand.guns : ZM.guns; },
  // what a gun holds for p: Deep Pockets, and what the voider added
  zsAmmoMul(p, w) { const u = p.z.up && p.z.up[w]; return (this.zsHas(p, 'pockets') ? ZM_COLAS.pockets.ammo : 1) * (u ? ZM_UP.ammo[u.t] || 1 : 1); },
  zsMine(p) { send(p, { t: 'zshop', colas: [...(p.z.colas || [])], up: p.z.up || {}, jank: p.z.cola ? 1 : 0 }); }, // what you've got (rides after every loadout)
  zsTarget(p, e, d) { return zmShopTarget(this.map.zm, e, d, 0.6); },
  zsNeed(t) { return t.kind === 'up' ? ZM_UP.hold : null; }, // seconds of F (zmUse)

  // ---------------------------------------------------------- going down (zmKilled): the colas go, the third gun goes
  // returns ms until p gets back up by themselves (Get Up Juice), or 0
  zsDowned(p) {
    const z = p.z, self = this.zsHas(p, 'getup') && this.zs.st !== 'over';
    if (self) { z.colas = z.colas.filter((c) => c !== 'getup'); this.zsMine(p); return ZM_COLAS.getup.self; } // the juice is spent, the rest stay
    z.colas = [];
    while (z.guns.length > ZM.guns) { const w = z.guns.pop(); delete z.ammo[w]; delete z.up[w]; }
    this.zsMine(p);
    return 0;
  },

  // ---------------------------------------------------------- F at a machine (zmDo)
  zsCola(p, t) {
    const zs = this.zs, z = p.z, def = ZM_COLAS[t.id];
    if (!def) return;
    if (!zs.power) { this.zmSay(p, t.k, false, 'no power. find the switch'); return; }
    if (z.colas.includes(t.id)) { this.zmSay(p, t.k, false, 'one is enough'); return; }
    if (this.zsColaN(p) >= ZM.colaMax) { this.zmSay(p, t.k, false, `${ZM.colaMax} colas is the limit. doctor's orders`); return; }
    if (!this.zmPay(p, def.price, t.k)) return;
    z.colas.push(t.id);
    if (def.ammo) for (const w of z.guns) { const max = this.zxMaxAmmo(p, w); if (max != null) z.ammo[w] = Math.max(z.ammo[w] || 0, Math.min(max, Math.round((z.ammo[w] || 0) * def.ammo))); } // the extra comes with it
    this.zmSay(p, t.k, true, def.name);
    this.broadcast({ t: 'fx', k: 'medkit', id: p.id });
    this.zmLoadout(p);
  },
  zsUp(p, t) {
    const zs = this.zs, z = p.z, w = p.w;
    if (!zs.power) { this.zmSay(p, t.k, false, 'no power. find the switch'); return; }
    if (!has(WEAPONS, w) || (w !== z.melee && !z.guns.includes(w))) { this.zmSay(p, t.k, false, 'hold the weapon you want voided'); return; }
    const cur = z.up[w] || { t: 0, fx: '' }, price = zmUpPrice(cur.t);
    if (price == null) { this.zmSay(p, t.k, false, 'it can\'t get any more void'); return; }
    if (!this.zmPay(p, price, t.k)) return;
    const tier = cur.t + 1, fx = tier >= 2 ? FORCE_FX || zmUpFx(cur.fx) : '';
    z.up[w] = { t: tier, fx };
    const max = this.zxMaxAmmo(p, w);
    if (max != null) z.ammo[w] = max; // comes back full
    this.zmSay(p, t.k, true, `${WEAPONS[w].name} · ${ZM_UP.tier[tier]}`);
    this.broadcast({ t: 'zup', k: 'done', id: p.id, w, tier, fx });
    this.zmLoadout(p, w);
  },

  // ---------------------------------------------------------- damage (zmDamage, a squad member hitting a zombie)
  zsHit(t, amt, a, w) {
    if (w === 'bow' && t.zmz && t.zmz.toastBy === a.id && now() < (t.burnUntil || 0)) amt = Math.max(amt, t.zmz.toastDmg || 0); // TOASTY: the fire's ticks scale with the gun that lit it
    const u = a.z && a.z.up && a.z.up[w];
    if (!u || amt <= 0) return amt;
    amt *= ZM_UP.mul[u.t] || 1;
    const fx = ZM_UPFX[u.fx], n = now();
    if (!fx || n - (a.z.fxT || 0) < ZM_UP.fxGap) return amt;
    a.z.fxT = n;
    if (u.fx === 'toast') { this.burn(t, a, fx.secs); t.zmz.toastBy = a.id; t.zmz.toastDmg = amt * fx.tick; }
    else if (u.fx === 'frost') { if (n >= (t.zmz.frostOk || 0)) { t.frozenUntil = n + fx.ms; t.zmz.frostOk = n + fx.again; this.broadcast({ t: 'zup', k: 'frost', id: t.id, ms: fx.ms }); } }
    else if (u.fx === 'boing') { t.vel[1] = Math.max(t.vel[1], fx.up); t.onGround = false; }
    else if (u.fx === 'tips') this.zmGive(a, fx.pay, 'tip');
    else if (u.fx === 'zap') (this.zs.zaps ||= []).push({ by: a.id, from: t.id, dmg: amt * fx.part, n: fx.n[u.t] || 2 }); // next tick: not in the middle of this hit
    return amt;
  },
  // every tick (zmRound): the zaps queued by hits jump to whatever's next to the one that was shot
  zsTick() {
    const zs = this.zs, Z = ZM_UPFX.zap;
    if (!zs.zaps || !zs.zaps.length) return;
    const zaps = zs.zaps; zs.zaps = [];
    for (const q of zaps.slice(0, 6)) {
      const a = this.players.get(q.by), t = this.players.get(q.from);
      if (!a || !a.alive || !t) continue;
      const near = zs.list.filter((o) => o !== t && o.alive && Math.hypot(o.pos[0] - t.pos[0], o.pos[1] - t.pos[1], o.pos[2] - t.pos[2]) <= Z.reach)
        .sort((x, y) => Math.hypot(x.pos[0] - t.pos[0], x.pos[2] - t.pos[2]) - Math.hypot(y.pos[0] - t.pos[0], y.pos[2] - t.pos[2])).slice(0, q.n);
      if (!near.length) continue;
      this.broadcast({ t: 'zup', k: 'zap', a: [r2(t.pos[0]), r2(t.pos[1] + 1.2), r2(t.pos[2])], to: near.map((o) => [r2(o.pos[0]), r2(o.pos[1] + 1.2), r2(o.pos[2])]) });
      for (const o of near) this.damage(o, q.dmg, a, 'zap');
    }
  },
};

export function installZmShop(Room, h) {
  ({ send } = h);
  Object.assign(Room.prototype, methods);
}
