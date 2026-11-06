// The weapon customize screen (it replaces the old COSMETICS list; that one is still one click away for grapples and
// sprays). Centre: your weapon, big, turning slowly over the blurred map, drag to spin it. Left: your card and every
// weapon by slot. Right: what it is, kills with it, its numbers and yours. Bottom: round tabs (Leave, Skin, Wrap, Charm,
// Effect, Finisher); a tab opens a strip of tiles: None, Random, then everything, coloured by rarity, hearts for
// favourites, a search box. Hover a tile to try it on. Random = something you own, rolled again every spawn (the
// server rolls it, server/randskin.js); "only favourites" makes Random pick from your hearts.
// The 3D view renders on demand: while it turns, while you drag or hover, then it rests.
import { G } from './ctx.js';
import { WEAPONS, ORDER, SLOTS, ITEMS, ITEM_ORDER, STREAKS, validStreaks } from '/shared/weapons.js';
import { streakIcon } from './icons.js';
import { hubTabs } from './hub.js';
import { COSMETICS, RARITY, CONTAINERS, owns, ownedSkin, modelsFor } from '/shared/cosmetics.js';
import { ACHIEVEMENTS, achProgress, ROYAL_ALL } from '/shared/looks.js';
import { validSkin, DEFAULT_SKIN, WRAP_MODES, WRAP_MODE_NAMES, makeHat } from './skins.js';
import { showPreview, resizePreview, setPreviewRes, previewManual } from './preview.js';
import { weaponIcon, objIcon, drawIcon, isPlaceholder, PLACEHOLDER, studioIcon, liveIcon } from './icons.js';
import { uiPic, itemPic } from './itemicons.js';
import { whenGlb, prefetch, want } from './glbkit.js';
import { defaultCard } from './cards.js';
import { royalBoxes } from './royal.js';
import { organic } from './organic.js';
import { account } from './account.js';
import { K } from './keys.js';
import { zlMount, zlRender } from './zmloadout.js'; // QUICK PLAY / ZOMBIES loadout tabs

export const RAND = 'random';
const $ = (id) => document.getElementById(id);
const S = G.settings;
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const pickOne = (a) => a[Math.floor(Math.random() * a.length)];
const SLOT_T = ['finish', 'hat', 'effect', 'model'];
const TABS = [
  { id: 'leave', name: 'Leave', ico: '🚪' },
  { id: 'skin', name: 'Skin', ico: '🔧', type: 'model', idx: 3, none: 'default' },
  { id: 'wrap', name: 'Wrap', ico: '🎨', type: 'finish', idx: 0, none: 'default' },
  { id: 'charm', name: 'Charm', ico: '🎩', type: 'hat', idx: 1, none: 'none' },
  { id: 'effect', name: 'Effect', ico: '✨', type: 'effect', idx: 2, none: 'none' },
  { id: 'finisher', name: 'Finisher', ico: '💀', type: 'kill', none: 'none', global: true },
];
// the round buttons' props, from the icon studio: a door, a spanner, a palette, the top hat off the charm rack, a crystal, a skull
const TAB_PIC = {
  leave: () => uiPic('ui_door', '#ffe14d', 44), skin: () => uiPic('ui_wrench', '#ff4fd8', 44), wrap: () => uiPic('ui_palette', '#4fd8ff', 44),
  charm: () => studioIcon('cztab:charm', () => makeHat('tophat'), { w: 44, h: 44, accent: '#ff4fd8', pitch: 0.3 }),
  effect: () => uiPic('ui_crystal', '#ffe14d', 44), finisher: () => uiPic('ui_skull', '#ff3030', 44),
};
const TYPE_LABEL = { model: 'Skin', finish: 'Wrap', hat: 'Charm', effect: 'Effect', kill: 'Finisher' };
const FX_ICO = { smoke: '💨', bubbles: '🫧', sparkles: '✨', music: '🎵', hearts: '💖', electric: '⚡', flames: '🔥', money: '💸', rainbow: '🌈' };
const KILL_ICO = { none: '🦴', confetti: '🎉', grave: '🪦', cash: '💵', pixel: '👾', balloon: '🎈', chicken: '🐔', bsod: '💻', yeet: '🚀', ascend: '🛸', duck: '🦆', blastzone: '💥' };
const KIND = { hitscan: 'gun', proj: 'launcher', cone: 'spray', melee: 'melee', reverse: 'card' };
const RAR_ORDER = ['free', 'common', 'rare', 'epic', 'legendary'];
const BASE_TIP = {
  finish: 'a paint job. pick where it goes: normal, reverse or full.',
  hat: 'sits on the gun. does nothing. very important.',
  effect: 'stuff that comes off the gun while you hold it.',
};
let api = null, root = null, open = false, sel = null, tab = null, copyAll = false;
const F = { q: '', r: 'all' };
const V = { yaw: 0.5, pitch: 0.12, dist: 3.0 }; // the 3D view (preview.js manual mode)
let drag = null, lastAct = 0, dirty = 0, acc = 0, spinHold = 0;

