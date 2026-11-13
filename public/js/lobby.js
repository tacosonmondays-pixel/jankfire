// Mode lobbies, the client side (rules in /shared/lobby.js, server/lobby.js):
// 1. the home menu's ONLINE / WITH BOTS mode picker: big cards in the end-screen vote look, each with a live
//    "N playing" from the server's /lobbies
// 2. the lobby HUD in game: the big countdown, who's ready, the READY button (key: K.label('ready'))
import { LOBBY } from '/shared/lobby.js';
import { GAMES } from '/shared/modes.js';
import { MAPS } from '/shared/map.js';
import { modeThumb, modeColors } from './modeart.js';
import { organic } from './organic.js';
import { K } from './keys.js';
import { pregameSync } from './pregame.js';
import { synth } from './audio.js';

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const STICK = { tex: false, bits: false, rim: 3, pad: 6, shadow: [3, 3], wob: 0.7, lumps: 1, lumpA: 1.2 };
let opts = {}, which = 'online', pollT = 0, counts = null;

// ---------------------------------------------------------------- the picker
export function initLobby(o) {
  opts = o; // { start(mode, cfg), show(id) }
  for (const b of document.querySelectorAll('[data-pick]')) b.addEventListener('click', () => openPicker(b.dataset.pick));
  $('mpCustom').addEventListener('click', () => opts.show('setup'));
  $('lbReady').addEventListener('click', (e) => { e.stopPropagation(); toggleReady(); });
  organic($('lbReady'), STICK);
  organic($('lobbyBox'), { rim: 6, lumps: 4, lumpA: 3.4, shadow: [8, 8] });
}
const pickerOn = () => !$('scr-modes').classList.contains('hidden') && !$('menu').classList.contains('hidden');
export function openPicker(w) {
  which = w === 'bots' ? 'bots' : 'online';
  opts.show('modes');
  $('mpTitle').textContent = which === 'bots' ? 'WITH BOTS' : 'ONLINE';
  $('mpNote').textContent = ''; // the home buttons and the cards already say all of it
  $('mpNote').classList.add('hidden');
  $('mpCustom').classList.toggle('hidden', which !== 'bots');
  const box = $('mpCards');
  box.innerHTML = '';
  LOBBY.order.forEach((k, i) => box.append(card(k, i)));
  box.classList.remove('deal'); void box.offsetWidth; box.classList.add('deal');
  renderCounts();
  poll();
}
function card(k, i) {
  const L = LOBBY.kinds[k], g = L.art, c = el('button', 'es-card mp-card');
  c.dataset.kind = k;
  c.style.setProperty('--i', i);
  const [a, b] = modeColors(g); c.style.setProperty('--ca', a); c.style.setProperty('--cb', b);
  c.append(el('span', 'key', String(i + 1)));
  c.append(modeThumb(g, L.name));
  const info = el('div', 'info');
  info.append(el('b', 'nm', L.name));
  const min = which === 'online' && L.min > 1 ? ` · ${L.min}+ PLAYERS` : '';
  info.append(el('span', 'sub', (k === 'qp' ? 'ANY MODE' : GAMES[L.game] && GAMES[L.game].teams ? 'TEAMS' : k === 'zm' ? 'CO-OP' : 'FREE FOR ALL') + min));
  info.append(el('span', 'desc', k === 'qp' && which === 'online' ? 'drop in anytime. everyone votes the next mode and map' : L.desc + (k !== 'qp' ? '. 60 s lobby first' : '')));
  c.append(info);
  const foot = el('div', 'foot');
  const cnt = el('b', 'cnt live'); cnt.append(el('span', 'n', '·'));
  foot.append(el('span', 'playing', 'asking...'), cnt);
  c.append(foot);
  c.addEventListener('click', () => go(k));
  organic(c, { band: 10, rim: 8, lumps: 4, lumpA: 3.6, holes: [c.querySelector('.mthumb')] });
  for (const s of c.querySelectorAll('.key, .cnt')) organic(s, STICK);
  return c;
}
function go(k) {
  clearTimeout(pollT);
  if (which === 'online' && k === 'qp') opts.start('ffa'); // the drop-in room, exactly as before
  else opts.start(which === 'bots' ? 'bots' : 'ffa', { lobby: k });
}
// 1-4 on the picker
addEventListener('keydown', (e) => {
  if (!pickerOn() || e.target.tagName === 'INPUT') return;
  const i = ['Digit1', 'Digit2', 'Digit3', 'Digit4'].indexOf(e.code);
  if (i >= 0) go(LOBBY.order[i]);
});
async function poll() {
  clearTimeout(pollT);
  if (!pickerOn()) return;
  try { counts = await (await fetch('/lobbies', { cache: 'no-store' })).json(); } catch { counts = null; }
  renderCounts();
  pollT = setTimeout(poll, 4000);
}
function renderCounts() {
  for (const c of document.querySelectorAll('#mpCards .mp-card')) {
    const n = counts && counts[which === 'bots' ? 'b' : 'o'] ? counts[which === 'bots' ? 'b' : 'o'][c.dataset.kind] | 0 : null;
    c.querySelector('.playing').textContent = n == null ? 'server not answering' : n ? `${n} player${n === 1 ? '' : 's'}` : 'no one yet'; // real people only, never bots
    c.querySelector('.cnt .n').textContent = n == null ? '?' : String(n);
    c.classList.toggle('busy', !!n);
  }
}

