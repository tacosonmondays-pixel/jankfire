// The city streamer: keeps the chunks around the camera loaded at the right detail, off the main thread.
// Rings (radii per render preset, shared/city/plan.js RINGS), by distance from the camera to the chunk's square:
//   collision  5 x 5 chunks round you: boxes in the shared ChunkWorld (movement, bullets, grenades)
//   props      instanced Blender props (props.js)
//   near       the full mesh (lod 0)          mid   one merged lod 1 mesh      far   one impostor mesh for ALL far chunks
// Chunks are built + meshed in 2 workers (chunkworker.js); the main thread uploads at most a few ms of buffers a frame.
// Meshes leave memory in LRU order once they're a ring past where they're drawn.
import * as THREE from 'three';
import { CHUNK, CITIES, RINGS, inCity, districtWeights, chunkId } from '/shared/city/plan.js';
import { chunkBoxes } from '/shared/city/chunk.js';
import { ChunkWorld } from '/shared/city/world.js';
import { cityMaterials, cityUniforms, NL } from './mats.js';
import { buildPropGroup, freeProps, onPropModel, propModel } from './props.js';
import './propcode.js'; // code stand-ins for every story prop (until its Blender model loads)
import { Crowd } from './crowd.js'; // the people standing about
import { Weather } from './weather.js'; // paper storms

const KINDS = ['solid', 'flesh', 'glow', 'glass', 'acid'];
const HYST = 16; // metres past a ring before something is dropped from it (no flicker at the edge)
// shader warm-up: a model that just loaded (a Blender prop, a crowd person) gets its shaders compiled and its textures
// uploaded here, one at a time, a frame apart, BEFORE anything draws it. drawn cold, the Gut's set pieces compiled 3-9
// programs and uploaded dozens of textures on the one frame they appeared (150-250 ms hitches walking in)
const TEXK = ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap', 'aoMap', 'alphaMap', 'bumpMap', 'lightMap', 'specularMap'];

function geoOf(b) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(b.pos, 3));
  g.setAttribute('normal', new THREE.BufferAttribute(b.nrm, 3, true));
  if (b.uv) g.setAttribute('wuv', new THREE.BufferAttribute(b.uv, 2));
  if (b.col && b.uv) g.setAttribute('cpack', new THREE.BufferAttribute(b.col, 4, true));
  else if (b.col) g.setAttribute('color', new THREE.BufferAttribute(b.col, 3, true));
  g.setIndex(new THREE.BufferAttribute(b.idx, 1));
  const mn = new THREE.Vector3(...b.min || [0, 0, 0]), mx = new THREE.Vector3(...b.max || [0, 0, 0]);
  if (b.min) { g.boundingBox = new THREE.Box3(mn, mx); g.boundingSphere = g.boundingBox.getBoundingSphere(new THREE.Sphere()); } else g.computeBoundingSphere();
  return g;
}
const bytesOf = (b) => b.pos.byteLength + b.nrm.byteLength + (b.uv ? b.uv.byteLength : 0) + b.col.byteLength + b.idx.byteLength;

function groupOf(mesh, mats, lod) {
  const g = new THREE.Group(); let bytes = 0, tris = 0;
  for (const k of KINDS) {
    const b = mesh[k];
    if (!b) continue;
    const m = new THREE.Mesh(geoOf(b), mats[k]);
    m.matrixAutoUpdate = false; m.userData.kind = k;
    if (k === 'glass' || k === 'acid') m.renderOrder = 2;
    m.receiveShadow = lod === 0; m.castShadow = lod === 0 && k !== 'glass' && k !== 'glow';
    g.add(m); bytes += bytesOf(b); tris += b.tris;
  }
  g.matrixAutoUpdate = false;
  g.userData = { bytes, tris };
  return g;
}
function freeGroup(g) { if (!g) return; g.removeFromParent(); for (const m of g.children) m.geometry.dispose(); }

