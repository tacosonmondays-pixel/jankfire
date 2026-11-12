// the chapter select (owner: "for story can you add a start from beggining, start from train start from overtime"):
// a save from later in the story, made by PLAYING the story up to there, never written by hand, so it can't drift from
// the content. a fresh save, the real sim systems (bag, body, the engine's state) and the real engine (shared/story),
// and every step done the way the game does it: talks talked through (first answer), scenes ended (as a skip does:
// seen + onEnd + sceneEnd), choices answered (first option), zones reached, fights won (the referee's kill events).
// whatever only a fight or a set piece sets (an encounter's flag) is set the way the rehearsal's shift+R does
// (public/js/story/boot.js fakeGoal). pure: no dom, no node. jump(id, { slot, loadout }) -> { save, log }
import { createSim } from './sim.js';
import './enginesys.js';
import './invsys.js';
import './bodysys.js';
import { newSave } from './save.js';
import { chapterOf } from './chapters.js';
import { makeStory } from './story.js';
import { openTalk } from './dialogue.js';
import { travelTo, DEFAULT_WORLD } from './worlds.js';
import { TRAIN } from './train.js';
import { PLACES } from '../city/slice.js';
import * as overdue from './content/overdue.js';

// where each jump lands: the main quest and the step you arrive on, and where you stand
//   train:    m06 TICKETS, PLEASE just boarded (the ride step): you start on the train, the ride in plays, then the fight
//   overtime: m04 CLOCKING IN past the sunset scene (the fight step): at the foot of the Gut Border Gate, facing him
//             (the arena's start mark: public/js/story/bossfight.js ARENA_MARKS 'arena.player', face 0)
export const JUMPS = {
  train: { quest: 'm06_tickets_please', step: 'ride', label: 'START FROM THE TRAIN', at: { map: DEFAULT_WORLD, p: PLACES['bottom:service_tunnel'].p, yaw: 0 }, travel: TRAIN.id, hype: 60 },
  overtime: { quest: 'm04_clocking_in', step: 'fight', label: 'START FROM OVERTIME', at: { map: DEFAULT_WORLD, p: [-44, 36, -2], yaw: 0 }, hype: 40 },
};
export const JUMP_SLOT = 3; // the scratch slot: never one of the 3 real ones (SAVE.slots), kept in this browser only

function content() { // (boot.js merge: the script as one engine pack)
  const D = { npcs: {}, quests: {}, scenes: {}, codex: {}, zones: {}, things: {}, bosses: {}, cast: {}, init: [], autostart: [] };
  for (const k of Object.keys(D)) { if (Array.isArray(D[k])) D[k].push(...(overdue[k] || [])); else Object.assign(D[k], overdue[k] || {}); }
  return D;
}
const GOALEV = { reach: 'reach', leave: 'leave', talk: 'talk', kill: 'kill', killBoss: 'killBoss', pickup: 'pickup', interact: 'interact', photo: 'photo', escort: 'reach', loseFees: 'loseFees', enterCar: 'enterCar', use: 'use', scene: 'sceneEnd', deliver: 'talk' };

