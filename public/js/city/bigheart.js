// THE BIG HEART, drawn (shared/city/bigheart.js is where it stands and what you bump into). Its own loader, because the
// city's prop path (props.js) throws away every vertex channel but position / normal / uv / colour, and this model's
// TEXCOORD_1 is the ripple: (phase, weight) per vertex. One vertex-shader line swells each small heart along its
// normal as the beat reaches it, top of the heart first, apex last, then on down the tower's vessels to the roots; a
// flush of colour travels with it (that's what you see from across the district) and the pits glow as it passes.
// The beat is the Gut's one clock (gutbeat.js): the fog closes in as the wave starts at the top.
// Cost: nothing is fetched until you're within LOAD_R of it; past the fog it isn't drawn; near / far model by
// distance (the far one is 8k triangles); the thud only inside 150 m.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { BIG_HEART } from '/shared/city/bigheart.js';
import { jankUniforms } from '../jank.js';
import { sfx } from '../audio.js';
import { cityUniforms, LIGHTS_GLSL, LIGHTS_HEAD } from './mats.js';
import { propEnv } from './props.js';
import { gutBeat, tickBeat } from './gutbeat.js';
import { startGutFog, stopGutFog, updateGutFog } from './gutfog.js';

export { gutBeat };
const URL = '/models/story/s_gut_heart.glb';
const LOAD_R = 340, SEE_R = 320, HEAR_R = 150; // metres from the tower: fetch it, draw it (if the fog lets you), hear it
const SWAP = [48, 84, 120, 120], HYST = 8; // near model inside this, per render preset (Potato .. Too HD), with a little slack so it doesn't flicker
// the swell at a crown (m), how much a heart flushes, how much the pits brighten; then its own light, because the Gut
// is dim and lit from above and you mostly see this thing from underneath: self = how much of its colour the flesh
// gives off at rest, lit = how much more as the beat passes through it, rim = the wet red edge, bone = the tower's
// big = the one big beat: the whole heart swells this much of its size on the lub (0.6 of it on the dub), all at once,
// up in a twentieth of a second and down over a quarter, with the ripple riding on top. bigLit = how much the whole
// heart flushes, glows and lights its pits with it
export const HEART_FX = { big: 0.08, bigLit: 1, amp: 0.09, flush: 0.6, glow: 1.1, self: 0.3, lit: 0.9, rim: 0.3, bone: 0.2 };
const HC = BIG_HEART.markers.heart_centre; // model space
const U = { uGhT: { value: 0 }, uGhSpan: { value: gutBeat.span }, uGhAmp: { value: HEART_FX.amp }, uGhBig: { value: new THREE.Vector4(HC[0], HC[1], HC[2], HEART_FX.big) }, uGhLub: { value: new THREE.Vector3(gutBeat.lub - 0.04, gutBeat.dub, HEART_FX.bigLit) }, uGhFlush: { value: HEART_FX.flush }, uGhGlow: { value: HEART_FX.glow },
  uGhSelf: { value: new THREE.Vector4(HEART_FX.self, HEART_FX.lit, HEART_FX.rim, HEART_FX.bone) } };

