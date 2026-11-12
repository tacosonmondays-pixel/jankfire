// THE HUB (docs/menu/HUB_LOBBY.md, build step 1): the main menu's mode cards, and each mode's lobby screen.
// a card opens its mode's lobby: you on the stage in the middle, MATCH on the left (PUBLIC = find a match: real
// players only, or with bots filling the seats; PRIVATE = your own match: map, bots, difficulty, hipfire), the big
// yellow button at the bottom. public goes through today's mode lobbies (server/lobby.js), private through a bots room
// nobody else can drop into (cfg.priv, server/room.js roomFor). parties come in step 2: for now the party is you.
import { G } from './ctx.js';
import { GAMES, GAME_ORDER, mapsFor } from '/shared/modes.js';
import { MAPS, MAP_ORDER } from '/shared/map.js';
import { BOT_DIFF, HIPFIRE } from '/shared/weapons.js';
import { LOBBY } from '/shared/lobby.js';
import { eventGame } from '/shared/vote.js';
import { modeThumb, modeColors } from './modeart.js';
import { fleshFrame } from './flesh.js';
import { resizePreview } from './preview.js';
import { synth } from './audio.js';

const $ = (id) => document.getElementById(id);
const click = () => { try { synth.tone('square', 500, 500, 0.03, 0.08); } catch { /* (no audio yet) */ } };
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
// the hub's cards. lobby: the shared/lobby.js kind PUBLIC uses (none: private only). games: what PRIVATE can play
export const HUB = {
  qp: { name: 'QUICK PLAY', art: 'dm', desc: 'drop in, vote the next mode. or make your own match', lobby: 'qp', games: null },
  bomb: { name: 'PLANT & DEFUSE', art: 'bomb', desc: '5v5. plant it, defuse it, buy guns between rounds', lobby: 'bomb', games: ['bomb'] },
  br: { name: 'JANK ROYALE', art: 'br', desc: 'blimp, umbrella, loot, shrinking zone. last one standing', lobby: 'br', games: ['br'] },
  zm: { name: 'ZOMBIES', art: 'zm', desc: 'you and your friends vs endless rounds. buy doors', lobby: 'zm', games: ['zm'] },
  isle: { name: 'BATTLE ISLAND', art: 'br', desc: 'squads of 3, mech heroes. go down, get picked up', lobby: null, games: ['island'], tag: 'MECHS', beta: 1 },
  training: { name: 'TRAINING', art: 'gun', desc: 'dummies and infinite ammo. nobody is judging', train: 1 },
};
const ORDER = ['qp', 'bomb', 'br', 'zm', 'isle', 'training'];
const COL = { qp: '#ff4f6a', bomb: '#ffb04f', br: '#4fd8ff', zm: '#39ff14', isle: '#ff4fd8', training: '#ffe14d' };
let opts = {}, counts = null, pollT = 0, cur = null;
// the lobby's choices (kept between visits, per mode)
const pick = {}; // kind -> { pub, fill, game, map, bots, botsOn, diff, hip }
const S = () => (G.settings.hub || (G.settings.hub = {}));

export function initHub(o) {
  opts = o; // { start(mode, cfg), show(id), hero(slot), save() }
  const box = $('hubCards');
  if (!box) return;
  for (const k of ORDER) box.append(card(k));
  $('hubBack').addEventListener('click', () => { click(); opts.show('main'); });
  $('hubGo').addEventListener('click', go);
  addEventListener('keydown', (e) => {
    if (!onLobby() || e.repeat) return;
    if (e.key === 'Escape') { e.preventDefault(); opts.show('main'); }
    if (e.key === 'Enter' && document.activeElement.tagName !== 'SELECT') { e.preventDefault(); go(); }
  });
  addEventListener('resize', () => { if (onLobby()) frame(); });
}
const onLobby = () => !$('scr-hubby').classList.contains('hidden') && !$('menu').classList.contains('hidden');

