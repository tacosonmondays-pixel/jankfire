// OVERDUE content pack for the WP8 story engine (docs/story/SCHEMA.md). The script is authored in the richer files next
// to this one (cast_*.js, missions/, side/, scenes_act*.js ...: see index.js); this module converts all of it into the
// engine's pack shape once, at import:
//   import * as overdue from './shared/story/content/overdue.js'; makeStory({ content: overdue, ... })
// Exports the engine keys (npcs, quests, scenes, codex, zones, things) plus `init` (actions for a new game),
// `autostart` (quest ids the host offers to S.quests.start whenever it likes: start() checks each one's `if`), and
// the systems data the engine doesn't own yet (cast, bosses, implants, loot, items, collectibles, endings, activities,
// districts, factions). Proposed SCHEMA additions for those are in docs/story/SCHEMA.md ("Additions from the script").
//
// How the authored format maps:
// - conditions 'flag:x !done:m standing.corp>=5' -> 'flag.x && !q.m.done && standing.corp >= 5'.
//   turf / fate / plan are exclusive flags ('turf.pinstripe.family', 'fate.mina.freed', 'flag.plan_lumps');
//   drift, cats, act, pages, frags.SET are vars the host (or these actions) keep (pages counts the pages_* flags); clock.D=hh:mm-hh:mm reads var.clock.D
//   (the district clock in minutes past midnight, kept by the host).
// - a mission's talks become nodes on the speaking NPC ('<quest>.<talk>.<node>'); the NPC's start node routes into
//   whichever of its quest talks is due (go: q.<quest>.at.<step>) and offers side quests it gives.
// - a step's `talk` (one that plays during a step) opens with the host action talk:NPC/NODE when the step starts.
// - choices become a talk on the 'choice' pseudo-NPC ('<quest>.<choice>'): the step that waits for the choice's flag
//   opens it; scenes open theirs with the same talk action.
// - deliver {item, zone} -> reach the zone holding the item (goal if: has.item), then take:item.
// - parts -> their own quests '<quest>__<part>', in autostart, gated by `if`.
import { CONTENT as C } from './index.js';

const FATES = ['alive', 'dead', 'gut', 'freed', 'gone', 'clocked_out', 'terminated', 'signed'];
const VOICE = { tuba: 'tuba', foghorn: 'tuba', kazoo: 'kazoo', dual_kazoo: 'kazoo', ukulele: 'kazoo', calliope: 'kazoo', trumpet_mute: 'kazoo', piccolo: 'kazoo',
  dialtone: 'dialtone', clarinet: 'crayon', choir: 'choir', organ: 'choir', theremin: 'wet', purr: 'wet' };
const voice = (v) => (v ? { kind: VOICE[v.kind] || (/(bassoon|oboe|trombone|accordion|saxophone|lawnmower|harmonica|cello)/.test(v.kind) ? 'grumble' : 'beep'), pitch: v.pitch, rate: v.rate, timbre: v.kind } : { kind: 'beep', pitch: 1, rate: 1 });
const hhmm = (s) => { const [h, m] = s.split(':').map(Number); return h * 60 + m; };

