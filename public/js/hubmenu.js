// THE HUB (docs/menu/HUB_LOBBY.md, build step 1, the owner's cut: "show your character and like online or offline
// options ... that way it's not so cluttered"). the main menu is you, the STAFF ENTRANCE, and two big buttons:
// ONLINE (real players) and OFFLINE (you and bots). either opens the lobby screen: the mode picker across the top, you
// on the stage in the middle, MATCH on the left, the map / what happens on the right, the big yellow button.
// ONLINE goes through today's mode lobbies (server/lobby.js); OFFLINE is a bots room of your own that nobody else drops
// into (cfg.priv, server/room.js roomFor). step 2, parties (party.js, server/party.js): the party strip under the big
// buttons (its code, JOIN a code, LEAVE, who's in it), the party stood on the stage (lineup.js); the leader picks and
// starts (everyone's lobby follows), everyone else hits READY.
import { G } from './ctx.js';
import { GAMES, GAME_ORDER, mapsFor, WIP_ON } from '/shared/modes.js';
import { MAPS, MAP_ORDER } from '/shared/map.js';
import { LOBBY } from '/shared/lobby.js';
import { eventGame } from '/shared/vote.js';
import { BGN, BGN_NAMES } from '/shared/bgn.js'; // board game night's names and round counts
import { BOT_DIFF } from '/shared/weapons.js';
import { modeThumb } from './modeart.js';
import { fleshFrame } from './flesh.js';
import { resizePreview } from './preview.js';
import { synth } from './audio.js';
import { mountLobbyScene, lobbyScenePrefetch } from './lobbyscenes/index.js'; // the 3D place behind each mode (LOBBY_SCENES.md)
import { P, onParty, inParty, isLead, leadName, partyJoin, partyLeave, partyKick, partyLead, partyReady, partySet, partyGo, meReady } from './party.js';
import { showLineup } from './lineup.js';
import { openFriends, friendsLoad, friendsOnline, friendsShown } from './friends.js'; // friends (step 3)

const $ = (id) => document.getElementById(id);
const click = () => { try { synth.tone('square', 500, 500, 0.03, 0.08); } catch { /* (no audio yet) */ } };
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
// the modes. lobby: the shared/lobby.js kind ONLINE uses (none: offline only). games: what OFFLINE can play (null: any)
export const HUB = {
  qp: { name: 'QUICK PLAY', art: 'dm', desc: 'drop in, vote the next mode and map', lobby: 'qp', games: null },
  bomb: { name: 'PLANT & DEFUSE', art: 'bomb', desc: '5v5. plant it, defuse it, buy guns between rounds', lobby: 'bomb', games: ['bomb'] },
  br: { name: 'JANK ROYALE', art: 'br', desc: 'blimp, umbrella, loot, shrinking zone. last one standing', lobby: 'br', games: ['br'] },
  zm: { name: 'ZOMBIES', art: 'zm', desc: 'you and your friends vs endless rounds. buy doors', lobby: 'zm', games: ['zm'] },
  isle: { name: 'BATTLE ISLAND', art: 'isle', desc: 'squads of 3, mech heroes. go down, get picked up', lobby: null, games: ['island'], tag: 'MECHS' },
  bgn: { name: BGN_NAMES.mode, art: 'bgn', desc: BGN_NAMES.desc, lobby: 'bgn', games: ['bgn'], tag: BGN_NAMES.tag, board: 1 }, // the party board mode (shared/bgn.js)
  training: { name: 'TRAINING', art: 'train', desc: 'dummies and infinite ammo. nobody is judging', train: 1 },
};
const ORDER = ['qp', 'bomb', 'br', 'zm', 'isle', 'bgn', 'training'];
const COL = { qp: '#ff4f6a', bomb: '#ffb04f', br: '#4fd8ff', zm: '#39ff14', isle: '#ff4fd8', bgn: '#ffb300', training: '#ffe14d' };
const SIDES = { online: { name: 'ONLINE', desc: 'real players. find a match, bots fill in if you want' }, offline: { name: 'OFFLINE', desc: 'just you and bots. your map, your rules, nobody drops in' } };
let opts = {}, counts = null, pollT = 0, side = 'online';
const pick = {}; // `${side}:${mode}` -> its choices (kept between visits)
const S = () => (G.settings.hub && typeof G.settings.hub === 'object' ? G.settings.hub : (G.settings.hub = {}));

