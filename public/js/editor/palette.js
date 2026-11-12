// The map editor's palette: every Blender prop (public/models/p_*.glb), every Blender building (models/arch) and a plain
// box in every map material, with pictures. Picking one hands its id to the editor (editor.js place()), which puts it
// where you aim and picks it up.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { studioIcon, liveIcon } from '../icons.js';
import { authored } from '../glbkit.js';
import { ARCH_IDS } from '../archfield.js';

const $ = (id) => document.getElementById(id);
let tab = 'props', onPick = null, archOk = () => true, list = { props: [], arch: [], box: [] }, mats = null, built = false;
const pretty = (id) => id.replace(/^p_/, '').replace(/_/g, ' ');

export function initPalette(o) {
  onPick = o.pick; mats = o.mats; if (o.archOk) archOk = o.archOk;
  for (const b of document.querySelectorAll('#edPal [data-tab]')) b.onclick = () => { tab = b.dataset.tab; draw(); };
  $('edPalQ').oninput = draw;
  $('edPalQ').onkeydown = (e) => { e.stopPropagation(); if (e.key === 'Escape') { $('edPalQ').value = ''; draw(); $('edPalQ').blur(); } };
}
export function togglePalette(on) {
  const el = $('edPal'), show = on ?? el.classList.contains('hidden');
  el.classList.toggle('hidden', !show);
  if (show && !built) { built = true; load(); }
  return show;
}
async function load() {
  let ids = [];
  try { ids = (await (await fetch('/models/list')).json()).map((it) => it.id); } catch { /* offline: boxes only */ }
  list.props = ids.filter((id) => id.startsWith('p_')).sort();
  list.arch = [...ARCH_IDS].filter((id) => archOk(id)).sort(); // (only buildings some map has: that's where their walls come from)
  const M = mats() || {};
  list.box = Object.keys(M).filter((k) => M[k] && M[k].mat && !/~$/.test(k)).sort();
  draw();
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
const archGlb = new Map(); // id -> scene (thumbnails only; the map draws buildings through archfield.js)
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
let io = null;
function lazy(img, fn) { // draw a picture only once its tile scrolls into view (66 studio renders at once would stall)
  io = io || new IntersectionObserver((es) => { for (const e of es) if (e.isIntersecting) { io.unobserve(e.target); const f = e.target._pic; e.target._pic = null; if (f) f(); } }, { root: $('edPalGrid'), rootMargin: '120px' });
  img._pic = fn; io.observe(img);
}

function draw() {
  for (const b of document.querySelectorAll('#edPal [data-tab]')) b.classList.toggle('on', b.dataset.tab === tab);
  const q = $('edPalQ').value.trim().toLowerCase(), grid = $('edPalGrid');
  grid.innerHTML = '';
  const ids = list[tab === 'props' ? 'props' : tab === 'arch' ? 'arch' : 'box'].filter((id) => !q || pretty(id).includes(q) || id.includes(q));
  if (!ids.length) { grid.innerHTML = '<p class="edPalNone">' + (built && !list.props.length && tab === 'props' ? 'loading the model list...' : 'nothing called that. try "car" or "crate"') + '</p>'; return; }
  for (const id of ids) {
    const d = document.createElement('button'), img = document.createElement('img'), s = document.createElement('span');
    d.className = 'edTile'; d.title = pretty(id); s.textContent = pretty(id); img.alt = '';
    d.append(img, s); grid.append(d);
    d.onclick = () => onPick(tab, id);
    if (tab === 'props') lazy(img, () => liveIcon(img, () => studioIcon('edprop:' + id, () => { const a = authored(id); return a ? small(a.obj) : null; }, { accent: '#ff4fd8' })));
    else if (tab === 'arch') lazy(img, () => archPic(img, id));
    else img.src = boxPic(id);
  }
}
export const paletteOpen = () => !$('edPal').classList.contains('hidden');
export const solidOn = () => $('edSolid').checked;
// the model's size in its own frame (a new prop with no map using it: its one collision box is this). the box the model
// was built against (meta.box) if it says, else its near model's bounds (not the far lod1 copy), like propfield.js fits it
const isLod1 = (o) => { for (let p = o; p; p = p.parent) if (String(p.userData.name ?? p.name).replace(/\.\d+$/, '') === 'lod1') return true; return false; };
export function modelBounds(id) {
  const a = authored(id);
  if (!a) return null;
  const mb = a.meta && a.meta.box;
  if (Array.isArray(mb) && mb.length === 2) return { lo: [...mb[0]], hi: [...mb[1]] };
  a.obj.updateMatrixWorld(true);
  const b = new THREE.Box3(), t = new THREE.Box3();
  a.obj.traverse((o) => { if (o.isMesh && o.geometry && !isLod1(o)) { o.geometry.computeBoundingBox(); t.copy(o.geometry.boundingBox).applyMatrix4(o.matrixWorld); b.union(t); } });
  return b.isEmpty() ? null : { lo: b.min.toArray(), hi: b.max.toArray() };
}
