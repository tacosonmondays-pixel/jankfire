// Zombies: the WARRANTY VOIDER (put a gun in, it comes out stronger, with a side effect nobody tested) and the other
// cola machines. Shared so the server (which sells) and the client (prompts, prices, the HUD) agree.
import { ZM } from './zombies.js';

// the other flavours (Jank Cola is still shared/zombies.js ZM.cola). colaMax at once, all gone if you go down
export const ZM_COLAS = {
  legday: { name: 'LEG DAY', price: 2000, color: '#4fd8ff', desc: 'you run faster. never skip it', speed: 1.12 },
  pockets: { name: 'DEEP POCKETS', price: 3000, color: '#ffe14d', desc: 'every gun holds half again as much ammo', ammo: 1.5 },
  thirdhand: { name: 'THIRD HAND', price: 4000, color: '#7dff4f', desc: 'carry three guns. don\'t ask where', guns: 3 },
  getup: { name: 'GET UP JUICE', price: 1500, color: '#ff4fd8', desc: 'go down and you get back up by yourself. once', self: 4000 },
};
Object.assign(ZM, { colaMax: 3 });

// the Warranty Voider (needs the power on): hold F with a weapon in your hands. three goes per weapon, each dearer.
// mul = x damage to zombies at tier 0..3, ammo = x what the gun holds. from tier 2 it rolls a side effect (again at 3)
export const ZM_UP = { name: 'WARRANTY VOIDER', hold: 1.2, price: [2500, 5000, 9000], mul: [1, 1.6, 2.4, 3.4], ammo: [1, 1.2, 1.4, 1.6], tier: ['', 'VOID', 'VOID II', 'VOID III'], fxGap: 350 };
export const ZM_UPFX = {
  zap: { name: 'ZAPPY', desc: 'hits jump to the zombies next to it', color: '#4fd8ff', reach: 6, n: [0, 0, 2, 4], part: 0.4 },
  toast: { name: 'TOASTY', desc: 'sets them on fire', color: '#ff8a3a', secs: 3 },
  frost: { name: 'FROSTY', desc: 'freezes them for a moment', color: '#bfefff', ms: 1100, again: 5000 },
  boing: { name: 'BOINGY', desc: 'pops them into the air', color: '#ff4fd8', up: 9 },
  tips: { name: 'TIPPY', desc: '+5 credits a hit', color: '#7dff4f', pay: 5 },
};
export const zmUpPrice = (tier) => ZM_UP.price[tier] ?? null; // tier = what the weapon has now
export function zmUpFx(last, rnd = Math.random) { const ids = Object.keys(ZM_UPFX).filter((k) => k !== last); return ids[(rnd() * ids.length) | 0]; }

// what F does at the extra machines: a cola flavour or the voider. Z = the map's zm block. same reach rules as the
// old cola machine (in front of it, close, roughly looking at it)
export function zmShopTarget(Z, e, d, slack = 0) {
  let best = null, bs = Infinity;
  const look = (at, n, reach, min, t) => {
    const v = [at[0] - e[0], at[1] - e[1], at[2] - e[2]], l = Math.hypot(v[0], v[1], v[2]) || 1e-6;
    if (l > reach + slack || (v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / l < min - slack * 0.5) return;
    if ((e[0] - at[0]) * n[0] + (e[2] - at[2]) * n[2] <= 0.05) return; // not through the wall
    if (l < bs) { bs = l; best = t; }
  };
  (Z.colas || []).forEach((c) => { if (Object.hasOwn(ZM_COLAS, c.id)) look([c.at[0], 1.3, c.at[2]], c.n, 2.4, 0.55, { k: 'cola:' + c.id, kind: 'cola2', id: c.id, price: ZM_COLAS[c.id].price }); });
  if (Z.up) look([Z.up.at[0] + Z.up.n[0] * 0.4, 1.3, Z.up.at[2] + Z.up.n[2] * 0.4], Z.up.n, 2.8, 0.4, { k: 'up', kind: 'up' });
  return best;
}
