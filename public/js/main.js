// JANKFIRE client entry: menus, modes, input, net handlers and the main loop.
import * as THREE from 'three';
import { BOXES, MAPS, MAP_ORDER } from '/shared/map.js';
import { WEAPONS, ORDER, SLOTS, FLAGS, SLIP_TIME, HIPFIRE, BOT_DIFF, MODES, STREAKS, ITEMS, ITEM_ORDER, validLoadout, validStreaks } from '/shared/weapons.js';
import { streakIcon } from './icons.js';
import { stepProjectile, raycast } from '/shared/physics.js';
import { G } from './ctx.js';
import { initWorld, renderFrame, setJank, updateWorld, loadMap } from './world.js';
import { loadTripoModels, buildProjectile, buildPeel, buildHole, makeShadow, tipColor, buildCharacter, M } from './models.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { fx, makeBeam, setBeam, scaleU } from './fx.js';
import { marbles } from './marbles.js';
import { initAudio, sfx, setVolume, setListener, stopLoops } from './audio.js';
import { ME, stepPlayer, tryHook, releaseHook, applyKb, slip, eye, hookPoint, hspeed, crouchTap } from './player.js';
import {
  W, initWeapons, rebuildViewmodels, rebuildOne, setLoadout, refillAmmo, switchSlot, lastSlot, cycleSlot, reload,
  fireDown, fireUp, updateWeapons, muzzleWorld, onSlipperBack, inspect, grantScythe, loseScythe, toggleScythe, cycleCard, heavyAttack,
  useItem, syncItem, resetItems, setMyKatana,
} from './weapons.js';
import { Remote, updateGibs } from './remote.js';
import { FINISHES, HATS, EFFECTS, validSkin, randomSkin, makeSkinSystems, emitSkinFx, skinTick, tracerColor, DEFAULT_SKIN } from './skins.js';
import { initPreview, showPreview, showCharacter, renderPreview, resizePreview } from './preview.js';
import { playKillFx, updateKillFx, clearKillFx } from './killfx.js';
import { updateSpeedLines } from './speedlines.js';
import { slipperUpdate, slipperStep } from './slipper.js';
import { setupObjectives, updateObjectives, addTag, removeTag, clearTags, canUse } from './objective.js';
import { GAMES, GAME_ORDER, TEAMS } from '/shared/modes.js';
import { defaultCard, cardEl, initCardEditor } from './cards.js';
import { recordSnap, recordEv, clearRec, localClip, playClip, stopReplay, updateReplay, RP, serverNow } from './replay.js';
import { LOOK_COLORS, ACHIEVEMENTS, ACCESSORIES, LOOK_SLOTS, DEFAULT_LOOK, validLook, SKIN_TONES, HAIR_COLORS, CLOTH_COLORS, HAIRS, TOPS, BOTTOMS } from '/shared/looks.js';
import { account, restore, login, register, logout, saveProfile, leaderboard as fetchLeaders } from './account.js';
import { COSMETICS, RARITY, TYPES, LOOT_TYPES, TYPE_NAMES_ALL as TYPE_NAMES, CONTAINERS, owns, ownedSkin, ownedKill, modelsFor } from '/shared/cosmetics.js';

const $ = (id) => document.getElementById(id);
const canvas = $('game');
const INTERP_MS = 110;
const wname = (id) => (WEAPONS[id] ? WEAPONS[id].name : id === 'hook' ? 'Grapple' : id === 'tbag' ? 'T-Bag' : id);
const wcolor = (id) => (WEAPONS[id] ? WEAPONS[id].color : '#ccc');

// ------------------------------------------------------------ settings
try {
  const saved = JSON.parse(localStorage.getItem('jankfire') || '{}');
  Object.assign(G.settings, saved);
} catch { /* private mode */ }
G.settings.loadout = validLoadout(G.settings.loadout);
if (!G.settings.skins || typeof G.settings.skins !== 'object') G.settings.skins = {};
if (!G.settings.look || typeof G.settings.look !== 'object') G.settings.look = { ...DEFAULT_LOOK };
const SYNC_KEYS = ['jank', 'sens', 'adsSens', 'vol', 'fov', 'swapAim', 'toggleAim', 'blood', 'shake', 'fovKick', 'showFps', 'killcam', 'showCards', 'speedLines'];
function profileData() {
  const settings = {};
  for (const k of SYNC_KEYS) settings[k] = G.settings[k];
  return { loadout: G.settings.loadout, skins: G.settings.skins, look: G.settings.look, card: G.settings.card || '', kfx: G.settings.kfx || 'none', settings };
}
function saveSettings() {
  try { localStorage.setItem('jankfire', JSON.stringify(G.settings)); } catch { /* whatever */ }
  saveProfile(profileData());
}
// what you actually wear = what you picked, minus anything you haven't unlocked
G.inv = {};
G.equipped = {};
function recomputeEquipped() {
  G.equipped = {};
  for (const [id, sk] of Object.entries(G.settings.skins || {})) {
    const o = ownedSkin(sk, G.inv, id);
    if (o[0] !== 'default' || o[1] !== 'none' || o[2] !== 'none' || o[3] !== 'default') G.equipped[id] = o;
  }
  if (G.equipped.scythe) G.equipped.scythe_rifle = G.equipped.scythe.slice(0, 3).concat('default'); // both forms look the same
}
recomputeEquipped();

// ------------------------------------------------------------ setup
initWorld(canvas);
setJank(G.settings.jank);
fx.init(G.scene);
const vmScaleU = { value: 300 };
G.skinFxWorld = makeSkinSystems(G.scene, scaleU);
G.skinFxVM = makeSkinSystems(G.vmScene, vmScaleU);
hud.init();
initWeapons();
setLoadout(G.settings.loadout);
hud.show(false);
initPreview($('preview'));

const myShadow = makeShadow();
G.scene.add(myShadow);
const myRope = makeBeam(0x3a2a1a);
myRope.visible = false;
G.scene.add(myRope);

loadTripoModels().then((n) => {
  if (!n) return;
  console.log(`loaded ${n} tripo models`);
  rebuildViewmodels();
  setLoadout(G.settings.loadout);
  for (const r of G.remotes.values()) r.build();
  $('status').textContent = `${n} Tripo model(s) loaded`;
});

// ------------------------------------------------------------ screens
let screen = 'main';
function show(id) {
  screen = id;
  for (const el of document.querySelectorAll('.screen')) el.classList.toggle('hidden', el.id !== 'scr-' + id);
  $('menu').classList.remove('hidden');
  hud.show(false);
  if (id === 'cosmetics') { $('cosSlot').append($('preview')); buildCosmeticsUI(); setTimeout(resizePreview, 0); }
  if (id === 'character') { $('charSlot').append($('preview')); buildCharacterUI(); setTimeout(resizePreview, 0); }
  if (id === 'namecard') cardEditor.open();
  if (id === 'crates') renderCrates();
  if (id === 'loadout') buildLoadoutUI();
  if (id === 'match') syncMatchUI();
  if (id === 'profile') { renderProfile(); restore().then((me) => { if (me && screen === 'profile') { renderProfile(); renderAcctBar(); } }); }
  if (id === 'leaders') renderLeaders();
  if (id === 'main') renderAcctBar();
}
function hideMenu() {
  $('menu').classList.add('hidden');
  hud.show(true);
}
for (const b of document.querySelectorAll('[data-go]')) b.addEventListener('click', () => show(b.dataset.go));
for (const b of document.querySelectorAll('.back')) b.addEventListener('click', () => show(G.joined ? 'pause' : 'main'));
for (const b of document.querySelectorAll('[data-mode]')) b.addEventListener('click', () => startMode(b.dataset.mode));
$('resume').addEventListener('click', resume);
$('quit').addEventListener('click', quitToMenu);

function resume() {
  hideMenu();
  lock();
}

// ------------------------------------------------------------ playing
let connecting = false;
function startMode(mode, cfg) {
  if (S.display === 'fullscreen' && !(window.jf && window.jf.display)) applyDisplay('fullscreen');
  G.settings.name = $('name').value.trim().slice(0, 16);
  saveSettings();
  initAudio(G.settings.vol);
  setVolume(G.settings.vol);
  if (connecting) return;
  if (G.joined) quitToMenu(true);
  connecting = true;
  $('status').textContent = 'connecting...';
  net.connect({ name: G.settings.name, mode, skins: G.equipped, look: G.settings.look, card: G.settings.card || '', kfx: myKfx(), kc: G.settings.killcam !== false, streaks: validStreaks(S.loadout.streaks), cfg, token: account.loggedIn ? account.token : undefined }, () => {
    connecting = false;
    resetWorldState();
    show('main');
    $('status').textContent = 'Disconnected. Server is down or restarted.';
  });
  hideMenu();
  lock();
}

function resetWorldState() {
  G.joined = false;
  ME.alive = false;
  releaseHook();
  stopLoops();
  for (const r of G.remotes.values()) r.dispose();
  G.remotes.clear(); G.names.clear(); G.skins.clear();
  clearEntities();
  for (const g of G.gibs) G.scene.remove(g.m);
  G.gibs.length = 0;
  hud.dead(false);
  hud.wave(null);
  hud.scope(false);
  endKillcam();
  stopReplay(true);
  hideReplayUI();
  if (G.forcedLoadout) { G.forcedLoadout = null; setLoadout(S.loadout); }
  for (const b of G.bubbles.values()) G.scene.remove(b.mesh);
  G.bubbles.clear(); G.smokes.length = 0; ME.frozenUntil = 0; G.frost = 0;
  clearRec();
  clearKillFx();
  G.roundOver = false;
  renderRound(null);
  $('roundEnd').classList.add('hidden');
  if (account.loggedIn) setTimeout(() => restore().then((me) => { if (me) renderAcctBar(); }), 900); // server saves stats when you leave
}
function clearEntities() {
  for (const pr of G.projs.values()) G.scene.remove(pr.mesh);
  for (const pl of G.peels.values()) G.scene.remove(pl);
  for (const h of G.holes.values()) G.scene.remove(h.mesh);
  G.projs.clear(); G.peels.clear(); G.holes.clear();
}
function quitToMenu(silent) {
  net.close();
  connecting = false;
  resetWorldState();
  if (document.pointerLockElement) document.exitPointerLock();
  if (silent !== true) show('main');
  $('status').textContent = '';
}

function lock() {
  try {
    const p = canvas.requestPointerLock({ unadjustedMovement: true });
    if (p && p.catch) p.catch(() => { try { const q = canvas.requestPointerLock(); if (q && q.catch) q.catch(() => {}); } catch { /* no lock */ } });
  } catch { /* headless or denied */ }
}
function pause() {
  show('pause');
  $('pauseTitle').textContent = `${MODES[G.mode] ? MODES[G.mode].name.toUpperCase() : 'PAUSED'} · ${MAPS[G.cfg.map] ? MAPS[G.cfg.map].name : ''}`;
  W.held = false; W.aimHeld = false;
  for (const k in keys) keys[k] = false;
  stopLoops();
}
let wasLocked = false, lockedAt = 0, mouseAvg = 8;
document.addEventListener('pointerlockchange', () => {
  const locked = document.pointerLockElement === canvas;
  if (locked) lockedAt = performance.now();
  if (!locked && wasLocked && G.joined && !chatOpen && $('menu').classList.contains('hidden')) pause();
  wasLocked = locked;
});
canvas.addEventListener('click', () => { if (G.joined && document.pointerLockElement !== canvas && $('menu').classList.contains('hidden')) lock(); });

// ------------------------------------------------------------ bots setup + match settings
function fillSelect(sel, entries, value) {
  sel.innerHTML = '';
  for (const [k, label] of entries) {
    const o = document.createElement('option');
    o.value = k; o.textContent = label;
    sel.append(o);
  }
  if (value != null) sel.value = value;
}
const mapEntries = MAP_ORDER.map((k) => [k, `${MAPS[k].name} (${MAPS[k].size})`]);
const hipEntries = Object.entries(HIPFIRE).map(([k, v]) => [k, v.name]);
const diffEntries = Object.entries(BOT_DIFF).map(([k, v]) => [k, v.name]);
const gameEntries = GAME_ORDER.map((k) => [k, GAMES[k].name]);
fillSelect($('setupGame'), gameEntries, 'dm');
fillSelect($('cfgGame'), gameEntries, 'dm');
$('cfgGame').addEventListener('change', () => net.send({ t: 'cfg', game: $('cfgGame').value }));
fillSelect($('setupMap'), mapEntries, 'islands');
fillSelect($('setupDiff'), diffEntries, 'normal');
fillSelect($('setupHip'), hipEntries, 'normal');
fillSelect($('cfgMap'), mapEntries);
fillSelect($('cfgHip'), hipEntries);
fillSelect($('cfgDiff'), diffEntries);
$('setupBots').addEventListener('input', () => { $('setupBotsN').textContent = $('setupBots').value; });
$('setupGo').addEventListener('click', () => startMode('bots', {
  map: $('setupMap').value, bots: Number($('setupBots').value), diff: $('setupDiff').value, hip: $('setupHip').value, game: $('setupGame').value,
}));
function syncMatchUI() {
  $('cfgMap').value = G.cfg.map;
  $('cfgMap').disabled = G.mode === 'training';
  $('cfgHip').value = G.cfg.hip;
  $('cfgDiff').value = G.cfg.diff;
  $('cfgBots').value = G.cfg.bots;
  $('cfgBotsN').textContent = G.cfg.bots;
  for (const el of document.querySelectorAll('.botsOnly')) el.style.display = G.mode === 'bots' || G.mode === 'coop' ? '' : 'none';
  $('cfgBots').parentElement.style.display = G.mode === 'bots' ? '' : 'none';
  $('cfgGame').parentElement.style.display = G.mode === 'bots' ? '' : 'none';
  if (G.round && G.round.game) $('cfgGame').value = G.round.game;
}
$('cfgMap').addEventListener('change', () => net.send({ t: 'cfg', map: $('cfgMap').value }));
$('cfgHip').addEventListener('change', () => net.send({ t: 'cfg', hip: $('cfgHip').value }));
$('cfgDiff').addEventListener('change', () => net.send({ t: 'cfg', diff: $('cfgDiff').value }));
$('cfgBots').addEventListener('input', () => { $('cfgBotsN').textContent = $('cfgBots').value; });
$('cfgBots').addEventListener('change', () => net.send({ t: 'cfg', bots: Number($('cfgBots').value) }));