// ------------------------------------------------------------ random slots + favourites (main.js uses these too)
G.rolled = G.rolled || {}; // what the server rolled for your random slots this life
const localRoll = {}; // menu-only rolls (not in a match): kept steady until you pick Random again
export function myFavs() { const f = S.favs; return f && typeof f === 'object' ? f : { only: [] }; }
const favList = (t) => (Array.isArray(myFavs()[t]) ? myFavs()[t] : []);
const favOnly = (t) => Array.isArray(myFavs().only) && myFavs().only.includes(t);
// what Random can land on: owned, this weapon's skins, your hearts if that's ticked (none owned: everything owned)
function pool(type, weapon) {
  let ids = Object.keys(COSMETICS[type]).filter((k) => owns(G.inv, type, k) && (type !== 'model' || k === 'default' || COSMETICS.model[k].weapon === weapon));
  if (favOnly(type)) { const f = ids.filter((k) => favList(type).includes(k)); if (f.length) ids = f; }
  return ids;
}
export function resolveRand(sk, id) {
  if (!Array.isArray(sk) || !sk.includes(RAND)) return sk;
  const r = G.joined ? G.rolled[id] : null;
  return sk.map((v, i) => {
    if (i > 3 || v !== RAND) return v;
    if (r && typeof r[i] === 'string') return r[i];
    const key = id + i;
    if (!localRoll[key] || !pool(SLOT_T[i], id).includes(localRoll[key])) localRoll[key] = pickOne(pool(SLOT_T[i], id)) || (i === 0 || i === 3 ? 'default' : 'none');
    return localRoll[key];
  });
}
// what goes to the server: your picks, owned-checked, with the random slots left as 'random'
export function wantSkins() {
  const out = {};
  for (const [id, sk] of Object.entries(S.skins || {})) {
    if (!Array.isArray(sk)) continue;
    const o = ownedSkin(sk, G.inv, id);
    for (let i = 0; i < 4; i++) if (sk[i] === RAND) o[i] = RAND;
    if (o[0] !== 'default' || o[1] !== 'none' || o[2] !== 'none' || o[3] !== 'default' || o[4] !== 'normal') out[id] = o;
  }
  if (out.scythe) out.scythe_rifle = out.scythe.slice(0, 3).concat('default', out.scythe[4]); // both forms look the same
  return out;
}
export function czRolled(s) { G.rolled = s && typeof s === 'object' ? s : {}; if (open) { dirty = 2; refresh(); } }
// kills with each weapon (this device + your account profile): the mastery bar
let wkT = null;
export function czKill(w) {
  if (typeof w !== 'string' || !Object.hasOwn(WEAPONS, w)) return;
  if (!S.wk || typeof S.wk !== 'object') S.wk = {};
  S.wk[w] = (S.wk[w] | 0) + 1;
  clearTimeout(wkT); wkT = setTimeout(() => api && api.save(), 3000);
}

// ------------------------------------------------------------ build
export function initCustomize(a) {
  api = a;
  root = $('scr-customize');
  root.innerHTML = `
    <div class="cz-blur"></div><div class="cz-glow" id="czGlow"></div>
    <div class="cz-stage" id="czStage"></div>
    <div class="cz-hover hidden" id="czHover"><b></b><i></i><span></span><div class="req"></div></div>
    <aside class="cz-left"><div class="cz-career" id="czCareer"></div><div class="cz-list" id="czList"></div></aside>
    <aside class="cz-right"><div class="cz-info" id="czInfo"></div><div class="cz-acts" id="czActs"></div></aside>
    <div class="cz-hub" id="czHub"></div>
    <div class="cz-bottom"><div class="cz-lo" id="czLo"></div><div class="cz-strip hidden" id="czStrip"><div class="cz-bar" id="czBar"></div><div class="cz-tiles" id="czTiles"></div></div>
      <nav class="cz-tabs" id="czTabs"></nav></div>
    <div class="cz-dragme" id="czDrag">drag to spin</div>`;
  for (const t of TABS) {
    const b = el('button', 'cz-tab' + (t.id === 'leave' ? ' leave' : ''));
    b.dataset.tab = t.id;
    const ico = el('span', 'ico', t.ico);
    b.append(ico, el('span', 'lbl', t.name.toUpperCase()));
    requestAnimationFrame(() => { const im = el('img'); im.alt = ''; if (liveIcon(im, TAB_PIC[t.id])) { ico.textContent = ''; ico.append(im); } }); // its 3D prop (the emoji stays if 3D can't draw)
    b.addEventListener('click', () => {
      if (t.id === 'leave') { api.show(G.joined ? 'pause' : 'main'); return; }
      setTab(tab === t.id ? null : t.id);
    });
    $('czTabs').append(b);
  }
  buildBar();
  $('czHub').append(hubTabs(() => (mode === 'loadout' ? 'loadout' : 'weapons'), api.show, api.classic));
  // drag to spin; wheel to zoom a little
  const st = $('czStage');
  st.addEventListener('pointerdown', (e) => { drag = { x: e.clientX, y: e.clientY }; st.setPointerCapture(e.pointerId); poke(); $('czDrag').classList.add('gone'); });
  st.addEventListener('pointermove', (e) => {
    if (!drag) return;
    V.yaw += (e.clientX - drag.x) * 0.012; V.pitch = Math.max(-0.6, Math.min(0.7, V.pitch + (e.clientY - drag.y) * 0.006));
    drag.x = e.clientX; drag.y = e.clientY; poke();
  });
  const up = () => { drag = null; spinHold = performance.now() + 1800; };
  st.addEventListener('pointerup', up); st.addEventListener('pointercancel', up);
  st.addEventListener('wheel', (e) => { V.dist = Math.max(2.1, Math.min(4.2, V.dist + Math.sign(e.deltaY) * 0.2)); previewManual(V); poke(); }, { passive: true });
  root.addEventListener('pointermove', () => { lastAct = performance.now(); });
  // wheel over the tile strip scrolls it sideways
  $('czTiles').addEventListener('wheel', (e) => { const t = $('czTiles'); if (Math.abs(e.deltaY) > Math.abs(e.deltaX) && t.scrollWidth > t.clientWidth) { t.scrollLeft += e.deltaY; e.preventDefault(); } }, { passive: false });
  addEventListener('resize', () => { if (open) { resizePreview(); dirty = 2; } });
}
const poke = () => { lastAct = performance.now(); dirty = Math.max(dirty, 1); };
// two faces of one screen: LOADOUT (what you take into a match) and WEAPONS (what it looks like)
let mode = 'weapons';
export function czMode(m) { mode = m === 'loadout' ? 'loadout' : 'weapons'; if (mode === 'loadout') tab = null; }

