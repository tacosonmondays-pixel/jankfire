// story boss fights, the presentation half: who's in the arena, the phase cutscenes, the boss's clips and damage states,
// driven by the combat referee's events (it owns HP, hits and the real attacks). until those land, rehearsal fakes them:
// JF_STORY.boss.test('overtime_1', 0.49) = he's at 49% HP.
// events in (G.story.combat, from the systems lane's referee, or G.story.on): the referee owns HP, phases and timing:
// { type: 'hit', target, kind, hp, max, head, crit, part }   a flinch on crits
// { type: 'phase', target, kind, phase, invuln }           the phase cutscene + his pose for it
// { type: 'part', target, kind, part, state }              damage states: plate_off, cracked, sparking (OT.dmg)
// { type: 'act', target, clip, t0 }                        play an attack clip (its marks are in c_overtime.parts.json)
// { type: 'kill', target, kind, boss }                      the quest's killBoss
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
  function hp(b, f, crit) {
    const a = actorOf(b); if (!HOOKS[b]) return;
    const was = B.hp; B.hp = Math.max(0, Math.min(1, f));
    if (a && (crit || was - B.hp > 0.03) && !(a.clip && a.clip.hold && a.clip.name === 'ot_coffee')) play(a, 'ot_flinch');
  }
  B.combat = (ev) => {
    if (!ev || typeof ev !== 'object') return;
    const b = bossOfKind(ev.boss || ev.kind || ev.target) || B.on; if (!b || !HOOKS[b]) return;
    if (B.on !== b) enter(b);
    const a = actorOf(b);
    if (ev.type === 'hit' && Number.isFinite(ev.hp) && Number.isFinite(ev.max) && ev.max > 0) hp(b, ev.hp / ev.max, !!(ev.crit || ev.head));
    if (ev.type === 'phase' && Number.isFinite(ev.phase)) setPhase(b, ev.phase);
    if (ev.type === 'part' && a && typeof ev.state === 'string') { OT.dmg(a, ev.state); if (ev.state === 'plate_off' && !B.plateOff) { B.plateOff = true; a.clip = null; play(a, 'ot_plate_rip'); } }
    if (ev.type === 'act' && a && typeof ev.clip === 'string' && /^ot_[a-z_]+$/.test(ev.clip)) { a.clip = null; play(a, ev.clip); }
    if (ev.type === 'kill' && (ev.boss || HOOKS[b])) S().emit({ type: 'killBoss', boss: b });
  };
  // rehearsal stand-in for the referee: hp fraction -> the hit, the plate at 75%, the phases from content/bosses.js
  B.test = (b, f) => {
    if (B.on !== b) enter(b);
    const D = S().defs.bosses?.[b], ph = D && D.phases ? D.phases.map((p) => (p.hp ? p.hp[0] / 100 : 1)) : [1, 0.5, 0.45];
    B.combat({ type: 'hit', boss: b, hp: f * 100, max: 100 });
    if (f <= 0.75 && !B.plateOff) B.combat({ type: 'part', boss: b, part: 'plate', state: 'plate_off' });
    for (let i = ph.length - 1; i > 0; i--) if (f < ph[i]) { B.combat({ type: 'phase', boss: b, phase: i }); break; }
    return { hp: B.hp, phase: B.phase };
  };
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
