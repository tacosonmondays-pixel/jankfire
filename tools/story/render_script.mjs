// Renders the OVERDUE story data (shared/story/content) into the human-readable script in docs/story/script/.
// The data is the source of truth; the markdown is generated, so the two never drift apart.
//   node tools/story/render_script.mjs          writes docs/story/script/*.md
// tests/story/content.test.mjs checks the docs are up to date.
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const ACT_NAMES = { 1: 'Please Take Your Item', 2: 'Hostile Takeovers', 3: 'Off the Clock', 4: 'Quarterly Review', 5: 'Overdue' };
const ACT_Q = { 1: 'What am I?', 2: 'Who did this?', 3: 'What are they planning?', 4: 'Who do you stand with?', 5: 'What do you become?' };

export function render(C) {
  const name = (id) => (C.CAST[id] ? C.CAST[id].name : id === 'you' ? 'CHANGE' : id.toUpperCase());
  const loc = (id) => (C.LOCATIONS[id] ? `${C.LOCATIONS[id].name} (${C.DISTRICTS[C.LOCATIONS[id].district].name})` : id);
  const line = (l, def) => (l && typeof l === 'object' && !Array.isArray(l) ? line(l.who ? [l.who, l.t] : l.t, def) : Array.isArray(l) ? `**${name(l[0])}:** ${l[1]}` : l.startsWith('*') ? `_${l.replace(/^\*|\*$/g, '')}_` : `**${name(def)}:** ${l}`);

  function talk(t, id) {
    const out = [`#### Talk: \`${id}\` (with ${name(t.with)})`];
    for (const [nid, n] of Object.entries(t.nodes)) {
      out.push(`- **[${nid}]**${n.branch ? ` _branch: ${n.branch.map(([c, to]) => `${c || 'else'} → ${to}`).join('; ')}_` : ''}`);
      for (const l of n.say || []) out.push(`  - ${line(l, n.who || t.with)}`);
      for (const o of n.opts || []) out.push(`  - ➤ _"${o[0]}"_ → ${o[1]}${o[2] && o[2].if ? ` (if ${o[2].if})` : ''}${o[2] && o[2].do ? ` [${o[2].do.join(', ')}]` : ''}`);
      if (n.next) out.push(`  - → ${n.next}`);
      if (n.do) out.push(`  - _does: ${n.do.join(', ')}_`);
    }
    return out.join('\n');
  }
  function choices(list) {
    return (list || []).map((ch) => [`#### Choice: ${ch.prompt}${ch.if ? ` _(only if ${ch.if})_` : ''}`, ...ch.options.map((o) => `- **${o.label}**${o.if ? ` _(if ${o.if})_` : ''}: ${o.consequence}`)].join('\n')).join('\n\n');
  }
  function steps(list) { return (list || []).filter((s) => s.text || s.scene || s.boss).map((s, i) => `${i + 1}. ${s.text || (s.scene ? '_(scene)_' : '_(automatic)_')}${s.scene ? ` · scene \`${s.scene}\`` : ''}${s.boss ? ` · **boss: ${C.BOSSES[s.boss].name}**` : ''}${s.timer ? ` · timer ${s.timer}s` : ''}${s.if ? ` · if ${s.if}` : ''}`).join('\n'); }
  function scene(id) {
    const s = C.SCENES[id];
    const out = [`#### Scene: \`${id}\` (${s.kind}, ${s.len} s${s.music ? `, music: ${s.music}` : ''})`];
    for (const t of s.tracks) {
      const bits = [];
      if (t.title) bits.push(`**${t.title}**`);
      if (t.panel) bits.push(`[panel ${t.panel.n}]${t.panel.cap ? ` _${t.panel.cap}_` : ''}${(t.panel.say || []).map(([w, x]) => ` **${name(s.cast[w] || w)}:** ${x}`).join('')}${t.panel.sfx ? ` (${t.panel.sfx})` : ''}`);
      if (t.dir) bits.push(`_${t.dir}_`);
      if (t.say) bits.push(`**${name(s.cast[t.say[0]] || t.say[0])}:** ${t.say[1]}`);
      if (t.boss) bits.push(`→ BOSS INTRO: ${C.BOSSES[t.boss].card}`);
      if (t.choice) bits.push(`→ CHOICE: ${t.choice}`);
      out.push(`- \`${String(t.t).padStart(3)}\`${t.if ? ` _(if ${t.if})_` : ''} ${bits.join(' ')}`);
    }
    return out.join('\n');
  }
  function quest(id, q) {
    const out = [`### ${q.n ? `${q.n}. ` : ''}${q.title} \`${id}\``, `_${q.logline}_`, ''];
    out.push(`**Where:** ${(q.locations || []).map(loc).join(', ')}  `, `**Who:** ${(q.cast || []).map(name).join(', ')}  `, `**Giver:** ${q.giver ? name(q.giver) : '—'} · **Needs:** ${[...((q.requires && q.requires.missions) || []), (q.requires && q.requires.if) || ''].filter(Boolean).join(', ') || '—'}`);
    if (q.mechanic) out.push('', `**Mechanic hook:** ${q.mechanic.hook} _(uses: ${q.mechanic.uses.map((u) => C.MECHANICS[u].name.toLowerCase()).join(', ')})_`);
    if (q.twist) out.push('', `**The twist:** ${q.twist}`);
    if (q.beats) out.push('', '**Beats**', ...q.beats.map((b) => `- ${b}`));
    if (q.reveals) out.push('', '**The mystery**', `- _learn:_ ${q.reveals.learn.join(' ')}`, `- _suspect:_ ${q.reveals.suspect.join(' ') || '—'}`, `- _withheld:_ ${q.reveals.withheld.join(' ') || '—'}`);
    out.push('', '**Objectives**', steps(q.steps));
    for (const p of q.parts || []) out.push('', `**Part: ${p.title}** _(if ${p.if})_`, steps(p.steps));
    for (const s of q.scenes || []) out.push('', scene(s));
    for (const [tid, t] of Object.entries(q.talks || {})) out.push('', talk(t, tid));
    if (q.choices && q.choices.length) out.push('', choices(q.choices));
    const r = q.reward || {};
    out.push('', `**Reward:** ${[r.coupons ? `${r.coupons} coupons` : '', ...(r.items || []), ...(r.loot || []), ...(r.implants || [])].filter(Boolean).join(', ') || '—'}`);
    if (q.grade && q.grade.exceeds) out.push(`**Review card:** ${q.grade.exceeds} / ${q.grade.meets} / ${q.grade.see_me}`);
    if (q.notes) out.push(`_Builder notes: ${q.notes}_`);
    return out.join('\n');
  }

  const files = {};
  const words = (s) => s.split(/\s+/).filter(Boolean).length;
  // ---- cast
  {
    const out = ['# OVERDUE cast bible', '', '_Generated from `shared/story/content/cast_*.js`. Edit the data, then run `node tools/story/render_script.mjs`._', ''];
    for (const [id, c] of Object.entries(C.CAST)) {
      out.push(`## ${c.name} \`${id}\``, `**${c.title}**${c.full ? ` · ${c.full}` : ''}${c.age ? ` · ${c.age}` : ''} · ${c.role} · ${c.body}${c.home ? ` · ${loc(c.home)}` : ''}${c.met ? ` · met in \`${c.met}\`` : ''}`, '', c.look, '');
      out.push(`- **Wants:** ${c.wants}`, `- **Fears:** ${c.fears}`, `- **Secret:** ${c.secret}`, `- **Arc:** ${c.arc}`, `- **How they talk:** ${c.speech}`, '', '**Sample lines**', ...c.samples.map((s) => `> ${s}`), '');
      if (Object.keys(c.rel).length) out.push('**Relationships**', ...Object.entries(c.rel).map(([k, v]) => `- ${name(k)}: ${v}`), '');
      out.push('**Fate**', ...Object.entries(c.fate).map(([k, v]) => `- ${C.ENDINGS[k].name}: ${v}`), '');
    }
    files['CAST.md'] = out.join('\n');
  }
  // ---- acts
  for (const a of [1, 2, 3, 4, 5]) {
    const out = [`# Act ${a}: "${ACT_NAMES[a]}"`, `_${ACT_Q[a]}_`, '', '_Generated from `shared/story/content/missions/act' + a + '.js` and `scenes_act' + a + '.js`._', ''];
    for (const id of C.MISSION_ORDER.filter((m) => C.MISSIONS[m].act === a)) out.push(quest(id, C.MISSIONS[id]), '', '---', '');
    files[`ACT_${a}.md`] = out.join('\n');
  }
  // ---- endings
  {
    const out = ['# The endings', '', '_Generated from `endings.js` and `scenes_act5.js`._', ''];
    for (const [id, e] of Object.entries(C.ENDING_SCRIPTS)) {
      out.push(`## ${C.ENDINGS[id].name}${C.ENDINGS[id].canon ? '' : ' (non-canon)'}`, `_${C.ENDINGS[id].blurb}_`, '', `**Available:** ${e.needs || 'always'}`, '');
      for (const s of e.scenes) if (s !== 'credits_drive') out.push(scene(s), '');
      out.push('**Panels**', ...e.panels.map((p) => `- ${p.if ? `_(if ${p.if})_ ` : ''}${p.text}`), '');
      if (Object.keys(e.districts).length) { out.push('**District epilogues**'); for (const [d, by] of Object.entries(e.districts)) for (const [f, t] of Object.entries(by)) out.push(`- ${C.DISTRICTS[d].name}${f === 'any' ? '' : ` (${C.FACTIONS[f].name})`}: ${t}`); out.push(''); }
      out.push(`**Post-game:** ${e.postgame}`, '');
    }
    out.push(scene('credits_drive'), '');
    files['ENDINGS.md'] = out.join('\n');
  }
  // ---- bosses
  {
    const out = ['# Bosses', '', '_Generated from `bosses.js`. Who they are is in CAST.md._', ''];
    for (const [id, b] of Object.entries(C.BOSSES)) {
      out.push(`## ${b.card} \`${id}\``, `> "${b.subtitle}"`, '', `**${b.kind}** · ${loc(b.zone)} · quest \`${b.quest}\`${b.unlock ? ` · unlocks: ${b.unlock}` : ''} · HP ${b.hp} (+60% per extra co-op player)`, '', `**Look:** ${b.look}`, '', `**Why they're here:** ${b.why}`, '');
      const A = b.arena;
      out.push(`### Arena: ${A.name}`, A.layout, '', `- **Levels:** ${A.vertical}`, `- **Grapple:** ${A.grapple.join('; ')}`, `- **Hazards:** ${A.hazards.map((h) => `${h.kind} (${h.where}): ${h.effect}`).join('; ')}`, `- **Cover:** ${A.cover.map((c) => `${c.what} (${c.breaks})`).join('; ')}`, '');
      out.push(`**Bars:** ${b.layers.map((l) => `${l.bar} ${l.of} (${l.how})`).join(' → ')}`, '');
      out.push('**Weak points**', ...b.weakPoints.map((w) => `- **${w.name}** ×${w.crit}: ${w.glow}. Opened by: ${w.exposedBy}`), '');
      out.push(`**Weakness (${b.weakness.element}):** ${b.weakness.weapons.join(', ')}. ${b.weakness.why} (Beatable with anything.)`, '');
      out.push('**Adds**', ...b.adds.map((x) => `- **${x.name}** ×${x.count}: _${x.personality}_. ${x.does}`), '');
      out.push('**Set pieces**', ...b.setPiece.map((x) => `- **${x.kind}** (${x.when}): ${x.what}`), '');
      for (const p of b.phases) { out.push(`### Phase: ${p.name} (${p.hp[0]}% → ${p.hp[1]}%)`, `> "${p.line}"`, '', `**Twist:** ${p.twist}`, ''); for (const m of p.mechanics) out.push(`- **${m.name}** · tell: ${m.tell} · ${m.effect} · _counter:_ ${m.counter}`); out.push(''); }
      out.push('**Lines**', `- intro: "${b.lines.intro}"`, `- hurt: ${b.lines.hurt.map((x) => `"${x}"`).join(', ')}`, `- kills you: ${b.lines.kill.map((x) => `"${x}"`).join(', ')}`, `- low: "${b.lines.low}"`, `- defeat: "${b.lines.defeat}"`, '', `**Defeat:** ${b.defeat}`, '');
      if (b.core) { const i = C.IMPLANTS[b.core]; out.push(`**Organ core: ${i.name}** (${i.slot}): ${i.perk}. _Downside:_ ${i.downside}.`, ''); }
      if (b.refight) out.push(`**Refight (${b.refight.card}):** "${b.refight.line}" Mods: ${b.refight.mods.join('; ')}.`, '');
      out.push(`**Piñata:** ${b.pinata}`, '', `**Loot table:** \`${b.lootTable}\` (${C.LOOT_TABLES[b.lootTable].entries.filter((e) => e.legendary).map((e) => C.LEGENDARIES[e.legendary].name).join(', ')}) · **Refights:** ${b.scaling}`, '');
      out.push(`**Drops:** ${b.drops.map((d) => (C.LEGENDARIES[d] ? C.LEGENDARIES[d].name : d)).join(', ')}`, '', '---', '');
    }
    files['BOSSES.md'] = out.join('\n');
  }
  // ---- side content
  {
    const out = ['# Side questlines and activities', '', '_Generated from `side/*.js` and `activities.js`._', ''];
    for (const d of Object.keys(C.DISTRICTS)) {
      const qs = Object.entries(C.SIDE).filter(([, q]) => q.district === d);
      if (!qs.length) continue;
      out.push(`## ${C.DISTRICTS[d].name}`, '');
      for (const [id, q] of qs) out.push(quest(id, q), '', '---', '');
    }
    out.push('## Repeatable activities', '');
    for (const [id, a] of Object.entries(C.ACTIVITIES)) out.push(`### ${a.name} \`${id}\``, `${a.desc}`, '', `_${a.repeat} · from Act ${a.unlock} · ${a.where.map(loc).join(', ')}_  `, `**Pays:** ${a.reward} · _"${a.voice[0]}"_`, '');
    files['SIDE_QUESTS.md'] = out.join('\n');
  }
  // ---- implants + secrets
  {
    const out = ['# Bio-implants, organ cores and secret bio upgrades', '', '_Generated from `implants.js`. The Drift rules are at the top of that file._', ''];
    for (const kind of ['shop', 'core', 'inheritance', 'secret']) {
      out.push(`## ${{ shop: 'Shop implants', core: 'Organ cores', inheritance: 'Inheritances (parts from friends)', secret: 'Secret bio upgrades' }[kind]}`, '');
      for (const [id, i] of Object.entries(C.IMPLANTS).filter(([, x]) => x.kind === kind)) {
        out.push(`### ${i.name} \`${id}\` (${i.slot})`, `_${i.text}_`, '', `- **Perk:** ${i.perk}`, `- **Downside:** ${i.downside}`, `- **Look:** ${i.look}`);
        if (i.cost) out.push(`- **Cost:** ${i.cost} coupons`);
        if (i.boss) out.push(`- **From:** ${C.BOSSES[i.boss].name} (\`${i.boss}\`)`);
        if (i.drift) out.push(`- **Drift:** ${i.drift > 0 ? '+' : ''}${i.drift} permanent`);
        if (i.secret) out.push(`- **Where:** ${loc(i.secret.where)}${i.secret.quest ? ` (after \`${i.secret.quest}\`)` : ''}${i.secret.if ? ` · needs ${i.secret.if}` : ''}`, `- **How:** ${i.secret.how}`, '- **The clue trail:**', ...i.secret.clues.map((c, n) => `  ${n + 1}. ${c}`));
        out.push('');
      }
    }
    files['IMPLANTS.md'] = out.join('\n');
  }
  // ---- loot
  {
    const out = ['# Loot', '', '_Generated from `loot.js`. No durability, ever._', '', '## Brands', ''];
    for (const [id, b] of Object.entries(C.BRANDS)) out.push(`- **${b.name}** \`${id}\`: _"${b.flavour}"_ ${b.rule}. Look: ${b.look}.`);
    out.push('', '## Modifiers', '', ...Object.entries(C.MODIFIERS).map(([id, m]) => `- **${m.name}** \`${id}\`: ${m.effect}`), '', '## Named legendaries', '');
    for (const [id, l] of Object.entries(C.LEGENDARIES)) {
      const d = l.drop || {};
      out.push(`### ${l.name} \`${id}\`${l.rarity === 'premium' ? ' (☺ PREMIUM)' : ''}`, `> "${l.flavour}"`, '', `**${l.base}** · ${C.BRANDS[l.brand].name}  `, `**Quirk:** ${l.quirk}  `, `**Lore:** ${l.lore}  `, `**Drops:** ${d.boss ? `boss ${C.BOSSES[d.boss].name}` : d.quest ? `quest \`${d.quest}\`` : d.where ? loc(d.where) : '—'}${d.farm ? ' (farmable)' : ''}${d.note ? ` · ${d.note}` : ''}`, '');
    }
    files['LOOT.md'] = out.join('\n');
  }
  // ---- collectibles
  {
    const out = ['# Collectibles', '', '_Generated from `collectibles.js`._', ''];
    for (const [sid, s] of Object.entries(C.COLLECTIBLE_SETS)) {
      out.push(`## ${s.name}`, `_${s.desc}_ **Set reward:** ${s.reward}`, '');
      for (const [id, c] of Object.entries(C.COLLECTIBLES).filter(([, x]) => x.set === sid)) out.push(`- **${c.name}** \`${id}\` · ${loc(c.where)} · _${c.how}_  `, `  ${c.text}`);
      out.push('');
    }
    files['COLLECTIBLES.md'] = out.join('\n');
  }
  // ---- mechanics (docs/story/MECHANICS.md)
  {
    const QS = { ...C.MISSIONS, ...C.SIDE };
    const usedBy = (id, kind) => Object.entries(QS).filter(([, q]) => (kind === 'main' ? q.kind !== 'side' : q.kind === 'side') && q.mechanic && q.mechanic.uses.includes(id)).map(([qid]) => qid);
    const bossBy = (m, id) => Object.entries(C.BOSSES).filter(([, b]) => b.uses.includes(id) || m.weapons.some((w) => b.weakness.weapons.includes(w))).map(([bid]) => bid);
    const out = ['# OVERDUE mechanics bible', '', '_Generated from `shared/story/content/mechanics.js`, the `mechanic` hooks on every mission and side quest, and the boss fight layer (`boss_fights.js`). Edit the data, then run `node tools/story/render_script.mjs`._', '',
      'Everything here is a mechanic the game already has (the `src` column says where). The story is built to use all of it, and it teaches each one in a mission or side quest, usually with a joke. The grapple is the star: every district has a swing route, and every boss arena has grapple points.', '',
      '## Coverage', '', '| mechanic | kind | taught in | main missions | side quests | boss fights |', '|---|---|---|---|---|---|'];
    for (const [id, m] of Object.entries(C.MECHANICS)) out.push(`| ${m.name} | ${m.kind} | ${QS[m.taught.quest].title} | ${usedBy(id, 'main').length} | ${usedBy(id, 'side').length} | ${bossBy(m, id).length} |`);
    out.push('', '## The grapple', '', C.MECHANICS.grapple.game, '', '### Swing routes (one per district)', ...Object.entries(C.GRAPPLE.routes).map(([d, r]) => `- **${C.DISTRICTS[d].name}:** ${r}`), '',
      '### Shortcuts', ...C.GRAPPLE.shortcuts.map((x) => `- ${x}`), '', '### Secrets', ...C.GRAPPLE.secrets.map((x) => `- ${x}`), '', '### Chases', ...C.GRAPPLE.chases.map((x) => `- ${x}`), '',
      '### Swinging fights', ...C.GRAPPLE.fights.map((x) => `- ${x}`), '', '### Grapple puzzles', ...C.GRAPPLE.puzzles.map((x) => `- ${x}`), '', '### Races', C.GRAPPLE.races, '', '### Upgrades', ...C.GRAPPLE.upgrades.map((x) => `- ${x}`), '',
      '### Grapple points in every boss arena', ...Object.entries(C.BOSSES).map(([id, b]) => `- **${b.name}** (${b.arena.name}): ${b.arena.grapple.join('; ')}`), '', '## Every mechanic', '');
    for (const [id, m] of Object.entries(C.MECHANICS)) {
      out.push(`### ${m.name} \`${id}\``, `_${m.kind} · ${m.src}${m.weapons.length ? ` · weapons: ${m.weapons.join(', ')}` : ''}_`, '', m.game, '');
      for (const [k, v] of Object.entries(m.story)) out.push(`- **${k}:** ${v}`);
      out.push(`- **taught:** ${QS[m.taught.quest].title} (\`${m.taught.quest}\`): ${m.taught.how}`);
      const mm = usedBy(id, 'main'), ss = usedBy(id, 'side');
      if (mm.length) out.push(`- **main missions:** ${mm.map((q) => QS[q].title).join(', ')}`);
      if (ss.length) out.push(`- **side quests:** ${ss.map((q) => QS[q].title).join(', ')}`);
      const bb = bossBy(m, id);
      if (bb.length) out.push(`- **boss fights:** ${bb.map((b) => C.BOSSES[b].name).join(', ')}`);
      out.push('');
    }
    out.push('## Every mission\'s mechanic hook', '', '| mission | uses | hook |', '|---|---|---|');
    for (const [qid, q] of Object.entries(QS)) if (q.mechanic) out.push(`| ${q.title} | ${q.mechanic.uses.join(', ')} | ${q.mechanic.hook} |`);
    out.push('', '## Boss weaknesses', '', '| boss | element | weapons that shine | weak points |', '|---|---|---|---|');
    for (const [id, b] of Object.entries(C.BOSSES)) out.push(`| ${b.card} | ${b.weakness.element} | ${b.weakness.weapons.join(', ')} | ${b.weakPoints.map((w) => w.name).join(', ')} |`);
    files['../MECHANICS.md'] = out.join('\n') + '\n';
  }
  // ---- grudges (docs/story/GRUDGE_LEDGER.md; the rules are hand-written in docs/story/GRUDGES.md)
  if (C.GRUDGES) {
    const G = C.GRUDGES;
    const out = ['# OVERDUE: the Grudge Ledger catalogue', '', '_Generated from `shared/story/content/grudges.js`. Edit the data, then run `node tools/story/render_script.mjs`. The rules, the save schema, why it is its own design and the example stories are in [GRUDGES.md](GRUDGES.md)._', '',
      '## Rules (numbers)', '', '| rule | value |', '|---|---|', ...Object.entries(G.RULES).map(([k, v]) => `| ${k} | ${v} |`), '',
      '## Who can open a file', '', '| faction | file tag | who | where | voice |', '|---|---|---|---|---|',
      ...Object.values(G.FACTIONS).map((f) => `| ${f.name} | ${f.tag} | ${f.who} | ${f.districts.map((d) => C.DISTRICTS[d].name).join(', ')} | ${f.voice} |`), '',
      '## Triggers', '', '| trigger | when | opens a file? | gives |', '|---|---|---|---|',
      ...Object.entries(G.TRIGGERS).map(([id, t]) => `| **${t.name}** \`${id}\` | ${t.when}${t.weapons ? ` (${t.weapons.join(', ')})` : ''} | ${t.opens ? 'yes' : 'only adds to an open file'} | ${G.ADAPTATIONS[t.adaptation].name} |`), '',
      `## Adaptations (${Object.keys(G.ADAPTATIONS).length})`, '', 'Each one is a thing you can see on the model, changes one behaviour, and has one counter-trick.', '', '| adaptation | after | looks like | what it changes | the counter |', '|---|---|---|---|---|',
      ...Object.values(G.ADAPTATIONS).map((a) => `| **${a.name}** ("${a.title}") | ${G.TRIGGERS[a.from].name} | ${a.look} | ${a.effect} | ${a.counter} |`), '',
      '## Resolutions', '', '| ending | how | what happens | file stamp |', '|---|---|---|---|', ...Object.values(G.RESOLUTIONS).map((r) => `| **${r.name}** | ${r.how} | ${r.result} | ${r.file} |`), '',
      '## Recap cards', '', `Fields: ${G.RECAP_FIELDS.map((f) => `\`{${f}}\``).join(', ')}.`, ''];
    for (const [id, r] of Object.entries(G.RECAPS)) out.push(`### ${r.title} \`${id}\``, `_${r.when}_`, '', ...r.lines.map((l) => `> ${l}  `), '');
    let n = 0; for (const f of Object.values(G.BARKS)) for (const ls of Object.values(f)) n += ls.length;
    out.push(`## Barks (${n} lines)`, '', '`{you}` is your name on the file, `{name}` theirs, `{district}` where it happened.', '');
    for (const [fid, f] of Object.entries(G.BARKS)) {
      out.push(`### ${G.FACTIONS[fid].name}`, '');
      for (const k of G.BARK_KEYS) out.push(`- **${k}:** ${f[k].map((l) => `"${l}"`).join(' · ')}`);
      out.push('');
    }
    files['../GRUDGE_LEDGER.md'] = out.join('\n');
  }
  // ---- index
  {
    const total = Object.values(files).reduce((n, t) => n + words(t), 0);
    const ms = C.MISSION_ORDER.map((id) => C.MISSIONS[id]);
    const out = ['# JANKFIRE: OVERDUE: the script', '',
      'The complete story script, generated from the data the game loads (`shared/story/content/`). The data is the source of truth: edit it, then run `node tools/story/render_script.mjs`. `node --test tests/story/content.test.mjs` checks every reference resolves and that these docs are up to date.', '',
      'Start with [CANON.md](CANON.md): the timeline, why Change is free, the six pages, the reveal order.', '',
      '| file | what | size |', '|---|---|---|',
      `| [CAST.md](CAST.md) | the cast bible: ${Object.keys(C.CAST).length} characters | ${words(files['CAST.md'])} words |`,
      ...[1, 2, 3, 4, 5].map((a) => `| [ACT_${a}.md](ACT_${a}.md) | Act ${a}: "${ACT_NAMES[a]}": ${ms.filter((m) => m.act === a).length} missions | ${words(files[`ACT_${a}.md`])} words |`),
      `| [ENDINGS.md](ENDINGS.md) | ON TIME, LATE, OFF THE BOOKS, NAP TIME | ${words(files['ENDINGS.md'])} words |`,
      `| [BOSSES.md](BOSSES.md) | ${Object.keys(C.BOSSES).length} fights, ${new Set(Object.values(C.BOSSES).map((b) => b.who)).size} named bosses | ${words(files['BOSSES.md'])} words |`,
      `| [SIDE_QUESTS.md](SIDE_QUESTS.md) | ${Object.keys(C.SIDE).length} side questlines, ${Object.keys(C.ACTIVITIES).length} activities | ${words(files['SIDE_QUESTS.md'])} words |`,
      `| [IMPLANTS.md](IMPLANTS.md) | ${Object.keys(C.IMPLANTS).length} implants (${Object.values(C.IMPLANTS).filter((i) => i.kind === 'secret').length} secret) and the Drift rules | ${words(files['IMPLANTS.md'])} words |`,
      `| [LOOT.md](LOOT.md) | ${Object.keys(C.BRANDS).length} brands, ${Object.keys(C.LEGENDARIES).length} named legendaries | ${words(files['LOOT.md'])} words |`,
      `| [../MECHANICS.md](../MECHANICS.md) | the mechanics bible: ${Object.keys(C.MECHANICS).length} mechanics, the grapple, coverage | ${words(files['../MECHANICS.md'])} words |`,
      ...(C.GRUDGES ? [`| [../GRUDGES.md](../GRUDGES.md) · [../GRUDGE_LEDGER.md](../GRUDGE_LEDGER.md) | the Grudge Ledger: enemies who remember you, ${Object.keys(C.GRUDGES.ADAPTATIONS).length} adaptations | ${words(files['../GRUDGE_LEDGER.md'])} words |`] : []),
      `| [COLLECTIBLES.md](COLLECTIBLES.md) | ${Object.keys(C.COLLECTIBLES).length} collectibles in ${Object.keys(C.COLLECTIBLE_SETS).length} sets | ${words(files['COLLECTIBLES.md'])} words |`,
      '', `**Total: about ${Math.round(total / 1000)}k words, ${ms.length} main missions, ${Object.keys(C.SCENES).length} scenes.**`, '',
      '## Main story at a glance', '', '| # | act | mission | logline |', '|---|---|---|---|',
      ...C.MISSION_ORDER.map((id) => `| ${C.MISSIONS[id].n} | ${C.MISSIONS[id].act} | ${C.MISSIONS[id].title} | ${C.MISSIONS[id].logline} |`), ''];
    files['README.md'] = out.join('\n');
  }
  return files;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const { CONTENT } = await import('../../shared/story/content/index.js');
  const dir = new URL('../../docs/story/script/', import.meta.url);
  mkdirSync(dir, { recursive: true });
  const files = render(CONTENT);
  for (const [f, t] of Object.entries(files)) writeFileSync(new URL(f, dir), t);
  console.log(Object.keys(files).join(', '));
}
