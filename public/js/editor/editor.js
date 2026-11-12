// The map editor (editor.html): fly round any map noclip, Minecraft-creative style, pick props, buildings and boxes,
// carry them, turn them, size them, copy them, delete them. Every change is an op (shared/mapedit.js) kept per map in
// this browser and exported as a file for us to ship. Nothing here talks to the server: edits never reach a match.
import '/shared/mapedits/apply.js'; // the shipped edits first: yours go on top of them
import * as THREE from 'three';
import { MAPS, BOXES, MAP } from '/shared/map.js';
import { resetGrid, movePlayer, playerOverlap } from '/shared/physics.js';
import { indexMap, bySig, boundsOf, pivotOf, canScale, xfThing, xfUndo, removeThing, insertThing, thingData, thingFrom, applyEdits, validEdits } from '/shared/mapedit.js';
import { G } from '../ctx.js';
import { K } from '../keys.js';
import { lockPointer, lookFilter } from '../mouselook.js';
import { initWorld, renderFrame, setJank, updateWorld, loadMap, refreshMapVisuals, mapMats, relightMap } from '../world.js';
import { whenGlb } from '../glbkit.js';
import { wantArch } from '../archfield.js';
import { initPalette, togglePalette, paletteOpen, solidOn, modelBounds, addRecent, setActiveSlot, slotItem, slotTool, dropOn } from './palette.js';
import { initTools, updateTools, toolDown, toolUp, toolWheel, toolKey, toolMouse, pickTool, loadItem, curTool, busy, toolState, hideVM } from './tools.js';
import { ghostOf, dropGhost } from './modelghost.js';
import { navCheck } from '/shared/navcheck.js';
import { EDITS } from '/shared/mapedits/index.js';
import { loadTripoModels } from '../models.js';
import { fx } from '../fx.js';
import { liquidBox } from '../liquids.js';

const $ = (id) => document.getElementById(id);
try { Object.assign(G.settings, JSON.parse(localStorage.getItem('jankfire') || '{}')); } catch { /* fresh settings */ }
K.attach(G.settings); // (the game's key module listens on the page too: it needs its bindings)
const canvas = $('c');
initWorld(canvas);
setJank(G.settings.jank ?? 1);
fx.init(G.scene); // (the lava's sparks, splashes: liquids.js spawns through it)
const cam = G.camera;
cam.fov = 80; cam.updateProjectionMatrix();

// ---------------------------------------------------------------- the map + its edits
const store = (id) => 'jfEdits:' + id;
const mapIds = Object.keys(MAPS).filter((id) => !MAPS[id].stream);
const Q = new URLSearchParams(location.search);
let mapId = Q.get('map'); if (!mapIds.includes(mapId)) { try { mapId = localStorage.getItem('jfEdMap'); } catch { mapId = null; } }
if (!mapIds.includes(mapId)) mapId = mapIds.includes('warehouse') ? 'warehouse' : mapIds[0];
try { localStorage.setItem('jfEdMap', mapId); } catch { /* fine */ }
const def = MAPS[mapId];
let saved = { map: mapId, v: 1, ops: [] };
try { const s = JSON.parse(localStorage.getItem(store(mapId)) || 'null'); if (s && validEdits(s) && s.map === mapId) saved = s; } catch { /* a broken save: start clean */ }
let rep;
try { rep = applyEdits(def, saved); } catch (e) { // a save that breaks the replay: keep it aside, start clean (the page reloads the map)
  console.error('editor: saved edits broke the replay', e);
  try { localStorage.setItem(store(mapId) + ':broken', JSON.stringify(saved)); localStorage.removeItem(store(mapId)); } catch { /* fine */ }
  location.reload(); throw e;
}
const { idx, stale } = rep; // (a map remodelled since: those ops just don't find their thing)
const staleOps = new Set(stale.map((s) => s.op));
loadMap(mapId);
loadTripoModels().then((n) => { if (n) rebuild(); }); // the Blender models list (props, buildings): then they replace their boxes, like in the game
let look = null; // sig -> thing, rebuilt after every change
const sigs = () => (look || (look = bySig(idx)));
const hist = saved.ops.map((op) => ({ op, stale: staleOps.has(op) })); // (replayed ops can't be undone by reference: only this session's can)
let undoN = 0; // how many of the last ops in hist are this session's (undoable)
const redo = [];

function persist() {
  clearBotMarks(); // (an edit: the old bot answer is about the old map)
  saved.ops = hist.map((h) => h.op);
  try { localStorage.setItem(store(mapId), JSON.stringify(saved)); } catch { toast('could not save in this browser (export it!)'); }
  $('edN').textContent = hist.length;
  if (!$('edList').classList.contains('hidden')) showList();
}
// the boxes changed: the physics copy, the drawing
let rebuildT = 0;
function rebuild() {
  look = null;
  BOXES.length = 0; BOXES.push(...def.boxes); resetGrid(BOXES);
  const t0 = performance.now();
  refreshMapVisuals();
  relightMap(); // (the lamps and neon light where their boxes are now)
  rebuildT = performance.now() - t0;
  drawSel();
}
// run a change now and keep it: h = { op, do(), undo() }
function commit(h) { h.do(); hist.push(h); undoN++; redo.length = 0; persist(); rebuild(); }
function undo() {
  if (!undoN) { toast(hist.length ? 'older changes: use RESET MAP or the change list' : 'nothing to undo'); return; }
  const h = hist.pop(); undoN--; h.undo(); redo.push(h); persist(); rebuild(); callout('UNDO\'D');
}
function redoIt() { const h = redo.pop(); if (!h) return toast('nothing to redo'); h.do(); hist.push(h); undoN++; persist(); rebuild(); callout('REDO\'D'); }

