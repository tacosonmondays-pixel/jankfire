// OVERDUE (story mode) on the client: the STORY button, the save-slot picker, starting a solo run in the story worker
// (host.js), the Machine terminal that drops you into the normal PLAY menu and brings you back, and saving.
// HIDDEN behind a flag until the owner approves the slice: only loaded when the url has ?story=1 or localStorage
// jfStory=1 (main.js checks, then imports this). without it, nothing here runs and the menu is untouched.
//
// for other lanes: G.story is the client-side story api while a run is on:
//   G.story.on(kind, fn)    listen to the sim's { t: 'sty', k: kind } messages (many listeners per kind)
//   G.story.send(kind, o)   tell the sim something ({ t: 'sty', k: kind, ...o })
//   G.story.save(why)       ask the sim for a snapshot and store it (server slot if logged in, else this browser)
//   G.story.cur             the last save we hold { v, slot, act, chapter, playtime, coupons, at, data }
//   G.story.active()        true while you're in the story world (not in a sim match, not in a menu)
import { G } from '../ctx.js';
import { net } from '../net.js';
import { K } from '../keys.js';
import { hud } from '../hud.js';
import { ME } from '../player.js';
import { account } from '../account.js';
import { organic } from '../organic.js';
import { MAPS, builder, horizon, rng, lollipop, conifer, unstick } from '/shared/map.js';
import { TEST, buildTestMap } from '/shared/story/testmap.js';
import { newSave, saveCard, SAVE } from '/shared/story/save.js';
import { WorkerSocket } from './host.js';

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const LOCAL = 'jfStorySaves', BACK = 'jfStoryBack';
const listeners = {};
let pausedWas = false, api = null, picker = null, hint = null, cur = null, useWas = false, autoT = 0, pendingSave = null, lastPost = 0;

export function initStory(a) {
  api = a; // { startMode(mode, cfg, mkSocket), quitToMenu(), toast(text, ms) }
  if (!MAPS[TEST.id]) { const m = buildTestMap({ builder, horizon, rng, lollipop, conifer }); unstick(m.boxes, m.spawns); MAPS[TEST.id] = m; } // client only: never in MAP_ORDER, so no menu lists it
  import('../city/storymap.js').then((m) => m.registerStoryMaps(MAPS)).catch(() => {}); // the world lane's streamed city (story_slice)
  css();
  button();
  net.on('sty', (m) => { const fs = listeners[m.k]; if (fs) for (const f of fs) f(m); });
  G.story = { on, send, save, active, tick, onMain, get cur() { return cur; } };
  on('hello', (m) => { ME.yaw = m.yaw || 0; hud.msg('OVERDUE', 2.2, 'brag'); });
  on('saved', (m) => stored(m.save));
  on('redispensed', () => hud.msg('BEEP. CLUNK. RESTOCKING FEE APPLIED.', 2.2, 'brag'));
}
function on(k, fn) { (listeners[k] ||= []).push(fn); }
function send(k, o) { net.send({ t: 'sty', k, ...o }); }
function active() { return !!(G.joined && G.mode === 'story' && $('menu').classList.contains('hidden')); }

// ------------------------------------------------------------ the STORY button + slot picker
function button() {
  const right = document.querySelector('#scr-main .home-right');
  if (!right || $('storyBtn')) return;
  const b = el('button', 'big mode story');
  b.id = 'storyBtn';
  b.append(el('b', null, 'STORY'), el('span', null, 'OVERDUE: the city after the end of the world'));
  right.insertBefore(b, right.firstChild);
  organic(b, { rim: 5, wet: false, veins: false, lumps: 4, lumpA: 3.2, shadow: [6, 6], bandL: 12 });
  b.addEventListener('click', () => openPicker());
  label();
}
function label() {
  const b = $('storyBtn');
  if (!b) return;
  b.querySelector('b').textContent = back() ? 'BACK TO THE CITY' : 'STORY';
}
const back = () => { try { return JSON.parse(sessionStorage.getItem(BACK) || 'null'); } catch { return null; } };
const setBack = (v) => { try { if (v) sessionStorage.setItem(BACK, JSON.stringify(v)); else sessionStorage.removeItem(BACK); } catch { /* fine */ } label(); };

