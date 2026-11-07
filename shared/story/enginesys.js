// the story engine (WP8) as a sim system: in solo the quest + dialogue engine runs on the page (it drives the talk UI
// and the scenes), and the page sends its state here before every save, so the sim's snapshot carries it
// (sim.state -> toSave -> the top of save.data, sim.js). co-op (WP10) will run makeStory in the room instead.
// { t: 'sty', k: 'engine', st: toSave(state), bag: [item ids], coupons }
import { addSystem } from './sim.js';
import { fromSave } from './state.js';

addSystem({
  id: 'engine',
  msg(sim, m) {
    if (m.k !== 'engine') return false;
    if (m.st && typeof m.st === 'object' && !Array.isArray(m.st)) sim.state = fromSave(m.st); // (fromSave checks every type and size)
    if (Array.isArray(m.bag)) sim.save.data.bagStub = [...new Set(m.bag.filter((s) => typeof s === 'string' && /^[\w.:-]{1,48}$/.test(s)))].slice(0, 64);
    if (Number.isFinite(m.coupons)) sim.save.coupons = Math.max(0, Math.min(1e9, Math.floor(m.coupons)));
    return true;
  },
});
