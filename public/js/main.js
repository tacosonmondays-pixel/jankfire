// JANKFIRE client entry: menus, modes, input, net handlers and the main loop.
import * as THREE from 'three';
import { BOXES, MAPS, MAP_ORDER } from '/shared/map.js';
import { WEAPONS, ORDER, SLOTS, FLAGS, SLIP_TIME, HIPFIRE, BOT_DIFF, MODES, STREAKS, ITEMS, ITEM_ORDER, validLoadout, validStreaks } from '/shared/weapons.js';
import { streakIcon } from './icons.js';
import { stepProjectile, raycast } from '/shared/physics.js';
import { duckFrame, duckStuck } from './duck.js';
import { G } from './ctx.js';
import { initWorld, renderFrame, setJank, updateWorld, loadMap, refreshMapVisuals } from './world.js';
import { setShadowPref } from './lighting.js';
import { hrFeed, hrDead } from './hrguy.js';
import { loadTripoModels, buildProjectile, buildPeel, buildHole, makeShadow, tipColor, buildCharacter, teamLook, M } from './models.js';
import { onLateModel, prefetchLoadout } from './glbkit.js';
import { initCrosses, crossEvent, crossShot, updateCrosses, clearCrosses } from './bloodcross.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { fx, makeBeam, setBeam, scaleU } from './fx.js';
import { marbles } from './marbles.js';
import { initAudio, sfx, setVolume, setListener, stopLoops } from './audio.js';
import { musicUpdate, musicNewMatch } from './music.js';
import { ME, stepPlayer, tryHook, releaseHook, applyKb, slip, eye, hookPoint, hspeed, crouchTap } from './player.js';
import {
  W, initWeapons, rebuildOne, setLoadout, refillAmmo, switchSlot, lastSlot, cycleSlot, reload,
  fireDown, fireUp, updateWeapons, muzzleWorld, onSlipperBack, inspect, grantScythe, loseScythe, toggleScythe, cycleCard, heavyAttack,
  useItem, syncItem, resetItems, setItem, showSlots, setMyKatana,
} from './weapons.js';
import { Remote, updateGibs } from './remote.js';
import { stepSoap, trapStart, trapEnd, updateWand, stuckInBubble } from './wand.js';
import { initGear, updateGear, gearFx, gearKeyDown, gearSpawn, gearLeave, gearKillParts, gearDeathLine } from './gear.js'; // laser pointer, camera, pop quiz, goggles
import { initSec, updateSec, secFx, secAimDown, secFrozen, secBlocked, secShot, secSpawn, secLeave } from './secondaries.js'; // water pistol, taser, tv remote, speed trap
import { parry } from './weapons.js';
import './parry.js'; // katana parry: sparks, sounds, PARRY!, the guard pose
import { addPatch, clearPatches } from './mslip.js'; // marble shotgun: marbles on the floor you slip on
import { FINISHES, HATS, EFFECTS, validSkin, randomSkin, makeSkinSystems, emitSkinFx, skinTick, tracerColor, DEFAULT_SKIN, WRAP_MODES, WRAP_MODE_NAMES } from './skins.js';
import { initPreview, showPreview, showCharacter, renderPreview, resizePreview, refreshPreview } from './preview.js';
import { playKillFx, updateKillFx, clearKillFx } from './killfx.js';
import { courtKill, courtVerdict, updateCourt, courtReset, courtSync } from './scales.js';
import { noScope, updateNoScope } from './noscope.js';
import { makeRope, setRope, setRopeSkin, myGrapple, initGrapplePreview, grappleThumb, showGrapple, renderGrapplePreview } from './grapple.js';
import { shredKill, shredHit, shredGrab, grabStep, updateShreds, clearShreds } from './shredder.js';
import { pitKill } from './shredpit.js'; // the Warehouse's shredder pit: it chews, then spits the bits back up
import { primFx, pinStep, tennisStep, tennisEnd, updatePrims, clearPrims, cartKey } from './primaries.js'; // nail gun, tennis balls, shopping carts
import { updateSpeedLines } from './speedlines.js';
import { slipperUpdate, slipperStep } from './slipper.js';
import { setupObjectives, updateObjectives, addTag, removeTag, clearTags, canUse } from './objective.js';
import { GAMES, GAME_ORDER, TEAMS, mapsFor, mapForGame } from '/shared/modes.js';
import { defaultCard, cardEl, initCardEditor } from './cards.js';
import { recordSnap, recordEv, clearRec, localClip, playClip, stopReplay, updateReplay, RP, serverNow } from './replay.js';
import { EPIC_CAM, epicMul, epicCamMs } from '/shared/epic.js';
import { LOOK_COLORS, ACHIEVEMENTS, ACCESSORIES, LOOK_SLOTS, DEFAULT_LOOK, validLook, SKIN_TONES, HAIR_COLORS, CLOTH_COLORS, HAIRS, TOPS, BOTTOMS } from '/shared/looks.js';
import { startBall, endBall, ballOn, BS } from './player.js';
import { updateWreck, ballCam, wreckFx, wreckDied } from './wreck.js';
import { hasAcc } from '/shared/looks.js';
import { airTick, airReset, airFlourish } from './airborne.js';
import { oobTick } from './bounds.js';
import { account, restore, login, register, logout, saveProfile, leaderboard as fetchLeaders } from './account.js';
import { updateRig, rigDied, rigOn } from './rig.js';
import { rigClash } from '/shared/rig.js'; // overdrive rig killstreak
import { updateChaos, lavaStep, spectateCam, chaosRoundStart, chaosRoundText, chaosNoStreaks } from './chaos.js';
import { brKey, brMouse, brCam, brFrame, brFeed, brRoundEnd, brDead, brNames, brReset } from './royale.js'; // jank royale
import { COSMETICS, RARITY, TYPES, LOOT_TYPES, TYPE_NAMES_ALL as TYPE_NAMES, CONTAINERS, owns, ownedSkin, ownedKill, modelsFor } from '/shared/cosmetics.js';
import { ecoKeyLabel } from './econ.js';
import { bodyReset } from './bodyhp.js'; // the wrecking ball + rig last until they break
import { initEcon, ecoOn, econKey, econMouse, econMenuOpen, econFrame, econCam, econHideVM, econDead, econWelcome, econSpawn, econKill, econIc, econLoadout, econReset } from './econ.js';
import { SPRAY, ownedSpray } from '/shared/cosmetics.js';
import { sprayAim, sprayFx, addSpray, clearSprays, updateSprays, sprayIcon } from './sprays.js';
import { achInv } from '/shared/cosmetics.js'; // achievement rewards (Golden Sniper) count as owned once you have the achievement
import { achProgress, ROYAL_ALL, ROYAL_FEATS } from '/shared/looks.js';
import { royalToast, royalUnlock, royalBoxes } from './royal.js';
import { updateTraffic, carCollide, carKill, carFeedIcon } from './traffic.js'; // cars on the roads
import { updateLore, updateLoreFx, loreKey, renderLore } from './lore.js'; // hidden NPCs + cats (F), the LORE page
import { setOnly, coughCloud } from './weapons.js';
import { renderPatchNotes, markPatchSeen, patchUnseen } from './patchnotes.js';
import { updateGunGame, ggRoundText, ggScoreRows, ggRowNote, resetGunGame } from './gungame.js';
import { updateInfection, infRoundText, infRoundTitle, infScoreRows, infRowNote, resetInfection, infClipInfo } from './infection.js';
import { initEndscreen, esRound, esVote, esVotes, esClose, esMini, esKey, esRoll, esAch, esFull, esActive, esHideClick, esClickShown, esRekey } from './endscreen.js';
import { initHome, homeShown, homeLeft, refreshHero } from './home.js';
import { skipVote, skipReset } from './skipvote.js';
import { lassoFrame, loopFrame, lassoWheel, lassoKey, lassoLate } from './lasso.js'; // lasso (secondary)
import { remoteK } from './rifles.js'; // the rifle pack (BURST!, lever ramp + quick-scope callouts register themselves)
import { K } from './keys.js';
import { initLobby, lobbyInfo, lobbyKey, lobbyMe, lobbyLeave } from './lobby.js'; // ONLINE / WITH BOTS mode picker + the lobby countdown
import { controlsScreen } from './controls.js';
import { containerPic, playContainer, stopContainer } from './crate3d.js'; // containers in 3D: the cards and the opening
import { hubTabs } from './hub.js'; // the CUSTOMIZE hub's tabs (loadout / weapons / character / grapple & spray)
import { initCustomize, czMode, czOpen, czClose, czFrame, czKill, czLate, czRefresh, czRolled, resolveRand, wantSkins, myFavs } from './customize.js'; // the weapon customize screen (replaces COSMETICS)
import { zmSetup, updateZombies, zmRoundText, zmScoreRows, zmKillFeed, zmReset, zmModelsLoaded } from './zombies.js';

const $ = (id) => document.getElementById(id);
const canvas = $('game');
const INTERP_MS = 110;
const wname = (id) => (WEAPONS[id] ? WEAPONS[id].name : id === 'hook' ? 'Grapple' : id === 'tbag' ? 'T-Bag' : id === 'carboom' ? 'Car Bomb' : id === 'car' ? 'Car' : id === 'bite' ? 'Claws' : id);
const wcolor = (id) => (WEAPONS[id] ? WEAPONS[id].color : '#ccc');

// ------------------------------------------------------------ settings
try {
  const saved = JSON.parse(localStorage.getItem('jankfire') || '{}');
  Object.assign(G.settings, saved);
} catch { /* private mode */ }
G.settings.loadout = validLoadout(G.settings.loadout);
if (!G.settings.skins || typeof G.settings.skins !== 'object') G.settings.skins = {};
if (!G.settings.look || typeof G.settings.look !== 'object') G.settings.look = { ...DEFAULT_LOOK };
K.attach(G.settings); // key bindings (keys.js): only what you changed is saved, old saves and the old swapAim box still load
const SYNC_KEYS = ['jank', 'sens', 'adsSens', 'vol', 'fov', 'swapAim', 'toggleAim', 'blood', 'shake', 'fovKick', 'showFps', 'killcam', 'showCards', 'speedLines', 'binds']; // swapAim stays synced (as false) so an old profile's true can't come back
function profileData() {
  const settings = {};
  for (const k of SYNC_KEYS) settings[k] = G.settings[k];
  return { loadout: G.settings.loadout, skins: G.settings.skins, look: G.settings.look, card: G.settings.card || '', kfx: G.settings.kfx || 'none', grap: G.settings.grap || 'rope', favs: G.settings.favs || undefined, wk: G.settings.wk || undefined, settings };
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
    const o = ownedSkin(resolveRand(sk, id), G.inv, id); // 'random' slots: this life's roll (customize.js)
    if (o[0] !== 'default' || o[1] !== 'none' || o[2] !== 'none' || o[3] !== 'default') G.equipped[id] = o;
  }
  if (G.equipped.scythe) G.equipped.scythe_rifle = G.equipped.scythe.slice(0, 3).concat('default', G.equipped.scythe[4]); // both forms look the same
}
recomputeEquipped();

// ------------------------------------------------------------ setup
initWorld(canvas);
setJank(G.settings.jank);
fx.init(G.scene);
initCrosses(G.scene);
const vmScaleU = { value: 300 };
G.skinFxWorld = makeSkinSystems(G.scene, scaleU);
G.skinFxVM = makeSkinSystems(G.vmScene, vmScaleU);
hud.init();
initEndscreen({
  note: (id, m) => ggRowNote(id, m) || infRowNote(id, m),
  title: (m) => { const t = m && !m.pending && infRoundTitle(m); return t ? t[0] : ''; },
  unlock: () => { if (document.pointerLockElement) document.exitPointerLock(); }, // the cards want a mouse
  level: () => (account.me ? { level: account.me.level, xp: account.me.xp || 0 } : null),
  gotXp: (x) => { // keep the account bar honest between matches (the server saved it already)
    const me = account.me;
    if (!me || !(x > 0)) return;
    me.xp = (me.xp || 0) + x;
    while (me.xp >= me.level * me.level * 40) me.level++;
    renderAcctBar();
  },
});
initWeapons();
setLoadout(G.settings.loadout);
hud.show(false);
initPreview($('preview'));
initHome({
  start: (mode, cfg) => startMode(mode, cfg),
  look: () => { const shown = validLook({ ...DEFAULT_LOOK, ...G.settings.look }, myAchs()); return [shown.color || G.myColor || '#ff4fd8', shown]; },
  skin: (id) => G.equipped[id], // what you actually wear
});
initLobby({ start: (mode, cfg) => startMode(mode, cfg), show: (id) => show(id), send: (m) => net.send(m), map: () => G.cfg && G.cfg.map });
initEcon({ pause: () => { if (document.pointerLockElement) document.exitPointerLock(); pause(); }, lock }); // Plant & Defuse economy

const myShadow = makeShadow();
G.scene.add(myShadow);
const myRope = makeRope(myGrapple());
myRope.visible = false;
G.scene.add(myRope);

loadTripoModels().then((n) => {
  if (!n) return;
  console.log(`loaded ${n} models`);
  rebuildOne(); // visuals only: a randomizer or pending loadout stays as it is
  refreshMapVisuals(); // Blender props replace their stand-in boxes
  zmModelsLoaded(); // zombies: the wall guns too
  prefetchLoadout(S.loadout); // your item's and killstreaks' models (they don't come with the startup download)
  for (const r of G.remotes.values()) r.build();
  $('status').textContent = `${n} model(s) loaded`;
});
onLateModel(() => { // a skin's model downloaded (the first time anyone showed it): swap it in everywhere it's on show
  rebuildOne();
  for (const r of G.remotes.values()) r.build();
  refreshPreview(); refreshHero(); czLate();
});

// ------------------------------------------------------------ screens
let screen = 'main', classicLocker = false;
function show(id) {
  // the CUSTOMIZE hub: LOADOUT and COSMETICS are the customize screen's two modes (the old loadout list is kept, hidden, for scripts)
  if (id === 'loadout') { czMode('loadout'); buildLoadoutUI(); id = 'customize'; }
  if (id === 'cosmetics' && !classicLocker) { czMode('weapons'); id = 'customize'; }
  classicLocker = false;
  screen = id;
  for (const el of document.querySelectorAll('.screen')) el.classList.toggle('hidden', el.id !== 'scr-' + id);
  $('menu').classList.remove('hidden');
  $('menu').classList.toggle('home-on', id === 'main');
  hud.show(false);
  if (id !== 'main') homeLeft();
  if (id !== 'customize') czClose();
  if (id === 'customize') czOpen();
  if (id === 'cosmetics') { skinAllNow = false; $('cosSlot').append($('preview')); buildCosmeticsUI(); setTimeout(resizePreview, 0); }
  for (const n of document.querySelectorAll('.screen > .hub-tabs')) n.mark();
  if (id === 'character') { $('charSlot').append($('preview')); buildCharacterUI(); setTimeout(resizePreview, 0); }
  if (id === 'namecard') cardEditor.open();
  if (id === 'crates') renderCrates();
  if (id === 'patchnotes') { renderPatchNotes($('pnList')); markPatchSeen(); $('pnNew').classList.add('hidden'); }
  if (id === 'loadout') { if ($('loNote').textContent === DRAFT_NOTE) $('loNote').textContent = ''; streakDraft = null; buildLoadoutUI(); }
  if (id === 'settings') syncDisplay();
  if (id === 'match') syncMatchUI();
  if (id === 'profile') { renderProfile(); restore().then((me) => { if (me && screen === 'profile') { renderProfile(); renderAcctBar(); } }); }
  if (id === 'leaders') renderLeaders();
  if (id === 'lore') renderLore($('loreList'));
  controlsScreen(id === 'controls', saveSettings);
  if (id === 'main') { renderAcctBar(); homeShown(); }
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
  if (!esFull()) lock(); // the end screen wants the mouse free for its cards
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
  net.connect({ name: G.settings.name, mode, skins: wantSkins(), favs: myFavs(), look: G.settings.look, card: G.settings.card || '', kfx: myKfx(), grap: myGrapple(), kc: G.settings.killcam !== false, streaks: validStreaks(S.loadout.streaks), item: S.loadout.item, cfg, token: account.loggedIn ? account.token : undefined }, () => {
    connecting = false;
    resetWorldState();
    show('main');
    $('status').textContent = 'Disconnected. Server is down or restarted.';
  });
  hideMenu();
  lock();
}

