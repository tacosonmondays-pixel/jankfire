// Reflections (the RAY-TRACED LOOK, part 3; the owner: "anything that would come from ray tracing"). Glass towers and
// wet streets show the sky and the buildings round them. Real ray-traced reflections trace every pixel every frame; this
// is the game-engine trick instead, a reflection probe:
//  - a little 360 snapshot of the world (a cube map, 128 px a side) taken where you are. Walk 30 m and a fresh one is
//    taken, one side per frame into a spare, then swapped in, so it never hitches and never shows half a picture.
//  - shiny map materials (REFL.mats) look up what's mirrored in their direction. "box projected": the snapshot is
//    treated as a room round the probe, so a reflection slides across the glass as you walk instead of sticking to you.
//  - fresnel: everything mirrors more at a glancing look (a road far ahead shines, the road at your feet barely).
//  - windows mirror on their dark panes only: lit windows and the concrete frames stay as they are.
// Turned on by the RAY-TRACED LOOK (fxsettings.js), Mid and Too HD only; off, the materials cost one uniform check.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { studioEnv } from './glbkit.js';
import { sunDir } from './lighting.js';
import { G } from './ctx.js';

// mats: key -> [strength, base mirror (straight on), dark panes only]
export const REFL = { res: 128, move: 30, box: [40, 30, 40], near: 0.5, far: 1500,
  mats: { glass: [0.9, 0.3, 0], greenglass: [0.6, 0.2, 0], office: [0.8, 0.22, 1], window: [0.7, 0.2, 1], glassblock: [0.55, 0.15, 1],
    wetroad: [0.6, 0.1, 0], wetroadz: [0.6, 0.1, 0], asphaltn: [0.5, 0.08, 0], asphalt: [0.3, 0.04, 0], asphalt2: [0.25, 0.03, 0],
    chrome: [0.7, 0.45, 0], metal: [0.3, 0.06, 0], floorcyan: [0.35, 0.05, 0], tile: [0.3, 0.05, 0], marble: [0.25, 0.04, 0] } };
const U = { uRK: { value: 0 }, uRC: { value: null }, uRP: { value: new THREE.Vector3() }, uRB: { value: new THREE.Vector3(...REFL.box) } };
let tick = 0, envDue = false, envWorld = false, night = false; const G0 = { r: null };
let on = false, scene = null, cams = null, rts = null, front = 0, face = -1, probe = new THREE.Vector3(1e9, 0, 0), want = new THREE.Vector3(), patched = new WeakSet(), alive = true;

