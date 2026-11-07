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
import { worldOf, DEFAULT_WORLD } from '/shared/story/worlds.js';
import * as THREE from 'three';
// ?storytest=1: new games start on the test lot (the e2e tests), not in the Bottom
const testLot = () => { try { return new URLSearchParams(location.search).get('storytest') === '1'; } catch { return false; } };
import { storyKeys, initBar, barTick, barShow, useBar, dropHeld, nearestDrop, atLocker, clearDrops } from './bar.js'; // WP3
import { openWheel, closeWheel, wheelOpen, wheelLook, wheelScale } from './wheel.js';
import { initBag, toggleBag, bagOpen } from './bag.js';
import { infoOf, count } from '/shared/story/items.js';
import { IV as IVref } from './bar.js';
import { LOOT_CSS } from './lootfx.js';
import { initDrive, driveStep, driveTick, driving, tryEnter, endDrive, nearestCar, carName, clearCars, blockFire, DRIVE_CSS } from './drive.js'; // WP7
import { initBody, bodyTick, bodyKey, bodyLeave, clinicOpen, toggleClinic, atClinic, bodyTimeScale, BODY_CSS } from './body.js'; // WP5

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
  G.story = { on, send, save, active, tick, onMain, key, look, uiOpen, timeScale, drive: driveStep, hideVM: driving, get cur() { return cur; } };
  // the bag as the story engine sees it (synchronous; kept fresh by the sim's 'inv' messages) + its host verbs
  G.story.inv = {
    has: (b, n = 1) => !!IVref.inv && count(IVref.inv, b) >= n,
    count: (b) => (IVref.inv ? count(IVref.inv, b) : 0),
    give: (b, n = 1, o = {}) => send('qgive', { b, n, ...o }),
    take: (b, n = 1) => send('qtake', { b, n }),
    coupons: (n) => send('qcoupons', { n }),
  };
  storyKeys(); initBar(G.story); initBag(G.story); initBody(G.story); initDrive(G.story);
  on('hello', (m) => { ME.yaw = m.yaw || 0; hud.msg('OVERDUE', 2.2, 'brag'); });
  on('saved', (m) => stored(m.save));
  on('redispensed', () => { if (driving()) endDrive(true); hud.msg('BEEP. CLUNK. RESTOCKING FEE APPLIED.', 2.2, 'brag'); });
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
        try { const s = c ? await loadSlot(i) : null; picker.classList.add('hidden'); start(s || newSave(i, testLot() ? 'story_test' : DEFAULT_WORLD)); }
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
function tick(dt = 1 / 60) {
  const bk = back();
  if (bk && bk.state === 'menu' && G.joined && G.mode !== 'story') setBack({ ...bk, state: 'sim' }); // you picked a sim
  const on = active() && ME.alive;
  const near = on && atTerminal();
  if (bagOpen() && !$('menu').classList.contains('hidden')) toggleBag(false); // the pause menu won over the bag
  if (!hint) { hint = el('div', 'st-hint hidden'); document.body.append(hint); }
  const car = on && !near && !driving() ? nearestCar() : null;
  const drop = on && !near && !car ? nearestDrop() : null, lock = on && !near && !drop && atLocker(), doc = on && !near && !drop && !lock && atClinic();
  const di = drop && infoOf(drop.item);
  hint.textContent = car ? `${K.label('use')} · DRIVE ${carName(car)}` : near ? `${K.label('use')} · ENTER THE SIMS` : drop ? `${K.label('use')} · PICK UP ${di ? di.name.toUpperCase() : ''}${drop.item.q > 1 ? ' x' + drop.item.q : ''}` : lock ? `${K.label('use')} · OPEN THE LOCKER` : doc ? `${K.label('use')} · SEE THE MEAT MECHANIC` : '';
  hint.classList.toggle('hidden', !(car || near || drop || lock || doc) || clinicOpen());
  const inStory = G.joined && G.mode === 'story';
  barShow(inStory);
  if (inStory) { barTick(dt); bodyTick(dt, G.camera); standIns(); driveTick(dt, G.camera); } else { if (wheelOpen()) closeWheel(false); if (bagOpen()) toggleBag(false); clearDrops(); bodyLeave(); clearCars(); }
  const use = on && K.isDown('use');
  if (near && use && !useWas) terminal();
  useWas = use;
  if (on && performance.now() - autoT > 60000) { autoT = performance.now(); save('auto'); }
  const paused = G.joined && G.mode === 'story' && !$('menu').classList.contains('hidden');
  if (paused && !pausedWas) save('pause'); // the pause menu is where you quit from: keep the spot
  pausedWas = paused;
}
// the slice has no Locker or clinic of its own yet: a green locker and a pink chair by the Machine (worlds.js)
let stands = null;
function standIns() {
  const W = worldOf(G.cfg && G.cfg.map), key = W.stand ? W.id : '';
  if ((stands && stands.userData.key) === key && (!stands || stands.parent === G.scene)) return;
  if (stands) { G.scene.remove(stands); stands = null; }
  if (!key) return;
  stands = new THREE.Group(); stands.userData.key = key;
  const box = (w, h, d, c, x, y, z) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshLambertMaterial({ color: c })); m.position.set(x, y, z); stands.add(m); };
  const [lx, ly, lz] = W.locker.p, [cx, cy, cz] = W.clinic.p;
  box(1.6, 2.2, 0.9, 0x7dff4f, lx, ly + 1.1, lz); box(0.2, 0.25, 0.1, 0xffe14d, lx + 0.25, ly + 1.1, lz + 0.48);
  box(1.2, 0.7, 1.2, 0x666677, cx, cy + 0.35, cz); box(1.1, 0.25, 1.1, 0xff4fd8, cx, cy + 0.82, cz); box(1.1, 0.95, 0.2, 0xff4fd8, cx, cy + 1.4, cz - 0.5);
  G.scene.add(stands);
}
let toSim = false;
// main.js hands every key / mouse button here first while story mode is loaded. true = story used it (stop there)
function key(e, down) {
  if (!G.joined || G.mode !== 'story') return false;
  if (!down) {
    if (wheelOpen() && K.up('wheel', e)) closeWheel(true);
    if (K.up('use', e)) { const r = bodyKey(e, false); if (r && r.pick) send('pick', { id: r.pick }); } // (a tap on a weapon with the Second Stomach still picks it up)
    return wheelOpen() || bagOpen() || clinicOpen();
  }
  if (clinicOpen()) { if (K.matches(['use', 'menu'], e)) toggleClinic(false); return true; }
  if (bagOpen()) { if (K.matches(['bag', 'menu'], e)) toggleBag(false); return true; } // (the bag has the mouse)
  if (wheelOpen()) return true; // nothing leaks out of the wheel: no firing, no slot keys, no jumps
  if (e.repeat && K.matches('wheel', e)) return true;
  if (K.matches('wheel', e)) { openWheel(); return true; }
  if (K.matches('bag', e)) { toggleBag(true); return true; }
  for (let i = 0; i < 8; i++) if (K.matches(`bar${i + 1}`, e)) { useBar(i); return true; }
  if (K.matches('dropHeld', e)) { dropHeld(); return true; }
  if (driving()) { // in a car: F gets out, the rest is the car's (main.js turns movement keys into the car's pedals)
    if (K.matches('use', e) && !e.repeat) { endDrive(true); return true; }
    if (K.matches('fire', e) && blockFire()) { hud.msg('SIDEARMS ONLY FROM THE DRIVER\'S SEAT', 1.2); return true; }
    if (K.matches(['bag', 'wheel'], e)) return true;
  }
  if (K.matches('use', e) && !e.repeat && ME.alive && !driving() && nearestCar() && !atTerminal()) { tryEnter(); return true; }
  if (K.matches('use', e) && !e.repeat && ME.alive && !atTerminal()) { // (at the Machine, F is the sims: tick() has it)
    const d = nearestDrop();
    if (d) { if (bodyKey(e, true, d) !== 'hold') send('pick', { id: d.id }); return true; } // hold F with the Second Stomach: eat it
    if (atClinic()) { toggleClinic(true); return true; }
    if (atLocker()) { toggleBag(true); return true; }
  }
  return false;
}
const atTerminal = () => { const T = worldOf(G.cfg && G.cfg.map).terminal; return Math.hypot(ME.pos[0] - T.p[0], ME.pos[2] - T.p[2]) < T.r && Math.abs(ME.pos[1] - T.p[1]) < 4; };
function look(e) { return wheelOpen() && wheelLook(e.movementX, e.movementY); }
function uiOpen() { return bagOpen() || clinicOpen(); }
function timeScale() { return G.joined && G.mode === 'story' ? wheelScale(false) * bodyTimeScale() : 1; }

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
.st-on #hotbar{display:none}
.st-bar{position:fixed;left:50%;bottom:10px;transform:translateX(-50%);display:flex;gap:6px;z-index:15;pointer-events:none}
.st-bar.hidden,.st-wheel.hidden{display:none}
.st-cell{position:relative;width:62px;height:52px;background:rgba(18,8,24,.85);border:3px solid #444;box-shadow:3px 3px 0 #000;display:flex;align-items:center;justify-content:center;font-family:var(--font);color:#fff;user-select:none}
.st-cell img{max-width:56px;max-height:44px;image-rendering:auto;pointer-events:none}
.st-cell.empty{border-color:#333;opacity:.75}
.st-cell.on{transform:translateY(-6px) rotate(-2deg);box-shadow:4px 4px 0 #ff4fd8;background:#3a1040}
.st-cell.gear::after{content:'G';position:absolute;right:2px;top:0;font-weight:700;color:#ffe14d}
.st-key{position:absolute;left:3px;top:0;font-style:normal;font-size:12px;font-weight:700;color:#ffe14d}
.st-q{position:absolute;right:3px;bottom:0;font-size:13px;color:#fff;text-shadow:1px 1px 0 #000}
.st-wheel{position:fixed;inset:0;z-index:40;background:radial-gradient(circle,rgba(18,8,24,.55) 0,rgba(18,8,24,.25) 60%,transparent 70%);pointer-events:none;font-family:var(--font)}
.st-wedge{position:absolute;transform:translate(-50%,-50%) scale(1.15)}
.st-wedge.pick{transform:translate(-50%,-50%) scale(1.45) rotate(-3deg);box-shadow:5px 5px 0 #4fd8ff;z-index:2}
.st-tag{position:absolute;bottom:-18px;left:50%;transform:translateX(-50%);font-style:normal;font-size:11px;font-weight:700;color:#4fd8ff;white-space:nowrap}
.st-wname{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-2deg);background:#ffe14d;color:#000;border:3px solid #000;box-shadow:4px 4px 0 #ff4fd8;padding:4px 12px;font-weight:700;font-size:20px}
.st-bag{width:min(760px,96vw);transform:rotate(-.5deg)}
.st-bagtop{display:flex;align-items:center;gap:14px}.st-bagtop h2{font-size:38px}.st-bagtop .st-btn{margin-left:auto}
.st-grid{display:grid;grid-template-columns:repeat(10,62px);gap:6px;margin:8px 0}
.st-grid.small{grid-template-columns:repeat(10,62px);min-height:52px}
.st-info{min-height:22px;color:#ffe14d;margin:2px 0 10px}
.st-barrow{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.st-lbl{color:#4fd8ff;margin-right:6px}
.st-drop{background:#ff3030;color:#fff;font-weight:700;border-color:#000}
.st-locker{margin-top:12px;border:3px dashed #7dff4f;padding:8px}
.st-bag .st-cell{cursor:grab}.st-cell.over{outline:3px solid #ffe14d}.st-cell.held{outline:3px solid #4fd8ff;transform:rotate(-3deg)}.st-cell.drag{opacity:.4}
`+ LOOT_CSS + BODY_CSS + DRIVE_CSS;
  document.head.append(s);
}