// ------------------------------------------------------------ settings screen
const S = G.settings;
$('name').value = S.name || '';
function bindRange(id, key, fmt, apply) {
  const el = $(id);
  el.value = String(S[key]);
  const out = $(id + 'N');
  const upd = () => { S[key] = Number(el.value); if (out) out.textContent = fmt ? fmt(S[key]) : S[key]; if (apply) apply(); saveSettings(); };
  el.addEventListener('input', upd);
  if (out) out.textContent = fmt ? fmt(S[key]) : S[key];
}
function bindCheck(id, key, apply) {
  const el = $(id);
  el.checked = !!S[key];
  el.addEventListener('change', () => { S[key] = el.checked; if (apply) apply(); saveSettings(); });
}
$('jank').value = String(S.jank);
$('jank').addEventListener('change', () => { S.jank = Number($('jank').value); setJank(S.jank); saveSettings(); });
bindRange('fov', 'fov');
bindRange('vol', 'vol', null, () => setVolume(S.vol));
bindRange('sens', 'sens', (v) => v.toFixed(1));
bindRange('adsSens', 'adsSens', (v) => v.toFixed(2));
bindCheck('fovKick', 'fovKick');
bindCheck('shake', 'shake');
bindCheck('showFps', 'showFps');
bindCheck('swapAim', 'swapAim');
bindCheck('toggleAim', 'toggleAim');
bindCheck('blood', 'blood');
bindCheck('killcam', 'killcam', () => { if (G.joined) net.send({ t: 'kc', on: S.killcam }); });
bindCheck('showCards', 'showCards');
bindCheck('speedLines', 'speedLines');
// display: windowed / windowed fullscreen (maximized, desktop app only) / fullscreen
const DISPLAY = window.jf && window.jf.display
  ? [['windowed', 'Windowed'], ['maximized', 'Windowed fullscreen'], ['fullscreen', 'Fullscreen']]
  : [['windowed', 'Windowed'], ['fullscreen', 'Fullscreen']];
fillSelect($('displayMode'), DISPLAY, S.display && DISPLAY.some(([k]) => k === S.display) ? S.display : 'windowed');
function applyDisplay(mode) {
  if (window.jf && window.jf.display) { window.jf.display(mode); return; }
  // browser: real fullscreen needs a click, so this runs from the settings menu or the PLAY buttons
  if (mode === 'fullscreen' && !document.fullscreenElement) document.documentElement.requestFullscreen({ navigationUI: 'hide' }).catch(() => {});
  if (mode !== 'fullscreen' && document.fullscreenElement) document.exitFullscreen().catch(() => {});
}
$('displayMode').addEventListener('change', () => { S.display = $('displayMode').value; saveSettings(); applyDisplay(S.display); });
if (window.jf && window.jf.displayGet) window.jf.displayGet().then((m) => { if (m) { S.display = m; $('displayMode').value = m; } });
// hotbar: weapons, item and killstreaks in one bar, along the bottom or down the right side
const applyHotbar = () => document.body.classList.toggle('hotbar-right', S.hotbar === 'right');
fillSelect($('hotbarPos'), [['bottom', 'Bottom'], ['right', 'Right side']], S.hotbar === 'right' ? 'right' : 'bottom');
$('hotbarPos').addEventListener('change', () => { S.hotbar = $('hotbarPos').value; saveSettings(); applyHotbar(); });
applyHotbar();

// ------------------------------------------------------------ loadout screen
function buildLoadoutUI() {
  for (const slot of SLOTS) {
    const col = $('lo-' + slot);
    col.innerHTML = '';
    for (const id of ORDER) {
      const w = WEAPONS[id];
      if (w.slot !== slot) continue;
      const b = document.createElement('button');
      b.className = 'wpick' + (S.loadout[slot] === id ? ' on' : '');
      b.textContent = w.name;
      b.style.setProperty('--c', w.color);
      b.addEventListener('mouseenter', () => { $('loDesc').textContent = `${w.name}: ${w.desc}`; });
      b.addEventListener('click', () => {
        S.loadout[slot] = id;
        G.cosSel = id;
        saveSettings();
        buildLoadoutUI();
        applyLoadout(false);
        $('loDesc').textContent = `${w.name}: ${w.desc}`;
      });
      col.append(b);
    }
  }
  // killstreaks: pick 3
  const kc = $('lo-streaks');
  kc.innerHTML = '';
  const picks = validStreaks(S.loadout.streaks);
  for (const [id, st] of Object.entries(STREAKS).sort((a, b) => a[1].kills - b[1].kills)) {
    const b = document.createElement('button');
    b.className = 'kpick' + (picks.includes(id) ? ' on' : '');
    const im = document.createElement('img'); im.src = streakIcon(id); im.alt = '';
    const t = document.createElement('span'); t.textContent = `${st.name} · ${st.kills}`;
    b.append(im, t);
    b.addEventListener('mouseenter', () => { $('loDesc').textContent = `${st.name} (${st.kills} kills in a row): ${st.desc}`; });
    b.addEventListener('click', () => {
      let list = picks.slice();
      if (list.includes(id)) { toast('you need 3 killstreaks: pick another one to swap it out'); return; }
      list = [...list.slice(0, 2), id]; // the newest pick replaces your most expensive one
      S.loadout.streaks = validStreaks(list);
      saveSettings();
      if (G.joined) net.send({ t: 'streaks', list: S.loadout.streaks });
      buildLoadoutUI(); renderStreak(G.streakN || 0);
    });
    kc.append(b);
  }
  // items
  const ic = $('lo-item');
  ic.innerHTML = '';
  for (const id of ITEM_ORDER) {
    const it = ITEMS[id];
    const b = document.createElement('button');
    b.className = 'wpick' + ((S.loadout.item || 'frag') === id ? ' on' : '');
    b.textContent = `${it.name} x${it.charges}`;
    b.style.setProperty('--c', it.color);
    b.addEventListener('mouseenter', () => { $('loDesc').textContent = `${it.name}: ${it.desc} (${it.charges} charge${it.charges > 1 ? 's' : ''}, ${it.recharge}s to refill)`; });
    b.addEventListener('click', () => { S.loadout.item = id; saveSettings(); buildLoadoutUI(); applyLoadout(false); });
    ic.append(b);
  }
}
function applyLoadout(force) {
  if (G.forcedLoadout) { $('loNote').textContent = 'randomizer is on: you get a random loadout every life'; return; }
  const canNow = force || !G.joined || !ME.alive || performance.now() - (G.spawnT || 0) < 5000;
  if (canNow) { setLoadout(S.loadout); G.pendingLoadout = false; $('loNote').textContent = ''; }
  else { G.pendingLoadout = true; $('loNote').textContent = 'loadout switches when you respawn'; }
}

// ------------------------------------------------------------ cosmetics screen
G.cosSel = S.loadout.primary;
let skinSendT = null;
function sendSkins() {
  clearTimeout(skinSendT);
  skinSendT = setTimeout(() => { if (G.joined) net.send({ t: 'skin', s: G.equipped }); }, 250);
}
// the weapons that show up in COSMETICS (the rifle form of the scythe borrows the scythe's look)
function skinnable() { return ORDER.filter((id) => WEAPONS[id] && (SLOTS.includes(WEAPONS[id].slot) || id === 'scythe')); }
function storeSkin(id, skin) {
  if (skin[0] === 'default' && skin[1] === 'none' && skin[2] === 'none' && (skin[3] || 'default') === 'default') delete S.skins[id];
  else S.skins[id] = skin;
}
// wrap / hat / effect on EVERY weapon at once (each weapon keeps its own model)
function setPartAll(idx, value) {
  for (const id of skinnable()) { const sk = validSkin(S.skins[id]).slice(); sk[idx] = value; storeSkin(id, sk); }
  saveSettings(); recomputeEquipped(); sendSkins(); rebuildViewmodels(); setLoadout(S.loadout);
}
const allMode = () => S.skinAll !== false;
function setSkin(id, skin) {
  if (skin[0] === 'default' && skin[1] === 'none' && skin[2] === 'none' && (skin[3] || 'default') === 'default') delete S.skins[id];
  else S.skins[id] = skin;
  saveSettings();
  recomputeEquipped();
  sendSkins();
  rebuildOne(id);
}
// ------------------------------------------------------------ character customizer
function myAchs() { return new Set((account.me && account.me.achs) || []); }
function rewardsFor(achId) {
  const out = [];
  for (const s2 of LOOK_SLOTS) for (const [k, v] of Object.entries(ACCESSORIES[s2])) if (v.ach === achId) out.push({ slot: s2, id: k, name: v.name });
  return out;
}
function setLook(look) {
  G.settings.look = look;
  saveSettings();
  if (G.joined) net.send({ t: 'look', look: validLook(look, myAchs()) });
}
function buildCharacterUI() {
  const achs = myAchs();
  const look = { ...DEFAULT_LOOK, ...G.settings.look };
  const shown = validLook(look, achs);
  showCharacter(buildCharacter, shown.color || G.myColor || '#ff4fd8', shown);
  // colour swatches (first one = whatever the server hands you)
  const cel = $('lk-color');
  cel.innerHTML = '';
  for (const c of ['', ...LOOK_COLORS]) {
    const b = document.createElement('button');
    b.className = 'swatch' + (c ? '' : ' auto') + (look.color === c ? ' on' : '');
    if (c) b.style.background = c;
    b.title = c ? c : 'random every match';
    b.addEventListener('click', () => { setLook({ ...look, color: c }); buildCharacterUI(); });
    cel.append(b);
  }
  // outfit: skin / hair / top / bottom, each a style + a colour
  const swatches = (elId, key, list, autoTitle) => {
    const el = $(elId);
    el.innerHTML = '';
    for (const c of autoTitle ? ['', ...list] : list) {
      const b = document.createElement('button');
      b.className = 'swatch' + (c ? '' : ' auto') + ((look[key] || '') === c ? ' on' : '');
      if (c) b.style.background = c;
      b.title = c || autoTitle;
      b.addEventListener('click', () => { setLook({ ...look, [key]: c }); buildCharacterUI(); });
      el.append(b);
    }
  };
  const styles = (elId, key, cat) => {
    const el = $(elId);
    el.innerHTML = '';
    for (const [k, v] of Object.entries(cat)) {
      const c = document.createElement('button');
      c.className = 'chip' + ((look[key] || DEFAULT_LOOK[key]) === k ? ' on' : '');
      c.textContent = v.name;
      c.addEventListener('click', () => { setLook({ ...look, [key]: k }); buildCharacterUI(); });
      el.append(c);
    }
  };
  swatches('lk-skin', 'skin', SKIN_TONES, 'mannequin');
  styles('lk-hair', 'hair', HAIRS); swatches('lk-hairColor', 'hairColor', HAIR_COLORS);
  styles('lk-top', 'top', TOPS); swatches('lk-topColor', 'topColor', CLOTH_COLORS, 'same as your colour');
  styles('lk-bottom', 'bottom', BOTTOMS); swatches('lk-bottomColor', 'bottomColor', CLOTH_COLORS, 'same as your colour');
  for (const slot of LOOK_SLOTS) {
    const el = $('lk-' + slot);
    el.innerHTML = '';
    for (const [k, v] of Object.entries(ACCESSORIES[slot])) {
      const have = !v.ach || achs.has(v.ach);
      const c = document.createElement('button');
      c.className = 'chip' + (look[slot] === k ? ' on' : '') + (have ? '' : ' locked');
      c.textContent = v.name;
      if (v.ach) c.style.setProperty('--rc', '#ffe14d');
      c.title = v.ach ? `${ACHIEVEMENTS[v.ach].name}: ${ACHIEVEMENTS[v.ach].desc}` : 'free';
      c.addEventListener('click', () => {
        if (!have) { toast(`${v.name}: unlock "${ACHIEVEMENTS[v.ach].name}" (${ACHIEVEMENTS[v.ach].desc})${account.loggedIn ? '' : '. log in so it counts'}`, 3200); return; }
        setLook({ ...look, [slot]: k }); buildCharacterUI();
      });
      el.append(c);
    }
  }
  // kill effect (rolled from duffel bags)
  const kel = $('lk-kill');
  kel.innerHTML = '';
  const curK = myKfx();
  for (const [k, v] of Object.entries(COSMETICS.kill)) {
    const have = owns(G.inv, 'kill', k);
    const c = document.createElement('button');
    c.className = 'chip' + (curK === k ? ' on' : '') + (have ? '' : ' locked');
    c.textContent = v.name;
    c.style.setProperty('--rc', RARITY[v.rarity].color);
    c.title = `${RARITY[v.rarity].name}: ${v.desc}`;
    c.addEventListener('click', () => {
      if (!have) { toast(`${v.name} (${RARITY[v.rarity].name}): ${v.desc}. find it in duffel bags`, 3000); return; }
      setKfx(k); toast(`${v.name}: ${v.desc}. try it on the dummies in TRAINING`);
    });
    kel.append(c);
  }
  $('lkCard').innerHTML = '';
  $('lkCard').append(cardEl(cardUrlFor('me'), (account.me && account.me.name) || S.name || 'you', S.card ? 'your name card' : 'generated card (make your own!)', shown.color || '#ff4fd8'));
  // achievements list with progress
  const list = $('achList');
  list.innerHTML = '';
  const h = document.createElement('div'); h.className = 'lt'; h.textContent = `achievements ${achs.size}/${Object.keys(ACHIEVEMENTS).length}`;
  list.append(h);
  const st = (account.me && account.me.stats) || {};
  for (const [id, a] of Object.entries(ACHIEVEMENTS)) {
    const d = document.createElement('div');
    const done = achs.has(id);
    d.className = 'ach' + (done ? ' done' : '');
    const b = document.createElement('b'); b.textContent = (done ? '★ ' : '') + a.name;
    const t = document.createElement('div'); t.textContent = a.desc;
    const have = Math.min(a.goal, st[a.stat] || 0);
    const bar = document.createElement('div'); bar.className = 'bar';
    const fill = document.createElement('i'); fill.style.width = (done ? 100 : (have / a.goal) * 100) + '%'; bar.append(fill);
    const rw = document.createElement('div'); rw.className = 'rw';
    rw.textContent = 'unlocks ' + rewardsFor(id).map((x) => x.name).join(', ');
    d.append(b, t, bar, rw);
    list.append(d);
  }
  $('lkNote').textContent = account.loggedIn ? 'other players see this. locked stuff unlocks from achievements.' : 'guest: free accessories only. log in to earn the achievement ones.';
}
const cardEditor = initCardEditor({
  get: () => S.card || '',
  save: (url) => { S.card = url; saveSettings(); if (G.joined) net.send({ t: 'card', card: url }); },
  toast: (t) => toast(t),
});
$('lkRandom').addEventListener('click', () => {
  const achs = myAchs();
  const pick = (arr) => arr[(Math.random() * arr.length) | 0];
  const look = { color: pick(LOOK_COLORS), skin: pick(SKIN_TONES), hair: pick(Object.keys(HAIRS)), hairColor: pick(HAIR_COLORS),
    top: pick(Object.keys(TOPS)), topColor: pick(CLOTH_COLORS), bottom: pick(Object.keys(BOTTOMS)), bottomColor: pick(CLOTH_COLORS) };
  for (const s2 of LOOK_SLOTS) look[s2] = pick(Object.entries(ACCESSORIES[s2]).filter(([, v]) => !v.ach || achs.has(v.ach)).map(([k]) => k));
  setLook(look); buildCharacterUI();
});
$('lkReset').addEventListener('click', () => { setLook({ ...DEFAULT_LOOK }); buildCharacterUI(); });

