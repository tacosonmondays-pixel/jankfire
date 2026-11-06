// OVERDUE quick bar (WP3): 8 slots on 1-8, the bridge that hands the bar's weapons to the normal weapon code, the
// loot lying in the world (F picks it up), and the story keys. the inventory itself lives in the sim
// (shared/story/invsys.js); this only shows it and asks for changes.
//
// IV.inv is the latest inventory the sim sent: { bag, cap, bar, locker, next }. IV.on(fn) runs fn after each change.
import * as THREE from 'three';
import { G } from '../ctx.js';
import { K, extendActions } from '../keys.js';
import { hud } from '../hud.js';
import { ME } from '../player.js';
import { W, setSlots } from '../weapons.js';
import { weaponIcon, itemIcon, streakIcon } from '../icons.js';
import { buildWeapon } from '../models.js';
import { RARITY } from '/shared/cosmetics.js';
import { infoOf, kindOf, itemAt, barWeapons, INV } from '/shared/story/items.js';
import { PICK } from '/shared/story/invsys.js';
import { TEST } from '/shared/story/testmap.js';

const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
export const RCOL = { ...Object.fromEntries(Object.entries(RARITY).map(([k, v]) => [k, v.color])), premium: '#ff00dc' }; // ☺ PREMIUM: hot pink
export const IV = { inv: null, subs: [], on(fn) { this.subs.push(fn); }, sel: -1 };
let story = null, barEl = null, wanted = '', shownK = '', drops = new Map();

// the story keys: their own group + context, so they only exist (and only show in CONTROLS) with story mode loaded
export function storyKeys() {
  extendActions('Story', [
    ...Array.from({ length: INV.bar }, (_, i) => [`bar${i + 1}`, `Quick bar ${i + 1}`, [`Digit${i + 1}`], 'story']),
    ['wheel', 'Weapon wheel (hold)', ['KeyQ'], 'story'],
    ['bag', 'Tote Bag', ['KeyI'], 'story'],
    ['dropHeld', 'Drop what you hold', ['KeyH'], 'story'],
  ]);
}

export function initBar(st) {
  story = st;
  st.on('inv', (m) => {
    if (m.inv) IV.inv = m.inv;
    if (m.err) hud.msg(m.err.toUpperCase(), 1.6);
    if (m.inv && m.inv.fresh) st.send('starter', { lo: G.settings.loadout || {} }); // a new game: your loadout is the starter kit
    render();
    for (const f of IV.subs) f(IV.inv);
  });
  st.on('drops', (m) => { clearDrops(); for (const d of m.list || []) addDrop(d); });
  st.on('drop+', (m) => addDrop(m.d));
  st.on('drop-', (m) => { removeDrop(m.id); if (m.by) { const i = infoOf({ b: m.b }); if (i) hud.msg(`+ ${i.name.toUpperCase()}`, 1.2); } });
}

export function iconOf(b) {
  const k = kindOf(b);
  if (k === 'gun' || k === 'melee') return weaponIcon(b, (G.equipped || {})[b]);
  if (k === 'gear') return itemIcon(b);
  if (k === 'streak') return streakIcon(b);
  return snackIcon(b);
}
const snackCache = new Map();
function snackIcon(b) { // story things (cola, bread, junk, quest items) get a sticker with their first letters
  if (snackCache.has(b)) return snackCache.get(b);
  const c = document.createElement('canvas'); c.width = 64; c.height = 64;
  const x = c.getContext('2d'), i = infoOf({ b }) || { name: b, color: '#fff' };
  x.fillStyle = i.color; x.strokeStyle = '#000'; x.lineWidth = 4;
  x.beginPath(); x.roundRect(8, 8, 48, 48, 6); x.fill(); x.stroke();
  x.fillStyle = '#000'; x.font = 'bold 22px "Comic Neue", sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(i.name.split(/\s+/).map((w) => w[0]).join('').slice(0, 2).toUpperCase(), 32, 33);
  const url = c.toDataURL(); snackCache.set(b, url); return url;
}
// one picture of an item, the way the bag and the bar draw it
export function itemCell(it, keyLabel) {
  const c = el('div', 'st-cell' + (it ? '' : ' empty'));
  if (keyLabel) c.append(el('i', 'st-key', keyLabel));
  if (!it) return c;
  const i = infoOf(it);
  c.style.borderColor = RCOL[it.r] || RCOL.common;
  const img = el('img'); img.src = iconOf(it.b); img.alt = i ? i.name : it.b; img.draggable = false;
  c.append(img);
  if (it.q > 1) c.append(el('b', 'st-q', 'x' + it.q));
  c.title = i ? `${i.name} · ${it.r}${i.desc ? '\n' + i.desc : ''}` : it.b;
  return c;
}