function localSaves() { try { const a = JSON.parse(localStorage.getItem(LOCAL) || '[]'); return Array.isArray(a) ? a : []; } catch { return []; } }
async function api2(path, body) {
  const r = await fetch('/api/story/' + path, { method: 'POST', headers: { 'content-type': 'application/json', authorization: 'Bearer ' + account.token }, body: JSON.stringify(body || {}) });
  let d = {};
  try { d = await r.json(); } catch { /* empty */ }
  if (!r.ok) throw new Error(d.error || 'request failed');
  return d;
}
async function listSlots() {
  if (account.loggedIn) { try { return { ...(await api2('list')), where: 'server' }; } catch (e) { return { slots: 0, saves: [], where: 'server', error: e.message }; } }
  const l = localSaves();
  return { slots: SAVE.slots, saves: Array.from({ length: SAVE.slots }, (_, i) => saveCard(l[i] || null)), where: 'local' };
}
async function loadSlot(slot) {
  if (account.loggedIn) return (await api2('load', { slot })).save;
  return localSaves()[slot] || null;
}

async function openPicker() {
  const bk = back();
  if (bk && cur && cur.slot === bk.slot) { setBack(null); return start(cur); } // back from a sim: same spot
  if (bk) setBack(null); // (a reload lost the run we were holding: just pick again)
  if (!picker) {
    picker = el('div', 'st-pick hidden');
    picker.id = 'storyPick';
    document.body.append(picker);
  }
  picker.innerHTML = '';
  const panel = el('div', 'st-panel');
  panel.append(el('h2', null, 'OVERDUE'), el('p', 'st-sub', 'pick a save slot. the machine remembers.'));
  const list = el('div', 'st-slots');
  panel.append(list);
  list.append(el('p', 'st-sub', 'checking the receipts...'));
  const close = el('button', 'st-btn', 'BACK');
  close.addEventListener('click', () => picker.classList.add('hidden'));
  panel.append(close);
  picker.append(panel);
  picker.classList.remove('hidden');
  const L = await listSlots();
  list.innerHTML = '';
  if (L.error) list.append(el('p', 'st-sub', `couldn't get your saves (${L.error}).`));
  for (let i = 0; i < SAVE.slots; i++) {
    const c = L.saves[i], open = i < L.slots;
    const card = el('div', 'st-slot' + (open ? '' : ' locked'));
    card.append(el('b', null, `SLOT ${i + 1}`));
    if (!open) card.append(el('span', null, 'locked: needs a server update'));
    else if (!c) card.append(el('span', null, 'empty. a fresh body, still in the wrapper.'));
    else card.append(el('span', null, `ACT ${c.act} · ${c.chapter.replace(/_/g, ' ')} · ${Math.floor(c.playtime / 60)} min · ${c.coupons} coupons`));
    if (open) {
      const go = el('button', 'st-btn yellow', c ? 'CONTINUE' : 'NEW GAME');
      go.addEventListener('click', async () => {
        go.disabled = true;
        try { const s = c ? await loadSlot(i) : null; picker.classList.add('hidden'); start(s || newSave(i)); }
        catch (e) { go.disabled = false; api.toast(`couldn't load that slot: ${e.message}`, 3000); }
      });
      card.append(go);
    }
    list.append(card);
  }
  list.append(el('p', 'st-sub', L.where === 'local' ? 'not logged in: saves stay in this browser.' : L.slots < SAVE.slots ? 'saves are on your account (1 slot until the server update).' : 'saves are on your account.'));
}

function start(save) {
  cur = save;
  autoT = performance.now();
  api.startMode('story', undefined, () => new WorkerSocket(save));
}

// ------------------------------------------------------------ saving
function save(why) { if (G.joined && G.mode === 'story') { pendingSave = why || 'manual'; send('save', { why: pendingSave }); } }
async function stored(s) {
  if (!s) return;
  cur = s;
  const why = pendingSave; pendingSave = null;
  const l = localSaves(); l[s.slot] = s; // a local copy always (guests: the only copy)
  try { localStorage.setItem(LOCAL, JSON.stringify(l)); } catch { /* full */ }
  if (!account.loggedIn) return;
  const quiet = why === 'auto' || why === 'pause';
  if (performance.now() - lastPost < SAVE.minGap + 200 && quiet) return; // the server takes 1 per 10 s
  lastPost = performance.now();
  try { await api2('save', { slot: s.slot, save: s }); } catch (e) { if (!quiet) api.toast(`save failed: ${e.message}`, 3000); }
}

