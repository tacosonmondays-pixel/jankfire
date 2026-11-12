// the mech hero clips' beats get their sounds: mechlook.js calls mechLook.onEvent(inst, ev, [x, y, z]) for each event
// a clip carries (meta clips[].events). a little gap per kind so a looped clip's beats don't pile up
import { mechLook } from './mechlook.js';
import { mechsfx } from './mechsfx.js';

const last = new Map();
mechLook.onEvent = (inst, ev, p) => {
  if (!ev || typeof ev.fx !== 'string' || !Array.isArray(p)) return;
  const t = performance.now(), key = ev.fx + (inst && inst.id != null ? inst.id : '');
  if (t - (last.get(key) || 0) < 120) return;
  last.set(key, t);
  if (last.size > 200) last.clear(); // (mechs come and go: never grows)
  mechsfx.look(ev.fx, p, Number.isFinite(ev.k) ? Math.max(0.2, Math.min(2, ev.k)) : 1);
};
