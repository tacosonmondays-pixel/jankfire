// the inventory as a sim system (WP3): sim.inv is the Tote Bag + quick bar + locker (shared/story/items.js), sim.drops
// the things lying in the world. every change a client asks for goes through invOp here, so in co-op (StoryRoom) the
// server rejects edits for items you don't have. pure: no node, no dom.
//
// client -> sim  { t: 'sty', k: 'inv', op, ... }   bar / move / drop / stash / unstash (see invOp)
//                { t: 'sty', k: 'pick', id }        pick up a drop within PICK m
//                { t: 'sty', k: 'starter', lo }     a new game's first join: your normal loadout becomes the bar
//                { t: 'sty', k: 'gear', u }         make a bar gear item your G item  ({ t: 'item' } then uses one)
//                { t: 'sty', k: 'eat', u }          eat a snack
// sim -> client  { k: 'inv', inv, err? }  { k: 'drops', list }  { k: 'drop+', d }  { k: 'drop-', id }  + 'ic' / 'heal'
//
// for other systems (quests, loot, bosses): sim.give(item) -> u (or it lands on the floor), sim.dropAt(item, p),
// sim.takeItem(b, n) -> bool, sim.hasItem(b, n)
import { addSystem } from './sim.js';
import { savePart } from './save.js';
import { TEST } from './testmap.js';
import { invAdd, invOp, invTake, cleanInv, starterInv, itemAt, kindOf, hasItem, find, makeItem, STORY_ITEMS } from './items.js';
import { ITEMS } from '../weapons.js';
import { rollTable, rollWeapon, legendaryItem, RARITY_ORDER } from './loot.js'; // WP4

export const PICK = 3.2; // metres
savePart('inv', (v) => cleanInv(v));
// loot left on the floor survives a reload: FLOOR per zone (the map / district), oldest goes first past the cap
export const FLOOR = 40;
const zoneOf = (sim) => sim.zone || TEST.id;
function cleanFloor(v) {
  const out = {};
  if (!v || typeof v !== 'object' || Array.isArray(v)) return out;
  for (const z of Object.keys(v).slice(0, 64)) {
    if (!/^[a-z0-9_:]{1,40}$/.test(z) || !Array.isArray(v[z])) continue;
    const list = [];
    for (const d of v[z].slice(-FLOOR)) {
      if (!d || !Array.isArray(d.p) || d.p.length !== 3 || !d.p.every((x) => Number.isFinite(x) && Math.abs(x) < 1e5)) continue;
      const it = makeItem(d.item && d.item.b, d.item || {});
      if (it) list.push({ item: it, p: r2(d.p) });
    }
    if (list.length) out[z] = list;
  }
  return out;
}
savePart('floor', cleanFloor);

const near = (a, b, r) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]) <= r;
const r2 = (p) => p.map((x) => Math.round(x * 100) / 100);

