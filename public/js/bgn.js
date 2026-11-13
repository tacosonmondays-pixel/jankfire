// BOARD GAME NIGHT: the client (docs/party/DESIGN.md 5). the server sends the board ({ t: 'bg', k: 'st' }) and small
// events; this draws the comic HUD over the board scene (bgnscene.js): four seat cards, ROUND n/N, the ROLL button,
// the choices, the CORNER STORE, callouts, the minigame cards and the results. clicks send choices only ({ t: 'bg', k }).
// while the board is up (everything but a minigame you're in) main.js draws the board instead of the map and lets go
// of the mouse (bgnBoardOn / bgnFrame).
import { G } from './ctx.js';
import { ME } from './player.js';
import { net } from './net.js';
import { synth } from './audio.js';
import { BGN, BGN_NAMES as N, BGN_ITEMS, BGN_JANK, BGN_HOUSE, BGN_MINIS, bgnFill } from '/shared/bgn.js';
import { BOARD, aheadSet } from '/shared/bgnboard.js';
import { miniState, miniEv, miniFrame, miniCtl, miniIntro, miniRes } from './bgnmini.js'; // minigames 11-15: carts, ducks, the bosses

let B = null, board = null, boardP = null, root = null, ui = null, opts = {}, aim = null, askT = 0, askDur = 1, lastAsk = '', wasOn = false, cardT = 0, t0 = performance.now();
const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const send = (o) => net.send({ t: 'bg', ...o });
const mine = () => (B ? B.seats.find((s) => s.id === G.myId) || null : null);
const seatName = (i) => (B && B.seats[i] ? B.seats[i].name : '?');
const tone = (...a) => { try { synth.tone(...a); } catch { /* no audio yet */ } };
const noise = (...a) => { try { synth.noise(...a); } catch { /* no audio yet */ } };
// sounds: cartoonish and short (Web Audio, like everything in audio.js)
const SFX = {
  rattle() { for (let i = 0; i < 6; i++) noise(0.04, 0.35, 'bandpass', 1800 + i * 300, 900, null, i * 0.07, 3); },
  thunk() { tone('sine', 140, 60, 0.18, 0.5); noise(0.06, 0.4, 'lowpass', 900, 300); },
  hop() { tone('square', 620, 880, 0.06, 0.08); },
  chime() { tone('triangle', 1320, 1320, 0.09, 0.18); tone('triangle', 1760, 1760, 0.14, 0.16, null, 0.08); },
  trombone() { for (let i = 0; i < 3; i++) tone('sawtooth', 300 - i * 30, 290 - i * 30, 0.28, 0.13, null, i * 0.3); tone('sawtooth', 210, 150, 0.8, 0.13, null, 0.9); },
  slap() { noise(0.08, 0.7, 'highpass', 2000, 800); tone('square', 220, 90, 0.1, 0.2); },
  pop() { tone('square', 300, 1200, 0.12, 0.2); noise(0.05, 0.4, 'bandpass', 3000, 1500); },
  big() { tone('square', 440, 660, 0.12, 0.18); tone('square', 660, 990, 0.18, 0.18, null, 0.12); },
  click() { tone('square', 500, 500, 0.03, 0.08); },
};
G.bgnHop = () => SFX.hop();
G.bgnThunk = () => SFX.thunk();

export function initBgn(o) { opts = o || {}; } // { lobby() } from main.js
export const bgnOn = () => !!B && !!G.joined;
// is the board what you see? (everything but a minigame you're playing in)
export function bgnBoardOn() {
  if (!bgnOn()) return false;
  const s = mine();
  return !(B.ph === 'mg' && s && B.mg && B.mg.seats.includes(s.i));
}
// the end screen's PLAY AGAIN / LOBBY (server/hubback.js), on the toasting card
let back = null;
export function bgnHubBack(m) {
  if (m.k === 'open') back = { again: false, n: 0, of: 0 };
  else if (m.k === 'again' && back) { back.n = m.n | 0; back.of = m.of | 0; }
  render();
}
export function bgnReset() { back = null; B = null; miniState(null); aim = null; if (root) root.classList.add('hidden'); document.body.classList.remove('bgn-board'); wasOn = false; }
// main.js's frame: true = the board was drawn (instead of the map)
export function bgnFrame(dt) {
  if (B) miniFrame(dt); // (the minigames' HUD + ducks, board up or not)
  const on = bgnBoardOn();
  if (on !== wasOn) {
    wasOn = on;
    document.body.classList.toggle('bgn-board', on);
    if (root) root.classList.toggle('hidden', !on && !(B && B.ph === 'mg'));
    if (on) { ME.alive = false; if (document.pointerLockElement) document.exitPointerLock(); }
    render();
  }
  if (!on) return false;
  if (!board) { loadBoard(); return false; }
  tickUi();
  board.frame(dt, (performance.now() - t0) / 1000);
  return true;
}
function loadBoard() {
  if (boardP) return;
  boardP = import('./bgnscene.js').then((m) => { board = m.makeBoard(); if (B) board.sync(B); }).catch((e) => { console.error('board scene', e); boardP = null; });
}