export class CityStream {
  constructor({ scene, city, preset = 1, boxes = [], workers = 2, workerUrl = '/js/city/chunkworker.js', renderer = null }) {
    if (!CITIES[city]) throw new Error('no city ' + city);
    this.scene = scene; this.city = city; this.def = CITIES[city];
    this.world = new ChunkWorld(boxes);
    this.root = new THREE.Group(); this.root.name = 'city'; scene.add(this.root);
    this.mats = cityMaterials();
    this.chunks = new Map(); // id -> record
    this.inbox = []; this.inflight = 0; this.maxInflight = workers * 2; this.colInflight = 0; // collision gets its own lane
    this.workers = Array.from({ length: workers }, () => { const w = new Worker(workerUrl, { type: 'module' }); w.onmessage = (e) => this.inbox.push(e.data); w.onerror = (e) => { this.errors.push(String(e.message || e)); }; return w; });
    this.rr = 0; this.errors = [];
    this.far = { mesh: null, key: '', wantKey: '', busy: false, t: 0, list: [] };
    this.props = { group: null, key: '', t: 0, n: 0 };
    this.st = { uploadMs: 0, maxUploadMs: 0, built: 0, buildMs: 0, maxBuildMs: 0, hitches: 0 };
    this.time = 0; this.cam = new THREE.Vector3(); this.first = true;
    this.setPreset(preset);
    this.renderer = renderer; this.warmQ = []; // (no renderer, no warm-up: things compile when first drawn, as before)
    onPropModel((id) => { // a Blender prop landed: warm it up, then rebuild the instances with it
      const m = propModel(id), objs = [];
      if (this.renderer && m && m.parts) for (const part of [...m.parts, ...(m.lod1 || [])]) { const im = new THREE.InstancedMesh(part.geo, part.mat, 1); if (part.paint) im.setColorAt(0, new THREE.Color()); objs.push(im); } // (as props.js draws it: instanced, paint parts coloured)
      this.warm(objs, () => { this.props.key = ''; for (const o of objs) o.dispose(); }, true);
    });
    this.crowd = new Crowd(scene); // the people standing about (crowd.js)
    this.crowd.warm = (objs, done) => this.warm(objs, done);
    this.weather = new Weather(scene); this.storm = 0; // 0-1: a paper storm round you (Late Fees can't see you in one)
    this.horizon = null;
    if (this.def.horizon) this.workers[1 % workers].postMessage({ op: 'horizon', city, gen: this.def.horizon });
  }
  setPreset(i) {
    this.preset = i; this.R = { ...(RINGS[i] || RINGS[1]) };
    const k = this.def.ringScale || {};
    for (const key of Object.keys(k)) this.R[key] = Math.round(this.R[key] * k[key]); this.props.key = ''; this.far.wantKey = ''; }
  get boxes() { return this.world.boxes; }

  rec(cx, cz) {
    const id = chunkId(this.city, cx, cz);
    let r = this.chunks.get(id);
    if (!r) { r = { id, cx, cz, packed: null, m0: null, m1: null, req: {}, d: 0, used: 0 }; this.chunks.set(id, r); }
    return r;
  }
  send(r, want) {
    const w = this.workers[this.rr++ % this.workers.length];
    for (const k in want) if (want[k]) r.req[k] = true;
    if (want.col) this.colInflight++; else this.inflight++;
    w.postMessage({ op: 'chunk', id: r.id, city: this.city, cx: r.cx, cz: r.cz, want });
  }