export function czOpen() {
  if (!root) return;
  const first = !open;
  open = true;
  if (first) { copyAll = false; tab = null; F.q = ''; }
  if (!sel || !api.skinnable().includes(sel)) sel = G.cosSel && api.skinnable().includes(G.cosSel) ? G.cosSel : S.loadout.primary;
  root.classList.toggle('potato', (S.jank | 0) === 0);
  root.classList.toggle('lo-mode', mode === 'loadout');
  zlMount(root, () => refresh());
  for (const b of root.querySelectorAll('.hub-tab')) b.classList.toggle('on', b.dataset.hub === (mode === 'loadout' ? 'loadout' : 'weapons'));
  const hn = $('czHub').firstElementChild; if (hn && hn.mark) hn.mark(); // (its pictures: your gun / look may have changed)
  if (mode === 'loadout' && !SLOTS.includes(WEAPONS[sel].slot)) sel = S.loadout.primary;
  $('czStage').append($('preview'));
  setPreviewRes([0.3, 0.45, 0.75, 1][S.jank] ?? 0.5); // potato is crunchy here too
  previewManual(V);
  refresh();
  setTab(tab);
  wantModels();
  requestAnimationFrame(() => { resizePreview(); dirty = 2; });
  lastAct = performance.now();
  if (first) for (const n of root.querySelectorAll('.cz-career, .cz-info')) if (!n._org) organic(n, { rim: 5, lumps: 4, shadow: [7, 7] }); // the menu's hand-cut slabs
}
export function czClose() {
  if (!open) return;
  open = false;
  previewManual(null);
  setPreviewRes(0.5);
  hoverOff();
}
export function czRefresh() { if (open) { refresh(); if (tab) renderTiles(); } }
export function czLate() { if (open) dirty = 2; } // a skin's model landed: only the pictures that waited on it redraw (pumpIcons + whenGlb), the 3D view refreshes itself

// called every frame while the screen is up: returns how much time to render (0 = rest)
export function czFrame(dt) {
  if (!open) return 0;
  pumpIcons();
  const n = performance.now(), idle = n - lastAct > 14000; // nobody touched it for a while: stop turning, stop drawing
  if (!drag && !idle && n > spinHold) V.yaw += dt * 0.32;
  acc += dt;
  const want = drag || dirty > 0 || (!idle && n > spinHold) || hovering;
  if (!want || acc < 1 / 30) return 0; // 30 fps is plenty for a turntable
  const d = Math.min(acc, 0.1); acc = 0;
  if (dirty > 0) dirty--;
  return d;
}

// ------------------------------------------------------------ helpers
const curSkin = (id = sel) => validSkin(S.skins[id]); // your picks (random kept)
const wearing = (id = sel) => (G.equipped[id] || DEFAULT_SKIN).slice(); // what you actually wear (random rolled)
function show3d(skin) { showPreview(sel, skin); dirty = 2; }
const achOf = (type, k) => { const v = COSMETICS[type][k]; return v && v.ach && ACHIEVEMENTS[v.ach]; };
const myAchs = () => api.myAchs();
function tipOf(type, k) {
  const v = COSMETICS[type][k];
  if (!v) return '';
  if (v.desc) return v.desc;
  if (type === 'model') return k === 'default' ? 'the standard model.' : `a different ${WEAPONS[v.weapon] ? WEAPONS[v.weapon].name : 'weapon'}. same gun, new body.`;
  return BASE_TIP[type] || '';
}
function whereFrom(type) { const c = Object.values(CONTAINERS).find((x) => x.types.includes(type)); return c ? c.plural.toLowerCase() : 'containers'; }
const isFav = (type, k) => favList(type).includes(k);
function toggleFav(type, k) {
  const f = { ...myFavs() };
  const l = favList(type).slice(), i = l.indexOf(k);
  if (i >= 0) l.splice(i, 1); else l.push(k);
  f[type] = l;
  if (!Array.isArray(f.only)) f.only = [];
  S.favs = f;
  api.save(); api.sendSkins();
}
function setFavOnly(type, on) {
  const f = { ...myFavs() };
  f.only = (Array.isArray(f.only) ? f.only : []).filter((t) => t !== type);
  if (on) f.only.push(type);
  S.favs = f;
  for (const k of Object.keys(localRoll)) delete localRoll[k];
  api.save(); api.recompute(); api.sendSkins();
}

