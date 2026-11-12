// OVERDUE quest engine: missions made of steps, each step waits for its goals (enter an area, talk, kill, pick up,
// a timer, a flag...), then runs its actions and moves on, maybe down a branch. Pure (no DOM, no Node), so the solo
// worker and a co-op StoryRoom run the same code. Content format: docs/story/SCHEMA.md.
// S (the story hub, story.js): S.st state · S.defs.quests · S.test(cond) · S.run(actions, why) · S.out(event) · S.has(item)

// goal types the engine knows. 'ev' = which event types count for it (the host emits events with that type)
export const GOALS = {
  reach: { ev: 'reach', keys: ['zone'] }, leave: { ev: 'leave', keys: ['zone'] },
  talk: { ev: 'talk', keys: ['npc', 'node'] }, kill: { ev: 'kill', keys: ['kind', 'npc'] }, killBoss: { ev: 'killBoss', keys: ['boss'] },
  pickup: { ev: 'pickup', keys: ['item'] }, deliver: { ev: 'talk', keys: [] }, enterCar: { ev: 'enterCar', keys: ['car'] },
  interact: { ev: 'interact', keys: ['thing'] }, photo: { ev: 'photo', keys: ['target'] }, escort: { ev: 'reach', keys: ['zone', 'npc'] }, // (an escort is done when the one you escort gets there: the host emits reach with npc)
  loseFees: { ev: 'loseFees', keys: [] }, scene: { ev: 'sceneEnd', keys: ['scene'] }, use: { ev: 'use', keys: ['item'] },
  // checked every tick, not by events:
  flag: { tick: true }, wait: { tick: true }, survive: { tick: true },
};
const any = (want, got) => want == null || (Array.isArray(want) ? want.includes(got) : want === got);
const goalsOf = (step) => step.goals || (step.goal ? [step.goal] : []);
const need = (g) => Math.max(1, g.n | 0 || 1);