// ---------------------------------------------------------------- messages
net.on('bg', (m) => {
  if (!m || typeof m.k !== 'string') return;
  if (m.k === 'st') { const was = B; B = m.s; if (!B) { bgnReset(); return; } miniState(B); ensureDom(); loadBoard(); if (board) board.sync(B); onState(was); render(); return; }
  if (!B) return;
  const fx = EV[m.k];
  if (fx) fx(m);
  else miniEv(m); // minigames 11-15 (bgnmini.js)
});
const EV = {
  roll(m) { if (board) board.roll(m); SFX.rattle(); setTimeout(() => call(`${m.n}`, B.seats[m.seat] && B.seats[m.seat].color, m.stuck ? 'STUCK: HALF' : m.v.length > 1 ? m.v.join(' + ') : 'ROLLED'), 950); },
  step(m) { if (board) board.step(m); },
  dibs(m) { call(N.call.dibs, '#ffe14d', m.rolls.map(([i, v]) => `${seatName(i)} ${v.join('/')}`).join(' · ')); },
  cash(m) { float(m.seat, (m.d > 0 ? '+' : '') + m.d, m.d >= 0 ? '#39ff14' : '#ff3030'); if (m.d > 0) SFX.chime(); else if (m.d < 0 && m.why === 'fee') SFX.trombone(); },
  bread(m) { float(m.seat, (m.d > 0 ? '+' : '') + m.d + ' BREAD', '#ffb300'); if (m.d > 0) SFX.big(); },
  call(m) {
    const t = N.call[m.c];
    if (!t) return;
    const s = m.seat != null ? B.seats[m.seat] : null;
    if (m.c === 'yourTurn') { if (s && s.id === G.myId) { call(N.call.yourTurn, '#ffe14d'); SFX.big(); } return; }
    call(bgnFill(t, m), s ? s.color : '#ffe14d', s ? s.name : '');
    if (m.c === 'duel' || m.c === 'lasso') SFX.slap();
    if (m.c === 'toast') SFX.pop();
  },
  say(m) { const h = $('bgHost'); if (h) { h.textContent = `${N.host}: "${m.line}"`; h.classList.remove('pop'); void h.offsetWidth; h.classList.add('pop'); } },
  jank(m) { const e = BGN_JANK[m.e]; if (e) call(e.name, '#ff00dc', e.desc); SFX.big(); },
  broke(m) { call(bgnFill(N.call.broke, m).toUpperCase(), '#ff3030', seatName(m.seat)); },
  duel(m) { call(N.call.duel, '#ff3030', `${seatName(m.a)} VS ${seatName(m.b)} · ${N.stake[m.stake]}`); },
  house(m) { const h = BGN_HOUSE[m.i]; if (h) call(h.name, '#ff3030', `${seatName(m.seat)} picked it. ${h.desc}`); },
  use(m) { const it = BGN_ITEMS[m.it]; if (it) call(it.name, it.color, `${seatName(m.seat)} used it`); },
  buy(m) { const it = BGN_ITEMS[m.it]; if (it) float(m.seat, it.name, it.color); },
  last() { call(N.call.last, '#ff3030', 'coupon spaces pay double'); },
  ducks(m) { if (board) board.mark(m.at); setTimeout(() => board && board.mark(aim ? aim.ids : []), 1500); },
  mg() { SFX.big(); },
  res() { SFX.pop(); },
  cere() { SFX.pop(); },
};

