// End of match: big VICTORY / DEFEAT, "next round in", the two-stage vote (mode first, then map) as big cards,
// and tabs: Leaderboard / Performance / Medals / Rewards. Shrinks to a side rail while the play of the round runs.
// Server side: Room.startVote / tickVote / advanceVote in server.js, rules in shared/vote.js, medals in server/match.js.
import { G } from './ctx.js';
import { net } from './net.js';
import { sfx } from './audio.js';
import { GAMES, TEAMS } from '/shared/modes.js';
import { MAPS } from '/shared/map.js';
import { MEDALS } from '/shared/medals.js';
import { CONTAINERS } from '/shared/cosmetics.js';
import { modeThumb, modeColors, medalImage, propImage } from './modeart.js';
import { fleshFrame } from './flesh.js';

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const pad2 = (n) => String(Math.max(0, n)).padStart(2, '0');
const clock = (ms) => { const s = Math.ceil(Math.max(0, ms) / 1000); return `${pad2(Math.floor(s / 60))}:${pad2(s % 60)}`; };
const pick = (a) => a[Math.floor(Math.random() * a.length)];

const LINES = {
  win: ['quarterly kill targets: exceeded.', 'you have been promoted to slightly less disposable.', 'the shareholders are pleased. for now.', 'a bonus of $0.00 has been wired to your account.', 'management will take credit for this.'],
  lose: ['your organs have been leased.', 'performance review: scheduled.', 'please return the weapon to the front desk.', 'the board is disappointed in you.', 'your contract has been renewed. unfortunately.', 'skill issue (corporate).'],
  draw: ['nobody wins. legal says that is fine.', 'a tie. HR is drafting a memo.', 'everyone gets a participation lanyard.'],
};
const TABS = [['board', 'LEADERBOARD'], ['perf', 'PERFORMANCE'], ['medals', 'MEDALS'], ['rewards', 'REWARDS']];
const ES = { open: false, mini: false, vote: null, my: -1, myStage: '', perf: null, round: null, tab: 'board', totalEnd: 0, stageEnd: 0, stageLen: 1, roll: null, achs: [], raf: 0, lastSec: -1, opts: {} };
export const endscreen = ES;

// ---------------------------------------------------------------- dom
let root, frameEl;
export function initEndscreen(opts = {}) {
  ES.opts = opts; // { note(id, roundMsg), unlock(), lock(), level(xp) }
  root = el('div', 'hidden'); root.id = 'endscreen';
  root.innerHTML = `
    <div class="es-back"></div>
    <div class="es-frame"></div>
    <div class="es-top">
      <div class="es-chip" id="esWhere"></div>
      <div class="es-timer"><small>NEXT ROUND IN</small><b id="esClock">00:00</b></div>
    </div>
    <div class="es-head">
      <div class="es-title" id="esTitle"></div>
      <div class="es-sub" id="esSub"></div>
    </div>
    <div class="es-vote">
      <div class="es-steps" id="esSteps">
        <span data-s="mode"><b>1</b> PICK A MODE</span><i></i><span data-s="map"><b>2</b> PICK A MAP</span><i></i><span data-s="done"><b>3</b> DROP IN</span>
      </div>
      <div class="es-stagebar"><i id="esBar"></i></div>
      <div class="es-cards" id="esCards"></div>
      <div class="es-vhint" id="esHint"></div>
    </div>
    <div class="es-tabs">
      <div class="es-tabbar" id="esTabbar"></div>
      <div class="es-tabbody" id="esBody"></div>
    </div>`;
  $('hud').append(root);
  frameEl = root.querySelector('.es-frame');
  const bar = $('esTabbar');
  for (const [id, label] of TABS) {
    const b = el('button', 'es-tab', label);
    b.dataset.tab = id;
    b.addEventListener('click', () => { setTab(id); sfx.click(); });
    bar.append(b);
  }
  const click = el('div', 'hidden', 'CLICK TO DROP IN'); click.id = 'esClick';
  $('hud').append(click);
  addEventListener('resize', () => { if (ES.open) drawFrame(); });
  net.on('perf', (m) => {
    ES.lv = ES.opts.level && ES.opts.level(); // before this match's xp lands
    if (m.acct && ES.opts.gotXp) ES.opts.gotXp(m.xp);
    ES.perf = m; if (ES.open) { if (ES.tab === 'board' && !ES.tabPicked) ES.tab = 'perf'; renderTab(); renderTitle(); } });
}
function drawFrame() { frameEl.innerHTML = fleshFrame(innerWidth, innerHeight); }

