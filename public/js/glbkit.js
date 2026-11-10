// Models made in Blender (tools/blender/make_*.py). Unlike the old generated ones they're built in the game's own
// space (metres, -z forward, muzzle where the code model has it), so they go in exactly as they are: no fitting.
// The root node carries a `jf` JSON blob (muzzle, sight line, hat spot, moving parts...) from the Blender script.
// Visual only: collisions stay boxes. Anything missing or broken falls back to the code-built model.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { jankify } from './jank.js';
import { G } from './ctx.js';
import { WEAPONS } from '/shared/weapons.js';
import { COSMETICS } from '/shared/cosmetics.js';

export const AUTHORED = {}; // id -> { scene, meta }

// skin models (w_<skin>.glb, pj_<skin>.glb) aren't downloaded up front: only the first time someone shows that skin
// (you, another player, the locker). Until then it's the code model; when it lands, onLateModel's callback rebuilds.
export const LAZY = new Map(); // id -> url
// the gear and killstreak models (x_<thing>.glb: the rig, the wrecking ball, the camera...) and the rig's missile load
// the same way: the first time something asks (prefetch() asks early for what your loadout will need)
export const isLazy = (id) => { if (/^x_/.test(id) || /^p_[a-z]+kit$/.test(id) || id === 'pj_rigmissile') return true; const m = /^(?:w|pj)_(.+)$/.exec(id); return !!(m && m[1] !== 'default' && Object.hasOwn(COSMETICS.model, m[1])); };
const late = { fn: null, t: 0, busy: 0, by: new Map(), seen: new Set() };
export function onLateModel(fn) { late.fn = fn; }
export function whenLate(id, fn) { if (!late.by.has(id)) late.by.set(id, []); late.by.get(id).push(fn); } // that model just landed: drop a cached copy built without it
export const lateBusy = () => late.busy; // skins still downloading (tests wait for them)
export function prefetch(ids, pri = 1) { for (const id of ids) want(id, pri); }
// what each item / killstreak shows: fetched as soon as it's in your loadout (killstreaks take a while to earn), so the
// first time you use it it's already the Blender one. other people's gear loads the first time it shows up
const GEAR_FILES = { camera: ['x_camera', 'x_photoframe'], quiz: ['x_calc'], nvg: ['x_nvg'], wand: ['x_wand'] };
const STREAK_FILES = { overdrive: ['x_rig', 'x_rigarms', 'pj_rigmissile'], wreckingball: ['x_wreck'] };
export function prefetchLoadout(lo) {
  if (!lo) return;
  const ids = [...(GEAR_FILES[lo.item] || [])];
  for (const k of Array.isArray(lo.streaks) ? lo.streaks : []) ids.push(...(STREAK_FILES[k] || []));
  prefetch(ids);
}
function fetchLate(id, pri = 3) {
  const url = LAZY.get(id);
  LAZY.delete(id);
  late.busy++;
  queueGlb(id, url, pri, (gltf) => {
    late.busy--;
    if (!prepAuthored(id, gltf.scene)) { landed(id); return; }
    for (const f of late.by.get(id) || []) try { f(id); } catch (e) { console.warn('late model', id, e); }
    landed(id);
    if (!late.seen.has(id)) return; // fetched ahead and nothing built it yet: nothing to rebuild
    clearTimeout(late.t);
    late.t = setTimeout(() => { if (late.fn) late.fn(id); }, 120); // a few at once: one rebuild
  }, () => { late.busy--; });
}