// ------------------------------------------------------------ left: career card + weapon list
function renderLeft() {
  const c = $('czCareer');
  const me = account.me, name = (me && me.name) || S.name || 'guest';
  const color = (S.look && S.look.color) || '#ff4fd8';
  let bg = c.querySelector('.cz-cbody');
  if (!bg) { bg = el('div', 'cz-cbody'); c.append(bg); }
  bg.innerHTML = '';
  const img = el('img', 'cz-card'); img.src = defaultCard(name, color); img.alt = '';
  const who = el('div', 'cz-who');
  const nm = el('b', null, name); nm.style.color = color;
  who.append(nm, el('span', null, me ? `level ${me.level || 1}` : 'guest. log in to unlock stuff'));
  const quick = el('div', 'cz-quick');
  for (const s of SLOTS) {
    const id = S.loadout[s];
    if (!id || !api.skinnable().includes(id)) continue;
    const q = el('button', 'cz-q' + (id === sel ? ' on' : ''));
    q.title = `${s}: ${WEAPONS[id].name}`;
    const im = el('img'); lazyIcon(im, () => weaponIcon(id, G.equipped[id]));
    q.append(im);
    q.addEventListener('click', () => pick(id));
    quick.append(q);
  }
  bg.append(img, who, quick);
  const list = $('czList');
  list.innerHTML = '';
  const ids = api.skinnable();
  for (const slot of mode === 'loadout' ? SLOTS : [...SLOTS, 'item', 'streak']) {
    const mine = ids.filter((id) => WEAPONS[id].slot === slot && id !== 'scythe_rifle'); // (skinnable() already keeps only items you hold)
    if (!mine.length) continue;
    list.append(el('div', 'cz-slot', slot === 'streak' ? 'Killstreak' : slot === 'item' ? `Item (${K.label('item')})` : slot[0].toUpperCase() + slot.slice(1)));
    for (const id of mine) {
      const w = WEAPONS[id];
      const r = el('button', 'cz-row' + (id === sel ? ' on' : ''));
      r.style.setProperty('--c', w.color);
      r.dataset.id = id;
      const im = el('img'); lazyIcon(im, () => weaponIcon(id, G.equipped[id]));
      const dressed = S.skins[id] && (S.skins[id].slice(0, 4).some((v, i) => v !== DEFAULT_SKIN[i]));
      const eq = SLOTS.includes(w.slot) && S.loadout[w.slot] === id;
      r.append(im, el('span', 'nm', w.name), el('span', 'dot', mode === 'loadout' ? (eq ? 'E' : '') : dressed ? '★' : ''));
      if (eq) r.classList.add('eq');
      r.addEventListener('dblclick', () => { if (SLOTS.includes(w.slot)) equip(id); });
      if (modelsFor(id).length > 1) r.title = `${modelsFor(id).length - 1} skin(s)`;
      r.addEventListener('click', () => pick(id));
      list.append(r);
    }
  }
  const on = list.querySelector('.cz-row.on');
  if (on && !list.dataset.scrolled) { list.dataset.scrolled = '1'; requestAnimationFrame(() => on.scrollIntoView({ block: 'center' })); }
}
function pick(id) { sel = id; G.cosSel = id; refresh(); if (tab) renderTiles(); poke(); wantModels(); }
// fetch ahead: what's on screen asks for itself (pri 3, glbkit noteMiss); then this weapon's skins, then, while you
// browse, every other weapon's skins a couple at a time in the background
let idleT = 0;
function wantModels() {
  prefetch(['w_' + sel, ...modelsFor(sel).filter((k) => k !== 'default').map((k) => 'w_' + k)], tab === 'skin' ? 4 : 2); // the Skin strip open: those are on screen now
  clearTimeout(idleT);
  idleT = setTimeout(() => { if (open) prefetch(api.skinnable().flatMap((id) => modelsFor(id).filter((k) => k !== 'default').map((k) => 'w_' + k)), 0); }, 1500);
}