export function initHub(o) {
  opts = o; // { start(mode, cfg), show(id), hero(slot), save(), look() -> [color, look], toast(text, ms) }
  if (!$('scr-hubby')) return;
  for (const b of document.querySelectorAll('[data-hub]')) b.addEventListener('click', () => { click(); openLobby(b.dataset.hub); });
  $('hubBack').addEventListener('click', () => { click(); opts.show('main'); });
  $('hubGo').addEventListener('click', go);
  addEventListener('keydown', (e) => {
    const a = document.activeElement;
    if (!onLobby() || e.repeat || /^(INPUT|SELECT|TEXTAREA)$/.test(a && a.tagName)) return;
    if (e.key === 'Enter' && a && a !== document.body && a !== $('hubGo')) return; // (Enter on a focused button presses that button)
    if (e.key === 'Escape') { e.preventDefault(); opts.show('main'); }
    else if (e.key === 'Enter') { e.preventDefault(); go(); }
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { const i = ORDER.indexOf(modeOf()); setMode(ORDER[(i + (e.key === 'ArrowRight' ? 1 : ORDER.length - 1)) % ORDER.length]); }
  });
  addEventListener('resize', () => { if (onLobby()) frame(); stage(); });
  onParty(partyChanged);
  partyStrip();
}
const onMain = () => !$('scr-main').classList.contains('hidden') && !$('menu').classList.contains('hidden');
const onLobby = () => !$('scr-hubby').classList.contains('hidden') && !$('menu').classList.contains('hidden');

// every time the main menu shows: the live count on ONLINE
export function hubShown() { poll(); partyStrip(); stage(); friendsLoad().then(partyStrip); }
async function poll() {
  clearTimeout(pollT);
  if (!$('scr-hubby') || $('menu').classList.contains('hidden') || ($('scr-main').classList.contains('hidden') && $('scr-hubby').classList.contains('hidden'))) return; // (only the home and the lobby show counts)
  try { counts = await (await fetch('/lobbies', { cache: 'no-store' })).json(); } catch { counts = null; }
  const live = $('hubLive');
  if (live) { const n = counts ? Object.values(counts.o || {}).reduce((a, v) => a + (v | 0), 0) : null; live.textContent = n == null ? '' : n ? `● ${n} playing online` : ''; }
  if (onLobby()) liveRow();
  if (onMain() && ++pollN % 3 === 1) friendsLoad().then(partyStrip); // (friends coming online: the strip's count, every ~18 s)
  pollT = setTimeout(poll, 6000);
}
let pollN = 0;

// ---------------------------------------------------------------- the lobby screen
const gamesOf = (k) => HUB[k].games || GAME_ORDER.filter((g) => GAMES[g] && !GAMES[g].royale && !GAMES[g].zombies && g !== 'bomb' && g !== 'island'); // (quick play offline: the deathmatch family)
const mapsOf = (g) => (GAMES[g] ? mapsFor(g, MAPS, MAP_ORDER) : MAP_ORDER);
const modeOf = () => { const m = S()[side + ':mode']; return HUB[m] && !(side === 'online' && HUB[m].lobby === null) ? m : 'qp'; };
function setMode(k) { if (!HUB[k] || (side === 'online' && HUB[k].lobby === null && !HUB[k].train) || (inParty() && !isLead())) return; click(); S()[side + ':mode'] = k; save(); partySet(side, k); render(); }
function stateOf(k) {
  const key = side + ':' + k;
  if (pick[key]) return pick[key];
  const sv = S()[key] && typeof S()[key] === 'object' ? S()[key] : {}, games = gamesOf(k), ev = eventGame();
  const st = { fill: sv.fill !== false, who: ['all', 'bots', 'coop'].includes(sv.who) ? sv.who : 'all',
    game: games.includes(sv.game) ? sv.game : k === 'qp' && games.includes(ev) ? ev : games[0], map: sv.map, botsOn: sv.botsOn !== false,
    bots: Number.isFinite(sv.bots) ? Math.max(1, Math.min(12, Math.round(sv.bots))) : 5,
    rounds: BGN.roundOpts.includes(sv.rounds) ? sv.rounds : BGN.rounds, diff: Object.hasOwn(BOT_DIFF, sv.diff) ? sv.diff : 'normal' }; // (board game night: its length and how good the bots are) // (no difficulty or hipfire here, the owner's call: an offline match plays the room's defaults)
  if (!mapsOf(st.game).includes(st.map)) st.map = mapsOf(st.game)[0];
  return (pick[key] = st);
}
function remember(k) { S()[side + ':' + k] = { ...stateOf(k) }; save(); }
function save() { if (opts.save) opts.save(); }