// ------------------------------------------------------------ the bar on the HUD
function render() {
  if (!barEl) { barEl = el('div', 'st-bar'); barEl.id = 'storyBar'; document.body.append(barEl); }
  barEl.innerHTML = '';
  const inv = IV.inv;
  if (!inv) return;
  for (let i = 0; i < INV.bar; i++) {
    const it = inv.bar[i] == null ? null : itemAt(inv, inv.bar[i]);
    const c = itemCell(it, K.label(`bar${i + 1}`));
    const k = it && kindOf(it.b);
    if ((k === 'gun' || k === 'melee') && W.slot === i && W.cur === it.b) c.classList.add('on');
    if (k === 'gear' && W.item === it.b) c.classList.add('gear');
    barEl.append(c);
  }
}
export function barShow(on) { if (barEl) barEl.classList.toggle('hidden', !on); document.body.classList.toggle('st-on', on); }

// press a bar key: weapons go in your hands, gear becomes your G item, snacks get eaten, streaks wait for HYPE (WP5)
export function useBar(i) {
  const inv = IV.inv;
  const u = inv && inv.bar[i], it = u == null ? null : itemAt(inv, u);
  if (!it) return;
  const k = kindOf(it.b);
  if (k === 'gun' || k === 'melee') { bridge(); if (W.cur !== it.b || W.slot !== i) { const ids = barWeapons(inv); if (W.slot !== i) W.prevSlot = W.slot; setSlots(ids, i); wanted = ids.join(','); } }
  else if (k === 'gear') { story.send('gear', { u }); hud.msg(`G: ${infoOf(it).name.toUpperCase()}`, 1); }
  else if (k === 'snack') story.send('eat', { u });
  else if (k === 'streak') hud.msg('STREAKS NEED HYPE. HYPE IS COMING.', 1.6);
  setTimeout(render, 0);
}
export function dropHeld() {
  const inv = IV.inv;
  if (!inv) return;
  const u = inv.bar[W.slot];
  if (u != null && itemAt(inv, u) && itemAt(inv, u).b === W.cur) story.send('inv', { op: 'drop', u });
}

// the bridge: the weapon code's slots ARE the bar (an empty box for anything that isn't a weapon). checked every frame
// because a respawn or a loadout change puts the normal 3 slots back
export function bridge() {
  if (!IV.inv || !G.joined || G.mode !== 'story') return;
  const ids = barWeapons(IV.inv), key = ids.join(',');
  if (key === wanted && W.slots.join(',') === key && ids[W.slot] === W.cur) return;
  if (!ids.some(Boolean)) return; // nothing to hold: keep whatever's in hand (fists come later)
  wanted = key;
  const keep = ids[W.slot] === W.cur ? W.slot : ids.indexOf(W.cur);
  setSlots(ids, keep >= 0 ? null : ids.findIndex(Boolean));
  if (keep >= 0) W.slot = keep; // (the slot index always points at what's really in your hands)
  render();
}

// ------------------------------------------------------------ loot on the floor
const dropGeo = new THREE.BoxGeometry(0.5, 0.5, 0.5);
function addDrop(d) {
  if (!d || drops.has(d.id) || !G.scene) return;
  const g = new THREE.Group(), k = kindOf(d.item.b), col = new THREE.Color(RCOL[d.item.r] || RCOL.common);
  let m = null;
  if (k === 'gun' || k === 'melee') { try { m = buildWeapon(d.item.b, (G.equipped || {})[d.item.b]); m.scale.setScalar(1.3); } catch { m = null; } }
  if (!m) {
    const tex = new THREE.TextureLoader().load(iconOf(d.item.b));
    tex.colorSpace = THREE.SRGBColorSpace;
    m = new THREE.Mesh(dropGeo, [0, 1, 2, 3, 4, 5].map(() => new THREE.MeshLambertMaterial({ map: tex, color: 0xffffff })));
  }
  g.add(m);
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.12, 3, 6, 1, true), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.45, depthWrite: false }));
  beam.position.y = 1.4; g.add(beam); // a plain rarity beam: WP4 makes these loud
  g.position.set(d.p[0], d.p[1], d.p[2]);
  G.scene.add(g);
  drops.set(d.id, { d, g, m, t: Math.random() * 6 });
}
function removeDrop(id) { const x = drops.get(id); if (!x) return; G.scene.remove(x.g); x.g.traverse((o) => { if (o.geometry && o.geometry !== dropGeo) o.geometry.dispose(); }); drops.delete(id); }
export function clearDrops() { for (const id of [...drops.keys()]) removeDrop(id); }
export function nearestDrop() {
  let best = null, bd = PICK;
  for (const x of drops.values()) { const dd = Math.hypot(x.d.p[0] - ME.pos[0], x.d.p[1] - ME.pos[1] - 0.6, x.d.p[2] - ME.pos[2]); if (dd < bd) { bd = dd; best = x.d; } }
  return best;
}
export const atLocker = () => Math.hypot(ME.pos[0] - TEST.locker.p[0], ME.pos[2] - TEST.locker.p[2]) < TEST.locker.r;
export function barTick(dt) {
  for (const x of drops.values()) { x.t += dt; x.m.rotation.y += dt * 1.6; x.m.position.y = Math.sin(x.t * 2.2) * 0.12; }
  bridge();
  const k = `${W.slot}|${W.cur}|${W.item}`;
  if (k !== shownK) { shownK = k; render(); } // scroll / Q / G changed what's highlighted
}
