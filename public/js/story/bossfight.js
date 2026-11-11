// story boss fights, the presentation half: who's in the arena, the phase cutscenes, the boss's clips and damage states,
// driven by the combat referee's events (it owns HP, hits and the real attacks). until those land, rehearsal fakes them:
// JF_STORY.boss.test('overtime_1', 0.49) = he's at 49% HP.
// events in (G.story.combat: the systems lane's story client hands each referee event over once): it owns HP, phases, timing:
// { type: 'hit', target, kind, hp, max, head, crit, part }   a flinch on crits
// { type: 'phase', target, kind, phase, invuln }           the phase cutscene + his pose for it
// { type: 'part', target, kind, part, state }              damage states: plate_off, cracked, sparking (OT.dmg)
// { type: 'act', target, clip, t0 }                        play an attack clip (its marks are in c_overtime.parts.json)
// { type: 'kill', target, kind, boss }                      the quest's killBoss
import { G } from '../ctx.js';
import { ME } from '../player.js';
import { hud } from '../hud.js';
import { actors, spawnActor, play, CLIPS } from './actors.js';
import { makeBossRef } from './bossref.js'; // the referee's boss: where he stands, his real hitboxes, the boss bar
import { OT } from './overtime.js';
import { marksNear } from '/shared/city/marks.js';
import { makeTrainFight, RP_ID } from './trainfight.js'; // REVENUE PROTECTION (m06): not an actor, its own show (the mask, the arms, THE GAP)

// per boss: where he stands, his phases (hp fraction they start below: from content/bosses.js), and what each quest
// step does to him. clip + hold = the pose he keeps afterwards
// the world lane's arena marks (shared/city/arenas.js gateArena, on main since #107; names are fixed, it tells us
// if one moves). marks.js will serve them from the chunks; until then, these
export const ARENA_MARKS = {
  'arena.boss': [-42, 36, -26], 'arena.player': [-44, 36, -2], ot_enter: [-44, 36, -30], ot_stairs: [-42.5, 35.8, 1.2], ot_retreat: [-44, 40, -52],
  'cam.wide': [-22, 45, 6], 'cam.gate': [-41, 38.2, -15], 'cam.roofs': [-73, 47.5, -4], // (arena.cam marks, #116: the gate's intro cameras)
};
export const HOOKS = {
  overtime_1: {
    actor: 'overtime', at: 'arena.boss', quest: 'm04_clocking_in', fight: 'fight', cp: 'arena.player', face: 0, place: ['THE GUT BORDER GATE', 'top of the long stairs'], // cp: where the fight starts you (and starts you again after a death), facing the gate
    start: { clip: 'ot_idle', hold: true, dmg: 'fresh' },
    phases: [null, { scene: 'ot1_coffee', clip: 'ot_coffee', hold: true, dmg: 'cracked' }, { scene: 'ot1_punching_in', clip: 'ot_stalk', hold: true, dmg: 'sparking' }],
    steps: { rip: { dmg: 'ripped', clip: 'ot_kneel', hold: true }, after: { clip: 'ot_kneel', hold: true } },
    stepDone: { after: 'ot1_retreat' },
  },
  // the later fights: his look per fight (bosses.js look), found by the step that fights him (its boss / killBoss goal)
  overtime_2: { actor: 'overtime', at: 'commute:spiral_freeway', start: { variant: 2, clip: 'ot_stalk', hold: true }, phases: [] },
  overtime_3: { actor: 'overtime', at: 'lates:waiting_room', start: { variant: 3, clip: 'ot_idle', hold: true }, phases: [] },
  overtime_4: { actor: 'overtime', at: 'corphill:master_clock', start: { variant: 4, clip: 'ot_idle', hold: true }, phases: [] },
  overtime_rehire: { actor: 'overtime', at: 'corphill:museum', start: { variant: 'rehire', clip: 'ot_idle', hold: true }, phases: [] },
};
for (const h of Object.values(HOOKS)) h.start.variant ??= 1;

