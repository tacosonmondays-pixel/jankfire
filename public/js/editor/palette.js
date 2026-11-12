// The map editor's CREATIVE MENU (E) and HOTBAR (1-9). The menu: every Blender prop (public/models/p_*.glb), every
// Blender building some map uses and a plain box in every map material, with 3D pictures, in tabs (city, nature,
// industrial, island, vehicles, lights, buildings, boxes, recent) and a search. Click one to load it into the PLOP
// CANNON, or drag it onto a hotbar slot. The hotbar: 1 GRABBY BEAM, 2 PLOP CANNON, 3 YEET RAY, 4 EDIT WAND, 5-9 your
// favourites (kept in this browser).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { studioIcon, liveIcon } from '../icons.js';
import { authored } from '../glbkit.js';
import { ARCH_IDS } from '../archfield.js';
import { TOOLS } from './vm.js';

const $ = (id) => document.getElementById(id);
let tab = 'all', onPick = null, onSlot = null, archOk = () => true, mats = null, built = false;
const list = { props: [], arch: [], box: [] };
const pretty = (id) => id.replace(/^p_/, '').replace(/_/g, ' ');
const CATS = [
  ['all', 'ALL'], ['city', 'CITY', /streetlight|billboard|vending|stall|tent|bench|grave|pot|cardboard|schoolkit|hospkit|numball|deadair|lollipop|cone|barrier|bus/],
  ['nature', 'NATURE', /palm|pine|birch|conifer|bush|fern|saguaro|deadtree|tree|rock|hay|camel|lollipop/],
  ['industrial', 'INDUSTRIAL', /container|pallet|barrel|crate|rack|generator|watertower|acunit|forklift|crane|excavator|dyevat|cone|barrier|pj_shed|quay|cardboard/],
  ['island', 'ISLAND', /palm|pj_|trawler|pier|bollard|hay/],
  ['vehicles', 'VEHICLES', /car|bus|truck|semi|trailer|forklift|excavator|heli|wagon|cart|trawler/],
  ['lights', 'LIGHTS', /light|lamp|neon|billboard/],
  ['arch', 'BUILDINGS'], ['box', 'BOXES'], ['recent', 'RECENT'],
];
const store = (k, v) => { try { if (v === undefined) return JSON.parse(localStorage.getItem(k) || 'null'); localStorage.setItem(k, JSON.stringify(v)); } catch { return null; } return v; };

export function initPalette(o) {
  onPick = o.pick; onSlot = o.slot; mats = o.mats; if (o.archOk) archOk = o.archOk;
  const tabs = $('edTabs'); tabs.innerHTML = '';
  for (const [k, name] of CATS) { const b = document.createElement('button'); b.dataset.tab = k; b.textContent = name; b.onclick = () => { tab = k; draw(); }; tabs.append(b); }
  $('edPalQ').oninput = draw;
  $('edPalQ').onkeydown = (e) => { e.stopPropagation(); if (e.key === 'Escape') { if ($('edPalQ').value) { $('edPalQ').value = ''; draw(); } else togglePalette(false); } };
  $('edPalClose').onclick = () => togglePalette(false);
  initHotbar();
}
export const paletteOpen = () => !$('edPal').classList.contains('hidden');
export function togglePalette(on) {
  const el = $('edPal'), show = on ?? el.classList.contains('hidden');
  el.classList.toggle('hidden', !show);
  document.body.classList.toggle('edMenu', show);
  if (show && !built) { built = true; load(); }
  if (show) setTimeout(() => $('edPalQ').focus(), 30);
  return show;
}
async function load() {
  let ids = [];
  try { ids = (await (await fetch('/models/list')).json()).map((it) => it.id); } catch { /* offline: boxes only */ }
  list.props = ids.filter((id) => id.startsWith('p_')).sort();
  list.arch = [...ARCH_IDS].filter((id) => archOk(id)).sort(); // (only buildings some map has: that's where their walls come from)
  const M = mats() || {};
  list.box = Object.keys(M).filter((k) => M[k] && M[k].mat && !/~$/.test(k)).sort();
  draw(); drawHotbar();
}

