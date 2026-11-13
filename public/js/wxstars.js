// STAR SHOWER (Rooftop now and then, the Desert): weather.js's meteors, played from the Blender kit
// public/models/wx/wx_stars.glb (tools/blender/weather/make_stars.py). Each meteor is where shared/weather.js
// wxMeteors puts it (the same ones for everyone) on a sky dome round the camera, flying the kit's baked unit flight;
// the sparkles sit on the dome and play the kit's twinkle. Look only. Potato: half the meteors, fewer sparkles.
import * as THREE from 'three';
import { G } from './ctx.js';
import { MAP } from '/shared/map.js';
import { wxOf, wxAt, wxMeteors, wxRand } from '/shared/weather.js';
import { glbLoader } from './glbkit.js';
import { sfx } from './audio.js';

const S = { kit: null, key: '', list: [], heard: new Set(), dark: 0, dusk: 0, info: { meteors: 0, sparkles: 0 }, chime: 0 };
const MAX = { met: 24, big: 3, tw: 40 }, DOME = 380, LEN = { meteor_fly: 1.0, meteor_big_fly: 2.0, twinkle: 1.2 };

function load() {
  if (S.kit) return typeof S.kit === 'object' ? S.kit : null;
  S.kit = 'loading';
  glbLoader().load('/models/wx/wx_stars.glb', (g) => { try { S.kit = build(g); } catch (e) { console.warn('stars kit', e); S.kit = 'failed'; } },
    undefined, (e) => { console.warn('stars kit missing', e && e.message); S.kit = 'failed'; });
  return null;
}
function build(g) {
  const src = g.scene, root = new THREE.Group(); root.name = 'starshower';
  const inst = (n, max) => {
    const s = src.getObjectByName(n), m = new THREE.InstancedMesh(s.geometry, s.material, max);
    m.name = n + '_i'; m.count = 0; m.frustumCulled = false; m.castShadow = m.receiveShadow = false; m.material.fog = false; // (sky things: past the fog)
    m.instanceMatrix.setUsage(THREE.DynamicDrawUsage); root.add(m); return m;
  };
  const P = { met: inst('wx_meteor', MAX.met), big: inst('wx_meteor_big', MAX.big), tw: inst('wx_twinkle', MAX.tw) };
  const sample = {};
  for (const c of g.animations) sample[c.name] = Object.fromEntries(c.tracks.map((t) => [t.name.split('.').pop(), t.createInterpolant()])); // (evaluated per copy)
  G.scene.add(root); root.visible = false;
  return { root, P, sample };
}

const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3(), _d = new THREE.Vector3(), _t = new THREE.Vector3(), _u = new THREE.Vector3(), X = new THREE.Vector3(1, 0, 0), ZV = new THREE.Vector3(0, 0, 1), UPV = new THREE.Vector3(0, 1, 0);
const dome = (az, el, out) => out.set(Math.cos(el) * Math.cos(az), Math.sin(el), Math.cos(el) * Math.sin(az));

