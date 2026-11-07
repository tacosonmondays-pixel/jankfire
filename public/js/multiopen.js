// Opening containers in bulk (OPEN x5 / x10 / ALL) and the management's gift popup.
// Bulk: one request to /api/rollmany (server/accounts.js rollMany: same picks as one at a time, one store write), and
// meanwhile every container on screen rattles together; then they all pop at once and the results drop in, rarest
// first. legendary / epic ones flash. SKIP (or a click anywhere) jumps straight to the results.
// Gift: "THE MANAGEMENT FEELS GENEROUS", the 3D crate, bag and box with how many of each, once per gift.
import { COSMETICS, CONTAINERS, RARITY, TYPE_NAMES_ALL as TYPE_NAMES } from '/shared/cosmetics.js';
import { WEAPONS } from '/shared/weapons.js';
import { activeGifts } from '/shared/gifts.js';
import { studioIcon, weaponIcon, liveIcon } from './icons.js';
import { buildContainer } from './crate3d.js';
import { sprayIcon } from './sprays.js';
import { grappleThumb } from './grapple.js';
import { account } from './account.js';
import { sfx } from './audio.js';

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const ACC = { crate: '#ffb04f', bag: '#7dff4f', box: '#ff4fd8' };
const RANK = { legendary: 0, epic: 1, rare: 2, common: 3, free: 4 };
const FX_ICO = { smoke: '💨', bubbles: '🫧', sparkles: '✨', music: '🎵', hearts: '💖', electric: '⚡', flames: '🔥', money: '💸', rainbow: '🌈' };
const KILL_ICO = { confetti: '🎉', grave: '🪦', cash: '💵', pixel: '👾', balloon: '🎈', chicken: '🐔', bsod: '💻', yeet: '🚀', ascend: '🛸', duck: '🦆', blastzone: '💥' };
export function containerIcon(kind) { return studioIcon('box3d:' + kind, () => buildContainer(kind), { w: 96, h: 96, accent: ACC[kind] || '#ff4fd8', yaw: -0.6, pitch: 0.35, roll: 0 }); }

let api = null, box = null;
// a: { equip(item) -> null | [label, fn] (what an EQUIP button does for this item), after() (refresh screens), toast }
export function initMultiOpen(a) {
  api = a;
  box = el('div', 'mo hidden'); box.id = 'multibox';
  document.body.append(box);
}

// ------------------------------------------------------------ bulk open
let busy = false;
export async function openMany(kind, n) {
  if (busy || !account.loggedIn || !CONTAINERS[kind]) return;
  busy = true;
  const c = CONTAINERS[kind];
  box.innerHTML = '';
  box.classList.remove('hidden', 'popped');
  const inner = el('div', 'mo-in');
  const title = el('div', 'mo-title', `OPENING ${n} ${(n === 1 ? c.name : c.plural).toUpperCase()}`);
  const grid = el('div', 'mo-shake');
  const pic = containerIcon(kind);
  for (let i = 0; i < Math.min(n, 100); i++) { const im = el('img'); im.src = pic; im.alt = ''; im.style.setProperty('--d', `${(Math.random() * -0.4).toFixed(2)}s`); im.style.setProperty('--r', `${((Math.random() - 0.5) * 16).toFixed(1)}deg`); grid.append(im); }
  grid.style.setProperty('--sz', n > 50 ? '44px' : n > 20 ? '58px' : '84px');
  const skip = el('button', 'mid mo-skip', 'SKIP');
  inner.append(title, grid, skip);
  box.append(inner);
  let skipped = false;
  const onSkip = () => { skipped = true; };
  skip.addEventListener('click', onSkip); box.addEventListener('pointerdown', onSkip, { once: true });
  const t0 = performance.now();
  let r;
  try {
    const res = await fetch('/api/rollmany', { method: 'POST', headers: { authorization: 'Bearer ' + account.token, 'content-type': 'application/json' }, body: JSON.stringify({ kind, n }) });
    r = await res.json();
    if (!res.ok) throw new Error(r.error || 'could not open them');
  } catch (e) { busy = false; box.classList.add('hidden'); api.toast(e.message); return; }
  account.me = r.me;
  // rattle for a bit (harder as it goes), unless skipped
  grid.classList.add('go');
  while (!skipped && performance.now() - t0 < 1700) await new Promise((res) => setTimeout(res, 50));
  box.classList.add('popped'); // they all burst at once
  sfx.click();
  if (!skipped) await new Promise((res) => setTimeout(res, 380));
  results(kind, n, r, inner, skipped);
  busy = false;
  api.after();
}