// ops on things (by reference here; by sig in the file)
const sigList = (ts) => ts.map((t) => sigs().sig.get(t));
function opXf(ts, o, k, q, d) {
  const op = { t: 'xf', sel: sigList(ts), o: o.map(r4), k: r4(k), q: q & 3, d: d.map(r4) };
  commit({ op, do() { for (const t of ts) xfThing(t, op.o, op.k, op.q, op.d); }, undo() { const u = xfUndo(op.o, op.k, op.q, op.d); for (const t of ts) xfThing(t, ...u); } });
}
function opDel(ts) {
  const op = { t: 'del', sel: sigList(ts) };
  commit({ op, do() { for (const t of ts) removeThing(def, idx, t); sel.clear(); }, undo() { for (const t of ts) insertThing(def, idx, t); } });
}
function opAdd(items) {
  const op = { t: 'add', items }, made = items.map(thingFrom);
  commit({ op, do() { for (const t of made) insertThing(def, idx, t); }, undo() { for (const t of made) { removeThing(def, idx, t); sel.delete(t); } } });
  return made;
}
const r4 = (v) => Math.round(v * 1e4) / 1e4;

// ---------------------------------------------------------------- picking
let floorsLocked = true;
const isFloor = (b) => (b.max[0] - b.min[0]) * (b.max[2] - b.min[2]) > 150 && b.max[1] - b.min[1] < 4;
const _o = new THREE.Vector3(), _d = new THREE.Vector3();
// ray against a box (turned deco boxes in their own frame). returns [t, axis it came in through, +1 = the max face] or null
function rayBox(o, d, b) {
  let ox = o.x, oz = o.z, dx = d.x, dz = d.z;
  const cx = (b.min[0] + b.max[0]) / 2, cz = (b.min[2] + b.max[2]) / 2;
  if (b.rot) { const c = Math.cos(-b.rot), s = Math.sin(-b.rot), px = ox - cx, pz = oz - cz; ox = cx + px * c + pz * s; oz = cz - px * s + pz * c; const ddx = dx * c + dz * s; dz = -dx * s + dz * c; dx = ddx; }
  const O = [ox, o.y, oz], D = [dx, d.y, dz];
  let t0 = 0, t1 = 1e9, ax = -1, sg = 0;
  for (let i = 0; i < 3; i++) {
    if (Math.abs(D[i]) < 1e-9) { if (O[i] < b.min[i] || O[i] > b.max[i]) return null; continue; }
    let a = (b.min[i] - O[i]) / D[i], z = (b.max[i] - O[i]) / D[i], s = -1;
    if (a > z) { [a, z] = [z, a]; s = 1; }
    if (a > t0) { t0 = a; ax = i; sg = s; }
    if (z < t1) t1 = z;
    if (t0 > t1) return null;
  }
  return ax < 0 ? null : [t0, ax, sg]; // (null: we're inside it, noclipped: pick what's beyond)
}
function extentBox(p) { // a model with no boxes of its own (deco trees): its fitted extent, as a turned box
  const c = Math.cos(p.y), s = Math.sin(p.y), mx = (p.lo[0] + p.hi[0]) / 2, mz = (p.lo[2] + p.hi[2]) / 2;
  const cx = p.a[0] + mx * c + mz * s, cz = p.a[2] - mx * s + mz * c, hx = (p.hi[0] - p.lo[0]) / 2, hz = (p.hi[2] - p.lo[2]) / 2;
  return { min: [cx - hx, p.a[1] + p.lo[1], cz - hz], max: [cx + hx, p.a[1] + p.hi[1], cz + hz], rot: p.y || 1e-6 };
}
const boxesOf = (t) => (t.boxes.length ? t.boxes : t.prop && t.prop.a ? [extentBox(t.prop)] : []);
function pick(o, d, skip, floors = !floorsLocked, dry = false) { // floors: big ground slabs count (you can always put things down on them). dry: not water / lava (you set things on the bottom)
  let best = null, bt = 1e9, top = false;
  for (const t of idx.things) {
    if (skip && skip.has(t)) continue;
    for (const b of boxesOf(t)) {
      if (!floors && isFloor(b)) continue;
      if (dry && liquidBox(b)) continue;
      const h = rayBox(o, d, b);
      if (h && h[0] < bt) { bt = h[0]; best = t; top = h[1] === 1 && h[2] === 1; }
    }
  }
  return best ? { t: best, dist: bt, top } : null;
}
// what's under the crosshair (or under the mouse when it's free)
const mouse = new THREE.Vector2(), ray = new THREE.Raycaster();
let moved = false; // (no hover outline until the mouse has been somewhere)
function aimRay() {
  if (document.pointerLockElement === canvas) { cam.getWorldPosition(_o); cam.getWorldDirection(_d); } else { ray.setFromCamera(mouse, cam); _o.copy(ray.ray.origin); _d.copy(ray.ray.direction); }
  return [_o, _d];
}

