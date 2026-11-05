// Big Laser Pointer: the beams (yours, everyone else's, and the ones in replays) and the charge glow on other people's
// pointers. The server does the hits; this is just what it looks like: a fat green beam out of the lens that follows
// where they look for as long as it lasts, a white-hot core, rings running down it, a splash where it hits a wall.
import * as THREE from 'three';
import { WEAPONS, FLAGS } from '/shared/weapons.js';
import { raycast } from '/shared/physics.js';
import { BOXES } from '/shared/map.js';
import { G } from './ctx.js';
import { fx } from './fx.js';
import { sfx, laserWhine } from './audio.js';

const L = WEAPONS.laser;
const beams = new Map(); // owner id -> { k, t0, until, meshes, src(): { o, d } }
const lerp = (ab, k) => ab[0] + (ab[1] - ab[0]) * k;
const BEAM_VS = `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
// u runs round the tube, v along it (0 at the lens). bright rings race down it, the edge fizzes
const BEAM_FS = `
uniform float uT, uLen, uA, uCore; uniform vec3 uCol;
varying vec2 vUv;
void main() {
  float along = vUv.y * uLen;
  float ring = pow(0.5 + 0.5 * sin(along * 1.6 - uT * 38.0), 6.0);
  float fizz = 0.75 + 0.25 * sin(vUv.x * 40.0 + uT * 50.0 + along * 3.0);
  vec3 c = mix(uCol, vec3(1.0), uCore) * (0.75 + ring * 0.9) * fizz;
  float fade = smoothstep(0.0, 0.02, vUv.y) * (1.0 - smoothstep(0.96, 1.0, vUv.y));
  gl_FragColor = vec4(c, uA * fade * (0.45 + 0.4 * ring));
}`;
let geo = null;
function tubeGeo() { // radius 1, length 1 along -z from the origin (scaled per frame)
  if (geo) return geo;
  geo = new THREE.CylinderGeometry(1, 1, 1, 14, 1, true);
  geo.rotateX(-Math.PI / 2); geo.translate(0, 0, -0.5);
  return geo;
}
function beamMat(core) {
  return new THREE.ShaderMaterial({
    uniforms: { uT: { value: 0 }, uLen: { value: 10 }, uA: { value: 1 }, uCore: { value: core }, uCol: { value: new THREE.Color(L.tracer) } },
    vertexShader: BEAM_VS, fragmentShader: BEAM_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
  });
}
let flareTex = null;
function flare() {
  if (!flareTex) {
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const x = c.getContext('2d'), gr = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(160,255,140,0.9)'); gr.addColorStop(1, 'rgba(57,255,20,0)');
    x.fillStyle = gr; x.fillRect(0, 0, 64, 64);
    flareTex = new THREE.CanvasTexture(c);
  }
  return new THREE.Sprite(new THREE.SpriteMaterial({ map: flareTex, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
}
function makeMeshes(scene) {
  const outer = new THREE.Mesh(tubeGeo(), beamMat(0.1)), core = new THREE.Mesh(tubeGeo(), beamMat(0.7));
  const mz = flare(), hit = flare();
  for (const m of [outer, core, mz, hit]) { m.frustumCulled = false; m.renderOrder = 5; scene.add(m); }
  return { outer, core, mz, hit, scene };
}
function dropMeshes(M) {
  for (const k of ['outer', 'core']) { M.scene.remove(M[k]); M[k].material.dispose(); }
  for (const k of ['mz', 'hit']) { M.scene.remove(M[k]); M[k].material.dispose(); }
}

// a beam from `id` at charge k for dur s. src() gives where it comes out and which way, every frame (their aim moves it)
export function beamStart(id, k, dur, src, scene = G.scene) {
  beamStop(id);
  const now = performance.now();
  const B = { k, t0: now, until: now + dur * 1000, src, M: makeMeshes(scene), spark: 0 };
  beams.set(id, B);
  const s = src();
  if (s) sfx.laserFire(k, id === G.myId ? null : s.o);
  return B;
}
export function beamStop(id) { const B = beams.get(id); if (B) { dropMeshes(B.M); beams.delete(id); } }
export function beamsClear() { for (const id of [...beams.keys()]) beamStop(id); }
export function beamOn(id) { return beams.has(id); }

const tmp = new THREE.Vector3(), q = new THREE.Quaternion(), fwd = new THREE.Vector3(0, 0, -1);
export function updateBeams(dt, now) {
  for (const [id, B] of beams) {
    const s = B.src();
    if (!s || now > B.until) { beamStop(id); continue; }
    const k = B.k, t = (now - B.t0) / 1000, life = (B.until - B.t0) / 1000;
    const wall = raycast(s.o, s.d, L.range, BOXES), len = wall ? wall.t : L.range;
    // thick at the start, a quick swell, then it thins out to nothing at the end
    const env = Math.min(1, t / 0.05) * (1 - Math.max(0, (t - life * 0.7) / (life * 0.3))) * (1 + 0.25 * Math.exp(-t * 18));
    const r = lerp(L.r, k) * Math.max(0.05, env) * (0.92 + Math.random() * 0.16);
    const { outer, core, mz, hit } = B.M;
    q.setFromUnitVectors(fwd, tmp.set(s.d[0], s.d[1], s.d[2]));
    for (const [m, rr] of [[outer, r], [core, r * 0.38]]) {
      m.position.set(s.o[0], s.o[1], s.o[2]); m.quaternion.copy(q); m.scale.set(rr, rr, len);
      m.material.uniforms.uT.value = now / 1000; m.material.uniforms.uLen.value = len; m.material.uniforms.uA.value = Math.min(1, env * 1.2);
    }
    mz.position.set(s.o[0], s.o[1], s.o[2]); mz.scale.setScalar(id === G.myId ? 0.12 + r * 0.5 : r * 4 + 0.2); // (yours is right in front of your face)
    hit.visible = !!wall;
    if (wall) {
      hit.position.set(wall.point[0] + wall.normal[0] * 0.05, wall.point[1] + wall.normal[1] * 0.05, wall.point[2] + wall.normal[2] * 0.05);
      hit.scale.setScalar(r * 4.5 * (0.8 + Math.random() * 0.4));
      B.spark -= dt;
      if (B.spark <= 0) { B.spark = 0.05; fx.sparks(wall.point, wall.normal, 3 + Math.round(k * 5), false); }
    }
    if (id === G.myId) G.shake = Math.max(G.shake, 0.12 + k * 0.25);
  }
}

// other people charging: the orb on their pointer's lens swells and the lens glows (FLAGS.CHARGE in their snapshots)
export function remoteCharge(r, dt) {
  const m = r.weaponMesh, ud = m && m.userData;
  if (!ud || !ud.orb) return;
  const on = r.alive && !!(r.f & FLAGS.CHARGE) && r.w === 'laser';
  r.lzK = on ? Math.min(1, (r.lzK || 0) + dt / L.charge) : 0;
  chargeLook(ud, r.lzK, on, performance.now());
  if (on && Math.random() < dt * (4 + r.lzK * 12)) { const mz = r.muzzle(); fx.sparks(mz, null, 1, false); }
}
// shared by the viewmodel and everyone else's: the orb, the lens, the meter LEDs, the button
export function chargeLook(ud, k, on, now) {
  ud.orb.visible = on && k > 0.02;
  if (ud.orb.visible) { ud.orb.scale.setScalar((0.012 + k * 0.05) * (1 + Math.sin(now * 0.05) * 0.12 * k)); ud.orb.material.opacity = 0.5 + k * 0.4; }
  const lit = on ? Math.min(5, Math.floor(k * 5 + 0.001)) : 0;
  if (ud.leds) ud.leds.forEach((l, i) => l.material.color.setHex(i < lit ? (lit === 5 && (now % 200) < 100 ? 0xffffff : 0x39ff14) : 0x0b2a08));
  if (ud.emit) ud.emit.material.color.setHex(on ? (k >= 1 ? 0xeaffea : 0x39ff14) : 0x1d7a10);
  if (ud.button) ud.button.position.y = 0.047 - (on ? 0.005 : 0);
}
export function chargeWhine(k) { laserWhine(k); }