// ------------------------------------------------------------ the download queue + "is it still coming?"
// every .glb (the boot set and the lazy ones) goes through one queue: a few at a time, the most wanted first, so the
// picture you're looking at isn't stuck behind 60 others. pictures ask pendingGlb(): while a Blender model is on its way
// they show a loading placeholder instead of the old code model. only if it fails, or the downloads stall (no bytes for
// WAIT_MS: a slow but moving connection keeps waiting), the code model stands in. onGlb listeners hear every model that lands, fails or times out, so only what used it redraws.
export const WAIT_MS = 4000;
export const glbLog = /jf_glblog/.test(location.search) ? [] : null; // ?jf_glblog: what was queued and started when (tests)
const LD = { prog: 0, timer: new Set(), list: null, done: new Set(), failed: new Set(), asked: new Map(), subs: new Set(), once: new Map(), track: null };
const Q = { items: new Map(), run: 0, max: 10 }; // (a lane stays taken while its model parses: 10 keeps the network busy)
let loader = null;
export function glbLoader() { return loader || (loader = new GLTFLoader()); }
export function queueGlb(id, url, pri, ok, bad) {
  const it = Q.items.get(id);
  if (it) { if (!it.go && pri > it.pri) it.pri = pri; return; }
  Q.items.set(id, { id, url, pri, ok, bad, go: false });
  if (glbLog) glbLog.push([Math.round(performance.now()), 'q', id, pri]);
  pump();
}
function pump() {
  for (;;) {
    let best = null;
    for (const it of Q.items.values()) if (!it.go && (!best || it.pri > best.pri)) best = it;
    if (!best) return;
    if (best.pri <= 0) { let hi = 0; for (const it of Q.items.values()) if (it.pri > 0) hi++; if (hi || Q.run >= 2) return; } // background fetches: only once everything wanted is in, two at a time
    if (Q.run >= Q.max + (best.pri >= 4 ? 3 : 0)) return; // what you're looking at right now gets three extra lanes
    best.go = true; Q.run++;
    if (glbLog) glbLog.push([Math.round(performance.now()), 'go', best.id, best.pri]);
    const end = () => { Q.run--; Q.items.delete(best.id); pump(); };
    glbLoader().load(best.url, (gltf) => { LD.prog = performance.now(); end(); try { best.ok(gltf); } catch (e) { console.warn('model', best.id, e); landed(best.id); } },
      () => { LD.prog = performance.now(); }, (e) => { end(); console.warn('model failed', best.id, e); LD.failed.add(best.id); if (best.bad) best.bad(e); emit(best.id); });
  }
}
// ask for a model sooner (pri: 0 idle, 1 soon, 2 this screen, 3 on screen right now)
export function want(id, pri = 2) {
  if (LAZY.has(id)) fetchLate(id, pri);
  else { const it = Q.items.get(id); if (it && !it.go && pri > it.pri) { it.pri = pri; if (glbLog) glbLog.push([Math.round(performance.now()), 'up', id, pri]); pump(); } }
}
export function setGlbList(ids) { LD.list = new Set(ids); emit(null); } // the server's list: anything not on it was never coming
export function landed(id) { LD.done.add(id); emit(id); }
export function onGlb(fn) { LD.subs.add(fn); return () => LD.subs.delete(fn); }
// fn() once, the first time any of ids lands / fails / gives up (null = the model list arrived)
export function whenGlb(ids, fn) { for (const id of ids) { if (!LD.once.has(id)) LD.once.set(id, new Set()); LD.once.get(id).add(fn); } }
function emit(id) {
  const fire = new Set();
  const take = (k) => { const s = LD.once.get(k); if (s) { LD.once.delete(k); for (const f of s) fire.add(f); } };
  if (id === null) for (const k of [...LD.once.keys()]) { if (!LD.list.has(k)) take(k); } else take(id);
  for (const f of LD.subs) try { f(id); } catch (e) { console.warn('glb sub', e); }
  for (const f of fire) try { f(id); } catch (e) { console.warn('glb once', e); }
}
// a Blender model that exists (or might: before the list comes) and isn't here yet
export function missingGlb(id) {
  if (AUTHORED[id] || LD.done.has(id) || LD.failed.has(id)) return false;
  return LD.list ? LD.list.has(id) : /^(w|pj|x|p)_/.test(id);
}
// ...and is still worth waiting for: a placeholder, not the code model
export function pendingGlb(id) {
  if (!missingGlb(id)) return false;
  const n = performance.now();
  if (!LD.asked.has(id)) LD.asked.set(id, n);
  const wait = n - Math.max(LD.asked.get(id), LD.prog) < WAIT_MS;
  if (wait && !LD.timer.has(id)) { LD.timer.add(id); giveUp(id, WAIT_MS + 20); }
  return wait;
}
function giveUp(id, ms) { // nothing arrived for WAIT_MS: redraw with the stand-in (it's swapped again if the model lands later)
  setTimeout(() => {
    if (!missingGlb(id)) { LD.timer.delete(id); return; }
    const left = WAIT_MS - (performance.now() - Math.max(LD.asked.get(id), LD.prog));
    if (left > 0) giveUp(id, left + 20); else { LD.timer.delete(id); emit(id); }
  }, ms);
}
// pictures wrap their build in trackGlb(): which Blender models it reached for that aren't here yet
export function trackGlb(fn) {
  const prev = LD.track, t = { missing: new Set(), pending: false };
  LD.track = t;
  try { return [fn(), t]; } finally { LD.track = prev; }
}
function noteMiss(id) {
  const t = LD.track;
  if (!t || !missingGlb(id)) return;
  t.missing.add(id);
  if (pendingGlb(id)) { t.pending = true; want(id, 3); }
}

