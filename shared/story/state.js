// OVERDUE story state: everything the quest + dialogue engines know about a playthrough. Plain JSON, small.
// toSave / fromSave convert it to the save slot's `data` shape (TECH_PLAN §7: flags are a list, quests an object) and
// back, checking every type and size on the way in, so a hand-edited or broken save loads as something sane.
export const LIMITS = { said: 4000, flags: 600, vars: 200, quests: 200, log: 60, codex: 400, met: 200, seen: 300, str: 48 };

export function newState() {
  return { flags: {}, said: {}, vars: {}, quests: {}, standing: { corp: 0, bottom: 0 }, met: {}, seen: {}, codex: {}, log: [], track: '' };
}

const okId = (s) => typeof s === 'string' && s.length > 0 && s.length <= LIMITS.str && /^[\w.:-]+$/.test(s);
const fin = (v, lo, hi) => (typeof v === 'number' && Number.isFinite(v) ? Math.max(lo, Math.min(hi, v)) : 0);

export function toSave(st) {
  return {
    flags: Object.keys(st.flags).filter((k) => st.flags[k]),
    said: packSaid(st.said || {}),
    vars: { ...st.vars },
    quests: JSON.parse(JSON.stringify(st.quests)),
    standing: { ...st.standing },
    met: Object.keys(st.met), seen: Object.keys(st.seen), codex: Object.keys(st.codex),
    log: st.log.slice(-LIMITS.log), track: st.track || '',
  };
}

// d: anything (a save's data). never throws
export function fromSave(d) {
  const st = newState();
  if (!d || typeof d !== 'object' || Array.isArray(d)) return st;
  const list = (a, max, into) => { if (Array.isArray(a)) for (const k of a.slice(0, max)) if (okId(k)) into[k] = true; };
  list(d.flags, LIMITS.flags, st.flags);
  list(d.met, LIMITS.met, st.met);
  unpackSaid(d.said, st.said);
  for (const k of Object.keys(st.flags)) if (k.startsWith('said.')) { if (Object.keys(st.said).length < LIMITS.said) st.said[k.slice(5)] = true; delete st.flags[k]; } // (older saves kept them as flags)
  list(d.seen, LIMITS.seen, st.seen);
  list(d.codex, LIMITS.codex, st.codex);
  if (d.vars && typeof d.vars === 'object') for (const k of Object.keys(d.vars).slice(0, LIMITS.vars)) if (okId(k) && Object.hasOwn(d.vars, k)) st.vars[k] = fin(d.vars[k], -1e6, 1e6);
  if (d.standing && typeof d.standing === 'object') for (const k of ['corp', 'bottom']) if (Object.hasOwn(d.standing, k)) st.standing[k] = fin(d.standing[k], -100, 100);
  if (d.quests && typeof d.quests === 'object') for (const id of Object.keys(d.quests).slice(0, LIMITS.quests)) {
    const q = Object.hasOwn(d.quests, id) && d.quests[id];
    if (!okId(id) || !q || typeof q !== 'object') continue;
    const o = { step: okId(q.step) ? q.step : '', n: Array.isArray(q.n) ? q.n.slice(0, 8).map((v) => fin(v, 0, 1e4)) : [], t: fin(q.t, 0, 1e6) };
    if (q.done === true) o.done = true;
    if (q.failed === true) o.failed = true;
    if (typeof q.end === 'string' && okId(q.end)) o.end = q.end; // which ending a branching quest took
    st.quests[id] = o;
  }
  if (Array.isArray(d.log)) st.log = d.log.slice(-LIMITS.log).filter((s) => typeof s === 'string').map((s) => s.slice(0, 160));
  if (okId(d.track)) st.track = d.track;
  return st;
}

// dialogue memory ('npc.node' and 'npc.node.answer' = heard / picked), kept apart from the flags and packed per
// person so a whole playthrough stays a few KB: { lumps: 'start soup soup.1 bye', ... }
function packSaid(said) {
  const by = {};
  for (const k of Object.keys(said)) { const i = k.indexOf('.'); if (i < 1) continue; const n = k.slice(0, i); (by[n] ||= []).push(k.slice(i + 1)); }
  for (const n of Object.keys(by)) by[n] = by[n].join(' ');
  return by;
}
function unpackSaid(d, into) {
  if (!d || typeof d !== 'object' || Array.isArray(d)) return;
  let n = 0;
  for (const npc of Object.keys(d)) {
    if (!okId(npc) || !Object.hasOwn(d, npc) || typeof d[npc] !== 'string') continue;
    for (const node of d[npc].slice(0, 20000).split(' ')) { if (++n > LIMITS.said) return; const k = npc + '.' + node; if (node && okId(k)) into[k] = true; }
  }
}