  // call once a frame with the camera (or the player's eye): plans rings, sends work, uploads results
  update(camera, dt = 1 / 60) {
    const t0 = performance.now();
    this.time += dt;
    cityUniforms.uTime.value = this.time;
    const beat = (this.time * 72 / 60) % 1; // lub-dub at 72 bpm
    cityUniforms.uBeat.value = Math.exp(-((beat - 0.05) ** 2) / 0.002) + 0.6 * Math.exp(-((beat - 0.25) ** 2) / 0.003);
    const p = camera.position; this.cam.copy(p);
    const R = this.R, pcx = Math.floor(p.x / CHUNK), pcz = Math.floor(p.z / CHUNK);
    const reach = Math.ceil(R.far / CHUNK) + 1;
    const want = [];
    // plan: every chunk in reach gets a wanted ring
    for (let dx = -reach; dx <= reach; dx++) for (let dz = -reach; dz <= reach; dz++) {
      const cx = pcx + dx, cz = pcz + dz;
      if (!inCity(this.city, cx, cz)) continue;
      const x0 = cx * CHUNK, z0 = cz * CHUNK;
      const d = Math.hypot(Math.max(x0 - p.x, 0, p.x - x0 - CHUNK), Math.max(z0 - p.z, 0, p.z - z0 - CHUNK));
      if (d > R.far + HYST) continue;
      const r = this.rec(cx, cz); r.d = d; r.used = this.time;
      r.col = Math.abs(dx) <= 2 && Math.abs(dz) <= 2;
      r.ring = d <= R.near ? 1 : d <= R.mid ? 2 : d <= R.far ? 3 : 4;
      want.push(r);
    }
    want.sort((a, b) => a.d - b.d);
    // send work, nearest first. collision (packed boxes, tiny + fast) has its own lane so meshes never hold it up;
    // then the near meshes, then mid
    for (const r of want) { if (this.colInflight >= 4) break; if (r.col && !r.packed && !r.req.packed) this.send(r, { packed: true, col: true }); }
    for (const pass of [1, 2]) for (const r of want) {
      if (this.inflight >= this.maxInflight) break;
      if (pass === 1 && r.ring === 1 && !r.m0 && !r.req.mesh0) this.send(r, { mesh0: true, packed: r.d <= this.R.props && !r.packed && !r.req.packed });
      else if (pass === 2 && r.ring === 2 && !r.m1 && !r.req.mesh1) this.send(r, { mesh1: true });
    }
    // take results, within a frame budget (the first frame takes everything: it's a loading screen)
    const budget = this.first ? 1e9 : 4;
    let up = 0;
    for (let i = 0; i < this.inbox.length; i++) if (this.inbox[i].col) { this.take(this.inbox[i]); this.inbox.splice(i--, 1); } // collision: always, now
    while (this.inbox.length && (performance.now() - t0 < budget || up === 0)) { this.take(this.inbox.shift()); up++; }
    if (this.first && this.inflight === 0 && this.colInflight === 0 && !this.inbox.length) this.first = false;
    // collision: the 5 x 5 round you
    for (const r of this.chunks.values()) {
      const col = r.col && r.used === this.time;
      if (col && r.packed && !this.world.has(r.id)) { r.boxes = r.boxes || chunkBoxes(r.packed); this.world.set(r.id, r.boxes); }
      else if (!col && this.world.has(r.id)) this.world.drop(r.id);
    }
    this.world.sync();
    // show / hide / drop meshes
    for (const r of this.chunks.values()) {
      const live = r.used === this.time, ring = live ? r.ring : 9;
      const showNear = ring === 1 && r.m0, showMid = (ring === 2 && r.m1) || (ring === 1 && !r.m0 && r.m1) || (ring === 2 && !r.m1 && r.m0);
      if (r.m0) {
        r.m0.visible = !!showNear || (ring === 2 && !r.m1);
        const cast = r.d < 64; // only the chunks round you cast sun shadows (the shadow pass was half the triangles)
        if (r.m0.userData.cast !== cast) { r.m0.userData.cast = cast; for (const m of r.m0.children) m.castShadow = cast && m.userData.kind !== 'glass' && m.userData.kind !== 'glow'; }
      }
      if (r.m1) r.m1.visible = !!showMid && !showNear;
      if (r.m0 && (!live || r.d > R.near + HYST + CHUNK)) { freeGroup(r.m0); r.m0 = null; r.req.mesh0 = false; }
      if (r.m1 && (!live || r.d > R.mid + HYST + CHUNK || ring === 1 && r.m0 && r.d < R.near - CHUNK)) { freeGroup(r.m1); r.m1 = null; r.req.mesh1 = false; }
      if (!live && !r.m0 && !r.m1 && this.time - r.used > 20 && !this.world.has(r.id) && !r.req.packed) this.chunks.delete(r.id); // LRU: forgotten 20 s after it left every ring
    }
    this.warmStep(camera);
    this.updateFar(want);
    this.updateProps(want);
    this.applyEnv(p);
    const commute = (districtWeights(this.city, p.x, p.z, 40).find(([d]) => d.id === 'commute') || [0, 0])[1];
    this.storm = this.weather.update(camera, dt, commute, this.clock ? this.clock() : Date.now() / 1000);
    this.weather.fog(this.env);
    this.pickLights(camera);
    this.crowd.update(this.marks(), this.cam, dt);
    const ms = performance.now() - t0;
    this.st.frameMs = ms; if (ms > 50 && !this.first) this.st.hitches++;
  }