// ---- pictures
// the icon studio's camera stops at 80 m: a fort or a rock formation gets shrunk to a 2 m model first (same picture)
function small(obj) {
  if (!obj) return null;
  obj.updateMatrixWorld(true);
  const b = new THREE.Box3().setFromObject(obj), s = b.getSize(new THREE.Vector3()), k = 2 / Math.max(s.x, s.y, s.z, 1e-3), g = new THREE.Group();
  obj.scale.multiplyScalar(k); obj.position.multiplyScalar(k); g.add(obj);
  return g;
}
const archGlb = new Map(); // id -> scene (pictures only; the map draws buildings through archfield.js)
let gl = null;
function archPic(img, id) {
  const key = 'edarch:' + id, make = () => studioIcon(key, () => small(archGlb.get(id) ? archGlb.get(id).clone(true) : null), { accent: '#ffe14d', yaw: 2.3, pitch: 0.5 });
  if (archGlb.has(id)) { img.src = make() || ''; return; }
  gl = gl || new GLTFLoader();
  gl.load('/models/arch/' + id + '.glb', (g) => { archGlb.set(id, g.scene); const u = make(); if (u) img.src = u; }, undefined, () => { img.alt = id; });
}
function boxPic(k) {
  const m = mats()[k], t = m && m.mat && (m.mat.map || m.mat.emissiveMap), c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d');
  x.fillStyle = m && m.mat && m.mat.color ? '#' + m.mat.color.getHexString() : '#888'; x.fillRect(0, 0, 64, 64);
  try { if (t && t.image) { x.imageSmoothingEnabled = false; const p = x.createPattern(t.image, 'repeat'); x.save(); x.scale(2, 2); x.fillStyle = p; x.globalCompositeOperation = 'multiply'; x.fillRect(0, 0, 32, 32); x.restore(); } } catch { /* a texture that isn't a canvas yet */ }
  x.strokeStyle = '#000'; x.lineWidth = 4; x.strokeRect(2, 2, 60, 60);
  return c.toDataURL();
}
// the picture of a kind:id into an <img> (the menu's tiles, the hotbar)
export function thumbInto(img, kind, id) {
  if (kind === 'props') liveIcon(img, () => studioIcon('edprop:' + id, () => { const a = authored(id); return a ? small(a.obj) : null; }, { accent: '#ff4fd8' }));
  else if (kind === 'arch') archPic(img, id);
  else img.src = boxPic(id);
}
function toolPic(t) { // the hotbar's tools: a chunky little tool in its colour, its head drawn on
  const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d'), col = '#' + new THREE.Color(TOOLS[t].col).getHexString();
  x.lineJoin = 'round'; x.lineWidth = 5; x.strokeStyle = '#000';
  const shape = () => { x.beginPath(); x.moveTo(10, 26); x.lineTo(40, 22); x.lineTo(40, 40); x.lineTo(26, 40); x.lineTo(22, 54); x.lineTo(12, 54); x.lineTo(14, 40); x.lineTo(10, 40); x.closePath(); };
  x.save(); x.translate(3, 3); shape(); x.fillStyle = '#ff4fd8'; x.fill(); x.restore();
  shape(); x.fillStyle = '#3a1850'; x.fill(); x.stroke();
  x.fillStyle = col; x.strokeStyle = '#000'; x.lineWidth = 3;
  if (t === 'grab') for (const y of [20, 31, 42]) { x.beginPath(); x.moveTo(40, y); x.lineTo(56, y - 4); x.lineTo(56, y + 2); x.closePath(); x.fill(); x.stroke(); }
  if (t === 'plop') { x.beginPath(); x.moveTo(40, 24); x.lineTo(58, 14); x.lineTo(58, 50); x.lineTo(40, 40); x.closePath(); x.fill(); x.stroke(); }
  if (t === 'yeet') { for (const y of [22, 38]) { x.fillRect(40, y, 16, 5); x.strokeRect(40, y, 16, 5); } x.beginPath(); x.arc(58, 30, 5, 0, 7); x.fill(); x.stroke(); }
  if (t === 'wand') { x.beginPath(); x.moveTo(40, 31); x.lineTo(50, 22); x.lineTo(60, 31); x.lineTo(50, 40); x.closePath(); x.fill(); x.stroke(); }
  x.beginPath(); x.arc(24, 31, 5, 0, 7); x.fillStyle = col; x.fill(); x.stroke();
  return c.toDataURL();
}

