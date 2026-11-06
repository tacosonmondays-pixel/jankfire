// story cars as a sim system (WP7). the client drives (shared/story/drive.js, client-authoritative like movement);
// the sim owns which cars exist, who is in which, and checks every update the way the co-op server will: a car can't
// go faster than it ever could (drive.js MAXV) or jump across the map, and you can only get into a car you're next to.
// pure: no node, no dom.
// client -> sim  { k: 'carIn', id }                  get in (within IN m, nobody driving it)
//                { k: 'car', id, p, h, v, hp }       while driving, ~10 a second
//                { k: 'carOut', id, p, h }           get out (or thrown out)
// sim -> client  { k: 'cars', list }  { k: 'carIn', id, car }  { k: 'carOut', id }  { k: 'carFix', id, p, h, why }
// for other systems: sim.cars (Map), sim.addCar(ty, p, h, col) -> id, sim.carOf() -> the car you're driving or null
import { addSystem } from './sim.js';
import { savePart } from './save.js';
import { MAXV, carType, STORY_CARS } from './drive.js';
import { CARS, CAR_COLORS } from '../traffic.js';

export const CARSYS = { in: 4.5, max: 12, rate: 40, slack: 3, teleport: 80 };
const okTy = (ty) => typeof ty === 'string' && (Object.hasOwn(CARS, ty) || Object.hasOwn(STORY_CARS, ty));
const v3 = (a, lim = 1e5) => Array.isArray(a) && a.length === 3 && a.every((x) => Number.isFinite(x) && Math.abs(x) < lim);
const r2 = (x) => Math.round(x * 100) / 100;
// where cars are parked on a fresh game, per world (open floor, checked by the e2e): the Bottom's sofa-car by the Machine
const PARKED = {
  story_slice: [['sofa', [-195, 8.15, 191], Math.PI, '#ff7ab8'], ['hatch', [-183, 8.15, 191], Math.PI, '#f2c230']],
  story_test: [['sofa', [-36, 0, 30], Math.PI, '#ff7ab8'], ['sedan', [-14, 0, 14], 0.4, '#2f6fe0'], ['pickup', [22, 0, 6], -1.2, '#3fae5a']],
};
function cleanCars(v) {
  const out = {};
  if (!v || typeof v !== 'object' || Array.isArray(v)) return out;
  for (const z of Object.keys(v).slice(0, 32)) {
    if (!/^[a-z0-9_:]{1,40}$/.test(z) || !Array.isArray(v[z])) continue;
    const list = v[z].filter((c) => c && okTy(c.ty) && v3(c.p) && Number.isFinite(c.h)).slice(0, CARSYS.max)
      .map((c) => ({ ty: c.ty, p: c.p.map(r2), h: r2(c.h), col: typeof c.col === 'string' && /^#[0-9a-f]{6}$/i.test(c.col) ? c.col : CAR_COLORS[0], hp: Number.isFinite(c.hp) ? Math.max(0, Math.min(carType(c.ty).hp, Math.round(c.hp))) : carType(c.ty).hp }));
    if (list.length) out[z] = list;
  }
  return out;
}
savePart('cars', cleanCars);

addSystem({
  id: 'cars',
  init(sim) {
    sim.cars = new Map(); sim.carN = 0; sim.carsSaved = null;
    sim.addCar = (ty, p, h = 0, col) => {
      if (!okTy(ty) || !v3(p) || sim.cars.size >= CARSYS.max) return 0;
      const id = ++sim.carN, c = { id, ty, p: p.map(r2), h: r2(h), col: col || CAR_COLORS[id % CAR_COLORS.length], hp: carType(ty).hp, driver: 0, t: sim.t, v: [0, 0, 0] };
      sim.cars.set(id, c);
      return id;
    };
    sim.carOf = () => (sim.me && sim.me.car ? sim.cars.get(sim.me.car) || null : null);
  },
  load(sim, part) { sim.carsSaved = cleanCars(part); },
  save(sim) {
    const out = { ...(sim.carsSaved || {}) }, list = [...sim.cars.values()].map((c) => ({ ty: c.ty, p: c.p.slice(), h: c.h, col: c.col, hp: c.hp }));
    if (list.length) out[sim.zone] = list; else delete out[sim.zone];
    return out;
  },
  join(sim) {
    if (!sim.cars.size) {
      const saved = sim.carsSaved && sim.carsSaved[sim.zone];
      if (saved) for (const c of saved) { const id = sim.addCar(c.ty, c.p, c.h, c.col); if (id) sim.cars.get(id).hp = c.hp; }
      else for (const [ty, p, h, col] of PARKED[sim.zone] || []) sim.addCar(ty, p, h, col);
    }
    sim.sty('cars', { list: [...sim.cars.values()].map(view) });
  },
  msg(sim, m) {
    const me = sim.me;
    switch (m.k) {
      case 'carIn': {
        const c = sim.cars.get(m.id);
        if (!c || !me) return true;
        if (c.driver || me.car) { sim.sty('carFix', { id: c.id, p: c.p, h: c.h, why: 'taken' }); return true; }
        if (Math.hypot(me.pos[0] - c.p[0], me.pos[1] - c.p[1], me.pos[2] - c.p[2]) > CARSYS.in) { sim.sty('carFix', { id: c.id, p: c.p, h: c.h, why: 'too far' }); return true; }
        c.driver = me.id; c.t = sim.t; me.car = c.id;
        sim.sty('carIn', { id: c.id, car: view(c) });
        return true;
      }
      case 'car': case 'carOut': {
        const c = sim.cars.get(m.id);
        if (!c || !me || me.car !== c.id) return true;
        if (m.k === 'car' && sim.t - (c.u || -1) < 1 / CARSYS.rate) return true; // too many updates
        c.u = sim.t;
        if (v3(m.p) && Number.isFinite(m.h)) {
          const dt = Math.max(0.05, sim.t - c.t), d = Math.hypot(m.p[0] - c.p[0], m.p[2] - c.p[2]), dy = m.p[1] - c.p[1];
          const lim = MAXV(c.ty) * dt + CARSYS.slack, speed = v3(m.v) ? Math.hypot(m.v[0], m.v[2]) : 0;
          // a car falls as fast as it likes (off a roof), but it doesn't fly up, teleport or outrun its own engine
          if (d > lim || d > CARSYS.teleport || dy > 12 + 8 * dt || speed > MAXV(c.ty)) { sim.sty('carFix', { id: c.id, p: c.p, h: c.h, why: d > CARSYS.teleport ? 'teleport' : 'too fast' }); c.t = sim.t; return true; }
          c.p = m.p.map(r2); c.h = r2(m.h); c.t = sim.t; if (v3(m.v)) c.v = m.v.map(r2);
          if (Number.isFinite(m.hp)) c.hp = Math.max(0, Math.min(c.hp, Math.round(m.hp))); // damage only goes down
        }
        if (m.k === 'carOut') {
          c.driver = 0; me.car = 0; c.v = [0, 0, 0];
          if (c.p[1] < sim.world.killY) { const home = (PARKED[sim.zone] || [])[0]; c.p = home ? home[1].slice() : sim.world.spawn.slice(); c.h = home ? home[2] : 0; c.towed = true; } // into the void: towed back to the Lost & Found
          sim.sty('carOut', { id: c.id, ...(c.towed ? { towed: true, p: c.p, h: c.h } : {}) }); c.towed = false;
        }
        return true;
      }
    }
    return false;
  },
});
const view = (c) => ({ id: c.id, ty: c.ty, p: c.p, h: c.h, col: c.col, hp: c.hp, driver: c.driver });
