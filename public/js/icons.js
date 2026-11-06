// Weapon pictures for the hotbar: each weapon (with your skin, wrap and hat) rendered side-on into a small
// transparent image, cached until something about it changes.
import * as THREE from 'three';
import { buildWeapon, freeTree, lookSkin } from './models.js';
import { withEnv, trackGlb, onGlb, whenGlb } from './glbkit.js';

const IW = 160, IH = 96;
let r = null, scene = null, cam = null;
const cache = new Map();
const box = new THREE.Box3(), size = new THREE.Vector3(), center = new THREE.Vector3();

function init() {
  r = new THREE.WebGLRenderer({ antialias: false, alpha: true, preserveDrawingBuffer: true });
  r.setPixelRatio(1);
  r.setSize(IW, IH, false);
  r.setClearColor(0x000000, 0);
  scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a6a8a, 3.2));
  const sun = new THREE.DirectionalLight(0xffffff, 2.0);
  sun.position.set(0.4, 1, 1.2);
  scene.add(sun);
  cam = new THREE.PerspectiveCamera(28, IW / IH, 0.01, 50);
}

// a picture drawn with the code model because its Blender one wasn't here yet remembers which model: when that lands
// (glbkit onGlb) only those pictures are dropped and redrawn, not every icon in the game
const deps = new Map(); // glb id -> cache keys drawn without it
const keyWait = new Map(); // cache key -> the models it was drawn without
onGlb((id) => { const ks = deps.get(id); if (!ks) return; deps.delete(id); for (const k of ks) { cache.delete(k); keyWait.delete(k); } });
let lastWait = null; // the models the last picture was missing (iconWaits)
export const iconWaits = () => lastWait;
// draw a picture and say which models it was missing: [url, ids or null]
export function drawIcon(fn) { lastWait = null; const u = fn(); return [u, lastWait]; }
// the loading placeholder: a pink wireframe cube turning over cyan scanlines + static (an animated SVG, so it moves
// in any <img> with no per-frame work). 'jfph' marks it for tests
export const PLACEHOLDER = placeholder();
export const isPlaceholder = (u) => u === PLACEHOLDER;
// an <img> that keeps itself right: fn() draws it now (maybe the placeholder) and again when a model it waited on lands.
// redraws queue up and go a few per frame, so twenty models landing at once don't stall a frame
const redrawQ = [];
let redrawOn = false;
export function liveIcon(img, fn) {
  const u = fn();
  if (u) img.src = u;
  const w = lastWait;
  if (w) whenGlb(w, () => { redrawQ.push([img, fn]); if (!redrawOn) { redrawOn = true; requestAnimationFrame(pumpRedraw); } });
  return u;
}
function pumpRedraw() {
  const t0 = performance.now();
  while (redrawQ.length && performance.now() - t0 < 8) { const [img, fn] = redrawQ.shift(); if (img.isConnected) liveIcon(img, fn); }
  redrawOn = redrawQ.length > 0;
  if (redrawOn) requestAnimationFrame(pumpRedraw);
}
// (soft) drop only pictures that were waiting on a model; all = everything
export function clearIcons(all = false) { if (all) { cache.clear(); deps.clear(); keyWait.clear(); return; } for (const ks of deps.values()) for (const k of ks) { cache.delete(k); keyWait.delete(k); } }
function keep(key, url, t) {
  lastWait = t.missing.size ? [...t.missing] : null;
  if (t.pending) return PLACEHOLDER; // still coming: don't draw the old model at all
  for (const id of t.missing) { if (!deps.has(id)) deps.set(id, new Set()); deps.get(id).add(key); }
  if (lastWait) keyWait.set(key, lastWait);
  cache.set(key, url);
  return url;
}