export function openLobby(s) {
  side = s === 'offline' ? 'offline' : 'online';
  if (inParty() && !isLead()) { opts.toast(`${leadName()} picks the match. they'll bring you in`, 2400); return; }
  partySet(side, modeOf());
  opts.show('hubby');
}
// an offline single-mode match ended (server/hubback.js 'go', or LOBBY on the end screen): back to that mode's lobby.
// a party member goes straight there too (the leader's lobby is the same one)
export function hubBackTo(mode) {
  if (!HUB[mode]) { opts.show('main'); return; }
  side = 'offline'; S()['offline:mode'] = mode;
  if (!inParty() || isLead()) partySet(side, mode);
  opts.show('hubby');
}
// show() calls this when the lobby screen comes up
export function hubLobbyShown() {
  frame();
  $('hubName').textContent = SIDES[side].name;
  $('hubDesc').textContent = SIDES[side].desc;
  $('scr-hubby').dataset.side = side;
  opts.hero($('hubStage'));
  setTimeout(() => { resizePreview(); stage(); }, 0);
  render();
  poll();
}
let lastFrame = '';
function frame() {
  const k = `${innerWidth}x${innerHeight}`;
  if (k === lastFrame && $('hubFrame').innerHTML) return;
  lastFrame = k; $('hubFrame').innerHTML = fleshFrame(innerWidth, innerHeight);
}