// ------------------------------------------------------------ right: info, mastery, overview, statistics
const openRow = { overview: true, stats: false };
function statRows(w) {
  const out = [];
  const dmg = w.dmg != null ? w.dmg * (w.pellets || 1) : w.damage;
  if (dmg != null) out.push(['damage', dmg, 120, `${w.pellets ? `${w.pellets} x ${w.dmg}` : Math.round(dmg)}`]);
  const rate = w.rateMax || w.rate || (w.cd ? 1 / w.cd : 0);
  if (rate) out.push(['fire rate', rate, 25, `${Math.round(rate * 10) / 10}/s${w.rateMax ? ' (low hp)' : ''}`]);
  if (w.mag) out.push(['mag', w.mag, 60, String(w.mag)]);
  if (w.reload) out.push(['reload', 4 - w.reload, 4, `${w.reload}s`]);
  if (w.range) out.push(['range', w.range, 300, `${w.range}m`]);
  if (w.head) out.push(['headshot', w.head, 4, `x${w.head}`]);
  if (w.kb) out.push(['knockback', w.kb, 8, String(w.kb)]);
  return out;
}
function bar(label, v, max, txt) {
  const r = el('div', 'cz-stat');
  const b = el('div', 'b'), f = el('i');
  f.style.width = `${Math.max(4, Math.min(100, (v / max) * 100))}%`;
  b.append(f);
  r.append(el('span', 'l', label), b, el('span', 'v', txt));
  return r;
}
function renderRight() {
  const w = WEAPONS[sel], info = $('czInfo');
  let body = info.querySelector('.cz-ibody');
  if (!body) { body = el('div', 'cz-ibody'); info.append(body); }
  body.innerHTML = '';
  const h = el('h3', null, w.name); h.style.color = w.color;
  const tag = el('div', 'cz-tag', `${w.slot === 'streak' ? 'killstreak' : w.slot} · ${KIND[w.kind] || w.kind || 'thing'}`);
  tag.style.setProperty('--c', w.color);
  body.append(h, tag, el('p', null, w.desc || 'it does what it says.'));
  if (SLOTS.includes(w.slot)) { // equip to its slot, right here (the old LOADOUT screen lives on as this)
    const on = S.loadout[w.slot] === sel;
    const eb = el('button', 'cz-equip' + (on ? ' on' : ''), on ? `EQUIPPED AS ${w.slot.toUpperCase()} ✓` : `EQUIP AS ${w.slot.toUpperCase()}`);
    eb.addEventListener('click', () => equip(sel));
    body.append(eb);
    const note = api.loNote();
    if (note) body.append(el('div', 'cz-lonote', note));
  }
  // mastery: kills with it, a level every 25
  const k = (S.wk && S.wk[sel]) | 0, lvl = Math.floor(k / 25) + 1;
  const m = el('div', 'cz-mast');
  m.append(el('span', 'l', `MASTERY ${lvl}`), (() => { const b = el('div', 'b'), f = el('i'); f.style.width = `${((k % 25) / 25) * 100}%`; b.append(f); return b; })(), el('span', 'v', `${k % 25}/25 kills`));
  body.append(m);
  // the action rows
  const acts = $('czActs');
  acts.innerHTML = '';
  const row = (key, title, sub, fill) => {
    const r = el('div', 'cz-act' + (openRow[key] ? ' open' : ''));
    const hd = el('button', 'hd');
    hd.append(el('b', null, title), el('span', null, sub), el('em', null, openRow[key] ? '−' : '+'));
    hd.addEventListener('click', () => { openRow[key] = !openRow[key]; renderRight(); });
    r.append(hd);
    if (openRow[key]) { const c = el('div', 'bd'); fill(c); r.append(c); }
    acts.append(r);
  };
  row('overview', 'OVERVIEW', 'its numbers', (c) => { const rs = statRows(w); if (!rs.length) c.append(el('div', 'cz-none', 'no numbers. it is a vibe.')); for (const s of rs) c.append(bar(...s)); });
  row('stats', 'STATISTICS', 'your numbers', (c) => {
    const st = (account.me && account.me.stats) || null;
    c.append(bar('kills with it', k, Math.max(25, lvl * 25), String(k)));
    if (!st) { c.append(el('div', 'cz-none', 'guest: log in to keep lifetime stats.')); return; }
    const kd = st.deaths ? (st.kills / st.deaths).toFixed(2) : String(st.kills || 0);
    for (const [l, v] of [['kills', st.kills || 0], ['deaths', st.deaths || 0], ['k/d', kd], ['headshots', st.headshots || 0], ['wins', st.wins || 0], ['t-bags', st.tbags || 0]]) {
      const r = el('div', 'cz-kv'); r.append(el('span', null, l), el('b', null, String(v))); c.append(r);
    }
  });
  const btns = el('div', 'cz-btns');
  const b = (t, fn, cls = '') => { const x = el('button', 'cz-btn ' + cls, t); x.addEventListener('click', fn); btns.append(x); return x; };
  b('COPY LOOK TO ALL', () => {
    const sk = curSkin();
    for (const id of api.skinnable()) { const s2 = validSkin(S.skins[id]).slice(); s2[0] = sk[0]; s2[1] = sk[1]; s2[2] = sk[2]; s2[4] = sk[4]; api.storeSkin(id, s2); }
    api.bulk(); api.toast(`${WEAPONS[sel].name}'s wrap, charm and effect are on everything now`); refresh();
  }).title = 'wrap, charm, effect and wrap mode go on every weapon. skins stay';
  b('RESET', () => { api.setSkin(sel, DEFAULT_SKIN.slice()); refresh(); if (tab) renderTiles(); }, 'danger');
  b('RANDOM LOOK', () => { // a random owned wrap, charm, effect and wrap mode on this weapon
    const s2 = curSkin().slice();
    s2[0] = pickOne(pool('finish', sel)) || 'default'; s2[1] = pickOne(pool('hat', sel)) || 'none'; s2[2] = pickOne(pool('effect', sel)) || 'none'; s2[4] = pickOne(WRAP_MODES);
    api.setSkin(sel, s2); refresh(); if (tab) renderTiles();
  });
  if (mode !== 'loadout') acts.append(btns);
}

function refresh() {
  if (!open) return;
  renderLeft();
  renderRight();
  for (const b of $('czTabs').children) b.classList.toggle('on', b.dataset.tab === tab);
  renderLo();
  if (!hovering) show3d(wearing());
}

