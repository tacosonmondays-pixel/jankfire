// Zombies extras: barricades on every window (zombies tear planks off, you nail them back), power-up drops (the
// killstreaks plus three zombies-only ones), the Cheat Machine (pay for a short random modifier once the power's on)
// and your zombies loadout (start pistol, item, one passive). Installed onto Room by server/zombies.js; the mode's own
// code calls in through a handful of zx* hooks.
import { ITEMS, STREAKS } from '../shared/weapons.js';
import { ZM, ZM_DROPS, ZM_MODS, ZM_PISTOLS, ZM_PASSIVES, zmAmmo, zmDropPick, zmModPick, zmMachPrice, zmValidLoadout, zmBoardTarget, zmClaw } from '../shared/zombies.js';

let send = () => {};
export const BOT_DROPS = new Set(['tipjar', 'restock', 'aisle5', 'chickenstrike', 'giantduck']); // what the squad's bots can pick up (the rest only work in a person's hands)
const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const has = (o, k) => typeof k === 'string' && Object.hasOwn(o, k);

const methods = {
  // ---------------------------------------------------------- state (zmReset / zmNextRound)
  zxReset() {
    const zs = this.zs, Z = this.map.zm;
    zs.planks = Z.windows.map(() => ZM.planks);
    zs.drops = []; zs.dropId = 1; zs.dropN = 0;
    zs.mods = [];
    zs.mach = { st: 0, k: '', by: 0, until: 0, cd: 0, uses: 0, last: '' };
  },
  zxRound() { // a new round: drops and the machine's price start over, so does what boarding pays
    const zs = this.zs;
    zs.dropN = 0; zs.mach.uses = 0;
    for (const h of this.zmSquad()) if (h.z) h.z.boardN = 0;
  },
  // your zombies loadout, checked (the 'zload' message and the join message both land here)
  zxSetLoadout(p, lo) { p.zl = zmValidLoadout(lo, ITEMS); },
  zxPerk(p, k) { return !!(p && p.zl && p.zl.perk === k && ZM_PASSIVES[k]); },
  // a fresh zombies kit (zmJoin): the passive's money, your item, nothing carried over in the streak tray
  zxJoin(p) {
    if (!p.zl) this.zxSetLoadout(p, null);
    if (this.zxPerk(p, 'trustfund')) p.z.c += 500;
    p.pocket = [];
    if (p.zPrevItem == null) p.zPrevItem = p.item;
    if (p.item !== p.zl.item) { p.item = p.zl.item; p.nextItem = null; p.ic = null; this.sendIc(p); }
  },
  zxLeave(p) { // zombies is over: your own item back
    if (p.zPrevItem == null) return;
    if (has(ITEMS, p.zPrevItem) && p.item !== p.zPrevItem) { p.item = p.zPrevItem; p.ic = null; this.sendIc(p); }
    p.zPrevItem = null;
  },
  // the start kit (zmKit): your start pistol and the knife
  zxKit(p) {
    const z = p.z, w = p.zl && ZM_PISTOLS[p.zl.pistol] ? p.zl.pistol : 'revolver';
    z.guns = [w]; z.ammo = {}; z.max = {};
    const a = ZM_PISTOLS[w].ammo;
    if (a != null) { z.ammo[w] = a; z.max[w] = a; }
  },
  zxMaxAmmo(p, w) { const m = p.z.max && p.z.max[w] != null ? p.z.max[w] : zmAmmo(w); return m == null ? m : Math.round(m * this.zsAmmoMul(p, w)); }, // (Deep Pockets and the voider make it hold more)
  zxPrice(p, price) { return this.zxPerk(p, 'coupons') ? Math.round((price * 0.9) / 10) * 10 : price; },

  // ---------------------------------------------------------- what everyone sees (rides in zmInfo)
  zxInfo(n) {
    const zs = this.zs, m = zs.mach;
    return {
      pk: zs.planks,
      dr: zs.drops.map((d) => [d.id, d.k, r2(d.at[0]), r2(d.at[1]), r2(d.at[2]), Math.max(0, d.until - n)]),
      md: zs.mods.filter((x) => n < x.until).map((x) => [x.k, x.by, x.until - n]),
      mc: [m.st, m.k, Math.max(0, m.until - n), m.uses, Math.max(0, m.cd - n), m.by],
    };
  },
  // a modifier p has right now (team ones are everyone's)
  zxMod(k, p) {
    const n = now();
    for (const x of this.zs.mods) if (x.k === k && n < x.until && (ZM_MODS[k].team || (p && x.by === p.id))) return true;
    return false;
  },

  // ---------------------------------------------------------- every tick (zmRound)
  zxTick(n, hs) {
    const zs = this.zs, m = zs.mach;
    if (m.st === 1 && n >= m.until) this.zxMachDone(n);
    zs.mods = zs.mods.filter((x) => n < x.until);
    for (let i = zs.drops.length - 1; i >= 0; i--) {
      const d = zs.drops[i];
      if (n >= d.until) { zs.drops.splice(i, 1); this.broadcast({ t: 'zdrop', k: 'gone', id: d.id }); continue; }
      const by = hs.find((h) => h.alive && h.z && (!h.isBot || BOT_DROPS.has(d.k)) && Math.hypot(h.pos[0] - d.at[0], h.pos[2] - d.at[2]) < ZM.dropReach && Math.abs(h.pos[1] + 0.9 - d.at[1]) < 2.2);
      if (by) { zs.drops.splice(i, 1); this.zxGrab(by, d); }
    }
  },

  // ---------------------------------------------------------- barricades
  // zmClimb hook, a zombie waiting outside: true = still tearing planks off (don't climb yet)
  zxTear(b, z, n) {
    const zs = this.zs;
    if (!zs.planks || zs.planks[z.win] <= 0) return false;
    if (zs.st === 'over') return true;
    if (!z.tearAt) { z.tearAt = n + 400 + Math.random() * 600; z.tear0 = n; return true; }
    if (n - z.tear0 > 45000) return false; // 45 s of planks going back up as fast as it rips them: it climbs through anyway
    if (n < z.tearAt) return true;
    const slow = this.zxMod('brainfreeze') ? 2.2 : 1;
    z.tearAt = n + (z.run ? ZM.tearRun : ZM.tear) * (0.8 + Math.random() * 0.4) * slow * this.zlTear(z); // (armless: it headbutts the planks, slowly)
    zs.planks[z.win]--;
    this.broadcast({ t: 'zplank', k: 'tear', i: z.win, n: zs.planks[z.win], by: b.id });
    this.broadcast({ t: 'fx', k: 'swing', w: 'bite', id: b.id, a: [r2(b.pos[0]), 1.4, r2(b.pos[2])] });
    return zs.planks[z.win] > 0;
  },
  // F held at a window (zmUse): a plank every ZM.board ms (Handyman: twice as fast), paid up to the round's cap
  zxBoard(p, t, u, n) {
    const zs = this.zs, i = t.i, z = p.z, fast = this.zxPerk(p, 'handyman');
    const gap = ZM.board * (fast ? 0.5 : 1);
    if (u.next == null) u.next = u.t0 + gap;
    while (n + 30 >= u.next && zs.planks[i] < ZM.planks) {
      u.next += gap;
      zs.planks[i]++;
      z.boardN = (z.boardN || 0) + 1;
      const pay = z.boardN <= ZM.boardCap ? Math.round(ZM.boardPay * (fast ? 1.5 : 1)) : 0;
      if (pay) this.zmGive(p, pay, 'board');
      this.broadcast({ t: 'zplank', k: 'nail', i, n: zs.planks[i], by: p.id, paid: pay ? 1 : 0 });
    }
  },
  zxTarget(p, e, d) { // the board or the machine p is looking at (checked after the mode's own targets)
    const Z = this.map.zm, zs = this.zs;
    if (Z.mach) {
      const at = [Z.mach.at[0] + Z.mach.n[0] * 0.4, 1.4, Z.mach.at[2] + Z.mach.n[2] * 0.4], v = [at[0] - e[0], at[1] - e[1], at[2] - e[2]], l = Math.hypot(...v) || 1e-6;
      if (l <= 3 && (v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / l >= 0.3 && (e[0] - at[0]) * Z.mach.n[0] + (e[2] - at[2]) * Z.mach.n[2] > 0) return { k: 'mach', kind: 'mach' };
    }
    return zmBoardTarget(Z, zs.planks, e, d, 0.6);
  },

  // ---------------------------------------------------------- the Cheat Machine
  zxMach(p, t) {
    const zs = this.zs, m = zs.mach, n = now();
    if (!zs.power) { this.zmSay(p, t.k, false, 'no power. find the switch'); return; }
    if (m.st === 1) { this.zmSay(p, t.k, false, 'it\'s rolling'); return; }
    if (n < m.cd) { this.zmSay(p, t.k, false, `cooling down · ${Math.ceil((m.cd - n) / 1000)}s`); return; }
    if (!this.zmPay(p, zmMachPrice(m.uses), t.k)) return;
    Object.assign(m, { st: 1, by: p.id, k: zmModPick(m.last), until: n + ZM.machSpin });
    m.uses++; m.last = m.k;
    this.broadcast({ t: 'zmach', k: 'spin', by: p.id, mod: m.k, ms: ZM.machSpin });
  },
  zxMachDone(n) {
    const zs = this.zs, m = zs.mach, def = ZM_MODS[m.k];
    m.st = 0; m.cd = n + ZM.machCd;
    if (!def) return;
    const by = this.players.get(m.by);
    if (!def.team && (!by || !by.z)) return; // paid, then left
    const old = zs.mods.find((x) => x.k === m.k && n < x.until && (def.team || x.by === m.by));
    if (old) old.until = Math.max(old.until, n) + def.dur * 1000; else zs.mods.push({ k: m.k, by: m.by, until: n + def.dur * 1000 });
    this.broadcast({ t: 'zmach', k: 'win', by: m.by, mod: m.k, ms: def.dur * 1000 });
  },

  // ---------------------------------------------------------- drops
  zxDrop(t, killer) { // zmKilled hook: maybe a power-up where the zombie fell
    const zs = this.zs;
    if (!killer || killer.zmz || !killer.z || zs.dropN >= ZM.dropCap || zs.st === 'over') return;
    if (Math.random() >= ZM.dropChance * (this.zxPerk(killer, 'rabbitfoot') ? 2 : 1) * (ZM.dropMul || 1)) return;
    zs.dropN++;
    const w = t.zmz.ph !== 'hunt' && this.map.zm.windows[t.zmz.win], p = w ? w.in : t.pos; // shot through the window: it lands inside, not in the alley. chest height, even if it was flung into the ceiling
    const d = { id: zs.dropId++, k: zmDropPick(), at: [p[0], 1.0, p[2]], until: now() + ZM.dropLife };
    zs.drops.push(d);
    this.broadcast({ t: 'zdrop', k: 'new', id: d.id, kind: d.k, a: d.at.map(r2) });
  },
  zxGrab(p, d) {
    const zs = this.zs, def = ZM_DROPS[d.k];
    this.broadcast({ t: 'zdrop', k: 'take', id: d.id, kind: d.k, by: p.id, a: d.at.map(r2) });
    if (!def) return;
    const hs = this.zmSquad().filter((h) => h.z);
    if (d.k === 'tipjar') { for (const h of hs) this.zmGive(h, 400, 'drop'); return; }
    if (d.k === 'restock') {
      for (const h of hs) { for (const w of h.z.guns) { const max = this.zxMaxAmmo(h, w); if (max != null) h.z.ammo[w] = max; } if (h.alive) this.zmLoadout(h); }
      return;
    }
    if (d.k === 'aisle5') {
      for (const b of [...this.players.values()]) if (b.zmz && b.alive) this.kill(b, null, 'aisle5');
      for (const h of hs) this.zmGive(h, 100, 'drop');
      return;
    }
    if (!def.streak || !STREAKS[d.k] || !p.alive) return;
    // a killstreak: it goes off right away, as if you'd pressed its key (aimed ones land on the nearest crowd)
    let at = null, best = 45;
    for (const b of this.players.values()) if (b.zmz && b.alive && b.zmz.ph === 'hunt') { const dd = Math.hypot(b.pos[0] - p.pos[0], b.pos[2] - p.pos[2]); if (dd < best) { best = dd; at = [b.pos[0], b.pos[1], b.pos[2]]; } }
    if (!at) at = [p.pos[0] - Math.sin(p.yaw || 0) * 10, p.pos[1], p.pos[2] - Math.cos(p.yaw || 0) * 10];
    p.pocket = (p.pocket || []).filter((x) => x !== d.k).concat(d.k);
    p.zmDeploy = true;
    try { this.handle(p, { t: 'deploy', r: d.k, at: at.map(r2) }); } finally { p.zmDeploy = false; }
  },

  // ---------------------------------------------------------- damage (zmDamage): modifiers and the passives
  zxHit(t, amt, a) { // a player hitting a zombie
    if (this.zxMod('oneshot', a)) amt = Math.max(amt, t.hp);
    if (this.zxMod('vampire', a) && a.alive && a.hp < 100) a.hp = Math.min(100, a.hp + Math.min(8, amt * 0.15));
    if (this.zxMod('bouncy', a)) {
      const dx = t.pos[0] - a.pos[0], dz = t.pos[2] - a.pos[2], l = Math.hypot(dx, dz) || 1;
      t.vel = [(dx / l) * 14, 11, (dz / l) * 14]; t.onGround = false;
    }
    return amt;
  },
  zxClaw(t) { return zmClaw(this.zs.n) * (this.zxPerk(t, 'thickskin') ? 0.85 : 1); },
};

export function installZmExtra(Room, h) {
  ({ send } = h);
  Object.assign(Room.prototype, methods);
}