// ---------------------------------------------------------------- selection + hover outlines
const sel = new Set();
let hover = null;
function edgesFor(ts) {
  const pos = [];
  for (const t of ts) for (const b of boxesOf(t)) {
    const c = [(b.min[0] + b.max[0]) / 2, (b.min[2] + b.max[2]) / 2], r = b.rot || 0, cs = Math.cos(r), sn = Math.sin(r);
    const P = (x, y, z) => { const lx = x - c[0], lz = z - c[1]; return [c[0] + lx * cs + lz * sn, y, c[1] - lx * sn + lz * cs]; };
    const v = []; for (const x of [b.min[0], b.max[0]]) for (const y of [b.min[1], b.max[1]]) for (const z of [b.min[2], b.max[2]]) v.push(P(x, y, z));
    for (const [a, z] of [[0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3], [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7]]) pos.push(...v[a], ...v[z]);
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  return g;
}
const lineMat = (c, o) => new THREE.LineBasicMaterial({ color: c, depthTest: false, transparent: true, opacity: o });
const selLines = new THREE.LineSegments(new THREE.BufferGeometry(), lineMat(0xff4fd8, 1)), hovLines = new THREE.LineSegments(new THREE.BufferGeometry(), lineMat(0xffe14d, 0.7));
selLines.renderOrder = hovLines.renderOrder = 999; selLines.frustumCulled = hovLines.frustumCulled = false;
G.scene.add(selLines, hovLines);
function drawSel() { selLines.geometry.dispose(); selLines.geometry = edgesFor([...sel]); showSel(); }
function drawHover(t) { if (t === hover) return; hover = t; hovLines.geometry.dispose(); hovLines.geometry = edgesFor(t && !sel.has(t) ? [t] : []); }

const NAMES = { box: 'box', prop: 'prop', arch: 'building' };
const nameOf = (t) => (t.kind === 'prop' ? t.prop.id.replace(/_/g, ' ') : t.kind === 'arch' ? t.arch.id.replace(/_/g, ' ') : (t.boxes[0].mat || 'box') + ' box');
function showSel() {
  const ts = [...sel], el = $('edSel');
  el.classList.toggle('hidden', !ts.length || !$('edList').classList.contains('hidden') || !$('edBots').classList.contains('hidden'));
  if (!ts.length) return;
  const { lo, hi } = unionBounds(ts), f = (v) => v.toFixed(1);
  $('edSelName').textContent = ts.length > 1 ? ts.length + ' things' : nameOf(ts[0]);
  $('edSelInfo').textContent = (ts.length > 1 ? '' : NAMES[ts[0].kind] + (ts[0].list === 'd' ? ' (look only)' : '') + ' · ' + ts[0].boxes.length + ' collision box' + (ts[0].boxes.length === 1 ? '' : 'es') + '\n') +
    'at ' + f((lo[0] + hi[0]) / 2) + ', ' + f(lo[1]) + ', ' + f((lo[2] + hi[2]) / 2) + '\nsize ' + f(hi[0] - lo[0]) + ' x ' + f(hi[1] - lo[1]) + ' x ' + f(hi[2] - lo[2]) + ' m';
}
function unionBounds(ts) {
  const lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
  for (const t of ts) { const b = boundsOf(t); for (let i = 0; i < 3; i++) { lo[i] = Math.min(lo[i], b.lo[i]); hi[i] = Math.max(hi[i], b.hi[i]); } }
  return { lo, hi };
}
const pivotFor = (ts) => { if (ts.length === 1) return pivotOf(ts[0]); const { lo, hi } = unionBounds(ts); return [(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]; };

// ---------------------------------------------------------------- carrying (move), with a see-through ghost
let carry = null; // { ts, o, k, q, dist, ghost }
const ghostMat = new THREE.MeshBasicMaterial({ color: 0xff4fd8, transparent: true, opacity: 0.28, depthWrite: false });
function startCarry(ts) {
  ts = ts.filter(Boolean); if (!ts.length) return;
  const o = pivotFor(ts), ghost = ghostOf(ts, o, edgesFor(ts)); // (the real model where there is one)
  ghost.position.set(...o); G.scene.add(ghost);
  cam.getWorldPosition(_o);
  carry = { ts, o, k: 1, q: 0, dist: Math.max(4, Math.hypot(o[0] - _o.x, o[1] - _o.y, o[2] - _o.z)), ghost, d: [0, 0, 0] };
  callout('YOINK');
}
// the snap grid under what you carry: lines every grid step, 20 m across, at its feet (none with snap off)
let gridH = null, gridStep = 0;
function showGrid(at) {
  if (!at || !snap) { if (gridH) gridH.visible = false; return; }
  if (!gridH || gridStep !== snap) {
    if (gridH) { G.scene.remove(gridH); gridH.geometry.dispose(); gridH.material.dispose(); }
    const size = Math.min(80, Math.max(10, snap * 20)); gridStep = snap;
    gridH = new THREE.GridHelper(size, Math.round(size / snap), 0xffe14d, 0xff4fd8);
    gridH.material.transparent = true; gridH.material.opacity = 0.55; gridH.material.depthTest = false; gridH.renderOrder = 997;
    G.scene.add(gridH);
  }
  gridH.visible = true;
  gridH.position.set(Math.round(at[0] / snap) * snap, at[1] + 0.02, Math.round(at[2] / snap) * snap); // (its lines land on whole grid steps)
}
// shaped ground (shared/terrain.js heightfield) isn't boxes: march the ray down onto it. returns the distance or null
let terBoxes = null; // the ground's own steps (b.ter): not things you can pick, but you can put things down on them
function terrainHit(o, d, max) {
  let best = null;
  const T = def.boxes.terrain;
  if (T && T.at) for (let t = 0.5; t < max; t += 0.5) { const g = T.at(o.x + d.x * t, o.z + d.z * t); if (g != null && o.y + d.y * t <= g) { best = t; break; } }
  if (!terBoxes) terBoxes = def.boxes.filter((b) => b.ter);
  for (const b of terBoxes) { const h = rayBox(o, d, b); if (h && h[1] === 1 && h[2] === 1 && h[0] < max && (best == null || h[0] < best)) best = h[0]; }
  return best;
}
function updateCarry() {
  if (!carry) { showGrid(null); return; }
  const [o, d] = aimRay(), skip = new Set(carry.ts);
  let h = pick(o, d, skip, true, true);
  const th = terrainHit(o, d, Math.min(200, h ? h.dist : carry.dist * 2.5));
  if (th != null && (!h || th < h.dist)) h = { dist: th, top: true };
  let p;
  if (h && h.top && h.dist < carry.dist * 2.5) p = [o.x + d.x * h.dist, o.y + d.y * h.dist, o.z + d.z * h.dist]; // aimed at a floor: it sits on it
  else p = [o.x + d.x * carry.dist, o.y + d.y * carry.dist, o.z + d.z * carry.dist];
  const dd = [p[0] - carry.o[0], p[1] - carry.o[1], p[2] - carry.o[2]];
  if (snap) { dd[0] = Math.round(dd[0] / snap) * snap; dd[2] = Math.round(dd[2] / snap) * snap; if (!(h && h.top)) dd[1] = Math.round(dd[1] / snap) * snap; }
  carry.d = dd;
  carry.ghost.position.set(carry.o[0] + dd[0], carry.o[1] + dd[1], carry.o[2] + dd[2]);
  carry.ghost.rotation.y = carry.q * Math.PI / 2; carry.ghost.scale.setScalar(carry.k);
  showGrid([carry.o[0] + dd[0], carry.o[1] + dd[1], carry.o[2] + dd[2]]);
}
function dropCarry() {
  if (!carry) return;
  const c = carry; endCarry();
  if (c.d.every((v) => Math.abs(v) < 1e-4) && c.q === 0 && c.k === 1) return;
  opXf(c.ts, c.o, c.k, c.q, c.d); callout('PLONK');
}
// put it back: a fresh copy (or a new thing from the palette) that never got put down goes away again
function cancelCarry() { const fresh = carry && carry.fresh; endCarry(); if (fresh && undoN) { undo(); redo.pop(); toast('never mind'); } else toast('put back'); }
function endCarry() { if (!carry) return; dropGhost(carry.ghost); carry = null; }

// ---------------------------------------------------------------- actions
let snap = 1;
const SNAPS = [0, 0.25, 0.5, 1, 2, 4];
function setSnap(v) { snap = v; $('edSnap').textContent = snap ? 'SNAP ' + snap + 'm' : 'SNAP OFF'; $('edSnap').classList.toggle('on', !!snap); }
function act(a, shift) {
  const ts = [...sel];
  if (a === 'grab') { if (carry) dropCarry(); else if (ts.length) startCarry(ts); else toast('select something first'); return; }
  if (!ts.length) return toast('select something first');
  if (a === 'turn') { const q = shift ? 3 : 1; if (carry) { carry.q = (carry.q + q) & 3; return; } opXf(ts, pivotFor(ts), 1, q, [0, 0, 0]); callout('SPEEN'); return; }
  if (a === 'bigger' || a === 'smaller') {
    if (!ts.every(canScale)) return toast('buildings keep their size (move and turn them)');
    const k = a === 'bigger' ? 1.1 : 1 / 1.1;
    if (carry) { carry.k *= k; return; }
    opXf(ts, pivotFor(ts), k, 0, [0, 0, 0]); callout(a === 'bigger' ? 'THICC' : 'SMOL'); return;
  }
  if (a === 'del') { endCarry(); opDel(ts); drawHover(null); callout('YEET'); return; }
  if (a === 'dupe') { endCarry(); const made = opAdd(ts.map(thingData)); sel.clear(); for (const t of made) sel.add(t); drawSel(); startCarry(made); carry.fresh = true; callout('COPY PASTA'); }
}
let nudgeT = 0;
function nudge(dx, dy, dz) {
  const ts = [...sel]; if (!ts.length) return;
  const st = snap || 0.25, yaw = cam.rotation.y, f = Math.round(yaw / (Math.PI / 2)) & 3; // move along the grid axis nearest to where you look
  const [fx, fz] = [[0, -1], [-1, 0], [0, 1], [1, 0]][f], [rx, rz] = [-fz, fx];
  const d = [(fx * -dz + rx * dx) * st, dy * st, (fz * -dz + rz * dx) * st];
  const last = hist[hist.length - 1];
  if (undoN && !redo.length && last && last.nudge && performance.now() - last.nudge < 1500 && last.ts.length === ts.length && last.ts.every((t) => sel.has(t))) { // (taps in a row: one change)
    for (const t of ts) xfThing(t, [0, 0, 0], 1, 0, d);
    last.op.d = last.op.d.map((v, i) => r4(v + d[i])); last.nudge = performance.now(); persist(); drawSel();
    clearTimeout(nudgeT); nudgeT = setTimeout(rebuild, 160); return; // (held arrows: one redraw when they stop)
  }
  opXf(ts, pivotFor(ts), 1, 0, d);
  Object.assign(hist[hist.length - 1], { nudge: performance.now(), ts });
}

// ---------------------------------------------------------------- placing from the palette
// a new thing copies one that's already on a map somewhere (a placed house gets that house's real walls, a car its
// 15 boxes); a model no map uses yet gets one collision box the size of the model
let TPL = null;
function tpl() {
  if (TPL) return TPL;
  TPL = { props: new Map(), arch: new Map() };
  const solid = new Set();
  for (const [mid, d] of Object.entries(MAPS)) {
    if (d.stream) continue;
    for (const t of (mid === mapId ? idx : indexMap(d)).things) {
      if (t.kind === 'arch' && !TPL.arch.has(t.arch.id) && t.boxes.length) TPL.arch.set(t.arch.id, thingData(t));
      if (t.kind !== 'prop') continue;
      const id = t.prop.id, good = t.list === 'b' && t.boxes.length > 0;
      if (!TPL.props.has(id) || (good && !solid.has(id))) { TPL.props.set(id, thingData(t)); if (good) solid.add(id); }
    }
  }
  return TPL;
}
// things the grabby beam holds leave the map for a moment (moved far below, exactly as they were kept aside): the beam
// shows the model instead, and the real move is one ordinary op when you let go
const hidden = new Map();
function hideThings(ts) {
  for (const t of ts) {
    if (hidden.has(t)) continue;
    hidden.set(t, { b: t.boxes.map((b) => [b.min, b.max]), d: (t.dboxes || []).map((b) => [b.min, b.max]), a: t.prop && t.prop.a, p: t.prop && t.prop.p, ap: t.arch && t.arch.p });
    xfThing(t, [0, 0, 0], 1, 0, [0, -10000, 0]);
  }
  rebuild();
}
function unhideThings(ts) {
  for (const t of ts) {
    const h = hidden.get(t); if (!h) continue; hidden.delete(t);
    t.boxes.forEach((b, i) => { [b.min, b.max] = h.b[i]; }); (t.dboxes || []).forEach((b, i) => { [b.min, b.max] = h.d[i]; });
    if (t.prop) { if (h.a) t.prop.a = h.a; if (h.p) t.prop.p = h.p; }
    if (t.arch) t.arch.p = h.ap;
  }
}
// the data a new thing starts from (an 'add' item): a copy of one already on some map, a model's own size, a plain box.
// null while its model is still loading (asked for; it comes)
const asked = new Set();
function itemData(kind, mid) {
  let data = null;
  if (kind === 'props') {
    const id = mid.replace(/^p_/, '');
    data = tpl().props.get(id);
    if (!data) {
      const mb = modelBounds(mid);
      if (!mb) { if (!asked.has(mid)) { asked.add(mid); whenGlb([mid], () => {}); } return null; }
      data = { list: 'b', boxes: [{ min: mb.lo, max: mb.hi, mat: 'metal', pv: id }], prop: { id, a: [0, 0, 0], y: 0, lo: mb.lo, hi: mb.hi } };
    }
  } else if (kind === 'arch') { data = tpl().arch.get(mid); if (!data) return null; }
  else data = { list: 'b', boxes: [{ min: [-1, 0, -1], max: [1, 2, 1], mat: mid }] };
  data = JSON.parse(JSON.stringify(data));
  if (kind !== 'arch' && !solidOn()) data.list = 'd'; // look-only: drawn, never bumped into (buildings are always solid)
  return data;
}
let retried = new Set();
function place(kind, mid) {
  let data = null;
  if (kind === 'props') {
    const id = mid.replace(/^p_/, '');
    data = tpl().props.get(id);
    if (!data) {
      const mb = modelBounds(mid);
      if (!mb) { if (retried.has(mid)) return toast('that model would not load'); retried.add(mid); toast('loading ' + id.replace(/_/g, ' ') + '...'); whenGlb([mid], () => place(kind, mid)); return; }
      data = { list: 'b', boxes: [{ min: mb.lo, max: mb.hi, mat: 'metal', pv: id }], prop: { id, a: [0, 0, 0], y: 0, lo: mb.lo, hi: mb.hi } };
    }
  } else if (kind === 'arch') { data = tpl().arch.get(mid); if (!data) return toast('no map uses that building yet'); }
  else data = { list: 'b', boxes: [{ min: [-1, 0, -1], max: [1, 2, 1], mat: mid }] };
  data = JSON.parse(JSON.stringify(data));
  if (kind !== 'arch' && !solidOn()) data.list = 'd'; // look-only: drawn, never bumped into (buildings are always solid)
  // where you aim: on the floor under the crosshair, or 10 m ahead
  const [o, d] = aimRay(), h = pick(o, d, null, true, true), th = terrainHit(o, d, 120), hd = h ? h.dist : 1e9, dist = Math.min(hd, th ?? 1e9) < 120 ? Math.min(hd, th ?? 1e9) : 10;
  const at = [o.x + d.x * dist, o.y + d.y * dist, o.z + d.z * dist];
  if (snap) { at[0] = Math.round(at[0] / snap) * snap; at[2] = Math.round(at[2] / snap) * snap; }
  const t = thingFrom(data), b = boundsOf(t), from = [(b.lo[0] + b.hi[0]) / 2, b.lo[1], (b.lo[2] + b.hi[2]) / 2];
  xfThing(t, from, 1, 0, [at[0] - from[0], at[1] - from[1], at[2] - from[2]]);
  const made = opAdd([thingData(t)]);
  if (kind === 'arch') wantArch(def.boxes.arch, () => rebuild()); // (a building this map didn't have: its model)
  sel.clear(); for (const m of made) sel.add(m); drawSel();
  startCarry(made); if (carry) carry.fresh = true; callout('PLOP');
}

// ---------------------------------------------------------------- bot check: can bots still get everywhere?
// the bots' own walk graph, rebuilt from the edited boxes, against the same map without your edits (a second, untouched
// build of the maps, made the first time you ask). red = cut off by your edits, grey = already unreachable before
let baseMaps = null, botMarks = null;
async function botCheck() {
  toast('asking the bots...');
  await new Promise((r) => setTimeout(r, 30)); // (let the toast show: the check takes a moment)
  if (!baseMaps) {
    try { baseMaps = (await import('/shared/map.js?editorbase=1')).MAPS; } catch { baseMaps = {}; }
    if (baseMaps[mapId] && EDITS[mapId]) applyEdits(baseMaps[mapId], EDITS[mapId]); // (the map as shipped)
  }
  let r = null;
  try { r = navCheck(def, baseMaps[mapId] || null); } catch (e) { console.error(e); return toast('the bot check broke on this map'); }
  clearBotMarks();
  const el = $('edBotList'); el.innerHTML = '';
  $('edBots').classList.remove('hidden'); $('edList').classList.add('hidden'); showSel();
  if (!r) { el.innerHTML = '<div>this map has no bot routes: bots walk straight at things here, so nothing to check.</div>'; return; }
  const bad = r.spots.filter((p) => !p.ok), cut = bad.filter((p) => p.was !== false), old = bad.filter((p) => p.was === false);
  botMarks = new THREE.Group(); botMarks.name = 'botcheck';
  const pin = (p, c) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 6, 8), new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: 0.75, depthTest: false })); m.position.set(p[0], p[1] + 3, p[2]); m.renderOrder = 998; botMarks.add(m); };
  for (const p of cut) pin(p.p, 0xff3030); for (const p of old) pin(p.p, 0x888888);
  if (r.lost.length) {
    const pos = new Float32Array(r.lost.length * 3); r.lost.forEach((p, i) => pos.set([p[0], p[1] + 0.15, p[2]], i * 3));
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const pts = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xff3030, size: 6, sizeAttenuation: false, depthTest: false })); pts.renderOrder = 998; botMarks.add(pts);
  }
  G.scene.add(botMarks);
  const line = (html, cls, p) => { const d = document.createElement('div'); d.innerHTML = html; if (cls) d.className = cls; if (p) d.onclick = () => { cam.position.set(p[0] + 7, p[1] + 6, p[2] + 7); lookAt(p); }; el.append(d); };
  line(cut.length || r.lost.length ? '<b class="edBad">' + (cut.length ? cut.length + ' spot' + (cut.length > 1 ? 's' : '') + ' bots can\'t reach any more' : 'all the important spots are fine') + '</b>' : '<b class="edOk">ALL GOOD: bots can still get everywhere they need to</b>');
  if (r.lost.length) line(r.lost.length + ' m² of floor got cut off (red dots)', 'edBad', r.lost[0]);
  for (const p of cut) line('CAN\'T REACH <em>' + p.what + '</em>', 'stale', p.p);
  for (const p of old) line('<em>' + p.what + '</em> (already unreachable before your edits)', 'undone', p.p);
  line('bots can walk on ' + Math.round(r.reach / Math.max(1, r.nodes) * 100) + '% of the floor · ' + r.spots.filter((p) => p.ok).length + ' of ' + r.spots.length + ' spots fine');
  callout(cut.length || r.lost.length ? 'BOTS ARE STUCK' : 'BOTS APPROVE');
}
function clearBotMarks() { if (!botMarks) return; G.scene.remove(botMarks); botMarks.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); }); botMarks = null; }