// ------------------------------------------------------------ LOADOUT: equip weapons, pick the item and 3 killstreaks
function equip(id) {
  const w = WEAPONS[id];
  if (!w || !SLOTS.includes(w.slot)) return;
  api.equip(w.slot, id);
  api.toast(`${w.name} equipped as ${w.slot}${api.loNote() ? `. ${api.loNote()}` : ''}`);
  refresh();
}
let draft = null; // killstreak picks while you have fewer than 3 (never saved like that)
function loTile(cls, pic, name, sub, on, tip, color, fn) {
  const t = el('button', 'cz-tile ' + cls + (on ? ' on' : ''));
  t.style.setProperty('--rc', color);
  const p = el('span', 'pic'), im = el('img'); im.alt = ''; im.src = PLACEHOLDER; p.append(im);
  t.append(p, el('span', 'nm', name));
  if (sub) t.append(el('span', 'eq sub', sub));
  if (on) t.append(el('span', 'eq', 'ON'));
  t._pic = pic; t._img = im;
  tileQ.push(t); // (killstreaks are 3D renders now too: queued like the rest)
  t.addEventListener('mouseenter', () => { const h = $('czHover'); h.classList.remove('hidden'); h.style.setProperty('--rc', color); h.querySelector('b').textContent = name; h.querySelector('i').textContent = tip[0]; h.querySelector('span').textContent = tip[1]; h.querySelector('.req').innerHTML = ''; });
  t.addEventListener('mouseleave', () => $('czHover').classList.add('hidden'));
  t.addEventListener('click', fn);
  return t;
}
function renderLo() {
  const box = $('czLo');
  box.innerHTML = '';
  if (mode !== 'loadout') return;
  if (zlRender(box, { loTile, toast: api.toast, save: api.save, redraw: refresh })) return; // the ZOMBIES tab
  const row = (title, list) => { const r = el('div', 'cz-lorow'); r.append(el('div', 'cz-lot', title)); const t = el('div', 'cz-tiles'); t.append(...list); r.append(t); box.append(r); };
  const cur = S.loadout.item || 'frag';
  row(`ITEM (${K.label('item')})`, ITEM_ORDER.map((id) => { const it = ITEMS[id]; return loTile('lo-item', () => itemPic(id, G.equipped[it.w]), it.name, `x${it.charges}`, id === cur, [`ITEM · ${it.charges} CHARGE${it.charges > 1 ? 'S' : ''} · ${it.recharge}s REFILL`, it.desc], it.color, () => { api.setItem(id); refresh(); }); }));
  const picks = draft || validStreaks(S.loadout.streaks);
  row(`KILLSTREAKS · PICK 3 · ${['streak1', 'streak2', 'streak3'].map((k) => K.label(k)).join(' / ')}`, Object.entries(STREAKS).sort((a, b) => a[1].kills - b[1].kills).map(([id, st]) => loTile('lo-streak', () => streakIcon(id), st.name, `${st.kills}`, picks.includes(id), [`KILLSTREAK · ${st.kills} KILLS IN A ROW`, st.desc], '#ffe14d', () => {
    if (picks.includes(id)) { draft = picks.filter((x) => x !== id); api.toast('pick another killstreak to fill the slot'); refresh(); return; }
    if (picks.length >= 3) { api.toast('click one of your killstreaks to drop it first'); return; }
    const next = [...picks, id];
    if (next.length < 3) { draft = next; refresh(); return; }
    draft = null; api.setStreaks(next); refresh();
  })));
}

// ------------------------------------------------------------ the strip: search, filters, tiles
function buildBar() {
  const bar = $('czBar');
  bar.innerHTML = '';
  const back = el('button', 'cz-back', '◀ BACK'); back.addEventListener('click', () => setTab(null));
  const q = el('input'); q.type = 'search'; q.placeholder = 'search by name or tooltip'; q.maxLength = 30; q.spellcheck = false; q.id = 'czSearch';
  q.addEventListener('input', () => { F.q = q.value.trim().toLowerCase(); renderTiles(); });
  q.addEventListener('keydown', (e) => e.stopPropagation()); // typing isn't hotkeys
  const pills = el('div', 'cz-pills'); pills.id = 'czPills';
  for (const r of ['all', 'owned', ...RAR_ORDER.slice(1), 'fav']) {
    const p = el('button', 'cz-pill', r === 'all' ? 'ALL' : r === 'owned' ? 'OWNED' : r === 'fav' ? '♥' : RARITY[r].name.toUpperCase());
    p.dataset.r = r;
    if (RARITY[r]) p.style.setProperty('--rc', RARITY[r].color);
    p.addEventListener('click', () => { F.r = r; renderTiles(); });
    pills.append(p);
  }
  const extra = el('div', 'cz-extra'); extra.id = 'czExtra';
  const n = el('span', 'cz-n'); n.id = 'czN';
  bar.append(back, q, pills, extra, n);
}
function setTab(t) {
  tab = t;
  $('czStrip').classList.toggle('hidden', !t);
  root.classList.toggle('strip-on', !!t);
  for (const b of $('czTabs').children) b.classList.toggle('on', b.dataset.tab === t);
  hoverOff();
  if (t) { F.r = 'all'; renderTiles(); $('czTiles').scrollLeft = 0; wantModels(); }
  requestAnimationFrame(() => { resizePreview(); dirty = 2; });
}
const TAB = () => TABS.find((x) => x.id === tab);
function current(T) { return T.global ? (S.kfx || 'none') : curSkin()[T.idx] || T.none; }
function itemsFor(T) {
  if (T.type === 'model') return modelsFor(sel).filter((k) => k !== 'default');
  return Object.keys(COSMETICS[T.type]).filter((k) => k !== T.none);
}
function renderExtra(T) {
  const x = $('czExtra');
  x.innerHTML = '';
  if (T.type === 'finish') { // where the wrap goes
    const wm = el('div', 'cz-wm');
    const sk = curSkin();
    for (const m of WRAP_MODES) {
      const b = el('button', sk[4] === m ? 'on' : '');
      b.innerHTML = wrapIcon(m); b.append(WRAP_MODE_NAMES[m].toUpperCase());
      b.title = { normal: 'the handle / body', reverse: 'the blade / barrel / business end', full: 'the whole thing' }[m];
      b.addEventListener('click', () => { setPart(4, m); renderTiles(); });
      wm.append(b);
    }
    x.append(wm);
  }
  const lab = (text, on, fn, tip) => { const l = el('label', 'cz-chk'); const c = el('input'); c.type = 'checkbox'; c.checked = on; c.addEventListener('change', () => fn(c.checked)); l.append(c, text); if (tip) l.title = tip; x.append(l); return l; };
  lab('only use favourites', favOnly(T.type), (on) => { setFavOnly(T.type, on); renderTiles(); }, 'Random only picks from your ♥ ones');
  if (!T.global && T.type !== 'model') lab('put it on every weapon', copyAll, (on) => { copyAll = on; }, 'untick to dress weapons one by one');
}
function setPart(idx, v) {
  if (copyAll && idx !== 3) api.setPartAll(idx, v);
  else { const s2 = curSkin().slice(); s2[idx] = v; api.setSkin(sel, s2); }
  refresh();
}

