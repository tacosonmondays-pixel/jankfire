// Weather: which maps get which weather, and the timeline the server picks for a match (server/weather.js sends it,
// public/js/weather.js plays it). Look only: nothing here touches movement, hits or bots.
// A plan is a list of phases [start s, end s, kind, strength 0-1], seconds from when the server picked it. Everyone
// gets the same plan, and the lightning strikes come out of its seed, so the whole lobby sees the same storm.
// Adding a weather later = a kind below + its kit (tools/blender/weather/make_<kind>.py) + the maps that get it.
import { MAPS } from './map.js';
import { raycast } from './physics.js';

// kind -> its Blender kit (public/models/wx/<kit>.glb) and how it rolls in
export const WX_KINDS = {
  rain: { kit: 'wx_rain', fade: 14, len: [90, 210], gap: [120, 300], first: [60, 120] }, // fade: s to roll in / out
  // Mount Kaboom: a rumble and a wisp (build s), the eruption, it settles (settle s); a tropical downpour (rain) right after
  erupt: { kit: 'wx_erupt', fade: 6, build: 35, settle: 30, len: [110, 150], gap: [240, 420], first: [150, 240], after: 'rain', rainLen: [90, 150] },
};
// map id -> its weather. s: strength range of a shower, bolts: lightning per minute at full strength, dark: how much the
// sky + sun dim (0-1). vent: a volcano's throat (x, crater floor y, z). rs: the downpour's strength after an eruption.
// maps not listed stay clear (crate, backrooms, desert, bazaar, forest: theirs come later)
const RAIN = { k: 'rain', s: [0.6, 1], bolts: 3, dark: 1 };
export const WX_MAPS = {
  suburb: RAIN, suburb_sd: RAIN, warehouse: RAIN, warehouse_sd: RAIN, skyline: RAIN, skyline_sd: RAIN,
  rooftop: { ...RAIN, bolts: 4 }, rooftop_sd: { ...RAIN, bolts: 4 }, range: { ...RAIN, s: [0.5, 0.85] },
  platform: { k: 'rain', s: [0.85, 1], bolts: 6, dark: 1.15 }, platform_sd: { k: 'rain', s: [0.85, 1], bolts: 6, dark: 1.15 }, // storm at sea
  deadmall: { k: 'rain', s: [0.7, 1], bolts: 4, dark: 0.5 }, // all roof: you hear it and the windows flash
  jankburg: { ...RAIN, s: [0.5, 0.9] },
  islands: { k: 'erupt', s: [1, 1], rs: [0.75, 1], bolts: 2, dark: 0.7, vent: [0, 11.5, -3] }, // (shared/map.js KABOOM: the crater floor round the throat)
  islands_sd: { k: 'erupt', s: [1, 1], rs: [0.75, 1], bolts: 2, dark: 0.7, vent: [0, 9.0, -13] }, // (KABOOM_SD: the same mountain, small)
};
export const WX_EARLY = 600; // a phase may have started up to this long before its plan (the eruption knob: already going)
export const WX_SPAN = 3600; // a plan covers an hour (the server picks a fresh one before it runs out)
export const WX_MAXPH = 40;

const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
export const wxOf = (map) => (typeof map === 'string' && has(WX_MAPS, map) ? WX_MAPS[map] : null);
// a small seeded random (mulberry32): the same seed gives the same plan and the same strikes everywhere
export function wxRand(seed) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
const lerp = (r, [a, b]) => a + (b - a) * r();
const r1 = (x) => Math.round(x * 10) / 10;

// the plan for a map. force: 'kind' = that weather from second 0 for the whole span (test knob JF_WEATHER), 'off' = none
export function wxPlan(map, seed, force = '') {
  const w = wxOf(map), ph = [];
  if (!w || force === 'off') return { m: map, s: seed >>> 0, ph };
  const K = WX_KINDS[w.k], r = wxRand(seed);
  if (force) {
    if (force === w.k && K.build) ph.push([-K.build, WX_SPAN, w.k, w.s[1]]); // (an eruption from second 0: its build-up already over)
    else if (force === w.k || force === K.after) ph.push([0, WX_SPAN, force, w.k === force ? w.s[1] : (w.rs || [1, 1])[1]]);
    return { m: map, s: seed >>> 0, ph };
  }
  if (K.after) { // a volcano: an eruption, then its downpour, then a long quiet, and again
    for (let t = lerp(r, K.first); t < WX_SPAN - 300 && ph.length < WX_MAXPH - 1; ) {
      const e = r1(t + lerp(r, K.len)), d = r1(Math.min(WX_SPAN, e + lerp(r, K.rainLen)));
      ph.push([r1(t), e, w.k, 1], [e, d, K.after, Math.round(lerp(r, w.rs || [1, 1]) * 100) / 100]);
      t = d + lerp(r, K.gap);
    }
    return { m: map, s: seed >>> 0, ph };
  }
  // starts clear, the first shower rolls in after a minute or two, passes, and comes back now and then
  for (let t = lerp(r, K.first); t < WX_SPAN - 60 && ph.length < WX_MAXPH; ) {
    const len = lerp(r, K.len), end = Math.min(WX_SPAN, t + len);
    ph.push([r1(t), r1(end), w.k, Math.round(lerp(r, w.s) * 100) / 100]);
    t = end + lerp(r, K.gap);
  }
  return { m: map, s: seed >>> 0, ph };
}