function buildCosmeticsUI() {
  const list = $('cosWeapons');
  list.innerHTML = '';
  for (const slot of [...SLOTS, 'streak']) {
    const h = document.createElement('div');
    h.className = 'lt'; h.textContent = slot === 'streak' ? 'killstreak' : slot;
    list.append(h);
    for (const id of ORDER) {
      const w = WEAPONS[id];
      if (w.slot !== slot || id === 'scythe_rifle') continue;
      const b = document.createElement('button');
      b.className = 'wpick' + (G.cosSel === id ? ' on' : '');
      if (modelsFor(id).length > 1) b.title = 'has skins';
      b.textContent = w.name + (S.skins[id] ? ' *' : '');
      b.style.setProperty('--c', w.color);
      b.addEventListener('click', () => { G.cosSel = id; buildCosmeticsUI(); });
      list.append(b);
    }
  }
  const id = G.cosSel;
  const sk = validSkin(S.skins[id]);
  $('cosName').innerHTML = '';
  const n = document.createElement('span');
  n.textContent = WEAPONS[id].name;
  n.style.color = WEAPONS[id].color;
  $('cosName').append(n);
  const chips = (elId, type, idx) => {
    const el = $(elId);
    el.innerHTML = '';
    for (const [k, v] of Object.entries(COSMETICS[type])) {
      const c = document.createElement('button');
      const have = owns(G.inv, type, k);
      c.className = 'chip' + (sk[idx] === k ? ' on' : '') + (have ? '' : ' locked');
      c.textContent = v.name;
      c.style.setProperty('--rc', RARITY[v.rarity].color);
      c.title = `${RARITY[v.rarity].name}${have ? '' : ' (locked: roll to unlock)'}`;
      c.addEventListener('click', () => {
        if (!have) { toast(`${v.name} is ${RARITY[v.rarity].name}. win rounds to get rolls.`); return; }
        if (allMode()) setPartAll(idx, k);
        else { const s2 = sk.slice(); s2[idx] = k; setSkin(id, s2); }
        buildCosmeticsUI();
      });
      el.append(c);
    }
  };
  $('skAllMode').checked = allMode();
  const kel = $('sk-kill');
  kel.innerHTML = '';
  const curK = myKfx();
  for (const [k, v] of Object.entries(COSMETICS.kill)) {
    const have = owns(G.inv, 'kill', k);
    const c = document.createElement('button');
    c.className = 'chip' + (curK === k ? ' on' : '') + (have ? '' : ' locked');
    c.textContent = v.name;
    c.style.setProperty('--rc', RARITY[v.rarity].color);
    c.title = `${RARITY[v.rarity].name}: ${v.desc}`;
    c.addEventListener('click', () => {
      if (!have) { toast(`${v.name} (${RARITY[v.rarity].name}): ${v.desc}. find it in duffel bags`, 3000); return; }
      setKfx(k); buildCosmeticsUI();
    });
    kel.append(c);
  }
  chips('sk-finish', 'finish', 0);
  chips('sk-hat', 'hat', 1);
  chips('sk-effect', 'effect', 2);
  // skins = different models for this weapon (knives, slappers, bread...)
  const models = modelsFor(id);
  $('sk-model').innerHTML = '';
  $('skModelRow').style.display = models.length > 1 ? '' : 'none';
  for (const k of models) {
    const v = COSMETICS.model[k];
    const have = owns(G.inv, 'model', k);
    const c = document.createElement('button');
    c.className = 'chip' + ((sk[3] || 'default') === k ? ' on' : '') + (have ? '' : ' locked');
    c.textContent = v.name;
    c.style.setProperty('--rc', RARITY[v.rarity].color);
    c.addEventListener('click', () => {
      if (!have) { toast(`${v.name} is ${RARITY[v.rarity].name}. win rounds to get rolls.`); return; }
      const s2 = sk.slice(); s2[3] = k; setSkin(id, s2); buildCosmeticsUI();
    });
    $('sk-model').append(c);
  }
  showPreview(id, ownedSkin(sk, G.inv, id));
}
$('skRandom').addEventListener('click', () => {
  const pick = (t) => { const ks = Object.keys(COSMETICS[t]).filter((k) => owns(G.inv, t, k)); return ks[(Math.random() * ks.length) | 0]; };
  if (allMode()) {
    const parts = ['finish', 'hat', 'effect'].map(pick);
    for (const id of skinnable()) { const sk = validSkin(S.skins[id]).slice(); sk[0] = parts[0]; sk[1] = parts[1]; sk[2] = parts[2]; storeSkin(id, sk); }
    saveSettings(); recomputeEquipped(); sendSkins(); rebuildViewmodels(); setLoadout(S.loadout);
  } else setSkin(G.cosSel, TYPES.map(pick));
  buildCosmeticsUI();
});
$('skReset').addEventListener('click', () => {
  if (allMode()) {
    for (const id of skinnable()) { const sk = validSkin(S.skins[id]).slice(); sk[0] = 'default'; sk[1] = 'none'; sk[2] = 'none'; storeSkin(id, sk); }
    saveSettings(); recomputeEquipped(); sendSkins(); rebuildViewmodels(); setLoadout(S.loadout);
  } else setSkin(G.cosSel, DEFAULT_SKIN.slice());
  buildCosmeticsUI();
});
$('skAll').addEventListener('click', () => { // copy this weapon's wrap/hat/effect to everything (models stay)
  const sk = validSkin(S.skins[G.cosSel]);
  for (const id of skinnable()) { const s2 = validSkin(S.skins[id]).slice(); s2[0] = sk[0]; s2[1] = sk[1]; s2[2] = sk[2]; storeSkin(id, s2); }
  saveSettings(); recomputeEquipped(); sendSkins(); rebuildViewmodels(); setLoadout(S.loadout); buildCosmeticsUI();
});
$('skAllMode').addEventListener('change', () => { S.skinAll = $('skAllMode').checked; saveSettings(); buildCosmeticsUI(); });

// ------------------------------------------------------------ input
const keys = {};
let jumpPressed = false, chatOpen = false, scoresOpen = false;
const inGame = () => G.joined && !chatOpen && $('menu').classList.contains('hidden');

function openChat() {
  chatOpen = true;
  for (const k in keys) keys[k] = false;
  $('chatin').classList.remove('hidden');
  $('chatin').value = '';
  setTimeout(() => $('chatin').focus(), 0);
}
function closeChat(sendIt) {
  const v = $('chatin').value.trim();
  if (sendIt && v) net.send({ t: 'chat', m: v });
  chatOpen = false;
  $('chatin').classList.add('hidden');
  $('chatin').blur();
}
$('chatin').addEventListener('keydown', (e) => {
  e.stopPropagation();
  if (e.key === 'Enter') closeChat(true);
  else if (e.key === 'Escape') closeChat(false);
});

function aimDown() {
  if (W.cur === 'cards') { cycleCard(); return; }
  if (heavyAttack()) return; // knife: right click is the heavy stab
  if (S.toggleAim) W.aimHeld = !W.aimHeld; else W.aimHeld = true;
}
function aimUp() { if (!S.toggleAim) W.aimHeld = false; }

addEventListener('keydown', (e) => {
  if (!inGame() || document.activeElement === $('name')) return;
  if ((RP.active || G.killcamPending) && (e.code === 'Space' || e.code === 'Enter')) { e.preventDefault(); skipReplay(); return; }
  if (e.code === 'Tab') { e.preventDefault(); scoresOpen = true; renderScores(); return; }
  if (e.code === 'KeyT' || e.code === 'Enter') { e.preventDefault(); openChat(); return; }
  if (e.code === 'KeyB') { if (document.pointerLockElement) document.exitPointerLock(); pause(); return; }
  if (e.code === 'Space') { e.preventDefault(); if (!e.repeat) jumpPressed = true; }
  if (e.code === 'KeyE' && !e.repeat) { if (S.swapAim) aimDown(); else tryHook(); }
  if (G.vote && ['Digit1', 'Digit2', 'Digit3'].includes(e.code)) { castVote(Number(e.code.slice(5)) - 1); return; }
  if (e.code === 'Digit1') switchSlot(0);
  if (e.code === 'Digit2') switchSlot(1);
  if (e.code === 'Digit3') switchSlot(2);
  if (e.code === 'KeyQ') lastSlot();
  if (e.code === 'KeyR') reload();
  if (e.code === 'KeyF' && !e.repeat) { if (canUse(G.round, ME.pos)) startUse(); else inspect(); }
  if (e.code === 'KeyV') W.dashHeld = true;
  if (e.code === 'KeyX' && !e.repeat) toggleScythe();
  if (e.code === 'KeyG' && !e.repeat) useItem();
  if (['Digit5', 'Digit6', 'Digit7'].includes(e.code) && !e.repeat) deployStreak(Number(e.code.slice(5)) - 5);
  if (e.code === 'Digit4') switchSlot(3);
  if ((e.code === 'KeyC' || e.code === 'ControlLeft' || e.code === 'ControlRight') && !e.repeat) {
    if (e.code !== 'KeyC') e.preventDefault();
    const t = crouchTap(performance.now());
    if (t === 2) { net.send({ t: 'tbag' }); G.shake = 1; }
    else if (t === 1) G.shake = Math.max(G.shake, 0.25);
  }
  keys[e.code] = true;
});
addEventListener('keyup', (e) => {
  keys[e.code] = false;
  if (e.code === 'KeyF') stopUse();
  if (e.code === 'KeyV') W.dashHeld = false;
  if (e.code === 'Tab') { scoresOpen = false; hud.scores(false); }
  if (e.code === 'KeyE') { if (S.swapAim) aimUp(); else releaseHook(); }
});
addEventListener('mousedown', (e) => {
  if (!inGame()) return;
  if (RP.mode === 'killcam' || G.killcamPending) { skipReplay(); return; }
  if (e.button === 0) fireDown();
  if (e.button === 2) { if (S.swapAim) tryHook(); else aimDown(); }
  if (e.button === 3 || e.button === 4) tryHook();
});
addEventListener('mouseup', (e) => {
  if (e.button === 0) fireUp();
  if (e.button === 2) { if (S.swapAim) releaseHook(); else aimUp(); }
  if (e.button === 3 || e.button === 4) releaseHook();
});
addEventListener('contextmenu', (e) => e.preventDefault());
addEventListener('wheel', (e) => { if (inGame()) cycleSlot(e.deltaY > 0 ? 1 : -1); }, { passive: true });
addEventListener('mousemove', (e) => {
  if (document.pointerLockElement !== canvas) return;
  if (performance.now() < (G.spinUntil || 0)) return; // the aimbot has the wheel
  const s = 0.0022 * S.sens * (W.aim > 0.5 ? S.adsSens / W.zoom : 1);
  const mx = e.movementX, my = e.movementY;
  // Chrome's pointer lock sometimes reports one giant fake jump (often the wrong way) when you move far or fast.
  // drop any single event that is way bigger than how you've actually been moving the mouse.
  const mag = Math.abs(mx) + Math.abs(my);
  const now = performance.now();
  if (now - lockedAt < 120) return; // first events after locking are often garbage
  if (mag > 90 && mag > mouseAvg * 6) { mouseAvg = Math.max(mouseAvg, mag / 6) * 0.5 + mouseAvg * 0.5; return; }
  mouseAvg = mouseAvg * 0.85 + mag * 0.15;
  ME.yaw -= mx * s;
  ME.pitch = Math.max(-1.55, Math.min(1.55, ME.pitch - my * s));
});
addEventListener('blur', () => { for (const k in keys) keys[k] = false; W.held = false; W.aimHeld = false; });
addEventListener('resize', resizePreview);

function renderScores() {
  const rows = [{ name: G.myName, color: G.myColor, k: G.kills, d: G.deaths, me: true, card: cardUrlFor(G.myId) }];
  for (const r of G.remotes.values()) if (!(r.bot && r.name === 'Dummy')) rows.push({ id: r.id, name: r.name, color: r.color, k: r.k, d: r.d, card: cardUrlFor(r.id) });
  rows.sort((a, b) => b.k - a.k || a.d - b.d);
  if (G.round && GAMES[G.round.game] && GAMES[G.round.game].teams) {
    const team = (r) => (r.me ? G.myTeam : (G.remotes.get(r.id) || {}).team || 0);
    const out = [];
    for (const t of [1, 2]) {
      const mine = rows.filter((r) => team(r) === t);
      const sc = G.round.game === 'bomb' && G.round.bomb ? G.round.bomb.wins[t - 1] : (G.round.sc || [0, 0])[t - 1];
      out.push({ name: `${TEAMS[t].name} · ${sc}`, color: TEAMS[t].color, k: '', d: '' }, ...mine);
    }
    hud.scores(true, out);
    return;
  }
  hud.scores(true, rows);
}
function nameOf(id) {
  if (id === G.myId) return [G.myName, G.myColor];
  const n = G.names.get(id);
  return n ? [n.name, n.color] : ['???', '#aaa'];
}
function updateLabel() {
  const g = G.round && G.round.game && G.round.game !== 'dm' && GAMES[G.round.game] ? ` · ${GAMES[G.round.game].name}` : '';
  hud.label(`${MODES[G.mode] ? MODES[G.mode].name : ''}${g} · ${MAPS[G.cfg.map] ? MAPS[G.cfg.map].name : ''}${G.mode === 'training' ? ' · infinite ammo' : ''}`);
}