// every material gets the Potato vertex snap and the city's lamp light (like a prop); flesh and glow get the ripple
function patch(mat, ripple) {
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, { uSnap: jankUniforms.uSnap }, cityUniforms, U);
    sh.vertexShader = `uniform vec2 uSnap;
      ${ripple ? `attribute vec2 aPulse; uniform float uGhT, uGhSpan, uGhAmp; uniform vec3 uGhLub; uniform vec4 uGhBig; varying vec3 vGh;
      float ghBeat(float t) { return exp(-pow((t - 0.12) / 0.045, 2.0)) + 0.6 * exp(-pow((t - 0.33) / 0.06, 2.0)); } // lub-dub, then rest
      float ghBig(float x) { // the big beat, x = beats since it began: up fast, down slow (a swell you can see, not a twitch), then the dub
        float y = x - uGhLub.y;
        return smoothstep(0.0, 0.04, x) * exp(-max(0.0, x - 0.04) / 0.11) + (y > 0.0 ? 0.6 * smoothstep(0.0, 0.04, y) * exp(-max(0.0, y - 0.04) / 0.09) : 0.0); }` : ''}
      ` + sh.vertexShader
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        ${ripple ? `float gh = ghBeat(fract(uGhT - aPulse.x * uGhSpan));
        // the one big beat: the whole heart swells from its middle, all at once, on the lub and again on the dub. the
        // base stays put (nothing below the apex moves: the sleeve and the tower's vessels are fused to bone)
        float ghB = ghBig(fract(uGhT - uGhLub.x)) * smoothstep(26.5, 32.5, position.y);
        vGh = vec3(gh, gh * aPulse.y, ghB * uGhLub.z);
        transformed += (position - uGhBig.xyz) * (uGhBig.w * ghB) + objectNormal * (aPulse.y * uGhAmp * gh); // the ripple rides on it` : ''}`)
      .replace('#include <project_vertex>', `#include <project_vertex>
        vec4 jsnap = gl_Position; jsnap.xyz /= jsnap.w; jsnap.xy = floor(jsnap.xy * uSnap + 0.5) / uSnap; jsnap.xyz *= jsnap.w; gl_Position = jsnap;`);
    let fs = 'uniform vec4 uGhSelf;\n' + sh.fragmentShader;
    if (ripple) fs = 'varying vec3 vGh; uniform float uGhFlush, uGhGlow;\n' + fs
      .replace('#include <color_fragment>', '#include <color_fragment>\n vec3 ghBase = diffuseColor.rgb; diffuseColor.rgb *= 1.0 + uGhFlush * (vGh.y + 0.7 * vGh.z);') // each heart flushes as it beats, and the whole thing a little on the big one
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        totalEmissiveRadiance *= 0.55 + uGhGlow * (vGh.x + 1.2 * vGh.z); // the light in the pits swells with the ripple, and all the pits flare on the big beat
        { float rim = pow(1.0 - abs(dot(normalize(vViewPosition), normal)), 2.5); // and the flesh glows a little by itself, more as the wave goes through
          totalEmissiveRadiance += ghBase * (uGhSelf.x + uGhSelf.y * (vGh.y + 0.6 * vGh.z)) + vec3(0.9, 0.1, 0.16) * rim * uGhSelf.z * (0.6 + vGh.x); }`);
    else fs = fs.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n totalEmissiveRadiance += diffuseColor.rgb * uGhSelf.w;'); // bone: never pitch black from below
    if (fs.includes('#include <lights_fragment_end>')) fs = '#define CITY_LIGHTS\n' + LIGHTS_HEAD + fs.replace('#include <lights_fragment_end>', '#include <lights_fragment_end>\n' + LIGHTS_GLSL);
    sh.fragmentShader = fs;
  };
  mat.customProgramCacheKey = () => 'bigheart' + (ripple ? 'r' : '');
  return mat;
}