// two looks to compare: 'glossy' (default: the materials as made in Blender + a studio reflection) and 'flat'
// (faceted Lambert like the code models, no gloss, each weapon's own colour from shared/weapons.js on its paint).
// pick with ?models=flat in the address or localStorage jf_models = 'flat'.
function styleFlag() {
  try {
    const q = new URLSearchParams(location.search).get('models');
    return (q || localStorage.getItem('jf_models') || 'glossy') === 'flat' ? 'flat' : 'glossy';
  } catch { return 'glossy'; }
}
export const MODEL_STYLE = styleFlag();

let env = null;
function envMap() { // one small studio reflection for glossy toy plastic and metal (the world's own materials don't use it)
  if (env || !G.renderer) return env;
  const pm = new THREE.PMREMGenerator(G.renderer);
  env = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  pm.dispose();
  return env;
}

// the hotbar pictures, the locker / menu hero and the mode art draw with their own renderers (other WebGL contexts),
// where the game's reflection map is just black (mirror chrome came out as a black shape): each gets its own while it draws
const sideEnv = new WeakMap();
export function withEnv(renderer, root, draw) {
  if (!env || !renderer || renderer === G.renderer) return draw();
  let e = sideEnv.get(renderer);
  if (!e) { const pm = new THREE.PMREMGenerator(renderer); e = pm.fromScene(new RoomEnvironment(), 0.04).texture; pm.dispose(); sideEnv.set(renderer, e); }
  const swapped = [];
  root.traverse((o) => { if (o.material) for (const m of Array.isArray(o.material) ? o.material : [o.material]) if (m && m.envMap === env) { m.envMap = e; swapped.push(m); } });
  try { return draw(); } finally { for (const m of swapped) m.envMap = env; } // (materials are shared with the game's copies)
}

export function metaOf(scene) {
  let meta = null;
  scene.traverse((o) => {
    if (meta || !o.userData || typeof o.userData.jf !== 'string') return;
    try { meta = JSON.parse(o.userData.jf); } catch { meta = null; }
  });
  return meta;
}

// the flat look: same texture + colour, faceted Lambert, glows kept. paint = the weapon's colour for its paint parts
function flatOf(m, paint) {
  const f = new THREE.MeshLambertMaterial({
    name: m.name, color: paint ? paint.clone() : m.color.clone(), map: paint ? null : m.map, flatShading: true,
    transparent: m.transparent, opacity: m.opacity, side: m.side, alphaTest: m.alphaTest,
    emissive: m.emissive ? m.emissive.clone() : new THREE.Color(0), emissiveIntensity: m.emissiveIntensity ?? 1, emissiveMap: m.emissiveMap || null,
  });
  f.depthWrite = m.depthWrite;
  return f;
}

// returns true if it took the model (it was made in Blender)
export function prepAuthored(id, scene) {
  const meta = metaOf(scene);
  if (!meta) return false;
  const flat = MODEL_STYLE === 'flat';
  const e = flat ? null : envMap();
  const w = meta.kind === 'weapon' && WEAPONS[meta.id];
  const paint = flat && w && w.color && meta.paint ? new THREE.Color(w.color) : null;
  const swapped = new Map();
  scene.traverse((o) => {
    if (!o.isMesh) return;
    o.geometry.userData.shared = true; // clones share it: freeTree leaves it alone
    o.castShadow = false; o.receiveShadow = false;
    if (flat) {
      const conv = (m) => {
        if (!swapped.has(m)) swapped.set(m, flatOf(m, paint && meta.paint.includes(m.name) ? paint : null));
        return swapped.get(m);
      };
      o.material = Array.isArray(o.material) ? o.material.map(conv) : conv(o.material);
    }
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) {
      for (const k of ['map', 'emissiveMap']) { // crunchy pixels at every preset, like the rest of the game
        if (m[k]) { m[k].magFilter = THREE.NearestFilter; m[k].minFilter = THREE.NearestMipmapNearestFilter; m[k].anisotropy = 1; m[k].needsUpdate = true; }
      }
      if (e && 'envMap' in m) { m.envMap = e; m.envMapIntensity = m.metalness > 0.5 ? 0.9 : 0.3; }
      if (m.transparent) { m.depthWrite = false; o.renderOrder = 2; }
      if (m.emissive && m.emissive.getHex() && m.emissiveIntensity > 0) { o.userData.noWrap = true; m.toneMapped = false; } // glows stay glowing under a skin
      if (m.userData.shared) continue;
      m.userData.shared = true;
      jankify(m); // potato vertex snap
      m.needsUpdate = true;
    }
  });
  AUTHORED[id] = { scene, meta };
  return true;
}