// ------------------------------------------------------------ world entities
function skinOf(owner, wid) { return (owner === G.myId ? G.equipped : (G.skins.get(owner) || {}))[wid]; }
function spawnProj(m) {
  const w = WEAPONS[m.k];
  if (!w) return;
  const mesh = buildProjectile(m.k, skinOf(m.o, m.k));
  G.scene.add(mesh);
  const pr = { id: m.id, k: m.k, o: m.o, p: m.p.slice(), v: m.v.slice(), r: w.r, bounce: w.bounce || 0, mesh, spin: 0, tip: m.tip || 0 };
  if (m.k === 'bow' && mesh.userData.tip) mesh.userData.tip.material = M(tipColor(m.tip), true);
  if (m.k === 'bow' && m.o !== G.myId) sfx.bowShot(m.p);
  mesh.position.set(...pr.p);
  G.projs.set(m.id, pr);
}
function addPeel(m) {
  const mesh = buildPeel();
  mesh.position.set(m.p[0], m.p[1], m.p[2]);
  mesh.rotation.y = Math.random() * 6.28;
  G.scene.add(mesh);
  G.peels.set(m.id, mesh);
}
function addHole(m) {
  const mesh = buildHole();
  mesh.position.set(...m.p);
  if (m.big) mesh.userData.big = true;
  G.scene.add(mesh);
  G.holes.set(m.id, { mesh, p: m.p, born: performance.now() - (m.age || 0) * 1000 });
  sfx.hole(m.p);
}
function addRemoteInfo(p) {
  G.names.set(p.id, { name: p.name, color: p.color, bot: p.bot, level: p.level, look: p.look, card: p.card || '', skins: p.skins || {}, team: p.team || 0 });
  G.skins.set(p.id, p.skins || {});
}

// ------------------------------------------------------------ net handlers
net.on('welcome', (m) => {
  G.myId = m.id; G.myName = m.name; G.myColor = m.color; G.joined = true; connecting = false;
  G.mode = m.mode; G.cfg = m.cfg;
  loadMap(m.cfg.map);
  ME.pos = m.pos.slice(); ME.vel = [0, 0, 0]; ME.alive = true; ME.hp = 100; ME.seq = m.q;
  ME.yaw = Math.atan2(m.pos[0], m.pos[2]);
  if (m.mode === 'training') ME.yaw = 0;
  G.spawnT = performance.now();
  for (const p of m.players) addRemoteInfo(p);
  for (const pl of m.peels) addPeel(pl);
  for (const pr of m.projs) spawnProj(pr);
  for (const h of m.holes || []) addHole(h);
  hud.wave(m.wave);
  renderRound(m.round);
  $('roundEnd').classList.add('hidden');
  G.round = m.round; G.myTeam = m.team || 0;
  G.pocket = []; G.streakN = 0; renderStreak(0);
  G.kat.clear(); setMyKatana(0);
  for (const [id, n] of m.kat || []) G.kat.set(id, n);
  setupObjectives(m.cfg.map);
  clearTags();
  for (const g of m.tags || []) addTag(g.id, g.p, g.team);
  showVote(m.vote);
  refillAmmo();
  applyLoadout(true);
  updateLabel();
  $('status').textContent = '';
  const tips = {
    ffa: 'T to chat, B for menu. Change the map or hipfire in Match Settings.',
    bots: 'bots are dumb but there are a lot of them. B for menu.',
    coop: 'survive the waves. bots only hurt humans, no friendly fire.',
    training: 'dummies respawn instantly. knock the ones on the left ledge off. movement playground on the right.',
  };
  hud.chat(null, null, `you are ${m.name}. ${tips[m.mode] || ''}`);
});
net.on('cfg', (m) => {
  const mapChanged = m.cfg.map !== G.cfg.map;
  G.cfg = m.cfg;
  if (mapChanged) { loadMap(m.cfg.map); clearEntities(); setupObjectives(m.cfg.map); }
  updateLabel();
  if (screen === 'match') syncMatchUI();
});
net.on('clear', () => clearEntities());
net.on('wave', (m) => {
  hud.wave(m);
  if (m.start) { hud.msg(`WAVE ${m.n}`, 2, 'brag'); sfx.kill(); }
  if (m.done) hud.msg(`WAVE ${m.n} CLEARED`, 2, 'brag');
});
net.on('pj', (m) => addRemoteInfo(m));
net.on('pl', (m) => {
  const r = G.remotes.get(m.id);
  if (r) { r.dispose(); G.remotes.delete(m.id); }
  G.names.delete(m.id);
  G.skins.delete(m.id);
  if (ME.hook && ME.hook.target === m.id) releaseHook();
});
net.on('sk', (m) => {
  G.skins.set(m.id, m.s || {});
  const r = G.remotes.get(m.id);
  if (r) r.setSkins(m.s);
});
net.on('lk', (m) => {
  if (m.id === G.myId) { G.myColor = m.color; return; }
  const n = G.names.get(m.id);
  if (n) { n.look = m.look; n.color = m.color; }
  const r = G.remotes.get(m.id);
  if (r) r.setLook(m.look, m.color);
});
// an achievement just popped mid-match
net.on('ach', (m) => {
  const a = ACHIEVEMENTS[m.id];
  if (!a) return;
  if (account.me) { account.me.achs = [...new Set([...(account.me.achs || []), m.id])]; }
  const rewards = rewardsFor(m.id).map((x) => x.name).join(', ');
  hud.msg(`ACHIEVEMENT: ${a.name}`, 3, 'brag');
  hud.chat(null, null, `achievement unlocked: ${a.name} (${a.desc})${rewards ? ' · unlocked ' + rewards + ' in CHARACTER' : ''}`);
  sfx.kill();
});
net.on('sn', (m) => {
  recordSnap(m);
  const off = m.s - performance.now();
  if (!G.offsetInit || Math.abs(off - G.offset) > 1000) { G.offset = off; G.offsetInit = true; }
  else G.offset += (off - G.offset) * 0.05;
  for (const e of m.p) {
    const id = e[0];
    if (id === G.myId) { ME.hp = e[10]; G.kills = e[14]; G.deaths = e[15]; continue; }
    let r = G.remotes.get(id);
    if (!r) {
      const n = G.names.get(id) || { name: '???', color: '#ffffff' };
      r = new Remote(id, n.level ? `${n.name} [${n.level}]` : n.name, n.color, G.skins.get(id) || {}, n.bot, n.look);
      r.team = n.team || 0;
      r.katN = G.kat.get(id) || 0;
      G.remotes.set(id, r);
    }
    r.snap(m.s, e);
  }
  if (m.wave) hud.wave(m.wave);
  if (m.round) { if (!G.round || G.round.game !== m.round.game) { G.round = m.round; updateLabel(); } G.round = m.round; }
  renderRound(m.round);
  if (scoresOpen) renderScores();
});
// ------------------------------------------------------------ modes: teams, tags, bomb, vote
net.on('teams', (m) => {
  for (const [id, team, color] of m.list) {
    if (id === G.myId) { G.myTeam = team; G.myColor = color; continue; }
    const n = G.names.get(id);
    if (n) { n.team = team; n.color = color; }
    const r = G.remotes.get(id);
    if (r) { r.team = team; if (r.color !== color) r.setLook(r.outfit, color); }
  }
  if (G.round) G.round.game = m.game;
  updateLabel();
  if (GAMES[m.game] && GAMES[m.game].teams && G.myTeam) hud.msg(`YOU ARE ${TEAMS[G.myTeam].name}`, 2, 'brag');
});
net.on('tag+', (m) => addTag(m.id, m.p, m.team));
net.on('tagc', () => clearTags());
net.on('tagx', (m) => {
  removeTag(m.id);
  if (m.by === G.myId) { hud.msg(m.k === 'confirm' ? 'KILL CONFIRMED +1' : 'KILL DENIED', 1.2, 'brag'); if (m.k === 'confirm') sfx.cash(); else sfx.ting(); }
});
net.on('bombyou', () => { hud.msg('YOU HAVE THE BOMB', 2, 'brag'); hud.chat(null, null, 'you have the bomb: get to site A or B and hold F to plant'); });
net.on('bombev', (m) => {
  const [n] = m.id ? nameOf(m.id) : [''];
  if (m.k === 'round') { hud.msg(`ROUND ${m.n} · ${G.myTeam === m.att ? 'ATTACK' : 'DEFEND'}`, 2.2, 'brag'); }
  else if (m.k === 'planted') { hud.msg(`BOMB PLANTED AT ${m.site}`, 2.2, 'brag'); sfx.ting(); hud.chat(null, null, `${n} planted the bomb at ${m.site}`); }
  else if (m.k === 'defused') { hud.msg('BOMB DEFUSED', 2.2, 'brag'); sfx.kill(); hud.chat(null, null, `${n} defused the bomb`); }
  else if (m.k === 'boom') { G.shake = 1; }
  else if (m.k === 'drop') hud.chat(null, null, 'the bomb was dropped');
  else if (m.k === 'pickup') hud.chat(null, null, `${n} picked up the bomb`);
  else if (m.k === 'win') {
    const mine = m.team === G.myTeam;
    const why = { defused: 'bomb defused', exploded: 'bomb went off', time: 'time ran out' }[m.why] || '';
    hud.msg(`${TEAMS[m.team].name} WINS THE ROUND`, 3, 'brag');
    hud.chat(null, null, `${TEAMS[m.team].name} wins the round (${why}) · ${m.wins[0]} - ${m.wins[1]}`);
    if (mine) sfx.kill();
  }
});
// ------------------------------------------------------------ items: charges, bubbles, smoke, frost
net.on('ic', (m) => syncItem(m.i, m.n, m.next));
// the katana grows: everyone sees how long yours is
G.kat = new Map();
net.on('kat', (m) => {
  G.kat.set(m.id, m.n);
  if (m.id === G.myId) { setMyKatana(m.n); if (m.n) hud.msg(`KATANA GROWS · ${m.n} kill${m.n > 1 ? 's' : ''}`, 1.3, 'brag'); return; }
  const r = G.remotes.get(m.id); if (r) r.setKat(m.n);
});
G.bubbles = new Map();
function addBubble(m) {
  const mesh = new THREE.Mesh(new THREE.IcosahedronGeometry(m.r, 2), new THREE.MeshBasicMaterial({ color: 0x4fd8ff, transparent: true, opacity: 0.22, depthWrite: false, side: THREE.DoubleSide }));
  const wire = new THREE.Mesh(mesh.geometry, new THREE.MeshBasicMaterial({ color: 0xbff4ff, wireframe: true, transparent: true, opacity: 0.35 }));
  mesh.add(wire);
  mesh.position.set(...m.p);
  G.scene.add(mesh);
  G.bubbles.set(m.id, { mesh, until: performance.now() + (m.left || 7000) });
}
net.on('bub+', (m) => { addBubble(m); sfx.reverse(m.p); });
net.on('bubx', (m) => { const b = G.bubbles.get(m.id); if (b) { G.scene.remove(b.mesh); G.bubbles.delete(m.id); sfx.pop(b.mesh.position.toArray()); } });
G.smokes = [];
net.on('smoke', (m) => { G.smokes.push({ p: m.p, r: m.r, until: performance.now() + m.dur }); sfx.blow(m.p); });
net.on('frost', (m) => {
  if (m.id === G.myId) { G.frost = m.n; hud.msg(`${'❄'.repeat(m.n)} FROSTY`, 0.8); }
  const r = G.remotes.get(m.id); if (r) fx.spray([r.pos[0], r.pos[1] + 1.2, r.pos[2]], 10, [0xffffff, 0xbfe8ff], 3, 0.6, 0.1, 2, 1);
});
net.on('freeze', (m) => {
  if (m.id === G.myId) { ME.frozenUntil = performance.now() + m.dur; G.frost = 0; releaseHook(); hud.msg('FROZEN SOLID', m.dur / 1000, 'slip'); sfx.ting(); }
  const r = G.remotes.get(m.id); if (r) { r.frozenUntil = performance.now() + m.dur; sfx.ting(r.pos); }
});

// hold F to plant / defuse: keep telling the server while it's held, and stand still
let useTimer = 0;
function startUse() {
  stopUse();
  G.using = true;
  net.send({ t: 'use' });
  useTimer = setInterval(() => { if (!G.using || !ME.alive) { stopUse(); return; } net.send({ t: 'use' }); }, 200);
}
function stopUse() { clearInterval(useTimer); useTimer = 0; G.using = false; }
// vote for the next match: press 1 / 2 / 3
let myVote = -1;
function showVote(v) {
  const panel = $('votePanel');
  G.vote = v;
  if (!v) { panel.classList.add('hidden'); myVote = -1; return; }
  panel.classList.remove('hidden');
  G.voteEnds = performance.now() + (v.left || 0);
  const box = $('voteOpts');
  box.innerHTML = '';
  v.options.forEach((o, i) => {
    const d = document.createElement('div');
    d.className = 'vopt' + (i === myVote ? ' on' : '');
    const k = document.createElement('b'); k.textContent = String(i + 1);
    const t = document.createElement('span'); t.textContent = `${o.name} · ${o.mapName}`;
    const c = document.createElement('i'); c.textContent = String((v.counts || [])[i] || 0);
    d.append(k, t, c);
    box.append(d);
  });
}
function castVote(i) { if (!G.vote || i >= G.vote.options.length) return; myVote = i; net.send({ t: 'vote', i }); showVote(G.vote); sfx.click(); }
net.on('vote', (m) => { myVote = -1; showVote(m); });
net.on('votes', (m) => { if (G.vote) { G.vote.counts = m.counts; showVote(G.vote); } });