// ---------------------------------------------------------------- the DOM
const CSS = `
#bgnHud{position:fixed;inset:0;pointer-events:none;z-index:45;font-family:var(--font,'Comic Neue',sans-serif);color:#fff}
#bgnHud.hidden{display:none}
body.bgn-board #hud{display:none!important}
#bgnHud .bg-p{background:rgba(18,8,24,0.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;padding:10px 14px}
#bgnHud button{pointer-events:auto;font-family:inherit;font-weight:700;cursor:pointer;border:3px solid #000;background:#fff;color:#111;box-shadow:4px 4px 0 #000;padding:8px 14px;font-size:18px;text-transform:uppercase}
#bgnHud button:active{transform:translate(3px,3px);box-shadow:1px 1px 0 #000}
#bgnHud button:disabled{opacity:.45;cursor:default}
#bgnHud button.bg-main{background:#ffe14d;border:4px solid #000;box-shadow:6px 6px 0 #ff4fd8;font-size:34px;padding:10px 34px;transform:rotate(-2deg)}
#bgnHud button.bg-main:active{transform:rotate(-2deg) translate(3px,3px);box-shadow:2px 2px 0 #ff4fd8}
.bg-seat{position:absolute;width:210px;background:rgba(18,8,24,0.92);border:4px solid #ff4fd8;box-shadow:4px 4px 0 #000;padding:6px 10px 6px 18px;transition:box-shadow .15s}
.bg-seat.on{box-shadow:8px 8px 0 #4fd8ff}
.bg-seat .st{position:absolute;left:0;top:0;bottom:0;width:10px}
.bg-seat b{display:block;font-size:19px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bg-seat .nums{display:flex;gap:12px;align-items:center;font-size:17px;margin-top:2px}
.bg-loaf{display:inline-block;width:22px;height:13px;border-radius:7px 7px 4px 4px;background:#ffb300;border:2px solid #000;margin-right:4px;vertical-align:-1px}
.bg-cpn{display:inline-block;width:16px;height:11px;background:#39ff14;border:2px dashed #000;margin-right:4px;vertical-align:-1px}
.bg-bag{display:flex;gap:4px;margin-top:4px;min-height:18px}
.bg-chip{font-size:11px;font-weight:700;color:#111;padding:1px 5px;border:2px solid #000}
.bg-tag{font-size:11px;background:#8a5a2b;color:#fff;padding:0 4px;margin-left:6px}
.bg-s0{left:14px;top:14px}.bg-s1{right:14px;top:14px}.bg-s2{left:14px;bottom:14px}.bg-s3{right:14px;bottom:14px}
.bg-top{position:absolute;left:50%;top:12px;transform:translateX(-50%);text-align:center}
.bg-round{font-size:28px;font-weight:700;color:#ffe14d;-webkit-text-stroke:1px #000;text-shadow:4px 4px 0 #ff00dc;padding:4px 16px}
.bg-round.lc{color:#ff3030;text-shadow:4px 4px 0 #000}
#bgHost{margin-top:6px;font-size:15px;font-style:italic;color:#ffd6f7;max-width:520px}
#bgHost.pop{animation:bgpop .3s}
.bg-act{position:absolute;left:50%;bottom:22px;transform:translateX(-50%);width:max-content;display:flex;flex-direction:column;align-items:center;gap:10px;max-width:min(760px,96vw)}
.bg-row{display:flex;gap:10px;flex-wrap:wrap;justify-content:center}
.bg-q{font-size:22px;font-weight:700;text-align:center}
.bg-timer{height:8px;width:260px;background:#000;border:2px solid #000}.bg-timer i{display:block;height:100%;background:#ff4fd8}
.bg-wait{font-size:20px;color:#ffd6f7}
.bg-shop{display:flex;gap:12px;flex-wrap:wrap;justify-content:center}
.bg-item{width:180px;background:#fff;color:#111;border:3px solid #000;box-shadow:6px 6px 0 #000;padding:8px;text-align:left;pointer-events:auto;cursor:pointer;transform:rotate(var(--r,0deg))}
.bg-item h4{margin:0 0 4px;font-size:18px}.bg-item p{margin:0;font-size:13px;line-height:1.2}.bg-item em{float:right;font-style:normal;font-weight:700}
.bg-item i{display:block;height:8px;margin:-8px -8px 6px;border-bottom:3px solid #000}
.bg-item.no{opacity:.45;cursor:default}.bg-item .broke{color:#ff3030;font-weight:700}
#bgCall{position:absolute;left:50%;top:38%;transform:translate(-50%,-50%);text-align:center;pointer-events:none}
#bgCall b{display:block;font-size:76px;line-height:1;color:#ffe14d;-webkit-text-stroke:3px #000;text-shadow:6px 6px 0 #ff00dc;white-space:nowrap}
#bgCall span{display:inline-block;margin-top:8px;font-size:20px;background:rgba(18,8,24,0.92);border:3px solid #000;padding:2px 10px}
#bgCall.pop{animation:bgcall 1.6s forwards}
#bgnHud.card #bgCall{top:max(22%,190px)}#bgnHud.card #bgCall b{font-size:44px}#bgnHud.card .bg-card{top:57%}
@keyframes bgcall{0%{transform:translate(-50%,-50%) scale(2.2) rotate(-6deg);opacity:0}10%{transform:translate(-50%,-50%) scale(.9) rotate(2deg);opacity:1}18%{transform:translate(-50%,-50%) scale(1) rotate(-1deg)}80%{opacity:1}100%{opacity:0;transform:translate(-50%,-60%) scale(1)}}
@keyframes bgpop{0%{transform:scale(1.15)}100%{transform:scale(1)}}
.bg-float{position:absolute;font-size:24px;font-weight:700;-webkit-text-stroke:1px #000;text-shadow:3px 3px 0 #000;animation:bgfloat 1.4s forwards;pointer-events:none}
@keyframes bgfloat{0%{transform:translateY(0) scale(1.4)}100%{transform:translateY(-50px);opacity:0}}
.bg-card{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-1deg);width:min(560px,92vw);text-align:center;pointer-events:auto}
.bg-card h2{margin:0;font-size:46px;color:#ffe14d;-webkit-text-stroke:2px #000;text-shadow:5px 5px 0 #ff00dc;line-height:1}
.bg-card .fmt{display:inline-block;margin:10px 0;font-size:20px;font-weight:700;background:#ff4fd8;color:#000;padding:2px 12px;border:3px solid #000}
.bg-card .rule{font-size:19px;margin:6px 0}.bg-card .ctl{font-size:14px;color:#ffd6f7}
.bg-sides{display:flex;gap:8px;justify-content:center;margin:8px 0}.bg-sides div{flex:1;padding:6px;border:3px solid #000;font-weight:700}
.bg-one{font-size:88px;font-weight:700;color:#ff3030;-webkit-text-stroke:3px #000;line-height:1}
.bg-cd{font-size:60px;font-weight:700;color:#4fd8ff;-webkit-text-stroke:2px #000}
.bg-ex{color:#ffd6f7;font-size:14px;font-weight:400}
.bg-res{width:100%;border-collapse:collapse;margin:8px 0;font-size:19px}.bg-res td{padding:3px 6px;border-bottom:2px solid #3a2340}.bg-res td:last-child{text-align:right;font-weight:700}
.bg-spec{position:absolute;left:50%;top:70px;transform:translateX(-50%);font-size:20px;font-weight:700}
.bg-view{position:absolute;right:14px;top:50%;transform:translateY(-50%)}
#bgnHud .bg-view button{font-size:13px;padding:4px 8px}
@media (max-width:640px){
 .bg-seat{width:calc(25vw - 8px);padding:3px 4px 3px 10px;border-width:3px}.bg-seat .st{width:6px}
 .bg-seat b{font-size:12px}.bg-seat .nums{font-size:12px;gap:4px;flex-wrap:wrap}.bg-bag{min-height:0}.bg-chip{font-size:9px;padding:0 2px}
 .bg-s0{left:4px;top:4px}.bg-s1{left:calc(25vw + 2px);right:auto;top:4px}.bg-s2{left:calc(50vw + 0px);top:4px;bottom:auto}.bg-s3{left:calc(75vw - 2px);right:auto;top:4px;bottom:auto}
 .bg-top{top:auto;bottom:auto;top:96px;width:94vw}.bg-round{font-size:20px}#bgHost{font-size:12px}
 #bgCall b{font-size:44px}#bgCall span{font-size:14px}
 .bg-item{width:calc(50vw - 24px)}.bg-item p{font-size:11px}
 #bgnHud button.bg-main{font-size:28px}
 .bg-card h2{font-size:32px}.bg-view{top:auto;bottom:160px}
 #bgnHud.card #bgCall{top:auto;bottom:4%}
}`;
function ensureDom() {
  if (root) return;
  const st = el('style'); st.textContent = CSS; document.head.append(st);
  root = el('div'); root.id = 'bgnHud'; root.className = 'hidden';
  ui = el('div'); const top = el('div', 'bg-top'), rd = el('div', 'bg-round bg-p'), host = el('div'), cl = el('div');
  rd.id = 'bgRound'; host.id = 'bgHost'; cl.id = 'bgCall'; top.append(rd, host);
  root.append(ui, top, cl); // (the callout and the host's line outlive every redraw)
  document.body.append(root);
  addEventListener('pointerdown', (e) => { if (aim && bgnBoardOn() && !(e.target instanceof Element && e.target.closest('button,.bg-item'))) boardClick(e); });
  addEventListener('keydown', (e) => {
    if (!bgnBoardOn() || e.repeat || !$('menu').classList.contains('hidden')) return;
    if ((e.code === 'Space' || e.code === 'Enter') && askMine('roll') && !aim) { e.preventDefault(); SFX.click(); send({ k: 'roll' }); }
    else if (e.code === 'KeyV') { topView = !topView; if (board) board.topDown(topView); }
    else if (e.code === 'Escape' && aim) { aim = null; if (board) board.mark([]); render(); }
  });
}
let topView = false;
const askMine = (k) => { const s = mine(); return !!(s && B.ask && B.ask.seat === s.i && (!k || B.ask.k === k)); };
function onState(was) {
  const key = B.ask ? `${B.ask.k}:${B.ask.seat}:${B.round}:${B.turn}:${B.ph}` : '';
  if (key !== lastAsk) { lastAsk = key; askT = B.ask ? performance.now() + B.ask.left : 0; askDur = B.ask ? Math.max(1, B.ask.left) : 1; if (aim && !askMine('roll')) { aim = null; if (board) board.mark([]); } }
  if (B.card) cardT = performance.now() + B.card;
  if (board && B.walk) board.focus(B.walk.seat); else if (board && B.ask) board.focus(B.ask.seat);
  if (was && was.ph !== B.ph && B.ph === 'mg' && !bgnBoardOn()) { if (root) root.classList.add('hidden'); }
  if (B.ph !== 'mg' && G.joined) ME.alive = false;
}
function call(big, color, small) {
  const c = $('bgCall');
  if (!c) return;
  c.innerHTML = '';
  const b = el('b', null, big); if (color) b.style.color = color;
  c.append(b);
  if (small) c.append(el('br'), el('span', null, small));
  c.classList.remove('pop'); void c.offsetWidth; c.classList.add('pop');
}
function float(seat, text, color) {
  const card = root && root.querySelector(`.bg-s${seat}`);
  if (!card) return;
  const r = card.getBoundingClientRect(), f = el('div', 'bg-float', text);
  f.style.left = `${r.left + r.width / 2 - 20}px`; f.style.top = `${r.top + (seat < 2 ? r.height : -30)}px`; f.style.color = color;
  root.append(f); setTimeout(() => f.remove(), 1500);
}
function tickUi() {
  const bar = root && root.querySelector('.bg-timer i');
  if (bar && B && B.ask) bar.style.width = `${Math.max(0, Math.min(100, ((askT - performance.now()) / askDur) * 100))}%`;
  const cd = root && root.querySelector('.bg-cd');
  if (cd) cd.textContent = String(Math.max(0, Math.ceil((cardT - performance.now()) / 1000)));
}