export function jump(id, { slot = JUMP_SLOT, loadout = {}, max = 400 } = {}) {
  const J = typeof id === 'object' && id ? { at: { map: DEFAULT_WORLD, p: [0, 0.1, 6], yaw: 0 }, ...id } : JUMPS[id]; // (an object: any { quest, step } to play up to: tests)
  if (!J) throw new Error(`no jump ${id}`);
  const log = [];
  const sim = createSim({ send: () => {}, save: newSave(slot, DEFAULT_WORLD) });
  sim.msg({ t: 'join', name: 'jump' });
  const sty = (k, o) => sim.msg({ t: 'sty', k, ...o });
  sty('starter', { lo: loadout }); // a new game: your loadout is the starter kit (bar.js)
  const talks = [], scenes = [];
  const host = { // boot.js HOST, minus the screen: what the engine asks the world for
    has: (b) => (b.startsWith('implant.') ? sim.hasItem(b.slice(8)) || !!(sim.body && JSON.stringify(sim.body).includes(`"${b.slice(8)}"`)) : sim.hasItem(b)),
    act(a) {
      const arg = a.arg ?? '';
      switch (a.do) {
        case 'give': sty('qgive', { b: String(a.item ? (a.item.id || a.item.roll || 'item') : arg), n: 1 }); break;
        case 'take': sty('qtake', { b: arg, n: 1 }); break;
        case 'coupons': { const n = Number(arg) || 0; sty('qcoupons', { n }); S.st.vars.coupons = (S.st.vars.coupons || 0) + n; break; }
        case 'implant': sty('qimplant', { b: arg }); break;
        case 'fees': S.st.vars.fees = Math.max(0, (S.st.vars.fees || 0) + (Number(arg) || 0)); break;
        case 'scene': scenes.push(arg); break;
        case 'talk': { const [n, node] = arg.split('/'); if (S.defs.npcs[n]) talks.push([n, node || 'start']); break; }
      }
    },
    event(e) { if (e.type === 'questDone') { log.push(`done ${e.quest}`); autostart(); } },
  };
  const S = makeStory({ content: content(), state: sim.state, host });
  const autostart = () => { S.quests.repair(); for (const q of S.defs.autostart) S.quests.start(q); };
  // a new game (boot.js): the script's init once, the district clocks, then whatever can start
  S.run(S.defs.init || []); S.st.flags.init_done = true;
  for (const z of Object.values(S.defs.zones)) if (z.district) S.st.vars[`clock.${z.district}`] ??= 17 * 60 + 29;
  autostart();
  // a conversation, played the way a player plays it: every line, the first answer
  const talk = (npc, node) => { const T = openTalk(S, npc, node); for (let i = 0; i < 300 && !T.end; i++) { if (T.opts && !T.choose(0)) break; else if (!T.opts && !T.next()) break; } };
  const scene = (sid) => { const d = S.defs.scenes[sid]; S.st.seen[sid] = true; if (d && d.onEnd) S.run(d.onEnd, `scene ${sid}`); S.emit({ type: 'sceneEnd', scene: sid }); };
  const drain = () => { for (let k = 0; k < 40 && (talks.length || scenes.length); k++) { if (scenes.length) scene(scenes.shift()); else talk(...talks.shift()); S.tick(0.01); } };
  const main = () => S.quests.objectives().find((o) => o.kind === 'main') || null;
  const key = (o) => (o ? `${o.quest}.${o.step}.${o.goals.map((g) => (g.done ? 1 : 0)).join('')}` : '');
  for (let i = 0; i < max; i++) {
    S.tick(0.01);
    const o = main();
    if (!o) throw new Error(`jump ${id}: no main objective (done: ${log.join(', ')})`);
    if (o.quest === J.quest && o.step === J.step) break; // (there: what its start asked for, the ride in, plays where the game plays it)
    if (talks.length || scenes.length) { drain(); continue; }
    const q = S.defs.quests[o.quest], st = q.steps.find((x) => x.id === o.step), G0 = st.goals || (st.goal ? [st.goal] : []);
    const gi = G0.findIndex((g, k) => !o.goals[k].done && !g.optional), g = G0[gi < 0 ? 0 : gi], was = key(o);
    let how = '';
    if (!g) { S.tick(st.timer ? st.timer + 0.1 : 0.01); how = 'tick'; }
    else if (g.type === 'talk' || g.type === 'deliver') { // walk up and talk (the npc's own start routes to the quest's node), else straight to the node
      if (g.type === 'deliver' && g.item && !sim.hasItem(g.item)) sty('qgive', { b: g.item, n: 1 });
      const who = g.npc || g.to;
      if (who && S.defs.npcs[who]) { talk(who, 'start'); how = 'talk'; drain(); if (key(main()) === was && g.node) { talk(who, g.node); how = 'talk node'; } }
    } else if (g.type === 'flag') { // a scene's flag: the step played it (ended above); a choice: answered above. else a fight / set piece sets it
      const f = String(g.flag || '').replace(/^flag\./, '');
      if (st.scene && !S.st.seen[st.scene]) { scene(st.scene); how = 'scene'; } else { S.run([`flag:${f}`]); how = 'flag (set piece)'; }
    } else if (g.type === 'wait' || g.type === 'survive') { S.tick((g.t || 0) + 0.1); how = 'wait'; }
    else if (g.type === 'scene') { scene(g.scene); how = 'scene'; }
    if (key(main()) === was) { // nothing above moved it: the event the world would send (a reach, a kill, a pick up...)
      if (g && (g.type === 'pickup' || g.item) && !sim.hasItem(g.item)) sty('qgive', { b: g.item, n: 1 });
      if (g && g.type === 'flag') S.run([`flag:${String(g.flag || '').replace(/^flag\./, '')}`]);
      else if (g) S.emit({ type: GOALEV[g.type], zone: g.zone, npc: g.npc || g.to, node: g.node, kind: Array.isArray(g.kind) ? g.kind[0] : g.kind, item: g.item, thing: g.thing, boss: g.boss, car: g.car, target: g.target, scene: g.scene, n: g.n || 1 });
      how = (how ? how + ' > ' : '') + 'event ' + (g ? g.type : '');
    }
    log.push(`${o.quest}.${o.step}: ${how}`);
    if (i === max - 1) throw new Error(`jump ${id}: still not there after ${max} goals (at ${o.quest}.${o.step})`);
  }
  talks.length = scenes.length = 0;
  // the bits a player would have by now that only play gives: some HYPE banked, standing where the jump lands
  // the bits a player would have by now that only play gives: some HYPE banked, standing where the jump lands
  sim.hype = Math.max(sim.hype || 0, J.hype || 0);
  sim.me.pos = J.at.p.slice(); sim.me.yaw = J.at.yaw;
  sim.state = S.st; // (the engine's state is the sim's: makeStory kept the same object, unless something replaced it)
  let save = sim.snapshot('jump');
  save.chapter = chapterOf(save.data, save.chapter).id || save.chapter;
  save.coupons = Math.max(save.coupons || 0, S.st.vars.coupons | 0);
  delete save.at.fresh;
  if (J.travel) save = travelTo(save, J.travel); // on the train, knowing the way back (worlds.js data.travelFrom)
  return { save, log };
}