addSystem({
  id: 'inv',
  init(sim) {
    sim.inv = cleanInv(null); sim.inv.fresh = true; // fresh: a new game, the first join hands over your loadout
    sim.drops = new Map(); sim.dropN = 0; sim.gearU = 0;
    const inv = () => sim.sty('inv', { inv: view(sim) });
    sim.invChanged = inv;
    sim.dropAt = (item, p) => {
      const id = ++sim.dropN, d = { id, item: { b: item.b, r: item.r || 'common', s: item.s || 0, ...(item.n ? { n: item.n } : {}), ...(item.q ? { q: item.q } : {}), ...(item.br ? { br: item.br } : {}), ...(item.m ? { m: item.m.slice() } : {}), ...(item.lg ? { lg: item.lg } : {}) }, p: r2(p) };
      sim.drops.set(id, d);
      sim.sty('drop+', { d });
      const z = [...sim.drops.values()];
      if (z.length > FLOOR + 20) for (const old of z.slice(0, z.length - FLOOR - 20)) { sim.drops.delete(old.id); sim.sty('drop-', { id: old.id }); } // a floor this full: the oldest rots away
      return id;
    };
    // roll a loot table (shared/story/content/loot.js) and scatter it round p. returns the drop ids
    sim.lootDrop = (table, p, ctx = {}) => rollTable(table, sim.rand || Math.random, ctx).map((it, i, a) => { const ang = (i / Math.max(1, a.length)) * Math.PI * 2; return sim.dropAt(it, [p[0] + Math.cos(ang) * 1.2, p[1] + 0.6, p[2] + Math.sin(ang) * 1.2]); });
    sim.give = (item) => { const u = invAdd(sim.inv, item); if (u) inv(); else if (sim.me) sim.dropAt(item, sim.me.pos); return u; };
    sim.hasItem = (b, n = 1) => hasItem(sim.inv, b, n);
    sim.takeItem = (b, n = 1) => {
      if (!hasItem(sim.inv, b, n)) return false;
      for (const x of sim.inv.bag.slice()) { if (n <= 0) break; if (x && x.b === b) { const t = invTake(sim.inv, x.u, n); n -= t.q || 1; } }
      inv();
      return true;
    };
  },
  load(sim, part) { sim.inv = cleanInv(part); },
  save(sim) { const { fresh, ...inv } = sim.inv; return JSON.parse(JSON.stringify(inv)); },
  join(sim) {
    const saved = sim.floorSaved && sim.floorSaved[zoneOf(sim)]; // what you left lying here last time
    if (saved && !sim.floorBack) { sim.floorBack = true; for (const d of saved) sim.dropAt(d.item, d.p); }
    if (sim.save.at.map === TEST.id && !sim.state.flags.testLoot) { // the test lot: a pile of things to try every kind on
      sim.state.flags.testLoot = true;
      const kit = ['redline', 'marbles', 'katana', 'scales', 'shotgun', 'lasso', 'medkit', 'smoke', 'moonboots', 'jank_cola', 'bottlecap'];
      kit.forEach((b, i) => { const a = (i / kit.length) * Math.PI * 2; sim.dropAt({ b, q: b === 'jank_cola' ? 3 : b === 'bottlecap' ? 7 : 0 }, [8 * Math.cos(a), 0.6, -2 + 8 * Math.sin(a)]); });
    }
    if (sim.save.at.map === TEST.id && !sim.state.flags.testLoot2) { // WP4: one of every rarity in a row by the wall, plus the slice's named four
      sim.state.flags.testLoot2 = true;
      RARITY_ORDER.forEach((r, i) => sim.dropAt(rollWeapon({ rarity: r }), [-12 + i * 3, 0.6, -24]));
      ['late_bloomer', 'grandmas_hands', 'mothers_ladle', 'severance_package'].forEach((id, i) => sim.dropAt(legendaryItem(id), [5 + i * 3, 0.6, -24]));
    }
    sim.sty('drops', { list: [...sim.drops.values()] });
    sim.invChanged();
  },
  msg(sim, m) {
    const err = (e) => { sim.sty('inv', { inv: view(sim), err: e }); return true; };
    switch (m.k) {
      case 'starter': {
        if (!sim.inv.fresh) return true;
        sim.inv = starterInv(m.lo && typeof m.lo === 'object' ? m.lo : {});
        sim.invChanged();
        return true;
      }
      case 'inv': {
        const r = invOp(sim.inv, m, { atLocker: !!(sim.me && near(sim.me.pos, TEST.locker.p, TEST.locker.r)) });
        delete sim.inv.fresh;
        if (r.error) return err(r.error);
        if (r.dropped && sim.me) { const y = sim.me.yaw || 0; sim.dropAt(r.dropped, [sim.me.pos[0] - Math.sin(y) * 1.5, sim.me.pos[1] + 0.6, sim.me.pos[2] - Math.cos(y) * 1.5]); }
        if (r.dropped && r.dropped.u === sim.gearU) sim.gearU = 0;
        sim.invChanged();
        return true;
      }
      case 'pick': {
        const d = sim.drops.get(m.id);
        if (!d || !sim.me || !near(sim.me.pos, d.p, PICK + 1)) return err('too far');
        delete sim.inv.fresh;
        const left = { ...d.item };
        const u = invAdd(sim.inv, left);
        if (!u) { if (left.q && left.q !== d.item.q) { d.item.q = left.q; sim.sty('drop+', { d }); sim.invChanged(); } return err('the tote bag is full'); }
        sim.drops.delete(d.id);
        sim.sty('drop-', { id: d.id, by: 1, b: d.item.b, item: d.item });
        sim.invChanged();
        return true;
      }
      case 'give': { // dev only (?storydev=1: tests and the sweep): any item onto the bar slot you name
        if (!sim.dev) return true;
        const u = invAdd(sim.inv, { b: m.b, q: m.q | 0 }, { toBar: false });
        if (u && Number.isInteger(m.slot)) invOp(sim.inv, { op: 'bar', slot: m.slot, u });
        delete sim.inv.fresh;
        sim.invChanged();
        return true;
      }
      case 'gear': {
        const it = itemAt(sim.inv, m.u);
        if (!it || kindOf(it.b) !== 'gear') return err("that's not gear");
        sim.gearU = it.u;
        sim.send({ t: 'ic', i: it.b, n: it.q || 1, next: 0 });
        return true;
      }
      case 'eat': {
        const it = itemAt(sim.inv, m.u), def = it && STORY_ITEMS[it.b];
        if (!def || def.kind !== 'snack' || !sim.me) return err("you can't eat that. you could try.");
        invTake(sim.inv, it.u, 1);
        const hp = sim.me.hp = Math.min(100, (sim.me.hp ?? 100) + (def.heal || 0));
        sim.send({ t: 'heal', id: 1, hp, a: def.heal || 0 });
        sim.invChanged();
        return true;
      }
    }
    return false;
  },
  // the G item: the game sends { t: 'item', i } when you throw / use it. one less in the stack
  raw(sim, m) {
    if (m.t !== 'item' || !sim.gearU) return false;
    const it = itemAt(sim.inv, sim.gearU);
    if (!it || it.b !== m.i || !ITEMS[it.b]) return false;
    invTake(sim.inv, it.u, 1);
    if (find(sim.inv, sim.gearU) < 0) sim.gearU = 0;
    sim.send({ t: 'ic', i: it.b, n: sim.gearU ? (itemAt(sim.inv, sim.gearU).q || 1) : 0, next: 0 });
    sim.invChanged();
    return true;
  },
});

// what the client gets: the bag with names filled in is the client's job (items.js infoOf), so this is just the data
function view(sim) { const { fresh, ...inv } = sim.inv; return { ...inv, fresh: !!fresh }; }

// the floor as its own save part (save.data.floor): { zone: [{ item, p }] }, newest FLOOR per zone
addSystem({
  id: 'floor',
  load(sim, part) { sim.floorSaved = cleanFloor(part); },
  save(sim) {
    const out = { ...(sim.floorSaved || {}) }, z = zoneOf(sim);
    const here = [...sim.drops.values()].map((d) => ({ item: { ...d.item }, p: d.p.slice() })).slice(-FLOOR);
    if (here.length) out[z] = here; else delete out[z];
    return out;
  },
});