// a fresh copy of an authored model (geometry + materials shared), or null
export function authored(id) {
  const a = AUTHORED[id];
  if (!a) { late.seen.add(id); noteMiss(id); if (LAZY.has(id)) fetchLate(id); return null; }
  const c = a.scene.clone(true);
  c.userData.glbId = id;
  return { obj: c, meta: a.meta };
}
export const hasAuthored = (id) => { if (!AUTHORED[id]) noteMiss(id); return !!AUTHORED[id]; };
// candy paint in a colour the game picks (the rig's plates in your colour): the same clear-coat + studio reflection as
// the Blender models, and an emissive so setColor-style code can keep tinting it
export function glossyPaint(color, emi = 0.18) {
  const c = new THREE.Color(color);
  const m = new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.34, metalness: 0, clearcoat: 0.7, clearcoatRoughness: 0.2, emissive: c.clone().multiplyScalar(emi), envMap: MODEL_STYLE === 'flat' ? null : envMap(), envMapIntensity: 0.3, fog: false });
  return jankify(m);
}
// the mesh of a named node (or the first mesh under it) gets the game's own material: returns that mesh, or null
export function ownMat(root, name, mat) {
  const n = nodeIn(root, name);
  let m = null;
  if (n) n.traverse((o) => { if (!m && o.isMesh) m = o; });
  if (m && mat) { m.material = mat; m.userData.noWrap = true; }
  return m;
}
// every mesh whose material is called `name` (or starts with it, Blender adds .001) gets `mat`: the player's colour band
export function ownMatByName(root, name, mat) {
  root.traverse((o) => { if (o.isMesh && !Array.isArray(o.material) && o.material.name && o.material.name.startsWith(name)) o.material = mat; });
}

export const nodeIn = (g, n) => { let r = null; g.traverse((o) => { if (!r && o.name === n) r = o; }); return r; };

// a Blender weapon's hooks into the game, the same ones the code models have: the Redline's tachometer needle and
// HP-hot vents, the minigun's spinning barrels, and our own moving parts (pump, cylinder, hammer, bolt)
export function bindAuthored(g, meta) {
  if (meta.needle) g.userData.needle = nodeIn(g, meta.needle);
  if (meta.barrels) g.userData.barrels = nodeIn(g, meta.barrels);
  if (meta.vents) { // one unlit material per gun (weapons.js sets its colour from your HP), like the code model
    const vm = jankify(new THREE.MeshBasicMaterial({ color: 0x401010 }));
    g.traverse((o) => { if (o.isMesh && o.material && o.material.name === meta.vents) { o.material = vm; o.userData.noWrap = true; } });
    g.userData.vents = vm;
  }
  // the code models' other hooks: the cigarette's ember (weapons.js swells it as you charge), the card fan (weapons.js
  // deals your hand onto it: each card is its face mesh, back + edge are its children), the slapper's hand, a scythe's blade
  if (meta.tip) {
    const t = nodeIn(g, meta.tip);
    if (t) { if (g.userData.tip && g.userData.tip.isObject3D && g.userData.tip !== t) g.userData.tip.removeFromParent(); g.userData.tip = t; }
  }
  for (const k of ['hand', 'blade', 'card']) if (meta[k]) { const n = nodeIn(g, meta[k]); if (n) g.userData[k] = n; }
  if (Array.isArray(meta.fan)) {
    const fan = meta.fan.map((n) => nodeIn(g, n)).filter((c) => c && c.isMesh);
    if (fan.length) { g.userData.fan = fan; for (const c of fan) c.traverse((o) => { o.userData.noWrap = true; }); }
  }
  // a katana skin's blade (grows with kills, setKatana in models.js): a node straight under the root, pointing -z, katLen = origin to tip
  if (meta.katBlade && Number.isFinite(meta.katLen)) { const n = nodeIn(g, meta.katBlade); if (n) { g.userData.katBlade = n; g.userData.katLen = meta.katLen; } }
  if (meta.bow) bowRig(g, meta.bow);
  if (meta.noWrap) g.traverse((o) => { if (o.isMesh) o.userData.noWrap = true; }); // trophies (the Golden Sniper): no wrap covers them
  g.userData.parts = findParts(g, meta);
}