// randomizer mode: the server hands you a loadout each life (null = use your own again)
net.on('loadout', (m) => {
  G.forcedLoadout = m.lo || null;
  setLoadout(m.lo || S.loadout);
  refillAmmo();
  if (m.lo) hud.msg(`${wname(m.lo.primary)} · ${wname(m.lo.secondary)} · ${wname(m.lo.melee)}`, 2.2, 'brag');
});
net.on('kb', (m) => applyKb(m.v));
net.on('slip', () => slip(performance.now()));
net.on('dmg', (m) => {
  const target = m.to === G.myId ? null : G.remotes.get(m.to);
  if (m.to === G.myId) {
    ME.hp -= m.a;
    hud.hp(ME.hp);
    hud.hurt(m.a);
    if (m.hs) sfx.headshotTaken(m.ko); else sfx.hurt();
    if (m.w === 'cig') G.burnUntil = performance.now() + 600;
  }
  if (target) {
    if (m.w === 'cig') target.burnUntil = performance.now() + 700;
    // pixel blood: everyone sees it except the person bleeding
    if (S.blood && m.a > 0) {
      const src = m.from === G.myId ? ME.pos : G.remotes.get(m.from) ? G.remotes.get(m.from).pos : null;
      const c = [target.pos[0], target.pos[1] + (m.hs ? 1.7 : 1.1), target.pos[2]];
      let dir = [0, 0, 0];
      if (src) { const dx = c[0] - src[0], dz = c[2] - src[2], l = Math.hypot(dx, dz) || 1; dir = [dx / l, 0, dz / l]; }
      const fl = raycast([target.pos[0], target.pos[1] + 0.5, target.pos[2]], [0, -1, 0], 6, BOXES);
      fx.blood(c, dir, Math.min(100, m.a), fl ? fl.point[1] : null);
    }
  }
  if (m.from === G.myId && m.to !== G.myId) {
    hud.hit(m.hs);
    if (m.hs) sfx.headshot(m.ko); else sfx.hit();
    if (target) {
      const v = new THREE.Vector3(target.pos[0], target.pos[1] + 2, target.pos[2]).project(G.camera);
      if (v.z < 1) hud.dmgNum((v.x * 0.5 + 0.5) * innerWidth + (Math.random() - 0.5) * 30, (-v.y * 0.5 + 0.5) * innerHeight, m.a, m.hs);
    }
  }
});
net.on('kill', (m) => {
  recordEv(m);
  const [kn, kc] = nameOf(m.k), [vn, vc] = nameOf(m.v);
  const via = m.w === 'void' || m.w === 'cough' ? m.via : m.w;
  const victim = G.remotes.get(m.v);
  const kfx = m.fx && m.fx !== 'none' ? m.fx : null;
  if (victim) {
    const vi = G.names.get(m.v) || {};
    const replaced = kfx && playKillFx(kfx, { pos: victim.pos.slice(), vel: m.vel || victim.vel, yaw: victim.yaw, color: victim.color, look: vi.look, name: vi.name });
    if (replaced) victim.ch.root.visible = false; else victim.breakApart(m.vel || victim.vel);
  } else if (m.v === G.myId && kfx) playKillFx(kfx, { pos: ME.pos.slice(), vel: m.vel || ME.vel, yaw: ME.yaw, color: G.myColor, look: validLook(G.settings.look, myAchs()), name: G.myName });
  const dummy = victim && victim.bot && victim.name === 'Dummy';
  let parts;
  if (m.w === 'void') {
    parts = m.k ? [[kn, kc], [`  [${wname(via)}]  `, wcolor(via)], [vn, vc], ['  into the void', '#aaa']] : [[vn, vc], ['  fell into the void', '#aaa']];
  } else if (m.w === 'tbag' && m.k === 0) {
    parts = [[vn, vc], ['  t-bagged too hard and exploded', '#ff9a3a']];
  } else if (m.w === 'cough') {
    parts = m.k ? [[kn, kc], [`  [${wname(via)}]  `, wcolor(via)], [vn, vc], ['  (coughed)', '#aaa']] : [[vn, vc], ['  smoked too much', '#aaa']];
  } else if (!m.k) {
    parts = [[vn, vc], ['  died', '#aaa']];
  } else {
    parts = [[kn, kc], [`  [${wname(via)}]  `, wcolor(via)], [vn, vc]];
  }
  if (!dummy) hud.feed(parts);
  if (m.v === G.myId) {
    ME.alive = false;
    releaseHook();
    W.held = false; W.aimHeld = false;
    stopLoops();
    G.deadAt = performance.now();
    sfx.death();
    deathCard(m.k && m.k !== G.myId ? m.k : 0, via);
    if (m.k && m.k !== G.myId && S.killcam !== false && G.mode !== 'training') queueKillcam(m.k, via);
    if (m.k) {
      hud.dead(true, m.w === 'void'
        ? [[kn, kc], [' knocked you into the void', '#fff'], [`  (${wname(via)})`, wcolor(via)]]
        : [['killed by ', '#fff'], [kn, kc], [`  (${wname(via)})`, wcolor(via)]]);
    } else hud.dead(true, [[m.w === 'void' ? 'you fell into the void' : m.w === 'tbag' ? 'you t-bagged too hard. your knees exploded.' : 'you smoked too much', '#fff']]);
  }
  if (m.k === G.myId && m.v !== G.myId) {
    sfx.kill();
    hud.msg(dummy ? 'dummy down' : `killed ${vn}`, 1.4, 'brag');
  }
});
net.on('spawn', (m) => {
  endKillcam();
  resetItems(); ME.frozenUntil = 0; G.frost = 0;
  ME.pos = m.p.slice(); ME.vel = [0, 0, 0]; ME.alive = true; ME.hp = 100; ME.seq = m.q;
  ME.slipUntil = 0; ME.combo = 0; ME.sleepUntil = 0;
  G.spawnT = performance.now();
  refillAmmo();
  if (G.pendingLoadout) applyLoadout(true);
  hud.dead(false);
});
net.on('ps', (m) => {
  spawnProj(m);
  if (m.o !== G.myId) {
    const s = { chicken: 'squawk', duck: 'squeak', bowling: 'thunk', slipper: 'swing' }[m.k] || 'pew';
    sfx[s](m.p);
  }
});
net.on('pu', (m) => {
  const pr = G.projs.get(m.id);
  if (pr && pr.k === 'slipper') return slipperUpdate(pr, m); // homing: steer between updates, ease corrections
  if (pr) { pr.p = m.p.slice(); pr.v = m.v.slice(); }
});
net.on('pd', (m) => {
  const pr = G.projs.get(m.id);
  if (pr) {
    G.scene.remove(pr.mesh);
    G.projs.delete(m.id);
    if (pr.k === 'slipper' && pr.o === G.myId) onSlipperBack();
  }
  if (m.x) {
    recordEv(m);
    fx.explosion(m.p, WEAPONS.chicken.radius);
    sfx.boom(m.p);
    const d = Math.hypot(m.p[0] - ME.pos[0], m.p[1] - ME.pos[1], m.p[2] - ME.pos[2]);
    G.shake = Math.max(G.shake, Math.max(0, 1 - d / 30));
  }
  if (m.b) {
    if (pr && pr.k === 'snowball') { fx.spray(m.p, 18, [0xffffff, 0xdff4ff], 5, 0.6, 0.12, 8, 1); sfx.thwack(m.p); }
    else { fx.splat(m.p); sfx.bonk(m.p); }
  }
  if (m.st && pr) { // arrow stuck in a wall: leave it there for a while
    const mesh = buildProjectile('bow');
    if (mesh.userData.tip) mesh.userData.tip.material = M(tipColor(m.tip), true);
    mesh.position.set(...m.p);
    mesh.lookAt(m.p[0] - m.d[0], m.p[1] - m.d[1], m.p[2] - m.d[2]);
    G.scene.add(mesh);
    setTimeout(() => G.scene.remove(mesh), 8000);
    sfx.thwack(m.p);
  }
});
net.on('tip', (m) => { G.tip = m.tip; });
net.on('hand', (m) => { G.hand = m.hand || []; });
net.on('tp', (m) => { ME.pos = m.p.slice(); fx.glitch(ME.pos, [0, 0, 0], 20); sfx.reverse(); });
net.on('heal', (m) => {
  if (m.id === G.myId) { ME.hp = m.hp; hud.msg(`+${m.a} HP`, 0.8); sfx.heal(); }
  const r = G.remotes.get(m.id);
  if (r) for (let i = 0; i < 12; i++) fx.burn([r.pos[0], r.pos[1], r.pos[2]]);
});
net.on('sleep', (m) => { ME.sleepUntil = performance.now() + m.dur * 1000; releaseHook(); hud.msg('zzz...', m.dur, 'slip'); sfx.snore(); });
net.on('boom', (m) => {
  recordEv(m);
  fx.explosion(m.p, m.r); sfx.boom(m.p);
  const d = Math.hypot(m.p[0] - ME.pos[0], m.p[1] - ME.pos[1], m.p[2] - ME.pos[2]);
  G.shake = Math.max(G.shake, Math.max(0, 1 - d / 25));
});
G.clouds = new Map();
net.on('cloud', (m) => { G.clouds.set(m.id, { p: m.p, born: performance.now() }); });
net.on('cloudx', (m) => { G.clouds.delete(m.id); });
net.on('pe', (m) => { addPeel(m); sfx.splat(m.p); });
net.on('pr', (m) => {
  const mesh = G.peels.get(m.id);
  if (mesh) {
    const p = [mesh.position.x, mesh.position.y, mesh.position.z];
    if (m.s) { fx.splat(p); sfx.whoops(p); }
    G.scene.remove(mesh);
    G.peels.delete(m.id);
  }
});
net.on('hs', (m) => addHole(m));
net.on('he', (m) => {
  recordEv(m);
  const h = G.holes.get(m.id);
  if (h) { G.scene.remove(h.mesh); G.holes.delete(m.id); }
  fx.blast(m.p, WEAPONS.duck.blastR);
  sfx.holePop(m.p);
  const d = Math.hypot(m.p[0] - ME.pos[0], m.p[1] - ME.pos[1], m.p[2] - ME.pos[2]);
  G.shake = Math.max(G.shake, Math.max(0, 1 - d / 25));
});
net.on('fx', (m) => {
  if (m.k === 'shot' || m.k === 'swing' || m.k === 'tbag') recordEv(m);
  const r = G.remotes.get(m.id);
  if (m.k === 'shot') {
    const w = WEAPONS[m.w];
    if (!w) return;
    const fast = w.rate > 8;
    const mz = r ? r.muzzle() : null;
    const color = () => tracerColor((G.skins.get(m.id) || {})[m.w], w.tracer || 0xfff0a0);
    if (w.marbles) {
      const sk = (G.skins.get(m.id) || {})[m.w];
      marbles.shootSegs(m.s, mz, sk && sk[3] === 'marbles_gumball' ? 'gumball' : 'glass');
      if (m.s.length) sfx.gun(m.w, m.s[0].slice(0, 3));
      return;
    }
    m.s.forEach((s, i) => {
      const a = mz && (i === 0 || w.pellets) ? mz : s.slice(0, 3);
      fx.tracer(a, s.slice(3), color(), w.thick || (fast ? 0.03 : 0.045), fast ? 0.07 : 0.2);
    });
    if (m.s.length) sfx.gun(m.w, m.s[0].slice(0, 3));
  } else if (m.k === 'shatter') {
    fx.spray(m.p, 70, [0xffffff, 0xbfe8ff, 0x7fd0ff], 11, 1.4, 0.2, 14, 0.5);
    sfx.crunch(m.p); sfx.ting(m.p);
    if (r) r.frozenUntil = 0;
  } else if (m.k === 'medkit') {
    const src = m.id === G.myId ? ME.pos : r ? r.pos : null;
    if (src) fx.spray([src[0], src[1] + 1.2, src[2]], 16, [0x7dff4f, 0xffffff], 3, 1.0, 0.14, -2, 1);
  } else if (m.k === 'bubhit') {
    fx.spray(m.p, 8, [0x4fd8ff, 0xffffff], 4, 0.3, 0.1, 0, 2); sfx.ricochet(m.p);
  } else if (m.k === 'burn') {
    if (r) r.burnUntil = performance.now() + 600;
    if (m.id === G.myId) G.burnUntil = performance.now() + 600;
  } else if (m.k === 'card') {
    if (r) r.swingT = performance.now();
    const who = m.id === G.myId ? 'you' : nameOf(m.id)[0];
    if (m.joker) { sfx.laugh(r ? r.pos : null); hud.chat(null, null, `${who} played a joker`); }
    if (m.suit === 'h' && r) sfx.heal(r.pos);
    if (m.suit === 'c') { const src = m.id === G.myId ? ME.pos : r ? r.pos : null; if (src) fx.confetti([src[0], src[1] + 1.2, src[2]], [0, 1, 0], [0, 0, 0]); sfx.popper(src); }
    if (m.suit === 'd') sfx.pad(r ? r.pos : null);
    if (m.ult && m.id === G.myId) hud.msg(m.joker ? 'JOKER!' : 'ULTIMATE', 1.2, 'brag');
  } else if (m.k === 'strikeCall') {
    sfx.squawk(m.p); hud.chat(null, null, `${nameOf(m.id)[0]} called in a chicken strike`);
  } else if (m.k === 'tbag') {
    fx.explosion(m.p, 6);
    sfx.boom(m.p); sfx.tbag(m.p);
    const d = Math.hypot(m.p[0] - ME.pos[0], m.p[1] - ME.pos[1], m.p[2] - ME.pos[2]);
    G.shake = Math.max(G.shake, Math.max(0, 1 - d / 25));
  } else if (m.k === 'swing') {
    if (r) r.swingT = performance.now();
    if (m.w === 'popper') {
      if (r) fx.confetti(r.muzzle(), r.look(), r.vel);
      sfx.popper(m.a);
    } else sfx.swing(m.a);
  } else if (m.k === 'reverse') {
    if (r) r.reverseUntil = performance.now() + m.dur * 1000;
    if (m.id !== G.myId) sfx.reverse(r ? r.pos : null);
  } else if (m.k === 'reflect') {
    if (m.by === G.myId) { hud.msg('REVERSED', 1.2, 'reverse'); sfx.reverse(); }
    if (m.id === G.myId) hud.msg('REVERSED THEM', 1.0, 'reverse');
  } else if (m.k === 'strike') {
    sfx.strike(m.p);
    if (m.n >= 2) hud.msg(m.n >= 3 ? 'STRIKE' : 'SPARE', 1.2, 'brag');
  } else if (m.k === 'thwack') {
    sfx.thwack(m.p);
  }
});
net.on('chat', (m) => {
  if (!m.id) { hud.chat(null, null, m.m); return; }
  const [n, c] = nameOf(m.id);
  hud.chat(n, c, m.m);
});
net.on('po', (m) => { G.ping = Math.round(performance.now() - m.c); hud.ping(G.ping); });

// ------------------------------------------------------------ main loop
let last = performance.now(), acc = 0, sendT = 0, pingT = 0, fovNow = S.fov, fpsAcc = 0, fpsN = 0;
const STEP = 1 / 120;