let tilesIO = null;
function renderTiles() {
  const T = TAB();
  if (!T) return;
  hoverOff(); // the tile under the mouse is about to go: no mouseleave will come
  for (const p of $('czPills').children) p.classList.toggle('on', p.dataset.r === F.r);
  renderExtra(T);
  const box = $('czTiles');
  box.innerHTML = '';
  if (tilesIO) tilesIO.disconnect();
  tilesIO = 'IntersectionObserver' in window ? new IntersectionObserver((es) => { for (const e of es) if (e.isIntersecting && e.target._pic) { tileQ.push(e.target); tilesIO.unobserve(e.target); } }, { root: box, rootMargin: '0px 200px' }) : null;
  const cur = current(T);
  const all = itemsFor(T);
  let list = all.filter((k) => {
    const v = COSMETICS[T.type][k];
    if (F.r === 'owned' && !owns(G.inv, T.type, k)) return false;
    if (F.r === 'fav' && !isFav(T.type, k)) return false;
    if (RARITY[F.r] && v.rarity !== F.r) return false;
    if (F.q && !(v.name.toLowerCase().includes(F.q) || k.includes(F.q) || tipOf(T.type, k).toLowerCase().includes(F.q))) return false;
    return true;
  }).sort((a, b) => RAR_ORDER.indexOf(COSMETICS[T.type][a].rarity) - RAR_ORDER.indexOf(COSMETICS[T.type][b].rarity));
  // None + Random first (search can't hide them)
  box.append(tile(T, T.none, cur, 'none'), tile(T, RAND, cur, 'rand'));
  for (const k of list) box.append(tile(T, k, cur));
  $('czN').textContent = `${list.length}/${all.length}`;
  if (!list.length) box.append(el('div', 'cz-empty', T.type === 'model' && !all.length ? `no skins for the ${WEAPONS[sel].name} yet` : 'nothing matches. try fewer letters'));
  if (!tilesIO) { for (const t of box.children) if (t._pic) tileQ.push(t); }
  else for (const t of [...box.children].slice(0, 12).reverse()) if (t._pic) { tilesIO.unobserve(t); tileQ.unshift(t); } // the first screenful right away (the observer can lag a busy frame or two)
}
function variant(T, k) { const s = wearing(); s[T.idx] = k === RAND ? pickOne(pool(T.type, sel)) || T.none : k; return s; }
function tile(T, k, cur, kind) {
  const v = k === RAND ? { name: 'Random', rarity: 'free' } : COSMETICS[T.type][k];
  const have = k === RAND || owns(G.inv, T.type, k);
  const ach = k !== RAND && achOf(T.type, k);
  const t = el('button', 'cz-tile' + (k === cur ? ' on' : '') + (have ? '' : ' locked') + (ach ? ' ach' : '') + (kind ? ' ' + kind : ''));
  t.style.setProperty('--rc', RARITY[v.rarity].color);
  t.dataset.k = k;
  const pic = el('span', 'pic');
  const name = kind === 'none' ? 'None' : v.name;
  t.append(pic, el('span', 'nm', name));
  if (k === cur) t.append(el('span', 'eq', 'ON'));
  if (!have) t.append(el('span', 'lk', '🔒'));
  if (!kind) {
    const h = el('span', 'heart' + (isFav(T.type, k) ? ' fav' : ''), '♥');
    h.title = 'favourite';
    h.addEventListener('click', (e) => { e.stopPropagation(); toggleFav(T.type, k); h.classList.toggle('fav', isFav(T.type, k)); if (F.r === 'fav') renderTiles(); });
    t.append(h);
  }
  // the picture
  if (k === RAND) pic.append(el('span', 'glyph', '?'));
  else if (T.type === 'kill') pic.append(el('span', 'glyph', KILL_ICO[k] || '💀'));
  else if (T.type === 'effect') pic.append(el('span', 'glyph', k === 'none' ? '∅' : FX_ICO[k] || '✨'));
  else if (T.type === 'hat' && k === 'none') pic.append(el('span', 'glyph', '∅'));
  else {
    const im = el('img'); im.alt = ''; im.src = PLACEHOLDER; pic.classList.add('loading');
    pic.append(im);
    const sk = wearing();
    if (T.type === 'hat') t._pic = () => objIcon('czhat:' + k, () => makeHat(k));
    else if (T.type === 'model') { sk[0] = 'default'; sk[1] = 'none'; sk[2] = 'none'; sk[3] = k; t._pic = () => weaponIcon(sel, sk); }
    else { sk[0] = k; sk[1] = 'none'; sk[2] = 'none'; t._pic = () => weaponIcon(sel, sk); }
    t._img = im;
    if (tilesIO) tilesIO.observe(t);
  }
  t.addEventListener('mouseenter', () => hoverOn(T, k, v, have, ach, kind));
  t.addEventListener('mouseleave', hoverOff);
  t.addEventListener('click', () => {
    if (!have && ach) { api.toast(`${v.name}: unlock "${ach.name}" (${ach.desc})${account.loggedIn ? '' : '. log in so it counts'}`, 3600); return; }
    if (!have) { api.toast(`${v.name} is ${RARITY[v.rarity].name}. ${account.loggedIn ? `find it in ${whereFrom(T.type)}` : 'log in, win rounds, open containers'}`); return; }
    if (k === RAND) for (const key of Object.keys(localRoll)) if (key.startsWith(sel) || T.global) delete localRoll[key];
    if (T.global) api.setKfx(k);
    else setPart(T.idx, k);
    if (k === RAND) api.toast(`random ${TYPE_LABEL[T.type].toLowerCase()}: a different one${favOnly(T.type) ? ' of your favourites' : ''} every spawn`);
    renderTiles();
    hoverOn(T, k, v, have, ach, kind); // still under the mouse (the strip was rebuilt under it)
  });
  return t;
}