export function makeQuests(S) {
  const st = () => S.st;
  const def = (id) => S.defs.quests[id];
  const stepOf = (d, sid) => d.steps.find((s) => s.id === sid);

  function enterStep(id, sid, quiet, hold) {
    const d = def(id), q = st().quests[id], s = stepOf(d, sid);
    if (!s) { finish(id, sid && sid.startsWith('end') ? sid.slice(4) || '' : ''); return; } // 'end' / 'end:good'
    q.step = sid; q.n = goalsOf(s).map(() => 0); q.t = 0; delete q.fin; if (hold) q.hold = true; else delete q.hold;
    if (!quiet) S.out({ type: 'stepStart', quest: id, step: sid, text: s.text });
    if (s.do) S.run(s.do, `quest ${id}/${sid}`);
    check(id);
  }

  function start(id, at) {
    const d = def(id);
    if (!d) { S.out({ type: 'warn', text: `no quest ${id}` }); return false; }
    const q0 = st().quests[id];
    if (q0 && !q0.failed && !(q0.done && d.repeat)) return false; // already running or done
    if (d.if && !S.test(d.if)) return false;
    st().quests[id] = { step: '', n: [], t: 0 };
    if (!st().track || !isActive(st().track)) st().track = id;
    S.out({ type: 'questStart', quest: id, title: d.title, kind: d.kind || 'side' });
    if (d.onStart) S.run(d.onStart, `quest ${id} start`);
    if (st().quests[id] && !st().quests[id].done) enterStep(id, at || d.steps[0].id);
    return true;
  }

  function stepDone(id, branch) {
    const d = def(id), q = st().quests[id], s = stepOf(d, q.step);
    if (!s || q.done) return;
    S.out({ type: 'stepDone', quest: id, step: s.id });
    q.fin = s.id; // (finishing: the re-check after its done actions mustn't finish it again)
    if (s.done) S.run(s.done, `quest ${id}/${s.id} done`);
    if (!isActive(id) || st().quests[id].step !== s.id) return; // an action already moved it (quest.step / quest.fail)
    let to = branch;
    if (!to && s.next != null) {
      if (typeof s.next === 'string') to = s.next;
      else for (const b of s.next) { if (typeof b === 'string') { to = b; break; } if (!b.if || S.test(b.if)) { to = b.to; break; } }
    }
    if (!to) { const i = d.steps.indexOf(s); to = d.steps[i + 1] ? d.steps[i + 1].id : 'end'; }
    enterStep(id, to);
  }

  function finish(id, end = '') {
    const d = def(id), q = st().quests[id];
    if (!q || q.done) return;
    q.done = true; q.step = ''; q.n = []; q.t = 0;
    if (end) q.end = end;
    const ends = d.ends && d.ends[end || 'default'];
    S.out({ type: 'questDone', quest: id, title: d.title, end, grade: ends && ends.grade, kind: d.kind || 'side' });
    if (d.reward) S.run(rewardActions(d.reward), `quest ${id} reward`);
    if (ends && ends.do) S.run(ends.do, `quest ${id} end ${end}`);
    if (d.onDone) S.run(d.onDone, `quest ${id} done`);
    if (st().track === id) st().track = nextTrack();
  }

  function fail(id, why = '') {
    const d = def(id), q = st().quests[id];
    if (!q || q.done || q.failed) return;
    const s = stepOf(d, q.step);
    S.out({ type: 'stepFail', quest: id, step: q.step, why: why || (s && s.failText) || '' });
    if (s && s.onFail) S.run(s.onFail, `quest ${id}/${s.id} fail`);
    if (!isActive(id) || st().quests[id].step !== (s && s.id)) return;
    if ((s && s.failQuest) || d.failQuest) { q.failed = true; S.out({ type: 'questFail', quest: id, title: d.title }); if (st().track === id) st().track = nextTrack(); return; }
    enterStep(id, (s && s.failTo) || q.step, true, true); // retry from the step's checkpoint
    S.out({ type: 'stepRetry', quest: id, step: st().quests[id].step });
  }

  const isActive = (id) => { const q = st().quests[id]; return !!(q && !q.done && !q.failed && def(id)); }; // (def: a quest an old save has that the content dropped isn't running)
  const active = () => Object.keys(st().quests).filter(isActive);
  const nextTrack = () => { const a = active(); return a.find((id) => (def(id) || {}).kind === 'main') || a[0] || ''; };

  // a goal reached its count: all of them (or any one, with step.any) finishes the step. a goal's own `to` is a branch
  function check(id) {
    if (!isActive(id)) return;
    const d = def(id), q = st().quests[id], s = stepOf(d, q.step);
    if (!s || q.fin === s.id) return;
    const G = goalsOf(s);
    for (let i = 0; i < G.length; i++) if (G[i].type === 'flag' && !(q.n[i] >= need(G[i])) && S.test(G[i].if || G[i].flag)) q.n[i] = need(G[i]); // (another goal's `if` is only a gate: a deliver's reach still needs the reach)
    const bad = s.fail && (typeof s.fail === 'string' || Array.isArray(s.fail) ? S.test(s.fail) : s.fail.type === 'flag' && S.test(s.fail.if || s.fail.flag));
    if (!bad) delete q.hold;
    else if (!q.hold) { fail(id); return; } // (hold: a retry waits for the fail condition to clear before it can fail again)
    const req = G.map((g, i) => [g, i]).filter(([g]) => !g.optional);
    const met = ([g, i]) => q.n[i] >= need(g);
    if (s.any) { const hit = req.find(met); if (hit) stepDone(id, hit[0].to); }
    else if (req.length && req.every(met)) stepDone(id);
    else if (!G.length && !s.timer) stepDone(id); // a step with nothing to do (just actions) passes straight through
  }

  // an event from the world: { type, zone?, npc?, node?, kind?, item?, n? }
  function emit(ev) {
    let hit = false;
    for (const id of active()) {
      const d = def(id), q = st().quests[id], s = stepOf(d, q.step);
      if (!s) continue;
      if (s.fail && typeof s.fail === 'object' && !Array.isArray(s.fail) && s.fail.type !== 'flag' && matches(s.fail, ev)) { fail(id); hit = true; continue; }
      const G = goalsOf(s);
      for (let i = 0; i < G.length; i++) {
        const g = G[i];
        if (q.n[i] >= need(g) || !matches(g, ev)) continue;
        if (g.type === 'deliver') { if (!any(g.to, ev.npc) || !S.has(g.item)) continue; S.run([`take:${g.item}`], 'deliver'); }
        q.n[i] = Math.min(need(g), q.n[i] + Math.max(1, ev.n | 0 || 1));
        hit = true;
        S.out({ type: 'progress', quest: id, step: s.id, goal: i, n: q.n[i], of: need(g) });
      }
      check(id);
    }
    return hit;
  }
  function matches(g, ev) {
    const G0 = GOALS[g.type];
    if (!G0 || G0.tick || G0.ev !== ev.type) return false;
    for (const k of G0.keys) if (g[k] != null && !any(g[k], ev[k])) return false;
    if (g.if && !S.test(g.if)) return false;
    return true;
  }

  function tick(dt) {
    for (const id of active()) {
      const d = def(id), q = st().quests[id], s = stepOf(d, q.step);
      if (!s) continue;
      q.t += dt;
      const G = goalsOf(s);
      for (let i = 0; i < G.length; i++) if ((G[i].type === 'wait' || G[i].type === 'survive') && q.t >= (G[i].t || 0)) q.n[i] = need(G[i]);
      if (s.timer && q.t >= s.timer && !G.some((g) => g.type === 'survive')) { fail(id, s.failText || 'out of time'); continue; }
      check(id);
    }
  }

  // what the HUD shows: the tracked quest first. marker = a zone / npc id / [x, y, z] the host turns into a waypoint
  function objectives() {
    const out = [];
    for (const id of active()) {
      const d = def(id), q = st().quests[id], s = stepOf(d, q.step);
      if (!s) continue;
      const G = goalsOf(s);
      const goals = G.map((g, i) => ({ text: g.text || '', n: q.n[i] || 0, of: need(g), done: q.n[i] >= need(g), optional: !!g.optional,
        marker: g.marker ?? g.zone ?? (g.type === 'talk' || g.type === 'deliver' ? g.npc || g.to : null) }));
      out.push({ quest: id, title: d.title, kind: d.kind || 'side', step: s.id, text: s.text || '', tracked: st().track === id,
        timer: s.timer ? Math.max(0, s.timer - q.t) : null, marker: s.marker ?? (goals.find((g) => !g.done && g.marker) || {}).marker ?? null, goals });
    }
    out.sort((a, b) => b.tracked - a.tracked || (a.kind === 'main' ? -1 : 0));
    return out;
  }

  // an old save (made before the content moved or renamed a step) can hold a running quest on a step that isn't there
  // any more: no objective, nothing finishes it, and every chapter after it waits forever. those start over from their
  // first step (the host calls this once a save is loaded). returns the quests it restarted
  function repair() {
    const out = [];
    for (const id of active()) {
      const d = def(id), q = st().quests[id];
      if (stepOf(d, q.step) || !d.steps.length) continue;
      S.out({ type: 'warn', text: `quest ${id}: step '${q.step}' is gone, starting it over` });
      out.push(id); enterStep(id, d.steps[0].id);
    }
    if (st().track && !isActive(st().track)) st().track = nextTrack();
    return out;
  }

  return { start, emit, tick, check, fail, finish, repair, enterStep: (id, sid) => isActive(id) && enterStep(id, sid), isActive, active, objectives };
}

// a reward block -> plain actions, so the host only has to know actions
export function rewardActions(r) {
  const A = [];
  if (r.coupons) A.push(`coupons:${r.coupons | 0}`);
  if (r.item) A.push({ do: 'give', item: r.item });
  for (const f of r.flags || []) A.push(`flag:${f}`);
  for (const k of Object.keys(r.standing || {})) A.push(`standing:${k}${r.standing[k] >= 0 ? '+' : ''}${r.standing[k]}`);
  for (const c of r.codex || []) A.push(`codex:${c}`);
  return A;
}