// one frame. plan + t: the server's plan and how far into it; test: { s, at } forces a shower (wxTest k 'stars').
export function starsFrame(dt, plan, t, on, test) {
  const w = wxOf(MAP.id);
  let i = -1, s = 0, P = plan;
  if (on && test) { P = { m: MAP.id, s: 777, ph: [[0, 3600, 'stars', test.s ?? 1]] }; if (test.t0 == null) test.t0 = t; t = 20 + (test.at || 0) + (t - test.t0); i = 0; s = test.s ?? 1; }
  else if (on && plan) { const c = wxAt(plan, t); if (c.k === 'stars') { i = c.i; s = c.s; } }
  const K = i >= 0 ? load() : (S.kit && typeof S.kit === 'object' ? S.kit : null);
  S.dark = s; S.dusk = w && w.dusk ? 1 : 0;
  if (i < 0 || !s) { if (K) K.root.visible = false; S.info = { meteors: 0, sparkles: 0 }; return; }
  const key = `${MAP.id}:${P.s}:${i}`;
  if (key !== S.key) { S.key = key; S.list = wxMeteors(P, i); S.heard.clear(); }
  if (!K) return;
  K.root.visible = true;
  const cam = G.camera.position, potato = (G.settings.jank | 0) === 0;
  // meteors: in flight for their clip's length, each from its spot on the dome along its heading, dipping as it goes
  let nm = 0, nb = 0;
  for (let j = 0; j < S.list.length; j++) {
    const [t0, az, el, hd, big] = S.list[j];
    if (t0 > t) break;
    const life = big ? LEN.meteor_big_fly : LEN.meteor_fly, u = (t - t0) / life;
    if (u >= 1 || (potato && j % 2 && !big)) continue;
    const m = big ? K.P.big : K.P.met;
    if ((big ? nb : nm) >= (big ? MAX.big : MAX.met)) continue;
    const A = K.sample[big ? 'meteor_big_fly' : 'meteor_fly'], tr = A.position.evaluate(u), sc = A.scale.evaluate(u);
    dome(az, el, _d); // where it starts, on the dome
    _t.crossVectors(UPV, _d).normalize(); _u.crossVectors(_d, _t).normalize(); // (the dome's sideways and upward there)
    _t.multiplyScalar(Math.cos(hd)).addScaledVector(_u, Math.sin(hd) * 0.5 - 0.6).normalize(); // its heading: across and always a bit down
    const way = (big ? 0.6 : 0.4) * DOME;
    _p.copy(_d).multiplyScalar(DOME).addScaledVector(_t, tr[0] * way).addScaledVector(UPV, tr[1] * way).add(cam);
    _q.setFromUnitVectors(X, _t);
    // (out on the dome a kit-size streak is a hair: drawn longer and much fatter, so the white-hot head and the tail read
    // as a comic meteor. the low ones, off towards the horizon, read further away: bigger still)
    const far = 1 + 0.45 * Math.max(0, 1 - (el - 0.35) / 0.75), ML = (big ? 4 : 3.4) * far, MW = (big ? 6.6 : 5.6) * far;
    m.setMatrixAt(big ? nb++ : nm++, _m.compose(_p, _q, _s.set(sc[0] * ML, sc[1] * MW, sc[2] * MW)));
    if (!S.heard.has(j) && u < 0.3) { S.heard.add(j); if (big || j % 3 === 0) sfx.meteor(big); }
  }
  K.P.met.count = nm; K.P.big.count = nb;
  // sparkles: fixed spots on the dome (from the shower's seed), each blinking in its own turn every few seconds
  const r = wxRand(P.s ^ 0x51ed27), TW = K.sample.twinkle, nt = Math.round((potato ? 16 : MAX.tw) * Math.min(1, s * 1.2));
  let n = 0;
  for (let j = 0; j < nt; j++) {
    const az = r() * Math.PI * 2, el = 0.3 + r() * 1.0, per = 3 + r() * 4, off = r() * per, ph = (t + off) % per, sz = 6 + r() * 7;
    if (ph >= LEN.twinkle) continue;
    const sc = TW.scale.evaluate(ph), ro = TW.quaternion.evaluate(ph);
    dome(az, el, _d); _p.copy(_d).multiplyScalar(DOME * 0.95).add(cam);
    _q.setFromUnitVectors(ZV, _d.negate()); _q2.set(ro[0], ro[1], ro[2], ro[3]); _q.multiply(_q2); // (its face to you, the kit's turn on top)
    K.P.tw.setMatrixAt(n++, _m.compose(_p, _q, _s.set(sc[0] * sz, sc[1] * sz, sc[2] * sz)));
  }
  K.P.tw.count = n;
  for (const m of [K.P.met, K.P.big, K.P.tw]) m.instanceMatrix.needsUpdate = true;
  if (n && (S.chime -= dt) < 0) { S.chime = 1.5 + Math.random() * 3; sfx.twinkle(); }
  S.info = { meteors: nm + nb, big: nb, sparkles: n };
}

export const starsLook = () => ({ dark: S.dark, dusk: S.dusk });
export function starsState() {
  const K = S.kit && typeof S.kit === 'object' ? S.kit : null;
  let draws = 0, tris = 0;
  if (K && K.root.visible) K.root.traverseVisible((o) => { if (!o.isInstancedMesh || !o.count) return; draws++; tris += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3 * o.count; });
  return { ...S.info, kit: K ? 'loaded' : S.kit || 'none', visible: !!(K && K.root.visible), draws, tris, s: +S.dark.toFixed(2) };
}