const tmpDir = new THREE.Vector3();
function frame(t) {
  requestAnimationFrame(frame);
  let dt = (t - last) / 1000;
  last = t;
  if (dt > 0.1) dt = 0.1;
  if (dt <= 0) return;
  const now = performance.now();

  if (G.joined) {
    const frozen = now < (ME.frozenUntil || 0);
    if (frozen) { ME.vel[0] = 0; ME.vel[2] = 0; }
    const playing = $('menu').classList.contains('hidden') && !chatOpen && now >= (ME.sleepUntil || 0) && !RP.active && !G.using && !frozen;
    const inp = playing ? {
      f: keys.KeyW, b: keys.KeyS, l: keys.KeyA, r: keys.KeyD, jump: keys.Space, jumpPressed,
      sprint: keys.ShiftLeft || keys.ShiftRight,
      crouch: keys.KeyC || keys.ControlLeft || keys.ControlRight,
    } : {};
    jumpPressed = false;
    acc += dt;
    while (acc >= STEP) { stepPlayer(STEP, inp, now); inp.jumpPressed = false; acc -= STEP; }
    // spinbot killstreak: lock onto the nearest enemy you can see
    const spinning = ME.alive && now < (G.spinUntil || 0);
    if (spinning) {
      const e = eye();
      let best = null, bd = 1e9;
      for (const r of G.remotes.values()) {
        if (!r.alive || (r.bot && r.name === 'Dummy' && G.mode !== 'training') || (G.myTeam && r.team === G.myTeam)) continue;
        const tx = r.pos[0] - e[0], ty = r.pos[1] + 2.0 - e[1], tz = r.pos[2] - e[2], d = Math.hypot(tx, ty, tz);
        if (d > 150 || d < 0.5 || d >= bd) continue;
        if (raycast(e, [tx / d, ty / d, tz / d], d, BOXES)) continue;
        best = [tx, ty, tz]; bd = d;
      }
      if (best) {
        const yaw = Math.atan2(-best[0], -best[2]), pitch = Math.atan2(best[1], Math.hypot(best[0], best[2]));
        let dy = yaw - ME.yaw; while (dy > Math.PI) dy -= Math.PI * 2; while (dy < -Math.PI) dy += Math.PI * 2;
        ME.yaw += dy * Math.min(1, dt * 25); ME.pitch += (pitch - ME.pitch) * Math.min(1, dt * 25);
      }
    }
    $('cheat').style.display = spinning ? 'block' : 'none';
    if (spinning) $('cheat').textContent = `JANKHAX v6.9\n[x] AIMBOT\n[x] SPINBOT\n[x] NO SPREAD\n${((G.spinUntil - now) / 1000).toFixed(1)}s left`;
    G.spinning = spinning;
    updateWeapons(dt, now);

    sendT -= dt;
    if (sendT <= 0 && ME.alive) {
      sendT = 1 / 30;
      const r2 = (x) => Math.round(x * 100) / 100;
      const hp = hookPoint();
      net.send({
        t: 's', q: ME.seq, p: ME.pos.map(r2), v: ME.vel.map(r2), y: r2(G.spinning ? (now * 0.03) % (Math.PI * 2) : ME.yaw), x: r2(G.spinning ? Math.sin(now * 0.02) * 1.2 : ME.pitch), w: W.cur,
        g: hp ? hp.map(r2) : 0,
        f: W.flags | (now < ME.slipUntil ? FLAGS.SLIP : 0) | (ME.sliding ? FLAGS.SLIDE : 0) | (ME.crouching ? FLAGS.CROUCH : 0),
      });
    }
    pingT -= dt;
    if (pingT <= 0) { pingT = 2; net.send({ t: 'pi', c: performance.now() }); }
    if (!ME.alive) { if (G.killcamPending) $('deadTimer').textContent = 'killcam... (space to skip)'; else hud.deadTimer(Math.max(0, 2.5 - (now - (G.deadAt || now)) / 1000)); }
  }

  const rt = now + G.offset - INTERP_MS;
  if (!RP.active) for (const r of G.remotes.values()) r.update(rt, dt, now);
  else for (const r of G.remotes.values()) { r.ch.root.visible = false; r.rope.visible = false; r.shadow.visible = false; } // the replay has its own copies
  updateGibs(dt);
  updateKillFx(dt);
  for (const [id, b] of G.bubbles) { if (now > b.until + 500) { G.scene.remove(b.mesh); G.bubbles.delete(id); continue; } b.mesh.rotation.y += dt * 0.3; b.mesh.material.opacity = 0.18 + Math.sin(now * 0.006) * 0.05; }
  for (let i = G.smokes.length - 1; i >= 0; i--) {
    const s2 = G.smokes[i];
    if (now > s2.until) { G.smokes.splice(i, 1); continue; }
    for (let k = 0; k < 11; k++) { const a = Math.random() * 6.28, rr = Math.sqrt(Math.random()) * s2.r; fx.smoke([s2.p[0] + Math.cos(a) * rr, s2.p[1] + Math.random() * 3.5, s2.p[2] + Math.sin(a) * rr], 1, 0.4); }
  }
  $('freezeFx').style.opacity = now < (ME.frozenUntil || 0) ? 1 : Math.min(0.6, (G.frost || 0) * 0.15);
  if (G.joined) {
    updateObjectives(dt, now, G.round, ME.pos);
    const a = G.round && G.round.bomb && G.round.bomb.act;
    if (a && a.by === G.myId) hud.meter(a.f, a.k === 'plant' ? 'PLANTING... keep holding F' : 'DEFUSING... keep holding F', '#ff4f4f');
    if (G.vote) $('voteLeft').textContent = `${Math.max(0, Math.ceil((G.voteEnds - performance.now()) / 1000))}s`;
  }

  for (const pr of G.projs.values()) {
    if (pr.k === 'slipper') {
      slipperStep(pr, dt, now);
      pr.spin += dt * 20;
      pr.mesh.position.set(...pr.p);
      pr.mesh.rotation.set(0, pr.spin, 0.3);
    } else {
      stepProjectile(pr, dt, BOXES, WEAPONS[pr.k].grav);
      pr.mesh.position.set(pr.p[0], pr.p[1], pr.p[2]);
      if (pr.k === 'bow') { // point first along the flight path, no tumbling
        pr.mesh.lookAt(pr.p[0] - pr.v[0], pr.p[1] - pr.v[1], pr.p[2] - pr.v[2]);
      } else if (pr.k === 'card') { // flat and spinning like a thrown playing card
        pr.spin += dt * 30;
        pr.mesh.rotation.set(0, pr.spin, 0); // the model is already lying flat
      } else if (pr.k === 'chicken') {
        pr.mesh.lookAt(pr.p[0] - pr.v[0], pr.p[1] - pr.v[1], pr.p[2] - pr.v[2]);
        pr.mesh.rotateZ(now * 0.02);
        if (Math.random() < dt * 8) fx.feathers(pr.p, 1);
      } else if (pr.k === 'bowling') {
        const hs = Math.hypot(pr.v[0], pr.v[2]);
        pr.spin += (hs / 0.45) * dt;
        pr.mesh.rotation.set(-pr.spin, Math.atan2(pr.v[0], pr.v[2]), 0, 'YXZ');
      } else if (pr.k === 'duck') {
        pr.spin += dt * 10;
        pr.mesh.rotation.set(pr.spin * 0.5, pr.spin, 0);
      } else {
        pr.spin += dt * 18;
        pr.mesh.rotation.set(pr.spin, pr.spin * 0.7, 0);
      }
    }
    pr.mesh.visible = !RP.active;
    // speed streaks behind fast stuff
    if ((pr.k === 'bow' || pr.k === 'card') && !RP.active && S.speedLines !== false) {
      if (pr.lastP && Math.hypot(pr.p[0] - pr.lastP[0], pr.p[1] - pr.lastP[1], pr.p[2] - pr.lastP[2]) > 0.25) fx.tracer(pr.lastP, pr.p.slice(), pr.k === 'bow' ? tipColor(pr.tip) : 0xffffff, 0.02, 0.1);
      pr.lastP = pr.p.slice();
    }
    pr.mesh.updateMatrixWorld(true);
    if (!RP.active) emitSkinFx(G.skinFxWorld, pr.mesh, dt, 1);
  }
  for (const c of G.clouds.values()) for (let i = 0; i < 3; i++) {
    const a = Math.random() * 6.28, rr = Math.random() * 5;
    fx.smoke([c.p[0] + Math.cos(a) * rr, c.p[1] + Math.random() * 2, c.p[2] + Math.sin(a) * rr], 1, 0.3);
  }
  for (const h of G.holes.values()) {
    const age = (now - h.born) / 1000;
    const k = Math.min(1, age / 0.3);
    h.mesh.scale.setScalar(k * (1 + Math.sin(age * 20) * 0.08) * (h.mesh.userData.big ? 4 : 1));
    h.mesh.userData.orbit.rotation.y += dt * 6;
    h.mesh.userData.ring.rotation.z += dt * 3;
    fx.vortex(h.p, WEAPONS.duck.holeR * (h.mesh.userData.big ? 1.6 : 0.6));
  }

  // camera
  const cam = G.camera;
  const e = eye();
  cam.position.set(e[0], e[1], e[2]);
  let roll = 0, pOff = 0;
  if (now < ME.slipUntil) {
    const k = 1 - (ME.slipUntil - now) / (SLIP_TIME * 1000);
    roll = Math.sin(k * Math.PI * 4) * 0.5 * (1 - k);
    pOff = Math.sin(k * Math.PI) * 1.1;
  }
  if (now < (ME.sleepUntil || 0)) { pOff = -0.5 + Math.sin(now * 0.002) * 0.1; roll = 0.3; }
  $('sleepFx').style.opacity = now < (ME.sleepUntil || 0) ? 1 : 0;
  if (G.joined && !ME.alive) { pOff = -0.6; roll = 0.4; cam.position.y += Math.min(4, (now - (G.deadAt || now)) / 600); }
  if (!G.joined) { // menu backdrop: slow orbit over the current map
    const a = now * 0.00005;
    cam.position.set(Math.sin(a) * 40, 18, Math.cos(a) * 40);
    ME.yaw = a; ME.pitch = -0.35;
  }

  G.shake = S.shake ? Math.max(0, G.shake - dt * 2.2) : 0;
  const sh = G.shake * G.shake * 0.08;
  const pu = G.punch || { x: 0, y: 0, z: 0 };
  cam.rotation.set(Math.max(-1.57, Math.min(1.57, ME.pitch + pOff + pu.x)) + (Math.random() - 0.5) * sh, ME.yaw + pu.y + (Math.random() - 0.5) * sh, roll + pu.z);
  const hs = hspeed();
  const fovTarget = (S.fov + (S.fovKick ? Math.min(35, hs * 0.3) + (ME.sprinting ? 6 : 0) : 0)) / (W.zoom || 1);
  fovNow += (fovTarget - fovNow) * Math.min(1, dt * (W.aim > 0 ? 14 : 6));
  if (Math.abs(cam.fov - fovNow) > 0.05) { cam.fov = fovNow; cam.updateProjectionMatrix(); }
  if (RP.active) updateReplay(dt, now, cam); // killcam / play of the round owns the camera
  cam.updateMatrixWorld();
  updateSpeedLines(dt, G.joined && ME.alive && !RP.active ? Math.hypot(ME.vel[0], ME.vel[1], ME.vel[2]) : 0, ME.vel, cam, ME.dashing ? 0.9 : 0, S.speedLines !== false);
  const rh = G.renderer.domElement.height;
  fx.setScale(rh / (2 * Math.tan((cam.fov * Math.PI) / 360)));
  vmScaleU.value = rh / (2 * Math.tan((G.vmCamera.fov * Math.PI) / 360));
  if (RP.active) { cam.getWorldDirection(tmpDir); setListener([cam.position.x, cam.position.y, cam.position.z], Math.atan2(-tmpDir.x, -tmpDir.z)); } else setListener(e, ME.yaw);

  const hp = hookPoint();
  if (hp && ME.alive && !RP.active) { myRope.visible = true; setBeam(myRope, muzzleWorld(), hp, 0.05); } else myRope.visible = false;
  const shHit = G.joined ? raycast([ME.pos[0], ME.pos[1] + 0.1, ME.pos[2]], [0, -1, 0], 120, BOXES) : null;
  myShadow.visible = !!shHit && ME.alive && !ME.onGround && !RP.active;
  if (shHit) myShadow.position.set(ME.pos[0], shHit.point[1] + 0.03, ME.pos[2]);
  if (now < (G.burnUntil || 0)) fx.burn([ME.pos[0] + Math.sin(ME.yaw) * -0.8, ME.pos[1], ME.pos[2] - Math.cos(ME.yaw) * 0.8]);
  $('reverseFx').style.opacity = now < W.reverseUntil ? 1 : 0;

  if (G.joined) {
    hud.hp(ME.hp);
    hud.speed(hs);
    hud.combo(ME.combo);
  }
  fpsAcc += dt; fpsN++;
  if (fpsAcc > 0.5) { $('fps').textContent = S.showFps ? Math.round(fpsN / fpsAcc) + ' fps' : ''; fpsAcc = 0; fpsN = 0; }
  hud.update(dt);
  fx.update(dt);
  G.skinFxWorld.update(dt);
  G.skinFxVM.update(dt);
  skinTick(dt, now);
  updateWorld(dt);
  G.vmScene.visible = G.joined && !RP.active;
  renderFrame();
  if ((screen === 'cosmetics' || screen === 'character') && !$('menu').classList.contains('hidden')) renderPreview(dt);
}

