// the cast in the city's own light (OVERDUE): the streamed city lights itself with its own point lights (the NL nearest
// lamps, heart lamps, fire barrels and goo glows: city/mats.js LIGHTS_GLSL, picked round the camera by city/stream.js)
// and the cast's materials never had them, so in the Gut or under a lamp people were dark cut-outs lit only by the
// district's dim sky. Here every cast mesh gets the same city lights, plus a soft fill and rim in the colour of the
// place (the nearby lamps over the grade's haze): lit like the world round them, still moody, never a silhouette.
// Only while you're in a streamed story map; elsewhere (the train, the test lot) the terms are zero and nothing changes.
import * as THREE from 'three';
import { G } from '../ctx.js';
import { MAPS } from '/shared/map.js';
import { cityUniforms, LIGHTS_GLSL, LIGHTS_HEAD, NL } from '../city/mats.js';
import { actors } from './actors.js';

// fill: an ambient term, rim: light from behind on the silhouette's edge. both scale the place's colour (below)
export const CAST_LIGHT = { fill: 0.25, rim: 0.45, rimPow: 2.4, lamps: 6, ease: 3 };
const uFill = { value: new THREE.Color(0, 0, 0) }, uRim = { value: new THREE.Color(0, 0, 0) };
const CAST_GLSL = `
#ifdef CAST_LIGHT
{ vec3 vd = normalize(vViewPosition); float rim = pow(1.0 - clamp(dot(normal, vd), 0.0, 1.0), ${CAST_LIGHT.rimPow.toFixed(2)});
  reflectedLight.indirectDiffuse += uCastFill * diffuseColor.rgb;
  reflectedLight.directDiffuse += uCastRim * rim * mix(vec3(1.0), diffuseColor.rgb, 0.5); }
#endif`;
const done = new WeakSet();

function patch(m) {
  if (!m || done.has(m)) return;
  done.add(m);
  if (m.isMeshBasicMaterial || m.isShaderMaterial || m.isRawShaderMaterial || m.isMeshDepthMaterial || m.isLineBasicMaterial || m.isSpriteMaterial || m.isPointsMaterial) return; // (unlit: eyes' glints, glows)
  const prev = m.onBeforeCompile, prevKey = m.customProgramCacheKey ? m.customProgramCacheKey.bind(m) : null;
  m.onBeforeCompile = function (sh, r) {
    if (prev) prev.call(this, sh, r);
    if (!sh.fragmentShader.includes('#include <lights_fragment_end>')) return;
    Object.assign(sh.uniforms, { uLP: cityUniforms.uLP, uLC: cityUniforms.uLC, uCastFill: uFill, uCastRim: uRim });
    sh.fragmentShader = '#define CITY_LIGHTS\n#define CAST_LIGHT\n' + LIGHTS_HEAD + 'uniform vec3 uCastFill; uniform vec3 uCastRim;\n'
      + sh.fragmentShader.replace('#include <lights_fragment_end>', '#include <lights_fragment_end>\n' + LIGHTS_GLSL + CAST_GLSL);
  };
  m.customProgramCacheKey = () => (prevKey ? prevKey() : '') + '|castlight'; // (its own program, with or without a key before)
  m.needsUpdate = true;
}
function patchActor(a) {
  if (!a || !a.ch || !a.ch.root) return;
  a.ch.root.traverse((o) => { if (o.isMesh || o.isSkinnedMesh) for (const m of [].concat(o.material)) patch(m); });
}

// the place's colour: the nearest lamps the city picked (their colour, weighted by how close the list put them) over
// the grade's haze. eased, so walking past a lamp doesn't flicker the cast
const want = { fill: new THREE.Color(), rim: new THREE.Color() }, c = new THREE.Color(), lamp = new THREE.Color();
let scanT = 0;
export function castLightFrame(dt) {
  const def = G.joined && G.cfg && MAPS[G.cfg.map], city = !!(def && def.stream && def.story);
  if (!city) { // (the train, the test lot, PvP: nothing added, and the city's lights don't follow you there)
    uFill.value.setRGB(0, 0, 0); uRim.value.setRGB(0, 0, 0);
    if (uLCset) { for (const v of cityUniforms.uLC.value) v.set(0, 0, 0, 0); uLCset = false; }
    return;
  }
  uLCset = true;
  if ((scanT -= dt) <= 0) { scanT = 0.5; for (const a of actors.values()) patchActor(a); } // (new arrivals: twice a second is plenty)
  lamp.setRGB(0, 0, 0); let w = 0;
  const LC = cityUniforms.uLC.value;
  for (let i = 0; i < Math.min(CAST_LIGHT.lamps, NL); i++) { const k = 1 / (1 + i); lamp.r += LC[i].x * k; lamp.g += LC[i].y * k; lamp.b += LC[i].z * k; w += k; }
  if (w > 0) lamp.multiplyScalar(1 / w);
  const haze = cityUniforms.uHaze.value;
  want.fill.copy(haze).multiplyScalar(0.6).add(c.copy(lamp).multiplyScalar(0.25)).multiplyScalar(CAST_LIGHT.fill);
  want.rim.copy(haze).multiplyScalar(0.5).add(c.copy(lamp).multiplyScalar(0.5)).multiplyScalar(CAST_LIGHT.rim);
  const k = Math.min(1, dt * CAST_LIGHT.ease);
  uFill.value.lerp(want.fill, k); uRim.value.lerp(want.rim, k);
}
let uLCset = false;
