// OVERDUE story hub: wires the condition language, the actions, the quest engine and dialogue to one state + content
// set. makeStory({ content, state, host }) -> S. The host is whoever runs it (the browser solo, a StoryRoom in co-op)
// and gets every outside effect as a call: host.has(item), host.act(action) for give / take / scene / coupons / toast,
// host.event(e) for quest + dialogue news (cards, HUD, sounds). Missing host functions are fine (a test has none).
import { compile } from './cond.js';
import { newState } from './state.js';
import { makeQuests } from './quests.js';
import { openTalk } from './dialogue.js';

// 'verb:arg' -> { do: verb, arg }. objects pass through; { if, do: [...], else: [...] } is a branch
export function parseAction(a) {
  if (typeof a !== 'string') return a;
  const i = a.indexOf(':');
  return i < 0 ? { do: a, arg: '' } : { do: a.slice(0, i), arg: a.slice(i + 1) };
}

export function makeStory({ content, state, host = {} } = {}) {
  const S = { st: state || newState(), defs: { npcs: {}, quests: {}, scenes: {}, codex: {}, zones: {}, ...(content || {}) }, host, trace: [] };
  S.test = (c) => { try { return !!compile(c)(S.st, host); } catch (e) { S.out({ type: 'warn', text: e.message }); return false; } };
  S.has = (item) => !!(host.has && host.has(item));
  S.out = (e) => { if (host.event) host.event(e); };
  let depth = 0;
  S.run = (list, why = '') => {
    if (!list) return;
    if (++depth > 32) { depth--; S.out({ type: 'warn', text: `action loop (${why})` }); return; }
    try { for (const a0 of [].concat(list)) one(parseAction(a0), why); } finally { depth--; }
    if (depth === 0) for (const id of S.quests.active()) S.quests.check(id); // flags may have finished a step
  };
  function one(a, why) {
    if (!a || !a.do) return;
    if (Array.isArray(a.do) || typeof a.do === 'object') { if (a.if == null || S.test(a.if)) S.run(a.do, why); else if (a.else) S.run(a.else, why); return; }
    if (a.if != null && !S.test(a.if)) return;
    const st = S.st, arg = a.arg ?? '';
    S.trace.push(a.do + (arg ? ':' + arg : ''));
    if (S.trace.length > 200) S.trace.shift();
    switch (a.do) {
      case 'flag': st.flags[arg] = true; break;
      case 'unflag': delete st.flags[arg]; break;
      case 'var': { const m = /^([\w.-]+)\s*([=+-])\s*(-?\d+(?:\.\d+)?)$/.exec(arg); if (!m) break; const v = Number(m[3]); st.vars[m[1]] = m[2] === '=' ? v : (st.vars[m[1]] || 0) + (m[2] === '+' ? v : -v); break; }
      case 'standing': { const m = /^(\w+)\s*([+-]\d+)$/.exec(arg); if (m) st.standing[m[1]] = Math.max(-100, Math.min(100, (st.standing[m[1]] || 0) + Number(m[2]))); break; }
      case 'meet': st.met[arg] = true; st.codex[`char.${arg}`] = true; break;
      case 'codex': if (!st.codex[arg]) { st.codex[arg] = true; S.out({ type: 'codex', id: arg, entry: S.defs.codex[arg] }); } break;
      case 'seen': st.seen[arg] = true; break;
      case 'log': st.log.push(String(arg).slice(0, 160)); if (st.log.length > 60) st.log.shift(); break;
      case 'quest': case 'quest.start': { const [id, at] = arg.split('/'); S.quests.start(id, at); break; }
      case 'quest.step': { const [id, sid] = arg.split('/'); S.quests.enterStep(id, sid); break; }
      case 'quest.done': { const [id, end] = arg.split('/'); S.quests.finish(id, end || ''); break; }
      case 'quest.fail': S.quests.fail(arg); break;
      case 'track': if (S.quests.isActive(arg)) st.track = arg; break;
      case 'emit': { const [type, id] = arg.split('/'); S.emitQuest({ type, thing: id, zone: id, item: id, npc: id }); break; }
      default: if (host.act) host.act(a); // give, take, scene, coupons, toast, music, ... (the host knows those)
    }
  }
  S.quests = makeQuests(S);
  S.emitQuest = (ev) => S.quests.emit(ev);
  S.talk = (npc, node) => openTalk(S, npc, node);
  S.emit = S.emitQuest;
  S.tick = (dt) => S.quests.tick(dt);
  return S;
}