// ---------------------------------------------------------------- conditions
export function cond(src) {
  if (src == null || src === '') return null;
  return src.trim().split(/\s+/).map((t0) => {
    const neg = t0.startsWith('!'), t = neg ? t0.slice(1) : t0;
    let m, e;
    if ((m = t.match(/^flag:(\w+)$/))) e = `flag.${m[1]}`;
    else if ((m = t.match(/^done:(\w+)$/))) e = `q.${m[1]}.done`;
    else if ((m = t.match(/^active:(\w+)$/))) e = `q.${m[1]}.active`;
    else if ((m = t.match(/^has:(\w+)$/))) e = `has.${m[1]}`;
    else if ((m = t.match(/^implant:(\w+)$/))) e = `has.implant.${m[1]}`;
    else if ((m = t.match(/^standing\.(\w+)(>=|<=|>|<|=)(-?\d+)$/))) e = `standing.${m[1]} ${m[2] === '=' ? '==' : m[2]} ${m[3]}`;
    else if ((m = t.match(/^turf\.(\w+)=(\w+)$/))) e = `flag.turf.${m[1]}.${m[2]}`;
    else if ((m = t.match(/^fate\.(\w+)=(\w+)$/))) e = `flag.fate.${m[1]}.${m[2]}`;
    else if ((m = t.match(/^plan=(\w+)$/))) e = `flag.plan_${m[1]}`;
    else if ((m = t.match(/^clock\.(\w+)=(\d\d:\d\d)-(\d\d:\d\d)$/))) e = `(var.clock.${m[1]} >= ${hhmm(m[2])} && var.clock.${m[1]} < ${hhmm(m[3])})`;
    else if ((m = t.match(/^frags\.(\w+)(>=|<=|>|<|=)(-?\d+)$/))) e = `var.frags.${m[1]} ${m[2] === '=' ? '==' : m[2]} ${m[3]}`;
    else if ((m = t.match(/^(drift|cats|act|pages)(>=|<=|>|<|=)(-?\d+)$/))) e = `var.${m[1]} ${m[2] === '=' ? '==' : m[2]} ${m[3]}`;
    else throw new Error(`overdue pack: can't convert condition term '${t0}' in '${src}'`);
    return neg ? `!(${e})` : e;
  }).join(' && ');
}

// ---------------------------------------------------------------- actions
export function acts(list) {
  const out = [];
  for (const a of list || []) {
    let m;
    if ((m = a.match(/^flag:(pages_\w+)$/))) out.push({ if: `!flag.${m[1]}`, do: ['var:pages+1'] }, a); // a page of Option C: count it once
    else if ((m = a.match(/^(flag|unflag):(\w+)$/))) out.push(a);
    else if ((m = a.match(/^start:(\w+)$/))) out.push(`quest.start:${m[1]}`);
    else if ((m = a.match(/^standing\.(\w+):([+-]\d+)$/))) out.push(`standing:${m[1]}${m[2]}`);
    else if ((m = a.match(/^drift:([+-])(\d+)$/))) out.push(`var:drift${m[1]}${m[2]}`);
    else if ((m = a.match(/^turf:(\w+)=(\w+)$/))) { for (const f of Object.keys(C.FACTIONS)) out.push(`unflag:turf.${m[1]}.${f}`); out.push(`flag:turf.${m[1]}.${m[2]}`, a); }
    else if ((m = a.match(/^fate:(\w+)=(\w+)$/))) { for (const f of FATES) out.push(`unflag:fate.${m[1]}.${f}`); out.push(`flag:fate.${m[1]}.${m[2]}`); }
    else if ((m = a.match(/^collect:(\w+)$/))) { const c = C.COLLECTIBLES[m[1]]; out.push({ if: `!codex.col.${m[1]}`, do: [`codex:col.${m[1]}`, `var:frags.${c.set}+1`] }, a); }
    else out.push(a); // give, take, coupons, scene, boss, loot, implant, fees, call, unlock, talk: the host's verbs
  }
  return out;
}

// ---------------------------------------------------------------- dialogue lines and nodes
const line = (l, who) => (Array.isArray(l) ? l : who && !l.startsWith('*') ? [who, l] : l);
function node(n, prefix, defWho) {
  const o = {};
  if (n.say) o.say = n.say.map((l) => line(l, n.who && n.who !== defWho ? n.who : null));
  if (n.opts) o.opts = n.opts.map(([t, to, x]) => [t, prefix + to, x ? { ...(x.if ? { if: cond(x.if) } : {}), ...(x.do ? { do: acts(x.do) } : {}) } : undefined].filter((v) => v !== undefined));
  if (n.next) o.next = prefix + n.next;
  if (n.branch) o.go = n.branch.map(([c, to]) => [c == null ? 'true' : cond(c), prefix + to]);
  if (n.do) o.do = acts(n.do);
  if (n.cam) o.cam = n.cam;
  if (n.if) o.if = cond(n.if);
  return o;
}