export function weaponIcon(id, skin) {
  skin = lookSkin(id, skin); // (the spoon look in gun game: the icon cache must see it)
  const key = id + '|' + (Array.isArray(skin) ? skin.join(',') : '');
  lastWait = keyWait.get(key) || null;
  if (cache.has(key)) return cache.get(key);
  try {
    if (!r) init();
    const [g, t] = trackGlb(() => buildWeapon(id, skin));
    if (t.pending) { freeTree(g); return keep(key, '', t); }
    const holder = new THREE.Group();
    const flat = id === 'cards' || id === 'reverse' || g.userData.faceOn; // flat things look at you, everything else side-on
    g.rotation.y = flat ? 0 : -Math.PI / 2; // muzzle to the right, like an inventory picture
    holder.add(g);
    if (id === 'akimbo') { // Lefty & Righty: the pair, one behind the other and a bit up, muzzles crossed like a poster
      const g2 = buildWeapon(id, skin); g2.rotation.set(0.32, Math.PI / 2, 0); g2.position.set(0.24, 0, -0.06); g.rotation.x = 0.32; holder.add(g2);
    }
    holder.rotation.x = flat ? -0.15 : 0.28; // a little from above
    holder.rotation.z = flat ? 0 : 0.06;
    scene.add(holder);
    holder.updateMatrixWorld(true);
    box.setFromObject(holder);
    box.getSize(size); box.getCenter(center);
    holder.position.sub(center);
    const fit = Math.max(size.x / cam.aspect, size.y) * 1.04;
    cam.position.set(0, 0, fit / (2 * Math.tan((cam.fov * Math.PI) / 360)) + size.z / 2);
    cam.lookAt(0, 0, 0);
    withEnv(r, holder, () => r.render(scene, cam)); // (its own reflections, or chrome is black)
    const url = r.domElement.toDataURL('image/png');
    scene.remove(holder);
    freeTree(holder); // only the picture is kept
    return keep(key, url, t);
  } catch (e) {
    console.warn('icon', id, e);
    return '';
  }
}

// any model as a picture, lit like the weapons (Plant & Defuse gear in the buy menu). build() makes it, key caches it
export function objIcon(key, build) {
  lastWait = keyWait.get(key) || null;
  if (cache.has(key)) return cache.get(key);
  try {
    if (!r) init();
    const holder = new THREE.Group();
    const [obj, t] = trackGlb(build);
    if (t.pending) { freeTree(obj); return keep(key, '', t); }
    holder.add(obj);
    scene.add(holder);
    holder.updateMatrixWorld(true);
    box.setFromObject(holder);
    box.getSize(size); box.getCenter(center);
    holder.position.sub(center);
    const fit = Math.max(size.x / cam.aspect, size.y) * 1.06;
    cam.position.set(0, 0, fit / (2 * Math.tan((cam.fov * Math.PI) / 360)) + size.z / 2);
    cam.lookAt(0, 0, 0);
    withEnv(r, holder, () => r.render(scene, cam)); // (its own reflections, or chrome is black)
    const url = r.domElement.toDataURL('image/png');
    scene.remove(holder);
    freeTree(holder);
    return keep(key, url, t);
  } catch (e) {
    console.warn('icon', key, e);
    return '';
  }
}

