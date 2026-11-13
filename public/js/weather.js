// Weather player: plays the server's weather timeline (shared/weather.js, server/weather.js) with Blender-made kits
// (public/models/wx/<kit>.glb, tools/blender/weather/). Everything you see is from the kit: this file only loads it,
// places copies round the camera, plays and stops its baked clips, and nudges the existing sky / fog / light numbers
// for the frame being drawn (put back right after, so nothing else ever sees them). Sounds come from audio.js.
// Settings > weather off = none of it. Potato: a smaller rain box, no splashes. Not the story city's paper storms
// (city/weather.js): those are their own thing.
import * as THREE from 'three';
import { G } from './ctx.js';
import { MAP, MAPS, BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { WX_KINDS, wxAt, wxStrikes, wxCheck, wxOf } from '/shared/weather.js';
import { glbLoader } from './glbkit.js';
import { net } from './net.js';
import { skyParts } from './world.js';
import { sceneryGroup } from './scenery.js';
import { rainLoop, windLoop, sfx } from './audio.js';
import { starsFrame, starsLook, starsState } from './wxstars.js'; // star showers (Rooftop, Desert)
import { eruptFrame, eruptLook, eruptState } from './wxerupt.js'; // Mount Kaboom erupts (Islands)
import { liquidAt } from './liquids.js'; // (every water surface the map draws: sea, pools, ponds, the shallows)

const W = {
  plan: null, t0: 0, snap: false, k: 0, kind: '', test: null, // test: { k, s } forced from a test (wxTest)
  kits: {}, // kit id -> { root, mixer, parts, meta } | 'loading' | 'failed'
  cols: new Map(), roof: null, roofMap: '', key: '', strikes: { i: -2, list: [], next: 0 }, bolt: null, thunder: [],
  pud: { key: '', list: [] }, cover: 0, flash: 0,
};
const now = () => performance.now() / 1000;

// ---------------------------------------------------------------- the server's timeline
net.on('wx', (m) => {
  const c = wxCheck(m);
  if (!c) return; // (anything malformed is ignored: the weather just stays as it was)
  W.plan = c; W.t0 = now() - c.el; W.snap = true; W.strikes.i = -2;
});

// ---------------------------------------------------------------- the kit
function kit(id) {
  const have = W.kits[id];
  if (have) return typeof have === 'object' ? have : null;
  W.kits[id] = 'loading';
  glbLoader().load(`/models/wx/${id}.glb`, (g) => { try { W.kits[id] = build(g, SPEC[id]); } catch (e) { console.warn('weather kit', id, e); W.kits[id] = 'failed'; } },
    undefined, (e) => { console.warn('weather kit missing', id, e && e.message); W.kits[id] = 'failed'; });
  return null;
}
const MAXI = { curtain: 12 * 12, splash: 40, puddle: 48 };
// the curtain kits (rain, snow): which node is which piece. a kit without a piece just doesn't have it (snow: no
// splashes, ripples or lightning; its 'puddles' are patches of settled snow)
const SPEC = {
  wx_rain: { root: 'wx_rain', curtain: 'wx_curtain', splashA: 'wx_splash_a', splashB: 'wx_splash_b', puddle: 'wx_puddle', ripple: 'wx_ripple', clouds: 'wx_clouds', bolts: ['wx_bolt_0', 'wx_bolt_1', 'wx_bolt_2'], pud: 0.3, lift: 0.015 },
  wx_snow: { root: 'wx_snow', curtain: 'wx_snow_curtain', puddle: 'wx_snowpatch', clouds: 'wx_snow_clouds', bolts: [], pud: 0.45, lift: 0.02 },
};
const CURTAIN = new Set(['rain', 'snow']); // (the kinds this file plays itself; the eruption and the stars have their own files)
function build(g, spec) {
  const src = g.scene, meta = JSON.parse((src.getObjectByName(spec.root) || src).userData.jf || '{}');
  const root = new THREE.Group(); root.name = 'weather';
  const node = (n) => src.getObjectByName(n);
  const inst = (n, max, name) => {
    const s = n && node(n);
    if (!s) return null;
    const m = new THREE.InstancedMesh(s.geometry, s.material, max);
    m.name = name || n; m.count = 0; m.frustumCulled = false; m.castShadow = m.receiveShadow = false;
    m.instanceMatrix.setUsage(THREE.DynamicDrawUsage); root.add(m); return m;
  };
  const P = {
    curtain: inst(spec.curtain, MAXI.curtain), // (the clip moves this one itself: translation only)
    splashA: inst(spec.splashA, MAXI.splash, 'wx_splash_a_i'), splashB: inst(spec.splashB, MAXI.splash, 'wx_splash_b_i'),
    puddle: inst(spec.puddle, MAXI.puddle), ripple: inst(spec.ripple, MAXI.puddle, 'wx_ripple_i'),
  };
  // the clips that scale splashes + ripples drive stand-in nodes; each copy takes the stand-in's scale (scaling the
  // instanced mesh itself would scale where the copies are, not just their size)
  for (const n of ['wx_splash_a', 'wx_splash_b', 'wx_ripple']) { const o = new THREE.Object3D(); o.name = n; root.add(o); P['px_' + n] = o; } // (unused by a kit without them)
  const hold = (n) => { const h = new THREE.Group(), s = node(n); s.position.set(0, 0, 0); s.castShadow = false; h.add(s); root.add(h); h.visible = false; return h; };
  P.clouds = hold(spec.clouds);
  P.bolts = spec.bolts.map((n) => hold(n));
  for (const o of [P.clouds, ...P.bolts]) o.traverse((c) => { if (c.material) { c.material.fog = false; c.frustumCulled = false; } }); // (sky things: past the fog)
  const mixer = new THREE.AnimationMixer(root), acts = {};
  for (const c of g.animations) {
    const a = mixer.clipAction(c);
    if ((meta.strikes || []).includes(c.name)) { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; } else a.play();
    acts[c.name] = a;
  }
  G.scene.add(root); root.visible = false;
  return { root, mixer, P, acts, meta, spec, tile: meta.tile || 3, per: meta.period || 6 };
}

// ---------------------------------------------------------------- where the rain can fall
// the roof test: anything above this spot (map boxes, plus the drawn-only ones big enough to keep rain off)
function roofBoxes() {
  if (W.roofMap === MAP.id && W.roof) return W.roof;
  const def = MAPS[MAP.id], deco = def && def.deco ? def.deco.filter((b) => b.min && (b.max[0] - b.min[0]) * (b.max[2] - b.min[2]) >= 0.5) : [];
  W.roof = deco.length ? [...BOXES, ...deco] : BOXES; W.roofMap = MAP.id; W.cols.clear(); W.pud.key = '';
  return W.roof;
}
const UP = [0, 1, 0], DOWN = [0, -1, 0], _o = [0, 0, 0];
function covered(x, y, z) { _o[0] = x; _o[1] = y; _o[2] = z; return !!raycast(_o, UP, 120, roofBoxes()); }
// a 3 m column of rain is drawn only if it's open to the sky at your height all across (no rain indoors, none
// leaking in through a wall the column straddles)
function colOpen(x0, z0, y, T) {
  const key = `${x0},${z0},${Math.floor(y / 2)}`;
  let v = W.cols.get(key);
  if (v === undefined) {
    if (W.cols.size > 6000) W.cols.clear();
    const e = 0.15;
    v = !covered(x0 + T / 2, y, z0 + T / 2) && !covered(x0 + e, y, z0 + e) && !covered(x0 + T - e, y, z0 + e) && !covered(x0 + e, y, z0 + T - e) && !covered(x0 + T - e, y, z0 + T - e);
    W.cols.set(key, v);
  }
  return v;
}
// the floor under a spot that the sky can see (the first top face from high above), or null
function floorAt(x, z, cy, lo, hi) {
  _o[0] = x; _o[1] = cy + 30; _o[2] = z;
  const h = raycast(_o, DOWN, 60, roofBoxes());
  if (!h || h.axis !== 1) return null;
  const def = MAPS[MAP.id], sea = def && Number.isFinite(def.seaY) ? def.seaY : -Infinity, y0 = _o[1] - h.t;
  // water: the sea's level, a drawn liquid over the spot (pool, pond, the shallows) or a box that is water / lava / glass
  const liq = liquidAt(x, y0, z, 0.4, 4), y = Math.max(y0, sea, liq ? liq.top : -Infinity);
  const wet = y > y0 + 0.01 || !!liq || WETMAT.test((h.box && h.box.mat) || '');
  return y >= cy - lo && y <= cy + hi ? { y, b: h.box, wet } : null;
}
const WETMAT = /water|sea|lava|mud|wetsand|glass|pool|lake|ice|acid|goo|slime/i; // (no puddle or snow patch on these: it would read as a hole)
const hash = (a, b, c = 0) => { let h = Math.imul(a | 0, 374761393) ^ Math.imul(b | 0, 668265263) ^ Math.imul(c | 0, 1274126177); h = Math.imul(h ^ (h >>> 13), 1103515245); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };

const _dir = new THREE.Vector3(), _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3(), _e = new THREE.Euler(), _c = new THREE.Color();
function curtain(K, cam, k, potato) {
  const T = K.tile, H = K.per, n = potato ? 8 : 12, half = (n / 2) * T;
  const bx = Math.floor((cam.x - half) / T), bz = Math.floor((cam.z - half) / T);
  const y0 = (Math.floor(cam.y / H) - 1) * H; // (the 4-period column then covers at least 6 m under you and over you)
  _dir.set(0, 0, -1).applyQuaternion(G.camera.quaternion); // looking up into it, the streaks over you all point at one spot (warp speed):
  const up = Math.max(0, (_dir.y - 0.45) / 0.55), clear = up > 0 ? 4 + 10 * up : 0; // so the columns right overhead go, more the steeper you look
  const key = `${Math.round(up * 8)},${Math.floor((cam.x + 0.7) / T)},${Math.floor((cam.x - 0.7) / T)},${Math.floor((cam.z + 0.7) / T)},${Math.floor((cam.z - 0.7) / T)},${y0},${Math.floor(cam.y / 2)},${n},${Math.round(k * 20)},${MAP.id}`;
  if (key === W.key) return;
  W.key = key;
  const m = K.P.curtain;
  let c = 0;
  for (let i = 0; i < n && k > 0; i++) for (let j = 0; j < n; j++) {
    const ix = bx + i, iz = bz + j;
    if (hash(ix, iz) > 0.25 + 0.75 * k) continue; // light rain: some columns stay dry (they fill in as it picks up)
    if (cam.x > ix * T - 0.7 && cam.x < ix * T + T + 0.7 && cam.z > iz * T - 0.7 && cam.z < iz * T + T + 0.7) continue;
    if (clear && Math.hypot(ix * T + T / 2 - cam.x, iz * T + T / 2 - cam.z) < clear) continue; // (streaks right in your face are giant bars: not in your own column)
    if (!colOpen(ix * T, iz * T, cam.y, T)) continue;
    _m.makeTranslation(ix * T, y0, iz * T); m.setMatrixAt(c++, _m);
  }
  m.count = c; m.instanceMatrix.needsUpdate = true;
}
// splashes: each set hops to fresh floor spots while its clip has it shrunk to nothing
function splashes(K, cam, k, which, n) {
  const m = K.P[which];
  m.count = n; m.userData.n = n;
  if (!n) return;
  const L = m.userData.spots || (m.userData.spots = []);
  L.length = 0;
  for (let i = 0, tries = 0; L.length < n && tries < n * 3; tries++) {
    const a = Math.random() * Math.PI * 2, r = 1.5 + Math.sqrt(Math.random()) * 14, x = cam.x + Math.cos(a) * r, z = cam.z + Math.sin(a) * r;
    const f = floorAt(x, z, cam.y, 14, 6);
    if (f) L.push([x, f.y + 0.004, z, Math.random() * 6.28, 0.75 + Math.random() * 0.6]);
    i++;
  }
  m.count = L.length;
}
function poseCopies(m, px, lift = 0) {
  const L = m.userData.spots || [];
  for (let i = 0; i < m.count && i < L.length; i++) {
    const [x, y, z, yaw, s] = L[i];
    _q.setFromEuler(_e.set(0, yaw, 0)); _p.set(x, y + lift, z); _s.copy(px.scale).multiplyScalar(s);
    m.setMatrixAt(i, _m.compose(_p, _q, _s));
  }
  m.instanceMatrix.needsUpdate = true;
}
// puddles: spots on wide flat floors, picked per 5 m cell (the same cell always has the same puddle, so they don't
// jump about as you walk), grown with the rain
function puddles(K, cam, k, max) {
  const C = 5, R = 4, cx = Math.floor(cam.x / C), cz = Math.floor(cam.z / C), key = `${cx},${cz},${Math.floor(cam.y / 3)},${MAP.id},${K.spec.root}`;
  if (key !== W.pud.key) {
    W.pud.key = key; const L = W.pud.list; L.length = 0;
    for (let i = -R; i <= R && L.length < max; i++) for (let j = -R; j <= R && L.length < max; j++) {
      const gx = cx + i, gz = cz + j;
      if (hash(gx, gz, 7) > K.spec.pud) continue;
      const x = (gx + 0.15 + hash(gx, gz, 8) * 0.7) * C, z = (gz + 0.15 + hash(gx, gz, 9) * 0.7) * C, s = 0.8 + hash(gx, gz, 10) * 0.9;
      const f = floorAt(x, z, cam.y, 9, 4);
      if (!f || !f.b || !f.b.min || f.wet) continue; // (no puddles on the sea)
      const r = 0.95 * s;
      if (x - r < f.b.min[0] || x + r > f.b.max[0] || z - r < f.b.min[2] || z + r > f.b.max[2]) continue; // all of it on the one floor
      if (liquidAt(x - r, f.y, z - r, 0.4, 4) || liquidAt(x + r, f.y, z - r, 0.4, 4) || liquidAt(x - r, f.y, z + r, 0.4, 4) || liquidAt(x + r, f.y, z + r, 0.4, 4)) continue; // (nor half in a pond)
      L.push([x, f.y + K.spec.lift, z, hash(gx, gz, 11) * 6.28, s, (hash(gx, gz, 12) - 0.5) * 0.7 * s, (hash(gx, gz, 13) - 0.5) * 0.7 * s]);
    }
  }
  const L = W.pud.list, grow = Math.min(1, Math.max(0, (k - 0.15) / 0.5)), m = K.P.puddle, rp = K.P.ripple || { count: 0, instanceMatrix: {} }, px = K.P.px_wx_ripple;
  m.count = grow > 0.02 ? L.length : 0; rp.count = K.P.ripple && grow > 0.3 ? L.length : 0;
  for (let i = 0; i < m.count; i++) {
    const [x, y, z, yaw, s, ox, oz] = L[i];
    _q.setFromEuler(_e.set(0, yaw, 0));
    m.setMatrixAt(i, _m.compose(_p.set(x, y, z), _q, _s.set(s * grow, 1, s * grow)));
    if (i < rp.count) rp.setMatrixAt(i, _m.compose(_p.set(x + ox * grow, y, z + oz * grow), _q, _s.copy(px.scale).multiplyScalar(0.8 + 0.3 * s)));
  }
  m.instanceMatrix.needsUpdate = true; rp.instanceMatrix.needsUpdate = true;
}

// ---------------------------------------------------------------- each frame
export function updateWeather(dt) {
  const cam = G.camera, t = now() - W.t0;
  const on = G.joined && G.settings.weather !== false && !!cam;
  const plan = W.plan && W.plan.m === MAP.id ? W.plan : null;
  let cur = W.test ? { k: W.test.k, s: W.test.s, i: W.test.i ?? -1 } : plan ? wxAt(plan, t) : { k: '', s: 0, i: -1 };
  if (!on) cur = { k: '', s: 0, i: -1 };
  // an eruption plays on its own (wxerupt.js); everything below is the rain (its downpour comes as a rain phase after it)
  const et = W.test && W.test.k === 'erupt' ? W.test : null;
  if (et && et.t == null) et.t = t;
  W.edark = eruptFrame(dt, W.test ? null : plan, t, on, et ? { at: et.at + (t - et.t), len: et.len } : null); // (a test of something else: no eruption)
  starsFrame(dt, W.test ? null : plan, t, on, W.test && W.test.k === 'stars' ? W.test : null); // star showers (wxstars.js)
  if (cur.k && !CURTAIN.has(cur.k)) cur = { k: '', s: 0, i: cur.i };
  if (cur.k && cur.k !== W.kind && W.k > 0.05 && !W.test && !W.snap) cur = { k: '', s: 0, i: cur.i }; // (rain to snow straight after: the last one eases out first)
  if (cur.k) W.kind = cur.k;
  if (W.snap || (W.test && CURTAIN.has(W.test.k))) { W.k = cur.s; W.snap = false; } // (just joined: straight into whatever the weather is now)
  else { const e = Math.min(1, Math.max(dt, now() - (W.last || 0))); W.k += Math.max(-e / 6, Math.min(e / 6, cur.s - W.k)); } // (a fresh plan or a new map eases over ~6 s of real time, whatever the frame rate)
  W.last = now();
  if (W.k < 0.003 || !on) W.k = 0; // (switched off in settings, or out of the match: gone at once, not eased out)
  if (!on && W.bolt) { W.bolt.h.visible = false; W.bolt = null; W.thunder.length = 0; }
  const kd = W.kind && WX_KINDS[W.kind] ? WX_KINDS[W.kind].kit : '';
  const K = W.k > 0 && kd ? kit(kd) : (kd && W.kits[kd] && typeof W.kits[kd] === 'object' ? W.kits[kd] : null);
  for (const [id, x] of Object.entries(W.kits)) if (typeof x === 'object' && x !== K) x.root.visible = false;
  const w = wxOf(MAP.id) || {}, k = W.k;
  W.dark = k * (w.dark ?? 1);
  // the sound: hiss outside, a drum on the roof inside
  W.cover = k > 0 && cam ? (covered(cam.position.x, cam.position.y + 0.3, cam.position.z) ? 1 : 0) : 0;
  rainLoop(on && W.kind === 'rain' ? k : 0, W.cover); windLoop(on && W.kind === 'snow' ? k : 0, W.cover); // (snow: a soft cold wind)
  for (let i = W.thunder.length - 1; i >= 0; i--) if (now() >= W.thunder[i][0]) { sfx.thunder(W.thunder[i][1], W.cover); W.thunder.splice(i, 1); }
  if (!K) { W.flash = 0; return; }
  const p = cam.position, potato = (G.settings.jank | 0) === 0;
  K.root.visible = k > 0 || !!W.bolt;
  if (!K.root.visible) { W.flash = 0; return; }
  // the clips: one mixer step (splash stand-ins wrap -> those copies move while they're shrunk away)
  const prev = { a: phase(K, 'wx_splash_a_clip'), b: phase(K, 'wx_splash_b_clip') };
  K.mixer.update(Math.min(dt, 0.1));
  if (K.P.splashA) {
    const ph = { a: phase(K, 'wx_splash_a_clip'), b: phase(K, 'wx_splash_b_clip') }, ns = potato ? 0 : Math.round(MAXI.splash * k);
    const more = (m) => ns > (m.userData.n || 0) + 4 || (ns && !m.userData.n); // (fewer: just show fewer; a lot more asked for: fresh spots now)
    if ((prev.a < 0.5 && ph.a >= 0.5) || more(K.P.splashA)) splashes(K, p, k, 'splashA', ns); else K.P.splashA.count = Math.min(ns, (K.P.splashA.userData.spots || []).length);
    if (ph.b < prev.b || more(K.P.splashB)) splashes(K, p, k, 'splashB', ns); else K.P.splashB.count = Math.min(ns, (K.P.splashB.userData.spots || []).length);
    poseCopies(K.P.splashA, K.P.px_wx_splash_a); poseCopies(K.P.splashB, K.P.px_wx_splash_b);
  }
  curtain(K, p, k, potato);
  puddles(K, p, k, potato ? 16 : MAXI.puddle);
  // the storm clouds drift in from upwind as it starts and sit over you while it rains
  const cl = K.P.clouds, def = MAPS[MAP.id];
  cl.visible = k > 0.02 && !(def && def.sealed);
  cl.position.set(p.x - (1 - Math.min(1, k * 1.6)) * 900, p.y - 25, p.z);
  // lightning: the plan's strikes for this shower (same for everyone), each a baked bolt clip + the lights flashing
  if (K.P.bolts.length) lightning(K, plan, cur.i, t, p, k); else W.flash = 0;
}
function phase(K, n) { const a = K.acts[n]; return a ? (a.time / a.getClip().duration) % 1 : 0; }

function lightning(K, plan, i, t, p, k) {
  const S = W.strikes;
  if (plan && i !== S.i && !W.test) { S.i = i; S.list = i >= 0 ? wxStrikes(plan, i) : []; S.next = 0; while (S.next < S.list.length && S.list[S.next][0] < t - 0.5) S.next++; }
  if (W.test && W.test.strike) { S.list = [[t, W.test.strike[0], W.test.strike[1], W.test.strike[2] | 0]]; S.next = 0; W.test.strike = null; }
  while (S.next < S.list.length && S.list[S.next][0] <= t) {
    const [, ang, dist, b] = S.list[S.next++];
    if (k < 0.25) continue; // (a drizzle doesn't throw bolts)
    const h = K.P.bolts[b % 3], a = K.acts['strike_' + (b % 3)], def = MAPS[MAP.id];
    const gx = p.x + Math.cos(ang) * dist, gz = p.z + Math.sin(ang) * dist, gy = def && Number.isFinite(def.floorY) ? def.floorY : p.y - 15;
    h.position.set(gx, gy, gz); h.rotation.set(0, Math.atan2(p.x - gx, p.z - gz), 0); // (the bolt's flat side to you)
    if (W.bolt && W.bolt.h !== h) W.bolt.h.visible = false; // (a new strike cuts the last one short)
    h.visible = true;
    if (a) { a.reset(); a.play(); }
    W.bolt = { h, a, b };
    W.thunder.push([now() + 0.25 + dist / 343, Math.max(0.2, 1 - (dist - 140) / 200) * Math.min(1, k + 0.3)]);
  }
  if (W.bolt) {
    const { h, a } = W.bolt, s = h.children[0] ? h.children[0].scale.x : 0;
    W.flash = Math.max(0, Math.min(1, s)) * Math.min(1, k + 0.3); // (the lights flash with the baked strokes)
    if (!a || !a.isRunning()) { h.visible = false; W.bolt = null; W.flash = 0; }
  } else W.flash = 0;
}

// ---------------------------------------------------------------- the sky, fog and lights for this frame only
const SAVE = { on: false };
const STORM_FOG = new THREE.Color(0x3b4152), STORM_SKY = new THREE.Color(0x4e5470), FLASH = new THREE.Color(0xe4ecff), HEMI_T = new THREE.Color(0x9aa6c8);
// each curtain kind's look: rain goes slate grey, snow goes a cold blue-white haze
const LOOK = {
  rain: { fog: STORM_FOG, fk: 0.65, near: 0.45, far: 0.4, sky: STORM_SKY, sk: 0.75, far2: 0.6, hemi: HEMI_T, hk: 0.4, hd: 0.4, sun: 0.65 },
  snow: { fog: new THREE.Color(0xd4dff0), fk: 0.55, near: 0.6, far: 0.5, sky: new THREE.Color(0xc4d0e8), sk: 0.7, far2: 0.45, hemi: new THREE.Color(0xdce8ff), hk: 0.55, hd: 0.1, sun: 0.55 },
};
export function wxPre() {
  const d = Math.min(1.2, W.dark || 0), f = W.flash || 0, el = eruptLook(), e = Math.min(1, el.dark || 0), ef = el.flash || 0, sl = starsLook(), st = Math.min(1, sl.dark || 0);
  if (!(d > 0.002 || f > 0.002 || e > 0.002 || ef > 0.002 || st > 0.002 || el.hide) || !G.scene || !G.scene.fog) return;
  const Lk = LOOK[W.kind] || LOOK.rain;
  const sc = G.scene, fog = sc.fog, hemi = sc.children.find((o) => o.isHemisphereLight), sun = sc.children.find((o) => o.isDirectionalLight), sky = skyParts();
  if (![fog.near, fog.far].every(Number.isFinite)) return;
  SAVE.on = true;
  SAVE.fog = [fog.near, fog.far, fog.color.getHex()];
  SAVE.hemi = hemi ? [hemi, hemi.intensity, hemi.color.getHex()] : null;
  SAVE.sun = sun ? [sun, sun.intensity, sun.color.getHex()] : null;
  SAVE.sky = sky.sky ? sky.sky.material.color.getHex() : null;
  SAVE.vis = [sky.sun, ...sky.clouds].filter(Boolean).map((o) => [o, o.visible]);
  SAVE.far = [];
  const g = sceneryGroup(); // the mountains / far skyline are unlit colours pre-mixed with the sky: they dim with it
  if (g) g.traverse((o) => { const m = o.material; if (m && m.isMeshBasicMaterial && !SAVE.far.some((x) => x[0] === m)) SAVE.far.push([m, m.color.getHex()]); });
  const dk = Math.min(1, d);
  fog.near *= 1 - Lk.near * dk; fog.far *= 1 - Lk.far * dk;
  fog.color.lerp(Lk.fog, Lk.fk * dk).lerp(FLASH, 0.35 * f);
  if (hemi) { hemi.intensity = hemi.intensity * (1 - Lk.hd * d) * (1 + 1.5 * f) + 1.4 * f; hemi.color.lerp(Lk.hemi, Lk.hk * dk).lerp(FLASH, 0.5 * f); } // (+ a flat boost: a dark room flashes too)
  for (const [m] of SAVE.far) m.color.multiply(_c.setHex(0xffffff).lerp(Lk.sky, Lk.far2 * dk)).lerp(FLASH, 0.3 * f);
  if (sun) sun.intensity = sun.intensity * (1 - Lk.sun * dk) + 1.5 * f;
  if (sky.sky) sky.sky.material.color.lerp(Lk.sky, Lk.sk * dk).lerp(FLASH, 0.6 * f);
  if (st > 0.002) { // a star shower: the sky goes deep violet (a day map all the way to dusk), the sun sinks low and pink
    const du = sl.dusk ? st : st * 0.35;
    fog.color.lerp(DUSK_FOG, 0.75 * du); fog.near *= 1 - 0.2 * du;
    if (hemi) { hemi.intensity *= 1 - 0.45 * du; hemi.color.lerp(DUSK_HEMI, 0.6 * du); }
    if (sun) { sun.intensity *= 1 - 0.7 * du; sun.color.lerp(DUSK_SUN, 0.7 * du); }
    if (sky.sky) sky.sky.material.color.lerp(DUSK_SKY, 0.85 * du);
    for (const [m] of SAVE.far) m.color.multiply(_c.setHex(0xffffff).lerp(DUSK_SKY, 0.7 * du));
  }
  if (e > 0.002 || ef > 0.002) { // the eruption: ash-brown haze closing in, an orange sky, the sun gone dull and red, the boom's flash
    fog.near *= 1 - 0.55 * e; fog.far *= 1 - 0.5 * e; fog.color.lerp(ASH_FOG, 0.8 * e).lerp(ERUPT_FLASH, 0.4 * ef);
    if (hemi) { hemi.intensity = hemi.intensity * (1 - 0.3 * e) + 1.2 * ef; hemi.color.lerp(ASH_HEMI, 0.75 * e).lerp(ERUPT_FLASH, 0.4 * ef); }
    if (sun) { sun.intensity = sun.intensity * (1 - 0.55 * e) + 1.2 * ef; sun.color.lerp(ASH_SUN, 0.85 * e); }
    if (sky.sky) sky.sky.material.color.lerp(ASH_SKY, 0.95 * e).lerp(ERUPT_FLASH, 0.5 * ef);
    for (const [m] of SAVE.far) m.color.multiply(_c.setHex(0xffffff).lerp(ASH_SKY, 0.75 * e));
  }
  if (el.hide) for (const o of wisp()) { SAVE.vis.push([o, o.visible]); o.visible = false; } // (the volcano's old wisp: the column has swallowed it)
  if (Math.max(dk, e, sl.dusk ? st : 0) > 0.35) for (const [o] of SAVE.vis) o.visible = false; // (the sun cube and the pink fair-weather clouds go behind the storm)
}
const DUSK_FOG = new THREE.Color(0x3a2a6a), DUSK_SKY = new THREE.Color(0x30205e), DUSK_HEMI = new THREE.Color(0x8a6ad0), DUSK_SUN = new THREE.Color(0xff6a9a);
const ASH_FOG = new THREE.Color(0x6a3426), ASH_SKY = new THREE.Color(0xc0502a), ASH_HEMI = new THREE.Color(0xff8a4a), ASH_SUN = new THREE.Color(0xff5a1a), ERUPT_FLASH = new THREE.Color(0xffb060);
// the volcano's smoke wisp: the arch meshes drawn with its see-through smoke materials (archfield.js names them arch_<name>)
const WISP = /^arch_b(wisp|smoke)/;
let wispList = [], wispKey = '', wispT = 0;
function wisp() {
  const n = performance.now();
  if (wispKey !== MAP.id || (!wispList.length && n - wispT > 3000)) { wispKey = MAP.id; wispT = n; wispList = []; G.scene.traverse((o) => { if (o.isMesh && o.material && WISP.test(o.material.name || '')) wispList.push(o); }); }
  return wispList;
}
export function wxPost() {
  if (!SAVE.on) return;
  SAVE.on = false;
  const sc = G.scene, fog = sc.fog;
  [fog.near, fog.far] = SAVE.fog; fog.color.setHex(SAVE.fog[2]);
  if (SAVE.hemi) { SAVE.hemi[0].intensity = SAVE.hemi[1]; SAVE.hemi[0].color.setHex(SAVE.hemi[2]); }
  if (SAVE.sun) { SAVE.sun[0].intensity = SAVE.sun[1]; SAVE.sun[0].color.setHex(SAVE.sun[2]); }
  const sky = skyParts();
  if (sky.sky && SAVE.sky != null) sky.sky.material.color.setHex(SAVE.sky);
  for (const [o, v] of SAVE.vis) o.visible = v;
  for (const [m, hx] of SAVE.far) m.color.setHex(hx);
}

// tests + screenshots: what the weather's doing, and forcing it (k: kind, s: strength; strike: [angle, dist, bolt])
export function wxState() {
  const K = W.kind && W.kits[WX_KINDS[W.kind].kit];
  const kk = typeof K === 'object' && K ? K : null;
  return { map: MAP.id, plan: !!(W.plan && W.plan.m === MAP.id), phases: W.plan ? W.plan.ph.length : 0, t: now() - W.t0, k: W.k, kind: W.kind, kit: kk ? 'loaded' : K || 'none',
    erupt: eruptState(), stars: starsState(), wisp: wispList.length, visible: !!(kk && kk.root.visible), draws: kk && kk.root.visible ? draws(kk.root) : 0, tris: kk && kk.root.visible ? draws(kk.root, true) : 0, tiles: kk ? kk.P.curtain.count : 0, splashes: kk && kk.P.splashA ? kk.P.splashA.count + kk.P.splashB.count : 0, puddles: kk ? kk.P.puddle.count : 0, cover: W.cover, flash: W.flash };
}
// what the weather adds to a frame: one draw per visible piece (the copies are instanced), and their triangles
function draws(root, tris) {
  let n = 0;
  root.traverseVisible((o) => { if (!o.isMesh || (o.isInstancedMesh && !o.count)) return; n += tris ? (o.geometry.index ? o.geometry.index.count / 3 : o.geometry.attributes.position.count / 3) * (o.isInstancedMesh ? o.count : 1) : 1; });
  return Math.round(n);
}
export function wxTest(o) { W.test = o ? { k: o.k || 'rain', s: o.s ?? 1, i: o.i, strike: o.strike || null, at: o.at || 0, len: o.len || 140 } : null; W.key = ''; } // (k 'erupt': at = s since the blast began, negative = still building)