// ---------------------------------------------------------------- drawing the HUD
function render() {
  if (!root || !B) return;
  const on = bgnBoardOn();
  root.classList.toggle('hidden', !on);
  if (!on) return;
  root.classList.toggle('card', B.ph === 'mgintro' || B.ph === 'mgres' || B.ph === 'done' || (askMine() && (B.ask.k === 'shop' || B.ask.k === 'house'))); // (big panels up: callouts move out of the way)
  ui.innerHTML = '';
  const me = mine(), active = B.ask ? B.ask.seat : B.walk ? B.walk.seat : -1;
  for (const s of B.seats) {
    const c = el('div', `bg-seat bg-s${s.i}` + (s.i === active ? ' on' : ''));
    const stripe = el('i', 'st'); stripe.style.background = s.color; c.append(stripe);
    const nm = el('b', null, (s.id === G.myId ? '★ ' : '') + s.name + (s.bot ? ' (bot)' : '')); nm.style.color = s.color; c.append(nm);
    const nums = el('div', 'nums');
    const br = el('span'); br.append(el('i', 'bg-loaf'), String(s.b));
    const cp = el('span'); cp.append(el('i', 'bg-cpn'), String(s.c));
    nums.append(br, cp);
    if (s.stuck) nums.append(el('span', 'bg-tag', 'STUCK'));
    c.append(nums);
    const bag = el('div', 'bg-bag');
    for (const it of s.bag) { const ch = el('span', 'bg-chip', BGN_ITEMS[it].name.split(' ').pop()); ch.style.background = BGN_ITEMS[it].color; ch.title = BGN_ITEMS[it].desc; bag.append(ch); }
    c.append(bag);
    ui.append(c);
  }
  const rd = $('bgRound');
  rd.className = 'bg-round bg-p' + (B.lc ? ' lc' : ''); rd.textContent = B.ph === 'done' ? N.toast : B.lc ? `${N.last} · ROUND ${Math.min(B.round, B.rounds)}/${B.rounds}` : `ROUND ${Math.min(B.round, B.rounds)}/${B.rounds}`;
  const vw = el('div', 'bg-view'), vb = el('button', null, topView ? 'TABLE VIEW [V]' : 'TOP VIEW [V]');
  vb.addEventListener('click', () => { topView = !topView; if (board) board.topDown(topView); render(); }); vw.append(vb); ui.append(vw);
  if (B.ph === 'mg' && B.mg) { // you're on the bench: who's playing
    ui.append(el('div', 'bg-spec bg-p', `${BGN_MINIS[B.mg.id].name}: ${B.mg.seats.map(seatName).join(' VS ')}`));
  }
  if (B.ph === 'mgintro' && B.mg) ui.append(introCard());
  else if (B.ph === 'mgres' && B.res) ui.append(resCard());
  else if (B.ph === 'done' && B.final) ui.append(finalCard());
  else ui.append(actions(me));
}
function actions(me) {
  const box = el('div', 'bg-act');
  const a = B.ask;
  if (!a) return box;
  const s = B.seats[a.seat], minePick = me && a.seat === me.i;
  if (!minePick) {
    const verb = { roll: 'is rolling', path: 'is picking a path', bread: 'is eyeing the golden bread', shop: 'is shopping', stake: 'is picking the stake', who: 'is picking a fight', house: 'is picking a house rule' }[a.k] || 'is thinking';
    const w = el('div', 'bg-wait bg-p', `${s.name} ${verb}...`); w.style.borderColor = s.color;
    box.append(w);
    return box;
  }
  const q = (t) => box.append(el('div', 'bg-q bg-p', t));
  const btn = (t, fn, cls) => { const b = el('button', cls || '', t); b.addEventListener('click', () => { SFX.click(); fn(); }); return b; };
  const row = (...b) => { const r = el('div', 'bg-row'); r.append(...b); box.append(r); return r; };
  if (a.k === 'roll') {
    if (aim) {
      q(aim.label);
      if (aim.seats) row(...aim.seats.map((i) => btn(seatName(i), () => useIt(aim.it, i))));
      row(btn('CANCEL', () => { aim = null; if (board) board.mark([]); render(); }));
    } else {
      if (!B.used && me.bag.length) row(...me.bag.map((it) => { const b = btn('USE ' + BGN_ITEMS[it].name, () => startUse(it)); b.style.background = BGN_ITEMS[it].color; b.title = BGN_ITEMS[it].desc; return b; }));
      row(btn(N.call.roll + (B.cart ? ' x2' : ''), () => send({ k: 'roll' }), 'bg-main'));
    }
  } else if (a.k === 'path') {
    q('FORK IN THE ROAD');
    row(btn(N.path[0], () => send({ k: 'path', i: 0 })), btn(N.path[1] + ' (sticky)', () => send({ k: 'path', i: 1 })));
  } else if (a.k === 'bread') {
    q(`BUY ${N.bread}? ${B.price} ${N.coupons}`);
    row(btn('YES', () => send({ k: 'bread', yes: true }), 'bg-main'), btn('NO', () => send({ k: 'bread', yes: false })));
  } else if (a.k === 'shop') {
    q(N.store);
    const shop = el('div', 'bg-shop');
    a.opts.forEach((it, k) => {
      const I = BGN_ITEMS[it], can = me.c >= I.cost && me.bag.length < BGN.bagMax;
      const c = el('div', 'bg-item' + (can ? '' : ' no')); c.style.setProperty('--r', `${(k - 1) * 1.5}deg`);
      const bar = el('i'); bar.style.background = I.color; c.append(bar);
      const h = el('h4', null, I.name); h.append(el('em', null, `${I.cost}`)); c.append(h, el('p', null, I.desc));
      if (!can) c.append(el('p', 'broke', me.bag.length >= BGN.bagMax ? 'bag full' : 'broke'));
      if (can) c.addEventListener('click', () => { SFX.click(); send({ k: 'buy', it }); });
      shop.append(c);
    });
    box.append(shop);
    row(btn('LEAVE', () => send({ k: 'buy', it: null })));
  } else if (a.k === 'stake') {
    q('WHAT ARE WE FIGHTING FOR');
    row(...a.opts.map((o) => btn(N.stake[o] + (o === 'bread' ? ` (costs ${BGN.duelFee})` : ''), () => send({ k: 'stake', s: o }))));
  } else if (a.k === 'who') {
    q('WHO ARE WE FIGHTING');
    row(...a.opts.map((i) => btn(seatName(i), () => send({ k: 'who', seat: i }))));
  } else if (a.k === 'house') {
    q(`${N.last}: PICK A HOUSE RULE`);
    const shop = el('div', 'bg-shop');
    BGN_HOUSE.forEach((h, i) => { const c = el('div', 'bg-item'); c.append(el('h4', null, h.name), el('p', null, h.desc)); c.addEventListener('click', () => { SFX.click(); send({ k: 'house', i }); }); shop.append(c); });
    box.append(shop);
  }
  const t = el('div', 'bg-timer'); t.append(el('i')); box.append(t);
  return box;
}
// items that need a target: a space on the board (click it) or a seat (buttons)
function startUse(it) {
  const me = mine(), I = BGN_ITEMS[it];
  if (!I.to) { useIt(it, null); return; }
  if (I.to === 'seat') { aim = { it, seats: B.seats.filter((s) => s.i !== me.i).map((s) => s.i), label: `${I.name}: WHO?` }; render(); return; }
  const traps = new Set(B.traps.map((t) => t[0]));
  const ids = it === 'sign' ? [...aheadSet(me.at, BGN.signRange)].filter((id) => !traps.has(id)) : BOARD.filter((sp) => sp.k === 'c' && !traps.has(sp.id) && sp.id !== B.bakery).map((sp) => sp.id);
  aim = { it, ids, label: `${I.name}: CLICK A GLOWING SPACE` };
  if (board) board.mark(ids);
  render();
}
function useIt(it, to) { send({ k: 'use', it, to }); aim = null; if (board) board.mark([]); render(); }
function boardClick(e) {
  if (!aim || !aim.ids || !board) return;
  const id = board.pick(e.clientX, e.clientY);
  if (id != null && aim.ids.includes(id)) { SFX.click(); useIt(aim.it, id); }
}
function okBtn() { const b = el('button', 'bg-main', 'OK'); b.addEventListener('click', () => { SFX.click(); send({ k: 'ok' }); b.disabled = true; b.textContent = 'WAITING...'; }); return b; }
function introCard() {
  const mg = B.mg, def = BGN_MINIS[mg.id], c = el('div', 'bg-card bg-p');
  c.append(el('div', 'ctl', N.call.mg), el('h2', null, def.name), el('div', 'fmt', N.fmt[mg.fmt] || mg.fmt));
  if (mg.fmt === '2v2' && mg.sides) {
    const sd = el('div', 'bg-sides');
    mg.sides.forEach((side, k) => { const d = el('div', null, side.map(seatName).join(' + ')); d.style.background = k ? '#4fa8ff' : '#ff4f4f'; sd.append(d); });
    c.append(sd);
  } else if (mg.fmt === '3v1' && mg.one != null) c.append(el('div', 'bg-one', '1'), el('div', 'rule', `${seatName(mg.one)} vs everyone`));
  else if ((mg.fmt === 'duel' || mg.fmt === 'tie') && mg.seats) c.append(el('div', 'rule', mg.seats.map(seatName).join(' VS ') + (mg.stake ? ` · ${N.stake[mg.stake]}` : '')));
  const art = miniIntro(mg); if (art) c.append(art); // (a boss: his name in big)
  c.append(el('div', 'rule', def.rule), el('div', 'ctl', miniCtl(def)), el('div', 'bg-cd', ''));
  const me = mine();
  if (me && mg.seats.includes(me.i)) c.append(okBtn()); else c.append(el('div', 'ctl', 'you sit this one out. watch the board'));
  return c;
}
function resCard() {
  const r = B.res, c = el('div', 'bg-card bg-p'), def = BGN_MINIS[r.id], pay = new Map(r.pay || []);
  c.append(el('h2', null, 'RESULTS'), el('div', 'fmt', `${def.name} · ${N.fmt[r.fmt] || r.fmt}`));
  const t = el('table', 'bg-res');
  let order = r.place || r.seats;
  if (r.winSide >= 0 && r.sides) order = [...r.sides[r.winSide], ...r.sides[1 - r.winSide]];
  if (r.fmt === 'duel' && r.win == null) c.append(el('div', 'rule', N.call.hung));
  if (r.fmt === 'boss' && N.boss[r.id]) { const b = el('div', 'rule', r.winSide === 0 ? `${N.call.bossDown}: ${N.boss[r.id].down}` : N.boss[r.id].loss); b.style.cssText = 'font-size:26px;font-weight:700;color:' + (r.winSide === 0 ? '#39ff14' : '#ff3030'); c.append(b); }
  order.forEach((i, k) => {
    const tr = el('tr'), s = B.seats[i], d = pay.get(i);
    const win = r.win === i || (r.winSide >= 0 && r.sides[r.winSide].includes(i)) || (r.fmt === 'ffa' && k === 0);
    const nm = el('td', null, (win ? '★ ' : '') + s.name); nm.style.color = s.color;
    const ex = miniRes(r, i); if (ex) nm.append(el('small', 'bg-ex', `  ${ex}`)); // (boss damage, ducks, falls)
    tr.append(el('td', null, r.fmt === 'ffa' ? `${k + 1}.` : ''), nm, el('td', null, d != null ? `${d > 0 ? '+' : ''}${d}${r.stake === 'bread' ? ' bread' : ''}` : ''));
    t.append(tr);
  });
  c.append(t, okBtn());
  return c;
}
function finalCard() {
  const f = B.final, c = el('div', 'bg-card bg-p'), w = B.seats[f.win];
  const h = el('h2', null, N.call.toast); c.append(h);
  const wn = el('div', 'rule', `${w.name} wins ${N.mode.toLowerCase()}`); wn.style.color = w.color; wn.style.fontSize = '26px'; c.append(wn);
  const t = el('table', 'bg-res');
  f.place.forEach(([i, b, cp], k) => { const tr = el('tr'), s = B.seats[i], nm = el('td', null, s.name); nm.style.color = s.color; tr.append(el('td', null, `${k + 1}.`), nm, el('td', null, `${b} bread · ${cp} coupons`)); t.append(tr); });
  c.append(t);
  const lb = el('button', null, 'LOBBY'); lb.addEventListener('click', () => { SFX.click(); if (opts.lobby) opts.lobby(); });
  const r = el('div', 'bg-row');
  if (back) { const pa = el('button', 'bg-main', back.again ? `PLAYING AGAIN ✓${back.of > 1 ? ` ${back.n}/${back.of}` : ''}` : 'PLAY AGAIN'); pa.addEventListener('click', () => { SFX.click(); back.again = !back.again; net.send({ t: 'hbagain', on: back.again }); render(); }); r.append(pa); }
  r.append(lb); c.append(r);
  return c;
}
