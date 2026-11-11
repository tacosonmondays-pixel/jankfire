// The train set's models (OVERDUE, m06 TICKETS, PLEASE): Dale's works train and the Under-Hill Loop's tunnel kit, drawn
// in place of trainfight.js's box stand-ins. Loaded here with their own loader path, like the boss (not by the city's
// prop loader). Nothing in this file is rules: the room's boxes stay the collision (shared/story/train.js is THE
// TABLE both were built to), and if a file never comes the boxes and the old tunnel are simply still there.
//   rp_train.glb   car_wagon / car_flat / car_van / car_loco, each cover_* its own node (origin = the middle of its foot)
//   rp_tunnel.glb  tk_lining, tk_lining_b, tk_niche, tk_track (+ tk_track_far), tk_cables, tk_bulbs, tk_bulb_lit, tk_bulb_dead, ...
//   rp_train.parts.json  what it was built to, the markers (lamps, the back rail, the couplings, the cab)
// tools/blender/make_rp_train.py builds all of it. docs/story/train/TRAIN_MODEL.md has the parts and the numbers.
import * as THREE from 'three';
import { glbLoader } from '../glbkit.js';
import { ARENA, CARS, CAR, COVER } from '/shared/story/train.js';

const BOXQ = /[?&]trainbox=1\b/.test(location.search); // ?trainbox=1: keep the box stand-ins (for a before / after picture, or a slow machine)
const SEG = 6, BULB = 12, PERIOD = 96; // a kit piece's length · the bulbs' pitch (trainfight's) · the layout repeats every this many metres
const NEAR = [-42, 44]; // track detail and cables are only drawn this near the train (z): past it the fog has them
const v3 = (a) => Array.isArray(a) && a.length === 3 && a.every(Number.isFinite);

let _halo = null;
function haloTex() {
  if (_halo) return _halo;
  const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d'), gr = x.createRadialGradient(32, 32, 1, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.2, 'rgba(255,255,255,0.5)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = gr; x.fillRect(0, 0, 64, 64);
  _halo = new THREE.CanvasTexture(c); return _halo;
}
const halo = (color, size, opacity = 0.7) => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTex(), color, transparent: true, opacity, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); s.scale.setScalar(size); return s; };

// as trainfight's prep does for the boss: nearest textures, the studio reflection turned well down (it is dark in here),
// lamps that keep their glow. k: how much of the reflection the painted parts get
function prep(root, env, k) {
  root.traverse((o) => {
    if (!o.isMesh) return; o.castShadow = false; o.receiveShadow = false;
    for (const m of [].concat(o.material)) {
      for (const key of ['map', 'emissiveMap', 'metalnessMap', 'roughnessMap']) if (m[key]) { m[key].magFilter = THREE.NearestFilter; m[key].minFilter = THREE.NearestMipmapNearestFilter; m[key].anisotropy = 1; m[key].needsUpdate = true; }
      m.envMap = env || null; m.envMapIntensity = m.transparent ? 0.7 : k;
      if (m.emissive && m.emissive.getHex() && m.emissiveIntensity > 0) m.toneMapped = false;
      if (m.transparent) m.depthWrite = false;
    }
  });
}

