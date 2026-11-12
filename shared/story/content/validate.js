// OVERDUE content validator. validate(content) returns a list of problems (strings); [] means every id and reference
// in the story content resolves: cast, missions, side quests, scenes, bosses, implants, items, loot, collectibles,
// flags, locations, and every `if` condition and `do` action string. Pure: no Node or DOM APIs, so the quest engine
// can run it at load in dev builds, and tests/story/content.test.mjs runs it in CI.

const GOALS = new Set(['reach', 'pickup', 'deliver', 'kill', 'killBoss', 'talk', 'enterCar', 'survive', 'escort', 'photo', 'interact', 'loseFees', 'flag']);
const ENDING_KEYS = ['on_time', 'late', 'off_books', 'nap_time'];
const SCENE_KINDS = new Set(['cinematic', 'panels', 'flashback', 'boss', 'moment', 'recap']);
const SLOTS = new Set(['head', 'eyes', 'mouth', 'heart', 'lungs', 'guts', 'spine', 'arms', 'legs', 'skin']);
const RARITIES = new Set(['common', 'rare', 'epic', 'legendary', 'premium']);
const FATES = new Set(['alive', 'dead', 'gut', 'freed', 'gone', 'clocked_out', 'terminated', 'signed']);
const OPS = '(>=|<=|>|<|=)';
const NUM = '-?\\d+';
const has = (o, k) => !!o && typeof k === 'string' && Object.hasOwn(o, k);