// ---------------------------------------------------------------- the lobby HUD
let L = null, gotAt = 0, myId = 0, lastSec = -1;
export function lobbyMe(id) { myId = id; }
// from the welcome, the 'lobby' message and every snapshot's round info (r.warm). null / end: the lobby's over
export function lobbyInfo(info) {
  pregameSync(info); // the pre-game deck (pregame.js)
  if (!info || info.end) { if (L) { L = null; $('lobbyBox').classList.add('hidden'); } return; }
  const fresh = !L;
  L = info; gotAt = performance.now();
  if (fresh) { lastSec = -1; $('lobbyBox').classList.remove('hidden'); }
  render();
}
export const lobbyOn = () => !!L;
export function lobbyLeave() { pregameSync(null); L = null; $('lobbyBox').classList.add('hidden'); }
function toggleReady() { if (L) opts.send({ t: 'ready', on: !L.ready.includes(myId) }); }
// the ready key (bindable): true = it was ours
export function lobbyKey(e) {
  if (!L || !K.matches('ready', e)) return false;
  e.preventDefault();
  if (!e.repeat) toggleReady();
  return true;
}
function render() {
  if (!L) return;
  const K0 = LOBBY.kinds[L.k] || LOBBY.kinds.qp;
  const left = Math.max(0, L.left - (performance.now() - gotAt)), s = Math.ceil(left / 1000);
  const map = MAPS[opts.map()] ? MAPS[opts.map()].name : '';
  const game = GAMES[L.game] ? GAMES[L.game].name : K0.name;
  $('lbTitle').textContent = `${L.after ? 'NEXT MATCH' : 'LOBBY'} · ${game.toUpperCase()}${map ? ' on ' + map.toUpperCase() : ''}`;
  $('lbClock').textContent = L.n < L.min ? 'WAITING' : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  $('lobbyBox').classList.toggle('hurry', s <= 5 && L.n >= L.min);
  const mine = L.ready.includes(myId);
  $('lbInfo').textContent = L.n < L.min ? `waiting for players (${L.n}/${L.min}). the countdown starts over till then`
    : `${L.ready.length}/${L.n} ready${L.ready.length === L.n && L.n ? '. here we go' : '. everyone ready = 5 seconds'} · pre-game: nothing hurts. fire = shove`;
  const rb = $('lbReady');
  rb.classList.toggle('on', mine);
  rb.querySelector('span').textContent = mine ? 'READY!' : 'READY UP';
  rb.querySelector('i').textContent = K.label('ready');
  if (s !== lastSec) { // the last five: a tick each second, a horn at zero
    if (lastSec !== -1 && s <= 5 && s > 0 && L.n >= L.min) synth.tone('square', 880, 880, 0.07, 0.12);
    if (lastSec > 0 && s === 0 && L.n >= L.min) synth.tone('sawtooth', 220, 440, 0.4, 0.2);
    lastSec = s;
  }
}
setInterval(render, 200);