export function makeTrainSet() {
  const S = { train: null, tunnel: null, parts: null, loading: false, tries: 0, retryAt: 0, err: null, off: BOXQ };
  const get = (u) => new Promise((ok, bad) => glbLoader().load(u, ok, undefined, bad));
  // fetch the two files and the parts list (once; a load that failed waits before it tries again, as the boss's does)
  S.load = (env, done) => {
    if (S.off || S.train || S.loading || performance.now() < S.retryAt) return; S.loading = true;
    Promise.all([get('/models/story/rp_train.glb'), get('/models/story/rp_tunnel.glb').catch((e) => { console.warn('tunnel kit', e); return null; }), fetch('/models/story/rp_train.parts.json').then((r) => (r.ok ? r.json() : null)).catch(() => null)]).then(([tr, tk, parts]) => {
      prep(tr.scene, env, 0.2); if (tk) prep(tk.scene, env, 0.04); // (the tunnel takes little of the studio: the bulbs light it)
      S.train = tr.scene; S.tunnel = tk ? tk.scene : null; S.parts = parts && typeof parts === 'object' ? parts : null; S.loading = false; S.tries = 0;
      try { done && done(S); } catch (e) { console.warn('train set', e); }
    }).catch((e) => { console.warn('train model', e); S.loading = false; S.err = e; S.retryAt = performance.now() + Math.min(60000, 2000 * 2 ** S.tries++); });
  };

  // ---------------------------------------------------------------- the train: each car's model into its box group
  // cars: { wagon, flat, van, loco } the stand-in's groups (trainfight moves / hides the wagon's when it is bitten off).
  // the boxes in them are hidden, not removed: turn the model off and they are back
  S.dress = (cars) => {
    if (!S.train || S.dressed) return null;
    const N = {}; S.train.traverse((o) => { if (o.name) N[o.name] = o; });
    const built = (S.parts && S.parts.cars) || {};
    for (const c of CARS) {
      const node = N['car_' + c.id], grp = cars[c.id]; if (!node || !grp) continue;
      const b = built[c.id], dz = b && Array.isArray(b.z) && Number.isFinite(b.z[0]) ? c.z0 - b.z[0] : 0; // (the table moved a car since the build: it follows)
      grp.userData.boxes = grp.children.slice(); for (const m of grp.userData.boxes) m.visible = false;
      node.position.set(0, 0, dz); grp.add(node); grp.userData.model = node;
    }
    const k = {}; // the cover pieces go where THE TABLE has them today
    for (const [car, x, z] of COVER) { const i = k[car] = (k[car] ?? -1) + 1, n = N[`cover_${car}_${i}`], p = N['car_' + car]; if (n && p) n.position.set(x, CAR[car].deck, z - p.position.z); }
    for (const n of Object.values(N)) if (/_lod$|_bitten$/.test(n.name)) n.visible = false;
    // the lamps that are lit get a little glow you can see down the tunnel
    const mk = (S.parts && S.parts.markers) || {}, glows = [];
    const glow = (at, car, color, size, op) => { if (!v3(at) || !cars[car]) return; const h = halo(color, size, op); h.position.set(at[0], at[1], at[2]); cars[car].add(h); glows.push(h); };
    glow(mk.tail_lamp, 'wagon', 0xff3020, 1.1, 0.75); glow(mk.headlamp && mk.headlamp.pos, 'loco', 0xfff0c8, 2.6, 0.8); glow(mk.work_lamp && mk.work_lamp.pos, 'van', 0xffe0b0, 1.6, 0.5); glow(mk.van_lantern, 'van', 0xffb060, 0.9, 0.5);
    S.dressed = { N, cars, glows };
    S.bitten(false);
    return S.dressed;
  };
  // the first lunge: the flatbed shows its torn end (the wagon itself is trainfight's to throw)
  S.bitten = (on) => { const d = S.dressed; if (!d) return; if (d.N.flat_end) d.N.flat_end.visible = !on; if (d.N.flat_end_bitten) d.N.flat_end_bitten.visible = !!on; };
  // back to boxes (and forward again): for the before / after pictures
  S.show = (on) => { const d = S.dressed; if (!d) return; for (const g of Object.values(d.cars)) { if (g.userData.model) g.userData.model.visible = on; for (const m of g.userData.boxes || []) m.visible = !on; } for (const h of d.glows) h.visible = on; };

  // ---------------------------------------------------------------- the tunnel: the kit laid end to end, scrolled past
  // g: the set's group. old: what the stand-in drew ({ bore, ribs, sl, cable, bulbs }): hidden while the kit is on
  S.lay = (g, old) => {
    if (!S.tunnel || S.laid) return null;
    const kit = S.tunnel; kit.updateMatrixWorld(true);
    const grp = new THREE.Group(); grp.name = 'rp_tunnel_kit'; g.add(grp);
    const nSeg = Math.ceil((ARENA.z1 - ARENA.z0) / SEG) + 1, nBulb = Math.ceil((ARENA.z1 - ARENA.z0) / BULB) + 1;
    const piece = (name, count) => { // every mesh under a kit node as an instanced mesh
      const n = kit.getObjectByName(name), out = []; if (!n) return out;
      n.traverse((o) => { if (!o.isMesh) return; const im = new THREE.InstancedMesh(o.geometry, o.material, count); im.frustumCulled = false; im.count = 0; im.castShadow = im.receiveShadow = false; im.userData.base = o.matrixWorld.clone(); grp.add(im); out.push(im); });
      return out;
    };
    const P = { lining: piece('tk_lining', nSeg), liningB: piece('tk_lining_b', nSeg), niche: piece('tk_niche', nSeg), track: piece('tk_track', nSeg), far: piece('tk_track_far', nSeg), cables: piece('tk_cables', nSeg),
      wire: piece('tk_bulbs', nBulb), lit: piece('tk_bulb_lit', nBulb), dead: piece('tk_bulb_dead', nBulb), marker: piece('tk_marker', 4), signal: piece('tk_signal', 4) };
    if (!P.far.length) P.far = null;
    // the dark at both ends (the room's end walls are bricks: a tunnel should go on into nothing)
    const dark = new THREE.MeshBasicMaterial({ color: 0x050307, fog: false }), disc = new THREE.CircleGeometry(ARENA.boreR + 0.3, 24);
    for (const [z, ry] of [[ARENA.z0 + 0.4, 0], [ARENA.z1 - 0.4, Math.PI]]) { const m = new THREE.Mesh(disc, dark); m.position.set(0, ARENA.cy, z); m.rotation.y = ry; grp.add(m); }
    const xc = Math.sqrt(ARENA.boreR ** 2 - ARENA.cy ** 2) - 0.55, m4 = new THREE.Matrix4(), r4 = new THREE.Matrix4();
    const put = (ims, i, z, x = 0, ry = 0) => { for (const im of ims) { m4.makeTranslation(x, 0, z); if (ry) m4.multiply(r4.makeRotationY(ry)); im.setMatrixAt(i, m4.multiply(im.userData.base)); } };
    const end = (ims, n) => { for (const im of ims) { im.count = n; im.instanceMatrix.needsUpdate = true; } };
    const L = { grp, P, old, dist: 0 };
    // dz: how far the tunnel went past this frame · bz / bon: each bulb's z and whether it is lit (trainfight's own count of them)
    L.step = (dz, bz, bon) => {
      L.dist = (L.dist + dz) % PERIOD;
      const sh = L.dist % SEG, k0 = Math.floor(L.dist / SEG); let nl = 0, nb = 0, nn = 0, nt = 0, nf = 0, nc = 0, nm = 0, ns = 0;
      for (let j = 0; j < nSeg; j++) {
        const z = ARENA.z0 + SEG * j - sh, k = (j + k0) % (PERIOD / SEG), near = z + SEG > NEAR[0] && z < NEAR[1];
        if (k % 4 === 1 && P.niche.length) put(P.niche, nn++, z); else if (k % 4 === 3 && P.liningB.length) put(P.liningB, nb++, z); else put(P.lining, nl++, z);
        if (near || !P.far) put(P.track, nt++, z); else put(P.far, nf++, z);
        if (near) put(P.cables, nc++, z);
        if (k === 6 && nm < 4) put(P.marker, nm++, z + 3, -xc, Math.PI / 2);
        if (k === 13 && ns < 4) put(P.signal, ns++, z + 3, xc - 0.1, 0);
      }
      end(P.lining, nl); end(P.liningB, nb); end(P.niche, nn); end(P.track, nt); if (P.far) end(P.far, nf); end(P.cables, nc); end(P.marker, nm); end(P.signal, ns);
      let on = 0, off = 0;
      for (let i = 0; i < bz.length && i < nBulb; i++) { put(P.wire, i, bz[i]); if (bon[i]) put(P.lit, on++, bz[i]); else put(P.dead, off++, bz[i]); }
      end(P.wire, Math.min(bz.length, nBulb)); end(P.lit, on); end(P.dead, off);
    };
    L.show = (on) => { grp.visible = on; for (const k of ['bore', 'ribs', 'sl', 'cable']) if (old[k]) old[k].visible = !on; for (const b of old.bulbs || []) b.visible = !on; };
    L.show(true);
    S.laid = L;
    return L;
  };
  return S;
}