function placeholder() {
  const cube = 'M56.9 55.2L56.9 77.3M56.9 14.7L56.9 36.8M103.1 55.2L103.1 77.3M103.1 14.7L103.1 36.8M56.9 55.2L56.9 14.7M56.9 77.3L56.9 36.8M103.1 55.2L103.1 14.7M103.1 77.3L103.1 36.8M56.9 55.2L103.1 55.2M56.9 77.3L103.1 77.3M56.9 14.7L103.1 14.7M56.9 36.8L103.1 36.8;M60.1 53.8L54.1 75.8M60.1 13.4L54.1 35.3M105.9 56.7L99.9 78.6M105.9 16.2L99.9 38.2M60.1 53.8L60.1 13.4M54.1 75.8L54.1 35.3M105.9 56.7L105.9 16.2M99.9 78.6L99.9 38.2M60.1 53.8L105.9 56.7M54.1 75.8L99.9 78.6M60.1 13.4L105.9 16.2M54.1 35.3L99.9 38.2;M63.7 52.7L51.8 74.1M63.7 12.2L51.8 33.6M108.2 58.4L96.3 79.8M108.2 17.9L96.3 39.3M63.7 52.7L63.7 12.2M51.8 74.1L51.8 33.6M108.2 58.4L108.2 17.9M96.3 79.8L96.3 39.3M63.7 52.7L108.2 58.4M51.8 74.1L96.3 79.8M63.7 12.2L108.2 17.9M51.8 33.6L96.3 39.3;M67.5 51.8L49.9 72.2M67.5 11.3L49.9 31.7M110.1 60.3L92.5 80.7M110.1 19.8L92.5 40.2M67.5 51.8L67.5 11.3M49.9 72.2L49.9 31.7M110.1 60.3L110.1 19.8M92.5 80.7L92.5 40.2M67.5 51.8L110.1 60.3M49.9 72.2L92.5 80.7M67.5 11.3L110.1 19.8M49.9 31.7L92.5 40.2;M71.6 51.1L48.5 70.3M71.6 10.7L48.5 29.8M111.5 62.2L88.4 81.3M111.5 21.7L88.4 40.9M71.6 51.1L71.6 10.7M48.5 70.3L48.5 29.8M111.5 62.2L111.5 21.7M88.4 81.3L88.4 40.9M71.6 51.1L111.5 62.2M48.5 70.3L88.4 81.3M71.6 10.7L111.5 21.7M48.5 29.8L88.4 40.9;M75.7 50.7L47.7 68.3M75.7 10.3L47.7 27.8M112.3 64.2L84.3 81.7M112.3 23.7L84.3 41.3M75.7 50.7L75.7 10.3M47.7 68.3L47.7 27.8M112.3 64.2L112.3 23.7M84.3 81.7L84.3 41.3M75.7 50.7L112.3 64.2M47.7 68.3L84.3 81.7M75.7 10.3L112.3 23.7M47.7 27.8L84.3 41.3;M80.0 50.6L47.4 66.2M80.0 10.1L47.4 25.8M112.6 66.2L80.0 81.9M112.6 25.8L80.0 41.4M80.0 50.6L80.0 10.1M47.4 66.2L47.4 25.8M112.6 66.2L112.6 25.8M80.0 81.9L80.0 41.4M80.0 50.6L112.6 66.2M47.4 66.2L80.0 81.9M80.0 10.1L112.6 25.8M47.4 25.8L80.0 41.4;M84.3 50.7L47.7 64.2M84.3 10.3L47.7 23.7M112.3 68.3L75.7 81.7M112.3 27.8L75.7 41.3M84.3 50.7L84.3 10.3M47.7 64.2L47.7 23.7M112.3 68.3L112.3 27.8M75.7 81.7L75.7 41.3M84.3 50.7L112.3 68.3M47.7 64.2L75.7 81.7M84.3 10.3L112.3 27.8M47.7 23.7L75.7 41.3;M88.4 51.1L48.5 62.2M88.4 10.7L48.5 21.7M111.5 70.3L71.6 81.3M111.5 29.8L71.6 40.9M88.4 51.1L88.4 10.7M48.5 62.2L48.5 21.7M111.5 70.3L111.5 29.8M71.6 81.3L71.6 40.9M88.4 51.1L111.5 70.3M48.5 62.2L71.6 81.3M88.4 10.7L111.5 29.8M48.5 21.7L71.6 40.9;M92.5 51.8L49.9 60.3M92.5 11.3L49.9 19.8M110.1 72.2L67.5 80.7M110.1 31.7L67.5 40.2M92.5 51.8L92.5 11.3M49.9 60.3L49.9 19.8M110.1 72.2L110.1 31.7M67.5 80.7L67.5 40.2M92.5 51.8L110.1 72.2M49.9 60.3L67.5 80.7M92.5 11.3L110.1 31.7M49.9 19.8L67.5 40.2;M96.3 52.7L51.8 58.4M96.3 12.2L51.8 17.9M108.2 74.1L63.7 79.8M108.2 33.6L63.7 39.3M96.3 52.7L96.3 12.2M51.8 58.4L51.8 17.9M108.2 74.1L108.2 33.6M63.7 79.8L63.7 39.3M96.3 52.7L108.2 74.1M51.8 58.4L63.7 79.8M96.3 12.2L108.2 33.6M51.8 17.9L63.7 39.3;M99.9 53.8L54.1 56.7M99.9 13.4L54.1 16.2M105.9 75.8L60.1 78.6M105.9 35.3L60.1 38.2M99.9 53.8L99.9 13.4M54.1 56.7L54.1 16.2M105.9 75.8L105.9 35.3M60.1 78.6L60.1 38.2M99.9 53.8L105.9 75.8M54.1 56.7L60.1 78.6M99.9 13.4L105.9 35.3M54.1 16.2L60.1 38.2;M103.1 55.2L56.9 55.2M103.1 14.7L56.9 14.7M103.1 77.3L56.9 77.3M103.1 36.8L56.9 36.8M103.1 55.2L103.1 14.7M56.9 55.2L56.9 14.7M103.1 77.3L103.1 36.8M56.9 77.3L56.9 36.8M103.1 55.2L103.1 77.3M56.9 55.2L56.9 77.3M103.1 14.7L103.1 36.8M56.9 14.7L56.9 36.8';
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 96" width="160" height="96"><!--jfph-->`
    + `<g opacity="0.85"><rect x="0" y="0" width="160" height="2" fill="#4fd8ff" opacity="0.5"><animate attributeName="y" values="8;88;8" dur="1.6s" repeatCount="indefinite"/></rect>`
    + `<rect x="40" y="30" width="22" height="2" fill="#fff" opacity="0.6"><animate attributeName="x" values="30;96;52;110;30" dur="0.7s" calcMode="discrete" repeatCount="indefinite"/><animate attributeName="y" values="26;64;40;70;26" dur="0.7s" calcMode="discrete" repeatCount="indefinite"/></rect>`
    + `<rect x="96" y="60" width="12" height="3" fill="#ff4fd8"><animate attributeName="x" values="100;44;118;60;100" dur="0.9s" calcMode="discrete" repeatCount="indefinite"/><animate attributeName="y" values="62;30;50;24;62" dur="0.9s" calcMode="discrete" repeatCount="indefinite"/></rect></g>`
    + `<path fill="none" stroke="#000" stroke-width="5" stroke-linejoin="round" d=""><animate attributeName="d" values="${cube}" dur="1.2s" repeatCount="indefinite"/></path>`
    + `<path fill="none" stroke="#ff4fd8" stroke-width="2.2" stroke-linejoin="round" d=""><animate attributeName="d" values="${cube}" dur="1.2s" repeatCount="indefinite"/></path>`
    + `<g fill="#ffe14d"><rect x="58" y="88" width="6" height="4"><animate attributeName="opacity" values="1;0.2;0.2" dur="0.9s" repeatCount="indefinite"/></rect><rect x="77" y="88" width="6" height="4"><animate attributeName="opacity" values="0.2;1;0.2" dur="0.9s" repeatCount="indefinite"/></rect><rect x="96" y="88" width="6" height="4"><animate attributeName="opacity" values="0.2;0.2;1" dur="0.9s" repeatCount="indefinite"/></rect></g></svg>`;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}

