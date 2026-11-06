// body, HYPE and Coupons as a sim system (WP5). pure: no node, no dom.
//   sim.body        installed implants (shared/story/implants.js), saved as save.data.body
//   sim.hype        0-100: kills, stylish kills, crashes and long grapples fill it, it drains when you're quiet;
//                   killstreak ITEMS cost HYPE to use (save.data.hype)
//   coupons         the money: save.coupons. sim.addCoupons(n) -> false if you can't afford a negative n
// client -> sim  { k: 'clinic', op: 'buy', id } / { op: 'install', u } / { op: 'uninstall', slot }  (at a clinic only)
//                { k: 'streak', u }       use a streak item from the bar (HYPE cost)
//                { k: 'hypeEv', ev, n }   grapple distance and other client-side style (capped)
//                { k: 'eatDrop', id }     Second Stomach: eat a dropped weapon for HP
//                { k: 'fine', n }         Punch-Clock: you didn't clock in (HP fine)
// sim -> client  { k: 'body', body, drift, budget, band }  { k: 'hype', v, why? }  { k: 'coupons', v, d }  + 'streak'
// for other systems: sim.addHype(n, why), sim.addCoupons(n), sim.bodyChanged()
import { addSystem } from './sim.js';
import './invsys.js'; // (needs sim.inv / sim.dropAt: the inventory system goes first)
import { savePart } from './save.js';
import { TEST } from './testmap.js';
import { IMPLANTS, newBody, cleanBody, installOp, driftOf, budget, driftBand, perk, eatHp, UNINSTALL_FEE } from './implants.js';
import { invAdd, invTake, itemAt, kindOf } from './items.js';
import { STREAKS } from '../weapons.js';

// a streak item's HYPE cost: Moon Boots 25% ... Giant Duck 100% (DESIGN §6.6), the rest by how many kills it took
export const HYPE = { max: 100, kill: 15, style: 25, quietAfter: 8, drain: 1.5, grappleMax: 10 };
export function hypeCost(id) { const k = STREAKS[id] ? STREAKS[id].kills : 10; return Math.max(25, Math.min(100, Math.round(25 + ((k - 3) / 7) * 75))); }
savePart('body', (v) => cleanBody(v));
savePart('hype', (v) => (Number.isFinite(v) ? Math.max(0, Math.min(HYPE.max, v)) : 0));
const ctxOf = (sim) => ({ act: sim.save.act, cats: (sim.state.vars && sim.state.vars.cats) || 0 });
const near = (a, b, r) => Math.hypot(a[0] - b[0], a[2] - b[2]) <= r;

