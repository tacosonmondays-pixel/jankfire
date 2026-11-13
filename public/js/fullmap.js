// THE BIG MAP (M, every mode) + PINGS. M opens a comic panel with the whole map from above (the minimap's painter,
// north up): you, your side, Plant & Defuse sites + the bomb (when your side would know), and in Jank Royale / Battle
// Island the zone, the next circle, the blimp's line and the supply crates. The mouse comes free while it's open (like
// the backpack), WASD still walks. Click the map, or press the ping key anywhere (where you look), to drop a ping: it
// shows on your side's big map, their minimap and in the world (a beam + a sticker with the distance), for 8 s.
// The server only relays pings to your side (server/pings.js); solo modes see their own.
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { ME } from './player.js';
import { RP } from './replay.js';
import { K } from './keys.js';
import { W, isFriend } from './weapons.js';
import { mapExtent, paintBoxes, mmLayers } from './minimap.js';
import { brState } from './royale.js';
import { MAPS, BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { TEAMS } from '/shared/modes.js';
import { BR, blimpAt, zoneAt } from '/shared/royale.js';
import { PING, inPingBox } from '/shared/pings.js';
import { topdownFor } from './topdown.js'; // the royale maps' real top-down pictures

const CSS = `
#fmWrap { position: fixed; inset: 0; display: none; z-index: 40; pointer-events: none; font-family: var(--font); }
#fmPanel { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%) rotate(-0.6deg); pointer-events: auto; background: rgba(18,8,24,0.92); border: 4px solid #ff4fd8; box-shadow: 8px 8px 0 #4fd8ff; padding: 30px 12px 10px; color: #fff; max-width: calc(100vw - 28px); box-sizing: border-box; }
#fmTag { position: absolute; left: -10px; top: -16px; background: #ffe14d; color: #000; border: 3px solid #000; box-shadow: 4px 4px 0 #ff4fd8; font: bold 20px var(--font); padding: 1px 10px; transform: rotate(-2.5deg); letter-spacing: 2px; white-space: nowrap; }
#fmName { position: absolute; left: 190px; right: 54px; top: 4px; font: bold 16px var(--font); color: #4fd8ff; letter-spacing: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-shadow: 2px 2px 0 #000; }
#fmX { position: absolute; right: 8px; top: 3px; width: 34px; height: 24px; background: #fff; color: #000; border: 3px solid #000; box-shadow: 3px 3px 0 #ff4fd8; font: bold 16px/16px var(--font); cursor: pointer; padding: 0; transform: rotate(2deg); }
#fmX:active { transform: translate(2px, 2px) rotate(2deg); box-shadow: 1px 1px 0 #ff4fd8; }
#fmCvBox { position: relative; }
#fmZoom { position: absolute; right: 8px; bottom: 8px; display: flex; flex-direction: column; gap: 6px; }
#fmZoom button { width: 38px; height: 30px; padding: 0; background: #fff; color: #000; border: 3px solid #000; box-shadow: 3px 3px 0 #ff4fd8; font: bold 18px/18px var(--font); cursor: pointer; }
#fmZoom button[data-z="fit"] { font-size: 11px; background: #ffe14d; }
#fmZoom button:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 #ff4fd8; }
#fmZoomK { position: absolute; left: 8px; bottom: 8px; font: bold 13px var(--font); color: #ffe14d; text-shadow: 2px 2px 0 #000; pointer-events: none; }
#fmCv { display: block; border: 3px solid #000; background: #0c0614; cursor: crosshair; touch-action: none; }
#fmFoot { display: flex; flex-wrap: wrap; gap: 4px 14px; margin-top: 7px; font-size: 13px; color: #ddd; align-items: center; }
#fmFoot kbd { background: #ffe14d; color: #000; border: 2px solid #000; padding: 0 5px; font: bold 12px var(--font); box-shadow: 2px 2px 0 #000; }
#fmFoot i { display: inline-block; width: 10px; height: 10px; border: 2px solid #000; margin-right: 4px; vertical-align: -1px; font-style: normal; }
#fmFoot .lg { color: #fff; }
#fmPins { position: absolute; inset: 0; pointer-events: none; overflow: hidden; font-family: var(--font); }
.fmPin { position: absolute; transform: translate(-50%, -100%); text-align: center; white-space: nowrap; color: #fff; }
.fmPin .d { width: 18px; height: 18px; margin: 0 auto; background: var(--c); border: 3px solid #000; box-shadow: 3px 3px 0 #000; transform: rotate(45deg); }
.fmPin b { display: block; font: bold 13px var(--font); color: var(--c); text-shadow: 2px 2px 0 #000, -1px -1px 0 #000; }
.fmPin small { display: block; font: bold 12px var(--font); color: #fff; text-shadow: 1px 1px 0 #000, -1px -1px 0 #000; margin-bottom: 3px; }
.fmPin.pop { animation: fmPop 0.45s ease-out; }
.fmPin.edge .d { transform: rotate(45deg) scale(0.8); }
@keyframes fmPop { 0% { transform: translate(-50%, -100%) scale(2.2) rotate(-12deg); } 60% { transform: translate(-50%, -100%) scale(0.9) rotate(3deg); } 100% { transform: translate(-50%, -100%) scale(1); } }
body.fmOpen #mmWrap, body.fmOpen #brHud { visibility: hidden; } /* (the big map covers the small ones) */
html.touch #fmX { width: 46px; height: 34px; font-size: 20px; }
@media (max-width: 560px) { #fmTag { font-size: 16px; } #fmName { left: 150px; font-size: 13px; } #fmFoot { font-size: 11px; } #fmFoot .keys { display: none; } }
`;

// extras that plug into the big map (mappencil.js): layers drawn under the pings, a pointer gesture on the map (down
// returns true to take it), and things to add once the panel exists
export const FMX = { layers: [], down: null, move: null, up: null, built: [] };
const FM = { open: false, base: null, baseFor: '', ext: null, ppm: 1, drawT: 0, cssW: 0, cssH: 0, view: null, lock: null, built: false };
const pings = new Map(); // id -> { id, by, p, t, col, name, el, beam }
let wrap = null, cv = null, pinLayer = null;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const PAL = ['#4fd8ff', '#39ff14', '#ff4fd8', '#ff9f1a', '#b07dff'];
export const pingCol = (by) => (by === G.myId ? '#ffe14d' : PAL[Math.abs(by | 0) % PAL.length]);
const nameOf = (id) => (id === G.myId ? 'YOU' : (G.names.get(id) || {}).name || '???');
const mapOn = () => G.joined && !G.story && !!MAPS[G.cfg.map];
const ally = (r) => isFriend(r) || ((G.mode === 'coop' || G.game === 'zombies') && !r.bot);

function build() {
  if (FM.built) return;
  FM.built = true;
  const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
  wrap = document.createElement('div'); wrap.id = 'fmWrap';
  wrap.innerHTML = '<div id="fmPanel"><div id="fmTag">THE BIG MAP</div><div id="fmName"></div><button id="fmX" title="close">✕</button><div id="fmCvBox"><canvas id="fmCv"></canvas><div id="fmZoom"><button data-z="in" title="zoom in">+</button><button data-z="out" title="zoom out">−</button><button data-z="fit" title="the whole map">FIT</button></div><div id="fmZoomK"></div></div><div id="fmFoot"></div></div>';
  document.body.appendChild(wrap);
  pinLayer = document.createElement('div'); pinLayer.id = 'fmPins';
  ($('hud') || document.body).appendChild(pinLayer);
  cv = $('fmCv');
  cv.addEventListener('click', (e) => { e.stopPropagation(); if (FM.took || FM.panned) { FM.took = false; FM.panned = false; return; } mapClick(e); });
  // zoom + pan: the wheel zooms at the cursor, a drag pans (right / middle button always; left when it isn't the pencil's)
  cv.addEventListener('wheel', (e) => { e.preventDefault(); e.stopPropagation(); zoomAt(e.deltaY < 0 ? 1.3 : 1 / 1.3, e.clientX, e.clientY); }, { passive: false });
  cv.addEventListener('pointerdown', (e) => { FM.pan = null; FM.panned = false; if (e.button === 1 || e.button === 2 || (e.button === 0 && !(FMX.wants && FMX.wants(e)))) { FM.pan = { x: e.clientX, y: e.clientY, moved: e.button !== 0 }; try { cv.setPointerCapture(e.pointerId); } catch { /* fine */ } } }, true);
  cv.addEventListener('pointermove', (e) => { const P = FM.pan; if (!P) return; if (!P.moved && Math.hypot(e.clientX - P.x, e.clientY - P.y) < 7) return; P.moved = true; FM.panned = true; panBy(e.clientX - P.x, e.clientY - P.y); P.x = e.clientX; P.y = e.clientY; });
  for (const t of ['pointerup', 'pointercancel']) cv.addEventListener(t, () => { FM.pan = null; });
  $('fmZoom').addEventListener('click', (e) => { e.stopPropagation(); const b = e.target.closest('button'); if (!b) return; const r = cv.getBoundingClientRect(); if (b.dataset.z === 'fit') { FM.zoom = 1; clampView(); } else zoomAt(b.dataset.z === 'in' ? 1.5 : 1 / 1.5, r.left + r.width / 2, r.top + r.height / 2); sfx.click(); });
  cv.addEventListener('pointerdown', (e) => { if (FMX.down && FM.open && FMX.down(e, ...fmWorld(e.clientX, e.clientY))) { FM.took = true; e.preventDefault(); try { cv.setPointerCapture(e.pointerId); } catch { /* fine */ } } else FM.took = false; });
  cv.addEventListener('pointermove', (e) => { if (FM.took && FMX.move) FMX.move(e, ...fmWorld(e.clientX, e.clientY)); });
  for (const t of ['pointerup', 'pointercancel']) cv.addEventListener(t, (e) => { if (FM.took && FMX.up) FMX.up(e, t === 'pointercancel'); });
  for (const f of FMX.built) f($('fmPanel'));
  $('fmX').addEventListener('click', (e) => { e.stopPropagation(); closeMap(true); });
  addEventListener('resize', () => { if (FM.open) size(); });
}

// ------------------------------------------------------------ the picture
function bake(id) {
  const map = MAPS[id], royale = !!(brState().on && map.royale);
  FM.ext = mapExtent(map);
  const w = FM.ext[2] - FM.ext[0], h = FM.ext[3] - FM.ext[1];
  FM.ppm = Math.min(6, 1400 / Math.max(w, h));
  const c = document.createElement('canvas'); c.width = Math.ceil(w * FM.ppm); c.height = Math.ceil(h * FM.ppm);
  const x = c.getContext('2d');
  x.fillStyle = royale ? '#2a1a10' : '#0c0614'; x.fillRect(0, 0, c.width, c.height);
  paintBoxes(x, map, (wx, wz) => [(wx - FM.ext[0]) * FM.ppm, (wz - FM.ext[1]) * FM.ppm], Math.max(c.width, c.height), royale ? { style: 'royale' } : {});
  if (map.bounds && !royale) { const b = map.bounds; x.strokeStyle = '#ff4fd8'; x.lineWidth = Math.max(2, FM.ppm * 0.6); x.setLineDash([FM.ppm * 3, FM.ppm * 2]); x.strokeRect((b[0] - FM.ext[0]) * FM.ppm, (b[1] - FM.ext[1]) * FM.ppm, (b[2] - b[0]) * FM.ppm, (b[3] - b[1]) * FM.ppm); x.setLineDash([]); }
  FM.base = c; FM.baseFor = id + (royale ? ':br' : '');
  FM.zoom = 1; FM.cx = (FM.ext[0] + FM.ext[2]) / 2; FM.cz = (FM.ext[1] + FM.ext[3]) / 2; // a new map: the whole of it
}
function size() {
  const e = FM.ext, w = e[2] - e[0], h = e[3] - e[1];
  const small = innerWidth < 560, maxW = Math.min(innerWidth - (small ? 46 : 80), 1100), maxH = innerHeight - (small ? 96 : 130);
  const k = Math.max(0.05, Math.min(maxW / w, maxH / h));
  FM.cssW = Math.max(120, Math.round(w * k)); FM.cssH = Math.max(90, Math.round(h * k));
  const dpr = Math.min(2, devicePixelRatio || 1);
  cv.width = Math.round(FM.cssW * dpr); cv.height = Math.round(FM.cssH * dpr);
  cv.style.width = FM.cssW + 'px'; cv.style.height = FM.cssH + 'px';
  FM.view = { s: (FM.cssW / w) * dpr, dpr };
}
// zoom + pan: the window shows ext / zoom metres round (cx, cz), kept inside the map
const vw = () => (FM.ext[2] - FM.ext[0]) / (FM.zoom || 1), vh = () => (FM.ext[3] - FM.ext[1]) / (FM.zoom || 1);
const vx0 = () => (FM.cx ?? (FM.ext[0] + FM.ext[2]) / 2) - vw() / 2, vz0 = () => (FM.cz ?? (FM.ext[1] + FM.ext[3]) / 2) - vh() / 2;
const toCv = (wx, wz) => { const k = FM.view.s * (FM.zoom || 1); return [(wx - vx0()) * k, (wz - vz0()) * k]; };
function clampView() {
  FM.zoom = Math.max(1, Math.min(8, FM.zoom || 1));
  const e = FM.ext, hw = vw() / 2, hh = vh() / 2;
  FM.cx = Math.max(e[0] + hw, Math.min(e[2] - hw, FM.cx ?? (e[0] + e[2]) / 2)); FM.cz = Math.max(e[1] + hh, Math.min(e[3] - hh, FM.cz ?? (e[1] + e[3]) / 2));
  if (cv && $('fmZoomK')) $('fmZoomK').textContent = FM.zoom > 1.01 ? `x${FM.zoom.toFixed(1)} · drag to move` : '';
  FM.drawT = 0;
}
function zoomAt(f, cx, cy) { if (!FM.ext) return; const a = fmWorld(cx, cy); FM.zoom = (FM.zoom || 1) * f; clampView(); const b = fmWorld(cx, cy); FM.cx += a[0] - b[0]; FM.cz += a[1] - b[1]; clampView(); }
function panBy(dx, dy) { const r = cv.getBoundingClientRect(); FM.cx -= dx * vw() / r.width; FM.cz -= dy * vh() / r.height; clampView(); }
export const fmView = () => ({ zoom: FM.zoom || 1, cx: FM.cx, cz: FM.cz, ext: FM.ext }); // (tests)
export function fmZoomTo(z, wx, wz) { if (!FM.ext) return; FM.zoom = z; FM.cx = wx; FM.cz = wz; clampView(); } // (spyglass.js / tests)

function foot() {
  const team = G.myTeam && TEAMS[G.myTeam] ? TEAMS[G.myTeam].color : '#4fd8ff';
  const pk = K.label('ping'), mk = K.label('map');
  $('fmFoot').innerHTML = `<span class="lg"><i style="background:#ffe14d"></i>you</span><span class="lg"><i style="background:${team}"></i>your side</span><span class="lg"><i style="background:#ff4fd8;transform:rotate(45deg)"></i>pings (8 s)</span>`
    + `<span class="keys">click the map: ping${pk ? ` · <kbd>${esc(pk)}</kbd> ping where you look` : ''} · <kbd>${esc(mk || 'M')}</kbd> close</span>`;
  $('fmName').textContent = (MAPS[G.cfg.map] ? MAPS[G.cfg.map].name.toUpperCase() : '') + (pingSide() ? ' · pings go to your side' : ' · pings are just for you');
}
const pingSide = () => !!(G.myTeam || G.mode === 'coop' || G.game === 'zombies' || [...G.remotes.values()].some((r) => ally(r) && !r.bot));

function drawMap(now) {
  const map = MAPS[G.cfg.map], R = brState(), royale = !!(R.on && map.royale);
  if (FM.baseFor !== G.cfg.map + (royale ? ':br' : '')) { bake(G.cfg.map); size(); }
  const x = cv.getContext('2d'), S = FM.view.s, dpr = FM.view.dpr, Wd = cv.width, Ht = cv.height;
  x.setTransform(1, 0, 0, 1, 0, 0);
  x.imageSmoothingEnabled = false;
  x.fillStyle = '#0c0614'; x.fillRect(0, 0, Wd, Ht);
  const td = topdownFor(G.cfg.map); // royale maps: the real picture from above (with its POI names) instead of the painted boxes
  if (td) { const a = toCv(td.ext[0], td.ext[1]), b = toCv(td.ext[2], td.ext[3]); x.imageSmoothingEnabled = true; x.drawImage(td.img, a[0], a[1], b[0] - a[0], b[1] - a[1]); x.imageSmoothingEnabled = false; }
  else { const a = toCv(FM.ext[0], FM.ext[1]), b = toCv(FM.ext[2], FM.ext[3]); x.drawImage(FM.base, a[0], a[1], b[0] - a[0], b[1] - a[1]); }
  // a comic grid: letters across, numbers down (so "pinged C4" means something)
  const ext = FM.ext, span = Math.max(ext[2] - ext[0], ext[3] - ext[1]), cell = [10, 16, 20, 25, 32, 40, 50, 64, 80, 100].find((c) => span / c <= 9) || 120;
  x.strokeStyle = 'rgba(255,255,255,0.10)'; x.lineWidth = 1;
  x.font = `bold ${Math.round(11 * dpr)}px sans-serif`; x.fillStyle = 'rgba(255,225,77,0.75)'; x.textAlign = 'left'; x.textBaseline = 'top';
  for (let i = 0, gx = ext[0]; gx < ext[2]; gx += cell, i++) { const p = toCv(gx, 0)[0]; x.beginPath(); x.moveTo(p, 0); x.lineTo(p, Ht); x.stroke(); x.fillText(String.fromCharCode(65 + (i % 26)), p + 3 * dpr, 3 * dpr); }
  for (let i = 1, gz = ext[1]; gz < ext[3]; gz += cell, i++) { const p = toCv(0, gz)[1]; x.beginPath(); x.moveTo(0, p); x.lineTo(Wd, p); x.stroke(); x.fillText(String(i), 3 * dpr, p + (i > 1 ? 3 : 17) * dpr); }
  FM.cell = cell;
  const dot = (p, col, r = 5) => { x.fillStyle = col; x.strokeStyle = '#000'; x.lineWidth = 2.5 * dpr; x.beginPath(); x.arc(p[0], p[1], r * dpr, 0, 7); x.stroke(); x.fill(); };
  const label = (p, text, col, dy = -10) => { x.font = `bold ${Math.round(12 * dpr)}px sans-serif`; x.textAlign = 'center'; x.textBaseline = 'bottom'; x.lineWidth = 3 * dpr; x.strokeStyle = '#000'; x.strokeText(text, p[0], p[1] + dy * dpr); x.fillStyle = col; x.fillText(text, p[0], p[1] + dy * dpr); };
  // jank royale / battle island: the zone, the next circle, the blimp's line + the blimp, crates, POI names
  if (R.on) {
    const zn = zoneAt(R.zone, now + (G.offset || 0));
    if (zn) {
      const [cx, cz] = toCv(zn.c[0], zn.c[1]);
      x.save(); x.fillStyle = 'rgba(110,40,220,0.42)'; x.beginPath(); x.rect(0, 0, Wd, Ht); x.arc(cx, cz, zn.r * S, 0, Math.PI * 2, true); x.fill('evenodd'); x.restore();
      x.strokeStyle = '#b07dff'; x.lineWidth = 3 * dpr; x.beginPath(); x.arc(cx, cz, zn.r * S, 0, Math.PI * 2); x.stroke();
      if (zn.next) { const [nx, nz] = toCv(zn.next.c[0], zn.next.c[1]); x.strokeStyle = '#fff'; x.lineWidth = 2 * dpr; x.setLineDash([8 * dpr, 6 * dpr]); x.beginPath(); x.arc(nx, nz, Math.max(2, zn.next.r * S), 0, Math.PI * 2); x.stroke(); x.setLineDash([]); }
    }
    if (R.path && R.phase !== 'live') {
      const a = toCv(R.path.a[0], R.path.a[1]), b = toCv(R.path.a[0] + R.path.d[0] * BR.blimp.len * 2, R.path.a[1] + R.path.d[1] * BR.blimp.len * 2);
      x.strokeStyle = '#000'; x.lineWidth = 6 * dpr; x.beginPath(); x.moveTo(a[0], a[1]); x.lineTo(b[0], b[1]); x.stroke();
      x.strokeStyle = '#ffe14d'; x.lineWidth = 3 * dpr; x.setLineDash([10 * dpr, 7 * dpr]); x.beginPath(); x.moveTo(a[0], a[1]); x.lineTo(b[0], b[1]); x.stroke(); x.setLineDash([]);
      const bp = blimpAt(R.path, now + (G.offset || 0)), [bx, bz] = toCv(bp[0], bp[2]);
      x.save(); x.translate(bx, bz); x.rotate(Math.atan2(R.path.d[1], R.path.d[0]));
      x.fillStyle = '#ff4fd8'; x.strokeStyle = '#000'; x.lineWidth = 2.5 * dpr; x.beginPath(); x.ellipse(0, 0, 11 * dpr, 6 * dpr, 0, 0, 7); x.fill(); x.stroke(); x.restore();
      label([bx, bz], 'BLIMP', '#ff4fd8', -9);
    }
    const pois = map.royale && map.royale.pois;
    if (pois && !(td && td.names)) for (const d of pois) { const p = toCv((d.rect[0] + d.rect[2]) / 2, (d.rect[1] + d.rect[3]) / 2); label(p, d.name.toUpperCase(), d.color || '#fff', 6); }
    for (const c of R.crates.values()) { const [px, pz] = toCv(c.x, c.z); x.fillStyle = '#ffe14d'; x.strokeStyle = '#000'; x.lineWidth = 2 * dpr; x.fillRect(px - 6 * dpr, pz - 6 * dpr, 12 * dpr, 12 * dpr); x.strokeRect(px - 6 * dpr, pz - 6 * dpr, 12 * dpr, 12 * dpr); }
  }
  // Plant & Defuse: the sites, and the bomb when your side would know where it is (the minimap's rules)
  const bomb = G.round && G.round.game === 'bomb' && G.round.bomb;
  if (bomb && map.sites) {
    x.font = `bold ${Math.round(15 * dpr)}px sans-serif`; x.textAlign = 'center'; x.textBaseline = 'middle';
    for (const s of map.sites) {
      const p = toCv((s.min[0] + s.max[0]) / 2, (s.min[2] + s.max[2]) / 2), hot = bomb.ph === 'planted' && bomb.site === s.id, h = 11 * dpr;
      x.fillStyle = hot ? '#ff3030' : '#ffe14d'; x.strokeStyle = '#000'; x.lineWidth = 3 * dpr; x.fillRect(p[0] - h, p[1] - h, h * 2, h * 2); x.strokeRect(p[0] - h, p[1] - h, h * 2, h * 2);
      x.fillStyle = '#000'; x.fillText(s.id, p[0], p[1] + dpr);
    }
    const att = G.myTeam && G.myTeam === bomb.att, bp = bomb.p || (att && bomb.drop);
    if (bp && Math.sin(now / 110) > -0.3) { const p = toCv(bp[0], bp[2]); dot(p, bomb.p ? '#ff3030' : '#ffb04f', 6.5); label(p, 'BOMB', '#ff3030'); }
  }
  // people: your side with names; enemies only on a spy satellite (it's a map, not a wallhack)
  const sat = now < (G.satUntil || 0);
  for (const r of G.remotes.values()) {
    if (!r.alive || (r.bot && r.name === 'Dummy' && G.mode !== 'training') || (R.on && R.blimp.has(r.id))) continue;
    const p = toCv(r.pos[0], r.pos[2]);
    if (ally(r)) { const col = TEAMS[r.team] ? TEAMS[r.team].color : '#4fd8ff'; dot(p, col); label(p, (G.names.get(r.id) || {}).name || '', col); if (bomb && bomb.carrier === r.id) { x.strokeStyle = '#ffb04f'; x.lineWidth = 2.5 * dpr; x.beginPath(); x.arc(p[0], p[1], 9 * dpr, 0, 7); x.stroke(); } }
    else if (sat) dot(p, '#ff3030', 4.5);
  }
  for (const f of FMX.layers) f(x, toCv, now, dpr); // pencil strokes (mappencil.js)
  // pings
  for (const g of pings.values()) drawPingMark(x, toCv(g.p[0], g.p[2]), g, now, dpr, true);
  // you: the arrow (in the blimp: you're the blimp)
  if (ME.alive && !(R.on && R.me && R.me.inBlimp)) {
    const [px, pz] = toCv(ME.pos[0], ME.pos[2]);
    x.save(); x.translate(px, pz); x.rotate(-(ME.yaw || 0)); x.scale(dpr * 1.5, dpr * 1.5);
    x.fillStyle = '#ffe14d'; x.strokeStyle = '#000'; x.lineWidth = 2;
    x.beginPath(); x.moveTo(0, -7); x.lineTo(5, 5); x.lineTo(0, 2); x.lineTo(-5, 5); x.closePath(); x.stroke(); x.fill(); x.restore();
  }
}
// a ping on a 2D map: a diamond with a black edge, a ring that pops out when it's new, fading at the end. k = px scale
function drawPingMark(x, p, g, now, k, big) {
  const age = now - g.t, left = PING.life - age;
  if (left <= 0) return;
  x.save();
  x.globalAlpha = Math.min(1, left / 1200);
  if (age < 900) { const f = age / 900; x.strokeStyle = g.col; x.lineWidth = (big ? 3 : 2) * k * (1 - f) + 0.5; x.beginPath(); x.arc(p[0], p[1], (big ? 8 + f * 26 : 4 + f * 12) * k, 0, 7); x.stroke(); }
  const r = (big ? 8 : 5) * k;
  x.translate(p[0], p[1]); x.rotate(Math.PI / 4);
  x.fillStyle = '#000'; x.fillRect(-r + 1.5 * k, -r + 1.5 * k, r * 2, r * 2); // the hard shadow
  x.fillStyle = g.col; x.strokeStyle = '#000'; x.lineWidth = (big ? 2.5 : 1.8) * k; x.fillRect(-r, -r, r * 2, r * 2); x.strokeRect(-r, -r, r * 2, r * 2);
  x.restore();
  if (big) { x.save(); x.globalAlpha = Math.min(1, left / 1200); x.font = `bold ${Math.round(11 * k)}px sans-serif`; x.textAlign = 'center'; x.textBaseline = 'top'; x.lineWidth = 3 * k; x.strokeStyle = '#000'; x.strokeText(g.name, p[0], p[1] + r + 4 * k); x.fillStyle = g.col; x.fillText(g.name, p[0], p[1] + r + 4 * k); x.restore(); }
}
// the HUD minimap + royale's zone map draw pings too (minimap.js / royale.js call their layers)
mmLayers.push((x, at, now, px) => {
  for (const g of pings.values()) {
    let p = at(g.p[0], g.p[2]);
    p = [Math.max(6, Math.min(px - 6, p[0])), Math.max(6, Math.min(px - 6, p[1]))]; // far ones sit on the rim
    drawPingMark(x, p, g, now, 1, false);
  }
});

// ------------------------------------------------------------ open / close
function openMap() {
  if (FM.open || !mapOn()) return;
  build();
  FM.open = true;
  if (FM.baseFor !== G.cfg.map + (brState().on && MAPS[G.cfg.map].royale ? ':br' : '')) bake(G.cfg.map);
  size(); foot();
  wrap.style.display = 'block'; document.body.classList.add('fmOpen');
  if (document.pointerLockElement) document.exitPointerLock(); // a real cursor (main.js doesn't pause for this)
  W.held = false; W.aimHeld = false;
  FM.drawT = 0;
  sfx.mapOpen();
}
function closeMap(relock) {
  if (!FM.open) return;
  FM.open = false;
  wrap.style.display = 'none'; document.body.classList.remove('fmOpen');
  if (relock && FM.lock && G.joined && $('menu') && $('menu').classList.contains('hidden') && !document.pointerLockElement && !document.documentElement.classList.contains('touch')) FM.lock();
  sfx.mapClose();
}
export const fmOpen = () => FM.open;
export function fmClose() { closeMap(false); }

// ------------------------------------------------------------ pings
function groundAt(x, z) {
  const top = PING.y[1] - 10, h = raycast([x, top, z], [0, -1, 0], top - PING.y[0], BOXES);
  return h ? top - h.t : 0;
}
function sendPing(x, y, z) {
  if (!mapOn()) return false;
  if (!inPingBox(MAPS[G.cfg.map], x, z)) { hud.msg('THAT\'S OFF THE MAP, BESTIE', 1.1); sfx.empty(); return false; }
  y = Math.max(PING.y[0], Math.min(PING.y[1], y));
  net.send({ t: 'mping', x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10, z: Math.round(z * 10) / 10 });
  return true;
}
// a point on the map canvas -> world x, z
export function fmWorld(cx, cy) {
  const r = cv.getBoundingClientRect(); // (the panel is tilted a hair: close enough)
  const fx = (cx - r.left) / r.width, fz = (cy - r.top) / r.height;
  return [vx0() + fx * vw(), vz0() + fz * vh()];
}
function mapClick(e) {
  if (!FM.open || !FM.view) return;
  const [wx, wz] = fmWorld(e.clientX, e.clientY);
  sendPing(wx, groundAt(wx, wz) + 0.1, wz);
}
// the ping key: wherever you look (the first thing the look ray hits)
const tv = new THREE.Vector3(), td = new THREE.Vector3();
function worldPing() {
  const cam = G.camera;
  if (!cam || !mapOn() || RP.active) return;
  cam.getWorldPosition(tv); cam.getWorldDirection(td);
  const o = [tv.x, tv.y, tv.z], d = [td.x, td.y, td.z];
  let h = raycast(o, d, PING.far, BOXES);
  if (!h && d[1] < -0.02 && o[1] > 0 && -o[1] / d[1] < PING.far) h = { t: -o[1] / d[1] }; // the sea / no floor box: sea level
  if (!h) { hud.msg('PING THE GROUND, NOT THE SKY', 1.1); sfx.empty(); return; }
  sendPing(o[0] + d[0] * h.t, o[1] + d[1] * h.t + 0.1, o[2] + d[2] * h.t);
}

let beamGeo = null, ringGeo = null;
function beam(col) {
  beamGeo ||= new THREE.CylinderGeometry(0.22, 0.22, 70, 6, 1, true).translate(0, 35, 0);
  ringGeo ||= new THREE.RingGeometry(0.9, 1.5, 16).rotateX(-Math.PI / 2);
  const mat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, side: THREE.DoubleSide });
  const g = new THREE.Group(); g.add(new THREE.Mesh(beamGeo, mat), new THREE.Mesh(ringGeo, mat)); g.name = 'fm_ping';
  g.userData.mat = mat;
  return g;
}
function dropPing(g) {
  if (g.el) g.el.remove();
  if (g.beam) { if (g.beam.parent) g.beam.parent.remove(g.beam); g.beam.userData.mat.dispose(); }
  pings.delete(g.id);
}
export function clearPings() { for (const g of [...pings.values()]) dropPing(g); }
function gotPing(m) {
  if (m.no) { hud.msg('TOO MANY PINGS. TOUCH GRASS FOR A SEC', 1.2); return; }
  const p = m.p;
  if (!Array.isArray(p) || p.length !== 3 || !p.every(Number.isFinite) || !Number.isFinite(m.id)) return;
  const mine = [...pings.values()].filter((g) => g.by === m.by).sort((a, b) => a.t - b.t);
  while (mine.length >= PING.keep) dropPing(mine.shift()); // a 4th pushes your oldest off
  const g = { id: m.id, by: m.by, p, t: performance.now(), col: pingCol(m.by), name: nameOf(m.by), el: null, beam: null };
  build();
  g.el = document.createElement('div'); g.el.className = 'fmPin pop'; g.el.style.setProperty('--c', g.col);
  g.el.innerHTML = `<b>${esc(g.name)}</b><small></small><div class="d"></div>`;
  pinLayer.appendChild(g.el);
  if (G.scene) { g.beam = beam(g.col); g.beam.position.set(p[0], p[1], p[2]); G.scene.add(g.beam); }
  pings.set(g.id, g);
  sfx.ping(m.by === G.myId);
}