// ------------------------------------------------------------ the icon studio: killstreaks + items as real 3D models
// one light rig for all of them (warm key from the top left, cool fill, a rim light in the icon's own colour from
// behind), a 3/4 view from a little above with a slight tilt, then the zine treatment: a thick black outline and a
// hard offset shadow in the accent colour (like the menu panels). drawn at 2x and scaled down so it stays crisp small.
// build() returns the model (or null = no model: the caller falls back to its 2D drawing). cached like every icon.
let sr = null, sScene = null, sCam = null, sRim = null, sBad = false;
function initStudio() {
  sr = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
  sr.setPixelRatio(1);
  sr.setClearColor(0x000000, 0);
  sr.toneMapping = THREE.ACESFilmicToneMapping; sr.toneMappingExposure = 1.15;
  sScene = new THREE.Scene();
  sScene.add(new THREE.HemisphereLight(0xffffff, 0x4a2a5a, 1.7));
  const key = new THREE.DirectionalLight(0xfff2e0, 2.6); key.position.set(-1.2, 1.8, 2); sScene.add(key);
  const fill = new THREE.DirectionalLight(0x9fdcff, 0.8); fill.position.set(1.6, 0.2, 1); sScene.add(fill);
  sRim = new THREE.DirectionalLight(0xff4fd8, 3.2); sRim.position.set(1, 0.8, -2.2); sScene.add(sRim);
  sCam = new THREE.PerspectiveCamera(22, 1, 0.01, 80);
}
const SIL = document.createElement('canvas');
function silhouette(src, color) { // the picture's shape, filled with one colour
  SIL.width = src.width; SIL.height = src.height;
  const x = SIL.getContext('2d');
  x.clearRect(0, 0, SIL.width, SIL.height); x.globalCompositeOperation = 'source-over'; x.drawImage(src, 0, 0);
  x.globalCompositeOperation = 'source-in'; x.fillStyle = color; x.fillRect(0, 0, SIL.width, SIL.height);
  return SIL;
}
export function studioIcon(key, build, o = {}) {
  lastWait = keyWait.get(key) || null;
  if (cache.has(key)) return cache.get(key);
  if (sBad) return '';
  if (!sr) try { initStudio(); } catch (e) { console.warn('icon studio: no WebGL', e); sBad = true; return ''; } // the 2D drawings from now on
  try {
    const W = (o.w || 96) * 2, H = (o.h || 96) * 2, accent = o.accent || '#4fd8ff';
    const [obj, t] = trackGlb(build);
    if (t.pending || !obj) { if (obj) freeTree(obj); return keep(key, '', t); }
    const spin = new THREE.Group(), tilt = new THREE.Group();
    spin.add(obj); tilt.add(spin);
    spin.rotation.y = o.yaw ?? 2.55; // 3/4 from the front (models face -z, the camera looks from +z)
    tilt.rotation.set(o.pitch ?? 0.42, 0, o.roll ?? -0.08); // a bit from above, a bit off level (jank)
    sScene.add(tilt);
    tilt.updateMatrixWorld(true);
    box.setFromObject(tilt); box.getSize(size); box.getCenter(center);
    tilt.position.sub(center);
    sr.setSize(W, H, false);
    sCam.aspect = W / H; sCam.updateProjectionMatrix();
    const fit = Math.max(size.x / sCam.aspect, size.y) * (o.pad || 1.14); // room for the outline + shadow
    sCam.position.set(0, 0, fit / (2 * Math.tan((sCam.fov * Math.PI) / 360)) + size.z / 2);
    sCam.lookAt(0, 0, 0);
    sRim.color.set(o.rim || accent);
    withEnv(sr, tilt, () => sr.render(sScene, sCam));
    sScene.remove(tilt);
    freeTree(tilt);
    const out = document.createElement('canvas'); out.width = W; out.height = H;
    const x = out.getContext('2d'), src = sr.domElement, ol = Math.max(3, Math.round(W / 48)), sh = Math.round(W / 22);
    const ring = (img, dx, dy, r) => { for (let a = 0; a < 16; a++) x.drawImage(img, dx + Math.round(Math.cos(a * Math.PI / 8) * r), dy + Math.round(Math.sin(a * Math.PI / 8) * r)); };
    ring(silhouette(src, accent), sh * 0.6, sh, ol); // the hard offset shadow (the outline's shape, pushed down right)
    ring(silhouette(src, '#000'), 0, 0, ol); // the ink outline
    x.drawImage(src, 0, 0);
    const fin = document.createElement('canvas'); fin.width = W / 2; fin.height = H / 2; // 2x down to size: crisp, not jaggy
    const f = fin.getContext('2d'); f.imageSmoothingEnabled = true; f.imageSmoothingQuality = 'high';
    f.drawImage(out, 0, 0, W / 2, H / 2);
    return keep(key, fin.toDataURL('image/png'), t);
  } catch (e) {
    console.warn('studio icon', key, e); // just this one falls back to its drawing (not cached: tried again next time)
    return '';
  }
}
// what draws the 3D killstreak / item pictures (itemicons.js registers them: it knows the models)
const pics3d = { streak: null, item: null };
export function set3dPics(streak, item) { pics3d.streak = streak; pics3d.item = item; }