// ------------------------------------------------------------ killstreaks
G.pocket = [];
// killstreak tray (bottom right): your 3 picks, the kills each needs, lit up when ready (press 5 / 6 / 7)
function renderStreak(n) {
  const tray = $('streakTray');
  const picks = validStreaks(S.loadout.streaks);
  const key = picks.join(',') + '|' + n + '|' + G.pocket.join(',');
  if (tray.dataset.key !== key) {
    tray.dataset.key = key;
    tray.innerHTML = '';
    picks.forEach((id, i) => {
      const st = STREAKS[id], ready = G.pocket.includes(id);
      const d = document.createElement('div');
      d.className = 'kstreak' + (ready ? ' ready' : '');
      d.title = `${st.name}: ${st.desc}`;
      const im = document.createElement('img'); im.src = streakIcon(id); im.alt = '';
      const k = document.createElement('b'); k.textContent = String(5 + i);
      const c = document.createElement('span'); c.textContent = ready ? 'READY' : `${Math.min(n, st.kills)}/${st.kills}`;
      d.append(im, k, c);
      tray.append(d);
    });
  }
  $('streak').textContent = n >= 2 ? `streak ${n}` : '';
}
function deployStreak(slot) {
  const id = validStreaks(S.loadout.streaks)[slot];
  if (!G.joined || !ME.alive || !id) return;
  if (!G.pocket.includes(id)) { hud.msg(`${STREAKS[id].name}: ${STREAKS[id].kills} kills in a row`, 1.2); sfx.empty(); return; }
  const e = eye(), d = lookDir();
  const h = raycast(e, d, 300, BOXES);
  const at = h ? h.point : [e[0] + d[0] * 60, e[1] + d[1] * 60, e[2] + d[2] * 60];
  G.pocket.splice(G.pocket.indexOf(id), 1);
  net.send({ t: 'deploy', r: id, at: at.map((x) => Math.round(x * 100) / 100) });
  hud.msg(STREAKS[id].name.toUpperCase(), 1.4, 'brag');
  renderStreak(G.streakN || 0);
}
function lookDir() { const cp = Math.cos(ME.pitch); return [-Math.sin(ME.yaw) * cp, Math.sin(ME.pitch), -Math.cos(ME.yaw) * cp]; }
net.on('streak', (m) => {
  if (m.reset) { // you died: the count starts over and active stuff ends. earned-but-unused streaks stay in the tray
    G.streakN = 0; G.satUntil = 0; G.spinUntil = 0; ME.moonUntil = 0;
    loseScythe();
    renderStreak(0);
    return;
  }
  if (m.earned) {
    const st = STREAKS[m.earned];
    if (!st) return;
    G.streakN = m.n;
    if (!G.pocket.includes(m.earned)) G.pocket.push(m.earned);
    const key = 5 + validStreaks(S.loadout.streaks).indexOf(m.earned);
    hud.msg(`${st.name.toUpperCase()} READY · PRESS ${key}`, 2.4, 'brag');
    sfx.kill();
    renderStreak(m.n);
    return;
  }
  // you activated one: switch it on here
  const st = STREAKS[m.reward];
  if (!st) return;
  if (m.reward === 'moonboots') ME.moonUntil = performance.now() + st.dur * 1000;
  if (m.reward === 'satellite') G.satUntil = performance.now() + st.dur * 1000;
  if (m.reward === 'spinbot') G.spinUntil = performance.now() + st.dur * 1000;
  if (m.reward === 'scythe') grantScythe();
  toast(st.desc, 2500);
});

// ------------------------------------------------------------ toast
let toastT = null;
function toast(text, ms = 2200) {
  const t = $('toast');
  t.textContent = text;
  t.style.opacity = 1;
  clearTimeout(toastT);
  toastT = setTimeout(() => { t.style.opacity = 0; }, ms);
  if (!$('menu').classList.contains('hidden')) $('status').textContent = text;
}

// ------------------------------------------------------------ name cards, kill effects, killcam
function cardUrlFor(id) {
  if (id === G.myId || id === 'me') return S.card || defaultCard(G.myName || S.name || (account.me && account.me.name) || 'you', G.myColor || (S.look && S.look.color) || '#ff4fd8');
  const n = G.names.get(id) || {};
  return (S.showCards !== false && n.card) || defaultCard(n.name || '???', n.color || '#ffffff');
}
function myKfx() { return ownedKill(S.kfx || 'none', G.inv); }
function setKfx(id) {
  S.kfx = id;
  saveSettings();
  if (G.joined) net.send({ t: 'kfx', id });
  if (screen === 'character') buildCharacterUI();
}
net.on('cd', (m) => { const n = G.names.get(m.id); if (n) n.card = m.card || ''; });
function infoOf(id) {
  if (id === G.myId) return { name: G.myName, color: G.myColor, skins: G.equipped, look: validLook(S.look, myAchs()), bot: false };
  const n = G.names.get(id) || {};
  return { name: n.name || '???', color: n.color || '#ffffff', skins: G.skins.get(id) || {}, look: n.look || null, bot: !!n.bot, level: n.level };
}
// the death screen shows whoever killed you, on their name card
function deathCard(killer, via) {
  const el = $('deadCard');
  el.innerHTML = '';
  if (!killer) return;
  const [kn, kc] = nameOf(killer);
  el.append(cardEl(cardUrlFor(killer), kn, wname(via), kc));
}
function showReplayUI(title, url, name, color, sub, hint) {
  $('rpTitle').textContent = title;
  $('rpCard').innerHTML = '';
  $('rpCard').append(cardEl(url, name, sub, color));
  $('rpHint').textContent = hint || '';
  $('rpFeed').innerHTML = '';
  $('replay').classList.remove('hidden');
}
function hideReplayUI() { $('replay').classList.add('hidden'); }
function replayFeed(k, info) {
  const nm = (id) => (info && info[id] ? [info[id].name, info[id].color] : nameOf(id));
  const d = document.createElement('div');
  const [a, ac] = nm(k.k), [b, bc] = nm(k.v);
  const via = k.w === 'void' || k.w === 'cough' ? k.via : k.w;
  for (const [t, c] of k.k ? [[a, ac], [`  [${wname(via)}]  `, wcolor(via)], [b, bc]] : [[b, bc], ['  died', '#aaa']]) {
    const sp = document.createElement('span'); sp.textContent = t; sp.style.color = c; d.append(sp);
  }
  $('rpFeed').append(d);
}
let killcamT = 0;
function queueKillcam(killer, via) {
  clearTimeout(killcamT);
  const deathS = serverNow();
  G.killcamPending = true;
  killcamT = setTimeout(() => {
    if (ME.alive || !G.joined || RP.active) { G.killcamPending = false; return; }
    const clip = localClip(deathS - 4500, deathS + 1200, infoOf);
    const [kn, kc] = nameOf(killer);
    showReplayUI('KILLCAM', cardUrlFor(killer), kn, kc, `got you with ${wname(via)}`, 'SPACE / CLICK to skip');
    $('dead').classList.add('hidden');
    playClip(clip, {
      focus: killer, mode: 'killcam', slow: [[deathS - 380, deathS + 220]], end: deathS + 1000,
      onKill: (k) => replayFeed(k, clip.info),
      onEnd: () => { G.killcamPending = false; hideReplayUI(); if (!ME.alive) $('dead').classList.remove('hidden'); net.send({ t: 'respawn' }); },
      onAbort: () => { G.killcamPending = false; hideReplayUI(); },
    });
  }, 900);
}
function endKillcam() {
  clearTimeout(killcamT);
  G.killcamPending = false;
  if (RP.mode === 'killcam') stopReplay(true);
}
function skipReplay() {
  if (RP.active) { stopReplay(false); return; }
  if (G.killcamPending) { clearTimeout(killcamT); G.killcamPending = false; net.send({ t: 'respawn' }); }
}

// ------------------------------------------------------------ accounts
function totalRolls(me) { const r = (me && me.rolls) || {}; return (r.crate || 0) + (r.bag || 0) + (r.box || 0); }
function fmtTime(sec) { const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60); return h ? `${h}h ${m}m` : `${m}m`; }
function renderAcctBar() {
  const tr0 = account.loggedIn ? totalRolls(account.me) : 0;
  $('cratesBtn').textContent = tr0 ? `CONTAINERS (${tr0})` : 'CONTAINERS';
  $('cratesBtn').classList.toggle('glow', tr0 > 0);
  const bar = $('acctBar');
  bar.innerHTML = '';
  const span = (t, cls) => { const e = document.createElement('span'); e.textContent = t; if (cls) e.className = cls; return e; };
  const btn = (t, fn) => { const b = document.createElement('button'); b.textContent = t; b.addEventListener('click', fn); return b; };
  if (account.loggedIn) {
    const me = account.me;
    const tr = totalRolls(me);
    bar.append(span(`Lv ${me.level}`, 'lv'), span(me.name), span(`${tr} to open`, 'rolls'),
      btn('PROFILE', () => show('profile')), btn('LOG OUT', doLogout));
    $('nameRow').classList.add('hidden');
  } else {
    bar.append(span('playing as guest'), btn('LOG IN', () => openAccount(false)), btn('SIGN UP', () => openAccount(true)));
    $('nameRow').classList.remove('hidden');
  }
}
let signup = false;
function openAccount(isSignup) {
  signup = isSignup;
  $('acctTitle').textContent = signup ? 'SIGN UP' : 'LOG IN';
  $('acctGo').innerHTML = `<b>${signup ? 'CREATE ACCOUNT' : 'LOG IN'}</b>`;
  $('acctPass2').classList.toggle('hidden', !signup);
  $('acctSwap').textContent = signup ? 'have an account? log in' : 'no account? sign up';
  $('acctErr').textContent = '';
  show('account');
  setTimeout(() => $('acctName').focus(), 0);
}
$('acctSwap').addEventListener('click', (e) => { e.preventDefault(); openAccount(!signup); });
async function submitAccount() {
  const name = $('acctName').value.trim(), pass = $('acctPass').value;
  if (signup && pass !== $('acctPass2').value) { $('acctErr').textContent = "passwords don't match"; return; }
  $('acctErr').textContent = '...';
  try {
    const me = signup ? await register(name, pass) : await login(name, pass);
    $('acctPass').value = ''; $('acctPass2').value = '';
    onLoggedIn(me, signup);
    show('main');
    toast(signup ? `welcome ${me.name}. you got a free crate, duffel bag and box: open them in COSMETICS` : `welcome back ${me.name}`);
  } catch (e) {
    // on a host-on-this-PC server, your online account doesn't exist here
    $('acctErr').textContent = e.message + (G.localHost && /wrong/.test(e.message) ? '. (you are hosting on this PC: accounts here are separate from your online one. use PLAY ONLINE to log in with it)' : '');
  }
}
$('acctGo').addEventListener('click', submitAccount);
for (const id of ['acctName', 'acctPass', 'acctPass2']) $(id).addEventListener('keydown', (e) => { if (e.key === 'Enter') submitAccount(); });

// a fresh account adopts what you already set up as a guest; an existing one brings its own setup to this device
function onLoggedIn(me, fresh) {
  const prof = me.profile || {};
  if (!fresh && prof.loadout) {
    G.settings.loadout = validLoadout(prof.loadout);
    G.settings.skins = prof.skins && typeof prof.skins === 'object' ? prof.skins : {};
    if (prof.look && typeof prof.look === 'object') G.settings.look = { ...DEFAULT_LOOK, ...prof.look };
    if (typeof prof.card === 'string') G.settings.card = prof.card;
    if (typeof prof.kfx === 'string') G.settings.kfx = prof.kfx;
    Object.assign(G.settings, prof.settings || {});
    try { localStorage.setItem('jankfire', JSON.stringify(G.settings)); } catch { /* fine */ }
    applySettingsToUI();
  } else saveSettings();
  G.inv = me.inv || {};
  recomputeEquipped();
  rebuildViewmodels();
  setLoadout(G.settings.loadout);
  renderAcctBar();
}
function doLogout() {
  logout();
  G.inv = {};
  recomputeEquipped();
  rebuildViewmodels();
  setLoadout(G.settings.loadout);
  renderAcctBar();
  show('main');
  toast('logged out. locked cosmetics are hidden until you log back in.');
}
$('logoutBtn').addEventListener('click', doLogout);
function applySettingsToUI() {
  $('jank').value = String(S.jank); setJank(S.jank);
  for (const id of ['fov', 'vol', 'sens', 'adsSens']) { $(id).value = String(S[id]); $(id).dispatchEvent(new Event('input')); }
  for (const id of ['fovKick', 'shake', 'showFps', 'swapAim', 'toggleAim', 'blood', 'killcam', 'showCards', 'speedLines']) $(id).checked = !!S[id];
  setVolume(S.vol);
}

function renderProfile() {
  const me = account.me;
  if (!me) { show('main'); return; }
  $('profName').textContent = me.name;
  const cur = (me.level - 1) * (me.level - 1) * 40, next = me.level * me.level * 40;
  const k = Math.max(0, Math.min(1, (me.xp - cur) / (next - cur)));
  $('profLevel').innerHTML = '';
  const t = document.createElement('div'); t.textContent = `Level ${me.level} · ${me.xp} xp · ${next - me.xp} to next`;
  const bar = document.createElement('div'); bar.className = 'xpbar'; const fill = document.createElement('div'); fill.style.width = k * 100 + '%'; bar.append(fill);
  $('profLevel').append(t, bar);
  const st = me.stats;
  const owned = LOOT_TYPES.reduce((a, ty) => a + Object.keys(COSMETICS[ty]).filter((id) => owns(me.inv, ty, id)).length, 0);
  const total = LOOT_TYPES.reduce((a, ty) => a + Object.keys(COSMETICS[ty]).length, 0);
  const rows = [
    ['wins', st.wins], ['kills', st.kills], ['deaths', st.deaths], ['k/d', st.deaths ? (st.kills / st.deaths).toFixed(2) : st.kills],
    ['bot kills', st.bot_kills], ['best coop wave', st.best_wave], ['top speed', `${st.top_speed} km/h`], ['played', fmtTime(st.playtime)],
    ['cosmetics', `${owned}/${total}`], ['crates / bags / boxes', `${me.rolls.crate || 0} / ${me.rolls.bag || 0} / ${me.rolls.box || 0}`],
  ];
  $('profStats').innerHTML = '';
  for (const [label, v] of rows) {
    const d = document.createElement('div'); d.className = 'stat';
    const b = document.createElement('b'); b.textContent = v;
    const sp = document.createElement('span'); sp.textContent = label;
    d.append(b, sp); $('profStats').append(d);
  }
}

async function renderLeaders() {
  const el = $('leaders');
  el.textContent = 'loading...';
  try {
    const lb = await fetchLeaders();
    el.innerHTML = '';
    const cols = [['wins', 'Most wins', (v) => v], ['kills', 'Most kills', (v) => v], ['speed', 'Fastest ever', (v) => `${v} km/h`], ['wave', 'Best coop wave', (v) => `wave ${v}`], ['xp', 'Highest level', (v, r) => `Lv ${r.level}`]];
    for (const [key, title, fmt] of cols) {
      const c = document.createElement('div');
      const h = document.createElement('h4'); h.textContent = title; c.append(h);
      const ol = document.createElement('ol');
      for (const r of lb[key] || []) {
        const li = document.createElement('li');
        li.textContent = r.name + ' ';
        const sp = document.createElement('span'); sp.textContent = fmt(r.value, r); li.append(sp);
        ol.append(li);
      }
      if (!(lb[key] || []).length) { const li = document.createElement('li'); li.textContent = 'nobody yet'; ol.append(li); }
      c.append(ol); el.append(c);
    }
  } catch { el.textContent = 'could not load the leaderboard'; }
}

