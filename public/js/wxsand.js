// SANDSTORM (Desert now and then, the Bazaar): weather.js's sandstorm, played from the Blender kit
// public/models/wx/wx_sand.glb (tools/blender/weather/make_sand.py). The wall of dust is placed round the camera, slid
// in from upwind as the storm rolls in (and out downwind as it passes) on the plan's clock, so everyone sees the front
// hit at the same moment; the grit and sand ribbons are tiles round the camera playing their blow clips (none indoors:
// weather.js's roof test, the same as the rain); the tumbleweeds and the rag fly the kit's baked clips, sampled per copy,
// started on open flat ground. The wind blows along +x. Look only. Potato: fewer grit tiles, no ribbons, one tumbleweed,
// no rag.
import * as THREE from 'three';
import { G } from './ctx.js';
import { MAP, MAPS } from '/shared/map.js';
import { WX_KINDS, wxAt } from '/shared/weather.js';
import { glbLoader } from './glbkit.js';
import { sfx, sandLoop } from './audio.js';

const S = { kit: null, key: '', dark: 0, clock: 0, tw: [], rag: [], gusted: '', info: { tiles: 0, tumble: 0, rags: 0, front: 0 } };
const MAX = { tile: 10 * 10, tw: 4, rag: 2 }, DRIFT = 420; // DRIFT: m upwind the wall starts (and ends up downwind)

function load() {
  if (S.kit) return typeof S.kit === 'object' ? S.kit : null;
  S.kit = 'loading';
  glbLoader().load('/models/wx/wx_sand.glb', (g) => { try { S.kit = build(g); } catch (e) { console.warn('sand kit', e); S.kit = 'failed'; } },
    undefined, (e) => { console.warn('sand kit missing', e && e.message); S.kit = 'failed'; });
  return null;
}
function build(g) {
  const src = g.scene, meta = JSON.parse((src.getObjectByName('wx_sand') || src).userData.jf || '{}');
  const root = new THREE.Group(); root.name = 'sandstorm';
  const node = (n) => src.getObjectByName(n);
  let sky = null; // (the wall shares its material with the grit in the file: its own copy, past the fog like the sky)
  const hold = (n) => { const h = new THREE.Group(), s = node(n); s.position.set(0, 0, 0); s.castShadow = s.receiveShadow = false; s.frustumCulled = false; s.material = sky || (sky = s.material.clone()); sky.fog = false; h.add(s); root.add(h); return h; };
  const inst = (n, max, name) => {
    const s = node(n), m = new THREE.InstancedMesh(s.geometry, s.material, max);
    m.name = name || n; m.count = 0; m.frustumCulled = false; m.castShadow = m.receiveShadow = false;
    m.instanceMatrix.setUsage(THREE.DynamicDrawUsage); root.add(m); return m;
  };
  const P = { wall: hold('wx_sand_wall'), billow: hold('wx_sand_billow'), grit: inst('wx_sand_grit', MAX.tile), ribbon: inst('wx_sand_ribbon', MAX.tile), // (the clips slide these two themselves: translation only)
    tw: inst('wx_tumbleweed', MAX.tw, 'wx_tumbleweed_i'), rag: inst('wx_sand_rag', MAX.rag, 'wx_sand_rag_i') };
  const mixer = new THREE.AnimationMixer(root), sample = {};
  for (const c of g.animations) {
    if ((meta.sample || []).includes(c.name)) { sample[c.name] = Object.fromEntries(c.tracks.map((t) => [t.name.split('.').pop(), t.createInterpolant()])); continue; } // (evaluated per copy)
    mixer.clipAction(c).play();
  }
  G.scene.add(root); root.visible = false;
  return { root, P, mixer, sample, meta, T: meta.tile || 4, len: meta.len || { tumble_bounce: 3.6, rag_fly: 4 } };
}

const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3();
const hash = (a, b) => { let h = Math.imul(a | 0, 374761393) ^ Math.imul(b | 0, 668265263); h = Math.imul(h ^ (h >>> 13), 1103515245); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };

// one frame. plan + t: the server's plan and how far into it; test: { s, at } forces a storm (wxTest k 'sand': at = s
// since it began rolling in). H: weather.js's roof + floor tests. returns nothing; sandLook() has the sky's share
export function sandFrame(dt, plan, t, on, test, H) {
  let P = plan, ph = null, s = 0;
  if (on && test) { P = { m: MAP.id, s: 555, ph: [[0, 3600, 'sand', test.s ?? 1]] }; if (test.t0 == null) test.t0 = t; t = (test.at ?? 60) + (t - test.t0); }
  if (on && P) { const c = wxAt(P, t); if (c.k === 'sand') { ph = P.ph[c.i]; s = c.s; } }
  const K = ph ? load() : (S.kit && typeof S.kit === 'object' ? S.kit : null);
  S.dark = s;
  const cam = G.camera && G.camera.position, cover = ph && cam ? (H.covered(cam.x, cam.y + 0.3, cam.z) ? 1 : 0) : 0;
  sandLoop(ph ? s : 0, cover);
  if (!ph) { if (K) K.root.visible = false; S.tw.length = 0; S.rag.length = 0; S.info = { tiles: 0, tumble: 0, rags: 0, front: 0 }; return; }
  // the front: the wall comes in from upwind over its first `front` seconds and goes on downwind over its last
  const F = WX_KINDS.sand.front, uin = (t - ph[0]) / F, uout = (ph[1] - t) / F;
  const off = uin < 1 ? -(1 - uin) * DRIFT : uout < 1 ? (1 - uout) * DRIFT : 0;
  const gk = `${MAP.id}:${ph[0]}`;
  if (uin >= 0.55 && uin < 0.75 && S.gusted !== gk) { S.gusted = gk; sfx.sandGust(); } // (the wall hitting you. late joiners: it hit already)
  S.info.front = Math.round(off);
  if (!K) return;
  K.root.visible = true;
  const potato = (G.settings.jank | 0) === 0, def = MAPS[MAP.id];
  for (const o of [K.P.wall, K.P.billow]) { o.position.set(cam.x + off, cam.y - 14, cam.z); o.visible = !(def && def.sealed); }
  K.mixer.update(Math.min(dt, 0.1)); S.clock += Math.min(dt, 0.1); // (the tumbleweeds' clock: the game's frames, like the clips)
  tiles(K, cam, s, potato, H);
  tumble(K, cam, s, potato, H);
}

// the grit + ribbon tiles round the camera. a tile's sand slides a whole tile downwind and its upwind copy fills in
// behind, so a tile is only drawn where it and the tiles either side along the wind are open to the sky (none blows
// in through a wall, none indoors)
function tiles(K, cam, k, potato, H) {
  const T = K.T, n = potato ? 6 : 10, half = (n / 2) * T, bx = Math.floor((cam.x - half) / T), bz = Math.floor((cam.z - half) / T);
  const y0 = Math.floor(cam.y - 1.6) - 0.3; // (the tile stands on your feet, give or take: a 1 m step, so a hop doesn't drag it along)
  const key = `${bx},${bz},${y0},${n},${Math.round(k * 20)},${MAP.id}`;
  if (key === S.key) return;
  S.key = key;
  const G1 = K.P.grit, R1 = K.P.ribbon;
  let c = 0;
  for (let i = 0; i < n && k > 0; i++) for (let j = 0; j < n; j++) {
    const ix = bx + i, iz = bz + j;
    if (hash(ix, iz) > 0.2 + 0.8 * k) continue; // (a light storm: patchy)
    if (!H.colOpen((ix - 1) * T, iz * T, cam.y, T) || !H.colOpen(ix * T, iz * T, cam.y, T) || !H.colOpen((ix + 1) * T, iz * T, cam.y, T)) continue;
    _m.makeTranslation(ix * T, y0, iz * T); G1.setMatrixAt(c, _m); R1.setMatrixAt(c, _m); c++;
  }
  G1.count = c; R1.count = potato ? 0 : c; S.info.tiles = c;
  G1.instanceMatrix.needsUpdate = true; R1.instanceMatrix.needsUpdate = true;
}