// ------------------------------------------------------------ hover: big title + tooltip up top, try it on
let hovering = false;
function hoverOn(T, k, v, have, ach, kind) {
  hovering = true; poke();
  const h = $('czHover');
  h.classList.remove('hidden');
  h.style.setProperty('--rc', RARITY[v.rarity].color);
  h.querySelector('b').textContent = kind === 'none' ? `No ${TYPE_LABEL[T.type]}` : v.name;
  h.querySelector('i').textContent = k === RAND ? `RANDOM ${TYPE_LABEL[T.type].toUpperCase()}` : `${RARITY[v.rarity].name.toUpperCase()} ${TYPE_LABEL[T.type].toUpperCase()}${have ? '' : ' · LOCKED'}`;
  let tip = k === RAND ? `a random one you own, rolled every time you spawn${favOnly(T.type) ? ' (only your ♥ favourites)' : ''}. (${pool(T.type, sel).length} to pick from)`
    : kind === 'none' ? (T.type === 'kill' ? 'they just fall apart. classic.' : `take the ${TYPE_LABEL[T.type].toLowerCase()} off.`) : tipOf(T.type, k);
  if (!have && !ach) tip += account.loggedIn ? ` · find it in ${whereFrom(T.type)}` : ' · log in to unlock stuff';
  h.querySelector('span').textContent = tip;
  const req = h.querySelector('.req');
  req.innerHTML = '';
  if (ach) { // an achievement skin: what it takes, with what you've done so far
    const st = (account.me && account.me.stats) || {}, done = myAchs().has(v.ach);
    req.append(el('b', null, done ? `★ ${ach.name}: yours${k === 'sniper_golden' ? '. stays gold under any wrap' : ''}` : `${ach.name} ${Math.min(ach.goal, achProgress(ach, st))}/${ach.goal}: ${ach.desc}${account.loggedIn ? '' : '. log in so it counts'}`));
    if (ach.feats) req.append(royalBoxes(done ? ROYAL_ALL : st[ach.stat] || 0, 0, ach.feats));
  }
  if (!T.global) show3d(variant(T, k)); // try it on, locked or not
}
function hoverOff() {
  if (!hovering) return;
  hovering = false;
  $('czHover').classList.add('hidden');
  if (open) show3d(wearing());
}

// ------------------------------------------------------------ tile + list pictures, a few per frame
let redraws = 0; // (tests read it: window.__czRedraws)
export const czRedraws = () => redraws;
const iconQ = [], tileQ = []; // the strip's tiles go first: they're what you're looking at
function lazyIcon(img, fn) { img.src = PLACEHOLDER; const holder = { _pic: fn, _img: img }; iconQ.push(holder); } // (the loading cube until it's drawn)
function pumpIcons() {
  const t0 = performance.now();
  while ((tileQ.length || iconQ.length) && performance.now() - t0 < 12) {
    const t = tileQ.length ? tileQ.shift() : iconQ.shift();
    if (t._img && t._img.isConnected) {
      const [u, w] = drawIcon(t._pic);
      if (u && t._img.src !== u) { t._img.src = u; redraws++; }
      if (t._img.parentNode) t._img.parentNode.classList.toggle('loading', isPlaceholder(u));
      if (w) { whenGlb(w, () => tileQ.push(t)); if (t.dataset && t.dataset.k) for (const g of w) want(g, 4); } // drawn without (or waiting for) a Blender model: again when it lands. the strip's tiles jump the queue
    }
  }
}
function wrapIcon(mode) { // a tiny knife: the half the wrap paints is pink
  const on = (z) => (mode === 'full' || mode === z ? '#ff4fd8' : '#9a9aa4');
  return `<svg viewBox="0 0 46 14"><rect x="1" y="4" width="15" height="6" fill="${on('normal')}" stroke="#000" stroke-width="1.5"/>`
    + `<rect x="16" y="2" width="3" height="10" fill="${on('normal')}" stroke="#000" stroke-width="1.5"/>`
    + `<path d="M19 3 L40 3 L45 7 L40 11 L19 11 Z" fill="${on('reverse')}" stroke="#000" stroke-width="1.5"/></svg>`;
}