// ---------------------------------------------------------------- the change list (the diff)
function opWhat(op) {
  const n = (op.sel || []).length, nm = n ? nameFromSig(op.sel[0]) + (n > 1 ? ' +' + (n - 1) : '') : '';
  if (op.t === 'del') return 'deleted <em>' + nm + '</em>';
  if (op.t === 'add') return 'added <em>' + (op.items[0] ? (op.items[0].prop ? op.items[0].prop.id : op.items[0].arch ? op.items[0].arch.id : op.items[0].boxes[0].mat + ' box') : '?') + (op.items.length > 1 ? ' +' + (op.items.length - 1) : '') + '</em>';
  const bits = [];
  const m = Math.hypot(...op.d); if (m > 1e-4) bits.push('moved ' + m.toFixed(2) + 'm');
  if (op.q) bits.push('turned ' + op.q * 90 + '°');
  if (op.k !== 1) bits.push('sized x' + op.k.toFixed(2));
  return (bits.join(', ') || 'touched') + ' <em>' + nm + '</em>';
}
function nameFromSig(s) { const p = s.split('|'); return p[0] === 'p' ? p[2] : p[0] === 'a' ? p[1] : p[2] + ' box'; }
function whereOf(op) {
  if (op.t === 'xf') return [op.o[0] + op.d[0], op.o[1] + op.d[1], op.o[2] + op.d[2]];
  if (op.t === 'add') { const it = op.items[0]; return it ? (it.prop ? it.prop.a || it.prop.p : it.arch ? it.arch.p : it.boxes[0].min) : null; }
  const p = (op.sel[0] || '').split('|'), c = (p[0] === 'a' ? p[2] : p[3]); return c ? c.split(',').map(Number) : null;
}
function showList() {
  const el = $('edOps'); el.innerHTML = '';
  if (!hist.length) el.innerHTML = '<div>nothing yet. go break something.</div>';
  hist.forEach((h, i) => {
    const d = document.createElement('div');
    d.innerHTML = (i + 1) + '. ' + opWhat(h.op) + (h.stale ? ' (MAP CHANGED: skipped)' : '');
    if (h.stale) d.className = 'stale';
    d.onclick = () => { const w = whereOf(h.op); if (w) { cam.position.set(w[0] + 6, w[1] + 5, w[2] + 6); lookAt(w); } };
    el.append(d);
  });
}
function lookAt(w) { const dx = w[0] - cam.position.x, dy = w[1] - cam.position.y, dz = w[2] - cam.position.z; cam.rotation.set(Math.atan2(dy, Math.hypot(dx, dz)), Math.atan2(-dx, -dz), 0); }