// is a run of `len` m downwind from (x, y, z) open flat ground (or open air, h above it)? the same floor height all the
// way, open to the sky, nothing in the way
// (flying: the rag swoops 1.2 m up and down and 1 m to each side, so the room for all of that)
const RUN = { flat: [[0.4, 0]], fly: [[-1.3, -1.1], [-1.3, 1.1], [0, 0], [2.1, -1.1], [2.1, 1.1]] };
function clearRun(H, x, y, z, len, h, flat) {
  const env = flat ? RUN.flat : RUN.fly;
  for (let d = 0; d <= len; d += len / 6) {
    if (flat) { const f = H.floorAt(x + d, z, y, 0.6, 0.6); if (!f || f.wet || Math.abs(f.y - y) > 0.45) return false; }
    for (const [dy, dz] of env) if (H.covered(x + d, y + h + dy, z + dz)) return false;
  }
  for (const [dy, dz] of env) if (H.ray([x, y + h + dy + 0.1, z + dz], [1, 0, 0], len + 1)) return false;
  return true;
}
// tumbleweeds bouncing past and a rag flapping by: each starts upwind of you on open ground, flies its clip, and a new
// one is found when it's done (local to you: they're just scenery)
function tumble(K, cam, k, potato, H) {
  const now = S.clock, nTw = k < 0.3 ? 0 : potato ? 1 : MAX.tw, nRag = potato || k < 0.5 ? 0 : MAX.rag;
  const spawn = (L, n, len, dist, fly) => {
    for (let i = L.length - 1; i >= 0; i--) if (now - L[i].t0 > len) L.splice(i, 1);
    if (L.length >= n || (L.next || 0) > now) return;
    L.next = now + 0.4 + Math.random() * 1.2; // (a few tries a second, not a frame-rate's worth of rays)
    for (let tries = 0; tries < 3; tries++) {
      const x = cam.x - 6 - Math.random() * 22, z = cam.z + (Math.random() - 0.5) * 36;
      const f = H.floorAt(x, z, cam.y - 1.6, 4, 3);
      if (!f || f.wet) continue;
      const h = fly ? 1.6 + Math.random() * 2 : 0;
      if (!clearRun(H, x, f.y, z, dist, h, !fly)) continue;
      L.push({ x, y: f.y + h, z, t0: now, heard: 0 }); return;
    }
  };
  spawn(S.tw, nTw, K.len.tumble_bounce, K.meta.tumbleX || 26, false);
  spawn(S.rag, nRag, K.len.rag_fly, K.meta.ragX || 36, true);
  const pose = (L, m, A, len, boing) => {
    let c = 0;
    for (const o of L) {
      const age = now - o.t0, tr = A.position.evaluate(age), q = A.quaternion.evaluate(age), sc = A.scale.evaluate(age);
      _p.set(o.x + tr[0], o.y + tr[1], o.z + tr[2]); _q.set(q[0], q[1], q[2], q[3]); _s.set(sc[0], sc[1], sc[2]);
      m.setMatrixAt(c++, _m.compose(_p, _q, _s));
      if (boing) while (o.heard < boing.length && age >= boing[o.heard]) { const d = _p.distanceTo(cam); if (d < 35) sfx.boing([_p.x, _p.y, _p.z], Math.max(0.25, 1 - d / 35)); o.heard++; }
    }
    m.count = c; m.instanceMatrix.needsUpdate = true;
  };
  pose(S.tw, K.P.tw, K.sample.tumble_bounce, K.len.tumble_bounce, K.meta.boing || []);
  pose(S.rag, K.P.rag, K.sample.rag_fly, K.len.rag_fly, null);
  S.info.tumble = S.tw.length; S.info.rags = S.rag.length;
}

export const sandLook = () => ({ dark: S.dark });
export function sandState() {
  const K = S.kit && typeof S.kit === 'object' ? S.kit : null;
  let draws = 0, tris = 0;
  if (K && K.root.visible) K.root.traverseVisible((o) => { if (!o.isMesh || (o.isInstancedMesh && !o.count)) return; draws++; tris += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3 * (o.isInstancedMesh ? o.count : 1); });
  return { ...S.info, kit: K ? 'loaded' : S.kit || 'none', visible: !!(K && K.root.visible), draws, tris: Math.round(tris), s: +S.dark.toFixed(2) };
}