export function makeBoss(ST, { where, playScene }) {
  const B = { on: null, hp: 1, phase: 0, plateOff: false, last: {} };
  ST.marks = { ...ARENA_MARKS, ...(ST.marks || {}) };
  try { for (const id of Object.keys(ARENA_MARKS)) { const m = marksNear('slice', -44, -14, 60, id)[0]; if (m) ST.marks[id] = [...m.p]; } } catch (e) { console.warn('arena marks', e); } // (the live ones win over the copies)
  const S = () => ST.S;
  const bossOfKind = (k) => (HOOKS[k] ? k : Object.keys(HOOKS).find((b) => HOOKS[b].actor === k || (k && String(k).startsWith(HOOKS[b].actor))));
  const actorOf = (b) => actors.get(HOOKS[b].actor);
  const TRAIN = makeTrainFight(ST, { playScene }); B.train = TRAIN;
  const REF = makeBossRef({ actorOf: (b) => (HOOKS[b] ? actorOf(b) : null), busy: () => !!(ST.scene && ST.scene.playing()), boxes: (c) => (c.id === RP_ID ? TRAIN.boxes() : null), own: (who) => who === 'revenue_protection' });
  B.tick = (dt) => { REF.tick(dt); TRAIN.tick(dt); }; // (every frame: boot.js)
  if (G.story) { G.story.fightKey = TRAIN.drive.key; G.story.fightScale = TRAIN.timeScale; } // the Blood Drive's trigger, the hit-stop on a sever (story/main.js asks)
  function pose(b, o) {
    if (!o) return; const a = actorOf(b); if (!a) return;
    if (o.variant != null) OT.variant(a, o.variant);
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
    if (a && (crit || was - B.hp > 0.03) && !(a.clip && a.clip.hold && a.clip.name === 'ot_coffee') && performance.now() > (B.actT || 0)) play(a, 'ot_flinch'); // (never over an attack: its tell has to read)
  }
  B.combat = (ev) => {
    if (!ev || typeof ev !== 'object') return;
    REF.combat(ev);
    if (TRAIN.combat(ev)) return; // (the train fight's events are its own)
    if (ev.target === 'me' || ev.type === 'down' || ev.type === 'up') return; // (what happens to you is not his HP)
    const id = ev.boss || ev.kind || ev.target;
    // everyone else: a kill counts for the quests (goals match the enemy id or the named npc)
    if (ev.type === 'kill' && !ev.boss && !HOOKS[id] && !(B.on && HOOKS[B.on].actor === id)) { if (typeof ev.kind === 'string') S().emit({ type: 'kill', kind: ev.kind, npc: typeof ev.npc === 'string' ? ev.npc : ev.kind, n: 1 }); return; }
    const b = HOOKS[id] ? id : (B.on && HOOKS[B.on].actor === id ? B.on : bossOfKind(id) || B.on); if (!b || !HOOKS[b]) return; // ('overtime' = whichever fight is on)
    if (B.on !== b) enter(b);
    const a = actorOf(b);
    if (ev.type === 'hit' && Number.isFinite(ev.hp) && Number.isFinite(ev.max) && ev.max > 0) hp(b, ev.hp / ev.max, !!(ev.crit || ev.head));
    if (ev.type === 'phase' && Number.isFinite(ev.phase)) setPhase(b, ev.phase);
    if (ev.type === 'part' && a && typeof ev.state === 'string') { OT.dmg(a, ev.state); if (ev.state === 'plate_off' && !B.plateOff) { B.plateOff = true; a.clip = null; play(a, 'ot_plate_rip'); } }
    if (ev.type === 'act' && a && typeof ev.clip === 'string' && /^ot_[a-z_]+$/.test(ev.clip)) { a.clip = null; play(a, ev.clip); B.actT = performance.now() + (CLIPS[ev.clip] ? Math.min(6, CLIPS[ev.clip].len) * 1000 : 0); }
    if (ev.type === 'kill' && (ev.boss || HOOKS[b])) { if (a && ev.defeat) { a.clip = null; play(a, 'ot_kneel', { hold: true }); } S().emit({ type: 'killBoss', boss: b }); } // (beaten, not dead: on one knee until the story's next step)
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
  // the real fight: ask the referee for him (it has the HP, the phases and the attacks). at the arena's mark on the
  // slice; anywhere else (the test lot) a few steps in front of you. nothing happens where no referee runs.
  // in the slice a fight that has a start spot (cp) and finds you far from it cuts there first: a fade, the place's
  // name, and you're at the foot of the arena facing him (the referee moves you: refsys.js 'warp')
  const r2 = (x) => Math.round(x * 100) / 100;
  B.spawn = (b) => {
    const h = HOOKS[b]; if (!h || !G.story || !G.story.send) return;
    if (B.on !== b) enter(b);
    const city = G.cfg && G.cfg.map === 'story_slice', p = city ? where(h.at) : null, cp = city && h.cp ? where(h.cp) : null;
    const at = p || [ME.pos[0] - Math.sin(ME.yaw) * 14, ME.pos[1], ME.pos[2] - Math.cos(ME.yaw) * 14];
    const go = () => G.story.send('spawn', { kind: b, id: b, at: at.map(r2) });
    if (cp && Math.hypot(ME.pos[0] - cp[0], ME.pos[2] - cp[2]) > B.ARRIVE) arrive(cp, h, go); else go();
  };
  B.ARRIVE = 45; // metres from the arena's start past which a fight cuts you there
  function arrive(cp, h, then) {
    if (B.arriving) return; B.arriving = true;
    const f = document.getElementById('stFade');
    const wait = () => { if (ST.scene && ST.scene.playing()) { setTimeout(wait, 200); return; } // (after the scene that led here)
      if (f) { f.style.transition = 'opacity .45s'; f.style.opacity = 1; }
      setTimeout(() => {
        G.story.send('warp', { at: cp.map(r2), yaw: h.face || 0 }); then(); // (in order: you're there before he is)
        setTimeout(() => { B.arriving = false; if (f) { f.style.transition = 'opacity .9s'; f.style.opacity = 0; } if (h.place) hud.msg(h.place[0], 2.6, 'brag'); }, 650);
      }, 480);
    };
    wait();
  }
  // the referee moved you (a fight's start) or put you back at a fight's start after a death: face the fight. the
  // streamed city holds you at your last good spot while chunks load: that spot moves with you, or it pulls you back
  if (G.story && G.story.on) {
    G.story.on('warped', (m) => { if (Array.isArray(m.at) && m.at.length === 3 && m.at.every(Number.isFinite)) { ME.hold = m.at.slice(); ME.pos = m.at.slice(); } if (Number.isFinite(m.yaw)) { ME.yaw = m.yaw; ME.pitch = 0; } });
    G.story.on('cp', (m) => { if (Number.isFinite(m.yaw)) { ME.yaw = m.yaw; ME.pitch = 0; } if (B.on && HOOKS[B.on] && HOOKS[B.on].place) hud.msg('BEEP. CLUNK. BACK IN THE QUEUE.', 2.2, 'brag'); });
  }
  // the quest side: entering the fight step sets him up; later steps pose him; some steps play a scene when done
  const fightStep = (b, o) => {
    const h = HOOKS[b]; if (h.fight) return o.step === h.fight;
    const q = S().defs.quests[o.quest], st = q && q.steps.find((x) => x.id === o.step); if (!st) return false;
    return [].concat(st.goals || [], st.goal || []).some((g) => g.type === 'killBoss' && g.boss === b);
  };
  B.frame = () => {
    TRAIN.frame();
    const objs = S().quests.objectives ? S().quests.objectives() : [];
    const D = S().defs.bosses || {};
    for (const [b, h] of Object.entries(HOOKS)) {
      const quest = h.quest || (D[b] && D[b].quest); if (!quest) continue;
      const o = objs.find((x) => x.quest === quest); const key = o ? o.quest + '/' + o.step : '';
      if (key === (B.last[b] || '')) continue;
      const prev = B.last[b] || ''; B.last[b] = key;
      if (prev) { const ps = prev.split('/')[1]; if (h.stepDone && h.stepDone[ps] && S().defs.scenes[h.stepDone[ps]]) playScene(h.stepDone[ps]); }
      if (!o) continue;
      if (fightStep(b, o)) { enter(b); B.spawn(b); }
      else if (h.steps && h.steps[o.step]) { if (!actorOf(b)) enter(b); pose(b, h.steps[o.step]); }
    }
  };
  // listen to the referee
  if (G.story) G.story.combat = B.combat;
  return B;
}
