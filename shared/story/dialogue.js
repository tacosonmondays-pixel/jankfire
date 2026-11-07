// OVERDUE dialogue: the lore-NPC tree format (shared/secrets.js: lines: { node: { say, opts } }) plus conditions and
// actions, as a step-by-step conversation the talk UI drives (next line, pick an answer). Pure: no DOM.
// A node: { say: [lines], opts: [[text, next, { if, do, once }]], do, go, next, cam, face, again, end }
// A line: 'text' (the NPC) · '*does a thing*' (an action, no voice) · ['who', 'text', face?] · { who, t, face, if, do }
// Every node you enter is a quest event { type: 'talk', npc, node }, so a goal can wait for a line to be heard.
import { GOALS } from './quests.js';

const saidKey = (npc, node, i) => `${npc}.${node}${i == null ? '' : '.' + i}`; // (in st.said, not the flags)

function normLine(l, npc) {
  if (typeof l === 'string') return { who: l.startsWith('*') ? '' : npc, t: l, act: l.startsWith('*') };
  if (Array.isArray(l)) return { who: l[0] === 'you' ? 'you' : l[0], t: String(l[1] ?? ''), face: l[2], act: String(l[1] ?? '').startsWith('*') };
  return { who: l.who ?? npc, t: String(l.t ?? ''), face: l.face, if: l.if, do: l.do, act: String(l.t ?? '').startsWith('*') };
}
const normOpt = (o) => (Array.isArray(o) ? { t: o[0], to: o[1], ...(o[2] || {}) } : { ...o, t: o.t ?? o.text, to: o.to ?? o.next });

export function openTalk(S, npcId, nodeId = 'start') {
  const npc = S.defs.npcs[npcId];
  if (!npc) throw new Error(`no npc ${npcId}`);
  const st = S.st;
  const T = { npc: npcId, node: '', lines: [], i: 0, opts: null, end: false, cam: null, face: null, history: [] };
  if (!st.met[npcId]) { st.met[npcId] = true; st.codex[`char.${npcId}`] = true; S.out({ type: 'meet', npc: npcId, name: npc.name }); }

  function enter(id, hops = 0) {
    if (hops > 20) throw new Error(`dialogue loop at ${npcId}/${id}`);
    let n = npc.lines[id];
    if (!n) { T.end = true; T.lines = []; T.opts = null; return; }
    // go: redirects checked on entry, first match wins ([[cond, node]] or [{ if, to }])
    if (n.go) for (const g of n.go) { const [c, to] = Array.isArray(g) ? g : [g.if, g.to]; if (S.test(c)) { if (to !== id) return enter(to, hops + 1); break; } }
    if (n.if && !S.test(n.if)) { T.end = true; return; }
    const again = st.said[saidKey(npcId, id)];
    st.said[saidKey(npcId, id)] = true;
    T.node = id; T.i = 0; T.opts = null; T.cam = n.cam || npc.cam || null; T.face = n.face || null;
    const L = again && n.again ? n.again : n.say || [];
    T.lines = L.map((l) => normLine(l, npcId)).filter((l) => !l.if || S.test(l.if));
    if (n.do) S.run(n.do, `talk ${npcId}/${id}`);
    if (n.codex) for (const c of [].concat(n.codex)) S.run([`codex:${c}`], 'talk');
    S.emitQuest({ type: GOALS.talk.ev, npc: npcId, node: id });
    if (!T.lines.length) T.lines = [{ who: npcId, t: '...', act: false }];
    lineFx();
  }
  function lineFx() { const l = T.lines[T.i]; if (l && l.do) S.run(l.do, 'line'); if (T.i === T.lines.length - 1) arrive(); }
  // the last line of a node: show its answers, or note where it goes next
  function arrive() {
    const n = npc.lines[T.node];
    if (!n || !n.opts) return;
    T.opts = n.opts.map(normOpt).map((o, i) => ({ ...o, i })).filter((o) => (!o.if || S.test(o.if)) && !(o.once && st.said[saidKey(npcId, T.node, o.i)]));
    if (!T.opts.length) T.opts = null;
  }
  T.line = () => T.lines[T.i] || null;
  // advance one line. returns false once the conversation is over
  T.next = () => {
    if (T.end) return false;
    if (T.i < T.lines.length - 1) { T.i++; lineFx(); return true; }
    if (T.opts) return true; // waiting for an answer
    const n = npc.lines[T.node] || {};
    if (n.next && !n.end) { enter(n.next); return !T.end; }
    T.end = true;
    return false;
  };
  T.choose = (k) => {
    if (!T.opts || T.i < T.lines.length - 1) return false;
    const o = T.opts[k];
    if (!o) return false;
    st.said[saidKey(npcId, T.node, o.i)] = true;
    T.history.push([T.node, o.i]);
    if (o.do) S.run(o.do, `answer ${npcId}/${T.node}`);
    if (o.to) enter(o.to); else { T.end = true; T.opts = null; }
    return true;
  };
  enter(nodeId);
  return T;
}