// ------------------------------------------------------------ every frame (main.js calls this)
function tick() {
  const bk = back();
  if (bk && bk.state === 'menu' && G.joined && G.mode !== 'story') setBack({ ...bk, state: 'sim' }); // you picked a sim
  const on = active() && ME.alive;
  const near = on && Math.hypot(ME.pos[0] - TEST.terminal.p[0], ME.pos[2] - TEST.terminal.p[2]) < TEST.terminal.r;
  if (!hint) { hint = el('div', 'st-hint hidden'); document.body.append(hint); }
  hint.textContent = `${K.label('use')} · ENTER THE SIMS`;
  hint.classList.toggle('hidden', !near);
  const use = on && K.isDown('use');
  if (near && use && !useWas) terminal();
  useWas = use;
  if (on && performance.now() - autoT > 60000) { autoT = performance.now(); save('auto'); }
  const paused = G.joined && G.mode === 'story' && !$('menu').classList.contains('hidden');
  if (paused && !pausedWas) save('pause'); // the pause menu is where you quit from: keep the spot
  pausedWas = paused;
}
let toSim = false;
function terminal() {
  if (toSim) return; // (one press, one trip)
  toSim = true;
  pendingSave = 'terminal';
  const off = () => { toSim = false; const i = listeners.saved.indexOf(go); if (i >= 0) listeners.saved.splice(i, 1); };
  const go = () => { off(); setBack({ slot: cur.slot, state: 'menu' }); api.quitToMenu(); api.toast('the machine hums. pick a sim. leave it to come back.', 3500); };
  on('saved', go);
  send('save', { why: 'terminal' });
}
// main.js: the main menu is about to show. true = we took over (back from a sim match: straight into the city)
function onMain() {
  const bk = back();
  if (!bk || bk.state !== 'sim' || G.joined || !cur || cur.slot !== bk.slot) { label(); return false; }
  setBack(null);
  start(cur);
  return true;
}

// ------------------------------------------------------------ looks (the zine style: CLAUDE.md "Style details")
function css() {
  const s = document.createElement('style');
  s.textContent = `
.st-pick{position:fixed;inset:0;z-index:60;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.45);font-family:var(--font)}
.st-pick.hidden,.st-hint.hidden{display:none}
.st-panel{background:rgba(18,8,24,.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;padding:22px 26px;width:min(560px,92vw);color:#fff;transform:rotate(-1deg)}
.st-panel h2{margin:0;font-size:46px;color:#ffe14d;letter-spacing:2px;text-shadow:4px 4px 0 #ff00dc}
.st-sub{margin:4px 0 12px;opacity:.85}
.st-slots{display:flex;flex-direction:column;gap:12px;margin-bottom:14px}
.st-slot{display:grid;grid-template-columns:90px 1fr auto;align-items:center;gap:10px;border:3px solid #000;background:#2a1030;box-shadow:5px 5px 0 #ff4fd8;padding:10px 12px}
.st-slot:nth-child(2){transform:rotate(.6deg)}
.st-slot.locked{opacity:.5}
.st-slot b{color:#4fd8ff;font-size:20px}
.st-btn{font-family:var(--font);font-weight:700;font-size:18px;border:3px solid #000;background:#fff;color:#000;padding:6px 14px;box-shadow:4px 4px 0 #000;cursor:pointer}
.st-btn.yellow{background:#ffe14d;box-shadow:4px 4px 0 #ff4fd8;transform:rotate(-2deg)}
.st-btn:disabled{opacity:.5}
.st-hint{position:fixed;left:50%;top:62%;transform:translateX(-50%) rotate(-1.5deg);z-index:20;font-family:var(--font);font-weight:700;font-size:22px;color:#000;background:#ffe14d;border:3px solid #000;box-shadow:5px 5px 0 #ff4fd8;padding:6px 14px;pointer-events:none}
`;
  document.head.append(s);
}