// ------------------------------------------------------------ hooks for main.js
let tapped = false;
export function initFullmap(lock) {
  FM.lock = lock || null;
  if (tapped) return;
  tapped = true;
  net.on('mping', gotPing);
  net.tap((m) => { if (m.t === 'welcome') { clearPings(); closeMap(false); } });
}
// a key in game (main.js pressed()). true = handled
export function fmKey(e) {
  if (FM.open && (e.code === 'Escape' || (K.matches('map', e) && !e.repeat))) { closeMap(e.code !== 'Escape'); return true; }
  if (K.matches('map', e)) { if (!e.repeat) openMap(); return true; }
  if (K.matches('ping', e)) { if (!e.repeat) worldPing(); return true; }
  return false;
}
// a mouse button in game (main.js mousedown): the map takes clicks on itself; a click off it closes it
export function fmMouse(e) {
  if (!FM.open) return false;
  if (e.target instanceof Element && e.target.closest('#fmPanel')) return true;
  closeMap(false);
  return true;
}
export function fullmapFrame(now) {
  // the map closes itself when there's nothing to show (died into a killcam, left the match, a replay)
  if (FM.open && (!mapOn() || RP.active || G.killcamPending)) closeMap(false);
  if (FM.open && now - FM.drawT > 45) { FM.drawT = now; drawMap(now); }
  if (!pings.size) return;
  if (!G.joined) { clearPings(); return; }
  const cam = G.camera, hide = RP.active || !cam, W2 = innerWidth / 2, H2 = innerHeight / 2;
  pinLayer.style.display = hide ? 'none' : '';
  for (const g of [...pings.values()]) {
    const age = now - g.t;
    if (age > PING.life) { dropPing(g); continue; }
    const fade = Math.min(1, (PING.life - age) / 1200);
    if (g.beam) { g.beam.visible = !hide; g.beam.userData.mat.opacity = 0.5 * fade * (age < 400 ? 1.6 - age / 1000 : 1); g.beam.children[1].scale.setScalar(1 + (age % 1200) / 600); }
    if (hide) continue;
    tv.set(g.p[0], g.p[1] + 1.2, g.p[2]).project(cam);
    let sx = tv.x, sy = tv.y;
    const behind = tv.z > 1;
    if (behind) { sx = -sx; sy = -sy; }
    const off = behind || Math.abs(sx) > 0.94 || Math.abs(sy) > 0.9;
    if (off) { const k = 1 / Math.max(Math.abs(sx) / 0.94, Math.abs(sy) / 0.86, 1e-3); sx *= k; sy *= k; } // pinned to the screen's edge
    g.el.style.left = `${W2 + sx * W2}px`; g.el.style.top = `${H2 - sy * H2}px`;
    g.el.style.opacity = fade;
    g.el.classList.toggle('edge', off);
    const d = Math.hypot(g.p[0] - ME.pos[0], g.p[1] - ME.pos[1], g.p[2] - ME.pos[2]);
    const s = `${Math.round(d)} m`;
    if (g.el.lastChild.previousSibling.textContent !== s) g.el.lastChild.previousSibling.textContent = s;
  }
}