// the bow: weapons.js pulls the arrow back as you draw (and the code bow's whole string with it). here the string stays
// on the limb tips and bends to the nock instead, and the limbs flex. b = { string: [top, bottom] node names,
// tips: where each half meets its limb, nock: the arrow's nock at rest, limbs: [top, bottom] nodes (origin = where they
// leave the riser), flex: radians at full draw, draw: metres of pull at full draw }
const tmpV3 = new THREE.Vector3();
function bowRig(g, b) {
  const halves = (b.string || []).map((n) => nodeIn(g, n));
  if (halves.length !== 2 || !halves.every(Boolean) || !Array.isArray(b.tips) || !Array.isArray(b.nock)) return;
  const arrow = nodeIn(g, b.arrow || 'arrow');
  if (arrow) g.userData.arrow = arrow;
  if (b.arrowTip) { const t = nodeIn(g, b.arrowTip); if (t && t.isMesh) g.userData.arrowTip = t; }
  g.userData.string = new THREE.Object3D(); // weapons.js moves this one; the real string follows the arrow below
  g.updateMatrixWorld(true);
  const nock = new THREE.Vector3(...b.nock);
  const rig = { nock, draw: b.draw || 0.16, flex: b.flex || 0, halves: [], limbs: [] };
  halves.forEach((h, i) => {
    const T = new THREE.Vector3(...b.tips[i]), v0 = nock.clone().sub(T);
    const piv = new THREE.Object3D(); // +y of the pivot runs along the string half, so scale.y stretches it
    piv.position.copy(T); piv.rotation.x = Math.atan2(v0.z, v0.y);
    h.parent.add(piv); piv.updateMatrixWorld(true); piv.attach(h);
    rig.halves.push({ piv, T, len: v0.length() });
  });
  (b.limbs || []).forEach((n, i) => { const l = nodeIn(g, n); if (l) rig.limbs.push({ l, rx: l.rotation.x, sign: i ? -1 : 1 }); });
  g.userData.bowRig = rig;
}
function stepBow(g) {
  const r = g.userData.bowRig, a = g.userData.arrow;
  const d = a ? a.position.z : 0, k = Math.max(0, Math.min(1.2, d / r.draw));
  const phi = k * r.flex;
  for (const L of r.limbs) L.l.rotation.x = L.rx + L.sign * phi;
  r.halves.forEach((h, i) => {
    const L = r.limbs[i], s = i ? -1 : 1;
    const T = h.T, P = L ? L.l.position : null;
    let ty = T.y, tz = T.z;
    if (P && phi) { const y = T.y - P.y, z = T.z - P.z, c = Math.cos(s * phi), sn = Math.sin(s * phi); ty = P.y + y * c - z * sn; tz = P.z + y * sn + z * c; }
    h.piv.position.set(T.x, ty, tz);
    tmpV3.set(r.nock.x, r.nock.y - ty, r.nock.z + d - tz);
    h.piv.rotation.x = Math.atan2(tmpV3.z, tmpV3.y);
    h.piv.scale.y = Math.hypot(tmpV3.y, tmpV3.z) / h.len;
  });
}