// ---------------------------------------------------------------- open / close
// round over (server 'round' message with over: 1)
export function esRound(m) {
  ES.round = m; ES.roll = null; ES.perf = null;
  ES.tabPicked = false; ES.tab = 'board';
  ES.totalEnd = performance.now() + (m.next || 0);
  ES.line = pick(LINES[result()]);
  open();
}
function open() {
  if (!root) return;
  const was = ES.open;
  ES.open = true;
  root.classList.remove('hidden');
  $('hud').classList.add('es-open');
  $('esClick').classList.add('hidden');
  if (!was) {
    drawFrame();
    root.classList.remove('slam'); void root.offsetWidth; root.classList.add('slam');
    const r = result();
    setTimeout(() => { if (!ES.open) return; if (r === 'win') sfx.rankUp(); else if (r === 'lose') sfx.sad(); else sfx.gavel(); }, 140);
  }
  if (!ES.mini && ES.opts.unlock) ES.opts.unlock();
  renderAll();
  if (!ES.raf) ES.raf = requestAnimationFrame(tick);
}
export function esClose(prompt) {
  ES.achs = []; // a new match: achievements from here on count for its end screen
  ES.open = false; ES.mini = false; ES.vote = null; ES.my = -1; ES.myStage = '';
  ES.round = null; ES.perf = null; ES.roll = null; ES.lv = null; ES.line = ''; ES.lineFor = ''; ES.tab = 'board'; ES.tabPicked = false; // forget this match
  if (!root) return;
  root.classList.add('hidden'); root.classList.remove('mini');
  $('hud').classList.remove('es-open');
  $('esClick').classList.toggle('hidden', !prompt);
}
export function esHideClick() { const c = $('esClick'); if (c) c.classList.add('hidden'); }
export function esClickShown() { const c = $('esClick'); return !!c && !c.classList.contains('hidden'); }
// the play of the round is on: shrink to a side rail so the clip is watchable and you can still vote
export function esMini(on) {
  ES.mini = !!on;
  if (!root) return;
  root.classList.toggle('mini', ES.mini);
  if (!ES.mini && ES.open && ES.opts.unlock) ES.opts.unlock();
  renderCards();
}
export const esActive = () => ES.open;
export const esFull = () => ES.open && !ES.mini;

// ---------------------------------------------------------------- vote
export function esVote(v) {
  if (!v) return;
  const stageChanged = !ES.vote || ES.vote.stage !== v.stage;
  ES.vote = v;
  if (stageChanged) { ES.my = -1; ES.myStage = v.stage; }
  ES.stageEnd = performance.now() + (v.left || 0);
  ES.stageLen = Math.max(1, v.left || 1);
  if (v.total) ES.totalEnd = performance.now() + v.total;
  if (!ES.open) { // joined mid-vote: no result of yours to show, just the vote
    ES.round = { pending: 1 }; ES.perf = null; ES.roll = null;
    open();
  }
  if (stageChanged && ES.open && !(ES.round && ES.round.pending && v.stage === 'mode')) { if (v.stage === 'done') sfx.gavel(); else if (v.stage === 'map') sfx.slam(); }
  renderVote(stageChanged);
}
export function esVotes(m) {
  if (!ES.vote || (m.stage && m.stage !== ES.vote.stage)) return;
  ES.vote.counts = m.counts; ES.vote.bots = m.bots;
  if (m.left != null) ES.stageEnd = performance.now() + m.left;
  if (m.total) ES.totalEnd = performance.now() + m.total;
  renderCards(true);
}
export function esCast(i) {
  const v = ES.vote;
  if (!v || v.stage === 'done' || i < 0 || i >= v.options.length || i === ES.my) return false;
  ES.my = i;
  net.send({ t: 'vote', i, s: v.stage }); // the stage too: a late mode pick must not land on the map with the same number
  sfx.pop();
  renderCards(true);
  const c = $('esCards').children[i];
  if (c) { c.classList.remove('squish'); void c.offsetWidth; c.classList.add('squish'); }
  return true;
}
// keys while the end screen is up: 1-4 vote, arrows switch tabs. returns true when it used the key
export function esKey(e) {
  if (!ES.open) return false;
  const d = /^(Digit|Numpad)([1-9])$/.exec(e.code);
  if (d && ES.vote && ES.vote.stage !== 'done') { if (!e.repeat) esCast(Number(d[2]) - 1); return true; }
  if (!ES.mini && (e.code === 'ArrowLeft' || e.code === 'ArrowRight')) {
    const i = TABS.findIndex(([id]) => id === ES.tab), j = (i + (e.code === 'ArrowLeft' ? TABS.length - 1 : 1)) % TABS.length;
    setTab(TABS[j][0]); sfx.click(); return true;
  }
  return false;
}
export function esRoll(m) { ES.roll = m; if (ES.open) renderTab(); }
export function esAch(a) { ES.achs.push({ ...a, at: performance.now() }); if (ES.open) renderTab(); }

