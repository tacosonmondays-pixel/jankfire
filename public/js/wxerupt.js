// MOUNT KABOOM ERUPTS (Islands + Islands S&D): weather.js's eruption, played from the Blender kit
// public/models/wx/wx_erupt.glb (tools/blender/weather/make_erupt.py). The kit's clips are scrubbed to the eruption's
// clock (the server's plan), so someone joining mid-eruption sees the same moment; the bombs fly the kit's baked unit arc
// stretched from the vent to where shared/weather.js wxBombs says each one lands (the same spots on every machine).
// Look only: the bombs hit nothing (yet). Potato: every other bomb, no smoke trails.
import * as THREE from 'three';
import { G } from './ctx.js';
import { MAP } from '/shared/map.js';
import { wxOf, wxErupt, wxBombs } from '/shared/weather.js';
import { glbLoader } from './glbkit.js';
import { sfx, eruptRumble } from './audio.js';

const E = { kit: null, key: '', heard: new Set(), boomed: '', dark: 0, flash: 0, info: { stage: '', bombs: 0, splats: 0 } };
const MAX = { bomb: 40, splat: 64 };

function load() {
  if (E.kit) return E.kit === 'loading' || E.kit === 'failed' ? null : E.kit;
  E.kit = 'loading';
  glbLoader().load('/models/wx/wx_erupt.glb', (g) => { try { E.kit = build(g); } catch (e) { console.warn('eruption kit', e); E.kit = 'failed'; } },
    undefined, (e) => { console.warn('eruption kit missing', e && e.message); E.kit = 'failed'; });
  return null;
}
function build(g) {
  const src = g.scene, meta = JSON.parse((src.getObjectByName('wx_erupt') || src).userData.jf || '{}');
  const root = new THREE.Group(); root.name = 'eruption';
  const node = (n) => src.getObjectByName(n);
  const hold = (n) => { const h = new THREE.Group(), s = node(n); s.position.set(0, 0, 0); h.add(s); root.add(h); return h; };
  const inst = (n, max) => {
    const s = node(n), m = new THREE.InstancedMesh(s.geometry, s.material, max);
    m.name = n + '_i'; m.count = 0; m.frustumCulled = false; m.castShadow = m.receiveShadow = false;
    m.instanceMatrix.setUsage(THREE.DynamicDrawUsage); root.add(m); return m;
  };
  const P = { plume: hold('wx_plume'), ash: hold('wx_ash'), pools: {}, bomb: inst('wx_bomb', MAX.bomb), trail: inst('wx_trail', MAX.bomb), splat: inst('wx_splat', MAX.splat) };
  for (const [m, v] of Object.entries(meta.maps || {})) { const o = node(v.pool); if (o) { root.add(o); P.pools[m] = o; } } // (world space: draped on that map's crater)
  for (const o of [P.plume, P.ash]) o.traverse((c) => { if (c.isMesh) c.castShadow = false; });
  const mixer = new THREE.AnimationMixer(root), acts = {}, sample = {};
  for (const c of g.animations) {
    if ((meta.sample || []).includes(c.name)) { sample[c.name] = Object.fromEntries(c.tracks.map((t) => [t.name.split('.').pop(), t.createInterpolant()])); continue; } // (evaluated per copy, never played)
    const a = mixer.clipAction(c);
    if ((meta.loops || []).includes(c.name)) a.play();
    else { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; a.play(); a.paused = true; } // (scrubbed: the eruption's clock sets the time)
    acts[c.name] = a;
  }
  G.scene.add(root); root.visible = false;
  return { root, P, mixer, acts, sample, meta };
}
const scrub = (K, n, s) => { const a = K.acts[n]; if (a) a.time = Math.max(0, Math.min(a.getClip().duration, s)); };

const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3(), _v = new THREE.Vector3(), _e = new THREE.Euler(), BACK = new THREE.Vector3(0, 0, 1);
function arcAt(K, b, u, out) { // where bomb b is, u 0..1 through its flight (the kit's baked arc, stretched to its ends)
  const A = K.sample.bomb_arc.position.evaluate(u);
  return out.set(b.sx + (b.x - b.sx) * A[0], b.sy + (b.y - b.sy) * A[0] + b.h * A[1], b.sz + (b.z - b.sz) * A[0]);
}