// ------------------------------------------------------------ containers screen
function containerArt(kind) {
  const c = document.createElement('canvas'); c.width = 96; c.height = 72;
  const x = c.getContext('2d'); x.lineWidth = 3; x.strokeStyle = '#000';
  if (kind === 'crate') { x.fillStyle = '#a8743a'; x.fillRect(14, 16, 68, 48); x.strokeRect(14, 16, 68, 48); x.fillStyle = '#7a5226'; for (const y of [28, 44]) x.fillRect(14, y, 68, 4); x.fillRect(44, 16, 8, 48); x.fillStyle = '#ffe14d'; x.fillRect(40, 8, 16, 10); x.strokeRect(40, 8, 16, 10); }
  else if (kind === 'bag') { x.fillStyle = '#3a6a2a'; x.beginPath(); x.ellipse(48, 44, 38, 20, 0, 0, Math.PI * 2); x.fill(); x.stroke(); x.strokeStyle = '#1a1a1a'; x.lineWidth = 5; x.beginPath(); x.arc(48, 30, 16, Math.PI, 0); x.stroke(); x.fillStyle = '#ffe14d'; x.fillRect(30, 40, 36, 4); }
  else { x.fillStyle = '#c8a46a'; x.fillRect(16, 22, 64, 42); x.strokeRect(16, 22, 64, 42); x.fillStyle = '#e0c088'; x.beginPath(); x.moveTo(16, 22); x.lineTo(32, 8); x.lineTo(80, 8); x.lineTo(80, 22); x.fill(); x.stroke(); x.fillStyle = '#ff4fd8'; x.fillRect(42, 22, 12, 42); }
  return c.toDataURL();
}
function renderCrates() {
  const box = $('crateCards');
  box.innerHTML = '';
  if (!account.loggedIn) {
    const d = document.createElement('div'); d.className = 'sub'; d.textContent = 'guests only get the free stuff. log in to earn crates, duffel bags and boxes.';
    const b = document.createElement('button'); b.className = 'mid'; b.textContent = 'LOG IN'; b.addEventListener('click', () => openAccount(false));
    box.append(d, b);
    return;
  }
  for (const [kind, c] of Object.entries(CONTAINERS)) {
    const n = account.me.rolls[kind] || 0;
    const own = c.types.reduce((a, t) => a + Object.keys(COSMETICS[t]).filter((id) => owns(G.inv, t, id)).length, 0);
    const all = c.types.reduce((a, t) => a + Object.keys(COSMETICS[t]).length, 0);
    const card = document.createElement('div'); card.className = 'cratecard' + (n > 0 ? ' has' : '');
    const im = document.createElement('img'); im.src = containerArt(kind); im.alt = '';
    const h = document.createElement('b'); h.textContent = c.name;
    const dsc = document.createElement('span'); dsc.textContent = c.desc;
    const prog = document.createElement('small'); prog.textContent = `you own ${own} / ${all}`;
    const btn = document.createElement('button'); btn.className = 'mid'; btn.textContent = n > 0 ? `OPEN (${n})` : 'NONE LEFT'; btn.disabled = n <= 0;
    btn.addEventListener('click', () => doRoll(kind));
    card.append(im, h, dsc, prog, btn);
    box.append(card);
  }
}
$('toCrates').addEventListener('click', (e) => { e.preventDefault(); show('crates'); });

// ------------------------------------------------------------ cosmetic rolls
let rolling = false;
function randomCard(kind) {
  const types = CONTAINERS[kind].types;
  const pool = [];
  for (const t of types) for (const [id, c] of Object.entries(COSMETICS[t])) if (c.rarity !== 'free') pool.push({ type: t, id, name: c.name, rarity: c.rarity });
  const r = Math.random() * 100;
  const want = r < 55 ? 'common' : r < 83 ? 'rare' : r < 96 ? 'epic' : 'legendary';
  const pref = pool.filter((p) => p.rarity === want);
  const from = pref.length ? pref : pool;
  return from[(Math.random() * from.length) | 0];
}
function card(item) {
  const d = document.createElement('div');
  d.className = 'rcard';
  d.style.setProperty('--rc', RARITY[item.rarity].color);
  const b = document.createElement('b'); b.textContent = item.name;
  const sm = document.createElement('small'); sm.textContent = `${TYPE_NAMES[item.type]} · ${RARITY[item.rarity].name}`;
  d.append(b, sm);
  return d;
}
async function doRoll(kind) {
  if (rolling || !account.loggedIn) return;
  rolling = true;
  initAudio(S.vol);
  let r;
  try {
    const res = await fetch('/api/roll', { method: 'POST', headers: { authorization: 'Bearer ' + account.token, 'content-type': 'application/json' }, body: JSON.stringify({ kind }) });
    r = await res.json();
    if (!res.ok) throw new Error(r.error || 'roll failed');
  } catch (e) { toast(e.message); rolling = false; return; }
  account.me = r.me;
  const item = r.item;
  const strip = $('rollStrip');
  strip.innerHTML = '';
  const WIN = 38;
  $('rollbox').querySelector('.rolltitle').textContent = `OPENING A ${CONTAINERS[kind].name.toUpperCase()}`;
  for (let i = 0; i < 46; i++) strip.append(card(i === WIN && item ? item : randomCard(kind)));
  $('rollResult').innerHTML = '';
  $('rollBtns').innerHTML = '';
  $('rollbox').classList.remove('hidden');
  strip.style.transition = 'none';
  strip.style.transform = 'translateX(0px)';
  const cw = 120; // card + gap
  const view = strip.parentElement.clientWidth;
  const target = WIN * cw - view / 2 + 56 + (Math.random() - 0.5) * 80;
  let lastIdx = -1;
  const ticker = () => {
    if (!rolling) return;
    const m = new DOMMatrixReadOnly(getComputedStyle(strip).transform);
    const idx = Math.floor((-m.m41 + view / 2) / cw);
    if (idx !== lastIdx) { lastIdx = idx; sfx.click(); }
    requestAnimationFrame(ticker);
  };
  requestAnimationFrame(() => requestAnimationFrame(() => {
    strip.style.transition = 'transform 4.6s cubic-bezier(0.05, 0.7, 0.1, 1)';
    strip.style.transform = `translateX(${-target}px)`;
    ticker();
  }));
  setTimeout(() => {
    rolling = false;
    G.inv = account.me.inv || {};
    recomputeEquipped();
    renderAcctBar();
    const res = $('rollResult');
    const btn = (t, fn) => { const b = document.createElement('button'); b.className = 'mid'; b.textContent = t; b.addEventListener('click', fn); $('rollBtns').append(b); };
    if (item) {
      const big = document.createElement('span'); big.className = 'big'; big.textContent = item.name; big.style.color = item.color;
      const sub = document.createElement('span'); sub.textContent = `${item.rarityName} ${TYPE_NAMES[item.type].toLowerCase()} unlocked`;
      res.append(big, sub);
      if (item.rarity === 'legendary' || item.rarity === 'epic') sfx.kill(); else sfx.ting();
      if (item.type === 'kill') {
        btn('EQUIP KILL EFFECT', () => { setKfx(item.id); closeRoll(); toast(`kill effect: ${item.name}`); });
      } else {
      // skins belong to one weapon; everything else can go on whatever you're looking at
      const target = item.type === 'model' ? COSMETICS.model[item.id].weapon : G.cosSel;
      btn(`PUT IT ON ${WEAPONS[target].name.toUpperCase()}`, () => {
        const sk = validSkin(S.skins[target]).slice();
        sk[TYPES.indexOf(item.type)] = item.id;
        G.cosSel = target;
        setSkin(target, sk);
        closeRoll();
      });
      }
    } else {
      const big = document.createElement('span'); big.className = 'big'; big.textContent = `you own everything from ${CONTAINERS[kind].plural.toLowerCase()}`; res.append(big);
      const sub = document.createElement('span'); sub.textContent = '+100 xp instead'; res.append(sub);
    }
    const left = account.me.rolls[kind] || 0;
    if (left > 0) btn(`OPEN ANOTHER (${left})`, () => { closeRoll(); doRoll(kind); });
    btn('OK', closeRoll);
  }, 4800);
}
function closeRoll() { $('rollbox').classList.add('hidden'); if (screen === 'cosmetics') buildCosmeticsUI(); if (screen === 'crates') renderCrates(); renderAcctBar(); }

// ------------------------------------------------------------ rounds
function fmtClock(ms) { const s2 = Math.ceil(ms / 1000); return `${Math.floor(s2 / 60)}:${String(s2 % 60).padStart(2, '0')}`; }
function renderRound(r) {
  const el = $('round');
  if (!r) { el.textContent = ''; return; }
  const teamGame = r.game && GAMES[r.game] && GAMES[r.game].teams;
  el.textContent = r.over ? `next round in ${Math.ceil(r.left / 1000)}` : teamGame ? '' : `first to ${r.target} · ${fmtClock(r.left)}`;
}
net.on('round', (m) => {
  const box = $('roundEnd');
  if (m.start) {
    G.roundOver = false; if (RP.mode === 'hl') stopReplay(true); box.classList.add('hidden'); showVote(null);
    if (m.game) { G.round = { ...(G.round || {}), ...m }; updateLabel(); }
    hud.msg(m.game && m.game !== 'dm' && GAMES[m.game] ? GAMES[m.game].name.toUpperCase() : 'ROUND START', 1.8, 'brag');
    if (m.game && GAMES[m.game]) hud.chat(null, null, GAMES[m.game].desc);
    return;
  }
  if (!m.over) return;
  G.roundOver = true;
  box.innerHTML = '';
  const h = document.createElement('h3');
  if (m.sc) {
    const won = m.winTeam && m.winTeam === G.myTeam;
    h.textContent = m.winTeam ? `${TEAMS[m.winTeam].name} WINS ${m.sc[0]} - ${m.sc[1]}${won ? ' (YOU)' : ''}` : `DRAW ${m.sc[0]} - ${m.sc[1]}`;
    if (m.winTeam) h.style.color = TEAMS[m.winTeam].color;
  } else {
    const [wn] = m.winner ? nameOf(m.winner) : ['nobody'];
    h.textContent = m.winner === G.myId ? 'YOU WIN' : `${wn} wins`;
  }
  box.append(h);
  for (const [id, name, k, d, team] of m.top) {
    const row = document.createElement('div');
    row.textContent = `${name}  ·  ${k} / ${d}`;
    if (team && TEAMS[team]) row.style.color = TEAMS[team].color;
    if (id === G.myId) row.style.color = '#ffe14d';
    box.append(row);
  }
  box.classList.remove('hidden');
  if (m.winner === G.myId || (m.winTeam && m.winTeam === G.myTeam)) sfx.kill();
});
// play of the round: the server picked the best moment and sent the recording
net.on('hl', (m) => {
  if (!G.joined || !m.clip) return;
  if (RP.mode === 'killcam' || G.killcamPending) skipReplay();
  const box = $('roundEnd');
  box.classList.add('hidden');
  const url = m.id === G.myId ? cardUrlFor(G.myId) : (S.showCards !== false && m.card) || defaultCard(m.name, m.color);
  showReplayUI('PLAY OF THE ROUND', url, m.name, m.color, m.label, 'SPACE to skip');
  const slow = (m.clip.ev || []).filter((e) => e.m && e.m.t === 'kill' && e.m.k === m.id).map((e) => [e.s - 260, e.s + 220]);
  playClip(m.clip, {
    focus: m.id, mode: 'hl', slow,
    onKill: (k) => replayFeed(k, m.clip.info),
    onEnd: () => { hideReplayUI(); if (G.roundOver) box.classList.remove('hidden'); },
    onAbort: () => hideReplayUI(),
  });
  sfx.kill();
});
net.on('roll+', (m) => {
  const box = $('roundEnd');
  const d = document.createElement('div');
  d.className = 'roll';
  if (m.n > 0) {
    const c = CONTAINERS[m.kind] || CONTAINERS.box;
    d.textContent = `+${m.n} ${c.name.toUpperCase()} (${c.desc})${m.why ? `: ${m.why}` : ''}. open it in COSMETICS`;
    if (account.me) { account.me.rolls[m.kind] = (account.me.rolls[m.kind] || 0) + m.n; renderAcctBar(); }
    toast(`+${m.n} ${c.name}`);
  } else if (m.guest) d.textContent = 'you would have earned a crate, bag or box. log in to keep them.';
  else d.textContent = m.why || '';
  if (!box.classList.contains('hidden')) box.append(d); else toast(d.textContent, 3500);
});

// ------------------------------------------------------------ install as an app (PWA)
let installEvt = null;
addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); installEvt = e; if (!window.jf) $('installBtn').classList.remove('hidden'); });
$('installBtn').addEventListener('click', async () => {
  if (!installEvt) return;
  installEvt.prompt();
  await installEvt.userChoice.catch(() => {});
  installEvt = null;
  $('installBtn').classList.add('hidden');
});
// desktop app (exe): it has its own window, so no "install app"; show server/quit buttons instead
if (window.jf && window.jf.desktop) {
  $('desktopRow').classList.remove('hidden');
  $('dChange').addEventListener('click', () => { quitToMenu(true); window.jf.launcher(); });
  $('dFull').addEventListener('click', () => {
    if (!window.jf.display) { window.jf.fullscreen(); return; }
    const order = ['windowed', 'maximized', 'fullscreen'];
    S.display = order[(order.indexOf(S.display || 'windowed') + 1) % 3];
    $('displayMode').value = S.display; saveSettings(); applyDisplay(S.display);
    toast({ windowed: 'windowed', maximized: 'windowed fullscreen', fullscreen: 'fullscreen' }[S.display]);
  });
  $('dQuit').addEventListener('click', () => window.jf.quit());
  window.jf.info().then((info) => {
    if (!info.hosting) return;
    G.localHost = true; // accounts on a host-on-this-PC server only exist on this PC
    $('status').textContent = `you're hosting${info.hosting.lan.length ? `. friends on your wifi join: ${info.hosting.lan.join('  or  ')}` : ''}. accounts here are local to this PC (play online for your real account)`;
  });
} else if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});

// ------------------------------------------------------------ boot
renderAcctBar();
restore().then((me) => { if (me) onLoggedIn(me, false); });

show('main');
requestAnimationFrame(frame);

// debug handle for poking at things from the console
window.JANK = { G, ME, W, net, switchSlot, setLoadout, fireDown, fireUp, tryHook, releaseHook, reload, startMode, quitToMenu, show };