// ---------------------------------------------------------------- fly camera (noclip)
const keys = new Set();
let speed = 14;
{
  const mc = def.menuCam, sp = (def.spawns && def.spawns[0]) || [0, 2, 0];
  if (mc) cam.position.set(mc[0], mc[1], mc[2]); else cam.position.set(sp[0], sp[1] + 8, sp[2]);
  lookAt([0, 0, 0]);
}
// WALK TEST (F): drop out of the sky and walk your edits with the game's own physics (shared/physics.js movePlayer):
// bump into what you moved, jump what you built, find the gap you left. F again to fly
let walk = null;
function toggleWalk() {
  if (walk) { walk = null; callout('FLY'); toast('flying again (F to walk)'); return; }
  const p = [cam.position.x, cam.position.y - 1.6, cam.position.z];
  for (let k = 0; k < 40 && playerOverlap(p, BOXES); k++) p[1] += 0.5; // (noclipped into a wall: come out on top of it)
  walk = { p, v: [0, 0, 0], ground: false };
  callout('WALK TEST'); toast('walking: WASD, SPACE jump, SHIFT run. F to fly');
}
function walkStep(dt, f, r) {
  const W = walk, y = cam.rotation.y, sp = keys.has('ShiftLeft') || keys.has('ShiftRight') ? 11 : 7;
  let wx = -Math.sin(y) * f + Math.cos(y) * r, wz = -Math.cos(y) * f - Math.sin(y) * r; const l = Math.hypot(wx, wz); if (l > 1) { wx /= l; wz /= l; }
  const acc = W.ground ? 14 : 3; // (a little air control)
  W.v[0] += (wx * sp - W.v[0]) * Math.min(1, acc * dt); W.v[2] += (wz * sp - W.v[2]) * Math.min(1, acc * dt);
  W.v[1] -= 25 * dt;
  if (W.ground && keys.has('Space')) { W.v[1] = 8.5; W.ground = false; }
  const res = movePlayer(W.p, W.v, dt, BOXES, W.ground);
  W.ground = !!res.ground;
  if (W.p[1] < (MAP.killY ?? -45)) { const s = (def.spawns && def.spawns[0]) || [0, 2, 0]; W.p = [s[0], s[1] + 0.2, s[2]]; W.v = [0, 0, 0]; callout('INTO THE VOID'); }
  cam.position.set(W.p[0], W.p[1] + 1.6, W.p[2]);
}
let last = performance.now();
function frame(now) {
  requestAnimationFrame(frame); // (first: one broken piece of the world can't stop the editor)
  try { step(now); } catch (e) { if (!frameErr) { frameErr = true; console.error('editor frame', e); } }
}
let frameErr = false;
function step(now) {
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  const f = (keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0), r = (keys.has('KeyD') ? 1 : 0) - (keys.has('KeyA') ? 1 : 0), u = (keys.has('Space') ? 1 : 0) - (keys.has('KeyC') ? 1 : 0);
  if (walk) walkStep(dt, f, r);
  else if (f || r || u) {
    const v = speed * (keys.has('ShiftLeft') || keys.has('ShiftRight') ? 4 : 1) * dt, y = cam.rotation.y;
    cam.position.x += (-Math.sin(y) * f + Math.cos(y) * r) * v; cam.position.z += (-Math.cos(y) * f - Math.sin(y) * r) * v; cam.position.y += u * v;
  }
  updateCarry();
  updateTools(dt, !!(f || r || u));
  if (!carry && !busy() && curTool() !== 'plop' && (moved || document.pointerLockElement === canvas)) { const [o, d] = aimRay(); const h = pick(o, d); drawHover(h && h.t); } else drawHover(null);
  try { updateWorld(dt); } catch (e) { if (!frameErr) { frameErr = true; console.error('editor world', e); } }
  renderFrame();
}

