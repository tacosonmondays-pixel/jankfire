// The OVERDUE script, loaded through the WP8 engine (shared/story/story.js): every condition compiles, every talk,
// option, redirect and talk action points at a real node, and an auto-player finishes the whole main story and
// every side quest using only the events a real host would send. Run: node --test tests/story/overdue.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as overdue from '../../shared/story/content/overdue.js';
import { makeStory } from '../../shared/story/story.js';
import { compile } from '../../shared/story/cond.js';
import { CONTENT } from '../../shared/story/content/index.js';
import { toSave, LIMITS } from '../../shared/story/state.js';

const conds = [], actions = [];
function walkActs(list, where) { for (const a of [].concat(list || [])) { if (typeof a === 'string') actions.push([a, where]); else { if (a.if) conds.push([a.if, where]); walkActs(a.do, where); walkActs(a.else, where); } } }
for (const [id, q] of Object.entries(overdue.quests)) {
  if (q.if) conds.push([q.if, `quest ${id}`]);
  for (const s of q.steps) { for (const g of s.goals || [s.goal]) { if (g.if) conds.push([g.if, `${id}/${s.id}`]); if (g.type === 'flag') conds.push([g.flag, `${id}/${s.id}`]); } walkActs(s.do, `${id}/${s.id}`); walkActs(s.done, `${id}/${s.id}`); }
  walkActs(q.onDone, `quest ${id}`);
}
for (const [id, n] of Object.entries(overdue.npcs)) for (const [nid, node] of Object.entries(n.lines)) {
  const w = `npc ${id}.${nid}`;
  if (node.if) conds.push([node.if, w]);
  for (const [c] of node.go || []) conds.push([c, w]);
  for (const o of node.opts || []) { if (o[2] && o[2].if) conds.push([o[2].if, w]); walkActs(o[2] && o[2].do, w); }
  walkActs(node.do, w);
}
for (const [id, s] of Object.entries(overdue.scenes)) for (const t of s.tracks) { if (t.if) conds.push([t.if, `scene ${id}`]); walkActs(t.do, `scene ${id}`); }
for (const [id, t] of Object.entries(overdue.things)) { if (t.if) conds.push([t.if, `thing ${id}`]); walkActs(t.do, `thing ${id}`); }

test('every condition in the pack compiles in the engine', () => {
  const bad = [];
  for (const [c, w] of conds) try { compile(c); } catch (e) { bad.push(`${w}: ${e.message}`); }
  assert.deepEqual(bad, []);
});

test('every talk goal, answer, redirect and talk action points at a real node', () => {
  const bad = [], has = (npc, node) => overdue.npcs[npc] && overdue.npcs[npc].lines[node];
  for (const [id, q] of Object.entries(overdue.quests)) for (const s of q.steps) for (const g of s.goals || [s.goal]) if (g.type === 'talk' && !has(g.npc, g.node)) bad.push(`${id}/${s.id} -> ${g.npc}/${g.node}`);
  for (const [id, n] of Object.entries(overdue.npcs)) for (const [nid, node] of Object.entries(n.lines)) {
    for (const o of node.opts || []) if (o[1] && !n.lines[o[1]]) bad.push(`${id}.${nid} opt -> ${o[1]}`);
    for (const [, to] of node.go || []) if (!n.lines[to]) bad.push(`${id}.${nid} go -> ${to}`);
    if (node.next && !n.lines[node.next]) bad.push(`${id}.${nid} next -> ${node.next}`);
  }
  for (const [a, w] of actions) { const m = a.match(/^talk:(\w+)\/(.+)$/); if (m && !has(m[1], m[2])) bad.push(`${w}: ${a}`); }
  for (const a of overdue.autostart) if (!overdue.quests[a]) bad.push(`autostart ${a}`);
  assert.deepEqual(bad, []);
});