addSystem({
  id: 'body',
  init(sim) {
    sim.body = newBody(); sim.hype = 0; sim.quietT = 0; sim.hypeEvT = 0; sim.eats = []; sim.lastFine = -1e9;
    sim.bodyChanged = () => { const c = ctxOf(sim), d = driftOf(sim.body, c); sim.sty('body', { body: sim.body, drift: d, budget: budget(c), band: driftBand(d) }); };
    sim.addHype = (n, why) => {
      const v = Math.max(0, Math.min(HYPE.max, sim.hype + n));
      if (n > 0) sim.quietT = 0;
      if (v !== sim.hype) { sim.hype = v; sim.sty('hype', { v: Math.round(v), why }); }
    };
    sim.addCoupons = (n) => {
      n = Math.round(n);
      if (!Number.isFinite(n) || (n < 0 && sim.save.coupons + n < 0)) return false;
      sim.save.coupons = Math.min(1e12, sim.save.coupons + n);
      sim.sty('coupons', { v: sim.save.coupons, d: n });
      return true;
    };
  },
  load(sim, part) { sim.body = cleanBody(part); },
  save(sim) { return JSON.parse(JSON.stringify(sim.body)); },
  join(sim) {
    sim.bodyChanged();
    sim.sty('hype', { v: Math.round(sim.hype) });
    sim.sty('coupons', { v: sim.save.coupons, d: 0 });
    if (sim.save.at.map === TEST.id && !sim.state.flags.testClinic) { // the test lot: coupons to spend at the clinic, and both slice cores to try
      sim.state.flags.testClinic = true;
      sim.addCoupons(5000);
      sim.dropAt({ b: 'core_second_stomach', ql: 'fresh' }, [-9, 0.6, -10]);
      sim.dropAt({ b: 'core_cracked_punch_clock', ql: 'prime' }, [-11, 0.6, -10]);
      for (const id of ['moonboots', 'giantduck', 'satellite']) sim.dropAt({ b: id }, [-13 - ['moonboots', 'giantduck', 'satellite'].indexOf(id) * 2, 0.6, -6]);
    }
  },
  tick(sim, dt) {
    sim.quietT += dt;
    if (sim.quietT > HYPE.quietAfter && sim.hype > 0) { sim.hype = Math.max(0, sim.hype - HYPE.drain * dt); if (Math.floor(sim.t * 2) !== Math.floor((sim.t - dt) * 2)) sim.sty('hype', { v: Math.round(sim.hype) }); }
  },
  msg(sim, m) {
    const err = (e) => { sim.sty('clinicErr', { err: e }); return true; };
    switch (m.k) {
      case 'clinic': {
        if (!sim.me || !near(sim.me.pos, TEST.clinic.p, TEST.clinic.r + 1)) return err('find a meat mechanic first');
        if (m.op === 'buy') {
          const I = typeof m.id === 'string' && Object.hasOwn(IMPLANTS, m.id) && IMPLANTS[m.id];
          if (!I || I.kind !== 'shop' || !Number.isFinite(I.cost)) return err("they don't sell that here");
          if (sim.save.coupons < I.cost) return err(`that's ${I.cost} coupons. you have ${sim.save.coupons}.`);
          if (!invAdd(sim.inv, { b: m.id }, { toBar: false })) return err('the tote bag is full');
          sim.addCoupons(-I.cost); sim.invChanged();
          return true;
        }
        if (m.op === 'uninstall' && sim.save.coupons < UNINSTALL_FEE) return err(`taking it out is ${UNINSTALL_FEE} coupons`);
        const r = installOp(sim.body, sim.inv, m, { takeItem: (u) => invTake(sim.inv, u), giveItem: (it) => invAdd(sim.inv, it, { toBar: false }) });
        if (r.error) return err(r.error);
        if (m.op === 'uninstall') sim.addCoupons(-UNINSTALL_FEE);
        sim.invChanged(); sim.bodyChanged();
        sim.sty('installed', { op: m.op, slot: r.slot, b: m.op === 'install' ? sim.body.slots[r.slot].b : r.out });
        return true;
      }
      case 'streak': { // a streak item from the bar: pay HYPE, use one, the normal streak switches on
        const it = itemAt(sim.inv, m.u);
        if (!it || kindOf(it.b) !== 'streak') return err('not a streak');
        const cost = hypeCost(it.b);
        if (sim.hype < cost) { sim.sty('hype', { v: Math.round(sim.hype), need: cost, why: 'short' }); return true; }
        sim.addHype(-cost, 'spent');
        invTake(sim.inv, it.u, 1); sim.invChanged();
        sim.send({ t: 'streak', reward: it.b, dur: STREAKS[it.b] && STREAKS[it.b].dur });
        return true;
      }
      case 'hypeEv': { // client-side style the sim can't see yet (long grapples): small and capped
        if (sim.t - sim.hypeEvT < 2) return true;
        sim.hypeEvT = sim.t;
        if (m.ev === 'grapple' && Number.isFinite(m.n)) sim.addHype(Math.min(HYPE.grappleMax, Math.max(0, m.n / 4)), 'grapple');
        if (m.ev === 'test' && sim.dev) sim.addHype(Number(m.n) || 0, 'test');
        return true;
      }
      case 'eatDrop': { // Second Stomach: eat a weapon off the floor
        const p = perk(sim.body, 'core_second_stomach', ctxOf(sim)), d = sim.drops.get(m.id);
        if (!p) return err('you only have the one stomach');
        if (!d || !sim.me || Math.hypot(sim.me.pos[0] - d.p[0], sim.me.pos[2] - d.p[2]) > 4) return err('too far to eat');
        const k = kindOf(d.item.b);
        if (k !== 'gun' && k !== 'melee') return err("you can't eat that. you could try.");
        const hp = eatHp(p, d.item.r);
        sim.drops.delete(d.id); sim.sty('drop-', { id: d.id });
        sim.me.hp = Math.min(100, (sim.me.hp ?? 100) + hp);
        sim.send({ t: 'heal', id: 1, hp: sim.me.hp, a: hp });
        sim.eats = sim.eats.filter((t) => sim.t - t < 20); sim.eats.push(sim.t);
        sim.sty('ate', { b: d.item.b, hp, row: sim.eats.length, vomit: sim.eats.length >= p.vomitAfter });
        if (sim.eats.length >= p.vomitAfter) sim.eats = [];
        return true;
      }
      case 'devHp': { if (sim.dev && sim.me && Number.isFinite(m.hp)) sim.me.hp = Math.max(1, Math.min(100, m.hp)); return true; } // tests only (?storydev=1)
      case 'fine': { // the Punch-Clock's 10 HP fine (the client times the clock-in)
        const p = perk(sim.body, 'core_cracked_punch_clock', ctxOf(sim));
        if (!p || !sim.me || sim.t - sim.lastFine < p.clockEvery * 0.5) return true;
        sim.lastFine = sim.t;
        sim.me.hp = Math.max(1, (sim.me.hp ?? 100) - p.fine);
        sim.sty('fined', { hp: sim.me.hp, n: p.fine });
        return true;
      }
    }
    return false;
  },
});
// HYPE save part (save.data.hype) rides on its own tiny system so it's saved and loaded like the rest
addSystem({ id: 'hype', load(sim, v) { sim.hype = Number.isFinite(v) ? v : 0; }, save(sim) { return Math.round(sim.hype); } });