// ---------------------------------------------------------------- input
canvas.addEventListener('mousedown', (e) => {
  if (!carry && toolDown(e.button)) return; // (the grabby beam, the plop cannon, the yeet ray)
  if (document.pointerLockElement !== canvas && e.button === 0) { if (carry) dropCarry(); else clickPick(e.shiftKey); }
  if (document.pointerLockElement === canvas) { if (e.button === 0) { if (carry) dropCarry(); else clickPick(e.shiftKey); } else if (e.button === 2 && carry) cancelCarry(); }
});
addEventListener('mouseup', (e) => { toolUp(e.button); });
canvas.addEventListener('dblclick', () => { if (document.pointerLockElement !== canvas) lockPointer(canvas); });
canvas.addEventListener('contextmenu', (e) => { e.preventDefault(); if (document.pointerLockElement !== canvas && !busy()) lockPointer(canvas); });
const mlook = lookFilter(); // (the game's mouse look: raw mouse, no snapping on Chrome's fake jumps)
function clickPick(add) {
  const [o, d] = aimRay(), h = pick(o, d);
  if (!add) sel.clear();
  if (h) { if (add && sel.has(h.t)) sel.delete(h.t); else sel.add(h.t); }
  hover = undefined; drawSel();
}
addEventListener('mousemove', (e) => {
  mouse.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1); moved = true;
  if (document.pointerLockElement !== canvas) return;
  if (!mlook.take(e.movementX, e.movementY)) return;
  if (toolMouse(e.movementX, e.movementY)) return; // (R held with something on the beam: the mouse turns it)
  const s = 0.0022 * (G.settings.sens || 1.2); // (the same feel as in a match)
  cam.rotation.order = 'YXZ'; cam.rotation.y -= e.movementX * s; cam.rotation.x = Math.max(-1.55, Math.min(1.55, cam.rotation.x - e.movementY * s)); cam.rotation.z = 0;
});
document.addEventListener('pointerlockchange', () => { if (document.pointerLockElement === canvas) mlook.locked(); $('edX').style.display = document.pointerLockElement === canvas ? '' : 'none'; canvas.style.cursor = document.pointerLockElement === canvas ? 'none' : 'crosshair'; });
addEventListener('wheel', (e) => {
  if (e.target !== canvas && document.pointerLockElement !== canvas) return;
  if (toolWheel(e.deltaY)) return;
  if (carry) carry.dist = Math.max(1.5, Math.min(200, carry.dist * (e.deltaY > 0 ? 0.9 : 1.1)));
  else { speed = Math.max(2, Math.min(90, speed * (e.deltaY > 0 ? 0.85 : 1.18))); toast('fly speed ' + speed.toFixed(0)); }
}, { passive: true });
addEventListener('keydown', (e) => {
  if (e.target.tagName === 'SELECT' || e.target.tagName === 'INPUT') return;
  const c = e.code, ctrl = e.ctrlKey || e.metaKey;
  if (busy() && (ctrl || ['KeyX', 'Delete', 'Backspace', 'KeyG', 'Equal', 'Minus'].includes(c))) return; // (not while the beam holds something)
  if (ctrl && c === 'KeyZ') { e.preventDefault(); if (e.shiftKey) redoIt(); else undo(); return; }
  if (ctrl && c === 'KeyY') { e.preventDefault(); redoIt(); return; }
  if (ctrl && c === 'KeyD') { e.preventDefault(); act('dupe'); return; }
  if (ctrl) return;
  keys.add(c);
  if (c === 'Space' || c.startsWith('Arrow') || c === 'PageUp' || c === 'PageDown') e.preventDefault();
  if (e.repeat && c === 'KeyR') return;
  if (c === 'KeyR' && toolKey('KeyR', true, e.shiftKey)) return;
  if (c === 'KeyG') act('grab');
  else if (c === 'KeyR') act('turn', e.shiftKey);
  else if (c === 'Equal' || c === 'NumpadAdd') act('bigger');
  else if (c === 'Minus' || c === 'NumpadSubtract') act('smaller');
  else if (c === 'Delete' || c === 'KeyX' || c === 'Backspace') act('del');
  else if (c === 'KeyB') setSnap(snap ? 0 : 1);
  else if (c === 'BracketRight') setSnap(SNAPS[Math.min(SNAPS.length - 1, SNAPS.indexOf(snap) + 1)] || 0.25);
  else if (c === 'BracketLeft') setSnap(SNAPS[Math.max(1, SNAPS.indexOf(snap) - 1)]);
  else if (c === 'KeyL') toggleFloors();
  else if (c === 'KeyN') botCheck();
  else if (c === 'KeyF') toggleWalk();
  else if (c === 'KeyP' || c === 'KeyE' || c === 'KeyQ') menu();
  else if (c === 'Escape' && paletteOpen()) menu(false);
  else if (c === 'Escape' && carry) cancelCarry();
  else if (c === 'ArrowUp') nudge(0, 0, -1); else if (c === 'ArrowDown') nudge(0, 0, 1); else if (c === 'ArrowLeft') nudge(-1, 0, 0); else if (c === 'ArrowRight') nudge(1, 0, 0);
  else if (c === 'PageUp') nudge(0, 1, 0); else if (c === 'PageDown') nudge(0, -1, 0);
  else if (/^Digit[1-9]$/.test(c) && !e.shiftKey) slot(+c.slice(5) - 1);
  else if (/^Digit[1-4]$/.test(c)) { G.settings.jank = +c.slice(5) - 1; setJank(G.settings.jank); toast(['Potato', 'Crusty', 'Mid', 'Too HD'][G.settings.jank]); }
});
addEventListener('keyup', (e) => { keys.delete(e.code); if (e.code === 'KeyR') toolKey('KeyR', false); });
addEventListener('blur', () => keys.clear());
function toggleFloors() { floorsLocked = !floorsLocked; $('edFloors').textContent = 'FLOORS: ' + (floorsLocked ? 'LOCKED' : 'PICKABLE'); $('edFloors').classList.toggle('on', !floorsLocked); }