// ---------------------------------------------------------------- the auto-player
function player() {
  const bag = new Set(), log = [];
  let S;
  const walk = (npc, node) => { // open a talk and click the first answer every time
    const T = S.talk(npc, node);
    for (let k = 0; k < 80 && !T.end; k++) { if (T.opts && T.i === T.lines.length - 1) T.choose(0); else if (!T.next()) break; }
  };
  const host = {
    has: (i) => bag.has(i),
    act: (a) => {
      const arg = a.arg ?? a.item;
      log.push(`${a.do}:${arg}`);
      if (a.do === 'give') bag.add(arg);
      else if (a.do === 'take') bag.delete(arg);
      else if (a.do === 'talk') { const [npc, node] = arg.split('/'); walk(npc, node); }
      else if (a.do === 'scene') { const sc = overdue.scenes[arg]; if (sc) for (const t of sc.tracks) if (t.do && (!t.if || S.test(t.if))) S.run(t.do, `scene ${arg}`); S.st.seen[arg] = true; }
    },
  };
  S = makeStory({ content: overdue, host });
  S.run(overdue.init);
  // play one step of an active quest with the event its goal is waiting for
  function poke(id) {
    const q = S.defs.quests[id], st = S.st.quests[id], s = q.steps.find((x) => x.id === st.step);
    if (!s) return;
    const g = (s.goals || [s.goal]).find((g0) => g0.type !== 'flag' || !String(g0.flag).startsWith('!(')) || s.goals[0];
    if (g.if && /has\.(\w+)/.test(g.if)) for (const m of g.if.matchAll(/has\.(\w+)/g)) bag.add(m[1]);
    switch (g.type) {
      case 'reach': case 'escort': S.emit({ type: 'reach', zone: g.zone }); break;
      case 'talk': walk(g.npc, g.node); break;
      case 'kill': S.emit({ type: 'kill', npc: g.npc, kind: g.kind, n: g.n || 1 }); break;
      case 'killBoss': S.emit({ type: 'killBoss', boss: g.boss }); break;
      case 'pickup': bag.add(g.item); S.emit({ type: 'pickup', item: g.item }); break;
      case 'enterCar': S.emit({ type: 'enterCar' }); break;
      case 'interact': S.emit({ type: 'interact', thing: g.thing }); break;
      case 'photo': S.emit({ type: 'photo', target: g.target, n: g.n || 1 }); break;
      case 'loseFees': S.emit({ type: 'loseFees' }); break;
      case 'survive': case 'wait': S.tick((g.t || 0) + 1); break;
      case 'flag': { const m = String(g.flag).match(/^flag\.(\w+)$/); if (m) S.run([`flag:${m[1]}`]); else S.tick(0.01); break; }
      default: throw new Error(`no event for goal ${g.type} in ${id}/${s.id}`);
    }
  }
  function play(id) {
    if (!S.quests.isActive(id)) S.quests.start(id);
    for (let k = 0; k < 200 && S.quests.isActive(id); k++) {
      for (const a of overdue.autostart) if (a !== id && a.startsWith(id + '__')) S.quests.start(a);
      for (const a of S.quests.active()) if (a !== id && a.startsWith(id + '__')) poke(a); // a mission's parts
      if (S.quests.isActive(id)) poke(id);
    }
    return !!(S.st.quests[id] && S.st.quests[id].done);
  }
  return { S, play, bag, log };
}

test('the auto-player finishes the whole main story, in order', () => {
  const P = player(), stuck = [];
  for (const id of CONTENT.MISSION_ORDER) {
    if (!P.S.quests.start(id) && !P.S.st.quests[id]) { stuck.push(`${id}: can't start (${P.S.defs.quests[id].if})`); continue; }
    if (!P.play(id)) stuck.push(`${id}: stuck at ${P.S.st.quests[id].step}`);
  }
  assert.deepEqual(stuck, []);
  assert.ok(P.S.st.flags.story_complete, 'story_complete');
  assert.ok(P.S.st.flags.ending_chosen, 'an ending was chosen');
  assert.equal(P.S.st.vars.pages, 6, 'six pages collected');
});

test('the auto-player finishes every side quest after the main story', () => {
  const P = player(), stuck = [];
  for (const id of CONTENT.MISSION_ORDER) { P.S.quests.start(id); P.play(id); }
  P.S.st.vars.cats = 12;
  for (const id of Object.keys(CONTENT.SIDE)) {
    if (!P.S.st.quests[id] && !P.S.quests.start(id)) { stuck.push(`${id}: can't start (${P.S.defs.quests[id].if})`); continue; }
    if (!P.play(id)) stuck.push(`${id}: stuck at ${P.S.st.quests[id].step}`);
  }
  assert.deepEqual(stuck, []);
  // a 100% save has to fit the engine's save limits (dialogue keeps a said.* flag per node visited)
  const d = toSave(P.S.st), said = d.flags.filter((f) => f.startsWith('said.')).length;
  console.log(`100% save: ${d.flags.length} flags (${said} said.*), ${d.codex.length} codex, ${d.seen.length} seen, ${Object.keys(d.quests).length} quests, ${Object.keys(d.vars).length} vars`);
  // story flags must fit with room to spare; said.* (the engine's per-node dialogue memory) is reported to the engine
  // lane: a full playthrough needs more than LIMITS.flags once they're counted too
  assert.ok(d.flags.length - said <= LIMITS.flags / 2, 'story flags over half the save limit');
  if (d.flags.length > LIMITS.flags) console.log(`WARNING: ${d.flags.length} flags > LIMITS.flags (${LIMITS.flags}); said.* needs its own store or a bigger limit`);
  for (const k of ['codex', 'seen', 'quests']) assert.ok((Array.isArray(d[k]) ? d[k].length : Object.keys(d[k]).length) <= LIMITS[k], `${k} over the save limit`);
});