function card(k) {
  const H = HUB[k], c = el('button', 'hub-card');
  c.dataset.kind = k; c.style.setProperty('--c', COL[k]);
  if (H.train) c.dataset.mode = 'training'; // (scripts click [data-mode="training"]: TRAINING still starts straight away)
  c.append(modeThumb(H.art, H.name));
  const t = el('div', 'hc-txt'); t.append(el('b', null, H.name), el('span', null, H.desc)); c.append(t);
  c.append(el('i', 'hc-live', H.train ? 'just you and the dummies' : '·'));
  if (H.tag) c.append(el('em', 'hc-tag', H.tag));
  if (k === 'qp') c.append(el('em', 'hc-ev', ''));
  if (!H.train) c.addEventListener('click', () => { click(); openLobby(k); });
  return c;
}

// every time the main menu shows: today's event on Quick Play, how many people are in each mode
export function hubShown() {
  const ev = $('hubCards') && $('hubCards').querySelector('.hc-ev'), g = GAMES[eventGame()];
  if (ev) { ev.textContent = g ? 'TODAY: ' + g.name : ''; ev.classList.toggle('hidden', !g); }
  poll();
}
async function poll() {
  clearTimeout(pollT);
  if (!$('hubCards') || $('menu').classList.contains('hidden')) return;
  try { counts = await (await fetch('/lobbies', { cache: 'no-store' })).json(); } catch { counts = null; }
  for (const c of document.querySelectorAll('#hubCards .hub-card')) {
    const k = c.dataset.kind, H = HUB[k];
    if (H.train) continue;
    const lk = H.lobby, n = counts && lk ? ((counts.o && counts.o[lk]) | 0) + ((counts.b && counts.b[lk]) | 0) : null;
    c.querySelector('.hc-live').textContent = !lk ? 'private matches (beta)' : n == null ? 'server not answering' : n ? `● ${n} playing` : 'no one yet. start it';
    c.classList.toggle('busy', !!n);
  }
  pollT = setTimeout(poll, 6000);
}

// ---------------------------------------------------------------- a mode's lobby
const gamesOf = (k) => HUB[k].games || GAME_ORDER.filter((g) => GAMES[g] && !GAMES[g].hidden && g !== 'island');
const mapsOf = (g) => (GAMES[g] ? mapsFor(g, MAPS, MAP_ORDER) : MAP_ORDER);
function stateOf(k) {
  if (pick[k]) return pick[k];
  const saved = S()[k] || {}, H = HUB[k], games = gamesOf(k);
  const ev = eventGame(), game = games.includes(saved.game) ? saved.game : k === 'qp' && games.includes(ev) ? ev : games[0];
  const st = { pub: H.lobby ? saved.pub !== false : false, fill: saved.fill !== false, coop: !!saved.coop, game, map: saved.map, botsOn: saved.botsOn !== false,
    bots: Number.isFinite(saved.bots) ? Math.max(1, Math.min(12, saved.bots)) : 5, diff: BOT_DIFF[saved.diff] ? saved.diff : (G.settings.diff || 'normal'), hip: HIPFIRE[saved.hip] ? saved.hip : 'normal' };
  if (!mapsOf(st.game).includes(st.map)) st.map = mapsOf(st.game)[0];
  return (pick[k] = st);
}
function remember(k) { const st = pick[k]; S()[k] = { ...st }; if (opts.save) opts.save(); }

export function openLobby(k) {
  if (!HUB[k] || HUB[k].train) return;
  cur = k;
  opts.show('hubby');
}
// show() calls this when the lobby screen comes up
export function hubLobbyShown() {
  if (!cur) cur = 'qp';
  frame();
  const H = HUB[cur], [ca] = modeColors(H.art);
  const scr = $('scr-hubby');
  scr.style.setProperty('--c', COL[cur] || ca);
  $('hubName').textContent = H.name;
  $('hubDesc').textContent = H.desc;
  opts.hero($('hubStage'));
  setTimeout(resizePreview, 0);
  render();
}
let lastFrame = '';
function frame() {
  const k = `${innerWidth}x${innerHeight}`;
  if (k === lastFrame && $('hubFrame').innerHTML) return;
  lastFrame = k; $('hubFrame').innerHTML = fleshFrame(innerWidth, innerHeight);
}