  take(m) {
    if (m.op === 'error') { this.errors.push(m.err); if (m.col) this.colInflight--; else this.inflight = Math.max(0, this.inflight - 1); return; }
    if (m.op === 'far') { this.far.busy = false; this.takeFar(m); return; }
    if (m.op === 'horizon') { this.horizon = groupOf(m.mesh, this.mats.horizon, 1); this.horizon.traverse((o) => { o.castShadow = o.receiveShadow = false; o.frustumCulled = false; }); this.root.add(this.horizon); return; }
    if (m.col) this.colInflight = Math.max(0, this.colInflight - 1); else this.inflight = Math.max(0, this.inflight - 1);
    const r = this.chunks.get(m.id);
    if (!r) return;
    const t = performance.now();
    if (m.packed) { r.packed = m.packed; r.req.packed = false; r.boxes = null; }
    if (m.mesh0) { freeGroup(r.m0); r.m0 = groupOf(m.mesh0, this.mats, 0); r.m0.visible = false; this.root.add(r.m0); }
    if (m.mesh1) { freeGroup(r.m1); r.m1 = groupOf(m.mesh1, this.mats, 1); r.m1.visible = false; this.root.add(r.m1); }
    if (m.mesh0) r.req.mesh0 = false; if (m.mesh1) r.req.mesh1 = false;
    const up = performance.now() - t;
    this.st.uploadMs = up; this.st.maxUploadMs = Math.max(this.st.maxUploadMs, up);
    this.st.built++; this.st.buildMs += m.ms; this.st.maxBuildMs = Math.max(this.st.maxBuildMs, m.buildMs || 0);
  }

  // queue meshes to warm up; done() once their shaders are compiled + checked and their textures are on the GPU
  warm(objs, done, prop = false) {
    if (!this.renderer || !objs.length) { if (done) done(); return; }
    this.warmQ.push({ objs, i: 0, progs: [], tex: [], seen: new Set(), done, prop });
  }
  // once a frame: at most one new shader compile, or one compiled shader's first-use check (the blocking part: by
  // now the GPU process has had a frame to finish it), or one texture upload
  warmStep(camera) {
    const w = this.warmQ[0], R = this.renderer;
    if (!w) return;
    if (w.progs.length) { const pr = w.progs.shift(); try { pr.getUniforms(); } catch { /* reported when drawn */ } return; }
    while (w.i < w.objs.length) {
      const o = w.objs[w.i++], n = R.info.programs.length;
      R.compile(o, camera, this.scene); // (with the real scene: its lights, fog and shadows, so the same programs as when drawn)
      o.traverse((q) => { for (const mt of [].concat(q.material || [])) { const pr = R.properties.get(mt).currentProgram; if (R.info.programs.length > n && pr && !w.seen.has(pr)) { w.seen.add(pr); w.progs.push(pr); }
        for (const k of TEXK) { const tx = mt[k]; if (tx && tx.isTexture && !w.seen.has(tx)) { w.seen.add(tx); w.tex.push(tx); } } } });
      if (R.info.programs.length > n) return; // a real compile: that's this frame's share (cached programs cost next to nothing, keep going)
    }
    if (w.tex.length) { R.initTexture(w.tex.shift()); return; }
    this.warmQ.shift();
    if (w.done) w.done();
  }