// item pictures, drawn: the fallback when the 3D ones can't be rendered (no WebGL)
const itemCache = new Map();
export function itemIcon(id, skin) {
  if (pics3d.item) { const u = pics3d.item(id, skin); if (u) return u; } // the 3D one (itemicons.js), or its loading cube
  return itemIcon2d(id);
}
export function itemIcon2d(id) {
  if (itemCache.has(id)) return itemCache.get(id);
  const c = document.createElement('canvas'); c.width = 96; c.height = 60;
  const x = c.getContext('2d');
  x.lineWidth = 3; x.strokeStyle = '#000';
  const circle = (cx, cy, r, fill) => { x.beginPath(); x.arc(cx, cy, r, 0, Math.PI * 2); x.fillStyle = fill; x.fill(); x.stroke(); };
  if (id === 'frag') {
    x.beginPath(); x.ellipse(48, 34, 16, 20, 0, 0, Math.PI * 2); x.fillStyle = '#5a6a2a'; x.fill(); x.stroke();
    x.fillStyle = '#3a4a1a'; for (let i = -1; i <= 1; i++) x.fillRect(34, 32 + i * 9, 28, 2);
    x.fillStyle = '#444'; x.fillRect(42, 10, 12, 8); x.strokeRect(42, 10, 12, 8);
    x.beginPath(); x.arc(62, 12, 6, 0, Math.PI * 2); x.strokeStyle = '#ddd'; x.stroke();
  } else if (id === 'medkit') {
    x.fillStyle = '#ffffff'; x.fillRect(24, 14, 48, 36); x.strokeRect(24, 14, 48, 36);
    x.fillStyle = '#ff3030'; x.fillRect(43, 20, 10, 24); x.fillRect(36, 27, 24, 10);
    x.fillStyle = '#ddd'; x.fillRect(40, 8, 16, 6); x.strokeRect(40, 8, 16, 6);
  } else if (id === 'bubble') {
    x.beginPath(); x.arc(48, 32, 22, 0, Math.PI * 2); x.fillStyle = 'rgba(79,216,255,0.35)'; x.fill(); x.strokeStyle = '#4fd8ff'; x.lineWidth = 4; x.stroke();
    x.beginPath(); x.arc(40, 24, 7, Math.PI, Math.PI * 1.6); x.strokeStyle = '#fff'; x.lineWidth = 3; x.stroke();
  } else if (id === 'wand') { // bubble wand: pink stick + ring, three rainbow soap bubbles drifting off it
    for (const [w, c] of [[6, '#000'], [3, '#ff7ad8']]) { x.lineWidth = w; x.strokeStyle = c; x.beginPath(); x.moveTo(14, 56); x.lineTo(30, 36); x.stroke(); x.beginPath(); x.arc(36, 28, 10, 0, Math.PI * 2); x.stroke(); }
    for (const [cx, cy, r] of [[64, 22, 13], [84, 40, 8], [56, 47, 6]]) {
      const g = x.createLinearGradient(cx - r, cy - r, cx + r, cy + r);
      g.addColorStop(0, '#ff7ad8'); g.addColorStop(0.35, '#ffe66b'); g.addColorStop(0.65, '#7dffb0'); g.addColorStop(1, '#6bb8ff');
      x.beginPath(); x.arc(cx, cy, r, 0, Math.PI * 2); x.fillStyle = 'rgba(200,240,255,0.22)'; x.fill(); x.lineWidth = 2.5; x.strokeStyle = g; x.stroke();
      x.beginPath(); x.arc(cx - r * 0.35, cy - r * 0.35, r * 0.3, Math.PI, Math.PI * 1.6); x.strokeStyle = '#fff'; x.lineWidth = 2; x.stroke();
    }
  } else if (id === 'duck') {
    circle(44, 38, 16, '#ffd23b'); circle(58, 22, 10, '#ffd23b');
    x.fillStyle = '#ff7a1a'; x.beginPath(); x.moveTo(66, 22); x.lineTo(78, 25); x.lineTo(66, 28); x.fill();
    x.fillStyle = '#000'; x.fillRect(58, 18, 3, 3);
  } else if (id === 'smoke') {
    x.fillStyle = '#9aa0a8'; x.fillRect(40, 26, 16, 26); x.strokeRect(40, 26, 16, 26);
    for (const [cx, cy, r] of [[40, 18, 9], [52, 14, 10], [62, 20, 8], [30, 22, 7]]) circle(cx, cy, r, '#d8dce0');
  } else if (id === 'popper') { // (the hotbar normally shows the real model; these are the fallbacks)
    x.beginPath(); x.moveTo(26, 50); x.lineTo(58, 14); x.lineTo(70, 30); x.closePath(); x.fillStyle = '#ff6bd0'; x.fill(); x.stroke();
    for (const [cx, cy, c] of [[66, 10, '#ffe14d'], [78, 18, '#4fd8ff'], [74, 6, '#7dff4f'], [84, 28, '#ffffff']]) { x.fillStyle = c; x.fillRect(cx, cy, 5, 5); }
  } else if (id === 'reverse') {
    x.fillStyle = '#e8262b'; x.fillRect(32, 6, 32, 48); x.strokeRect(32, 6, 32, 48);
    x.strokeStyle = '#fff'; x.lineWidth = 4;
    x.beginPath(); x.arc(48, 30, 10, Math.PI * 0.9, Math.PI * 1.9); x.stroke();
    x.beginPath(); x.arc(48, 30, 10, -Math.PI * 0.1, Math.PI * 0.9); x.stroke();
  } else if (id === 'camera') { // instant camera: cream body, black top, a big lens, the print hanging out
    x.fillStyle = '#f8f5ec'; x.fillRect(36, 44, 26, 14); x.strokeRect(36, 44, 26, 14); x.fillStyle = '#6fb8ff'; x.fillRect(40, 46, 18, 9);
    x.fillStyle = '#f3eee2'; x.fillRect(22, 18, 52, 30); x.strokeRect(22, 18, 52, 30);
    x.fillStyle = '#2c2c33'; x.fillRect(22, 10, 52, 12); x.strokeRect(22, 10, 52, 12);
    circle(48, 32, 11, '#1a1c28'); circle(48, 32, 5, '#3a4a7a');
    x.fillStyle = '#ff2d6a'; x.beginPath(); x.arc(66, 26, 4, 0, Math.PI * 2); x.fill(); x.stroke();
    x.fillStyle = '#fff6d8'; x.fillRect(27, 13, 14, 6);
  } else if (id === 'quiz') { // a calculator with a sum on it
    x.save(); x.translate(48, 30); x.rotate(-0.18);
    x.fillStyle = '#23263a'; x.fillRect(-17, -26, 34, 52); x.strokeRect(-17, -26, 34, 52);
    x.fillStyle = '#b9c8a2'; x.fillRect(-13, -22, 26, 12);
    x.fillStyle = '#1d2418'; x.font = 'bold 9px monospace'; x.fillText('7x8=?', -12, -13);
    for (let r = 0; r < 4; r++) for (let k = 0; k < 3; k++) { x.fillStyle = r === 3 && k === 2 ? '#ff8a2a' : '#e3e6ee'; x.fillRect(-13 + k * 9, -6 + r * 8, 7, 6); }
    x.restore();
    x.fillStyle = '#ffe14d'; x.font = 'bold 20px sans-serif'; x.fillText('?', 74, 22); x.fillText('?', 12, 50);
  } else if (id === 'nvg') { // night vision goggles: two olive tubes, green lenses
    x.fillStyle = '#ff4fd8'; x.fillRect(10, 22, 76, 6); x.strokeRect(10, 22, 76, 6);
    x.fillStyle = '#48503a'; x.fillRect(28, 18, 40, 16); x.strokeRect(28, 18, 40, 16);
    for (const cx of [34, 62]) { circle(cx, 38, 14, '#3a4030'); circle(cx, 38, 9, '#39ff14'); x.fillStyle = '#d8ffd0'; x.fillRect(cx - 4, 33, 3, 3); }
  }
  const url = c.toDataURL();
  itemCache.set(id, url);
  return url;
}