function seg(options, on, set) {
  const s = el('div', 'hub-seg');
  for (const [v, label, dis] of options) {
    const b = el('button', v === on ? 'on' : '', label);
    if (dis) { b.disabled = true; b.title = dis; }
    b.addEventListener('click', () => { if (v !== on) { click(); set(v); render(); } });
    s.append(b);
  }
  return s;
}
function row(label, ctl, title) { const r = el('div', 'hub-set'); r.append(el('span', null, label), ctl); if (title) r.title = title; return r; }
function toggle(on, set) { const b = el('button', 'hub-tog' + (on ? '' : ' off')); b.setAttribute('aria-pressed', on ? 'true' : 'false'); b.addEventListener('click', () => { click(); set(!on); render(); }); return b; }
function stepper(list, v, set, name = (x) => x) { // < VALUE >
  const w = el('span', 'hub-step'), i = Math.max(0, list.indexOf(v));
  const a = el('button', null, '<'), b = el('button', null, '>'), t = el('em', null, name(list[i]));
  a.addEventListener('click', () => { click(); set(list[(i + list.length - 1) % list.length]); render(); });
  b.addEventListener('click', () => { click(); set(list[(i + 1) % list.length]); render(); });
  if (list.length < 2) a.disabled = b.disabled = true;
  w.append(a, t, b); return w;
}