let io = null;
function lazy(img, fn) { // draw a picture only once its tile scrolls into view (dozens of studio renders at once would stall)
  io = io || new IntersectionObserver((es) => { for (const e of es) if (e.isIntersecting) { io.unobserve(e.target); const f = e.target._pic; e.target._pic = null; if (f) f(); } }, { root: $('edPalGrid'), rootMargin: '160px' });
  img._pic = fn; io.observe(img);
}
function entries() {
  const q = $('edPalQ').value.trim().toLowerCase(), ok = (id) => !q || pretty(id).includes(q) || id.includes(q);
  if (tab === 'recent') return (store('jfEdRecent') || []).filter((it) => ok(it.id));
  if (tab === 'arch') return list.arch.filter(ok).map((id) => ({ kind: 'arch', id }));
  if (tab === 'box') return list.box.filter(ok).map((id) => ({ kind: 'box', id }));
  const cat = CATS.find((c) => c[0] === tab), re = cat && cat[2];
  const props = list.props.filter((id) => ok(id) && (!re || re.test(id.replace(/^p_/, '')))).map((id) => ({ kind: 'props', id }));
  return tab === 'all' && q ? [...props, ...list.arch.filter(ok).map((id) => ({ kind: 'arch', id })), ...list.box.filter(ok).map((id) => ({ kind: 'box', id }))] : props;
}
function draw() {
  for (const b of document.querySelectorAll('#edTabs button')) b.classList.toggle('on', b.dataset.tab === tab);
  const grid = $('edPalGrid'), es = entries();
  grid.innerHTML = '';
  if (!es.length) { grid.innerHTML = '<p class="edPalNone">' + (tab === 'recent' ? 'nothing yet. plop something.' : built && !list.props.length ? 'loading the model list...' : 'nothing called that. try "car" or "crate"') + '</p>'; return; }
  for (const it of es) {
    const d = document.createElement('button'), img = document.createElement('img'), s = document.createElement('span');
    d.className = 'edTile'; d.title = pretty(it.id) + ' (click: load the plop cannon, drag: onto the hotbar)'; s.textContent = pretty(it.id); img.alt = ''; img.draggable = false;
    d.append(img, s); grid.append(d);
    d.draggable = true;
    d.ondragstart = (e) => { e.dataTransfer.setData('text/plain', it.kind + ':' + it.id); e.dataTransfer.effectAllowed = 'copy'; document.body.classList.add('edDragging'); };
    d.ondragend = () => document.body.classList.remove('edDragging');
    d.onclick = () => onPick(it.kind, it.id);
    if (it.kind === 'box') img.src = boxPic(it.id); else lazy(img, () => thumbInto(img, it.kind, it.id));
  }
}
export function addRecent(it) { const r = (store('jfEdRecent') || []).filter((x) => !(x.kind === it.kind && x.id === it.id)); r.unshift({ kind: it.kind, id: it.id }); store('jfEdRecent', r.slice(0, 30)); }
export const solidOn = () => $('edSolid').checked;