export function validate(C) {
  const errs = [];
  const err = (where, msg) => errs.push(`${where}: ${msg}`);
  const flagsUsed = new Set();
  const quests = { ...C.MISSIONS, ...C.SIDE };
  const isQuest = (id) => has(quests, id);
  const isSpeaker = (k) => has(C.CAST, k) || C.SPEAKERS.includes(k) || k === 'you';

  // ---- conditions and actions
  const flag = (where, f) => { flagsUsed.add(f); if (!has(C.FLAGS, f)) err(where, `undeclared flag '${f}'`); };
  function cond(where, s) {
    if (s == null) return;
    if (typeof s !== 'string' || !s.trim()) { err(where, `bad condition ${JSON.stringify(s)}`); return; }
    for (let t of s.trim().split(/\s+/)) {
      if (t.startsWith('!')) t = t.slice(1);
      let m;
      if ((m = t.match(/^flag:([a-z0-9_]+)$/))) flag(where, m[1]);
      else if ((m = t.match(/^(done|active):([a-z0-9_]+)$/))) { if (!isQuest(m[2])) err(where, `unknown quest '${m[2]}' in condition`); }
      else if ((m = t.match(/^has:([a-z0-9_]+)$/))) { if (!has(C.ITEMS, m[1])) err(where, `unknown item '${m[1]}'`); }
      else if ((m = t.match(/^implant:([a-z0-9_]+)$/))) { if (!has(C.IMPLANTS, m[1])) err(where, `unknown implant '${m[1]}'`); }
      else if ((m = t.match(new RegExp(`^standing\\.([a-z]+)${OPS}${NUM}$`)))) { if (!has(C.STANDING, m[1])) err(where, `unknown standing '${m[1]}'`); }
      else if ((m = t.match(/^turf\.([a-z]+)=([a-z_]+)$/))) { if (!has(C.DISTRICTS, m[1])) err(where, `unknown district '${m[1]}'`); if (!has(C.FACTIONS, m[2])) err(where, `unknown faction '${m[2]}'`); }
      else if ((m = t.match(/^fate\.([a-z0-9_]+)=([a-z_]+)$/))) { if (!has(C.CAST, m[1])) err(where, `unknown cast '${m[1]}' in fate`); if (!FATES.has(m[2])) err(where, `unknown fate '${m[2]}'`); }
      else if ((m = t.match(/^plan=(lumps|gordo|auntie)$/))) { /* ok */ }
      else if ((m = t.match(/^clock\.([a-z]+)=\d\d:\d\d-\d\d:\d\d$/))) { if (!has(C.DISTRICTS, m[1])) err(where, `unknown district '${m[1]}'`); }
      else if ((m = t.match(new RegExp(`^frags\\.([a-z]+)${OPS}${NUM}$`)))) { if (!has(C.COLLECTIBLE_SETS, m[1])) err(where, `unknown fragment set '${m[1]}'`); }
      else if (new RegExp(`^(drift|cats|act|pages)${OPS}${NUM}$`).test(t)) { /* ok */ }
      else err(where, `unparsed condition term '${t}'`);
    }
  }
  function act(where, a) {
    if (typeof a !== 'string') { err(where, `bad action ${JSON.stringify(a)}`); return; }
    let m;
    if ((m = a.match(/^(flag|unflag):([a-z0-9_]+)$/))) flag(where, m[2]);
    else if ((m = a.match(/^start:([a-z0-9_]+)$/))) { if (!isQuest(m[1])) err(where, `unknown quest '${m[1]}'`); }
    else if ((m = a.match(/^(give|take):([a-z0-9_]+)$/))) { if (!has(C.ITEMS, m[2]) && !has(C.IMPLANTS, m[2]) && !has(C.LEGENDARIES, m[2])) err(where, `unknown item '${m[2]}'`); }
    else if ((m = a.match(/^implant:([a-z0-9_]+)$/))) { if (!has(C.IMPLANTS, m[1])) err(where, `unknown implant '${m[1]}'`); }
    else if ((m = a.match(new RegExp(`^(coupons|drift|fees):[+-]\\d+$`)))) { /* ok */ }
    else if ((m = a.match(/^standing\.([a-z]+):[+-]\d+$/))) { if (!has(C.STANDING, m[1])) err(where, `unknown standing '${m[1]}'`); }
    else if ((m = a.match(/^turf:([a-z]+)=([a-z_]+)$/))) { if (!has(C.DISTRICTS, m[1])) err(where, `unknown district '${m[1]}'`); if (!has(C.FACTIONS, m[2])) err(where, `unknown faction '${m[2]}'`); }
    else if ((m = a.match(/^scene:([a-z0-9_]+)$/))) { if (!has(C.SCENES, m[1])) err(where, `unknown scene '${m[1]}'`); }
    else if ((m = a.match(/^boss:([a-z0-9_]+)$/))) { if (!has(C.BOSSES, m[1])) err(where, `unknown boss '${m[1]}'`); }
    else if ((m = a.match(/^fate:([a-z0-9_]+)=([a-z_]+)$/))) { if (!has(C.CAST, m[1])) err(where, `unknown cast '${m[1]}'`); if (!FATES.has(m[2])) err(where, `unknown fate '${m[2]}'`); }
    else if ((m = a.match(/^loot:([a-z0-9_]+)$/))) { if (!has(C.LOOT_TABLES, m[1])) err(where, `unknown loot table '${m[1]}'`); }
    else if ((m = a.match(/^unlock:([a-z]+:[a-z0-9_]+)$/))) { if (!has(C.LOCATIONS, m[1])) err(where, `unknown location '${m[1]}'`); }
    else if ((m = a.match(/^collect:([a-z0-9_]+)$/))) { if (!has(C.COLLECTIBLES, m[1])) err(where, `unknown collectible '${m[1]}'`); }
    else if ((m = a.match(/^call:([a-z0-9_]+)$/))) { if (!has(C.CAST, m[1])) err(where, `unknown cast '${m[1]}'`); }
    else if ((m = a.match(/^anim:([a-z0-9_]+)\/([a-z0-9_]+)$/))) { if (!has(C.CAST, m[1])) err(where, `unknown cast '${m[1]}'`); } // (a cast member plays a clip: actors.js CLIPS, the host's 'anim')
    else err(where, `unparsed action '${a}'`);
  }
  const acts = (where, list) => { if (list == null) return; if (!Array.isArray(list)) { err(where, 'do must be an array'); return; } list.forEach((a) => act(where, a)); };
  const loc = (where, id) => { if (id != null && !has(C.LOCATIONS, id)) err(where, `unknown location '${id}'`); };
  const cast = (where, id) => { if (id != null && !has(C.CAST, id)) err(where, `unknown cast '${id}'`); };
  const item = (where, id) => { if (!has(C.ITEMS, id) && !has(C.IMPLANTS, id) && !has(C.LEGENDARIES, id)) err(where, `unknown item '${id}'`); };

  // ---- world
  for (const [id, f] of Object.entries(C.FACTIONS)) cast(`faction ${id}`, f.leader);
  for (const [id, d] of Object.entries(C.DISTRICTS)) { if (!has(C.FACTIONS, d.ruler)) err(`district ${id}`, `unknown ruler '${d.ruler}'`); if (d.takeover && !has(C.FACTIONS, d.takeover)) err(`district ${id}`, `unknown takeover '${d.takeover}'`); }
  for (const [id, l] of Object.entries(C.LOCATIONS)) { if (!has(C.DISTRICTS, l.district)) err(`location ${id}`, `unknown district '${l.district}'`); if (id.split(':')[0] !== l.district) err(`location ${id}`, 'id prefix must be its district'); }

  // ---- cast
  for (const [id, c] of Object.entries(C.CAST)) {
    const w = `cast ${id}`;
    for (const k of ['name', 'title', 'role', 'body', 'look', 'wants', 'fears', 'secret', 'arc', 'speech', 'samples', 'rel', 'fate']) if (c[k] == null) err(w, `missing ${k}`);
    loc(w, c.home);
    if (c.met != null && !isQuest(c.met)) err(w, `met in unknown quest '${c.met}'`);
    for (const r of Object.keys(c.rel || {})) cast(`${w} rel`, r);
    for (const e of ENDING_KEYS) if (!c.fate || typeof c.fate[e] !== 'string') err(w, `missing fate.${e}`);
  }

  // ---- talks (missions and side quests share the format)
  function talks(w, T, choices) {
    for (const [tid, t] of Object.entries(T || {})) {
      const tw = `${w} talk ${tid}`;
      if (t.with !== 'change' && !isSpeaker(t.with)) err(tw, `unknown speaker '${t.with}'`);
      const nodes = t.nodes || {};
      if (!has(nodes, 'start')) err(tw, 'no start node');
      for (const [nid, n] of Object.entries(nodes)) {
        const nw = `${tw}.${nid}`;
        if (n.who) cast(nw, n.who);
        for (const line of n.say || []) if (Array.isArray(line)) { if (!isSpeaker(line[0])) err(nw, `unknown speaker '${line[0]}'`); } else if (line && typeof line === 'object' && typeof line.t === 'string') { if (line.who && !isSpeaker(line.who)) err(nw, `unknown speaker '${line.who}'`); if (line.if != null) cond(nw, line.if); acts(nw, line.do); } else if (typeof line !== 'string') err(nw, 'bad line');
        if (n.next && !has(nodes, n.next)) err(nw, `next -> missing node '${n.next}'`);
        for (const br of n.branch || []) { if (!Array.isArray(br) || !has(nodes, br[1])) err(nw, `branch -> missing node '${br && br[1]}'`); else if (br[0] != null) cond(nw, br[0]); }
        for (const o of n.opts || []) {
          if (!Array.isArray(o) || typeof o[0] !== 'string' || typeof o[1] !== 'string') { err(nw, 'bad option'); continue; }
          if (!has(nodes, o[1])) err(nw, `option '${o[0]}' -> missing node '${o[1]}'`);
          if (o[2]) { cond(nw, o[2].if); acts(nw, o[2].do); }
        }
        acts(nw, n.do);
        if (n.if !== undefined) cond(nw, n.if);
        if (n.choice && !(choices || []).some((c) => c.id === n.choice)) err(nw, `unknown choice '${n.choice}'`);
      }
    }
  }
  function steps(w, list, T) {
    const ids = new Set();
    for (const s of list || []) {
      const sw = `${w} step ${s.id}`;
      if (ids.has(s.id)) err(sw, 'duplicate step id'); ids.add(s.id);
      const g = s.goal || {};
      if (!GOALS.has(g.type)) err(sw, `bad goal type '${g.type}'`);
      if (g.zone) loc(sw, g.zone);
      if (g.target && !has(C.LOCATIONS, g.target)) err(sw, `unknown target '${g.target}'`);
      if (g.item) item(sw, g.item);
      if (g.boss && !has(C.BOSSES, g.boss)) err(sw, `unknown boss '${g.boss}'`);
      if (g.who && g.who !== 'any' && !isSpeaker(g.who)) err(sw, `unknown who '${g.who}'`);
      if (g.flag) flag(sw, g.flag);
      if (g.talk && !has(T, g.talk)) err(sw, `unknown talk '${g.talk}'`);
      if (s.talk && !has(T, s.talk)) err(sw, `unknown talk '${s.talk}'`);
      if (s.scene && !has(C.SCENES, s.scene)) err(sw, `unknown scene '${s.scene}'`);
      if (s.boss && !has(C.BOSSES, s.boss)) err(sw, `unknown boss '${s.boss}'`);
      if (s.marker) loc(sw, s.marker);
      if (s.fail && s.fail.flag) flag(sw, s.fail.flag);
      if (s.if) cond(sw, s.if);
      acts(sw, s.do);
    }
  }
  function choices(w, list) {
    for (const ch of list || []) if (ch.if) cond(`${w} choice ${ch.id}`, ch.if);
    for (const ch of list || []) for (const o of ch.options || []) { const ow = `${w} choice ${ch.id}.${o.id}`; cond(ow, o.if); acts(ow, o.do); if (typeof o.consequence !== 'string') err(ow, 'missing consequence'); }
  }
  function reward(w, r) {
    if (!r) return;
    for (const i of r.items || []) item(`${w} reward`, i);
    for (const i of r.implants || []) if (!has(C.IMPLANTS, i)) err(`${w} reward`, `unknown implant '${i}'`);
    for (const l of r.loot || []) if (!has(C.LOOT_TABLES, l) && !has(C.LEGENDARIES, l)) err(`${w} reward`, `unknown loot '${l}'`);
    for (const f of r.flags || []) flag(`${w} reward`, f);
    for (const s of Object.keys(r.standing || {})) if (!has(C.STANDING, s)) err(`${w} reward`, `unknown standing '${s}'`);
  }

  // ---- missions and side quests
  for (const [id, m] of Object.entries(quests)) {
    const w = `quest ${id}`;
    for (const k of ['title', 'logline', 'steps']) if (m[k] == null) err(w, `missing ${k}`);
    if (m.giver) cast(w, m.giver);
    if (m.district && !has(C.DISTRICTS, m.district)) err(w, `unknown district '${m.district}'`);
    (m.locations || []).forEach((l) => loc(w, l));
    (m.cast || []).forEach((c) => cast(w, c));
    for (const r of (m.requires && m.requires.missions) || []) if (!isQuest(r)) err(w, `requires unknown quest '${r}'`);
    if (m.requires) cond(w, m.requires.if);
    steps(w, m.steps, m.talks || {});
    talks(w, m.talks, m.choices);
    choices(w, m.choices);
    for (const s of m.scenes || []) if (!has(C.SCENES, s)) err(w, `unknown scene '${s}'`);
    reward(w, m.reward);
    for (const p of m.parts || []) { steps(`${w} part ${p.id}`, p.steps, m.talks || {}); acts(`${w} part ${p.id}`, p.do); if (p.if) cond(`${w} part ${p.id}`, p.if); }
  }

  // ---- scenes
  for (const [id, s] of Object.entries(C.SCENES)) {
    const w = `scene ${id}`;
    if (!SCENE_KINDS.has(s.kind)) err(w, `bad kind '${s.kind}'`);
    if (s.mission != null && !isQuest(s.mission)) err(w, `unknown mission '${s.mission}'`);
    const keys = s.cast || {};
    for (const [k, c] of Object.entries(keys)) if (!C.SPEAKERS.includes(c)) cast(`${w} cast ${k}`, c);
    let last = -1;
    for (const t of s.tracks || []) {
      if (!(t.t >= last)) err(w, `tracks out of order at t=${t.t}`); last = t.t;
      if (t.say && !(has(keys, t.say[0]) || C.SPEAKERS.includes(t.say[0]))) err(w, `unknown speaker '${t.say[0]}' at t=${t.t}`);
      if (t.panel && t.panel.say) for (const [who] of t.panel.say) if (!(has(keys, who) || C.SPEAKERS.includes(who))) err(w, `unknown panel speaker '${who}'`);
      if (t.boss && !has(C.BOSSES, t.boss)) err(w, `unknown boss '${t.boss}'`);
      if (t.if) cond(w, t.if);
      if (t.choice) { const m = s.mission && quests[s.mission]; if (m && !(m.choices || []).some((c) => c.id === t.choice)) err(w, `unknown choice '${t.choice}' in ${s.mission}`); }
      if (t.anim && !has(keys, t.anim[0])) err(w, `anim on unknown actor '${t.anim[0]}'`);
    }
  }

  // ---- bosses
  for (const [id, b] of Object.entries(C.BOSSES)) {
    const w = `boss ${id}`;
    cast(w, b.who);
    loc(w, b.zone);
    if (!Array.isArray(b.phases) || b.phases.length < 2) err(w, 'needs 2+ phases');
    if (b.core && !has(C.IMPLANTS, b.core)) err(w, `unknown core '${b.core}'`);
    for (const d of b.drops || []) if (!has(C.LEGENDARIES, d) && !has(C.LOOT_TABLES, d) && !has(C.ITEMS, d)) err(w, `unknown drop '${d}'`);
    if (b.quest && !isQuest(b.quest)) err(w, `unknown quest '${b.quest}'`);
    if (b.unlock) cond(w, b.unlock);
  }

  // ---- the fight layer (boss_fights.js): every fight has an arena, layers, weak points, a weakness, adds, a set piece,
  // a pinata, a dedicated loot table with at least one legendary, scaling, and a twist on every phase
  const HAZ = new Set(['water', 'lava', 'acid', 'oil', 'electric', 'fire', 'void', 'gas', 'rad', 'paper', 'crush']);
  const BARS = new Set(['armour', 'shield', 'health']);
  const ELEM = new Set(['fire', 'water', 'shock', 'frost', 'slip', 'verdict', 'explosive', 'knockback', 'blood', 'sleep', 'grapple']);
  const SETP = new Set(['chase', 'transform', 'grapple', 'vehicle', 'climb']);
  for (const [id, b] of Object.entries(C.BOSSES)) {
    const w = `boss ${id}`;
    const a = b.arena;
    if (!a || !a.name || !a.layout || !a.vertical) err(w, 'needs an arena { name, layout, vertical }');
    else {
      if (!Array.isArray(a.grapple) || !a.grapple.length) err(w, 'arena needs grapple points');
      if (!Array.isArray(a.hazards) || !a.hazards.length) err(w, 'arena needs hazards');
      for (const h of a.hazards || []) if (!HAZ.has(h.kind) || !h.where || !h.effect) err(w, `bad hazard ${JSON.stringify(h)}`);
      if (!Array.isArray(a.cover) || !a.cover.length) err(w, 'arena needs cover');
    }
    if (!Array.isArray(b.layers) || !b.layers.length) err(w, 'needs health layers'); else for (const l of b.layers) if (!BARS.has(l.bar) || !(l.of > 0) || !l.how) err(w, `bad layer ${JSON.stringify(l)}`);
    if (Array.isArray(b.layers) && b.layers.reduce((n, l) => n + (l.of || 0), 0) !== b.hp) err(w, `layers add up to ${b.layers.reduce((n, l) => n + (l.of || 0), 0)}, not hp ${b.hp}`);
    if (!Array.isArray(b.weakPoints) || !b.weakPoints.length) err(w, 'needs weak points'); else for (const p of b.weakPoints) if (!p.name || !p.glow || !p.exposedBy || !(p.crit > 1)) err(w, `bad weak point ${p.name}`);
    if (!b.weakness || !ELEM.has(b.weakness.element) || !b.weakness.why || !Array.isArray(b.weakness.weapons) || !b.weakness.weapons.length) err(w, 'needs a weakness { element, weapons, why }');
    else if (C.WEAPON_IDS) for (const x of b.weakness.weapons) if (!C.WEAPON_IDS.includes(x)) err(w, `weakness: unknown weapon '${x}'`);
    if (!Array.isArray(b.adds) || !b.adds.length) err(w, 'needs adds'); else for (const x of b.adds) if (!x.name || !x.personality || !x.does) err(w, `bad add ${x.name}`);
    if (!Array.isArray(b.setPiece) || !b.setPiece.length) err(w, 'needs a set piece'); else for (const x of b.setPiece) if (!SETP.has(x.kind) || !x.what) err(w, `bad set piece ${JSON.stringify(x)}`);
    for (const [i, p] of (b.phases || []).entries()) if (!p.twist) err(w, `phase ${i + 1} (${p.name}) has no twist`);
    for (const u of b.uses || []) if (!has(C.MECHANICS, u)) err(w, `unknown mechanic '${u}'`);
    if (!(b.uses || []).includes('grapple')) err(w, 'every boss fight uses the grapple');
    if (!b.pinata) err(w, 'needs a pinata');
    if (!b.scaling) err(w, 'needs refight scaling');
    if (!has(C.LOOT_TABLES, b.lootTable)) err(w, `unknown loot table '${b.lootTable}'`);
    else if (!C.LOOT_TABLES[b.lootTable].entries.some((e) => e.legendary)) err(w, `loot table '${b.lootTable}' has no dedicated legendary`);
  }

  // ---- mechanics: the bible, and the hooks on missions and side quests
  for (const [id, m] of Object.entries(C.MECHANICS || {})) {
    const w = `mechanic ${id}`;
    if (!m.name || !m.game || !m.story || !m.taught) err(w, 'needs name, game, story, taught');
    if (m.taught && !isQuest(m.taught.quest)) err(w, `taught in unknown quest '${m.taught.quest}'`);
    if (C.WEAPON_IDS) for (const x of m.weapons || []) if (!C.WEAPON_IDS.includes(x)) err(w, `unknown weapon '${x}'`);
  }
  for (const [id, q] of Object.entries(quests)) {
    if (q.kind === 'main' && !q.mechanic) err(`quest ${id}`, 'a main mission needs a mechanic hook');
    if (q.mechanic) { if (!q.mechanic.hook) err(`quest ${id}`, 'mechanic hook text missing'); for (const u of q.mechanic.uses || []) if (!has(C.MECHANICS, u)) err(`quest ${id}`, `unknown mechanic '${u}'`); }
  }

  // ---- implants
  for (const [id, i] of Object.entries(C.IMPLANTS)) {
    const w = `implant ${id}`;
    if (!SLOTS.has(i.slot)) err(w, `bad slot '${i.slot}'`);
    for (const k of ['name', 'perk', 'downside', 'look']) if (!i[k]) err(w, `missing ${k}`);
    if (i.boss && !has(C.BOSSES, i.boss)) err(w, `unknown boss '${i.boss}'`);
    if (i.secret) { loc(w, i.secret.where); if (!Array.isArray(i.secret.clues) || i.secret.clues.length < 2) err(w, 'a secret implant needs 2+ clues'); if (i.secret.quest && !isQuest(i.secret.quest)) err(w, `unknown quest '${i.secret.quest}'`); if (i.secret.if) cond(w, i.secret.if); }
  }

  // ---- loot
  for (const [id, l] of Object.entries(C.LEGENDARIES)) {
    const w = `legendary ${id}`;
    if (C.WEAPON_IDS && !C.WEAPON_IDS.includes(l.base)) err(w, `unknown base weapon '${l.base}'`);
    if (!has(C.BRANDS, l.brand)) err(w, `unknown brand '${l.brand}'`);
    if (!RARITIES.has(l.rarity)) err(w, `bad rarity '${l.rarity}'`);
    for (const k of ['name', 'quirk', 'lore', 'flavour']) if (!l[k]) err(w, `missing ${k}`);
    if (l.drop) { if (l.drop.boss && !has(C.BOSSES, l.drop.boss)) err(w, `unknown boss '${l.drop.boss}'`); if (l.drop.where) loc(w, l.drop.where); if (l.drop.quest && !isQuest(l.drop.quest)) err(w, `unknown quest '${l.drop.quest}'`); }
  }
  for (const [id, t] of Object.entries(C.LOOT_TABLES)) for (const e of t.entries || []) {
    if (e.legendary && !has(C.LEGENDARIES, e.legendary)) err(`loot table ${id}`, `unknown legendary '${e.legendary}'`);
    if (e.item && !has(C.ITEMS, e.item) && !has(C.IMPLANTS, e.item)) err(`loot table ${id}`, `unknown item '${e.item}'`);
    if (e.rarity && !RARITIES.has(e.rarity)) err(`loot table ${id}`, `bad rarity '${e.rarity}'`);
    if (e.base && C.WEAPON_IDS && !C.WEAPON_IDS.includes(e.base)) err(`loot table ${id}`, `unknown base '${e.base}'`);
  }
  for (const [id, m] of Object.entries(C.MODIFIERS || {})) if (!m.name || !m.effect) err(`modifier ${id}`, 'missing name/effect');

  // ---- collectibles
  for (const [id, c] of Object.entries(C.COLLECTIBLES)) {
    const w = `collectible ${id}`;
    if (!has(C.COLLECTIBLE_SETS, c.set)) err(w, `unknown set '${c.set}'`);
    loc(w, c.where);
    if (!c.text) err(w, 'missing text');
    if (c.if) cond(w, c.if);
    if (c.quest && !isQuest(c.quest)) err(w, `unknown quest '${c.quest}'`);
    acts(w, c.do);
  }

  // ---- activities
  for (const [id, a] of Object.entries(C.ACTIVITIES || {})) { (a.where || []).forEach((l) => loc(`activity ${id}`, l)); if (a.giver) cast(`activity ${id}`, a.giver); }

  // ---- endings
  for (const [id, e] of Object.entries(C.ENDING_SCRIPTS || {})) {
    if (!has(C.ENDINGS, id)) err(`ending ${id}`, 'not in world.js ENDINGS');
    for (const s of e.scenes || []) if (!has(C.SCENES, s)) err(`ending ${id}`, `unknown scene '${s}'`);
    for (const [d, by] of Object.entries(e.districts || {})) { if (!has(C.DISTRICTS, d)) err(`ending ${id}`, `unknown district '${d}'`); for (const f of Object.keys(by)) if (f !== 'any' && !has(C.FACTIONS, f)) err(`ending ${id} ${d}`, `unknown faction '${f}'`); }
    for (const p of e.panels || []) if (p.if) cond(`ending ${id}`, p.if);
  }

  // ---- grudges (the Grudge Ledger, docs/story/GRUDGES.md)
  if (C.GRUDGES) {
    const G = C.GRUDGES, W = C.WEAPON_IDS;
    for (const [k, v] of Object.entries(G.RULES)) if (!Number.isFinite(v) && typeof v !== 'boolean') err(`grudge rule ${k}`, 'must be a number or boolean');
    for (const [id, f] of Object.entries(G.FACTIONS)) {
      if (!f.name || !f.tag || !f.who || !f.voice) err(`grudge faction ${id}`, 'needs name, tag, who, voice');
      for (const d of f.districts || []) if (!has(C.DISTRICTS, d)) err(`grudge faction ${id}`, `unknown district '${d}'`);
      if (!(f.names || []).length) err(`grudge faction ${id}`, 'needs a name pool');
    }
    for (const [id, t] of Object.entries(G.TRIGGERS)) {
      if (!t.name || !t.when) err(`grudge trigger ${id}`, 'needs name and when');
      if (!has(G.ADAPTATIONS, t.adaptation)) err(`grudge trigger ${id}`, `unknown adaptation '${t.adaptation}'`);
      if (W) for (const w of t.weapons || []) if (!W.includes(w)) err(`grudge trigger ${id}`, `unknown weapon '${w}'`);
    }
    for (const [id, a] of Object.entries(G.ADAPTATIONS)) {
      if (!has(G.TRIGGERS, a.from)) err(`adaptation ${id}`, `unknown trigger '${a.from}'`);
      for (const k of ['name', 'title', 'look', 'effect', 'counter']) if (typeof a[k] !== 'string' || !a[k].trim()) err(`adaptation ${id}`, `missing ${k}`);
    }
    for (const [id, r] of Object.entries(G.RESOLUTIONS)) if (!r.name || !r.how || !r.result || !r.file) err(`grudge resolution ${id}`, 'needs name, how, result, file');
    const field = /\{(\w+)\}/g;
    for (const [id, r] of Object.entries(G.RECAPS)) for (const l of r.lines || []) for (const m of l.matchAll(field)) if (!G.RECAP_FIELDS.includes(m[1])) err(`recap ${id}`, `unknown field {${m[1]}}`);
    for (const f of Object.keys(G.FACTIONS)) for (const k of G.BARK_KEYS) {
      const ls = (G.BARKS[f] || {})[k] || [];
      if (ls.length < 4) err(`barks ${f}.${k}`, `${ls.length} lines (need 4)`);
      for (const l of ls) { if (typeof l !== 'string' || !l.trim()) err(`barks ${f}.${k}`, 'empty line'); for (const m of l.matchAll(field)) if (!['you', 'name', 'district'].includes(m[1])) err(`barks ${f}.${k}`, `unknown field {${m[1]}}`); }
    }
    for (const f of Object.keys(G.BARKS)) if (!has(G.FACTIONS, f)) err(`barks ${f}`, 'unknown grudge faction');
  }

  // ---- flags declared but never used (a typo catcher)
  for (const f of Object.keys(C.FLAGS)) if (!flagsUsed.has(f) && !(C.FLAGS[f] && C.FLAGS[f].engine)) err(`flag ${f}`, 'declared but never used');
  return errs;
}