function render() {
  const k = cur, H = HUB[k], st = stateOf(k), L = $('hubMatch'), R = $('hubSide');
  L.innerHTML = ''; R.innerHTML = '';
  L.append(el('span', 'hub-tag', 'MATCH'));
  L.append(seg([[true, 'PUBLIC', H.lobby ? '' : 'public Battle Island comes with parties'], [false, 'PRIVATE']], st.pub, (v) => { st.pub = v; remember(k); }));
  if (st.pub) {
    if (k === 'qp') L.append(row('who', seg([['all', 'EVERYONE'], ['bots', 'WITH BOTS'], ['coop', 'CO-OP']], st.coop ? 'coop' : st.fill ? 'bots' : 'all', (v) => { st.coop = v === 'coop'; st.fill = v === 'bots'; remember(k); })));
    else L.append(row('fill empty seats with bots', toggle(st.fill, (v) => { st.fill = v; remember(k); }), 'off: real players only, the match waits for enough people'));
    L.append(row('map', el('em', null, k === 'qp' ? 'VOTED EACH MATCH' : 'RANDOM, THEN VOTED')));
    L.append(row('lobby', el('em', null, k === 'qp' ? 'DROP IN NOW' : 'WARM-UP ARENA, 60 s')));
  } else {
    if (k === 'qp') L.append(row('mode', select(gamesOf(k), st.game, (v) => { st.game = v; if (!mapsOf(v).includes(st.map)) st.map = mapsOf(v)[0]; remember(k); }, (g) => GAMES[g].name)));
    const own = GAMES[st.game] && (GAMES[st.game].royale || GAMES[st.game].zombies); // (a royale brings its crowd, zombies its horde)
    if (own) L.append(row('bots', el('em', null, GAMES[st.game].zombies ? 'THE HORDE' : 'A CROWD OF THEM')));
    else L.append(row('bots', toggle(st.botsOn, (v) => { st.botsOn = v; remember(k); })));
    if (st.botsOn && !own) {
      const r = el('input'); r.type = 'range'; r.min = 1; r.max = 12; r.step = 1; r.value = st.bots;
      const n = el('em', null, String(st.bots));
      r.addEventListener('input', () => { st.bots = Number(r.value); n.textContent = r.value; });
      r.addEventListener('change', () => remember(k));
      const w = el('span', 'hub-range'); w.append(r, n); L.append(row('bot count', w));
    }
    if (st.botsOn || own) L.append(row('difficulty', stepper(Object.keys(BOT_DIFF), st.diff, (v) => { st.diff = v; remember(k); }, (d) => BOT_DIFF[d].name.toUpperCase())));
    L.append(row('hipfire', stepper(Object.keys(HIPFIRE), st.hip, (v) => { st.hip = v; remember(k); }, (h) => HIPFIRE[h].name.toUpperCase())));
    L.append(el('div', 'hub-small', 'private: nobody else drops in. (friends and party codes come next)'));
  }
  // right: the map (private) or what happens next (public)
  if (st.pub) {
    R.append(el('span', 'hub-tag', 'WHAT HAPPENS'));
    const txt = k === 'qp' ? (st.coop ? 'you and whoever is online vs waves of bots.' : st.fill ? 'you drop into a match with bots and people. you take a bot\'s seat.' : 'you drop into the online room right now. everyone votes the next mode and map.')
      : `you land in the ${H.name.toLowerCase()} lobby: a warm-up deathmatch on the match's map while the countdown runs. hit READY when you're ready.` + (st.fill ? ' bots take the empty seats.' : ` it needs ${LOBBY.kinds[H.lobby].min} real players.`);
    R.append(el('p', 'hub-p', txt));
    const n = counts && H.lobby ? ((counts[st.fill || st.coop ? 'b' : 'o'] || {})[H.lobby] | 0) : null;
    if (n != null) R.append(row('in there now', el('em', null, String(n))));
  } else {
    R.append(el('span', 'hub-tag', 'MAP'));
    const maps = mapsOf(st.game);
    if (!maps.includes(st.map)) st.map = maps[0];
    const img = el('img', 'hub-map'); img.alt = ''; img.src = `/thumbs/${st.map}.jpg`; img.onerror = () => { img.style.visibility = 'hidden'; };
    R.append(img);
    R.append(stepper(maps, st.map, (v) => { st.map = v; remember(k); }, (m) => MAPS[m].name.toUpperCase()));
    const strip = el('div', 'hub-maps');
    for (const m of maps) {
      const t = el('button', m === st.map ? 'on' : ''); t.title = MAPS[m].name;
      const i = el('img'); i.alt = MAPS[m].name; i.src = `/thumbs/${m}.jpg`; t.append(i);
      t.addEventListener('click', () => { click(); st.map = m; remember(k); render(); });
      strip.append(t);
    }
    R.append(strip);
  }
  const b = $('hubGo');
  b.textContent = st.pub ? (k === 'qp' && !st.fill && !st.coop ? 'PLAY NOW' : 'FIND MATCH') : 'START MATCH';
}
function select(list, v, set, name) {
  const s = el('select');
  for (const x of list) { const o = el('option', null, name(x)); o.value = x; if (x === v) o.selected = true; s.append(o); }
  s.addEventListener('change', () => { set(s.value); render(); });
  return s;
}

// the big button
function go() {
  if (!onLobby() || !cur) return;
  const k = cur, H = HUB[k], st = stateOf(k);
  remember(k);
  click();
  if (st.pub) {
    if (k === 'qp') { if (st.coop) opts.start('coop'); else if (st.fill) opts.start('bots', { lobby: 'qp' }); else opts.start('ffa'); return; }
    opts.start(st.fill ? 'bots' : 'ffa', { lobby: H.lobby });
    return;
  }
  const game = k === 'qp' ? st.game : H.games[0], maps = mapsOf(game), map = maps.includes(st.map) ? st.map : maps[0];
  const own = GAMES[game] && (GAMES[game].royale || GAMES[game].zombies);
  opts.start('bots', { priv: true, game, map, bots: own ? 5 : st.botsOn ? st.bots : 0, diff: st.diff, hip: st.hip });
}