function resetWorldState() {
  bodyReset(); // wrecking ball / rig HP bars
  G.joined = false;
  ME.alive = false;
  releaseHook();
  endBall();
  stopLoops();
  for (const r of G.remotes.values()) r.dispose();
  G.remotes.clear(); G.names.clear(); G.skins.clear();
  clearEntities();
  for (const g of G.gibs) { G.scene.remove(g.m); if (g.own) g.m.geometry.dispose(); }
  G.gibs.length = 0;
  hud.dead(false);
  hud.wave(null);
  hud.scope(false);
  endKillcam();
  stopReplay(true);
  hideReplayUI();
  if (G.forcedLoadout) { G.forcedLoadout = null; setLoadout(S.loadout); }
  econReset();
  if (W.only) setOnly(null, S.loadout);
  resetGunGame(); resetInfection();
  zmReset();
  for (const b of G.bubbles.values()) G.scene.remove(b.mesh);
  G.bubbles.clear(); G.smokes.length = 0; ME.frozenUntil = 0; G.frost = 0;
  gearLeave();
  secLeave();
  brReset(); // the zone, eviction notice and loot rules stay with the royale room
  resetItems(); stopUse(); G.activeStreaks = null; G.itemSent = null;
  clearRec();
  clearKillFx();
  clearSprays();
  clearShreds();
  G.roundOver = false;
  lobbyLeave();
  renderRound(null);
  $('roundEnd').classList.add('hidden');
  esClose(false);
  skipReset();
  if (account.loggedIn) setTimeout(() => restore().then((me) => { if (me) renderAcctBar(); }), 900); // server saves stats when you leave
}
function clearEntities() {
  for (const pr of G.projs.values()) G.scene.remove(pr.mesh);
  for (const pl of G.peels.values()) G.scene.remove(pl);
  for (const h of G.holes.values()) G.scene.remove(h.mesh);
  G.projs.clear(); G.peels.clear(); G.holes.clear();
  clearCrosses();
  clearPatches();
  clearPrims();
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
  $('pauseMatch').classList.toggle('hidden', !!G.lk); // a mode lobby is everyone's: nobody changes its match
  $('pauseTitle').textContent = `${MODES[G.mode] ? MODES[G.mode].name.toUpperCase() : 'PAUSED'} · ${MAPS[G.cfg.map] ? MAPS[G.cfg.map].name : ''}`;
  W.held = false; W.aimHeld = false;
  K.clear();
  stopUse();
  stopLoops();
}
let wasLocked = false, lockedAt = 0, mouseAvg = 8;
document.addEventListener('pointerlockchange', () => {
  const locked = document.pointerLockElement === canvas;
  if (locked) { lockedAt = performance.now(); esHideClick(); }
  if (!locked && wasLocked && G.joined && !chatOpen && $('menu').classList.contains('hidden') && !esFull() && !econMenuOpen()) pause(); // the end screen lets go of the mouse on purpose
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
// a mode only offers the maps it can be played on (bomb sites, a floor to turn into lava; Plant & Defuse the S&D versions,
// the other modes the standard ones). the server refuses the rest
const mapsOf = (game) => (GAMES[game] ? mapsFor(game, MAPS, MAP_ORDER) : MAP_ORDER);
fillSelect($('setupMap'), mapEntries.filter(([k]) => mapsOf('dm').includes(k)), 'islands');
$('setupGame').addEventListener('change', () => {
  const keep = $('setupMap').value, list = mapsOf($('setupGame').value);
  fillSelect($('setupMap'), mapEntries.filter(([k]) => list.includes(k)), list.includes(keep) ? keep : list[0]);
});
$('cfgGame').addEventListener('change', () => {
  const g = $('cfgGame').value, list = mapsOf(g);
  if (!list.includes(mapForGame(g, MAPS, G.cfg.map))) { // (a map with an S&D version swaps to the version the mode plays)
    toast(`${GAMES[g].name} needs ${GAMES[g].sites ? 'a map with bomb sites' : 'another map'} (${list.map((k) => MAPS[k].name).join(', ')}): change the map first`, 3200);
    $('cfgGame').value = (G.round && G.round.game) || 'dm';
    return;
  }
  net.send({ t: 'cfg', game: g });
  setTimeout(() => { if (screen === 'match') syncMatchUI(); }, 1800); // show what the server actually did
});
fillSelect($('setupDiff'), diffEntries, 'normal');
fillSelect($('setupHip'), hipEntries, 'normal');
fillSelect($('cfgMap'), mapEntries);
fillSelect($('cfgHip'), hipEntries);
fillSelect($('cfgDiff'), diffEntries);
$('setupBots').addEventListener('input', () => { $('setupBotsN').textContent = $('setupBots').value; });
$('setupGo').addEventListener('click', () => startMode('bots', {
  map: $('setupMap').value, bots: Number($('setupBots').value), diff: $('setupDiff').value, hip: $('setupHip').value, game: $('setupGame').value, hr: $('setupHr').value,
}));
function syncMatchUI() {
  { const g = (G.round && G.round.game) || 'dm', list = mapsOf(g); // only the maps (and versions) this mode plays
    fillSelect($('cfgMap'), mapEntries.filter(([k]) => list.includes(k) || k === G.cfg.map), G.cfg.map); }
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
$('shadows').value = S.shadows || 'auto'; setShadowPref(S.shadows);
$('shadows').addEventListener('change', () => { S.shadows = $('shadows').value; setShadowPref(S.shadows); saveSettings(); });
bindRange('fov', 'fov');
bindRange('vol', 'vol', null, () => setVolume(S.vol));
// music has its own volume (the main one still scales it). in matches it's on (quieter, its own slider) for bots, co-op
// and training, and off in competitive (online room, plant & defuse) unless you turn that on. old saves have none of it
if (typeof S.musicVol !== 'number') S.musicVol = 0.35;
if (typeof S.musicMatchVol !== 'number') S.musicMatchVol = 0.15;
if (typeof S.musicMatch !== 'boolean') S.musicMatch = true;
S.musicComp = !!S.musicComp;
bindRange('musicVol', 'musicVol', null, musicUpdate);
bindRange('musicMatchVol', 'musicMatchVol', null, musicUpdate);
bindCheck('musicMatch', 'musicMatch', musicUpdate);
bindCheck('musicComp', 'musicComp', musicUpdate);
SYNC_KEYS.push('musicVol', 'musicMatch', 'musicComp', 'musicMatchVol');
bindRange('sens', 'sens', (v) => v.toFixed(1));
bindRange('adsSens', 'adsSens', (v) => v.toFixed(2));
bindCheck('fovKick', 'fovKick');
bindCheck('shake', 'shake');
bindCheck('showFps', 'showFps');
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
// the desktop app knows the real mode (F11 changes it behind the page's back), so ask before showing or cycling it
function syncDisplay() {
  if (!(window.jf && window.jf.displayGet)) return Promise.resolve();
  return window.jf.displayGet().then((m) => { if (DISPLAY.some(([k]) => k === m)) { S.display = m; $('displayMode').value = m; } }).catch(() => {});
}
syncDisplay();
// hotbar: weapons, item and killstreaks in one bar, along the bottom or down the right side
const applyHotbar = () => document.body.classList.toggle('hotbar-right', S.hotbar === 'right');
fillSelect($('hotbarPos'), [['bottom', 'Bottom'], ['right', 'Right side']], S.hotbar === 'right' ? 'right' : 'bottom');
$('hotbarPos').addEventListener('change', () => { S.hotbar = $('hotbarPos').value; saveSettings(); applyHotbar(); });
applyHotbar();
// every key hint outside the HUD follows the bindings (the hotbar, tray and messages ask keys.js when they draw)
function renderKeyHints() {
  const L = (id) => K.label(id).toUpperCase(), mv = ['forward', 'left', 'back', 'right'].map(L);
  const B = (t) => `<b>${String(t).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c])}</b>`; // key names are ours, but '<' style labels exist
  const mvs = mv.every((k) => k.length === 1) ? mv.join('') : mv.join(' ');
  $('keyHint').textContent = `${mvs} move · ${L('sprint')} run · ${K.labels('crouch').toUpperCase()} crouch (slide when fast) · `
    + `${L('jump')} jump (hold to bhop, jump while grappling to launch) · ${L('aim')} aim · ${L('grapple')} grapple · ${L('reload')} reload · ${L('use')} inspect · `
    + `${L('slot1')} ${L('slot2')} ${L('slot3')} switch · ${L('item')} use item · ${L('streak1')} ${L('streak2')} ${L('streak3')} use killstreaks · ${L('spray')} spray · `
    + `${L('dash')}/${L('scythe')} scythe · ${L('menu')} menu · ${L('scores')} scores · ${L('chat')} chat · /skip in chat votes to skip the match`;
  $('gMove').innerHTML = `${B(mvs)} move · ${B(L('sprint'))} run · ${B(K.labels('crouch').toUpperCase())} crouch, slide when fast · ${B(L('jump'))} jump (hold to bhop)`;
  $('gHook').innerHTML = `${B(L('grapple'))} grapple · jump while grappling to launch. momentum is infinite. use it irresponsibly.`;
  $('gFight').innerHTML = `${B(L('fire'))} shoot · ${B(L('aim'))} aim · ${B(L('parry'))} katana parry · ${B(L('reload'))} reload · ${B(L('use'))} inspect · ${B(`${L('slot1')} ${L('slot2')} ${L('slot3')}`)} switch · ${B(L('lastSlot'))} last weapon`;
  $('gItems').innerHTML = `${B(L('item'))} item · ${B(L('nvgFlash'))} goggles flash · ${B(`${L('streak1')} ${L('streak2')} ${L('streak3')}`)} killstreaks · ${B(`${L('dash')} / ${L('scythe')}`)} scythe · ${B(L('spray'))} spray`;
  $('gElse').innerHTML = `${B(L('menu'))} menu · ${B(L('scores'))} scores · ${B(L('chat'))} chat`;
  $('gEcon').innerHTML = `plant &amp; defuse: ${B(ecoKeyLabel('buy'))} buy · ${B(ecoKeyLabel('drop'))} drop what you hold · ${B(L('grapple'))} pick up · ${B(L('sprint'))} slow walk (silent) · stand still to shoot straight`;
  $('voteKeys').textContent = VOTES.map(K.label).join(' ');
  $('gLore').innerHTML = `${B(L('use'))} next to someone talks to them. some people are hidden around the maps, and so is the board of directors (${B(L('use'))} to pet). what you find goes in ${B('LORE')}.`; // hidden NPCs + cats (lore.js)
  $('sprayKey').textContent = K.label('spray');
  $('loItemKey').textContent = K.label('item');
  $('loStreakKeys').textContent = ['streak1', 'streak2', 'streak3'].map(K.label).join(' / ');
}
const VOTES = ['vote1', 'vote2', 'vote3', 'vote4'];
renderKeyHints();
K.onChange(() => {
  renderKeyHints();
  esRekey(); // the vote cards show the vote keys
  if (W.slots) showSlots(); // hotbar numbers + item key
  $('streakTray').dataset.key = ''; renderStreak(G.streakN || 0);
});

// ------------------------------------------------------------ loadout screen
function buildLoadoutUI() {
  for (const slot of SLOTS) {
    const col = $('lo-' + slot);
    col.innerHTML = '';
    for (const id of ORDER) {
      const w = WEAPONS[id];
      if (w.slot !== slot || w.modeOnly) continue; // mode-only weapons (the spoon) aren't loadout picks
      const b = document.createElement('button');
      b.className = 'wpick' + (S.loadout[slot] === id ? ' on' : '');
      b.textContent = w.name;
      b.style.setProperty('--c', w.color);
      b.addEventListener('mouseenter', () => { $('loDesc').textContent = `${w.name}: ${K.hint(w.desc)}`; });
      b.addEventListener('click', () => {
        S.loadout[slot] = id;
        G.cosSel = id;
        saveSettings();
        buildLoadoutUI();
        applyLoadout(false);
        $('loDesc').textContent = `${w.name}: ${K.hint(w.desc)}`;
      });
      col.append(b);
    }
  }
  // killstreaks: pick 3. click one of yours to drop it, then click the one you want in its place
  const kc = $('lo-streaks');
  kc.innerHTML = '';
  const picks = streakDraft || validStreaks(S.loadout.streaks);
  for (const [id, st] of Object.entries(STREAKS).sort((a, b) => a[1].kills - b[1].kills)) {
    const b = document.createElement('button');
    b.className = 'kpick' + (picks.includes(id) ? ' on' : '');
    const im = document.createElement('img'); im.src = streakIcon(id); im.alt = '';
    const t = document.createElement('span'); t.textContent = `${st.name} · ${st.kills}`;
    b.append(im, t);
    b.addEventListener('mouseenter', () => { $('loDesc').textContent = `${st.name} (${st.kills} kills in a row): ${K.hint(st.desc)}`; });
    b.addEventListener('click', () => {
      // a draft under 3 picks is never saved or sent (validStreaks would pad it straight back with the defaults)
      if (picks.includes(id)) { streakDraft = picks.filter((x) => x !== id); $('loNote').textContent = DRAFT_NOTE; buildLoadoutUI(); return; }
      if (picks.length >= 3) { toast('click one of your killstreaks to drop it first'); return; }
      const next = [...picks, id];
      if (next.length < 3) { streakDraft = next; buildLoadoutUI(); return; } // still a slot to fill: nothing saved yet
      streakDraft = null;
      S.loadout.streaks = validStreaks(next);
      saveSettings();
      $('loNote').textContent = '';
      applyStreaks();
      buildLoadoutUI();
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
  if (econLoadout()) return; // Plant & Defuse: you buy your gear
  sendItemSel();
  if (G.forcedLoadout) { $('loNote').textContent = G.forcedLoadout.only ? 'this mode hands everyone the same weapons' : 'randomizer is on: you get a random loadout every life'; return; }
  if (W.only) { $('loNote').textContent = 'this mode hands you one weapon: your loadout comes back after the match'; return; }
  const canNow = force || !G.joined || !ME.alive || performance.now() - (G.spawnT || 0) < 5000;
  prefetchLoadout(S.loadout); // (a new item or killstreak: its model, ahead of time)
  if (canNow) { setLoadout(S.loadout); G.pendingLoadout = false; $('loNote').textContent = ''; }
  else { G.pendingLoadout = true; $('loNote').textContent = 'loadout switches when you respawn'; }
}
// the server only lets you use the item you have equipped (it switches it by the same rule as the weapons)
function sendItemSel() {
  const i = S.loadout.item || 'frag';
  if (!G.joined || i === G.itemSent) return;
  G.itemSent = i;
  net.send({ t: 'itemsel', i });
}
// killstreak picks: the server switches them now, or from your next life while you have a streak going
let streakDraft = null;
const DRAFT_NOTE = 'pick a killstreak for each empty slot', NEXT_NOTE = 'killstreak picks apply next life (you have a streak going)';
const activeStreaks = () => G.activeStreaks || validStreaks(S.loadout.streaks);
function applyStreaks() {
  const list = validStreaks(S.loadout.streaks);
  if (G.joined) net.send({ t: 'streaks', list });
  if (G.joined && (G.streakN || 0) > 0) { $('loNote').textContent = NEXT_NOTE; toast('killstreak picks apply next life'); }
  else G.activeStreaks = list;
  renderStreak(G.streakN || 0);
}
// the server's word on which picks count this life (a kill still in flight when you changed them makes it wait)
net.on('streaks', (m) => {
  if (!Array.isArray(m.list)) return;
  G.activeStreaks = validStreaks(m.list);
  if (m.pending) $('loNote').textContent = NEXT_NOTE;
  else if ($('loNote').textContent === NEXT_NOTE) $('loNote').textContent = '';
  renderStreak(G.streakN || 0);
});

// ------------------------------------------------------------ cosmetics screen
G.cosSel = S.loadout.primary;
let skinSendT = null;
function sendSkins() {
  clearTimeout(skinSendT);
  skinSendT = setTimeout(() => { if (G.joined) net.send({ t: 'skin', s: wantSkins(), fav: myFavs() }); }, 250); // random slots go as 'random': the server rolls them
}
// the weapons that show up in COSMETICS (the rifle form of the scythe borrows the scythe's look)
function skinnable() { return ORDER.filter((id) => WEAPONS[id] && !WEAPONS[id].modeOnly && (SLOTS.includes(WEAPONS[id].slot) || itemModel(id) || id === 'scythe')); }
// items you see in your hand wear skins (popper, reverse card). the thrown duck is a plain projectile, so not that
function itemModel(id) { return Object.values(ITEMS).some((it) => it.w === id); }
// nothing picked = no entry. a wrap mode that isn't normal is kept even without a wrap, so it's still there when you pick one
const plainSkin = (skin) => skin[0] === 'default' && skin[1] === 'none' && skin[2] === 'none' && (skin[3] || 'default') === 'default' && (skin[4] || 'normal') === 'normal';
function storeSkin(id, skin) {
  if (plainSkin(skin)) delete S.skins[id];
  else S.skins[id] = skin;
}
// wrap / hat / effect on EVERY weapon at once (each weapon keeps its own model)
function setPartAll(idx, value) {
  for (const id of skinnable()) { const sk = validSkin(S.skins[id]).slice(); sk[idx] = value; storeSkin(id, sk); }
  saveSettings(); recomputeEquipped(); sendSkins(); rebuildOne(); // visuals only: keeps a randomizer or pending loadout
}
// copy-to-every-weapon starts unticked every time you open COSMETICS (it isn't saved): you dress one weapon unless you ask
let skinAllNow = false;
const allMode = () => skinAllNow;
function setSkin(id, skin) {
  if (plainSkin(skin)) delete S.skins[id];
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
  for (const [k, v] of Object.entries(BOTTOMS)) if (v.ach === achId) out.push({ slot: 'bottom', id: k, name: v.name }); // (Overalls)
  for (const [k, v] of Object.entries(TOPS)) if (v.ach === achId) out.push({ slot: 'top', id: k, name: v.name }); // (Maid Dress)
  for (const t of LOOT_TYPES) for (const [k, v] of Object.entries(COSMETICS[t])) if (v.ach === achId) out.push({ type: t, id: k, name: v.name }); // weapon skins live in COSMETICS
  return out;
}
function setLook(look) {
  G.settings.look = look;
  saveSettings();
  if (G.joined) net.send({ t: 'look', look: validLook(look, myAchs()) });
}
// every achievement (and old one), for trying on locked accessories in the preview only: what you wear stays validLook(look, myAchs())
const ALL_ACHS = new Set([...Object.keys(ACHIEVEMENTS), ...LOOK_SLOTS.flatMap((sl) => Object.values(ACCESSORIES[sl]).map((v) => v.legacy).filter(Boolean))]);
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
      const have = hasAcc(v, achs); // achievement-locked styles (Overalls) work like locked accessories: a chip you can try on
      c.className = 'chip' + ((look[key] || DEFAULT_LOOK[key]) === k ? ' on' : '') + (have ? '' : ' locked');
      c.textContent = v.name;
      if (v.ach) {
        c.style.setProperty('--rc', '#ffe14d');
        c.title = `${ACHIEVEMENTS[v.ach].name}: ${ACHIEVEMENTS[v.ach].desc}`;
        c.addEventListener('mouseenter', () => { const t = validLook({ ...look, [key]: k }, ALL_ACHS); showCharacter(buildCharacter, t.color || G.myColor || '#ff4fd8', t); });
        c.addEventListener('mouseleave', () => showCharacter(buildCharacter, shown.color || G.myColor || '#ff4fd8', shown));
      }
      c.addEventListener('click', () => {
        if (!have) { toast(`${v.name}: unlock "${ACHIEVEMENTS[v.ach].name}" (${ACHIEVEMENTS[v.ach].desc})${account.loggedIn ? '' : '. log in so it counts'}`, 3200); return; }
        setLook({ ...look, [key]: k }); buildCharacterUI();
      });
      el.append(c);
    }
  };
  swatches('lk-skin', 'skin', SKIN_TONES, 'mannequin');
  styles('lk-hair', 'hair', HAIRS); swatches('lk-hairColor', 'hairColor', HAIR_COLORS);
  styles('lk-top', 'top', TOPS); swatches('lk-topColor', 'topColor', CLOTH_COLORS, look.top === 'runner' ? 'hi-vis yellow' : look.top === 'maid' ? 'classic black' : 'same as your colour');
  styles('lk-bottom', 'bottom', BOTTOMS); swatches('lk-bottomColor', 'bottomColor', CLOTH_COLORS, 'same as your colour');
  for (const slot of LOOK_SLOTS) {
    const el = $('lk-' + slot);
    el.innerHTML = '';
    for (const [k, v] of Object.entries(ACCESSORIES[slot])) {
      const have = hasAcc(v, achs);
      const c = document.createElement('button');
      c.className = 'chip' + (look[slot] === k ? ' on' : '') + (have ? '' : ' locked');
      c.textContent = v.name;
      if (v.ach) c.style.setProperty('--rc', '#ffe14d');
      c.title = v.ach ? `${ACHIEVEMENTS[v.ach].name}: ${ACHIEVEMENTS[v.ach].desc}` : 'free';
      c.addEventListener('mouseenter', () => { const t = validLook({ ...look, [slot]: k }, ALL_ACHS); showCharacter(buildCharacter, t.color || G.myColor || '#ff4fd8', t); }); // try it on, locked or not
      c.addEventListener('mouseleave', () => showCharacter(buildCharacter, shown.color || G.myColor || '#ff4fd8', shown));
      if (v.legacy && achs.has(v.legacy) && !achs.has(v.ach)) c.title += ' (yours anyway: you earned them before they moved here)';
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
  const h = document.createElement('div'); h.className = 'lt'; h.textContent = `achievements ${[...achs].filter((a) => ACHIEVEMENTS[a]).length}/${Object.keys(ACHIEVEMENTS).length}`;
  list.append(h);
  const st = (account.me && account.me.stats) || {};
  for (const [id, a] of Object.entries(ACHIEVEMENTS)) {
    const d = document.createElement('div');
    const done = achs.has(id);
    d.className = 'ach' + (done ? ' done' : '');
    const b = document.createElement('b'); b.textContent = (done ? '★ ' : '') + a.name;
    const t = document.createElement('div'); t.textContent = a.desc;
    const have = Math.min(a.goal, achProgress(a, st));
    const bar = document.createElement('div'); bar.className = 'bar';
    const fill = document.createElement('i'); fill.style.width = (done ? 100 : (have / a.goal) * 100) + '%'; bar.append(fill);
    const rw = document.createElement('div'); rw.className = 'rw';
    rw.textContent = 'unlocks ' + rewardsFor(id).map((x) => x.name).join(', ');
    d.append(b, t, bar, rw);
    if (a.feats) d.insertBefore(royalBoxes(done ? ROYAL_ALL : st[a.stat] || 0, 0, a.feats), bar); // the parts, ticked or not
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
    top: pick(Object.entries(TOPS).filter(([, v]) => hasAcc(v, achs)).map(([k]) => k)), topColor: pick(CLOTH_COLORS), bottom: pick(Object.entries(BOTTOMS).filter(([, v]) => hasAcc(v, achs)).map(([k]) => k)), bottomColor: pick(CLOTH_COLORS) };
  for (const s2 of LOOK_SLOTS) look[s2] = pick(Object.entries(ACCESSORIES[s2]).filter(([, v]) => hasAcc(v, achs)).map(([k]) => k));
  setLook(look); buildCharacterUI();
});
$('lkReset').addEventListener('click', () => { setLook({ ...DEFAULT_LOOK }); buildCharacterUI(); });

// hover a cosmetic to see it on the weapon in the preview, locked or not; leaving puts your real look back.
// req: a locked achievement skin whose "what it takes" box shows while hovering
function tryOn(chip, skinFn, id, sk, req) {
  const box = () => req && [...$('skAch').children].find((b) => b.dataset.skin === req);
  chip.addEventListener('mouseenter', () => { showPreview(id, skinFn()); const b = box(); if (b) b.style.display = ''; });
  chip.addEventListener('mouseleave', () => { showPreview(id, ownedSkin(sk, G.inv, id)); const b = box(); if (b) b.style.display = 'none'; });
}
function buildCosmeticsUI() {
  const list = $('cosWeapons');
  list.innerHTML = '';
  for (const slot of [...SLOTS, 'item', 'streak']) { // items with a model (popper, reverse card) wear skins too
    const h = document.createElement('div');
    h.className = 'lt'; h.textContent = slot === 'streak' ? 'killstreak' : slot === 'item' ? `item (${K.label('item')})` : slot;
    list.append(h);
    for (const id of ORDER) {
      const w = WEAPONS[id];
      if (w.slot !== slot || id === 'scythe_rifle' || (slot === 'item' && !itemModel(id))) continue;
      const b = document.createElement('button');
      b.className = 'wpick' + (G.cosSel === id ? ' on' : '');
      if (modelsFor(id).length > 1) b.title = 'has skins';
      b.textContent = w.name + (S.skins[id] && !plainSkin([...S.skins[id].slice(0, 4), 'normal']) ? ' *' : ''); // a wrap mode alone isn't a skin
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
    let list = Object.entries(COSMETICS[type]);
    if (type === 'finish') list = wrapFilterList(list, sk[idx]); // 60-odd wraps: rarity order + the filter row
    for (const [k, v] of list) {
      const c = document.createElement('button');
      const have = owns(G.inv, type, k);
      c.className = 'chip' + (sk[idx] === k ? ' on' : '') + (have ? '' : ' locked');
      c.textContent = v.name;
      c.style.setProperty('--rc', RARITY[v.rarity].color);
      c.title = `${RARITY[v.rarity].name}${have ? '' : ' (locked: roll to unlock)'}`;
      tryOn(c, () => { const s2 = sk.slice(); s2[idx] = k; return s2; }, id, sk); // hover: try it on, locked or not
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
  buildSprayUI();
  wrapModeUI(id, sk);
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
    const ach = v.ach && ACHIEVEMENTS[v.ach]; // achievement skins: not in crates, you earn them
    if (ach) { c.classList.add('achchip'); c.title = `${ach.name}: ${ach.desc}`; }
    tryOn(c, () => { const s2 = sk.slice(); s2[3] = k; return s2; }, id, sk, !have && ach ? k : null); // hover: try it on (+ what it takes)
    c.addEventListener('click', () => {
      if (!have && ach) { toast(`${v.name}: unlock "${ach.name}" (${ach.desc})${account.loggedIn ? '' : '. log in so it counts'}`, 3600); return; }
      if (!have) { toast(`${v.name} is ${RARITY[v.rarity].name}. win rounds to get rolls.`); return; }
      const s2 = sk.slice(); s2[3] = k; setSkin(id, s2); buildCosmeticsUI();
    });
    $('sk-model').append(c);
  }
  buildGrappleUI();
  // a locked achievement skin: what it takes, with the parts you've ticked so far. only shown while you hover it
  $('skAch').innerHTML = '';
  for (const k of models) {
    const v = COSMETICS.model[k], a = v.ach && ACHIEVEMENTS[v.ach];
    if (!a || owns(G.inv, 'model', k)) continue;
    const st = (account.me && account.me.stats) || {}, done = myAchs().has(v.ach);
    const box = document.createElement('div'); box.className = 'achskin' + (done ? ' done' : '');
    box.dataset.skin = k; box.style.display = 'none';
    const h = document.createElement('b'); h.textContent = done ? `★ ${v.name}: yours` : `${v.name} (locked): ${a.name} ${Math.min(a.goal, achProgress(a, st))}/${a.goal}`;
    const t = document.createElement('div'); t.textContent = done ? `${a.name} complete${k === 'sniper_golden' ? '. stays gold under any wrap' : ''}` : a.desc + (account.loggedIn ? '' : '. log in so it counts');
    box.append(h, t);
    if (a.feats) box.append(royalBoxes(done ? ROYAL_ALL : st[a.stat] || 0, 0, a.feats));
    $('skAch').append(box);
  }
  showPreview(id, ownedSkin(sk, G.inv, id));
}
// the wrap list's filter row: rarity pills, OWNED, and a search box. the wrap you're wearing always shows
const WF = { r: 'all', q: '' };
const RAR_ORDER = ['free', 'common', 'rare', 'epic', 'legendary'];
function wrapFilterList(list, cur) {
  const el = $('skWrapFilter');
  if (!el.dataset.built) { // built once: rebuilding it on every click would eat the search box focus
    el.dataset.built = '1';
    for (const r of ['all', 'owned', ...RAR_ORDER.slice(1)]) {
      const b = document.createElement('button');
      b.dataset.r = r; b.textContent = r === 'all' ? 'ALL' : r === 'owned' ? 'OWNED' : RARITY[r].name.toUpperCase();
      if (RARITY[r]) b.style.setProperty('--rc', RARITY[r].color);
      b.addEventListener('click', () => { WF.r = r; buildCosmeticsUI(); });
      el.append(b);
    }
    const q = document.createElement('input');
    q.type = 'search'; q.placeholder = 'search wraps'; q.maxLength = 24; q.spellcheck = false;
    q.addEventListener('input', () => { WF.q = q.value.trim().toLowerCase(); buildCosmeticsUI(); });
    const n = document.createElement('span'); n.className = 'n';
    el.append(q, n);
  }
  for (const b of el.querySelectorAll('button')) b.classList.toggle('on', b.dataset.r === WF.r);
  const out = list.filter(([k, v]) => k === cur || ((WF.r === 'all' || (WF.r === 'owned' ? owns(G.inv, 'finish', k) : v.rarity === WF.r)) && (!WF.q || v.name.toLowerCase().includes(WF.q) || k.includes(WF.q))))
    .sort((a, b) => RAR_ORDER.indexOf(a[1].rarity) - RAR_ORDER.indexOf(b[1].rarity));
  el.querySelector('.n').textContent = `${out.length}/${list.length}`;
  return out;
}
// NORMAL / REVERSE / FULL: which part of the weapon the wrap paints (wrapzones.js). free, goes with the wrap
const WRAP_HINT = {
  normal: 'normal: the wrap goes on the handle / body. the blade and barrel keep their metal',
  reverse: 'reverse: the wrap goes on the blade / barrel / business end. the handle keeps its look',
  full: 'full: the whole weapon, like the old wraps',
};
function wrapIcon(mode) { // a tiny knife: the half the wrap paints is pink
  const on = (z) => (mode === 'full' || mode === z ? '#ff4fd8' : '#9a9aa4');
  return `<svg viewBox="0 0 46 14"><rect x="1" y="4" width="15" height="6" fill="${on('normal')}" stroke="#000" stroke-width="1.5"/>`
    + `<rect x="16" y="2" width="3" height="10" fill="${on('normal')}" stroke="#000" stroke-width="1.5"/>`
    + `<path d="M19 3 L40 3 L45 7 L40 11 L19 11 Z" fill="${on('reverse')}" stroke="#000" stroke-width="1.5"/></svg>`;
}
function wrapModeUI(id, sk) {
  const el = $('sk-wrapmode');
  el.innerHTML = '';
  el.classList.toggle('off', sk[0] === 'default');
  for (const m of WRAP_MODES) {
    const b = document.createElement('button');
    b.className = sk[4] === m ? 'on' : '';
    b.innerHTML = wrapIcon(m);
    b.append(WRAP_MODE_NAMES[m].toUpperCase());
    b.title = WRAP_HINT[m];
    b.addEventListener('click', () => {
      if (allMode()) setPartAll(4, m);
      else { const s2 = sk.slice(); s2[4] = m; setSkin(id, s2); }
      buildCosmeticsUI();
    });
    el.append(b);
  }
  const h = document.createElement('div'); h.className = 'hint';
  h.textContent = sk[0] === 'default' ? 'pick a wrap, then choose where it goes' : WRAP_HINT[sk[4]];
  el.append(h);
}
$('skRandom').addEventListener('click', () => {
  const pick = (t) => { const ks = Object.keys(COSMETICS[t]).filter((k) => owns(G.inv, t, k)); return ks[(Math.random() * ks.length) | 0]; };
  if (allMode()) {
    const parts = ['finish', 'hat', 'effect'].map(pick), wm = WRAP_MODES[(Math.random() * 3) | 0];
    for (const id of skinnable()) { const sk = validSkin(S.skins[id]).slice(); sk[0] = parts[0]; sk[1] = parts[1]; sk[2] = parts[2]; sk[4] = wm; storeSkin(id, sk); }
    saveSettings(); recomputeEquipped(); sendSkins(); rebuildOne();
  } else setSkin(G.cosSel, [...TYPES.map(pick), WRAP_MODES[(Math.random() * 3) | 0]]);
  buildCosmeticsUI();
});
$('skReset').addEventListener('click', () => {
  if (allMode()) {
    for (const id of skinnable()) { const sk = validSkin(S.skins[id]).slice(); sk[0] = 'default'; sk[1] = 'none'; sk[2] = 'none'; sk[4] = 'normal'; storeSkin(id, sk); }
    saveSettings(); recomputeEquipped(); sendSkins(); rebuildOne();
  } else setSkin(G.cosSel, DEFAULT_SKIN.slice());
  buildCosmeticsUI();
});
$('skAll').addEventListener('click', () => { // copy this weapon's wrap/hat/effect to everything (models stay)
  const sk = validSkin(S.skins[G.cosSel]);
  for (const id of skinnable()) { const s2 = validSkin(S.skins[id]).slice(); s2[0] = sk[0]; s2[1] = sk[1]; s2[2] = sk[2]; s2[4] = sk[4]; storeSkin(id, s2); }
  saveSettings(); recomputeEquipped(); sendSkins(); rebuildOne(); buildCosmeticsUI();
});
$('skAllMode').addEventListener('change', () => { skinAllNow = $('skAllMode').checked; buildCosmeticsUI(); });

// ------------------------------------------------------------ grapple skins (one per player, everyone sees your rope)
function setGrap(id) {
  S.grap = id;
  saveSettings();
  if (G.joined) net.send({ t: 'grap', id });
}
function buildGrappleUI() {
  const el = $('sk-grapple');
  el.innerHTML = '';
  const cur = myGrapple(), live = initGrapplePreview($('grapPreview'));
  showGrapple(cur);
  for (const [k, v] of Object.entries(COSMETICS.grapple)) {
    const have = owns(G.inv, 'grapple', k);
    const c = document.createElement('button');
    c.className = 'gcard' + (cur === k ? ' on' : '') + (have ? '' : ' locked');
    c.style.setProperty('--rc', RARITY[v.rarity].color);
    c.title = `${v.name} (${RARITY[v.rarity].name}): ${v.desc}`;
    if (live) { const im = document.createElement('img'); im.src = grappleThumb(k); im.alt = ''; c.append(im); }
    const nm = document.createElement('span'); nm.textContent = v.name;
    c.append(nm);
    c.addEventListener('mouseenter', () => showGrapple(k)); // hover to try it on in the preview, locked or not
    c.addEventListener('mouseleave', () => showGrapple(myGrapple()));
    c.addEventListener('click', () => {
      if (!have) { showGrapple(k); toast(`${v.name} (${RARITY[v.rarity].name}): ${v.desc}. find it in duffel bags`, 3000); return; }
      setGrap(k); buildGrappleUI();
    });
    el.append(c);
  }
}

// ------------------------------------------------------------ input
let jumpPressed = false, chatOpen = false, scoresOpen = false;
const inGame = () => G.joined && !chatOpen && $('menu').classList.contains('hidden');

function openChat() {
  chatOpen = true;
  releaseHeld(); // keyups typed in the box don't reach the game, so let go of everything now
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
  if (secAimDown()) return; // tv remote: aim (right click) rewinds
  if (W.cur === 'cards') { cycleCard(); return; }
  if (heavyAttack()) return; // knife: right click is the heavy stab
  if (W.cur === 'katana' && !rigOn()) { if (!K.get('parry').some(Boolean)) parry(); return; } // katana: the parry key parries (pressed()); aim only stands in when parry is unbound
  if (W.cur === 'akimbo') { W.aimHeld = true; return; } // Lefty & Righty: the aim key is the right gun's trigger (never a toggle)
  if (S.toggleAim) W.aimHeld = !W.aimHeld; else W.aimHeld = true;
}
function aimUp() { if (!S.toggleAim || W.cur === 'akimbo') W.aimHeld = false; }

addEventListener('keydown', (e) => {
  if (!inGame() || K.typing(e) || document.activeElement === $('name')) return;
  if (econKey(e)) return; // buy menu, drop, pause (keys.js 'buy' / 'drop' / 'pause')
  if (K.bound(e) || e.code === 'Tab') e.preventDefault(); // bound keys never scroll, tab focus or click a button
  pressed(e);
});
// a key or a mouse button went down in game. every check goes through the bindings (keys.js), so any action works on either
function pressed(e) {
  if ((RP.active || G.killcamPending) && K.matches('skip', e)) { e.preventDefault(); skipReplay(); return; }
  if (esKey(e, VOTES.findIndex((a) => K.matches(a, e)))) { e.preventDefault(); return; } // end screen: the vote keys win over any game action on the same key, arrows switch tabs
  if (brKey(e)) return; // jank royale: F pick up, H heal, space spectates the next one
  if (loreKey(e, canUse(G.round, ME.pos))) { e.preventDefault(); return; } // the use key next to a hidden NPC / cat (not where it plants, defuses or buys), 1-3 answer in a chat
  if (K.matches('scores', e)) { e.preventDefault(); scoresOpen = true; renderScores(); return; }
  if (K.matches('chat', e)) { e.preventDefault(); openChat(); return; }
  if (K.matches('menu', e)) { if (document.pointerLockElement) document.exitPointerLock(); pause(); return; }
  if (lobbyKey(e)) return; // a mode lobby: ready up
  if (gearKeyDown(e)) return; // pop quiz answers (1-4), goggles flash (nvgFlash)
  if (lassoKey(e, true)) return; // holding someone on the lasso: reel keys, fire / aim lets go, no weapon switching. held: jump / move wriggles
  if (K.matches(BUBBLED, e) && stuckInBubble(true)) return; // sealed in a soap bubble: no shooting, aiming, grapple, items, dash, t-bag, sprays or streaks
  if (K.matches(SEC_STOPPED, e) && secBlocked()) return; // tased, paused or jailed: hands off everything
  const now = performance.now(), out = now < (ME.sleepUntil || 0) || now < (ME.quizUntil || 0); // asleep on the floor / pens down for a pop quiz: no shooting
  if (W.cur === 'katana' && !rigOn() && K.matches('parry', e)) { if (!e.repeat && !out) parry(); return; } // the parry key wins while the katana's out
  if (K.matches('jump', e)) { e.preventDefault(); if (!e.repeat) jumpPressed = true; }
  if (K.matches('grapple', e) && !e.repeat && !out) tryHook();
  if (K.matches('slot1', e)) switchSlot(0);
  if (K.matches('slot2', e)) switchSlot(1);
  if (K.matches('slot3', e)) switchSlot(2);
  if (K.matches('lastSlot', e)) lastSlot();
  if (K.matches('reload', e)) reload();
  if (K.matches('use', e) && !e.repeat) { if (canUse(G.round, ME.pos)) startUse(); else if (!cartKey()) inspect(); } // the use key on a shopping cart: hop in / out
  if (K.matches('dash', e)) W.dashHeld = true;
  if (K.matches('scythe', e) && !e.repeat) toggleScythe();
  if (K.matches('item', e) && !e.repeat) useItem();
  if (K.matches('spray', e) && !e.repeat) spray();
  const streak = ['streak1', 'streak2', 'streak3'].findIndex((a) => K.matches(a, e));
  if (streak >= 0 && !e.repeat) deployStreak(streak);
  if (K.matches('slot4', e)) switchSlot(3);
  if (K.matches('crouch', e) && !e.repeat) {
    const t = crouchTap(performance.now());
    if (t === 2) { net.send({ t: 'tbag' }); G.shake = 1; }
    else if (t === 1) G.shake = Math.max(G.shake, 0.25);
  }
  if (K.matches('fire', e) && !e.repeat && !out) fireDown();
  if (K.matches('aim', e) && !e.repeat && !out) aimDown();
}
const BUBBLED = ['fire', 'aim', 'grapple', 'item', 'dash', 'crouch', 'spray', 'streak1', 'streak2', 'streak3'];
const SEC_STOPPED = ['fire', 'aim', 'grapple', 'item', 'dash', 'spray', 'streak1', 'streak2', 'streak3']; // (secondaries.js: stunned, paused, caged)
// a key or button came up: releases match whatever pressed the action, even if it got rebound since
function released(e) {
  if (e.type === 'keyup' && K.typing(e)) return; // typed in chat / a text box (opening chat already let go of everything)
  lassoKey(e, false);
  if (K.up('use', e)) stopUse();
  if (K.up('dash', e)) W.dashHeld = false;
  if (K.up('scores', e)) { scoresOpen = false; hud.scores(false); }
  if (K.up('grapple', e)) releaseHook();
  if (K.up('fire', e)) fireUp();
  if (K.up('aim', e)) aimUp();
}
addEventListener('keyup', released);
addEventListener('mousedown', (e) => {
  if (!inGame()) return;
  if (e.target instanceof Element && e.target.closest('#endscreen')) return; // the end screen's cards and tabs take the click, not your gun (or the replay skip)
  if (esClickShown()) { esHideClick(); lock(); return; } // CLICK TO DROP IN: that click only grabs the mouse
  if (RP.mode === 'killcam' || G.killcamPending) { skipReplay(); return; } // a click skips the killcam
  if (RP.mode === 'hl') return; // ...but not the play of the round
  if (brMouse(e)) return; // jank royale: no shooting from the blimp; out = click to watch someone else
  if (econMouse(e)) return;
  if (e.button === 1 && K.bound(e)) e.preventDefault(); // a bound middle button never starts autoscroll
  pressed(e);
});
addEventListener('mouseup', released);
// let go of everything held: losing focus, or the bindings changing under your fingers
function releaseHeld() { K.clear(); W.held = false; W.aimHeld = false; W.dashHeld = false; stopUse(); releaseHook(); if (scoresOpen) { scoresOpen = false; hud.scores(false); } }
K.onChange((rebound) => { if (rebound) releaseHeld(); });
addEventListener('contextmenu', (e) => e.preventDefault());
addEventListener('wheel', (e) => { if (inGame() && !esActive() && !lassoWheel(e.deltaY)) cycleSlot(e.deltaY > 0 ? 1 : -1); }, { passive: true }); // not while the end screen is up (its tab panel scrolls); holding someone on the lasso: the wheel reels
addEventListener('mousemove', (e) => {
  if (document.pointerLockElement !== canvas) return;
  if (performance.now() < (G.spinUntil || 0)) return; // the aimbot has the wheel
  if (performance.now() < (ME.sleepUntil || 0)) return; // asleep on the floor: no looking around either
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
addEventListener('blur', releaseHeld);
addEventListener('resize', resizePreview);

function renderScores() {
  const rows = [{ name: G.myName, color: G.myColor, k: G.kills, d: G.deaths, me: true, card: cardUrlFor(G.myId) }];
  for (const r of G.remotes.values()) if (!(r.bot && r.name === 'Dummy')) rows.push({ id: r.id, name: r.name, color: r.color, k: r.k, d: r.d, card: cardUrlFor(r.id) });
  zmScoreRows(rows); // zombies: no zombies on it, credits next to names
  rows.sort((a, b) => b.k - a.k || a.d - b.d);
  ggScoreRows(rows); infScoreRows(rows); // gun game: by rung · infection: survivors first, zombies green
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
function skinOf(owner, wid) { return (owner === G.myId ? W.skinOver || G.equipped : (G.skins.get(owner) || {}))[wid]; }
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
  G.holes.set(m.id, { mesh, p: m.p, born: performance.now() - (m.age || 0) * 1000, o: m.o, big: !!m.big, on: m.on || 0 });
  if (m.on && m.age < 0) duckStuck(G.holes.get(m.id), m); // a duck stuck on someone: the hole opens (and hums) in a moment
  else sfx.hole(m.p);
}
function addRemoteInfo(p) {
  G.names.set(p.id, { name: p.name, color: p.color, bot: p.bot, level: p.level, look: p.look, card: p.card || '', skins: p.skins || {}, team: p.team || 0, grap: p.grap });
  G.skins.set(p.id, p.skins || {});
}

// ------------------------------------------------------------ net handlers
net.on('welcome', (m) => {
  G.myId = m.id; G.myName = m.name; G.myColor = m.color; G.joined = true; connecting = false;
  airReset();
  brReset(); // a new room: whatever royale the last one had is over (that room's 'off' never reaches us)
  G.mode = m.mode; G.cfg = m.cfg; G.lk = m.lk || null;
  lobbyMe(m.id); lobbyInfo(m.lobby || null); // a mode lobby: the countdown is on
  G.game = m.game; // (music needs it before the first round info arrives)
  musicNewMatch(); // a fresh random song for this match
  loadMap(m.cfg.map);
  ME.pos = m.pos.slice(); ME.vel = [0, 0, 0]; ME.alive = true; ME.hp = 100; ME.seq = m.q;
  ME.yaw = Math.atan2(m.pos[0], m.pos[2]);
  if (m.mode === 'training') ME.yaw = 0;
  G.spawnT = performance.now();
  for (const p of m.players) addRemoteInfo(p);
  for (const pl of m.peels) addPeel(pl);
  for (const pr of m.projs) spawnProj(pr);
  for (const h of m.holes || []) addHole(h);
  for (const b of m.bubbles || []) addBubble(b); // domes and smoke that are already up when you join
  for (const s2 of m.smokes || []) if (Array.isArray(s2)) G.smokes.push({ p: s2.slice(0, 3), r: ITEMS.smoke.r, until: performance.now() + (s2[3] || 0) });
  hud.wave(m.wave);
  renderRound(m.round);
  $('roundEnd').classList.add('hidden');
  G.round = m.round; G.myTeam = m.team || 0;
  econWelcome(m);
  G.pocket = []; G.streakN = 0; G.activeStreaks = validStreaks(S.loadout.streaks); renderStreak(0);
  G.kat.clear(); setMyKatana(0);
  for (const [id, n] of m.kat || []) G.kat.set(id, n);
  setupObjectives(m.cfg.map);
  zmSetup(m.cfg.map);
  clearTags();
  for (const g of m.tags || []) addTag(g.id, g.p, g.team);
  openVote(m.vote);
  skipVote(m.skip || null); // a /skip vote that's already on
  refillAmmo();
  resetItems(); // a fresh player on the server: welcome.ic has its real charges
  G.itemSent = null;
  applyLoadout(true);
  if (m.ic) onIc(m.ic);
  updateLabel();
  $('status').textContent = '';
  const tips = {
    ffa: `${K.label('chat')} to chat, ${K.label('menu')} for menu. Change the map or hipfire in Match Settings. /skip in chat votes to skip the match.`,
    bots: `bots are dumb but there are a lot of them. ${K.label('menu')} for menu. /skip in chat skips the match.`,
    coop: 'survive the waves. bots only hurt humans, no friendly fire.',
    training: 'dummies respawn instantly. knock the ones on the left ledge off. movement playground on the right.',
  };
  hud.chat(null, null, `you are ${m.name}. ${tips[m.mode] || ''}`);
  clearSprays(); sprayT = -1e9;
  for (const s of m.sprays || []) addSpray(s, true); // graffiti that was already on the walls
  for (const pt of m.mpatch || []) addPatch(pt); // marbles already on the floor
});
net.on('cfg', (m) => {
  const mapChanged = m.cfg.map !== G.cfg.map;
  G.cfg = m.cfg;
  if (mapChanged) { loadMap(m.cfg.map); clearEntities(); setupObjectives(m.cfg.map); G.smokes.length = 0; } // the server drops its smokes too
  if (mapChanged) clearSprays(); // sprays belong to the map they were painted on
  if (mapChanged) zmSetup(m.cfg.map);
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
  if (m.id === G.myId) { czRolled(m.s); recomputeEquipped(); rebuildOne(); return; } // your random slots, rolled for this life
  G.skins.set(m.id, m.s || {});
  const r = G.remotes.get(m.id);
  if (r) r.setSkins(m.s);
});
net.on('gr', (m) => { // someone picked another grapple skin
  const n = G.names.get(m.id);
  if (n) n.grap = m.g;
  const r = G.remotes.get(m.id);
  if (r) r.setGrapple(m.g);
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
  const where = rewardsFor(m.id).some((x) => x.type) ? 'COSMETICS' : 'CHARACTER';
  hud.msg(`ACHIEVEMENT: ${a.name}`, 3, 'brag');
  esAch({ name: a.name, desc: a.desc });
  hud.chat(null, null, `achievement unlocked: ${a.name} (${a.desc})${rewards ? ' · unlocked ' + rewards + ' in ' + where : ''}`);
  sfx.kill();
  if (m.id === 'airborne') airFlourish();
  const skins = rewardsFor(m.id).filter((x) => x.type === 'model');
  if (skins.length && account.me) unlockSkins(skins);
});
// an achievement that unlocks a weapon skin (Sniper Royalty: the Golden Sniper) puts it straight on that weapon.
// the server lets you: it checks your achievements, not your inventory
function unlockSkins(list) {
  G.inv = achInv(account.me.inv, account.me.achs);
  for (const r of list) {
    const w = COSMETICS.model[r.id].weapon, sk = validSkin(S.skins[w]).slice();
    sk[3] = r.id;
    storeSkin(w, sk);
  }
  saveSettings(); recomputeEquipped(); sendSkins(); rebuildOne();
  if (list.some((r) => r.id === 'sniper_golden')) royalUnlock(`SNIPER ROYALTY ${ROYAL_FEATS.length}/${ROYAL_FEATS.length} · it's on your sniper now (swap it in COSMETICS)`);
}
// Smarty Pants: a pop quiz answer that counted (the server's count)
net.on('quizpt', (m) => {
  const n = Number(m.n) || 0, goal = ACHIEVEMENTS.smarty.goal;
  if (account.me) account.me.stats = { ...(account.me.stats || {}), quiz_right: n };
  if (n < goal) setTimeout(() => hud.msg(`SMARTY PANTS ${n}/${goal}`, 1.6, 'brag'), 1900); // after the GOLD STAR callout
});
// Sniper Royalty: you just ticked a box (the server decides; a guest is told it would have counted)
net.on('royal', (m) => {
  const all = m.all | 0, add = m.add | 0;
  if (!add) return;
  if (account.me && !m.guest) account.me.stats = { ...(account.me.stats || {}), sniper_feats: all };
  royalToast(all, add, !!m.guest);
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
      r = new Remote(id, n.level ? `${n.name} [${n.level}]` : n.name, n.color, G.skins.get(id) || {}, n.bot, n.look, n.team || 0);
      r.katN = G.kat.get(id) || 0;
      r.setGrapple(n.grap);
      G.remotes.set(id, r);
    }
    r.snap(m.s, e);
  }
  if (m.wave) hud.wave(m.wave);
  if (m.round) { if (!G.round || G.round.game !== m.round.game) { G.round = m.round; updateLabel(); } G.round = m.round; lobbyInfo(m.round.warm || null); }
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
    if (r) { const was = !!r.team; r.team = team; if (r.color !== color || was !== !!team) r.setLook(r.outfit, color); } // team colour beats clothes
  }
  if (G.round) G.round.game = m.game;
  G.game = m.game;
  updateLabel();
  if (screen === 'match') syncMatchUI();
  if (GAMES[m.game] && GAMES[m.game].teams && G.myTeam) hud.msg(`YOU ARE ${TEAMS[G.myTeam].name}`, 2, 'brag');
});
net.on('tag+', (m) => addTag(m.id, m.p, m.team));
net.on('tagc', () => clearTags());
net.on('tagx', (m) => {
  removeTag(m.id);
  if (m.by === G.myId) { hud.msg(m.k === 'confirm' ? 'KILL CONFIRMED +1' : 'KILL DENIED', 1.2, 'brag'); if (m.k === 'confirm') sfx.cash(); else sfx.ting(); }
});
net.on('bombyou', () => { hud.msg('YOU HAVE THE BOMB', 2, 'brag'); hud.chat(null, null, `you have the bomb: get to site A or B and hold ${K.label('use')} to plant`); });
net.on('bombev', (m) => {
  const [n] = m.id ? nameOf(m.id) : [''];
  if (m.k === 'round') { if (!ecoOn()) hud.msg(`ROUND ${m.n} · ${G.myTeam === m.att ? 'ATTACK' : 'DEFEND'}`, 2.2, 'brag'); } // the economy has its own banner
  else if (m.k === 'planted') { hud.msg(`BOMB PLANTED AT ${m.site}`, 2.2, 'brag'); sfx.ting(); hud.chat(null, null, `${n} planted the bomb at ${m.site}`); }
  else if (m.k === 'defused') { hud.msg('BOMB DEFUSED', 2.2, 'brag'); sfx.kill(); hud.chat(null, null, `${n} defused the bomb`); }
  else if (m.k === 'boom') { G.shake = 1; }
  else if (m.k === 'drop') hud.chat(null, null, 'the bomb was dropped');
  else if (m.k === 'pickup') hud.chat(null, null, `${n} picked up the bomb`);
  else if (m.k === 'win') {
    const mine = m.team === G.myTeam;
    const why = { defused: 'bomb defused', exploded: 'bomb went off', time: 'time ran out', elim: 'team wiped' }[m.why] || '';
    hud.msg(`${TEAMS[m.team].name} WINS THE ROUND`, 3, 'brag');
    hud.chat(null, null, `${TEAMS[m.team].name} wins the round (${why}) · ${m.wins[0]} - ${m.wins[1]}`);
    if (mine) sfx.kill();
  }
});
// ------------------------------------------------------------ items: charges, bubbles, smoke, frost
// item charges: the server's count is the real one, and so is the item it says you have
function onIc(m) {
  if (!m || !Object.hasOwn(ITEMS, m.i)) return;
  if (econIc(m)) return; // Plant & Defuse: the inventory says
  syncItem(m.i, m.n, m.next);
  // (gun game / zombies hand you one weapon and no item, a chaos kit can say no item: the 'ic' doesn't put it back)
  const noItem = W.only || (G.forcedLoadout && G.forcedLoadout.only && G.forcedLoadout.item === 'none');
  if (m.i !== W.item && !noItem) { setItem(m.i); showSlots(); }
}
net.on('ic', onIc);
// the katana grows: everyone sees how long yours is
G.kat = new Map();
net.on('kat', (m) => {
  recordEv({ ...m, was: G.kat.get(m.id) || 0 }); // killcam ghosts start with the length before this change
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
  if (m.id === G.myId) { G.frost = m.n; G.frostT = performance.now(); hud.msg(`${'❄'.repeat(m.n)} FROSTY`, 0.8); }
  const r = G.remotes.get(m.id); if (r) fx.spray([r.pos[0], r.pos[1] + 1.2, r.pos[2]], 10, [0xffffff, 0xbfe8ff], 3, 0.6, 0.1, 2, 1);
});
net.on('freeze', (m) => {
  recordEv(m);
  if (m.id === G.myId) { ME.frozenUntil = performance.now() + m.dur; G.frost = 0; releaseHook(); hud.msg('FROZEN SOLID', m.dur / 1000, 'slip'); sfx.ting(); }
  const r = G.remotes.get(m.id); if (r) { r.frozenUntil = performance.now() + m.dur; sfx.ting(r.pos); }
});
// bubble wand: someone got sealed in a giant soap bubble / it popped (wand.js does the rest)
net.on('trap', (m) => { trapStart(m); recordEv(m); });
net.on('trapx', (m) => { trapEnd(m); recordEv(m); });

// hold F to plant / defuse: keep telling the server while it's held, and stand still
let useTimer = 0;
function startUse() {
  stopUse();
  G.using = true;
  net.send({ t: 'use' });
  // F has to still be down: blur, pause and chat clear the keys, so a lost keyup can't root you in place
  useTimer = setInterval(() => { if (!G.using || !ME.alive || !K.isDown('use')) { stopUse(); return; } net.send({ t: 'use' }); }, 200);
}
function stopUse() { clearInterval(useTimer); useTimer = 0; G.using = false; }
// the end-of-match vote (mode first, then map) lives on the end screen (endscreen.js)
function openVote(v) { G.vote = v || null; if (v) esVote(v); }
net.on('vote', (m) => openVote(m));
net.on('votes', (m) => esVotes(m));
net.on('skipvote', (m) => skipVote(m)); // someone typed /skip (server/skip.js)

// randomizer mode: the server hands you a loadout each life (null = use your own again)
net.on('loadout', (m) => {
  // randomizer: weapons only, you keep your own item. chaos kits (lo.only) come with their own item rule (none)
  G.forcedLoadout = m.lo ? (m.lo.only ? m.lo : { ...m.lo, item: S.loadout.item }) : null;
  hud.descFor = (m.lo && m.lo.desc) || null; // chaos modes can say what a weapon does in this mode
  setLoadout(G.forcedLoadout || S.loadout);
  refillAmmo();
  if (m.lo && !m.lo.only) hud.msg(`${wname(m.lo.primary)} · ${wname(m.lo.secondary)} · ${wname(m.lo.melee)}`, 2.2, 'brag');
});
// gun game / infection: the server hands you exactly one weapon (null = your own loadout again)
net.on('modew', (m) => { if (m.w) endBall(); setOnly(m.w || null, G.forcedLoadout || S.loadout); }); // (a mode weapon ends a wrecking ball: the server already did)
net.on('kb', (m) => applyKb(m.v));
net.on('grab', (m) => shredGrab(m)); // you're in someone's shredder
net.on('slip', (m) => slip(performance.now(), m.k));
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
  if (m.w === 'shredder') shredHit(m);
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
  if (m.k === G.myId && m.v !== G.myId && !RP.active) czKill(m.w); // kills with it (the customize screen's mastery bar)
  courtKill(m); // scales of justice: streaks + revenge
  let [kn, kc] = nameOf(m.k), [vn, vc] = nameOf(m.v);
  [kn, vn] = brNames(m, kn, vn); // jank royale: no names in Pronoun Park
  const via = m.w === 'void' || m.w === 'cough' || ((m.w === 'car' || m.w === 'carboom') && m.via) ? m.via : m.w;
  const victim = G.remotes.get(m.v);
  if (m.pit && m.w === 'void') pitKill(m, victim ? victim.color : m.v === G.myId ? G.myColor : null); // into the shredder pit's teeth (sets m.vel: the bits fly back up)
  // shredder kills: the pieces go through the killer's machine instead of the usual gibs / kill effect
  if (m.w === 'shredder' && shredKill(m, G.remotes, m.v === G.myId ? { pos: ME.pos.slice(), yaw: ME.yaw, color: G.myColor, look: teamLook(validLook(G.settings.look, myAchs()), G.myTeam) } : null)) m.fx = 'none'; // (team colour beats clothes)
  const kfx = m.fx && m.fx !== 'none' ? m.fx : null;
  if (victim) {
    victim.reverseUntil = 0; // the server ends their reverse card on death too
    const vi = G.names.get(m.v) || {};
    const replaced = kfx && playKillFx(kfx, { pos: victim.pos.slice(), vel: m.vel || victim.vel, yaw: victim.yaw, color: victim.color, look: teamLook(vi.look, vi.team), name: vi.name });
    rigDied(victim, m.vel); // they died in the overdrive rig: the frame bursts apart into scrap
    if (replaced) victim.ch.root.visible = false; else victim.breakApart(m.vel || victim.vel);
    wreckDied(victim, m.vel); // they died as a wrecking ball: it bursts open
    victim.frozenUntil = 0;
  } else if (m.v === G.myId && kfx) playKillFx(kfx, { pos: ME.pos.slice(), vel: m.vel || ME.vel, yaw: ME.yaw, color: G.myColor, look: teamLook(validLook(G.settings.look, myAchs()), G.myTeam), name: G.myName });
  const dummy = victim && victim.bot && victim.name === 'Dummy';
  if (zmKillFeed(m, victim)) return; // zombies: a zombie went down. no feed line, the credits popup says it
  let parts;
  if (m.w === 'void' && m.pit) { // the shredder pit
    parts = m.k ? [[kn, kc], [`  [${wname(via)}]  `, wcolor(via)], [vn, vc], ['  fed to the shredder', '#ff5a3a']] : [[vn, vc], ['  fed themselves to the shredder', '#ff5a3a']];
  } else if (m.w === 'void') {
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
  if (m.w === 'hr') parts = hrFeed(vn, vc); // scary forest: the tall guy from HR got them
  const gp = gearKillParts(m, kn, kc, vn, vc, wname, wcolor); // failed a pop quiz, telefragged
  if (gp) parts = gp;
  const hazard = m.w === 'lava' || (m.w === 'duck' && m.sky); // floor is lava / duck rain: nobody owns those
  if (hazard) parts = m.k ? [[kn, kc], [`  [${wname(m.via)}]  `, wcolor(m.via)], [vn, vc], [m.w === 'lava' ? '  into the lava' : '  under a sky duck', '#aaa']] : [[vn, vc], [m.w === 'lava' ? '  touched the floor' : '  got flattened by a sky duck', '#ff8a3a']];
  const brp = brFeed(m, vn, vc); if (brp) parts = brp; // jank royale: the zone
  if (m.ep && m.k) parts.push([`  EPIC ${Math.round(m.ep.d)}m`, '#ffe14d']);
  const carK = (m.w === 'car' || m.w === 'carboom') && carKill(m, kn, kc, vn, vc, wname, wcolor); // traffic: its own lines and icon
  if (carK) parts = carK.parts;
  if (!dummy) hud.feed(parts);
  if (carK && !dummy) carFeedIcon();
  if (m.v === G.myId) epicKC = m.ep && m.ep.lock && m.k && m.k !== G.myId && S.killcam !== false && G.mode !== 'training' ? { ...m.ep, w: via } : null; // too epic to skip (the server holds your respawn)
  if (m.v === G.myId) epicHold = !!(m.ep && m.ep.lock); // ...until it spawns you, killcam or not
  if (m.v === G.myId) {
    if (performance.now() < (ME.sleepUntil || 0) && $('center').textContent === 'zzz...') hud.msg('', 0); // died in your sleep: no "zzz..." over the killcam
    ME.alive = false;
    releaseHook();
    W.held = false; W.aimHeld = false;
    stopLoops();
    G.deadAt = performance.now();
    G.respawnMs = m.rs ?? 2500; // the mode's respawn delay (Plant & Defuse is longer)
    G.frost = 0; ME.frozenUntil = 0; // shattered: no ice overlay on the death screen
    sfx.death();
    deathCard(m.k && m.k !== G.myId ? m.k : 0, via);
    if (m.k && m.k !== G.myId && S.killcam !== false && G.mode !== 'training') queueKillcam(m.k, via);
    if (m.k) {
      hud.dead(true, m.w === 'void'
        ? [[kn, kc], [m.pit ? ' fed you to the shredder' : ' knocked you into the void', '#fff'], [`  (${wname(via)})`, wcolor(via)]]
        : [['killed by ', '#fff'], [kn, kc], [`  (${wname(via)})`, wcolor(via)]]);
    } else hud.dead(true, [[m.w === 'void' ? (m.pit ? 'the shredder ate you. it was not hungry.' : 'you fell into the void') : m.w === 'tbag' ? 'you t-bagged too hard. your knees exploded.' : 'you smoked too much', '#fff']]);
    if (carK) hud.dead(true, carK.dead);
    else if (m.w === 'hr') hud.dead(true, hrDead());
    const gd = gearDeathLine(m);
    if (gd) hud.dead(true, m.k ? [[kn, kc], [' gave you a pop quiz. ', '#fff'], [gd, '#7fffd4']] : [[gd, '#fff']]);
    if (hazard) hud.dead(true, m.k ? [[kn, kc], [m.w === 'lava' ? ' knocked you into the lava' : ' softened you up for a sky duck', '#fff'], [`  (${wname(m.via)})`, wcolor(m.via)]] : [[m.w === 'lava' ? 'the floor was lava' : 'a duck fell out of the sky on you', '#fff']]);
  }
  econKill(m);
  if (m.k === G.myId && m.v !== G.myId) {
    G.streakN = (G.streakN || 0) + 1; // the server counts every kill too, but only tells you at your picks
    renderStreak(G.streakN);
    sfx.kill();
    hud.msg(dummy ? 'dummy down' : m.pit ? 'FED TO THE SHREDDER' : `killed ${vn}`, m.pit ? 1.8 : 1.4, 'brag');
  }
  if (m.ep && m.k === G.myId && m.v !== G.myId) epicBrag({ ...m.ep, w: via });
});
net.on('spawn', (m) => {
  endKillcam();
  gearSpawn();
  secSpawn();
  ME.frozenUntil = 0; G.frost = 0; // item charges come from the server's 'ic' (a new round doesn't refill them)
  ME.pos = m.p.slice(); ME.vel = [0, 0, 0]; ME.alive = true; ME.hp = 100; ME.seq = m.q;
  ME.slipUntil = 0; ME.combo = 0; ME.sleepUntil = 0;
  G.spawnT = performance.now();
  endBall(); // a new life or round: no wrecking ball rolls on (the server ends it too)
  refillAmmo();
  if (G.pendingLoadout) applyLoadout(true);
  hud.dead(false);
  econSpawn(m);
});
net.on('ps', (m) => {
  spawnProj(m);
  if (m.k === 'bloodcross') { crossShot(m, G.projs.get(m.id)); return; } // a heartbeat, not a pew
  if (m.o !== G.myId) {
    const s = { chicken: 'squawk', duck: 'squeak', bowling: 'thunk', slipper: 'swing', soap: 'bloop', tennis: 'tennisFire' }[m.k] || 'pew';
    sfx[s](m.p);
  }
});
net.on('pu', (m) => {
  const pr = G.projs.get(m.id);
  if (pr && pr.k === 'slipper') return slipperUpdate(pr, m); // homing: steer between updates, ease corrections
  if (pr) { pr.p = m.p.slice(); pr.v = m.v.slice(); if (Number.isInteger(m.b)) pr.b = m.b; } // b: a tennis ball's bounces so far
});
net.on('pd', (m) => {
  const pr = G.projs.get(m.id);
  if (pr) {
    G.scene.remove(pr.mesh);
    G.projs.delete(m.id);
    if (pr.k === 'slipper' && pr.o === G.myId) onSlipperBack();
    if (pr.k === 'tennis') tennisEnd(pr, m);
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
net.on('court', courtSync); // scales of justice: everyone's kill streak when you join
net.on('hand', (m) => { G.hand = m.hand || []; });
net.on('tp', (m) => { ME.pos = m.p.slice(); fx.glitch(ME.pos, [0, 0, 0], 20); sfx.reverse(); });
net.on('heal', (m) => {
  if (m.id === G.myId) { ME.hp = m.hp; hud.msg(`+${m.a} HP`, 0.8); sfx.heal(); }
  const r = G.remotes.get(m.id);
  if (r) for (let i = 0; i < 12; i++) fx.burn([r.pos[0], r.pos[1], r.pos[2]]);
});
net.on('sleep', (m) => {
  const n = performance.now();
  if (n >= (ME.sleepUntil || 0)) ME.sleepAt = n; // a second arrow keeps you down longer, it doesn't knock you down again
  ME.sleepUntil = n + m.dur * 1000;
  releaseHook(); fireUp(); W.aimHeld = false; // knocked flat: let go of everything
  hud.msg('zzz...', m.dur, 'slip'); sfx.snore();
});
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
// Blood Cross: the X sticking to someone (or a wall), the spikes, the pop, the blood coming back on a kill
net.on('bcross', (m) => { recordEv(m); crossEvent(m); });
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
  if (gearFx(m)) return; // laser beams, photo teleports, goggle flashes (gear.js)
  if (secFx(m)) return; // taser zaps, remote pauses + rewinds, radar readings (secondaries.js)
  if (primFx(m)) return; // carts running people over; nail gun shots leave nails in walls (primaries.js)
  if (m.k === 'shot' || m.k === 'swing' || m.k === 'tbag' || m.k === 'shatter') recordEv(m);
  const r = G.remotes.get(m.id);
  if (m.k === 'shot') {
    const w = WEAPONS[m.w];
    if (!w) return;
    if (r && w.fanHammer) r.revShot(!!m.fan); // their revolver twirls too
    const fast = w.rate > 8;
    const mz = r ? r.muzzle(m.hd === 1) : null; // hd: the left gun of Lefty & Righty
    const color = () => tracerColor((G.skins.get(m.id) || {})[m.w], w.tracer || 0xfff0a0);
    if (w.water && secShot(m.s, mz)) { if (m.s.length) sfx.gun(m.w, m.s[0].slice(0, 3)); return; } // water pistol: a stream
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
    if (m.s.length) sfx.gun(m.w, m.s[0].slice(0, 3), remoteK(m.id, m.w)); // (a hot Belt Sander gets louder)
  } else if (m.k === 'shatter') {
    fx.spray(m.p, 70, [0xffffff, 0xbfe8ff, 0x7fd0ff], 11, 1.4, 0.2, 14, 0.5);
    sfx.crunch(m.p); sfx.ting(m.p);
    if (r) r.frozenUntil = 0;
  } else if (m.k === 'medkit') {
    const src = m.id === G.myId ? ME.pos : r ? r.pos : null;
    if (src) fx.spray([src[0], src[1] + 1.2, src[2]], 16, [0x7dff4f, 0xffffff], 3, 1.0, 0.14, -2, 1);
  } else if (m.k === 'bubhit') {
    fx.spray(m.p, 8, [0x4fd8ff, 0xffffff], 4, 0.3, 0.1, 0, 2); sfx.ricochet(m.p);
  } else if (m.k === 'cough') { // someone over-smoked the cigarette: they double over and smoke bursts out in front of them
    if (r) r.coughT = performance.now();
    const ok = (a) => Array.isArray(a) && a.length === 3 && a.every(Number.isFinite);
    if (ok(m.p) && ok(m.d)) { coughCloud(m.p, m.d); if (Math.hypot(m.p[0] - ME.pos[0], m.p[2] - ME.pos[2]) < 30) sfx.cough(); }
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
    if (m.w === 'popper') { // an item now: it pops into their hand for a moment
      if (r) { r.popItem('popper', 450); fx.confetti(r.itemMuzzle(), r.look(), r.vel); }
      sfx.popper(m.a); sfx.partyHorn(m.a);
    } else sfx.swing(m.a);
  } else if (m.k === 'reverse') {
    if (r) r.reverseUntil = performance.now() + m.dur * 1000;
    if (m.id === G.myId) { W.reverseUntil = performance.now() + m.dur * 1000; hud.msg('REVERSE', 1.2, 'reverse'); } // only once the server really started it
    if (m.id !== G.myId) sfx.reverse(r ? r.pos : null);
    if (r) { // they flash the card: a red + yellow burst everyone can see
      r.popItem('reverse', 700);
      const c = [r.pos[0], r.pos[1] + 1.3, r.pos[2]];
      fx.blast(c, 2.2, 0xff3b3b, 0xffd23b);
      fx.spray(c, 40, [0xff3b3b, 0xffd23b, 0xffffff], 10, 0.9, 0.2, 0, 2);
    }
  } else if (m.k === 'reflect') {
    if (m.by === G.myId) { hud.msg('REVERSED', 1.2, 'reverse'); sfx.reverse(); }
    if (m.id === G.myId) hud.msg('REVERSED THEM', 1.0, 'reverse');
    if (r) { fx.spray([r.pos[0], r.pos[1] + 1.3, r.pos[2]], 18, [0xff3b3b, 0xffd23b], 7, 0.5, 0.16, 0, 2); if (m.by !== G.myId) sfx.reverse(r.pos); }
  } else if (m.k === 'strike') {
    sfx.strike(m.p);
    if (m.n >= 2) hud.msg(m.n >= 3 ? 'STRIKE' : 'SPARE', 1.2, 'brag');
  } else if (m.k === 'slam' || m.k === 'ram') { // wrecking ball
    recordEv(m);
    wreckFx(m);
  } else if (m.k === 'thwack') {
    sfx.thwack(m.p);
  } else if (m.k === 'verdict') {
    recordEv(m); // killcams show the ruling too
    courtVerdict(m);
  }
});
net.on('chat', (m) => {
  if (!m.id) { hud.chat(null, null, m.m); return; }
  const [n, c] = nameOf(m.id);
  hud.chat(n, c, m.m);
});
net.on('po', (m) => { G.ping = Math.round(performance.now() - m.c); hud.ping(G.ping); });
// no-scope hype (cosmetic): badge for the shooter, feed icon, the MLG treatment for a long one, fireworks for a headshot
net.on('ns', (m) => {
  recordEv(m); // the killcam replays the fireworks
  const hold = noScope(m, nameOf(m.k), nameOf(m.v));
  if (hold && G.killcamPending && !RP.active) queueKillcam(m.k, 'sniper', hold); // got no-scoped from far: the overlay plays out first
});

initGear(); // the new gear's server messages + the G hook
initSec(); // the new secondaries + the speed trap (after initGear: it wraps the G hook)

// ------------------------------------------------------------ main loop
let last = performance.now(), acc = 0, sendT = 0, pingT = 0, fovNow = S.fov, fpsAcc = 0, fpsN = 0;
// your state for the server. Plant & Defuse also sends one right before every gun shot (weapons.js), so the server can
// check the shot against the aim it was really fired at
function sendSnap(now = performance.now()) {
  const r2 = (x) => Math.round(x * 100) / 100;
  const hp = hookPoint();
  net.send({
    t: 's', q: ME.seq, p: ME.pos.map(r2), v: ME.vel.map(r2), y: r2(G.spinning ? (now * 0.03) % (Math.PI * 2) : ME.yaw), x: r2(G.spinning ? Math.sin(now * 0.02) * 1.2 : ME.pitch), w: W.cur,
    g: hp ? hp.map(r2) : 0,
    f: W.flags | (G.brGlide ? FLAGS.GLIDE : 0) | (now < ME.slipUntil ? FLAGS.SLIP : 0) | (ME.sliding ? FLAGS.SLIDE : 0) | (ME.crouching ? FLAGS.CROUCH : 0) | (now < (ME.sleepUntil || 0) ? FLAGS.SLEEP : 0) | (ME.walking ? FLAGS.WALK : 0),
  });
}
W.sendSnap = () => { if (ME.alive && G.joined) sendSnap(); };
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
    const frozen = now < (ME.frozenUntil || 0) || now < (ME.quizUntil || 0) || secFrozen(now); // (pens down: no walking out of a pop quiz; tased, paused, jailed)
    if (frozen) { ME.vel[0] = 0; ME.vel[2] = 0; if (ME.hook) releaseHook(); }
    const playing = $('menu').classList.contains('hidden') && !chatOpen && now >= (ME.sleepUntil || 0) && !RP.active && !G.using && !frozen;
    const inp = playing ? {
      f: K.isDown('forward'), b: K.isDown('back'), l: K.isDown('left'), r: K.isDown('right'), jump: K.isDown('jump'), jumpPressed,
      sprint: K.isDown('sprint'),
      crouch: K.isDown('crouch'),
    } : {};
    jumpPressed = false;
    acc += dt;
    while (acc >= STEP) { stepPlayer(STEP, inp, now); carCollide(STEP); airTick(now); lavaStep(now); inp.jumpPressed = false; acc -= STEP; }
    grabStep(now); // held in a shredder's intake
    pinStep(now); // nailed to a wall
    oobTick(now); // out of the play area: RETURN TO THE MAP 3 2 1
    econFrame(dt); // Plant & Defuse: barriers, drops, armor on models, spectating
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
    lassoFrame(dt, now); // lasso: spin + throw, the rope you hold, your hands (before the snapshot: it sets a flag)
    if (ballOn(now)) { W.flags |= FLAGS.BALL; if (BS.snapNow) { BS.snapNow = false; sendT = 0; } } // wrecking ball (a slam dive goes out right away: the server checks it)

    sendT -= dt;
    if (sendT <= 0 && ME.alive) { sendT = 1 / 30; sendSnap(now); }
    pingT -= dt;
    if (pingT <= 0) { pingT = 2; net.send({ t: 'pi', c: performance.now() }); }
    if (!ME.alive) { if (G.killcamPending) $('deadTimer').textContent = epicKC ? 'killcam... too epic to skip' : `killcam... (${K.label('skip').toLowerCase()} to skip)`; else if (epicHold) epicTimer(now); else if (!econDead() && !brDead()) hud.deadTimer(Math.max(0, ((G.respawnMs ?? 2500) - (now - (G.deadAt || now))) / 1000)); }
  }

  const rt = now + G.offset - INTERP_MS;
  if (!RP.active) for (const r of G.remotes.values()) r.update(rt, dt, now);
  else for (const r of G.remotes.values()) { r.ch.root.visible = false; r.rope.visible = false; r.shadow.visible = false; } // the replay has its own copies
  updateTraffic(dt, now, RP.active);
  updateLore(dt, now); updateLoreFx(now); // (out of a match it clears them away)
  brFrame(dt, now); // jank royale: blimp, zone, loot, hud
  updateGibs(dt);
  updateKillFx(dt);
  updateCourt(dt, now);
  updateSprays(dt);
  updateShreds(dt);
  for (const [id, b] of G.bubbles) { if (now > b.until + 500) { G.scene.remove(b.mesh); G.bubbles.delete(id); continue; } b.mesh.rotation.y += dt * 0.3; b.mesh.material.opacity = 0.18 + Math.sin(now * 0.006) * 0.05; }
  updateWand(dt, now); // bubble wand: giant soap bubbles round people, the view from inside one, the wand in your hand
  updateGear(dt, now); // laser beams, photo frames, pop quizzes, night vision
  updateSec(dt, now); // soaks, zaps, pauses, rewinds, the radar gun, cages
  updatePrims(dt, now); // nails in walls, pins, shopping carts
  for (let i = G.smokes.length - 1; i >= 0; i--) {
    const s2 = G.smokes[i];
    if (now > s2.until) { G.smokes.splice(i, 1); continue; }
    for (let k = 0; k < 11; k++) { const a = Math.random() * 6.28, rr = Math.sqrt(Math.random()) * s2.r; fx.smoke([s2.p[0] + Math.cos(a) * rr, s2.p[1] + Math.random() * 3.5, s2.p[2] + Math.sin(a) * rr], 1, 0.4); }
  }
  // frost wears off one stack per frostDecay seconds, like on the server (which doesn't tell us)
  const frost = Math.max(0, (G.frost || 0) - Math.floor((now - (G.frostT || 0)) / (WEAPONS.snowball.frostDecay * 1000)));
  $('freezeFx').style.opacity = now < (ME.frozenUntil || 0) ? 1 : Math.min(0.6, frost * 0.15);
  if (G.joined) {
    updateObjectives(dt, now, G.round, ME.pos);
    updateGunGame(); updateInfection(dt);
    updateZombies(dt, now);
    const a = G.round && G.round.bomb && G.round.bomb.act;
    if (a && a.by === G.myId) hud.meter(a.f, `${a.k === 'plant' ? 'PLANTING' : 'DEFUSING'}... keep holding ${K.label('use')}`, '#ff4f4f');
  }
  updateChaos(dt, now);

  for (const pr of G.projs.values()) {
    if (pr.k === 'soap') { stepSoap(pr, dt, now); continue; } // bubble wand: wobbly bubbles on an exact path (wand.js)
    if (pr.k === 'tennis') { tennisStep(pr, dt); pr.mesh.visible = !RP.active; continue; } // counted bounces (primaries.js)
    if (pr.k === 'loop') { loopFrame(pr, dt, now); continue; } // a lasso loop in flight (lasso.js)
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
    if (age < 0) continue; // still a duck stuck on someone (duck.js)
    const k = Math.min(1, age / 0.3);
    h.mesh.scale.setScalar(k * (1 + Math.sin(age * 20) * 0.08) * (h.mesh.userData.big ? 4 : 1));
    h.mesh.userData.orbit.rotation.y += dt * 6;
    h.mesh.userData.ring.rotation.z += dt * 3;
    fx.vortex(h.p, WEAPONS.duck.holeR * (h.mesh.userData.big ? 1.6 : 0.6));
  }
  duckFrame(now, dt); // homing ducks, stuck ducks, holes riding their victim

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
  const asleep = G.joined && ME.alive && now < (ME.sleepUntil || 0);
  if (asleep) { // knocked flat: the view drops to the floor and rolls onto its side, breathes, then gets back up at the end
    const t = (now - (ME.sleepAt || now)) / 1000, left = (ME.sleepUntil - now) / 1000;
    const fall = Math.min(1, t / 0.45), up = Math.min(1, left / 0.4);
    const k = fall * fall * (up * up * (3 - 2 * up)); // falls like a plank, gets up quick
    cam.position.y += (ME.pos[1] + 0.32 - e[1]) * k;
    roll = (1.38 + Math.sin(now * 0.0021) * 0.05) * k + (fall < 1 ? Math.sin(fall * Math.PI) * 0.15 : 0);
    pOff = (Math.sin(now * 0.0021 + 1) * 0.035 - ME.pitch * 0.6) * k;
  }
  $('sleepFx').style.opacity = asleep ? 1 : 0;
  if (G.joined && !ME.alive) { pOff = -0.6; roll = 0.4; cam.position.y += Math.min(4, (now - (G.deadAt || now)) / 600); }
  if (G.joined && ME.alive && S.shake) roll += ME.lean || 0; // leaning into a grapple swing (eased in player.js)
  if (!G.joined) { // menu backdrop: slow orbit over the current map
    const a = now * 0.00005;
    cam.position.set(Math.sin(a) * 40, 18, Math.cos(a) * 40);
    ME.yaw = a; ME.pitch = -0.35;
    const mc = MAPS[G.cfg.map] && MAPS[G.cfg.map].menuCam; // sealed maps: orbit inside instead of over the roof
    if (mc) { cam.position.set(Math.sin(a) * mc[0], mc[1], Math.cos(a) * mc[0]); ME.pitch = mc[2]; }
    const tc = G.thumbCam; // tools/thumbs.cjs parks the camera here to photograph a map: [x, y, z, yaw, pitch]
    if (tc) { cam.position.set(tc[0], tc[1], tc[2]); ME.yaw = tc[3]; ME.pitch = tc[4]; }
  }

  G.shake = S.shake ? Math.max(0, G.shake - dt * 2.2) : 0;
  const sh = G.shake * G.shake * 0.08;
  const pu = G.punch || { x: 0, y: 0, z: 0 };
  cam.rotation.set(Math.max(-1.57, Math.min(1.57, ME.pitch + pOff + pu.x)) + (Math.random() - 0.5) * sh, ME.yaw + pu.y + (Math.random() - 0.5) * sh, roll + pu.z);
  if (!RP.active) ballCam(cam, dt); // wrecking ball: third person, behind and above the ball
  const hs = hspeed();
  const fovTarget = (S.fov + (S.fovKick ? Math.min(35, hs * 0.3) + (ME.sprinting ? 6 : 0) + (ME.alive ? ME.ropeFov || 0 : 0) : 0)) / (W.zoom || 1);
  fovNow += (fovTarget - fovNow) * Math.min(1, dt * (W.aim > 0 ? 14 : 6));
  if (Math.abs(cam.fov - fovNow) > 0.05) { cam.fov = fovNow; cam.updateProjectionMatrix(); }
  if (RP.active) updateReplay(dt, now, cam); // killcam / play of the round owns the camera
  const specCam = !RP.active && (spectateCam(dt, cam) || econCam(cam, dt) || brCam(dt, cam)); // one in the chamber: out of lives, watching someone; Plant & Defuse: a teammate; jank royale: the blimp ride + spectating
  cam.updateMatrixWorld();
  lassoLate(dt, now); // lasso ropes between people + from your hand, now that everyone (and the camera) has moved
  updateSpeedLines(dt, G.joined && ME.alive && !RP.active ? Math.hypot(ME.vel[0], ME.vel[1], ME.vel[2]) : 0, ME.vel, cam, ME.dashing ? 0.9 : 0, S.speedLines !== false);
  const rh = G.renderer.domElement.height;
  fx.setScale(rh / (2 * Math.tan((cam.fov * Math.PI) / 360)));
  vmScaleU.value = rh / (2 * Math.tan((G.vmCamera.fov * Math.PI) / 360));
  if (RP.active) { cam.getWorldDirection(tmpDir); setListener([cam.position.x, cam.position.y, cam.position.z], Math.atan2(-tmpDir.x, -tmpDir.z)); } else setListener(e, ME.yaw);

  const hp = hookPoint();
  if (hp && ME.alive && !RP.active) { myRope.visible = true; setRopeSkin(myRope, myGrapple()); setRope(myRope, muzzleWorld(), hp); } else myRope.visible = false;
  const shHit = G.joined ? raycast([ME.pos[0], ME.pos[1] + 0.1, ME.pos[2]], [0, -1, 0], 120, BOXES) : null;
  myShadow.visible = !!shHit && ME.alive && !ME.onGround && !RP.active;
  if (shHit) myShadow.position.set(ME.pos[0], shHit.point[1] + 0.03, ME.pos[2]);
  updateWreck(dt, now, RP.active, myShadow, myRope); // your own wrecking ball, its chain (instead of your rope), rumble + timer
  if (now < (G.burnUntil || 0)) fx.burn([ME.pos[0] + Math.sin(ME.yaw) * -0.8, ME.pos[1], ME.pos[2] - Math.cos(ME.yaw) * 0.8]);
  updateRig(dt, now, cam, RP.active); // overdrive rig: you in it (camera, HUD, trail) and its effects
  const revLeft = W.reverseUntil - now; // reverse card: red edges, blinking for the last second
  $('reverseFx').style.opacity = revLeft > 0 ? (revLeft > 1000 || Math.floor(revLeft / 150) % 2 ? 1 : 0.25) : 0;

  if (G.joined) {
    hud.hp(ME.hp);
    hud.speed(hs);
    hud.combo(ME.combo);
  }
  fpsAcc += dt; fpsN++;
  if (fpsAcc > 0.5) { $('fps').textContent = S.showFps ? Math.round(fpsN / fpsAcc) + ' fps' : ''; fpsAcc = 0; fpsN = 0; }
  hud.update(dt);
  updateNoScope(dt, cam, RP.active);
  fx.update(dt);
  G.skinFxWorld.update(dt);
  G.skinFxVM.update(dt);
  skinTick(dt, now);
  updateWorld(dt);
  updateCrosses(dt, RP.active ? (RP.sp || 1) * (RP.dt != null && dt > 0 ? RP.dt / dt : 1) : 1); // after the projectile loop + replay: it turns blood bolts nose-first
  G.vmScene.visible = G.joined && !RP.active && !specCam && !asleep && !econHideVM();
  if (ballOn(now)) G.vmScene.visible = false; // weapons are holstered inside the ball
  renderFrame();
  if ((screen === 'character' || (screen === 'main' && heroTick(dt))) && !$('menu').classList.contains('hidden')) renderPreview(heroDt || dt); // (grapple & spray has no weapon preview any more)
  if (screen === 'cosmetics' && !$('menu').classList.contains('hidden')) renderGrapplePreview(dt);
  if (screen === 'customize' && !$('menu').classList.contains('hidden')) { const d = czFrame(dt); if (d) renderPreview(d); } // on demand: only while it turns, you drag, or particles fly
}

// the home hero turns at 30 fps and rests once nobody has touched the page for a while (the browser stops it when hidden)
let heroAcc = 0, heroDt = 0, heroPoke = performance.now();
for (const t of ['pointermove', 'keydown', 'pointerdown']) addEventListener(t, () => { heroPoke = performance.now(); }, { passive: true });
function heroTick(dt) {
  heroAcc += dt;
  if (performance.now() - heroPoke > 20000 || heroAcc < 1 / 30) return false;
  heroDt = Math.min(heroAcc, 0.1); heroAcc = 0;
  return true;
}

// ------------------------------------------------------------ killstreaks
G.pocket = [];
// killstreak tray (bottom right): your 3 picks, the kills each needs, lit up when ready (press 5 / 6 / 7)
function renderStreak(n) {
  const tray = $('streakTray');
  const picks = activeStreaks();
  const key = picks.join(',') + '|' + n + '|' + G.pocket.join(',');
  if (tray.dataset.key !== key) {
    tray.dataset.key = key;
    tray.innerHTML = '';
    picks.forEach((id, i) => {
      const st = STREAKS[id], ready = G.pocket.includes(id);
      const d = document.createElement('div');
      d.className = 'kstreak' + (ready ? ' ready' : '');
      d.title = `${st.name}: ${K.hint(st.desc)}`;
      const im = document.createElement('img'); im.src = streakIcon(id); im.alt = '';
      const k = document.createElement('b'); k.textContent = K.label('streak' + (i + 1));
      const c = document.createElement('span'); c.textContent = ready ? 'READY' : `${Math.min(n, st.kills)}/${st.kills}`;
      d.append(im, k, c);
      tray.append(d);
    });
  }
  $('streak').textContent = n >= 2 ? `streak ${n}` : '';
}
function deployStreak(slot) {
  const id = activeStreaks()[slot];
  if (!G.joined || !ME.alive || !id) return;
  if (W.only) { hud.msg('no killstreaks in this mode (they keep for later)', 1.2); sfx.empty(); return; }
  if (chaosNoStreaks()) { hud.msg('no killstreaks in this mode', 1.2); sfx.empty(); return; }
  if (!G.pocket.includes(id)) { hud.msg(`${STREAKS[id].name}: ${STREAKS[id].kills} kills in a row`, 1.2); sfx.empty(); return; }
  if (rigClash(id, rigOn(), ballOn(performance.now()))) { hud.msg(id === 'overdrive' ? 'not inside the wrecking ball' : 'not in the overdrive rig (it keeps for later)', 1.2); sfx.empty(); return; }
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
    G.activeStreaks = validStreaks(S.loadout.streaks); // picks changed mid-streak count from now on (the server does the same)
    if ($('loNote').textContent === NEXT_NOTE) $('loNote').textContent = '';
    loseScythe();
    endBall();
    renderStreak(0);
    return;
  }
  if (m.earned) {
    const st = STREAKS[m.earned];
    if (!st) return;
    G.streakN = Math.max(G.streakN || 0, m.n - 1); // this arrives just before the 'kill' that counts it
    if (!G.pocket.includes(m.earned)) G.pocket.push(m.earned);
    const key = K.label('streak' + (1 + activeStreaks().indexOf(m.earned)));
    hud.msg(`${st.name.toUpperCase()} READY · PRESS ${key.toUpperCase()}`, 2.4, 'brag');
    sfx.kill();
    renderStreak(G.streakN);
    return;
  }
  // you activated one: switch it on here
  const st = STREAKS[m.reward];
  if (!st) return;
  if (m.reward === 'moonboots') ME.moonUntil = performance.now() + st.dur * 1000;
  if (m.reward === 'satellite') G.satUntil = performance.now() + st.dur * 1000;
  if (m.reward === 'spinbot') G.spinUntil = performance.now() + st.dur * 1000;
  if (m.reward === 'scythe') grantScythe();
  if (m.reward === 'wreckingball') startBall(m.dur || st.dur);
  toast(K.hint(st.desc), 2500);
});

// ------------------------------------------------------------ sprays (Z): paint your graffiti where you look
SYNC_KEYS.push('spray'); // your pick follows your account like the other settings
function mySpray() { return ownedSpray(S.spray, G.inv); }
function setSpray(id) { S.spray = id; saveSettings(); }
let sprayT = -1e9;
function spray() {
  if (!G.joined || !ME.alive || RP.active || ballOn()) return; // (no hands in the wrecking ball)
  const now = performance.now(), left = SPRAY.cd * 1000 - (now - sprayT);
  if (left > 0) { hud.msg(`spray ready in ${Math.ceil(left / 1000)}s`, 0.9); return; }
  const h = sprayAim(eye(), lookDir());
  if (!h) { hud.msg('nothing to spray on (get closer)', 0.9); return; }
  sprayT = now;
  const id = mySpray(), r3 = (x) => Math.round(x * 1000) / 1000;
  net.send({ t: 'spray', id, p: h.p.map(r3), n: h.n, y: r3(ME.yaw) }); // the server checks it and shows everyone
  sprayFx(h.p, h.n, id); // hiss right away, the paint shows up when the server says so
}
net.on('spray', (m) => addSpray(m, false));
// cosmetics screen: a little picture of each spray on a concrete square
function buildSprayUI() {
  const el = $('sk-spray');
  el.innerHTML = '';
  const cur = mySpray();
  for (const [k, v] of Object.entries(COSMETICS.spray)) {
    const have = owns(G.inv, 'spray', k);
    const c = document.createElement('button');
    c.className = 'chip' + (cur === k ? ' on' : '') + (have ? '' : ' locked');
    c.style.setProperty('--rc', RARITY[v.rarity].color);
    c.title = `${v.name} · ${RARITY[v.rarity].name}: ${v.desc}`;
    const im = document.createElement('img'); im.src = sprayIcon(k); im.alt = '';
    const t = document.createElement('span'); t.textContent = v.name;
    c.append(im, t);
    c.addEventListener('click', () => {
      if (!have) { toast(`${v.name} (${RARITY[v.rarity].name}): ${v.desc}. find it in boxes`, 3000); return; }
      setSpray(k); buildSprayUI(); toast(`spray: ${v.name}. press ${K.label('spray')} in a match`);
    });
    el.append(c);
  }
}

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
function myKfx() { return S.kfx === 'random' ? 'random' : ownedKill(S.kfx || 'none', G.inv); } // random: the server rolls one per life
function setKfx(id) {
  S.kfx = id;
  saveSettings();
  if (G.joined) net.send({ t: 'kfx', id });
  if (screen === 'character') buildCharacterUI();
}
net.on('cd', (m) => { const n = G.names.get(m.id); if (n) n.card = m.card || ''; });
function infoOf(id) {
  if (id === G.myId) return { name: G.myName, color: G.myColor, skins: G.equipped, look: validLook(S.look, myAchs()), bot: false, grap: myGrapple(), team: G.myTeam || 0, kat: W.kat || 0 };
  const n = G.names.get(id) || {};
  return { name: n.name || '???', color: n.color || '#ffffff', skins: G.skins.get(id) || {}, look: n.look || null, bot: !!n.bot, level: n.level, grap: n.grap, team: n.team || 0, kat: G.kat.get(id) || 0 };
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
  epicUI(false);
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
  if (k.ep && k.k) { const sp = document.createElement('span'); sp.textContent = `  EPIC ${Math.round(k.ep.d)}m`; sp.style.color = '#ffe14d'; d.append(sp); if (k.k === RP.focus) epicBanner({ ...k.ep, w: via }); }
  $('rpFeed').append(d);
}
let killcamT = 0;
function queueKillcam(killer, via, delay = 900) {
  clearTimeout(killcamT);
  const deathS = serverNow();
  G.killcamPending = true;
  killcamT = setTimeout(() => {
    if (ME.alive || !G.joined || RP.active) { G.killcamPending = false; return; }
    if (epicKC) { epicCam(killer, via, deathS, delay); return; } // (a long no-scope: after the MLG overlay)
    const clip = localClip(deathS - 4500, deathS + 1200, infoOf);
    infClipInfo(clip.info);
    const [kn, kc] = nameOf(killer);
    showReplayUI('KILLCAM', cardUrlFor(killer), kn, kc, `got you with ${wname(via)}`, `${K.label('skip').toUpperCase()} / CLICK to skip`);
    $('dead').classList.add('hidden');
    playClip(clip, {
      focus: killer, mode: 'killcam', slow: [[deathS - 380, deathS + 220]], end: deathS + 1000,
      onKill: (k) => replayFeed(k, clip.info),
      onEnd: () => { G.killcamPending = false; hideReplayUI(); if (!ME.alive) $('dead').classList.remove('hidden'); net.send({ t: 'respawn' }); },
      onAbort: () => { G.killcamPending = false; hideReplayUI(); },
    });
  }, delay);
}
function endKillcam() {
  clearTimeout(killcamT);
  G.killcamPending = false;
  epicKC = null; epicHold = false; epicExtra = 0;
  if (RP.mode === 'killcam') stopReplay(true);
}
function skipReplay() {
  if (epicLocked()) { epicNope(); return; }
  if (RP.active && RP.mode === 'hl') return; // the play of the round can't be skipped: everyone watches it (it still ends when the next match starts)
  if (RP.active) { stopReplay(false); return; }
  if (G.killcamPending) { clearTimeout(killcamT); G.killcamPending = false; net.send({ t: 'respawn' }); }
}

// ------------------------------------------------------------ EPIC kills: too epic to skip
// the server flags far / clutch / mid-air / no-scope kills as EPIC (shared/epic.js) and holds the victim's respawn until the
// whole epic killcam has played, so a hacked client can't skip it either. here: a longer, slower cut that punches in on you,
// a banner when the shot lands, and a padlock where the skip button was.
let epicKC = null; // the epic kill you're stuck watching
let epicHold = false, nopeT = 0; // the server is holding your respawn (until 'spawn')
let epicExtra = 0; // ms the epic killcam started later than usual (no-scope MLG overlay first)
function epicLocked() { return !!epicKC && !ME.alive && !G.roundOver && (G.killcamPending || RP.mode === 'killcam'); }
function epicTags(ep) {
  const w = WEAPONS[ep.w];
  const far = w && w.kind === 'melee' ? 'WHAT A REACH' : w && epicMul(ep.w) >= 2 ? `WITH A ${w.name.toUpperCase()}?!` : 'LONG SHOT';
  const T = { far, hs: 'HEADSHOT', ns: 'NO-SCOPE', air: 'MID-AIR', rope: 'OFF THE GRAPPLE', fast: `${ep.kmh || 300} KM/H`, hp: `ON ${ep.hp || 1} HP` };
  return (Array.isArray(ep.why) ? ep.why : []).map((k) => T[k]).filter(Boolean).join(' · ');
}
function epicCam(killer, via, deathS, delay = EPIC_CAM.delay) {
  const ep = epicKC, C = EPIC_CAM;
  // started late (a slow PC hitching on the kill): cut into the lead-up so it still ends before the server lets you go.
  // a long no-scope holds the killcam back for the MLG overlay on purpose (delay), and the server's lock waits that out too
  epicExtra = Math.max(0, delay - C.delay);
  const late = Math.max(0, Math.min(C.pre - 1000, performance.now() - (G.deadAt || 0) - delay));
  const clip = localClip(deathS - C.pre + late, deathS + 1200, infoOf);
  const [kn, kc] = nameOf(killer);
  showReplayUI('KILLCAM', cardUrlFor(killer), kn, kc, `got you with ${wname(via)}`, '');
  epicUI(true);
  $('dead').classList.add('hidden');
  const done = () => { epicKC = null; G.killcamPending = false; hideReplayUI(); epicUI(false); };
  playClip(clip, {
    focus: killer, mode: 'killcam', victim: G.myId, zoom: Math.max(2, Math.min(5, (ep.d || 30) / 14)),
    slow: C.slow.map(([a, b, r]) => [deathS + a, deathS + b, r]), end: deathS + C.post,
    // swing onto you as it slows down, hold through the hit, ease off after
    punch: (t) => { const r = t - deathS; return r < -650 ? 0 : r < -150 ? (r + 650) / 500 : r < 450 ? 1 : 1 - (r - 450) / 700; },
    onKill: (k) => replayFeed(k, clip.info),
    onEnd: () => { done(); if (!ME.alive) $('dead').classList.remove('hidden'); net.send({ t: 'respawn' }); },
    onAbort: done,
  });
}
// the skip prompt turns into a padlock (off again for every other replay)
function epicUI(on) {
  const h = $('rpHint');
  h.classList.toggle('locked', on);
  h.classList.remove('nope');
  $('replay').classList.toggle('epic', on);
  const b = $('rpEpic');
  if (b) b.remove();
  if (!on) return;
  const lk = document.createElement('span');
  lk.className = 'lock';
  h.textContent = '';
  h.append(lk, 'TOO EPIC TO SKIP');
}
// the clip ended (or was too short to play) but the server still holds you: count down to the end of the lock
function epicTimer(now) { $('deadTimer').textContent = `too epic to skip · ${Math.max(0, (epicCamMs() + epicExtra - (now - (G.deadAt || now))) / 1000).toFixed(1)}...`; }
// trying to skip anyway: the padlock rattles (at most every 300 ms: holding space auto-repeats)
function epicNope() {
  const tn = performance.now();
  if (tn - nopeT < 300) return;
  nopeT = tn;
  const el = RP.active ? $('rpHint') : $('deadTimer');
  el.classList.remove('nope'); void el.offsetWidth; el.classList.add('nope');
  el.addEventListener('animationend', () => el.classList.remove('nope'), { once: true });
  sfx.error();
}
// EPIC SHOT · 64m slams in when the shot lands (killcam and play of the round)
function epicBanner(ep) {
  const old = $('rpEpic');
  if (old) old.remove();
  const b = document.createElement('div'), t = document.createElement('div'), s = document.createElement('div');
  b.id = 'rpEpic'; t.className = 'et'; s.className = 'es';
  t.textContent = `EPIC SHOT · ${Math.round(ep.d)}m`;
  s.textContent = epicTags(ep);
  b.append(t, s);
  $('replay').append(b);
  sfx.choir();
}
// and the killer gets to brag about it
function epicBrag(ep) {
  hud.msg(ep.lock ? `UNSKIPPABLE:\nthey HAVE to watch this · ${Math.round(ep.d)}m` : `EPIC SHOT · ${Math.round(ep.d)}m\n${epicTags(ep)}`, 3.2, 'epicbrag');
  sfx.choir();
}

// ------------------------------------------------------------ accounts
function totalRolls(me) { const r = (me && me.rolls) || {}; return (r.crate || 0) + (r.bag || 0) + (r.box || 0); }
function fmtTime(sec) { const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60); return h ? `${h}h ${m}m` : `${m}m`; }
function renderAcctBar() {
  const tr0 = account.loggedIn ? totalRolls(account.me) : 0;
  $('cratesLbl').textContent = tr0 ? `CONTAINERS (${tr0})` : 'CONTAINERS'; // the label only: the button keeps its slab
  $('cratesBtn').classList.toggle('glow', tr0 > 0);
  const bar = $('acctBar');
  bar.innerHTML = '';
  const span = (t, cls) => { const e = document.createElement('span'); e.textContent = t; if (cls) e.className = cls; return e; };
  const btn = (t, fn) => { const b = document.createElement('button'); b.textContent = t; b.addEventListener('click', fn); return b; };
  if (account.loggedIn) {
    const me = account.me;
    const tr = totalRolls(me);
    bar.append(span(`Lv ${me.level}`, 'lv'), span(me.name), span(`${tr} to open`, 'rolls'),
      btn('PROFILE', () => show('profile'))); // log out lives on the profile page
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
    if (typeof prof.grap === 'string') G.settings.grap = prof.grap;
    if (prof.favs && typeof prof.favs === 'object') G.settings.favs = prof.favs;
    if (prof.wk && typeof prof.wk === 'object') G.settings.wk = prof.wk;
    Object.assign(G.settings, prof.settings || {});
    try { localStorage.setItem('jankfire', JSON.stringify(G.settings)); } catch { /* fine */ }
    applySettingsToUI();
  } else saveSettings();
  G.inv = achInv(me.inv, me.achs); // achievement rewards you've earned count as owned
  if (G.joined) { net.send({ t: 'kfx', id: myKfx() }); net.send({ t: 'grap', id: myGrapple() }); } // the profile may have brought other picks: tell the server
  recomputeEquipped();
  rebuildOne();
  if (!fresh && prof.loadout) { applyLoadout(false); applyStreaks(); } // the account's own loadout, by the respawn rule
  renderAcctBar();
  czRefresh();
}
function doLogout() {
  logout();
  G.inv = {};
  recomputeEquipped();
  rebuildOne(); // only the skins changed
  renderAcctBar();
  show('main');
  toast('logged out. locked cosmetics are hidden until you log back in.');
}
$('logoutBtn').addEventListener('click', doLogout);
// the customize screen (customize.js) borrows the locker's own save / equip helpers
initCustomize({
  setSkin, storeSkin, setPartAll, skinnable, itemModel, setKfx, myKfx, myAchs, toast, show,
  equip: (slot, id) => { S.loadout[slot] = id; G.cosSel = id; saveSettings(); applyLoadout(false); },
  setItem: (id) => { S.loadout.item = id; saveSettings(); applyLoadout(false); },
  setStreaks: (list) => { S.loadout.streaks = validStreaks(list); saveSettings(); applyStreaks(); },
  loNote: () => $('loNote').textContent,
  bulk: () => { saveSettings(); recomputeEquipped(); sendSkins(); rebuildOne(); },
  save: () => saveSettings(), sendSkins: () => sendSkins(), recompute: () => recomputeEquipped(),
  classic: () => { classicLocker = true; show('cosmetics'); },
});
// the same hub on the outfit screen and on grapple & spray
$('scr-character').prepend(hubTabs('character', show, () => { classicLocker = true; show('cosmetics'); }));
$('scr-cosmetics').prepend(hubTabs('grapple', show, () => { classicLocker = true; show('cosmetics'); }));
function applySettingsToUI() {
  $('jank').value = String(S.jank); setJank(S.jank);
  $('shadows').value = S.shadows || 'auto'; setShadowPref(S.shadows);
  for (const id of ['fov', 'vol', 'sens', 'adsSens']) { $(id).value = String(S[id]); $(id).dispatchEvent(new Event('input')); }
  for (const id of ['fovKick', 'shake', 'showFps', 'toggleAim', 'blood', 'killcam', 'showCards', 'speedLines']) $(id).checked = !!S[id];
  K.attach(S); // the profile may have brought its own key bindings
  setVolume(S.vol);
  $('musicVol').value = String(S.musicVol); $('musicMatchVol').value = String(S.musicMatchVol);
  $('musicMatch').checked = S.musicMatch !== false; $('musicComp').checked = !!S.musicComp; musicUpdate();
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
  const myInv = achInv(me.inv, me.achs); // achievement rewards you've earned count as owned
  const owned = LOOT_TYPES.reduce((a, ty) => a + Object.keys(COSMETICS[ty]).filter((id) => owns(myInv, ty, id)).length, 0);
  const total = LOOT_TYPES.reduce((a, ty) => a + Object.keys(COSMETICS[ty]).length, 0);
  const rows = [
    ['wins', st.wins], ['kills', st.kills], ['deaths', st.deaths], ['k/d', st.deaths ? (st.kills / st.deaths).toFixed(2) : st.kills],
    ['bot kills', st.bot_kills], ['best coop wave', st.best_wave], ['top speed', `${st.top_speed} km/h`], ['played', fmtTime(st.playtime)],
    ['never landed', `${st.airborne || 0}x`],
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
    const own = c.types.reduce((a, t) => a + Object.keys(COSMETICS[t]).filter((id) => !COSMETICS[t][id].ach && owns(G.inv, t, id)).length, 0);
    const all = c.types.reduce((a, t) => a + Object.keys(COSMETICS[t]).filter((id) => !COSMETICS[t][id].ach).length, 0); // achievement rewards aren't in containers
    const card = document.createElement('div'); card.className = 'cratecard' + (n > 0 ? ' has' : '');
    const im = document.createElement('img'); im.src = containerPic(kind) || containerArt(kind); im.alt = ''; // rendered from the 3D one
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
  for (const t of types) for (const [id, c] of Object.entries(COSMETICS[t])) if (c.rarity !== 'free' && !c.ach) pool.push({ type: t, id, name: c.name, rarity: c.rarity });
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
  playContainer($('roll3d'), kind, item ? RARITY[item.rarity].color : '#ffffff', 4.6, (S.jank | 0) === 0 ? 0.35 : (S.jank | 0) === 1 ? 0.6 : 1); // it rattles while the strip spins, bursts on the reveal
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
    G.inv = achInv(account.me.inv, account.me.achs);
    recomputeEquipped();
    renderAcctBar();
    const res = $('rollResult');
    const btn = (t, fn) => { const b = document.createElement('button'); b.className = 'mid'; b.textContent = t; b.addEventListener('click', fn); $('rollBtns').append(b); };
    if (item) {
      const big = document.createElement('span'); big.className = 'big'; big.textContent = item.name; big.style.color = item.color;
      const sub = document.createElement('span'); sub.textContent = `${item.rarityName} ${TYPE_NAMES[item.type].toLowerCase()} unlocked`;
      res.append(big, sub);
      if (item.rarity === 'legendary' || item.rarity === 'epic') sfx.kill(); else sfx.ting();
      if (item.type === 'spray') {
        const im = document.createElement('img'); im.className = 'sprayPic'; im.src = sprayIcon(item.id); im.alt = ''; res.append(im);
        btn('EQUIP SPRAY', () => { setSpray(item.id); closeRoll(); toast(`spray: ${item.name}. press ${K.label('spray')} in a match`); });
      } else if (item.type === 'kill') {
        btn('EQUIP KILL EFFECT', () => { setKfx(item.id); closeRoll(); toast(`kill effect: ${item.name}`); });
      } else if (item.type === 'grapple') {
        btn('EQUIP GRAPPLE', () => { setGrap(item.id); closeRoll(); toast(`grapple: ${item.name}`); });
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
function closeRoll() { $('rollbox').classList.add('hidden'); stopContainer(); if (screen === 'cosmetics') buildCosmeticsUI(); czRefresh(); if (screen === 'crates') renderCrates(); renderAcctBar(); }

// ------------------------------------------------------------ rounds
function fmtClock(ms) { const s2 = Math.ceil(ms / 1000); return `${Math.floor(s2 / 60)}:${String(s2 % 60).padStart(2, '0')}`; }
function renderRound(r) {
  const el = $('round');
  if (!r) { el.textContent = ''; return; }
  if (r.warm) { el.textContent = 'warm-up · nothing counts'; return; } // a mode lobby: its own big countdown box
  const mt = zmRoundText(r) ?? ggRoundText(r) ?? infRoundText(r); // zombies: zombies left / the break. gun game / infection: just the clock, their bars show the rest
  if (mt != null) { el.textContent = mt; return; }
  const teamGame = r.game && GAMES[r.game] && GAMES[r.game].teams;
  el.textContent = r.over ? `next round in ${Math.ceil(r.left / 1000)}` : teamGame ? '' : `first to ${r.target} · ${fmtClock(r.left)}`;
  const ct = chaosRoundText(r);
  if (ct) el.textContent = ct;
  if (r.game === 'br' && !r.over) el.textContent = 'last one standing wins'; // jank royale: the zone clock is in its own panel
}
net.on('lobby', (m) => lobbyInfo(m)); // the countdown / who's ready / end: the match is on
net.on('round', (m) => {
  const box = $('roundEnd');
  if (m.start) {
    courtReset(); // scales of justice: a new match, a clean record (the server does the same)
    if (m.game) G.game = m.game;
    musicNewMatch(true); // (straight after joining, it's the same match: the song stays)
    G.roundOver = false; if (RP.mode === 'hl') stopReplay(true); box.classList.add('hidden'); G.vote = null;
    esClose(G.joined && document.pointerLockElement !== canvas); // back in: click to grab the mouse again
    if (m.game) { G.round = { ...(G.round || {}), ...m }; updateLabel(); if (screen === 'match') syncMatchUI(); }
    if (m.warm) { hud.msg('WARM-UP', 1.8, 'brag'); hud.chat(null, null, `lobby: run around, nothing counts. ${K.label('ready')} = ready`); chaosRoundStart(m.game); return; } // a mode lobby's warm-up
    hud.msg(m.game && m.game !== 'dm' && GAMES[m.game] ? GAMES[m.game].name.toUpperCase() : 'ROUND START', 1.8, 'brag');
    if (m.game && GAMES[m.game]) hud.chat(null, null, K.hint(GAMES[m.game].desc));
    chaosRoundStart(m.game);
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
  const it = infRoundTitle(m); // infection: survivors or the infected
  if (it) { h.textContent = it[0]; h.style.color = it[1]; }
  box.append(h);
  for (const [id, name, k, d, team] of m.top) {
    const row = document.createElement('div');
    row.textContent = `${name}  ·  ${k} / ${d}`;
    const note = ggRowNote(id, m) || infRowNote(id, m);
    if (note) row.textContent += `  ·  ${note}`;
    if (team && TEAMS[team]) row.style.color = TEAMS[team].color;
    if (id === G.myId) row.style.color = '#ffe14d';
    box.append(row);
  }
  brRoundEnd(m, box); // jank royale: placements (the old box; the end screen gets them too)
  esRound(m); // the end screen replaces the old round box (still built above for anything that reads it)
});
// play of the round: the server picked the best moment and sent the recording
net.on('hl', (m) => {
  if (!G.joined || !m.clip) return;
  if (RP.mode === 'killcam' || G.killcamPending) skipReplay();
  const box = $('roundEnd');
  box.classList.add('hidden');
  const url = m.id === G.myId ? cardUrlFor(G.myId) : (S.showCards !== false && m.card) || defaultCard(m.name, m.color);
  esMini(true); // the end screen steps aside to a vote rail while the clip plays
  showReplayUI('PLAY OF THE ROUND', url, m.name, m.color, m.label, 'no skipping. witness greatness'); // unskippable; the round end and vote come after it
  const slow = (m.clip.ev || []).filter((e) => e.m && e.m.t === 'kill' && e.m.k === m.id).map((e) => [e.s - 260, e.s + 220]);
  playClip(m.clip, {
    focus: m.id, mode: 'hl', slow,
    onKill: (k) => replayFeed(k, m.clip.info),
    onEnd: () => { hideReplayUI(); esMini(false); },
    onAbort: () => { hideReplayUI(); esMini(false); },
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
  esRoll(m);
  if (!esActive()) toast(d.textContent, 3500);
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
  $('dFull').addEventListener('click', async () => {
    if (!window.jf.display) { window.jf.fullscreen(); return; }
    await syncDisplay();
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

// PATCH NOTES: a NEW badge on the menu link until you've read the latest entry
if (patchUnseen()) $('pnNew').classList.remove('hidden');
