// story boss fights, the presentation half: who's in the arena, the phase cutscenes, the boss's clips and damage states,
// driven by the combat referee's events (it owns HP, hits and the real attacks). until those land, rehearsal fakes them:
// JF_STORY.boss.test('overtime_1', 0.49) = he's at 49% HP.
// events in (G.story.on or G.story.combat): { type: 'hit', kind, target, hp, max, head } { type: 'kill', kind, boss }
// { type: 'phase', kind, phase } { type: 'plate' } (the referee says the plate came off)
import { G } from '../ctx.js';
import { ME } from '../player.js';
import { actors, spawnActor, play } from './actors.js';
import { OT } from './overtime.js';

// per boss: where he stands, his phases (hp fraction they start below: from content/bosses.js), and what each quest
// step does to him. clip + hold = the pose he keeps afterwards
export const HOOKS = {
  overtime_1: {
    actor: 'overtime', at: 'gut:border', quest: 'm04_clocking_in', fight: 'fight',
    start: { clip: 'ot_idle', hold: true, dmg: 'fresh' },
    plate: 0.75, // (the plate comes off at 75% unless the referee says otherwise)
    phases: [null, { scene: 'ot1_coffee', clip: 'ot_coffee', hold: true, dmg: 'cracked' }, { scene: 'ot1_punching_in', clip: 'ot_stalk', hold: true, dmg: 'sparking' }],
    steps: { rip: { dmg: 'ripped', clip: 'ot_kneel', hold: true }, after: { clip: 'ot_kneel', hold: true } },
    stepDone: { after: 'ot1_retreat' },
  },
};

export function makeBoss(ST, { where, playScene }) {
  const B = { on: null, hp: 1, phase: 0, plateOff: false, lastStep: '' };
  const S = () => ST.S;
  const bossOfKind = (k) => (HOOKS[k] ? k : Object.keys(HOOKS).find((b) => HOOKS[b].actor === k || (k && String(k).startsWith(HOOKS[b].actor))));
  const actorOf = (b) => actors.get(HOOKS[b].actor);
  function pose(b, o) {
    if (!o) return; const a = actorOf(b); if (!a) return;
    if (o.dmg) OT.dmg(a, o.dmg);
    if (o.clip) { a.clip = null; play(a, o.clip, { hold: !!o.hold }); }
  }
  // the arena: he's there (spawned if the roster hasn't), facing you
  function enter(b) {
    const h = HOOKS[b]; B.on = b; B.hp = 1; B.phase = 0; B.plateOff = false;
    let a = actorOf(b);
    const p = where(h.at) || [ME.pos[0], ME.pos[1], ME.pos[2] - 12];
    if (!a) { const n = S().defs.npcs[h.actor] || { look: h.actor, voice: { kind: 'dialtone', pitch: 0.7 } }; a = spawnActor(h.actor, { ...n, look: n.look || h.actor }, p, Math.atan2(ME.pos[0] - p[0], ME.pos[2] - p[2]) + Math.PI); }
    a.boss = b; a.lookAt = null;
    pose(b, h.start);
  }
  function setPhase(b, i) {
    const h = HOOKS[b]; if (!h || i <= B.phase || !h.phases[i]) return;
    B.phase = i; const ph = h.phases[i];
    const after = () => pose(b, ph);
    if (ph.scene && S().defs.scenes[ph.scene]) playScene(ph.scene, { done: after }); else after();
    const a = actorOf(b); if (a && ph.dmg) OT.dmg(a, ph.dmg);
  }
  function hp(b, f) {
    const h = HOOKS[b], a = actorOf(b); if (!h) return;
    const was = B.hp; B.hp = Math.max(0, Math.min(1, f));
    if (a && was - B.hp > 0.015 && !a.clip?.hold) play(a, 'ot_flinch');
    if (!B.plateOff && h.plate != null && B.hp <= h.plate) { B.plateOff = true; if (a) play(a, 'ot_plate_rip'); }
    const D = S().defs.bosses?.[b] || (S().bosses || {})[b];
    // phase thresholds: from content (phases[i].hp = [from, to] in %), else the hooks' order
    const ranges = (D && D.phases) ? D.phases.map((p) => (p.hp ? p.hp[0] / 100 : 1)) : null;
    for (let i = h.phases.length - 1; i > 0; i--) { const below = ranges ? ranges[i] : 1 - i / h.phases.length; if (B.hp < below) { setPhase(b, i); break; } }
  }
  B.combat = (ev) => {
    if (!ev || typeof ev !== 'object') return;
    const b = bossOfKind(ev.boss || ev.kind || ev.target) || B.on; if (!b || !HOOKS[b]) return;
    if (ev.type === 'hit' && Number.isFinite(ev.hp) && Number.isFinite(ev.max) && ev.max > 0) hp(b, ev.hp / ev.max);
    if (ev.type === 'hit' && ev.head) { const a = actorOf(b); if (a) play(a, 'ot_flinch'); }
    if (ev.type === 'phase' && Number.isFinite(ev.phase)) setPhase(b, ev.phase);
    if (ev.type === 'plate') { B.plateOff = true; const a = actorOf(b); if (a) play(a, 'ot_plate_rip'); }
    if (ev.type === 'kill' && (ev.boss || HOOKS[b])) S().emit({ type: 'killBoss', boss: b });
  };
  B.test = (b, f) => { if (B.on !== b) enter(b); hp(b, f); return { hp: B.hp, phase: B.phase }; };
  // the quest side: entering the fight step sets him up; later steps pose him; some steps play a scene when done
  B.frame = () => {
    const objs = S().quests.objectives ? S().quests.objectives() : [];
    for (const [b, h] of Object.entries(HOOKS)) {
      const o = objs.find((x) => x.quest === h.quest); const key = o ? o.quest + '/' + o.step : '';
      if (key === B.lastStep) continue;
      const prev = B.lastStep; B.lastStep = key;
      if (prev.startsWith(h.quest + '/')) { const ps = prev.split('/')[1]; if (h.stepDone && h.stepDone[ps] && S().defs.scenes[h.stepDone[ps]]) playScene(h.stepDone[ps]); }
      if (!o) continue;
      if (o.step === h.fight) enter(b);
      else if (h.steps && h.steps[o.step]) { if (!actorOf(b)) enter(b); pose(b, h.steps[o.step]); }
    }
  };
  // listen to the referee
  if (G.story && typeof G.story.on === 'function') for (const k of ['hit', 'kill', 'phase', 'plate']) G.story.on(k, (m) => B.combat({ ...m, type: k }));
  if (G.story) G.story.combat = B.combat;
  return B;
}