const FRAG = `
if ( uRK > 0.0 ) { // the world mirrored in this surface (reflect.js)
  vec3 rN = normalize( vRN ), rV = normalize( vRW - cameraPosition ), rR = reflect( rV, rN );
  // box projection: where the mirrored ray leaves the room round the probe, seen from the probe
  vec3 bmax = uRP + uRB, bmin = uRP - uRB;
  vec3 f1 = ( bmax - vRW ) / rR, f2 = ( bmin - vRW ) / rR, ff = max( f1, f2 );
  float d = min( min( ff.x, ff.y ), ff.z );
  // (a surface outside the room, like a tower's upper floors, fades to the plain direction instead)
  vec3 rq = abs( vRW - uRP ) / uRB; float rin = 1.0 - smoothstep( 0.75, 1.0, max( max( rq.x, rq.y ), rq.z ) );
  vec3 rD = mix( rR, normalize( vRW + rR * max( d, 0.0 ) - uRP ), rin );
  vec3 rc = textureCube( uRC, rD ).rgb; // (a rendered cube isn't mirrored the way an image one is)
  float ndv = clamp( dot( -rV, rN ), 0.0, 1.0 ), fr = rS.y + ( 1.0 - rS.y ) * pow( 1.0 - ndv, 5.0 );
  float msk = rS.z > 0.5 ? smoothstep( 0.5, 0.18, dot( diffuseColor.rgb, vec3( 0.3, 0.5, 0.2 ) ) ) : 1.0;
  outgoingLight = mix( outgoingLight, rc, clamp( fr * rS.x * msk * uRK, 0.0, 1.0 ) );
}
`;
// one shiny material: its own strength, the shared snapshot
function reflMaterial(m, s) {
  if (!m || patched.has(m) || m.isShaderMaterial) return;
  patched.add(m);
  const prev = m.onBeforeCompile, prevKey = m.customProgramCacheKey ? m.customProgramCacheKey.bind(m) : null, rS = { value: new THREE.Vector3(...s) };
  m.onBeforeCompile = function (sh, r) {
    if (prev && prev !== THREE.Material.prototype.onBeforeCompile) prev.call(this, sh, r);
    if (!sh.fragmentShader.includes('#include <opaque_fragment>') || !sh.vertexShader.includes('#include <worldpos_vertex>')) return;
    Object.assign(sh.uniforms, U, { rS });
    sh.vertexShader = 'varying vec3 vRW; varying vec3 vRN;\n' + sh.vertexShader.replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
	{ vec4 rw = vec4( transformed, 1.0 ); vec3 rn = normal;
	#ifdef USE_INSTANCING
	rw = instanceMatrix * rw; rn = mat3( instanceMatrix ) * rn;
	#endif
	vRW = ( modelMatrix * rw ).xyz; vRN = normalize( mat3( modelMatrix ) * rn ); }`);
    sh.fragmentShader = 'uniform float uRK; uniform samplerCube uRC; uniform vec3 uRP; uniform vec3 uRB; uniform vec3 rS; varying vec3 vRW; varying vec3 vRN;\n'
      + sh.fragmentShader.replace('#include <opaque_fragment>', FRAG + '#include <opaque_fragment>');
  };
  m.customProgramCacheKey = () => (prevKey ? prevKey() : '') + '|refl';
  m.needsUpdate = true;
}

// world.js, once the map is built: patch its shiny materials, take a fresh snapshot
export function reflectMap(sc, def, MAT) {
  scene = sc; night = !!(def && def.night); probe.set(1e9, 0, 0); face = -1; U.uRK.value = 0;
  if (!def) return;
  for (const [k, s] of Object.entries(REFL.mats)) if (MAT[k] && MAT[k].mat) reflMaterial(MAT[k].mat, s);
}
export function setReflect(v) { on = !!v && alive; if (!on) { U.uRK.value = 0; if (envWorld && G0.r) propEnv(G0.r, false); } else probe.set(1e9, 0, 0); }

function setup() {
  rts = [0, 1].map(() => new THREE.WebGLCubeRenderTarget(REFL.res, { generateMipmaps: false, minFilter: THREE.LinearFilter }));
  const dirs = [[1, 0, 0, 0, -1, 0], [-1, 0, 0, 0, -1, 0], [0, 1, 0, 0, 0, 1], [0, -1, 0, 0, 0, -1], [0, 0, 1, 0, -1, 0], [0, 0, -1, 0, -1, 0]]; // three's cube faces
  cams = dirs.map(([x, y, z, ux, uy, uz]) => { const c = new THREE.PerspectiveCamera(90, 1, REFL.near, REFL.far); c.up.set(ux, uy, uz); c.userData.look = new THREE.Vector3(x, y, z); return c; });
}
// every frame (world.js renderFrame, before the main render): one side of a snapshot when one is due
export function updateReflect(r, cam) {
  if (!on || !scene || !cam) return;
  G0.r = r;
  if (envWorld && ++tick % 120 === 0) boostEnv(); // (models that landed since)
  try {
    if (!rts) setup();
    if (envDue && face < 0) { envDue = false; propEnv(r, true); return; } // (the frame after a snapshot: the models' reflection)
    if (face < 0) { if (cam.position.distanceTo(probe) < REFL.move) return; want.copy(cam.position); face = 0; }
    const c = cams[face], back = rts[1 - front], prevRT = r.getRenderTarget(), prevAuto = r.autoClear, prevSh = r.shadowMap.autoUpdate;
    c.position.copy(want); c.lookAt(want.x + c.userData.look.x, want.y + c.userData.look.y, want.z + c.userData.look.z);
    r.shadowMap.autoUpdate = false; // (the shadows from this frame's main render do: not six more shadow passes)
    r.setRenderTarget(back, face); r.autoClear = true; r.render(scene, c);
    r.setRenderTarget(prevRT); r.autoClear = prevAuto; r.shadowMap.autoUpdate = prevSh;
    if (++face === 6) { front = 1 - front; face = -1; probe.copy(want); U.uRC.value = rts[front].texture; U.uRP.value.copy(probe); U.uRK.value = 1; envDue = true; }
  } catch (e) { alive = false; on = false; U.uRK.value = 0; console.warn('reflections off:', e); } // (a card that can't: the look without them)
}
export const reflectInfo = () => ({ on, alive, k: U.uRK.value, probe: probe.toArray().map(Math.round), face });

// ---- the models (Blender props, buildings, mechs, your gun) reflect the real world too, not a photo studio
// (the owner: "can you give props reflections for shiny and light? ... missing highlights and midtones"). Every glossy
// model already reads one shared reflection (glbkit.js, a studio room). After each snapshot that target is repainted
// from it: the world a little brighter (PROPENV.gain, so matte paint still gets a fill and the mids lift), plus the sun
// as a small hot spot, so chrome, brass and clear-coat get a real sun glint. Turn reflections off: the studio comes back.
export const PROPENV = { size: 256, gain: 1.5, lift: 0.05, sunK: 70, sunPow: 350, sunC: [1, 0.93, 0.8], k: 2.4, metalK: 1.4 }; // k: how much more the glossy models take of it (metal already takes plenty)
let pm = null, envCube = null, envCam = null, envScene = null, studioCube = null, envMat = null;
function propEnv(r, world) {
  try {
    const rt = studioEnv(); if (!rt) return;
    if (!pm) {
      pm = new THREE.PMREMGenerator(r);
      const o = { type: THREE.HalfFloatType, generateMipmaps: false, minFilter: THREE.LinearFilter };
      envCube = new THREE.WebGLCubeRenderTarget(PROPENV.size, o); envCam = new THREE.CubeCamera(0.1, 20, envCube);
      envMat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, depthTest: false,
        uniforms: { uC: { value: null }, uG: { value: PROPENV.gain }, uL: { value: PROPENV.lift }, uS: { value: new THREE.Vector3(0, 1, 0) }, uSC: { value: new THREE.Vector3() }, uSP: { value: PROPENV.sunPow } },
        vertexShader: 'varying vec3 vD; void main() { vD = position; gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 ); }',
        fragmentShader: `uniform samplerCube uC; uniform float uG; uniform float uL; uniform vec3 uS; uniform vec3 uSC; uniform float uSP; varying vec3 vD;
void main() { vec3 d = normalize( vD ); vec3 c = textureCube( uC, d ).rgb * uG + uL; c += uSC * pow( max( dot( d, uS ), 0.0 ), uSP ); gl_FragColor = vec4( c, 1.0 ); }` });
      envScene = new THREE.Scene(); envScene.add(new THREE.Mesh(new THREE.SphereGeometry(5, 48, 24), envMat));
      studioCube = new THREE.WebGLCubeRenderTarget(PROPENV.size, o); new THREE.CubeCamera(0.1, 100, studioCube).update(r, new RoomEnvironment());
      pm.fromCubemap(studioCube.texture).dispose(); // (once: makes the generator's own work targets at this size)
    }
    let src = studioCube.texture;
    if (world && rts) {
      const d = sunDir(), k = night ? PROPENV.sunK * 0.15 : PROPENV.sunK;
      envMat.uniforms.uC.value = rts[front].texture; if (d) envMat.uniforms.uS.value.copy(d).normalize();
      envMat.uniforms.uSC.value.set(...PROPENV.sunC).multiplyScalar(k);
      envCam.update(r, envScene); src = envCube.texture;
    }
    pm.fromCubemap(src, rt); envWorld = !!world; boostEnv(r);
  } catch (e) { console.warn('model reflections off:', e); }
}
// the models' reflection strength: stronger with the real world in it (a glint and a fill you can see), as it was without
let nBoost = 0;
function boostEnv() {
  const env = studioEnv(), t = env && env.texture; if (!t) return;
  const each = (root) => root && root.traverse((o) => { if (!o.isMesh || !o.material) return; for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
    if (!m || m.envMap !== t) continue;
    if (m.userData.envI0 == null) m.userData.envI0 = m.envMapIntensity;
    m.envMapIntensity = m.userData.envI0 * (envWorld ? (m.metalness > 0.5 ? PROPENV.metalK : PROPENV.k) : 1); nBoost++;
  } });
  nBoost = 0; each(scene); each(G.vmScene);
}
export const propEnvInfo = () => ({ world: envWorld, boosted: nBoost });