// how strong the weather is t seconds into a plan (0 when clear): each phase ramps in and out over its kind's fade
export function wxAt(plan, t) {
  if (!plan || !plan.ph) return { k: '', s: 0, i: -1 };
  for (let i = 0; i < plan.ph.length; i++) {
    const [a, b, k, s] = plan.ph[i];
    if (t < a || t >= b) continue;
    const f = WX_KINDS[k] ? WX_KINDS[k].fade : 10;
    return { k, s: s * Math.max(0, Math.min(1, (t - a) / f, (b - t) / f)), i };
  }
  return { k: '', s: 0, i: -1 };
}

// lightning in phase i: [time s, angle rad, distance m, bolt 0-2], from the plan's seed (no messages needed)
export function wxStrikes(plan, i) {
  const p = plan && plan.ph && plan.ph[i], w = plan && wxOf(plan.m);
  if (!p || !w || !w.bolts) return [];
  const [a, b, , s] = p, r = wxRand((plan.s ^ Math.imul(i + 1, 0x9e3779b1)) >>> 0), out = [];
  const gap = 60 / (w.bolts * Math.max(0.3, s)); // seconds between strikes, on average
  for (let t = a + 12 + r() * gap; t < b - 6 && out.length < 400; t += gap * (0.4 + r() * 1.2)) out.push([r1(t), r() * Math.PI * 2, 140 + r() * 160, (r() * 3) | 0]);
  return out;
}

// the 'wx' message: m map, s seed, el seconds since the plan started (when it was sent), ph the phases
export const wxMsg = (plan, el) => ({ t: 'wx', m: plan.m, s: plan.s, el: r1(el), ph: plan.ph });
// a client checks what it's sent: known map, finite numbers in range, known kinds, not too many phases. null = ignore
export function wxCheck(m) {
  if (!m || typeof m !== 'object' || typeof m.m !== 'string' || m.m.length > 40) return null;
  if (!Number.isFinite(m.s) || !Number.isFinite(m.el) || m.el < 0 || m.el > WX_SPAN * 2) return null;
  if (!Array.isArray(m.ph) || m.ph.length > WX_MAXPH) return null;
  const ph = [];
  for (const p of m.ph) {
    if (!Array.isArray(p) || p.length !== 4) return null;
    const [a, b, k, s] = p;
    if (!Number.isFinite(a) || !Number.isFinite(b) || !(a >= -WX_EARLY && b > a && b <= WX_SPAN) || typeof k !== 'string' || !has(WX_KINDS, k) || !Number.isFinite(s) || s < 0 || s > 1) return null;
    ph.push([a, b, k, s]);
  }
  return { m: m.m, s: m.s >>> 0, el: m.el, ph };
}

// where an eruption is, t seconds into the plan: the phase p = [a, b, 'erupt', s]. stage: 'build' (rumble, a wisp),
// 'blast' (the column, the bombs), 'settle' (it sinks back); u: 0..1 through that stage; at: s since the blast began
export function wxErupt(p, t) {
  const K = WX_KINDS.erupt, x = t - p[0], len = p[1] - p[0], b1 = K.build, b2 = Math.max(b1 + 10, len - K.settle);
  if (x < b1) return { stage: 'build', u: Math.max(0, x / b1), at: x - b1, len };
  if (x < b2) return { stage: 'blast', u: (x - b1) / (b2 - b1), at: x - b1, len };
  return { stage: 'settle', u: Math.min(1, (x - b2) / (len - b2)), at: x - b1, len };
}

// lava bombs (look only for now: nothing hits). every bomb of the eruption going on at time t, the same on every machine
// (from the plan's seed): launched from the vent at t0, lands at (x, y, z) at t (seconds into the plan), arcing h metres
// over the higher end. landings are snapped to the map's ground or the top of a box (or the sea), so a server hit can
// be hung on them later as they are. [] when no eruption is on at t
const BOMBS = new Map(); // (plan seed : phase) -> the list (worked out once)
export function wxBombs(plan, t) {
  const w = plan && wxOf(plan.m);
  if (!w || !w.vent || !plan.ph) return [];
  const i = plan.ph.findIndex((p) => p[2] === 'erupt' && t >= p[0] && t < p[1]);
  if (i < 0) return [];
  const key = `${plan.m}:${plan.s}:${i}:${plan.ph[i][0]}`;
  if (BOMBS.has(key)) return BOMBS.get(key);
  const p = plan.ph[i], K = WX_KINDS.erupt, r = wxRand((plan.s ^ Math.imul(i + 7, 0x85ebca6b)) >>> 0), out = [];
  const [vx, vy, vz] = w.vent, map = MAPS[plan.m], top = vy + 60, b0 = p[0] + K.build, b1 = Math.max(b0 + 10, p[1] - K.settle) - 4;
  for (let t0 = b0 + 0.6; t0 < b1 && out.length < 900; t0 += 0.2 + r() * 0.45) {
    const ang = r() * Math.PI * 2, d = 9 + 58 * Math.pow(r(), 1.4), x = vx + Math.cos(ang) * d, z = vz + Math.sin(ang) * d;
    const hit = map ? raycast([x, top, z], [0, -1, 0], top + 60, map.boxes) : null;
    const sea = map && Number.isFinite(map.seaY) ? map.seaY : -Infinity, y = hit ? Math.max(top - hit.t, sea) : Number.isFinite(sea) ? sea : 0; // (in the sea: on the water)
    const dur = 2.2 + d / 28;
    out.push({ x: r1x(x), y: r1x(y), z: r1x(z), t: r1x(t0 + dur), t0: r1x(t0), sx: vx, sy: vy + 2, sz: vz, h: r1x(12 + d * 0.32) });
  }
  if (BOMBS.size > 32) BOMBS.clear();
  BOMBS.set(key, out);
  return out;
}
const r1x = (v) => Math.round(v * 100) / 100;