// moving parts of Blender guns (nodes named in the file's metadata): the shotgun's forend racks with the pump
// animation, the revolver's cylinder turns a chamber and its hammer flicks on every shot, the sniper's bolt cycles
export function findParts(g, meta) {
  const p = {};
  if (meta.pump) { p.pump = nodeIn(g, meta.pump.node); if (p.pump) { p.pump0 = p.pump.position.z; p.travel = meta.pump.travel || 0.09; } else delete p.pump; }
  if (meta.cylinder) { p.cyl = nodeIn(g, meta.cylinder.node); p.step = meta.cylinder.step || Math.PI / 3; p.cylA = 0; p.cylTo = 0; if (!p.cyl) delete p.cyl; }
  if (meta.hammer) { p.hammer = nodeIn(g, meta.hammer.node); p.hamT = 1; if (!p.hammer) delete p.hammer; }
  if (meta.bolt) { p.bolt = nodeIn(g, meta.bolt.node); if (p.bolt) { p.bolt0 = p.bolt.position.z; p.lift = meta.bolt.lift || 1; p.btravel = meta.bolt.travel || 0.1; } else delete p.bolt; }
  return Object.keys(p).length ? p : null;
}
export function partsShot(g) {
  const p = g && g.userData.parts;
  if (!p) return;
  if (p.cyl) p.cylTo += p.step;
  if (p.hammer) p.hamT = 0;
}
export function stepParts(g, dt, an, at) {
  if (g && g.userData.bowRig) stepBow(g);
  const p = g && g.userData.parts;
  if (!p) return;
  if (p.pump) { // back on the way out, snap home: same timing as the pump_shotgun keys (0.1 s back, 0.17 s home)
    const k = an !== 'pump_shotgun' ? 0 : at < 0.1 ? at / 0.1 : at < 0.17 ? 1 - (at - 0.1) / 0.07 : 0;
    p.pump.position.z = p.pump0 + k * p.travel;
  }
  if (p.cyl) { p.cylA += (p.cylTo - p.cylA) * Math.min(1, dt * 24); p.cyl.rotation.z = -p.cylA; }
  if (p.hammer) { p.hamT = Math.min(1, p.hamT + dt); const t = p.hamT; p.hammer.rotation.x = t < 0.05 ? (t / 0.05) * 0.55 : Math.max(0, 0.55 * (1 - (t - 0.05) / 0.05)); }
  if (p.bolt) { // lift, run back, slam home, drop: the bolt_sniper keys (up by 0.12 s, back by 0.22, home by 0.3)
    let up = 0, back = 0;
    if (an === 'bolt_sniper') {
      up = at < 0.12 ? at / 0.12 : at < 0.3 ? 1 : at < 0.42 ? 1 - (at - 0.3) / 0.12 : 0;
      back = at < 0.12 ? 0 : at < 0.22 ? (at - 0.12) / 0.1 : at < 0.3 ? 1 - (at - 0.22) / 0.08 : 0;
    }
    p.bolt.rotation.z = up * p.lift;
    p.bolt.position.z = p.bolt0 + back * p.btravel;
  }
}

// knives + katanas (public/js/blades) stay code-built: they're real-reference models already. this gives them the
// Blender models' studio gloss so they sit with the rest: steel and brass get a satin metal sheen, wood a varnish, dark
// grips a satin coat, coloured bits candy paint. glows, see-through bits and the flat look stay as they are
const glossMats = new Map(), hsl = {};
function glossOf(m) {
  if (!m || !m.isMeshLambertMaterial || m.transparent || (m.emissive && m.emissive.getHex())) return m;
  let c = glossMats.get(m);
  if (c) return c;
  m.color.getHSL(hsl);
  const { h, s, l } = hsl;
  const steel = (s < 0.2 && l > 0.38) || (s < 0.25 && l > 0.6);
  const brass = h > 0.09 && h < 0.14 && s > 0.45 && s < 0.75 && l > 0.4 && l < 0.62;
  const wood = !brass && h > 0.02 && h < 0.13 && s > 0.25 && l < 0.85;
  const metal = steel || brass;
  c = new THREE.MeshPhysicalMaterial({
    name: m.name, color: m.color.clone(), map: m.map, side: m.side, flatShading: true,
    // steel: mostly metal with a bit of its own colour left (full metalness goes dark grey on flats that face away
    // from the lights; a low one + a strong reflection turned big flat blades into white plastic)
    metalness: metal ? 0.8 : 0, roughness: metal ? 0.25 : wood ? 0.55 : l < 0.25 ? 0.42 : 0.36,
    clearcoat: metal ? 0 : wood ? 0.3 : l < 0.25 ? 0.35 : 0.6, clearcoatRoughness: 0.25,
    envMap: envMap(), envMapIntensity: metal ? 0.9 : 0.3,
  });
  c.userData.shared = true;
  jankify(c);
  glossMats.set(m, c);
  return c;
}
export function glossBlade(g) {
  if (MODEL_STYLE === 'flat' || !Object.keys(AUTHORED).length || !envMap()) return; // comes with the Blender set: no models loaded, no gloss
  g.traverse((o) => { if (o.isMesh) o.material = Array.isArray(o.material) ? o.material.map(glossOf) : glossOf(o.material); });
}