let H = null; // { root, near: [], far: [], state, lod, parent }
export function startHeart(parent) {
  stopHeart();
  H = { parent, root: null, near: [], far: [], state: 'idle', lod: -1, beatN: null, d: 1e9 };
  startGutFog(parent);
}
export function stopHeart() {
  stopGutFog();
  if (!H) return;
  if (H.root) { H.root.removeFromParent(); H.root.traverse((o) => { if (o.isMesh) { o.geometry.dispose(); for (const m of [].concat(o.material)) { for (const k of ['map', 'emissiveMap']) if (m[k]) m[k].dispose(); m.dispose(); } } }); }
  H = null;
}
function load() {
  const me = H; me.state = 'loading';
  new GLTFLoader().load(URL, (g) => {
    if (H !== me) return; // the city was stopped while it was on its way
    const env = propEnv(), done = new Set();
    g.scene.traverse((o) => {
      if (!o.isMesh) return;
      let lod = false; for (let p = o; p; p = p.parent) if (/_lod1/.test(p.name) || /_lod1/.test(p.userData.name || '')) lod = true;
      (lod ? me.far : me.near).push(o);
      const uv1 = o.geometry.getAttribute('uv1');
      for (const m of [].concat(o.material)) {
        const ripple = /gh_flesh|gh_glow/.test(m.name) && !!uv1;
        if (ripple) o.geometry.setAttribute('aPulse', uv1);
        if (done.has(m)) continue; done.add(m);
        for (const k of ['map', 'emissiveMap']) if (m[k]) { m[k].magFilter = THREE.NearestFilter; m[k].minFilter = THREE.NearestMipmapNearestFilter; m[k].anisotropy = 1; m[k].needsUpdate = true; }
        if (env && 'envMap' in m) { m.envMap = env; m.envMapIntensity = 0.3; }
        patch(m, ripple);
      }
      o.matrixAutoUpdate = false;
    });
    g.scene.position.set(BIG_HEART.x, BIG_HEART.y, BIG_HEART.z); g.scene.name = 'bigheart';
    g.scene.updateMatrixWorld(true);
    me.root = g.scene; me.state = 'ready'; me.lod = -1; me.root.visible = false;
    me.parent.add(me.root);
  }, undefined, (e) => { if (H === me) me.state = 'failed'; console.warn('the big heart did not load', e); });
}

// once a frame from ingame.js, after the stream's update (so the district env is this frame's)
export function updateHeart(dt, S, camera) {
  if (!H) return;
  const b = tickBeat(), p = camera.position, e = S.env;
  const d = Math.hypot(p.x - BIG_HEART.x, p.z - BIG_HEART.z); H.d = d;
  if (H.state === 'idle' && d < LOAD_R) load();
  if (H.root && !H.warm && S.warm) { const me = H; me.warm = 'wait'; const ms = []; me.root.traverse((o) => { if (o.isMesh) ms.push(o); }); S.warm(ms, () => { me.warm = 'done'; }); } // its shaders and textures warm up first (stream.js), a frame at a time
  if (H.root) {
    const far = e ? e.far : 250, see = d < Math.min(SEE_R, far + BIG_HEART.reach) && (H.warm === 'done' || !S.warm); // (not drawn until then: it compiled 4-6 shaders on the frame it first showed)
    H.root.visible = see;
    if (see) {
      const R = SWAP[S.preset] ?? SWAP[1], lod = H.lod === 0 ? (d > R + HYST ? 1 : 0) : (d < R - HYST ? 0 : 1);
      if (lod !== H.lod) { H.lod = lod; for (const o of H.near) o.visible = lod === 0; for (const o of H.far) o.visible = lod === 1; }
      U.uGhT.value = b.t % 64; U.uGhAmp.value = HEART_FX.amp; U.uGhBig.value.w = HEART_FX.big; U.uGhLub.value.set(gutBeat.lub - 0.04, gutBeat.dub, HEART_FX.bigLit); U.uGhFlush.value = HEART_FX.flush; U.uGhGlow.value = HEART_FX.glow; U.uGhSelf.value.set(HEART_FX.self, HEART_FX.lit, HEART_FX.rim, HEART_FX.bone);
    }
  }
  // the thud: once a beat as the top of the heart goes, louder the closer you are, nothing past HEAR_R
  const n = Math.floor(b.t - gutBeat.lub + 0.02); // just ahead of the big beat's peak (counted in beats, so a slow frame is late, never silent or double)
  if (n !== H.beatN && d < HEAR_R && b.fix == null && H.beatN != null) { const v = 1 - d / HEAR_R; sfx.bigHeart(v * v, [BIG_HEART.x, BIG_HEART.y + 30, BIG_HEART.z], gutBeat.dub / b.rate); }
  H.beatN = n;
  updateGutFog(dt, S, camera, b);
}
// what's drawn right now (tests, tools): { state, lod: 0 near | 1 far, visible, d }
export const heartState = () => (H ? { state: H.state, lod: H.lod, visible: !!(H.root && H.root.visible), d: Math.round(H.d) } : null);