function build() {
  const npcs = {}, quests = {}, codex = {}, zones = {}, things = {}, autostart = [], routes = {}, offers = {};
  const QS = { ...C.MISSIONS, ...C.SIDE };
  const ensureNpc = (id) => {
    if (npcs[id]) return npcs[id];
    const c = C.CAST[id];
    npcs[id] = c ? { id, name: c.name, title: c.title, look: id, voice: voice(c.voice), home: c.home ? { zone: c.home } : null, idle: 'idle', cam: 'closeup', lines: {} }
      : { id, name: id.toUpperCase(), title: '', look: id === 'choice' ? null : 'mannequin', voice: voice(null), home: null, idle: 'idle', lines: {} };
    return npcs[id];
  };
  const talkStart = (q, tid) => `${q}.${tid}.start`;

  // ---- quests
  // a step's after-actions run at the start of the step after it (or when the quest ends): the engine's stepDone
  // re-checks the same step when `done` actions run at depth 0, so we don't use `done` (reported to the engine lane)
  function convertSteps(qid, steps, T, choices) {
    const out = convertSteps0(qid, steps, T, choices);
    const tail = [];
    for (let i = 0; i < out.length; i++) if (out[i].done) { (i + 1 < out.length ? (out[i + 1].do = [...out[i].done, ...(out[i + 1].do || [])]) : tail.push(...out[i].done)); delete out[i].done; }
    out.tail = tail;
    return out;
  }
  function convertSteps0(qid, steps, T, choices) {
    return steps.map((s) => {
      const g0 = s.goal || {}, o = { id: s.id.startsWith('end') ? `x_${s.id}` : s.id, text: s.text || '' }; // 'end*' is the engine's word for finishing
      const pre = [], post = [];
      let g;
      switch (g0.type) {
        case 'talk': g = { type: 'talk', npc: g0.who, node: talkStart(qid, g0.talk) }; routes[g0.who] = routes[g0.who] || []; routes[g0.who].push([`q.${qid}.at.${s.id}`, talkStart(qid, g0.talk)]); break;
        case 'deliver': g = { type: 'reach', zone: g0.zone, if: `has.${g0.item}` }; post.push(`take:${g0.item}`); break;
        case 'escort': g = { type: 'escort', zone: g0.zone, npc: g0.who }; break;
        case 'interact': g = { type: 'interact', thing: g0.target }; break;
        case 'photo': g = { type: 'photo', target: g0.subject || g0.target, n: g0.n }; break;
        case 'survive': g = { type: 'survive', t: g0.secs }; break;
        case 'kill': g = { type: 'kill', n: g0.n, ...(g0.who && g0.who !== 'any' ? { npc: g0.who } : {}) }; break;
        case 'flag': g = { type: 'flag', flag: `flag.${g0.flag}` }; break;
        default: g = { ...g0 };
      }
      if (s.marker) g.marker = s.marker;
      if (s.if) { o.any = true; o.goals = [g, { type: 'flag', flag: `!(${cond(s.if)})`, text: '' }]; } // a step that only happens if: skipped when it doesn't apply
      else o.goal = g;
      if (s.scene) pre.push(`scene:${s.scene}`);
      if (s.talk && T[s.talk]) pre.push(`talk:${T[s.talk].with === 'change' ? 'you' : T[s.talk].with}/${talkStart(qid, s.talk)}`);
      // a step waiting for a choice's flag opens the choice
      if (g0.type === 'flag') for (const ch of choices || []) if (ch.options.some((op) => (op.do || []).includes(`flag:${g0.flag}`))) pre.push({ ...(ch.if ? { if: cond(ch.if) } : {}), do: [`talk:choice/${qid}.${ch.id}`] });
      if (s.do) post.push(...acts(s.do));
      if (pre.length) o.do = acts(pre.filter((x) => typeof x === 'string')).concat(pre.filter((x) => typeof x !== 'string'));
      if (post.length) o.done = post;
      if (s.timer) { o.timer = s.timer; if (s.fail && s.fail.type === 'timer') o.failText = 'out of time'; }
      if (s.fail && s.fail.type === 'flag') o.fail = { type: 'flag', flag: `flag.${s.fail.flag}` };
      if (s.notes) o.notes = s.notes;
      return o;
    });
  }
  function rewardOf(r) {
    if (!r) return { reward: null, extra: [] };
    const extra = [...(r.items || []).map((i) => `give:${i}`), ...(r.loot || []).map((l) => `loot:${l}`), ...(r.implants || []).map((i) => `give:${i}`)];
    return { reward: { coupons: r.coupons || 0, flags: r.flags || [], standing: r.standing || {} }, extra: acts(extra) };
  }
  for (const [qid, m] of Object.entries(QS)) {
    const T = m.talks || {};
    const req = [...((m.requires && m.requires.missions) || []).map((r) => `q.${r}.done`), cond(m.requires && m.requires.if)].filter(Boolean).join(' && ');
    const { reward, extra } = rewardOf(m.reward);
    const q = { id: qid, title: m.title, giver: m.giver, act: m.act || m.from, kind: m.kind === 'side' ? 'side' : 'main', blurb: m.logline,
      ...(req ? { if: req } : {}), steps: convertSteps(qid, m.steps, T, m.choices), reward, onDone: extra,
      scenes: { start: (m.scenes || [])[0] || null, end: null }, district: m.district };
    q.onDone = [...q.steps.tail, ...q.onDone];
    if (q.kind === 'main') q.onStart = [`var:act=${m.act}`];
    if (m.grade && m.grade.meets) q.ends = { default: { grade: m.grade.meets } };
    quests[qid] = q;
    // parts: their own quests
    for (const p of m.parts || []) {
      const pid = `${qid}__${p.id}`;
      quests[pid] = { id: pid, title: p.title, giver: m.giver, act: q.act, kind: q.kind, blurb: m.logline, if: [req, cond(p.if)].filter(Boolean).join(' && '), steps: convertSteps(qid, p.steps, T, []), reward: null, onDone: [], district: m.district };
      quests[pid].onDone = [...quests[pid].steps.tail, ...acts(p.do)];
      // part steps talk to the parent's talks: re-point their routes at the part quest
      for (const s of quests[pid].steps) for (const g of s.goals || [s.goal]) if (g.type === 'talk') routes[g.npc].forEach((r) => { if (r[1] === g.node) r[0] = `q.${pid}.at.${s.id}`; });
      autostart.push(pid);
    }
    if (m.kind !== 'side' || !m.giver) autostart.push(qid);
    else (offers[m.giver] = offers[m.giver] || []).push(qid);
    // talks -> nodes on the speaker
    for (const [tid, t] of Object.entries(T)) {
      const npc = ensureNpc(t.with === 'change' ? 'you' : t.with), prefix = `${qid}.${tid}.`;
      for (const [nid, n] of Object.entries(t.nodes)) npc.lines[prefix + nid] = node(n, prefix, t.with);
      if (t.cam) npc.lines[prefix + 'start'].cam = t.cam;
    }
    // choices -> the choice pseudo-npc
    for (const ch of m.choices || []) {
      const npc = ensureNpc('choice'), base = `${qid}.${ch.id}`;
      npc.lines[base] = { say: [`*${ch.prompt}*`], opts: ch.options.map((op, i) => [op.label, `${base}.${op.id}`, { ...(op.if ? { if: cond(op.if) } : {}), do: acts(op.do) }]) };
      for (const op of ch.options) npc.lines[`${base}.${op.id}`] = { say: [`*${op.consequence}*`] };
    }
  }
  // ---- every cast member is an npc; start = route into due talks, offer side quests, else a bark
  for (const id of Object.keys(C.CAST)) ensureNpc(id);
  for (const [id, npc] of Object.entries(npcs)) {
    if (id === 'choice') continue;
    const c = C.CAST[id];
    const go = (routes[id] || []).slice();
    const opts = [];
    for (const sq of offers[id] || []) {
      const q = quests[sq], oid = `offer.${sq}`;
      npc.lines[oid] = { say: [q.blurb], opts: [["i'll do it.", `${oid}.yes`, { do: [`quest.start:${sq}`] }], ['not now.', `${oid}.no`]] };
      npc.lines[`${oid}.yes`] = { say: ['*nods*'] };
      npc.lines[`${oid}.no`] = { say: ['*shrugs*'] };
      opts.push([`(${q.title.toLowerCase()})`, oid, { if: `!q.${sq}.started${q.if ? ` && ${q.if}` : ''}` }]);
    }
    npc.lines.start = { ...(go.length ? { go } : {}), say: c ? [c.samples[0]] : ['...'], ...(opts.length ? { opts } : {}), ...(c ? { again: [c.samples[1] || c.samples[0]] } : {}) };
    if (c) codex[`char.${id}`] = { kind: 'char', title: c.name, text: `${c.title}. ${c.look}` };
  }
  // ---- scenes: convert track conditions; choices inside scenes open the choice pseudo-npc
  const scenes = {};
  for (const [id, s] of Object.entries(C.SCENES)) scenes[id] = { id, ...s, skip: true, tracks: s.tracks.map((t) => ({ ...t, ...(t.if ? { if: cond(t.if) } : {}), ...(t.choice && s.mission ? { do: [`talk:choice/${s.mission}.${t.choice}`] } : {}) })) };
  // a step that plays a scene and waits on a flag only that scene can earn (seen_c4, heart_ripped): the scene's end sets it
  for (const [qid, m] of Object.entries(QS)) for (const st of m.steps || []) { const g = st.goal; if (!st.scene || !scenes[st.scene] || !g || g.type !== 'flag' || scenes[st.scene].tracks.some((t) => t.choice)) continue; // (a scene with a choice in it: skipping it mustn't skip the choice)
    if ((m.choices || []).some((ch) => ch.options.some((op) => (op.do || []).includes(`flag:${g.flag}`)))) continue;
    scenes[st.scene].onEnd = [...(scenes[st.scene].onEnd || []), `flag:${g.flag}`]; }
  // ---- zones and things: locations (positions come from the district generators), collectibles as interactables
  for (const [id, l] of Object.entries(C.LOCATIONS)) zones[id] = { name: l.name, district: l.district, p: null, r: 6 };
  for (const [id, c] of Object.entries(C.COLLECTIBLES)) {
    codex[`col.${id}`] = { kind: c.set === 'option_c' ? 'frag' : 'lore', title: c.name, text: c.text };
    things[`col_${id}`] = { zone: c.where, name: c.name, look: c.set, ...(c.if ? { if: cond(c.if) } : {}), do: acts([`collect:${id}`, ...(c.do || [])]), how: c.how };
  }
  for (const [id, it] of Object.entries(C.ITEMS)) if (it.kind === 'page') codex[`frag.${id}`] = { kind: 'frag', title: it.name, text: it.desc };
  // ---- a new game: who runs what, and the counters
  const init = [...Object.entries(C.DISTRICTS).map(([d, v]) => `flag:turf.${d}.${v.ruler}`), 'var:act=1', 'var:drift=0', 'var:pages=0', 'var:cats=0',
    ...Object.keys(C.COLLECTIBLE_SETS).map((s) => `var:frags.${s}=0`), ...['auntie', 'lumps', 'gordo', 'dale', 'mina', 'dot', 'overtime'].map((c) => `flag:fate.${c}.${c === 'dot' ? 'gut' : 'alive'}`)];
  return { npcs, quests, scenes, codex, zones, things, init, autostart };
}

const P = build();
export const { npcs, quests, scenes, codex, zones, things, init, autostart } = P;
export const cast = C.CAST, bosses = C.BOSSES, implants = C.IMPLANTS, items = C.ITEMS, collectibles = C.COLLECTIBLES, collectibleSets = C.COLLECTIBLE_SETS;
export const loot = { brands: C.BRANDS, modifiers: C.MODIFIERS, legendaries: C.LEGENDARIES, tables: C.LOOT_TABLES };
export const mechanics = C.MECHANICS, grapple = C.GRAPPLE;
export const endings = C.ENDING_SCRIPTS, activities = C.ACTIVITIES, districts = C.DISTRICTS, factions = C.FACTIONS, storyFlags = C.FLAGS;