  // the far ring: one impostor mesh for every chunk that's in it (rebuilt in the worker when the set changes)
  updateFar(want) {
    const list = want.filter((r) => r.ring === 3 || (r.ring === 2 && !r.m1 && !r.m0));
    const key = list.map((r) => r.cx + ',' + r.cz).sort().join(';');
    if (key === this.far.key || key === this.far.wantKey && this.far.busy) return;
    if (this.far.busy || this.time - this.far.t < 0.4) return;
    this.far.busy = true; this.far.t = this.time; this.far.wantKey = key;
    this.workers[0].postMessage({ op: 'far', key, city: this.city, ids: list.map((r) => [r.cx, r.cz]) });
  }
  takeFar(m) {
    if (this.far.mesh) { this.far.mesh.removeFromParent(); this.far.mesh.geometry.dispose(); this.far.mesh = null; }
    this.far.key = m.key;
    if (!m.mesh.verts) return;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(m.mesh.pos.subarray(0, m.mesh.verts * 3), 3));
    g.setAttribute('normal', new THREE.BufferAttribute(m.mesh.nrm.subarray(0, m.mesh.verts * 3), 3, true));
    g.setAttribute('color', new THREE.BufferAttribute(m.mesh.col.subarray(0, m.mesh.verts * 3), 3, true));
    g.setIndex(new THREE.BufferAttribute(m.mesh.idx.subarray(0, m.mesh.tris * 3), 1));
    if (m.mesh.min) { g.boundingBox = new THREE.Box3(new THREE.Vector3(...m.mesh.min), new THREE.Vector3(...m.mesh.max)); g.boundingSphere = g.boundingBox.getBoundingSphere(new THREE.Sphere()); } else g.computeBoundingSphere(); // (the worker's bounds: no 25 ms pass over every vertex here)
    this.far.mesh = new THREE.Mesh(g, this.mats.far); this.far.mesh.matrixAutoUpdate = false; this.far.mesh.userData = { tris: m.mesh.tris, bytes: m.mesh.pos.byteLength * 2 + m.mesh.idx.byteLength };
    this.root.add(this.far.mesh);
  }

  updateProps(want) {
    const list = want.filter((r) => r.d <= this.R.props && r.packed);
    const hiCell = Math.floor(this.cam.x / 16) + ',' + Math.floor(this.cam.z / 16); // the detail bubbles move with you
    const key = list.map((r) => r.id).sort().join(';') + '|' + hiCell;
    if (key === this.props.key || this.time - this.props.t < 0.3) return;
    if (this.warmQ.some((w) => w.prop) && this.time - this.props.t < 1) return; // (a prop model is still warming up: a rebuild now would draw it cold. wait a few frames, never more than a second)
    this.props.key = key; this.props.t = this.time;
    const inst = [];
    for (const r of list) {
      const P = r.packed.prop, ids = r.packed.ids;
      const TL = r.packed.ptilt; // (some lean with the ground: chunk.js ptilt)
      for (let i = 0; i < P.length; i += 7) inst.push({ id: ids[P[i]], x: P[i + 1], y: P[i + 2], z: P[i + 3], yaw: P[i + 4], s: P[i + 5], v: P[i + 6], tx: TL ? TL[i / 7 * 2] : 0, tz: TL ? TL[i / 7 * 2 + 1] : 0 });
    }
    freeProps(this.props.group);
    this.props.group = buildPropGroup(inst, this.R.propsHi, this.cam, this.R.props / 224); this.props.n = inst.length;
    this.root.add(this.props.group);
  }

  // the NL nearest lights in the chunks round the camera -> the shader's arrays (view space, so no per-pixel matrix)
  pickLights(camera) {
    const p = camera.position, seen = new Set(), list = [];
    for (const r of this.chunks.values()) {
      if (!r.packed || !r.packed.lights || r.d > 70) continue;
      for (const L of r.packed.lights) {
        const key = L[0] * 7 + L[1] * 13 + L[2] * 17;
        if (seen.has(key)) continue; seen.add(key);
        const d = Math.hypot(L[0] - p.x, L[1] - p.y, L[2] - p.z) - L[4];
        if (d < 50) list.push([d, L]);
      }
    }
    list.sort((a, b) => a[0] - b[0]);
    const v = new THREE.Vector3(), LP = cityUniforms.uLP.value, LC = cityUniforms.uLC.value, M = camera.matrixWorldInverse;
    camera.updateMatrixWorld();
    for (let i = 0; i < NL; i++) {
      const L = list[i] && list[i][1];
      if (!L) { LP[i].set(0, -1e4, 0, 1); LC[i].set(0, 0, 0, 0); continue; }
      v.set(L[0], L[1], L[2]).applyMatrix4(M);
      // fade the last few in/out so a light popping into the list doesn't snap
      const fade = Math.min(1, Math.max(0, (50 - list[i][0]) / 12)) * (i > NL - 4 ? (NL - i) / 4 : 1);
      LP[i].set(v.x, v.y, v.z, L[4]);
      const k = L[5] * fade * 2.2;
      LC[i].set(((L[3] >> 16) & 255) / 255 * k, ((L[3] >> 8) & 255) / 255 * k, (L[3] & 255) / 255 * k, 0);
    }
    this.nLights = Math.min(NL, list.length);
  }

  // sky + fog blended between districts round the camera (40 m across a border)
  applyEnv(p) {
    const ws = districtWeights(this.city, p.x, p.z, 40);
    const fog = new THREE.Color(0, 0, 0), top = new THREE.Color(0, 0, 0), mid = new THREE.Color(0, 0, 0), bot = new THREE.Color(0, 0, 0), c = new THREE.Color();
    let near = 0, far = 0, night = 0, pulse = 0;
    const hemi = [new THREE.Color(0, 0, 0), new THREE.Color(0, 0, 0), 0], sun = [new THREE.Color(0, 0, 0), 0];
    for (const [d, w] of ws) {
      fog.add(c.setHex(d.sky.fog).multiplyScalar(w)); top.add(c.setHex(d.sky.top).multiplyScalar(w)); mid.add(c.setHex(d.sky.mid).multiplyScalar(w)); bot.add(c.setHex(d.sky.bot).multiplyScalar(w));
      near += d.fogNear * w; far += d.fogFar * w; night += (+d.night || 0) * w; pulse += (+d.pulse || 0) * w;
      const L = d.light || { hemi: [0xcfe8ff, 0x7a4a6a, 1.5], sun: [0xfff0dd, 1.8] };
      hemi[0].add(c.setHex(L.hemi[0]).multiplyScalar(w)); hemi[1].add(c.setHex(L.hemi[1]).multiplyScalar(w)); hemi[2] += L.hemi[2] * w;
      sun[0].add(c.setHex(L.sun[0]).multiplyScalar(w)); sun[1] += L.sun[1] * w;
    }
    cityUniforms.uNight.value = night; cityUniforms.uHaze.value.copy(fog).lerp(mid, 0.35);
    this.env = { fog, top, mid, bot, near, far: Math.min(far, this.R.far + 60), night, pulse, hemi, sun, district: ws.length ? ws.reduce((a, b) => (b[1] > a[1] ? b : a))[0] : null };
  }

  stats() {
    let near = 0, mid = 0, packed = 0, bytes = 0, tris = 0;
    for (const r of this.chunks.values()) {
      if (r.packed) packed++;
      if (r.m0) { bytes += r.m0.userData.bytes; if (r.m0.visible) { near++; tris += r.m0.userData.tris; } }
      if (r.m1) { bytes += r.m1.userData.bytes; if (r.m1.visible) { mid++; tris += r.m1.userData.tris; } }
    }
    const fm = this.far.mesh;
    return {
      chunks: this.chunks.size, packed, near, mid, far: this.far.key ? this.far.key.split(';').length : 0, collision: this.world.chunks.size,
      boxes: this.world.boxes.length, props: this.props.n, inflight: this.inflight + this.colInflight, inbox: this.inbox.length,
      geoMB: +((bytes + (fm ? fm.userData.bytes : 0) + (this.horizon ? this.horizon.userData.bytes : 0)) / 1048576).toFixed(1), cityTris: tris + (fm ? fm.userData.tris : 0) + (this.horizon ? this.horizon.userData.tris : 0),
      built: this.st.built, avgBuildMs: this.st.built ? +(this.st.buildMs / this.st.built).toFixed(1) : 0, maxBuildMs: +this.st.maxBuildMs.toFixed(1),
      maxUploadMs: +this.st.maxUploadMs.toFixed(1), hitches: this.st.hitches, errors: this.errors.length,
    };
  }
  // the gimmick triggers (shared/city/gimmicks.js) of the collision chunks: rebuilt when that set changes
  triggers() {
    if (this._trigV === this.world.version) return this._trig;
    const out = [];
    for (const id of this.world.chunks.keys()) { const r = this.chunks.get(id); if (r && r.packed) for (const t of r.packed.triggers) out.push(t); }
    this._trig = out; this._trigV = this.world.version;
    return out;
  }
  marks() {
    if (this._markV === this.world.version) return this._marks;
    const out = []; for (const id of this.world.chunks.keys()) { const r = this.chunks.get(id); if (r && r.packed) out.push(...r.packed.marks); }
    this._marks = out; this._markV = this.world.version;
    return out;
  }
  // is everything round (x, z) that you could stand on loaded? (hold the player until it is)
  ready(x, z) { return this.world.readyAt(this.city, x, z); }
  progress() { let n = 0, k = 0; for (const r of this.chunks.values()) if (r.used === this.time && r.ring === 1) { n++; if (r.m0) k++; } return n ? k / n : 0; } // the near ring's share that's built (the loading card)
  dispose() {
    for (const w of this.workers) w.terminate();
    for (const r of this.chunks.values()) { freeGroup(r.m0); freeGroup(r.m1); }
    if (this.far.mesh) { this.far.mesh.geometry.dispose(); }
    freeProps(this.props.group); this.crowd.dispose(); this.weather.dispose();
    this.root.removeFromParent(); this.chunks.clear(); this.world.boxes.length = 0; this.world.boxes.terrain = null; // (the city's hills go with it)
  }
}