// ---------------------------------------------------------------- the panels
const sel0 = $('edMap');
for (const id of mapIds) { const o = document.createElement('option'); o.value = id; o.textContent = (MAPS[id].name || id) + (MAPS[id].sd ? ' (S&D)' : ''); sel0.append(o); }
sel0.value = mapId;
sel0.onchange = () => { location.search = '?map=' + sel0.value; };
$('edUndo').onclick = undo; $('edRedo').onclick = redoIt;
$('edSnap').onclick = () => setSnap(snap ? 0 : 1); $('edFloors').onclick = toggleFloors;
for (const b of document.querySelectorAll('#edSel [data-a]')) b.onclick = () => act(b.dataset.a);
$('edDiff').onclick = () => { $('edList').classList.toggle('hidden'); showList(); showSel(); };
$('edClose').onclick = () => { $('edList').classList.add('hidden'); showSel(); };
$('edReset').onclick = () => { if (!confirm('Throw away every change on ' + (def.name || mapId) + '?')) return; try { localStorage.removeItem(store(mapId)); } catch { /* fine */ } location.reload(); };
$('edQuit').onclick = () => { location.href = '/'; };
$('edPalBtn').onclick = () => menu();
$('edBotBtn').onclick = () => botCheck();
$('edBotClose').onclick = () => { $('edBots').classList.add('hidden'); clearBotMarks(); showSel(); };
// the creative menu (E): click = into the plop cannon; the hotbar (1-9): 1-4 tools, 5-9 favourites
function menu(on) { const open = togglePalette(on); hideVM(open); if (open && document.pointerLockElement) document.exitPointerLock(); return open; }
function slot(i, it) {
  if (i < 4) { if (i === 1 && it) { loadItem(it); addRecent(it); setActiveSlot(1, it); return; } pickTool(slotTool(i)); setActiveSlot(i); return; }
  const x = it || slotItem(i);
  if (!x) { toast('empty slot: drag something here from the menu (E)'); return; }
  loadItem(x); setActiveSlot(i, x);
}
function onTool(t) { document.body.dataset.tool = t; if (t !== 'wand') { if (carry) cancelCarry(); if (sel.size) { sel.clear(); drawSel(); } } } // (selecting is the wand's thing)
initPalette({ pick: (k, id) => { const it = { kind: k, id }; loadItem(it); addRecent(it); setActiveSlot(1, it); menu(false); toast('plop cannon: ' + id.replace(/^p_/, '').replace(/_/g, ' ') + ' (click to plop)'); }, slot: (i, it) => slot(i, it), mats: mapMats, archOk: (id) => tpl().arch.has(id) });
initTools({ G, MAP, sel, aimRay, pick, terrainHit, pivotFor, edgesFor, select: (ts) => { sel.clear(); for (const t of ts) sel.add(t); drawSel(); }, hide: hideThings, unhide: unhideThings, rebuild, opXf, opAdd, opDel, itemData, thingFrom, thingData, xfThing, boundsOf, snap: () => snap, grid: showGrid, toast, callout, recent: addRecent, onTool });
onTool('grab'); setActiveSlot(0);
$('edExport').onclick = () => {
  const txt = JSON.stringify({ ...saved, ops: hist.map((h) => h.op), name: def.name, at: new Date().toISOString() });
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([txt], { type: 'application/json' })); a.download = 'jankfire-edits-' + mapId + '.json'; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  if (navigator.clipboard) navigator.clipboard.writeText(txt).catch(() => {});
  toast('saved jankfire-edits-' + mapId + '.json (send it to us!)');
};
$('edImport').onclick = () => $('edFile').click();
$('edFile').onchange = async () => {
  const f = $('edFile').files[0]; if (!f) return;
  let e; try { e = JSON.parse(await f.text()); } catch { return toast('that is not a changes file'); }
  if (!validEdits(e) || !mapIds.includes(e.map)) return toast('that file looks broken');
  if (!confirm('Load ' + e.ops.length + ' changes for ' + (MAPS[e.map].name || e.map) + '? (replaces the changes you have on it)')) return;
  try { localStorage.setItem(store(e.map), JSON.stringify({ map: e.map, v: 1, ops: e.ops })); } catch { return toast('could not save in this browser'); }
  location.search = '?map=' + e.map;
};
let callT = 0, toastT = 0;
function callout(t) { const el = $('edCall'); el.textContent = t; el.style.opacity = 1; clearTimeout(callT); callT = setTimeout(() => { el.style.opacity = 0; }, 700); }
function toast(t) { const el = $('edToast'); el.textContent = t; el.style.opacity = 1; clearTimeout(toastT); toastT = setTimeout(() => { el.style.opacity = 0; }, 1800); }

const topBar = () => document.body.style.setProperty('--edtop', Math.round($('edTop').getBoundingClientRect().bottom + 10) + 'px');
addEventListener('resize', topBar); topBar();
setSnap(1);
$('edN').textContent = hist.length;
$('edX').style.display = 'none'; canvas.style.cursor = 'crosshair';
if (stale.length) toast(stale.length + ' old change' + (stale.length > 1 ? 's' : '') + ' no longer fit this map (see CHANGES)');
// tests + the console
window.JFED = { G, toggleWalk, walking: () => walk && { p: walk.p.slice(), ground: walk.ground }, toolState, slot, menu, dropOn, opAdd, botCheck, place, togglePalette, idx, def, sel, hist, get carry() { return carry; }, act, pick: (o, d) => pick(new THREE.Vector3(...o), new THREE.Vector3(...d).normalize()), select: (ts) => { sel.clear(); for (const t of ts) sel.add(t); drawSel(); }, startCarry, dropCarry, undo, redo: redoIt, nudge, rebuildMs: () => rebuildT, cam, lookAt, MAP, showList };
requestAnimationFrame(frame);