// ---------------------------------------------------------------- render
function result() {
  const m = ES.round;
  if (!m || m.pending) return 'none';
  if (ES.perf && ES.perf.won) return 'win';
  if (m.game === 'inf' && G.infSide) return (G.infSide === 'inf') === !!G.zombie ? 'win' : 'lose'; // infection: your side won or it didn't
  const teams = !!m.sc;
  if (teams) return !m.winTeam ? 'draw' : m.winTeam === G.myTeam ? 'win' : 'lose';
  return !m.winner ? 'draw' : m.winner === G.myId ? 'win' : 'lose';
}
function renderAll() { renderWhere(); renderTitle(); renderVote(true); renderTabbar(); renderTab(); }
function renderWhere() {
  const g = (ES.round && ES.round.game) || (G.round && G.round.game) || 'dm';
  $('esWhere').textContent = `${GAMES[g] ? GAMES[g].name : g} · ${MAPS[G.cfg.map] ? MAPS[G.cfg.map].name : ''}`;
}
function renderTitle() {
  const t = $('esTitle'), r = result();
  const word = r === 'win' ? 'VICTORY' : r === 'lose' ? 'DEFEAT' : r === 'draw' ? 'DRAW' : 'NEXT MATCH';
  if (ES.lineFor !== r && LINES[r]) { ES.line = pick(LINES[r]); ES.lineFor = r; } // the deadpan line matches the result
  renderSub(r);
  if (t.dataset.word === word) return;
  t.dataset.word = word;
  t.className = `es-title r-${r}`;
  t.innerHTML = '';
  const prop = (flip) => { // 3d, rendered from boxes (no webgl for it: no prop)
    const i = el('span', 'es-ico' + (flip ? ' flip' : '')), url = propImage(r === 'win' ? 'win' : r === 'draw' ? 'draw' : 'lose', flip);
    if (url) { const img = new Image(); img.alt = ''; img.src = url; i.append(img); }
    return i;
  };
  const ico = prop(false);
  const w = el('b', 'es-word');
  [...word].forEach((ch, i) => { const s = el('span', null, ch); s.style.setProperty('--i', i); w.append(s); });
  t.append(ico, w);
  if (r !== 'none') t.append(prop(true)); else ico.remove();
}
function renderSub(r) {
  const m = ES.round || {};
  let sub = ES.line || '';
  if (m.sc) sub = `${TEAMS[1].name} ${m.sc[0]} - ${m.sc[1]} ${TEAMS[2].name} · ${sub}`;
  else if (m.winner && m.winner !== G.myId) { const n = G.names.get(m.winner); if (n) sub = `${n.name} took it · ${sub}`; }
  if (r === 'none') sub = 'the vote is on. pick something.';
  if (ES.opts.title) { const x = ES.opts.title(m); if (x) sub = `${x} · ${sub}`; }
  $('esSub').textContent = sub;
}
function renderVote(stageChanged) {
  const v = ES.vote;
  const steps = $('esSteps');
  const order = ['mode', 'map', 'done'];
  const at = v ? order.indexOf(v.stage) : -1;
  for (const s of steps.querySelectorAll('span')) {
    const i = order.indexOf(s.dataset.s);
    s.classList.toggle('on', i === at); s.classList.toggle('past', i < at);
  }
  // the locked-in mode shows on step 1 once it's decided
  const s1 = steps.querySelector('[data-s="mode"]');
  s1.lastChild.textContent = v && v.gameName ? ` ${v.gameName.toUpperCase()}` : ' PICK A MODE';
  const s2 = steps.querySelector('[data-s="map"]');
  s2.lastChild.textContent = v && v.mapName ? ` ${v.mapName.toUpperCase()}` : ' PICK A MAP';
  $('esHint').textContent = !v ? 'waiting for the vote...' : v.stage === 'done' ? 'locked in. get ready.' : `click a card or press 1-${v.options.length} · humans decide, bots only break ties`;
  renderCards(false, stageChanged);
}
function renderCards(countsOnly, stageChanged) {
  const box = $('esCards'), v = ES.vote;
  if (!box) return;
  if (!v) { box.innerHTML = ''; return; }
  if (v.stage === 'done') { if (!countsOnly) renderDone(box, v); return; }
  const n = v.options.length, h = v.counts || [], b = v.bots || [];
  const tot = h.map((x, i) => x + (b[i] || 0));
  const lead = Math.max(...h.map((x, i) => x * 100 + (b[i] || 0)));
  if (!countsOnly || box.children.length !== n || box.dataset.stage !== v.stage) {
    box.innerHTML = ''; box.dataset.stage = v.stage;
    box.classList.toggle('deal', !!stageChanged); void box.offsetWidth;
    v.options.forEach((o, i) => box.append(card(o, i)));
  }
  [...box.children].forEach((c, i) => {
    c.classList.toggle('mine', i === ES.my);
    c.classList.toggle('lead', lead > 0 && h[i] * 100 + (b[i] || 0) === lead);
    c.querySelector('.cnt').textContent = String(tot[i] || 0);
    const pips = c.querySelector('.pips');
    pips.innerHTML = '';
    for (let k = 0; k < Math.min(12, h[i] || 0); k++) pips.append(el('i', 'h'));
    for (let k = 0; k < Math.min(12, b[i] || 0); k++) pips.append(el('i', 'b'));
    c.querySelector('.who').textContent = (h[i] || 0) + (b[i] || 0) ? `${h[i] || 0} human${h[i] === 1 ? '' : 's'} · ${b[i] || 0} bot${b[i] === 1 ? '' : 's'}` : 'no votes yet';
  });
}
function mapThumb(id) {
  const d = el('div', 'mapthumb');
  const img = new Image();
  img.alt = ''; img.decoding = 'async'; img.loading = 'eager';
  img.onerror = () => { img.remove(); d.classList.add('nothumb'); d.append(el('b', null, (MAPS[id] && MAPS[id].name) || id)); };
  img.src = `/thumbs/${id}.jpg`;
  d.append(img);
  return d;
}
function card(o, i) {
  const c = el('button', 'es-card' + (o.event ? ' event' : ''));
  c.style.setProperty('--i', i);
  if (o.game) { const [a, b] = modeColors(o.game); c.style.setProperty('--ca', a); c.style.setProperty('--cb', b); }
  c.append(el('span', 'key', String(i + 1)));
  if (o.event) c.append(el('span', 'tag', 'EVENT'));
  c.append(o.game ? modeThumb(o.game, o.name) : mapThumb(o.map));
  const info = el('div', 'info');
  info.append(el('b', 'nm', o.game ? o.name : o.mapName));
  const vgame = ES.vote && ES.vote.gameName;
  info.append(el('span', 'sub', o.game ? (o.teams ? 'TEAMS' : 'FREE FOR ALL') : `${(o.size || '').toUpperCase()} · ${vgame || ''}`));
  const desc = o.game && GAMES[o.game] ? GAMES[o.game].desc : '';
  if (desc) info.append(el('span', 'desc', desc));
  c.append(info);
  const foot = el('div', 'foot');
  foot.append(el('span', 'pips'), el('b', 'cnt', '0'));
  c.append(foot, el('span', 'who'), el('span', 'stamp', 'YOUR VOTE'));
  c.title = desc;
  c.addEventListener('click', (e) => { e.stopPropagation(); esCast(i); });
  return c;
}
function renderDone(box, v) {
  box.innerHTML = ''; box.dataset.stage = 'done';
  const c = el('div', 'es-next');
  c.append(modeThumb(v.game, v.gameName), mapThumb(v.map));
  const t = el('div', 'txt');
  t.append(el('small', null, 'NEXT UP'), el('b', null, v.gameName || ''), el('span', null, `on ${v.mapName || ''}`));
  if (v.event) t.append(el('span', 'tag', 'EVENT'));
  c.append(t);
  box.append(c);
}
function renderTabbar() { for (const b of $('esTabbar').children) b.classList.toggle('on', b.dataset.tab === ES.tab); }
function setTab(id) { ES.tab = id; ES.tabPicked = true; renderTabbar(); renderTab(); }
function renderTab() {
  renderTabbar();
  const body = $('esBody');
  body.innerHTML = '';
  body.dataset.tab = ES.tab;
  ({ board: tabBoard, perf: tabPerf, medals: tabMedals, rewards: tabRewards })[ES.tab](body);
}
function tabBoard(body) {
  const m = ES.round || {};
  const rows = m.board || (m.top || []).map((r) => [...r, 0, 0]);
  if (!rows.length) { body.append(el('div', 'es-empty', 'no scores yet. you joined mid-vote.')); return; }
  const t = el('div', 'es-board');
  const head = el('div', 'row head');
  for (const h of ['#', 'PLAYER', 'K', 'D', 'KDR', 'SCORE']) head.append(el('span', null, h));
  t.append(head);
  rows.forEach(([id, name, k, d, team, bot, score], i) => {
    const r = el('div', 'row' + (id === G.myId ? ' me' : ''));
    if (team && TEAMS[team]) r.style.setProperty('--tc', TEAMS[team].color);
    r.append(el('span', 'rk', String(i + 1)));
    const nm = el('span', 'nm');
    const dot = el('i', 'dot'); const nfo = G.names.get(id); dot.style.background = (nfo && nfo.color) || '#fff';
    nm.append(dot, el('b', null, bot ? String(name).replace(/ \[bot\]$/, '') : name));
    if (bot) nm.append(el('em', 'bot', 'BOT'));
    if (id === G.myId) nm.append(el('em', 'you', 'YOU'));
    const note = ES.opts.note && ES.opts.note(id, m);
    if (note) nm.append(el('em', 'note', note));
    r.append(nm, el('span', null, String(k)), el('span', null, String(d)), el('span', null, (k / Math.max(1, d)).toFixed(2)), el('span', 'sc', String(score || k * 100)));
    r.style.setProperty('--i', i);
    t.append(r);
  });
  body.append(t);
}
function tile(label, value, cls, sub) {
  const d = el('div', 'es-tile' + (cls ? ' ' + cls : ''));
  d.append(el('small', null, label), el('b', null, value));
  if (sub) d.append(el('span', null, sub));
  return d;
}
function tabPerf(body) {
  const p = ES.perf;
  if (!p) { body.append(el('div', 'es-empty', 'no record for you this match.')); return; }
  const wrap = el('div', 'es-perf');
  const earn = el('div', 'grp'); earn.append(el('h4', null, 'COMBAT EARNINGS'));
  const eg = el('div', 'tiles');
  eg.append(tile('EXPERIENCE', `+${p.xp}`, 'xp', p.acct ? 'XP' : 'xp (log in to keep it)'));
  const r = ES.roll;
  const crate = r && r.n > 0 ? (CONTAINERS[r.kind] || CONTAINERS.box).name.toUpperCase() : '—';
  eg.append(tile('CONTAINER', r && r.n > 0 ? `+${r.n}` : '+0', 'crate', r && r.n > 0 ? crate : r && r.guest ? 'you earned one. log in to keep them' : r && r.why ? r.why : 'win the round for one'));
  earn.append(eg);
  const rec = el('div', 'grp'); rec.append(el('h4', null, 'COMBAT RECORD'));
  const rg = el('div', 'tiles');
  rg.append(tile('SCORE', String(p.score), 'big'), tile('KILLS', String(p.kills)), tile('DEATHS', String(p.deaths)), tile('RANK', `#${p.rank}`, '', `of ${p.of}`), tile('KDR', p.kdr.toFixed(2)),
    tile('BEST STREAK', String(p.best)), tile('HEADSHOT KILLS', String(p.hsk)), tile('FASTEST KILL', `${p.fast}`, '', 'km/h'), tile('LONGEST KILL', `${p.far}`, '', 'metres'));
  rec.append(rg);
  wrap.append(earn, rec);
  body.append(wrap);
  countUp(wrap);
}
// numbers roll up when the tab opens
function countUp(box) {
  for (const b of box.querySelectorAll('.es-tile b')) {
    const m = /^([+#]?)(-?\d+(?:\.\d+)?)$/.exec(b.textContent);
    if (!m) continue;
    const to = Number(m[2]), dec = m[2].includes('.') ? 2 : 0, t0 = performance.now();
    const step = () => { const k = Math.min(1, (performance.now() - t0) / 700); b.textContent = m[1] + (to * (1 - (1 - k) ** 3)).toFixed(dec); if (k < 1 && b.isConnected) requestAnimationFrame(step); };
    step();
  }
}
function medal(id, got) {
  const md = MEDALS[id];
  const d = el('div', 'es-medal' + (got ? ' got' : ''));
  d.style.setProperty('--mc', md.c);
  const url = medalImage(id, md); // a 3d badge (no webgl for it: a plain square with the glyph)
  if (url) { const img = new Image(); img.alt = ''; img.className = 'coin'; img.src = url; d.append(img); }
  else { const c = el('span', 'coin flat', md.g); c.style.background = md.c; d.append(c); }
  d.append(el('b', null, md.name), el('small', null, md.desc));
  return d;
}
function tabMedals(body) {
  const got = (ES.perf && ES.perf.medals) || [];
  const w = el('div', 'es-medals');
  if (!got.length) w.append(el('div', 'es-empty', 'no medals. HR has noted this in your file.'));
  got.forEach((id, i) => { if (MEDALS[id]) { const m = medal(id, true); m.style.setProperty('--i', i); w.append(m); } });
  body.append(w);
  const rest = Object.keys(MEDALS).filter((id) => !got.includes(id));
  if (rest.length) {
    body.append(el('h4', 'es-h', 'NOT THIS TIME'));
    const l = el('div', 'es-medals small');
    for (const id of rest) l.append(medal(id, false));
    body.append(l);
  }
}
function tabRewards(body) {
  const p = ES.perf || { xp: 0 };
  const w = el('div', 'es-rewards');
  const lv = ES.perf && ES.perf.acct ? ES.lv : null;
  const xpBox = el('div', 'es-xp');
  if (lv) {
    const { level, xp } = lv, need = (l) => (l - 1) * (l - 1) * 40;
    let L = level; while (xp + p.xp >= need(L + 1)) L++;
    const a = need(L), b2 = need(L + 1), from = Math.max(0, Math.min(1, (xp - a) / (b2 - a))), to = Math.min(1, (xp + p.xp - a) / (b2 - a));
    xpBox.append(el('b', null, L > level ? `LEVEL UP! ${level} → ${L}` : `LEVEL ${L}`), el('span', null, `+${p.xp} xp · ${Math.max(0, b2 - xp - p.xp)} to level ${L + 1}`));
    const bar = el('div', 'bar'); const f0 = el('i', 'old'), f1 = el('i', 'new');
    f0.style.width = `${(L > level ? 0 : from) * 100}%`; f1.style.width = `${(L > level ? 0 : from) * 100}%`;
    bar.append(f1, f0); xpBox.append(bar);
    requestAnimationFrame(() => requestAnimationFrame(() => { f1.style.width = `${to * 100}%`; }));
  } else xpBox.append(el('b', null, `+${p.xp} XP`), el('span', null, 'you are a guest. log in and this goes on your record (plus crates when you win).'));
  w.append(xpBox);
  const r = ES.roll;
  const loot = el('div', 'es-loot');
  if (r && r.n > 0) { const c = CONTAINERS[r.kind] || CONTAINERS.box; loot.append(el('b', null, `+${r.n} ${c.name.toUpperCase()}`), el('span', null, `${c.desc}. open it in CONTAINERS`)); loot.classList.add('got'); }
  else loot.append(el('b', null, 'NO CONTAINER'), el('span', null, (r && (r.why || (r.guest && 'you would have earned one. log in to keep them.'))) || 'win a round to earn one'));
  w.append(loot);
  if (ES.achs.length) {
    w.append(el('h4', 'es-h', 'ACHIEVEMENTS UNLOCKED'));
    for (const a of ES.achs) { const d = el('div', 'es-ach'); d.append(el('b', null, a.name), el('span', null, a.desc || '')); w.append(d); }
  }
  body.append(w);
}

// ---------------------------------------------------------------- clock
function tick() {
  ES.raf = 0;
  if (!ES.open) return;
  const n = performance.now();
  const total = ES.totalEnd - n;
  $('esClock').textContent = clock(total);
  const sec = Math.ceil(total / 1000);
  if (sec !== ES.lastSec) { ES.lastSec = sec; if (sec <= 3 && sec > 0) { sfx.plip(); $('esClock').parentElement.classList.remove('beat'); void root.offsetWidth; $('esClock').parentElement.classList.add('beat'); } }
  const left = Math.max(0, ES.stageEnd - n);
  $('esBar').style.transform = `scaleX(${ES.vote && ES.vote.stage !== 'done' ? Math.min(1, left / ES.stageLen) : 0})`;
  root.classList.toggle('hurry', !!ES.vote && ES.vote.stage !== 'done' && left < 3000);
  ES.raf = requestAnimationFrame(tick);
}