function results(kind, n, r, inner, fast) {
  inner.innerHTML = '';
  const items = r.items.filter(Boolean).sort((a, b) => RANK[a.rarity] - RANK[b.rarity] || a.name.localeCompare(b.name));
  const dupes = r.items.length - items.length;
  const best = items[0] && items[0].rarity;
  inner.append(el('div', 'mo-title', best === 'legendary' ? 'LEGENDARY!!' : best === 'epic' ? 'EPIC PULL' : `${n} OPENED`));
  const sum = el('div', 'mo-sum', `${items.length} new${dupes ? ` · ${dupes} with nothing new left → +${r.xp} xp` : ''}`);
  inner.append(sum);
  const grid = el('div', 'mo-res');
  items.forEach((it, i) => {
    const card = el('div', 'mo-card r-' + it.rarity);
    card.style.setProperty('--rc', RARITY[it.rarity].color);
    card.style.setProperty('--i', fast ? 0 : Math.min(i, 40));
    const p = el('span', 'pic'), im = el('img'); im.alt = ''; p.append(im);
    const g = glyph(it); if (g) p.append(el('span', 'glyph', g)); else queuePic(im, it);
    card.append(p, el('b', null, it.name), el('small', null, `${RARITY[it.rarity].name} ${TYPE_NAMES[it.type].toLowerCase()}`));
    const eq = api.equip(it);
    if (eq) { const b = el('button', 'mo-eq', eq[0]); b.addEventListener('click', () => { eq[1](); b.textContent = 'ON ✓'; b.disabled = true; }); card.append(b); }
    grid.append(card);
  });
  for (let i = 0; i < dupes; i++) { const card = el('div', 'mo-card dupe'); card.style.setProperty('--i', fast ? 0 : Math.min(items.length + i, 40)); card.append(el('span', 'pic', '+100'), el('b', null, 'XP'), el('small', null, 'you own all of it')); grid.append(card); }
  inner.append(grid);
  if (best === 'legendary' || best === 'epic') { box.classList.add(best === 'legendary' ? 'flash-l' : 'flash-e'); setTimeout(() => box.classList.remove('flash-l', 'flash-e'), 900); sfx.kill(); } else sfx.ting();
  const row = el('div', 'row mo-btns');
  const left = (account.me.rolls[kind] || 0);
  const again = Math.min(n, left);
  if (again > 0) { const b = el('button', 'mid', `OPEN ${again} MORE (${left} left)`); b.addEventListener('click', () => { close(); openMany(kind, again); }); row.append(b); }
  const ok = el('button', 'mid glow', 'OK'); ok.addEventListener('click', close); row.append(ok);
  inner.append(row);
}
function close() { box.classList.add('hidden'); box.innerHTML = ''; api.after(); }
function glyph(it) {
  if (it.type === 'effect') return FX_ICO[it.id] || '✨';
  if (it.type === 'kill') return KILL_ICO[it.id] || '💀';
  return null;
}
// pictures for the cards: a few per frame (a hundred weapon renders at once would stall)
const picQ = [];
function queuePic(img, it) { picQ.push([img, it]); if (picQ.length === 1) requestAnimationFrame(pumpPics); }
function pumpPics() {
  const t0 = performance.now();
  while (picQ.length && performance.now() - t0 < 14) {
    const [img, it] = picQ.shift();
    if (!img.isConnected) continue;
    // liveIcon: a skin whose model is still downloading shows the loading cube, then redraws itself when it lands
    let u = '';
    try { u = liveIcon(img, () => picFor(it)); } catch { /* no picture */ }
    if (!u && img.parentElement) img.parentElement.append(el('span', 'glyph', '🎁')); // nothing to draw it on: a present
  }
  if (picQ.length) requestAnimationFrame(pumpPics);
}

function picFor(it) {
  if (it.type === 'model') { const w = COSMETICS.model[it.id] && COSMETICS.model[it.id].weapon; return w && WEAPONS[w] ? weaponIcon(w, ['default', 'none', 'none', it.id, 'normal']) : ''; }
  if (it.type === 'finish') return weaponIcon('ar', [it.id, 'none', 'none', 'default', 'full']);
  if (it.type === 'hat') return weaponIcon('ar', ['default', it.id, 'none', 'default', 'normal']);
  if (it.type === 'spray') return sprayIcon(it.id);
  if (it.type === 'grapple') return grappleThumb(it.id);
  return '';
}

// ------------------------------------------------------------ the management's gift
// gifts: the ones the server just gave (account.gifts). guest: show the current gift with "log in to claim"
export function showGift(gifts, guestLogin) {
  const g = gifts && gifts[0];
  if (!g) return;
  box.innerHTML = '';
  box.classList.remove('hidden', 'popped');
  const inner = el('div', 'mo-in gift');
  inner.append(el('div', 'mo-kicker', 'MEMO FROM THE MANAGEMENT'), el('div', 'mo-title big', g.title.replace('GENEROUS', 'GENEROUS:')));
  const row = el('div', 'gift-row');
  for (const [kind, n] of Object.entries(g.rolls)) {
    const c = CONTAINERS[kind]; if (!c) continue;
    const t = el('div', 'gift-c');
    const im = el('img'); im.src = containerIcon(kind); im.alt = '';
    t.append(im, el('b', null, `+${n}`), el('span', null, c.plural.toUpperCase()));
    t.style.setProperty('--ac', ACC[kind]);
    row.append(t);
  }
  inner.append(row);
  inner.append(el('div', 'mo-sum', guestLogin ? 'for every account. log in (or sign up) to claim yours.' : 'they are in CONTAINERS now. there is an OPEN ALL button. go nuts.'));
  const btns = el('div', 'row mo-btns');
  if (guestLogin) { const b = el('button', 'mid glow', 'LOG IN TO CLAIM'); b.addEventListener('click', () => { close(); guestLogin(); }); btns.append(b); }
  else { const b = el('button', 'mid glow', 'OPEN THEM'); b.addEventListener('click', () => { close(); api.toCrates(); }); btns.append(b); }
  const ok = el('button', 'mid', guestLogin ? 'LATER' : 'NICE'); ok.addEventListener('click', close); btns.append(ok);
  inner.append(btns);
  box.append(inner);
  box.classList.add('flash-l'); setTimeout(() => box.classList.remove('flash-l'), 900);
  try { sfx.kill(); } catch { /* audio not started yet */ }
}
// a guest sees the running gift once (per gift), with "log in to claim"
export function guestGiftOnce(login) {
  const g = activeGifts()[0];
  if (!g) return;
  const k = 'jf_giftseen_' + g.id;
  try { if (localStorage.getItem(k)) return; localStorage.setItem(k, '1'); } catch { return; }
  showGift([g], login);
}