// killstreak pictures (3D from itemicons.js; these drawings are the fallback)
const streakCache = new Map();
export function streakIcon(id) {
  if (pics3d.streak) { const u = pics3d.streak(id); if (u) return u; } // the 3D one (or its loading placeholder)
  return streakIcon2d(id);
}
// the old drawings: only if the 3D one can't be made (no WebGL, model missing)
export function streakIcon2d(id) {
  if (streakCache.has(id)) return streakCache.get(id);
  const c = document.createElement('canvas'); c.width = 64; c.height = 64;
  const x = c.getContext('2d');
  x.lineWidth = 3; x.strokeStyle = '#000';
  const circle = (cx, cy, r, fill) => { x.beginPath(); x.arc(cx, cy, r, 0, Math.PI * 2); x.fillStyle = fill; x.fill(); x.stroke(); };
  if (id === 'moonboots') {
    circle(44, 18, 11, '#ffe14d'); circle(50, 14, 9, '#1a1030'); // crescent moon
    x.fillStyle = '#b0b8ff'; x.fillRect(16, 26, 14, 22); x.fillRect(16, 42, 26, 10); x.strokeRect(16, 26, 14, 22); x.strokeRect(16, 42, 26, 10);
    x.fillStyle = '#fff'; x.fillRect(14, 52, 30, 4);
  } else if (id === 'chickenstrike') {
    x.strokeStyle = '#ff3030'; x.lineWidth = 3; x.beginPath(); x.arc(32, 36, 20, 0, Math.PI * 2); x.stroke();
    x.beginPath(); x.moveTo(32, 12); x.lineTo(32, 60); x.moveTo(8, 36); x.lineTo(56, 36); x.stroke();
    x.strokeStyle = '#000'; circle(32, 18, 9, '#ffe14d'); x.fillStyle = '#ff7a1a'; x.fillRect(38, 17, 7, 4); x.fillStyle = '#ff3030'; x.fillRect(29, 6, 6, 5);
  } else if (id === 'scythe') {
    x.fillStyle = '#6a4a2a'; x.save(); x.translate(32, 32); x.rotate(-0.6); x.fillRect(-3, -26, 6, 52); x.strokeRect(-3, -26, 6, 52); x.restore();
    x.beginPath(); x.moveTo(14, 12); x.quadraticCurveTo(40, 0, 58, 22); x.quadraticCurveTo(36, 12, 20, 22); x.closePath(); x.fillStyle = '#3ee6c8'; x.fill(); x.stroke();
  } else if (id === 'spinbot') {
    x.strokeStyle = '#ff4fd8'; x.lineWidth = 4;
    for (let i = 0; i < 3; i++) { x.beginPath(); x.arc(32, 32, 22, i * 2.1, i * 2.1 + 1.4); x.stroke(); }
    x.strokeStyle = '#000'; x.fillStyle = '#111'; x.fillRect(16, 26, 13, 8); x.fillRect(35, 26, 13, 8); x.fillRect(29, 28, 6, 2); // shades
    x.fillStyle = '#7dff4f'; x.font = 'bold 11px monospace'; x.fillText('AIM', 22, 50);
  } else if (id === 'satellite') {
    x.fillStyle = '#4fa8ff'; x.fillRect(4, 24, 18, 12); x.fillRect(42, 24, 18, 12); x.strokeRect(4, 24, 18, 12); x.strokeRect(42, 24, 18, 12);
    circle(32, 30, 9, '#cccccc');
    x.strokeStyle = '#ffe14d'; x.lineWidth = 2; for (const r of [10, 16, 22]) { x.beginPath(); x.arc(32, 60, r, -2.4, -0.7); x.stroke(); }
  } else if (id === 'overdrive') {
    // the rig's rocket fist punching out of the frame: speed lines, a plated forearm, a glowing magenta knuckle strip
    x.lineWidth = 2;
    for (const [y, c] of [[22, '#2ef2ff'], [31, '#ff2bd6'], [40, '#2ef2ff']]) { x.strokeStyle = c; x.beginPath(); x.moveTo(2, y); x.lineTo(15, y); x.stroke(); }
    x.lineWidth = 3; x.strokeStyle = '#000';
    x.fillStyle = '#30363e'; x.beginPath(); x.moveTo(6, 52); x.lineTo(24, 40); x.lineTo(30, 50); x.lineTo(14, 62); x.closePath(); x.fill(); x.stroke(); // forearm
    x.fillStyle = '#a87c24'; x.fillRect(12, 47, 9, 5);
    x.fillStyle = '#58616c'; x.fillRect(22, 14, 30, 30); x.strokeRect(22, 14, 30, 30); // knuckle block
    x.fillStyle = '#30363e';
    for (let i = 0; i < 4; i++) { x.fillRect(51, 15 + i * 7, 8, 6); x.strokeRect(51, 15 + i * 7, 8, 6); } // fingers curled at the front
    x.fillStyle = '#83391b'; x.fillRect(46, 13, 7, 32); x.strokeRect(46, 13, 7, 32); // knuckle plate
    x.fillStyle = '#ff2bd6'; x.fillRect(48, 15, 3, 28); // the glow strip
    x.fillStyle = 'rgba(255,43,214,0.35)'; x.beginPath(); x.arc(56, 29, 12, 0, Math.PI * 2); x.fill();
    x.fillStyle = '#ff1e1e'; x.fillRect(26, 20, 14, 3); // a red tally light on the back of the hand
    x.fillStyle = '#2ef2ff'; x.fillRect(24, 38, 20, 2);
  } else if (id === 'giantduck') {
    circle(32, 34, 24, '#120018'); x.strokeStyle = '#b07dff'; x.lineWidth = 2; x.beginPath(); x.arc(32, 34, 27, 0, Math.PI * 2); x.stroke();
    x.strokeStyle = '#000'; x.lineWidth = 3; circle(28, 38, 11, '#ffd23b'); circle(38, 26, 7, '#ffd23b'); x.fillStyle = '#ff7a1a'; x.fillRect(44, 25, 7, 4);
  } else if (id === 'wreckingball') {
    // riveted steel ball on a chain, hazard stripe, eyes peeking out of the slot
    for (const [w, c] of [[4.5, '#000'], [2, '#b8c4d0']]) { // chain links: dark outline, light steel
      x.lineWidth = w; x.strokeStyle = c;
      for (let i = 0; i < 3; i++) { x.beginPath(); x.ellipse(32, 4 + i * 5.5, i & 1 ? 1.2 : 2.8, 3.4, 0, 0, Math.PI * 2); x.stroke(); }
    }
    x.lineWidth = 2; x.strokeStyle = '#000'; x.fillStyle = '#8a96a4'; x.fillRect(28, 17, 8, 6); x.strokeRect(28, 17, 8, 6);
    x.strokeStyle = '#000'; x.lineWidth = 3; circle(32, 41, 20, '#98a1ab');
    x.save(); x.beginPath(); x.arc(32, 41, 18.5, 0, Math.PI * 2); x.clip();
    for (let i = -3; i < 6; i++) { x.fillStyle = i & 1 ? '#111' : '#ffe14d'; x.beginPath(); x.moveTo(6 + i * 9, 50); x.lineTo(15 + i * 9, 50); x.lineTo(21 + i * 9, 42); x.lineTo(12 + i * 9, 42); x.fill(); }
    x.fillStyle = '#ffffff'; x.globalAlpha = 0.35; x.beginPath(); x.ellipse(24, 30, 6, 3.5, -0.6, 0, Math.PI * 2); x.fill(); x.globalAlpha = 1;
    x.restore();
    x.fillStyle = '#16181c'; x.fillRect(20, 31, 24, 7);
    x.fillStyle = '#fff'; x.fillRect(24, 32, 5, 4); x.fillRect(35, 32, 5, 4);
    x.fillStyle = '#000'; x.fillRect(26, 33, 2, 3); x.fillRect(37, 33, 2, 3);
    x.fillStyle = '#ccd3db'; for (const [rx, ry] of [[15, 41], [49, 41], [32, 58], [20, 54], [44, 54], [20, 27], [44, 27]]) x.fillRect(rx - 1, ry - 1, 2.5, 2.5);
  }
  const url = c.toDataURL();
  streakCache.set(id, url);
  return url;
}