// the mode picker across the top
function modes() {
  const box = $('hubModes'), cur = modeOf();
  box.innerHTML = '';
  for (const k of ORDER) {
    const H = HUB[k], off = side === 'online' && H.lobby === null && !H.train;
    const b = el('button', 'hub-mode' + (k === cur ? ' on' : ''));
    b.style.setProperty('--c', COL[k]); b.dataset.mode2 = k;
    b.append(modeThumb(H.art, H.name), el('b', null, H.name));
    if (H.tag) b.append(el('em', 'hm-tag', H.tag));
    if (k === 'qp' && GAMES[eventGame()]) b.append(el('em', 'hm-ev', 'TODAY: ' + GAMES[eventGame()].name));
    if (off) { b.disabled = true; b.title = 'offline only for now: play it from OFFLINE (online squads come with parties)'; b.append(el('i', 'hm-off', 'OFFLINE ONLY')); }
    b.addEventListener('click', () => setMode(k));
    b.addEventListener('pointerenter', () => lobbyScenePrefetch(k)); // (its 3D place: fetched before the click)
    box.append(b);
  }
}
function seg(options, on, set) {
  const s = el('div', 'hub-seg');
  for (const [v, label] of options) {
    const b = el('button', v === on ? 'on' : '', label);
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
function select(list, v, set, name) {
  const s = el('select');
  for (const x of list) { const o = el('option', null, name(x)); o.value = x; if (x === v) o.selected = true; s.append(o); }
  s.addEventListener('change', () => { set(s.value); render(); });
  return s;
}
function liveRow() {
  const r = $('hubSide') && $('hubSide').querySelector('.hub-live em'), k = modeOf(), H = HUB[k], st = stateOf(k);
  if (!r || !H.lobby) return;
  const n = counts ? ((counts[k === 'qp' ? (st.who === 'all' ? 'o' : 'b') : st.fill ? 'b' : 'o'] || {})[H.lobby] | 0) : null;
  r.textContent = n == null ? '?' : String(n);
}

function render() {
  modes();
  const k = modeOf(), H = HUB[k], st = stateOf(k), L = $('hubMatch'), R = $('hubSide');
  $('scr-hubby').style.setProperty('--c', COL[k]);
  L.innerHTML = ''; R.innerHTML = '';
  L.append(el('span', 'hub-tag', H.name));
  L.append(el('p', 'hub-p', H.desc));
  if (H.train) {
    L.append(row('who', el('em', null, 'JUST YOU')), row('map', el('em', null, 'THE RANGE')));
    R.append(el('span', 'hub-tag', 'WHAT HAPPENS'), el('p', 'hub-p', 'the range: dummies to shoot, infinite ammo, your three killstreaks ready to try. leave whenever.'));
  } else if (H.board && side === 'offline') { // board game night: 4 seats, you and 3 bots
    L.append(row('rounds', seg(BGN.roundOpts.map((n) => [n, String(n)]), st.rounds, (v) => { st.rounds = v; remember(k); }), 'about 3 minutes a round'));
    L.append(row('bot difficulty', seg(Object.keys(BOT_DIFF).map((d) => [d, BOT_DIFF[d].name.toUpperCase()]), st.diff, (v) => { st.diff = v; remember(k); })));
    L.append(row('seats', el('em', null, 'YOU + 3 BOTS')));
    R.append(el('span', 'hub-tag', 'WHAT HAPPENS'), el('p', 'hub-p', `${BGN_NAMES.board.toLowerCase()}: roll ${BGN_NAMES.die.toLowerCase()}, collect ${BGN_NAMES.coupons.toLowerCase()}, buy ${BGN_NAMES.bread.toLowerCase()} at ${BGN_NAMES.bakery.toLowerCase()} (it moves). land on someone: duel. every round ends in a minigame. most bread wins.`));
  } else if (side === 'online') {
    if (k === 'qp') L.append(row('who', seg([['all', 'EVERYONE'], ['bots', '+ BOTS'], ['coop', 'CO-OP']], st.who, (v) => { st.who = v; remember(k); })));
    else L.append(row('fill empty seats with bots', toggle(st.fill, (v) => { st.fill = v; remember(k); }), 'off: real players only, the match waits for enough people'));
    L.append(row('map', el('em', null, k === 'qp' ? 'VOTED EACH MATCH' : 'RANDOM, THEN VOTED')));
    L.append(row('lobby', el('em', null, k === 'qp' ? 'DROP IN NOW' : 'PRE-GAME DECK, 60 s')));
    R.append(el('span', 'hub-tag', 'WHAT HAPPENS'));
    const txt = k === 'qp' ? (st.who === 'coop' ? 'you and whoever is online vs waves of bots.' : st.who === 'bots' ? 'you drop into a match with bots and people. you take a bot\'s seat.' : 'you drop into the online room right now. everyone votes the next mode and map.')
      : `you land in the ${H.name.toLowerCase()} lobby: a little deck floating off the edge of the match's map while the countdown runs. nothing hurts: shove people, spray, hit READY when you're ready.` + (st.fill ? ' bots take the empty seats.' : ` it needs ${LOBBY.kinds[H.lobby].min} real players.`);
    R.append(el('p', 'hub-p', txt));
    const lv = row('in there now', el('em', null, '·')); lv.classList.add('hub-live'); R.append(lv); liveRow();
  } else {
    if (k === 'qp') L.append(row('mode', select(gamesOf(k), st.game, (v) => { st.game = v; if (!mapsOf(v).includes(st.map)) st.map = mapsOf(v)[0]; remember(k); }, (g) => GAMES[g].name)));
    const own = GAMES[st.game] && (GAMES[st.game].royale || GAMES[st.game].zombies); // (a royale brings its crowd, zombies its horde)
    const team = !own && GAMES[st.game] && GAMES[st.game].teams; // (a team mode with nobody on the other side is no match: bots stay on)
    if (own) L.append(row('bots', el('em', null, GAMES[st.game].zombies ? 'THE HORDE' : 'A CROWD OF THEM')));
    else if (!team) L.append(row('bots', toggle(st.botsOn, (v) => { st.botsOn = v; remember(k); })));
    if ((st.botsOn || team) && !own) {
      const r = el('input'); r.type = 'range'; r.min = 1; r.max = 12; r.step = 1; r.value = st.bots;
      const n = el('em', null, String(st.bots));
      r.addEventListener('input', () => { st.bots = Number(r.value); n.textContent = r.value; });
      r.addEventListener('change', () => remember(k));
      const w = el('span', 'hub-range'); w.append(r, n); L.append(row('bot count', w));
    }
    R.append(el('span', 'hub-tag', 'MAP'));
    const maps = mapsOf(st.game);
    if (!maps.includes(st.map)) st.map = maps[0];
    const img = el('img', 'hub-map'); img.alt = ''; img.src = `/thumbs/${st.map}.jpg`; img.onerror = () => { img.style.visibility = 'hidden'; };
    R.append(img, stepper(maps, st.map, (v) => { st.map = v; remember(k); }, (m) => MAPS[m].name.toUpperCase()));
    const strip = el('div', 'hub-maps');
    for (const m of maps) {
      const t = el('button', m === st.map ? 'on' : ''); t.title = MAPS[m].name;
      const i = el('img'); i.alt = MAPS[m].name; i.src = `/thumbs/${m}.jpg`; t.append(i);
      t.addEventListener('click', () => { click(); st.map = m; remember(k); render(); });
      strip.append(t);
    }
    R.append(strip);
  }
  mountLobbyScene(k, { side, onMe: () => opts.show('character'), save }); // (the same mode again: a no-op)
  $('hubGo').textContent = H.train ? 'START TRAINING' : side === 'offline' ? 'START MATCH' : k === 'qp' && st.who === 'all' ? 'PLAY NOW' : 'FIND MATCH';
  // in a party: only the leader picks. everyone else watches the leader's choices and gets READY
  const ro = inParty() && !isLead();
  $('scr-hubby').classList.toggle('hub-ro', ro);
  if (ro) { $('hubGo').textContent = meReady() ? 'READY ✓' : 'READY?'; L.append(el('div', 'hub-small', `${leadName()} picks the match. you hit READY.`)); }
  else if (inParty()) { const r = P.ms.filter((m) => m.ready || m.id === P.lead).length; $('hubGo').title = `${r}/${P.ms.length} ready`; }
}

// the big button
function go() {
  if (!onLobby()) return;
  click();
  if (inParty() && !isLead()) { partyReady(!meReady()); return; }
  const [mode, cfg] = plan() || [];
  if (!mode) return;
  if (inParty()) partyGo(mode, cfg || {}); // (the server hands everyone a ticket to one room: party.js 'pgo')
  else opts.start(mode, cfg);
}
// what the big button starts: [mode, cfg] (the same as a solo join's, the party's leader sends it to the server)
function plan() {
  const k = modeOf(), H = HUB[k], st = stateOf(k);
  if (H.train) return ['training'];
  remember(k);
  if (side === 'online') {
    if (!H.lobby) return null;
    if (k === 'qp') return st.who === 'coop' ? ['coop'] : st.who === 'bots' ? ['bots', { lobby: 'qp' }] : ['ffa'];
    return [st.fill ? 'bots' : 'ffa', { lobby: H.lobby }];
  }
  if (H.board) return ['bots', { priv: true, game: 'bgn', map: 'crate', bots: 3, rounds: st.rounds, diff: st.diff, hub: k }]; // board game night: your own table (server/bgn.js)
  const game = k === 'qp' ? st.game : H.games[0], maps = mapsOf(game), map = maps.includes(st.map) ? st.map : maps[0];
  const own = GAMES[game] && (GAMES[game].royale || GAMES[game].zombies);
  const team = !own && GAMES[game] && GAMES[game].teams;
  return ['bots', { priv: true, game, map, bots: own ? 5 : st.botsOn || team ? st.bots : 0, hub: k === 'qp' ? undefined : k, wip: WIP_ON || undefined }]; // hub: a single-mode pick comes back to this lobby after (server/hubback.js)
}

// ---------------------------------------------------------------- the party
// the stage: the party stood in a row, or (alone) the usual hero
// the lobby scenes (the scene lane's module) own the stage while one is mounted: it registers its lobbySceneOn() here
// on load (no import from this side: the module may not be there)
let sceneOn = () => false;
export function lobbySceneFlag(fn) { if (typeof fn === 'function') sceneOn = fn; }
function stage() {
  if (onLobby() && sceneOn()) { showLineup(null); for (const s of [$('heroSlot'), $('hubStage')]) if (s) s.classList.remove('lineup-on'); return; } // (a scene is up: it stands the party itself)
  const slot = onLobby() ? $('hubStage') : onMain() ? $('heroSlot') : null;
  const on = !!slot && inParty() && showLineup(slot, P.ms, P.lead, P.me, opts.look ? opts.look()[1] : null);
  if (!on) showLineup(null);
  for (const s of [$('heroSlot'), $('hubStage')]) if (s) s.classList.toggle('lineup-on', on && s === slot);
}
function partyChanged(why) {
  partyStrip(); stage();
  // the leader picked: a member in the menu follows into that lobby (or out of it, when the leader went back)
  if (inParty() && !isLead() && P.set && (onMain() || onLobby()) && (why === 'set' || why === 'grew')) {
    side = P.set.side === 'offline' ? 'offline' : 'online';
    if (HUB[P.set.mode]) S()[side + ':mode'] = P.set.mode;
    if (onLobby()) hubLobbyShown(); else opts.show('hubby');
  }
  else if (onLobby()) render();
}
// the strip under ONLINE / OFFLINE: PARTY n/6, its code, JOIN a code, who's in it (the leader can kick or pass the lead)
function partyStrip() {
  const box = $('hubParty');
  if (!box) return;
  box.innerHTML = '';
  if (!P.on) { box.append(el('span', 'hp-off', 'parties: connecting...')); return; }
  const top = el('div', 'hp-row');
  top.append(el('span', 'hub-tag', `PARTY ${P.ms.length}/${P.max}`));
  const code = el('button', 'hp-code', P.code); code.title = 'your party code: friends type it in JOIN. click to copy';
  code.addEventListener('click', () => { click(); try { navigator.clipboard.writeText(P.code); opts.toast('party code copied: ' + P.code, 1800); } catch { /* (no clipboard) */ } });
  top.append(code);
  if (inParty()) { const lv = el('button', 'mid danger', 'LEAVE'); lv.addEventListener('click', () => { click(); partyLeave(); }); top.append(lv); }
  if (friendsShown()) { const fb = el('button', 'mid hp-fr'), n = friendsOnline(); fb.append('FRIENDS'); if (n) fb.append(el('b', null, ` ${n} ON`)); fb.addEventListener('click', () => { click(); openFriends(); }); top.append(fb); }
  box.append(top);
  const row = el('div', 'hp-row');
  const inp = el('input'); inp.maxLength = 5; inp.placeholder = 'CODE'; inp.autocomplete = 'off'; inp.spellcheck = false;
  const j = el('button', 'mid', 'JOIN');
  const doJoin = () => { const c = inp.value.trim().toUpperCase(); if (c.length === 5) { click(); partyJoin(c); inp.value = ''; } else opts.toast('party codes are 5 letters', 1600); };
  j.addEventListener('click', doJoin);
  inp.addEventListener('keydown', (e) => { e.stopPropagation(); if (e.key === 'Enter') doJoin(); });
  row.append(inp, j);
  box.append(row);
  if (inParty()) {
    const list = el('div', 'hp-list');
    for (const m of P.ms) {
      const c = el('span', 'hp-m' + (m.id === P.me ? ' me' : '') + (m.ready ? ' rd' : ''));
      c.append(el('b', null, (m.id === P.lead ? '👑 ' : '') + m.name));
      if (isLead() && m.id !== P.me) {
        const kk = el('button', null, 'KICK'), ll = el('button', null, 'LEAD');
        kk.title = 'kick ' + m.name; ll.title = 'make ' + m.name + ' the leader';
        kk.addEventListener('click', () => { click(); partyKick(m.id); }); ll.addEventListener('click', () => { click(); partyLead(m.id); });
        c.append(kk, ll);
      }
      list.append(c);
    }
    box.append(list);
  }
}

// a friend's invite: a pop-up on the menu (JOIN / NAH, gone in 30 s); in a match, a toast with the code
export function hubInvite(inv, joined) {
  if (joined) { opts.toast(`${inv.from} wants you in their party${inv.mode ? ' (' + inv.mode + ')' : ''}. code ${inv.code}`, 6000); return; }
  document.getElementById('hubInvite')?.remove();
  const box = el('div', 'hub-invite'); box.id = 'hubInvite';
  box.append(el('span', 'hub-tag', 'INVITE'), el('b', null, inv.from), el('span', null, ` wants you in their party${inv.mode ? ' (' + inv.mode + ')' : ''}`));
  const y = el('button', 'hub-go hi-yes', 'JOIN'), n = el('button', 'mid', 'NAH');
  y.addEventListener('click', () => { click(); partyJoin(inv.code); box.remove(); });
  n.addEventListener('click', () => { click(); box.remove(); });
  box.append(y, n);
  document.getElementById('menu').append(box);
  setTimeout(() => box.remove(), 30000);
}