// one frame of the eruption. plan + t: the server's plan and how far into it; test: { at, len } forces one (wxTest).
// returns how hard to tint the sky (0-1)
export function eruptFrame(dt, plan, t, on, test) {
  const w = wxOf(MAP.id);
  let ph = null, P = plan;
  if (on && w && w.vent) {
    if (test) { ph = [t - test.at - 35, t - test.at - 35 + (test.len || 140), 'erupt', 1]; P = { m: MAP.id, s: 4242, ph: [ph] }; }
    else if (plan) ph = plan.ph.find((p) => p[2] === 'erupt' && t >= p[0] && t < p[1]) || null;
  }
  const K = ph ? load() : (E.kit && typeof E.kit === 'object' ? E.kit : null);
  if (!ph) { if (K) K.root.visible = false; eruptRumble(0); E.dark = 0; E.flash = 0; E.info = { stage: '', bombs: 0, splats: 0 }; return 0; }
  const st = wxErupt(ph, t), key = `${MAP.id}:${ph[0]}`, potato = (G.settings.jank | 0) === 0, vent = w.vent;
  if (key !== E.key) { E.key = key; E.heard.clear(); }
  // the sky + sound follow the stage even before the kit lands
  E.dark = st.stage === 'build' ? 0.25 * st.u : st.stage === 'blast' ? Math.min(1, 0.25 + st.at / 5) : 1 - st.u;
  eruptRumble(st.stage === 'build' ? 0.25 + 0.6 * st.u : st.stage === 'blast' ? 1 - 0.35 * Math.min(1, st.at / 25) : 0.65 * (1 - st.u));
  if (st.stage === 'blast' && st.at < 3 && E.boomed !== key) { E.boomed = key; sfx.eruptBoom(vent); E.flash = 1; G.shake = Math.max(G.shake || 0, 0.7); } // (late joiners get no boom: it went off already)
  E.flash = Math.max(0, E.flash - dt * 1.4);
  E.info = { stage: st.stage, u: +st.u.toFixed(2), bombs: 0, splats: 0 };
  if (!K) return E.dark;
  K.root.visible = true;
  K.P.plume.position.set(vent[0], vent[1], vent[2]); K.P.ash.position.set(vent[0], vent[1], vent[2]);
  for (const [m, o] of Object.entries(K.P.pools)) o.visible = m === MAP.id;
  // the clips, scrubbed to the eruption's clock: a wisp while it builds, the column goes up, then it all sinks back
  const S = st.stage, at = st.at;
  scrub(K, 'plume_rise', S === 'build' ? 0.5 * st.u : S === 'blast' ? at : 8 * (1 - st.u));
  const ash = S === 'build' ? 0 : S === 'blast' ? at : 30 * (1 - st.u);
  scrub(K, 'ash_spread', ash); K.P.ash.visible = ash > 0.3;
  const pool = S === 'build' ? Math.max(0, (st.u - 0.55) / 0.45) * 1.5 : S === 'blast' ? 1.5 + at : 4 * (1 - st.u);
  scrub(K, 'pool_rise', pool); scrub(K, 'pool_rise_sd', pool);
  K.mixer.update(Math.min(dt, 0.1)); // (the churn turns; the scrubbed ones are paused at the times set above)
  bombs(K, P, t, potato);
  return E.dark;
}

function bombs(K, plan, t, potato) {
  const L = wxBombs(plan, t), cam = G.camera.position, B = K.P.bomb, Tr = K.P.trail, Sp = K.P.splat, SP = K.sample.splat_pop;
  let nb = 0, ns = 0;
  for (let i = 0; i < L.length; i++) {
    const b = L[i];
    if (b.t0 > t) break; // (in launch order)
    if (t > b.t + 3 || (potato && i % 2)) continue;
    if (t < b.t) { // in flight: the bomb tumbling along its arc, its smoke trailing back along where it came from
      if (nb >= MAX.bomb) continue;
      const u = (t - b.t0) / (b.t - b.t0), Q = K.sample.bomb_arc.quaternion.evaluate(u);
      arcAt(K, b, u, _p); _q.set(Q[0], Q[1], Q[2], Q[3]);
      B.setMatrixAt(nb, _m.compose(_p, _q, _s.set(1, 1, 1)));
      if (!potato) {
        arcAt(K, b, Math.max(0, u - 0.03), _v); _v.sub(_p).normalize(); // (back along the flight)
        _q2.setFromUnitVectors(BACK, _v); Tr.setMatrixAt(nb, _m.compose(_p, _q2, _s.set(1, 1, 0.6 + 0.6 * Math.min(1, u * 4))));
      }
      nb++;
      // the whistle as it comes down near you, then the thud (only for bombs landing close: a few at a time)
      const near = Math.hypot(b.x - cam.x, b.z - cam.z) < 45;
      if (near && b.t - t < 1.1 && !E.heard.has(i)) { E.heard.add(i); sfx.bombWhistle([b.x, b.y, b.z], Math.max(0.2, b.t - t)); }
    } else { // landed: a splat that pops in, sits and cools away
      if (ns >= MAX.splat) continue;
      const age = t - b.t, sc = SP.scale.evaluate(age);
      _q.setFromEuler(_e.set(0, i * 2.4, 0));
      Sp.setMatrixAt(ns++, _m.compose(_p.set(b.x, b.y + 0.03, b.z), _q, _s.set(sc[0], sc[1], sc[2])));
      if (age < 0.3 && !E.heard.has(-1 - i)) { E.heard.add(-1 - i); if (Math.hypot(b.x - cam.x, b.z - cam.z) < 80) sfx.bombThud([b.x, b.y, b.z]); }
    }
  }
  B.count = nb; Tr.count = potato ? 0 : nb; Sp.count = ns;
  B.instanceMatrix.needsUpdate = Tr.instanceMatrix.needsUpdate = Sp.instanceMatrix.needsUpdate = true;
  E.info.bombs = nb; E.info.splats = ns;
}

export const eruptLook = () => ({ dark: E.dark, flash: E.flash });
export function eruptState() {
  const K = E.kit && typeof E.kit === 'object' ? E.kit : null;
  let draws = 0, tris = 0;
  if (K && K.root.visible) K.root.traverseVisible((o) => { if (!o.isMesh || (o.isInstancedMesh && !o.count)) return; draws++; tris += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3 * (o.isInstancedMesh ? o.count : 1); });
  return { ...E.info, kit: K ? 'loaded' : E.kit || 'none', visible: !!(K && K.root.visible), draws, tris: Math.round(tris), dark: +E.dark.toFixed(2) };
}