// ---- the hotbar
const TOOL_SLOTS = ['grab', 'plop', 'yeet', 'wand'];
let fav = [null, null, null, null, null], active = 0;
const DEFAULT_FAV = [{ kind: 'props', id: 'p_crate' }, { kind: 'props', id: 'p_barrel' }, { kind: 'props', id: 'p_car_sedan' }, { kind: 'props', id: 'p_palm' }, { kind: 'props', id: 'p_cone' }];
function initHotbar() {
  const f = store('jfEdHot');
  fav = Array.isArray(f) && f.length === 5 ? f.map((x) => (x && typeof x.kind === 'string' && typeof x.id === 'string' ? x : null)) : DEFAULT_FAV.slice();
  const el = $('edHot'); el.innerHTML = '';
  for (let i = 0; i < 9; i++) {
    const s = document.createElement('div'); s.className = 'edSlot'; s.dataset.i = i;
    s.innerHTML = '<b>' + (i + 1) + '</b><img alt="" draggable="false"><span></span>';
    s.onclick = () => onSlot(i);
    if (i === 1 || i >= 4) {
      s.ondragover = (e) => { e.preventDefault(); s.classList.add('drop'); };
      s.ondragleave = () => s.classList.remove('drop');
      s.ondrop = (e) => { e.preventDefault(); s.classList.remove('drop'); const [kind, ...rest] = (e.dataTransfer.getData('text/plain') || '').split(':'); const id = rest.join(':'); if (!['props', 'arch', 'box'].includes(kind) || !id) return; dropOn(i, { kind, id }); };
    }
    el.append(s);
  }
  drawHotbar();
}
// put an item on slot i (2 = straight into the plop cannon, 5-9 = a favourite)
export function dropOn(i, it) {
  if (i >= 4) { fav[i - 4] = it; store('jfEdHot', fav); }
  drawHotbar(); onSlot(i, it);
}
export const slotItem = (i) => (i >= 4 ? fav[i - 4] : null);
export const slotTool = (i) => TOOL_SLOTS[i] || 'plop';
export function setActiveSlot(i, cannon) { active = i; if (cannon !== undefined) cannonItem = cannon; drawHotbar(); }
let cannonItem = null;
export function drawHotbar() {
  for (const s of document.querySelectorAll('#edHot .edSlot')) {
    const i = +s.dataset.i, img = s.querySelector('img'), lab = s.querySelector('span');
    s.classList.toggle('on', i === active);
    if (i < 4) {
      const t = TOOL_SLOTS[i]; if (!img.src) img.src = toolPic(t); lab.textContent = TOOLS[t].name.toLowerCase();
      if (i === 1 && cannonItem) { lab.textContent = 'plop: ' + pretty(cannonItem.id); }
    } else {
      const it = fav[i - 4]; s.classList.toggle('empty', !it);
      if (!it) { img.removeAttribute('src'); lab.textContent = 'drag here'; continue; }
      if (img.dataset.k !== it.kind + ':' + it.id) { img.dataset.k = it.kind + ':' + it.id; img.removeAttribute('src'); if (built || it.kind !== 'box') thumbInto(img, it.kind, it.id); }
      lab.textContent = pretty(it.id);
    }
  }
}
export function modelBounds(id) { // the model's size in its own frame (a model no map uses: its one collision box is this)
  const a = authored(id);
  if (!a) return null;
  const mb = a.meta && a.meta.box;
  if (Array.isArray(mb) && mb.length === 2) return { lo: [...mb[0]], hi: [...mb[1]] };
  a.obj.updateMatrixWorld(true);
  const b = new THREE.Box3(), t = new THREE.Box3(), lod1 = (o) => { for (let p = o; p; p = p.parent) if (String(p.userData.name ?? p.name).replace(/\.\d+$/, '') === 'lod1') return true; return false; };
  a.obj.traverse((o) => { if (o.isMesh && o.geometry && !lod1(o)) { o.geometry.computeBoundingBox(); t.copy(o.geometry.boundingBox).applyMatrix4(o.matrixWorld); b.union(t); } });
  return b.isEmpty() ? null : { lo: b.min.toArray(), hi: b.max.toArray() };
}
